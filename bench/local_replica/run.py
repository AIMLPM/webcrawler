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
import random
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

def content_signal_pct(site_results: List[dict],
                       run_dir: Path, word_threshold: int = 50) -> float:
    """Fraction of crawled pages with ≥word_threshold extracted words.

    Mirrors the public benchmark's "content signal" column: reading the
    pages.jsonl files written during the run, counting how many pages
    have non-trivial extracted text.
    """
    total = 0
    signal = 0
    for r in site_results:
        jsonl = run_dir / r["name"] / "pages.jsonl"
        if not jsonl.is_file():
            continue
        for line in jsonl.open():
            line = line.strip()
            if not line:
                continue
            try:
                pg = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            words = len((pg.get("text") or "").split())
            if words >= word_threshold:
                signal += 1
    return round(100.0 * signal / total, 2) if total > 0 else 0.0


# Cost-at-scale and pipeline-timing formulas (SC-6).
#
# We extrapolate from this run's measured rates to the v2.0 leaderboard's
# "1M URLs at 50 pages each" reference scale (50M pages total). All
# assumptions are documented so reviewers can audit:
#
#   * embed_dollars_per_M_chunks: $0.02 per 1M tokens (text-embedding-3-small,
#     2026 pricing) × ~500 tokens/chunk avg = $10/1M chunks. The v2.0
#     reference number $5,464 (scrapy+md) appears to count a more
#     expensive embedder; we report ours at the cheap-but-strong 3-small.
#   * chunks_per_page: ~3 (measured median across our existing replica
#     runs, e.g. rust-book pages avg 3.2 chunks).
#   * pipeline_timing_1k_pages_sec: extrapolated from this run's
#     end-to-end wallclock per page × 1000.
#
# These are dependent on this run's measured rates. If the embedder or
# chunker changes materially, recompute and update REPLICA.md.
SCALE_TOTAL_PAGES = 50_000_000  # v2.0 ref: 1M URLs × 50 pages = 50M
SCALE_REF_TIMING_PAGES = 1000   # ref pipeline-timing slice
EMBED_DOLLARS_PER_M_CHUNKS = 10.0
CHUNKS_PER_PAGE = 3.0


def cost_at_scale(n_chunks_in_run: int, n_pages_in_run: int) -> float:
    """Project total $ to embed 50M pages worth of chunks, given this
    run's chunk-density.

    Returns dollars (not millicents).
    """
    if n_pages_in_run <= 0:
        return 0.0
    chunks_per_page = n_chunks_in_run / n_pages_in_run if n_chunks_in_run else CHUNKS_PER_PAGE
    total_chunks = SCALE_TOTAL_PAGES * chunks_per_page
    return round(total_chunks / 1_000_000 * EMBED_DOLLARS_PER_M_CHUNKS, 2)


def pipeline_timing_1k(n_pages: int, total_wallclock: float) -> float:
    """Extrapolated end-to-end wallclock for 1000 pages, in seconds.

    End-to-end = crawl + chunk + embed + score. Lets reviewers compare
    directly against the v2.0 leaderboard's pipeline-timing column
    (scrapy+md = 1465s for the 1k-page reference)."""
    if n_pages <= 0:
        return 0.0
    sec_per_page = total_wallclock / n_pages
    return round(sec_per_page * SCALE_REF_TIMING_PAGES, 2)


