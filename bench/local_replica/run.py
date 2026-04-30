"""Local replica of llm-crawler-benchmarks (v1.2 site pool, v2.0 methodology).

Runs the canonical 11-site retrieval benchmark on the local machine using
the current markcrawl source. Output JSON per run with per-site
pages/sec, MRR, hit rates, and total wallclock — directly comparable to
the public leaderboard's "speed" and "MRR" columns.

This is the gate for SC-1..SC-3 of specs/v099-speed-recovery-and-mrr-closure.md:
every change to markcrawl/core.py must keep speed and MRR within the
documented bounds before we push to the public CI.

Usage:
    .venv/bin/python bench/local_replica/run.py --label v098-baseline
    .venv/bin/python bench/local_replica/run.py --label v099-step1 --sites react-dev,stripe-docs
    .venv/bin/python bench/local_replica/run.py --label rotated --rotated-pool

The canonical pool comes from
``sites_v1.2_canonical.yaml`` (mirrored from
github.com/AIMLPM/llm-crawler-benchmarks/sites/pool_v1.yaml @ v1.2,
released 2026-04-24). Queries come from ``queries/<site>.json``,
extracted from the same repo's ``benchmark_retrieval.py:TEST_QUERIES``.

Output:
    bench/local_replica/runs/<label>/<site>/pages.jsonl    -- crawl
    bench/local_replica/runs/<label>/<site>/report.json    -- per-site MRR
    bench/local_replica/runs/<label>/summary.json          -- aggregate
    bench/local_replica/runs/<label>/REPORT.md             -- human-readable
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from markcrawl.chunker import chunk_markdown  # noqa: E402
from markcrawl.core import crawl  # noqa: E402

REPLICA = Path(__file__).resolve().parent
QUERIES = REPLICA / "queries"
RUNS = REPLICA / "runs"
CANONICAL = REPLICA / "sites_v1.2_canonical.yaml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("replica")


# ---------------------------- Site loading -----------------------------

def load_sites() -> List[dict]:
    raw = yaml.safe_load(CANONICAL.open())["sites"]
    out = []
    for s in raw:
        if not s.get("has_queries", True):
            continue
        out.append({
            "name": s["name"],
            "url": s["url"],
            "category": s.get("category", "?"),
            "max_pages": int(s.get("max_pages", 200)),
            "render_js": bool(s.get("render_js", False)),
            "difficulty": s.get("difficulty", []),
        })
    return out


# ---------------------------- Crawl + extract -----------------------------

def crawl_site(site: dict, out_dir: Path, dispatch_kwargs: dict) -> Tuple[int, float]:
    """Crawl one site. Return (pages_saved, wallclock_sec)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    kwargs = dict(
        base_url=site["url"], out_dir=str(out_dir), fmt="markdown",
        max_pages=site["max_pages"], delay=0.0, timeout=20,
        show_progress=False, min_words=5,
        render_js=site["render_js"],
        auto_path_scope=True, auto_path_priority=True, use_sitemap=True,
    )
    kwargs.update(dispatch_kwargs)
    t0 = time.perf_counter()
    try:
        result = crawl(**kwargs)
        pages = result.pages_saved
    except Exception as exc:
        log.warning("crawl failed for %s: %s", site["name"], exc)
        pages = 0
    return pages, time.perf_counter() - t0


# ---------------------------- MRR scoring -----------------------------

_PAGE_CACHE: Dict[Path, List[dict]] = {}


def load_pages(jsonl_path: Path) -> List[dict]:
    if jsonl_path in _PAGE_CACHE:
        return _PAGE_CACHE[jsonl_path]
    pages = [json.loads(line) for line in jsonl_path.open() if line.strip()]
    _PAGE_CACHE[jsonl_path] = pages
    return pages


def chunkify(pages: List[dict]) -> List[dict]:
    """Yield {url, text} chunks. JSONL field is 'text' (not 'markdown'); chunks are Chunk dataclasses."""
    out = []
    for p in pages:
        md = p.get("text") or p.get("markdown") or ""
        if not md:
            continue
        url = p.get("url", "")
        for ck in chunk_markdown(md):
            text = getattr(ck, "text", None) or (ck if isinstance(ck, str) else str(ck))
            out.append({"url": url, "text": text})
    return out


_CLIENT = None


def _openai_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        env_path = ROOT / ".env"
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        raise SystemExit("OPENAI_API_KEY missing (env or .env)")
    from openai import OpenAI
    _CLIENT = OpenAI(api_key=api_key)
    return _CLIENT


def embed_openai(texts: List[str], model: str = "text-embedding-3-small",
                 batch: int = 96) -> List[List[float]]:
    """Embed via OpenAI batch API. Loads OPENAI_API_KEY from env or .env."""
    client = _openai_client()
    out: List[List[float]] = []
    for i in range(0, len(texts), batch):
        chunk = texts[i:i+batch]
        resp = client.embeddings.create(input=chunk, model=model)
        out.extend([d.embedding for d in resp.data])
    return out