def summarize(site_results: List[dict], total_wallclock: float,
              run_dir: Path = None,
              n_chunks: int = 0,
              full_report: bool = False) -> dict:
    n_pages = sum(r.get("pages", 0) for r in site_results)
    crawl_seconds = sum(r.get("wallclock", 0) for r in site_results)
    crawl_pps = n_pages / crawl_seconds if crawl_seconds > 0 else 0.0
    e2e_pps = n_pages / total_wallclock if total_wallclock > 0 else 0.0
    mrrs = [r["mrr"] for r in site_results if "mrr" in r]
    by_cat: Dict[str, List[float]] = {}
    for r in site_results:
        if "mrr" in r:
            by_cat.setdefault(r["category"], []).append(r["mrr"])

    # Per-site p/s for the "ex-NPR" cut. NPR-style sites are server-bound
    # and drag the aggregate; the spec's 8-site bar (and the public
    # leaderboard) rotate news sites, so reporting both is honest.
    pps_ex_npr = 0.0
    npr_names = {"npr-news"}
    ex_npr_pages = sum(r.get("pages", 0) for r in site_results
                       if r.get("name") not in npr_names)
    ex_npr_secs = sum(r.get("wallclock", 0) for r in site_results
                      if r.get("name") not in npr_names)
    if ex_npr_secs > 0:
        pps_ex_npr = round(ex_npr_pages / ex_npr_secs, 3)

    out = {
        "n_sites": len(site_results),
        "n_pages_total": n_pages,
        "wallclock_total_sec": round(total_wallclock, 2),
        "wallclock_crawl_only_sec": round(crawl_seconds, 2),
        "pages_per_sec_crawl_only": round(crawl_pps, 3),
        "pages_per_sec_end_to_end": round(e2e_pps, 3),
        "pages_per_sec_ex_npr": pps_ex_npr,
        "mrr_mean": round(sum(mrrs) / len(mrrs), 4) if mrrs else 0.0,
        "mrr_median": round(sorted(mrrs)[len(mrrs)//2], 4) if mrrs else 0.0,
        "by_category": {c: {"n": len(ms), "mrr_mean": round(sum(ms)/len(ms), 4)}
                        for c, ms in by_cat.items()},
    }

    if full_report:
        out["full_report"] = {
            "content_signal_pct": (
                content_signal_pct(site_results, run_dir) if run_dir else None
            ),
            "cost_at_scale_50M_dollars": cost_at_scale(n_chunks, n_pages),
            "pipeline_timing_1k_pages_sec": pipeline_timing_1k(n_pages, total_wallclock),
            "assumptions": {
                "embedder": "text-embedding-3-small",
                "embed_dollars_per_M_chunks": EMBED_DOLLARS_PER_M_CHUNKS,
                "scale_total_pages": SCALE_TOTAL_PAGES,
                "scale_ref_timing_pages": SCALE_REF_TIMING_PAGES,
                "chunks_per_page_observed": (
                    round(n_chunks / n_pages, 2) if n_pages else None
                ),
            },
            "leaderboard_runner_up_v2": {
                "speed_pps": 5.3,
                "content_signal_pct": 99.0,
                "cost_at_scale_dollars": 5464.0,
                "pipeline_timing_sec": 1465.0,
                "tool": "scrapy+md",
            },
        }
    return out


def write_report_md(label: str, summary: dict, site_results: List[dict],
                    out: Path) -> None:
    lines = [f"# Local Replica Report — {label}",
             f"", f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", ""]
    lines.append(f"**Aggregate:** {summary['n_sites']} sites, "
                 f"{summary['n_pages_total']} pages")
    lines.append(f"- crawl-only: {summary['wallclock_crawl_only_sec']}s, "
                 f"**{summary['pages_per_sec_crawl_only']} p/s** (leaderboard-comparable)")
    lines.append(f"- ex-NPR (server-bound site excluded): "
                 f"**{summary.get('pages_per_sec_ex_npr', '?')} p/s**")
    lines.append(f"- end-to-end (incl. embedding/scoring): {summary['wallclock_total_sec']}s, "
                 f"{summary['pages_per_sec_end_to_end']} p/s")
    lines.append(f"- **MRR mean = {summary['mrr_mean']}** (median = {summary['mrr_median']})")
    lines.append("")
    if "full_report" in summary:
        fr = summary["full_report"]
        ru = fr["leaderboard_runner_up_v2"]
        lines.append("## 4 leadership dimensions (SC-6)")
        lines.append("")
        lines.append("| dimension | this run | v2 runner-up ({}) |".format(ru["tool"]))
        lines.append("|-----------|----------|--------------------|")
        lines.append(f"| speed (p/s, crawl-only) | {summary['pages_per_sec_crawl_only']} | {ru['speed_pps']} |")
        lines.append(f"| content_signal (%) | {fr['content_signal_pct']} | {ru['content_signal_pct']} |")
        lines.append(f"| cost_at_scale ($, 50M pages) | {fr['cost_at_scale_50M_dollars']} | {ru['cost_at_scale_dollars']} |")
        lines.append(f"| pipeline_timing (s, 1k ref) | {fr['pipeline_timing_1k_pages_sec']} | {ru['pipeline_timing_sec']} |")
        lines.append("")
        a = fr["assumptions"]
        lines.append(f"_Assumptions: embedder={a['embedder']}, ${a['embed_dollars_per_M_chunks']}/1M chunks, "
                     f"chunks_per_page_observed={a['chunks_per_page_observed']}, "
                     f"scale={a['scale_total_pages']:,} pages._")
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
    p.add_argument("--rotated-sample", type=int, default=None,
                   help="Sample N sites from the rotated pool (seed=42). Defaults to all when --rotated-pool is set without this flag.")
    p.add_argument("--rotated-seed", type=int, default=42,
                   help="Random seed for --rotated-sample. Default 42.")
    p.add_argument("--full-report", action="store_true",
                   help="Emit 4 leaderboard dimensions (pages/sec, content_signal_pct, cost_at_scale_dollars, pipeline_timing_sec). See SC-6 in specs/v099-...md.")
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
        if args.rotated_sample and args.rotated_sample < len(sites):
            rng = random.Random(args.rotated_seed)
            sites = rng.sample(sites, args.rotated_sample)
            log.info("rotated-sample: %d/%d sites (seed=%d)",
                     len(sites), len(all_sites), args.rotated_seed)
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
    n_chunks = sum(r.get("n_chunks", 0) for r in site_results)
    summary = summarize(site_results, total, run_dir=run_dir,
                        n_chunks=n_chunks, full_report=args.full_report)
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
    print(f"  ex-NPR p/s:  {summary['pages_per_sec_ex_npr']}")
    print(f"  MRR mean:    {summary['mrr_mean']}  (median {summary['mrr_median']})")
    print(f"  Per-cat:     " + " | ".join(
        f"{c}: {st['mrr_mean']:.3f} (n={st['n']})"
        for c, st in summary["by_category"].items()))
    if args.full_report:
        fr = summary["full_report"]
        ru = fr["leaderboard_runner_up_v2"]
        print()
        print(f"  --- 4 leadership dimensions ---")
        print(f"  speed (p/s, crawl-only):    {summary['pages_per_sec_crawl_only']}  vs runner-up {ru['speed_pps']}")
        print(f"  content_signal (%):         {fr['content_signal_pct']}  vs runner-up {ru['content_signal_pct']}")
        print(f"  cost_at_scale ($, 50M pgs): {fr['cost_at_scale_50M_dollars']}  vs runner-up {ru['cost_at_scale_dollars']}")
        print(f"  pipeline_timing (s, 1k):    {fr['pipeline_timing_1k_pages_sec']}  vs runner-up {ru['pipeline_timing_sec']}")


if __name__ == "__main__":
    main()