def cosine_top_k(query_vec: List[float], chunk_vecs: List[List[float]], k: int = 20) -> List[int]:
    import numpy as np
    qv = np.asarray(query_vec, dtype=np.float32)
    cv = np.asarray(chunk_vecs, dtype=np.float32)
    qn = qv / (np.linalg.norm(qv) + 1e-9)
    cn = cv / (np.linalg.norm(cv, axis=1, keepdims=True) + 1e-9)
    scores = cn @ qn
    top = np.argsort(scores)[::-1][:k]
    return top.tolist()


def score_site(site_name: str, jsonl_path: Path) -> dict:
    """Compute MRR + Hit@K against canonical queries."""
    qpath = QUERIES / f"{site_name}.json"
    if not qpath.is_file():
        return {"error": f"no queries for {site_name}"}
    queries = json.loads(qpath.read_text())
    pages = load_pages(jsonl_path)
    chunks = chunkify(pages)
    if not chunks:
        return {"mrr": 0.0, "n_queries": len(queries), "n_chunks": 0,
                "hits": {1: 0, 3: 0, 5: 0, 10: 0, 20: 0}, "per_query": []}

    # Embed chunks (cached per-site under the run dir)
    cache = jsonl_path.parent / "embed_cache.json"
    if cache.is_file():
        cdata = json.loads(cache.read_text())
        if cdata.get("n") == len(chunks):
            chunk_vecs = cdata["vecs"]
        else:
            cdata = None
    else:
        cdata = None
    if cdata is None:
        log.info("  embedding %d chunks for %s ...", len(chunks), site_name)
        chunk_vecs = embed_openai([c["text"] for c in chunks])
        cache.write_text(json.dumps({"n": len(chunks), "vecs": chunk_vecs}))

    # Embed queries
    query_vecs = embed_openai([q["query"] for q in queries])

    # Score
    K = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in K}
    rr_sum = 0.0
    per_query = []
    for qi, q in enumerate(queries):
        url_match = q.get("url_match", "")
        topk = cosine_top_k(query_vecs[qi], chunk_vecs, k=20)
        # Find first chunk whose URL matches
        first_rank = None
        for rank, idx in enumerate(topk, start=1):
            chunk_url = chunks[idx]["url"]
            if url_match and url_match.lower() in chunk_url.lower():
                first_rank = rank
                break
        if first_rank is not None:
            rr_sum += 1.0 / first_rank
            for k in K:
                if first_rank <= k:
                    hits[k] += 1
        per_query.append({"query": q["query"][:80], "rank": first_rank,
                          "url_match": url_match, "covered": first_rank is not None})

    n = len(queries)
    return {
        "mrr": rr_sum / n if n else 0.0,
        "n_queries": n,
        "n_chunks": len(chunks),
        "hits": {f"{k}": f"{hits[k]}/{n}" for k in K},
        "hits_raw": hits,
        "per_query": per_query,
    }


# ---------------------------- Aggregation -----------------------------

def summarize(site_results: List[dict], total_wallclock: float) -> dict:
    n_pages = sum(r.get("pages", 0) for r in site_results)
    crawl_seconds = sum(r.get("wallclock", 0) for r in site_results)
    crawl_pps = n_pages / crawl_seconds if crawl_seconds > 0 else 0.0
    e2e_pps = n_pages / total_wallclock if total_wallclock > 0 else 0.0
    mrrs = [r["mrr"] for r in site_results if "mrr" in r]
    by_cat: Dict[str, List[float]] = {}
    for r in site_results:
        if "mrr" in r:
            by_cat.setdefault(r["category"], []).append(r["mrr"])
    return {
        "n_sites": len(site_results),
        "n_pages_total": n_pages,
        "wallclock_total_sec": round(total_wallclock, 2),
        "wallclock_crawl_only_sec": round(crawl_seconds, 2),
        "pages_per_sec_crawl_only": round(crawl_pps, 3),
        "pages_per_sec_end_to_end": round(e2e_pps, 3),
        "mrr_mean": round(sum(mrrs) / len(mrrs), 4) if mrrs else 0.0,
        "mrr_median": round(sorted(mrrs)[len(mrrs)//2], 4) if mrrs else 0.0,
        "by_category": {c: {"n": len(ms), "mrr_mean": round(sum(ms)/len(ms), 4)}
                        for c, ms in by_cat.items()},
    }


def write_report_md(label: str, summary: dict, site_results: List[dict],
                    out: Path) -> None:
    lines = [f"# Local Replica Report — {label}",
             f"", f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", ""]
    lines.append(f"**Aggregate:** {summary['n_sites']} sites, "
                 f"{summary['n_pages_total']} pages")
    lines.append(f"- crawl-only: {summary['wallclock_crawl_only_sec']}s, "
                 f"**{summary['pages_per_sec_crawl_only']} p/s** (leaderboard-comparable)")
    lines.append(f"- end-to-end (incl. embedding/scoring): {summary['wallclock_total_sec']}s, "
                 f"{summary['pages_per_sec_end_to_end']} p/s")
    lines.append(f"- **MRR mean = {summary['mrr_mean']}** (median = {summary['mrr_median']})")
    lines.append("")
    lines.append("## Per-site")
    lines.append("| site | category | pages | wallclock (s) | p/s | MRR | Hit@1 | Hit@10 |")
    lines.append("|------|----------|-------|---------------|-----|-----|-------|--------|")
    for r in site_results:
        h = r.get("hits", {})
        pps = r["pages"] / r["wallclock"] if r.get("wallclock", 0) > 0 else 0.0
        lines.append(f"| {r['name']} | {r['category']} | {r.get('pages','?')} | "
                     f"{r.get('wallclock',0):.1f} | {pps:.2f} | "
                     f"{r.get('mrr','?'):.3f} | {h.get('1','-')} | {h.get('10','-')} |")
    lines.append("")
    lines.append("## Per-category")
    for cat, st in summary["by_category"].items():
        lines.append(f"- **{cat}** — n={st['n']}, mean MRR = {st['mrr_mean']}")
    out.write_text("\n".join(lines) + "\n")


# ---------------------------- Main -----------------------------

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--label", required=True, help="Run label (becomes runs/<label>/)")
    p.add_argument("--sites", help="Comma-separated subset to run (default: all)")
    p.add_argument("--auto-scan", action="store_true", help="Pass auto_scan=True to crawl()")
    p.add_argument("--reuse-crawl", action="store_true", help="Skip crawl if pages.jsonl exists")
    p.add_argument("--rotated-pool", action="store_true",
                   help="Use sites_scrape_evals.yaml + sites_hand_curated.yaml (171 sites, generalization test)")
    args = p.parse_args()

    if args.rotated_pool:
        # Build sites list from scrape-evals + hand-curated
        sites_a = yaml.safe_load((REPLICA/"sites_scrape_evals.yaml").open())["sites"]
        sites_b = yaml.safe_load((REPLICA/"sites_hand_curated.yaml").open())["sites"]
        all_sites = []
        for s in sites_a + sites_b:
            all_sites.append({"name": s["slug"], "url": s["base_url"],
                              "category": s["category"], "max_pages": s.get("max_pages", 50),
                              "render_js": s.get("render_js", False), "difficulty": []})
        sites = all_sites
    else:
        sites = load_sites()

    if args.sites:
        wanted = set(args.sites.split(","))
        sites = [s for s in sites if s["name"] in wanted]

    if not sites:
        log.error("No sites selected.")
        return

    log.info("Replica run label=%s sites=%d auto_scan=%s",
             args.label, len(sites), args.auto_scan)

    run_dir = RUNS / args.label
    run_dir.mkdir(parents=True, exist_ok=True)
    site_results: List[dict] = []
    dispatch = {"auto_scan": args.auto_scan}

    t_total = time.perf_counter()
    for s in sites:
        log.info("[%s] crawl start (max=%d, render_js=%s)",
                 s["name"], s["max_pages"], s["render_js"])
        out = run_dir / s["name"]
        jsonl = out / "pages.jsonl"
        if args.reuse_crawl and jsonl.is_file() and jsonl.stat().st_size > 0:
            n = sum(1 for _ in jsonl.open())
            log.info("  reuse cached crawl: %d pages", n)
            pages, wall = n, 0.0
        else:
            pages, wall = crawl_site(s, out, dispatch)
            log.info("  done: %d pages in %.1fs (%.2f p/s)",
                     pages, wall, pages / wall if wall > 0 else 0.0)
        # Score
        if jsonl.is_file() and pages > 0:
            log.info("  scoring MRR ...")
            r = score_site(s["name"], jsonl)
            r.setdefault("mrr", 0.0)
        else:
            r = {"mrr": 0.0, "error": "no pages"}
        r.update(name=s["name"], category=s["category"], pages=pages, wallclock=wall)
        site_results.append(r)
        # Save per-site report
        (out / "report.json").write_text(json.dumps(r, indent=2))

    total = time.perf_counter() - t_total
    summary = summarize(site_results, total)
    summary["label"] = args.label
    summary["auto_scan"] = args.auto_scan
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    write_report_md(args.label, summary, site_results, run_dir / "REPORT.md")

    print()
    print(f"Replica run done -> {run_dir}/REPORT.md")
    print(f"  crawl-only:  {summary['pages_per_sec_crawl_only']} p/s "
          f"({summary['n_pages_total']} pages in {summary['wallclock_crawl_only_sec']}s)")
    print(f"  end-to-end:  {summary['pages_per_sec_end_to_end']} p/s "
          f"({summary['wallclock_total_sec']}s total)")
    print(f"  MRR mean:    {summary['mrr_mean']}  (median {summary['mrr_median']})")
    print(f"  Per-cat:     " + " | ".join(
        f"{c}: {st['mrr_mean']:.3f} (n={st['n']})"
        for c, st in summary["by_category"].items()))


if __name__ == "__main__":
    main()
