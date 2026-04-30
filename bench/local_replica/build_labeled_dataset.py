"""DS-4: Build labeled site dataset for the autoresearch sweep.

For each site in sites_scrape_evals.yaml + sites_hand_curated.yaml, crawl
twice (render_js=False, render_js=True), 50 pages each, then label
`needs_render_js` based on the extracted-word-count ratio.

Ground-truth label rule:
  - playwright_yield = sum of word counts across all rendered pages
  - static_yield     = sum of word counts across all static pages
  - needs_render_js  = (playwright_yield / max(static_yield, 1)) > 2.0
  - indeterminate    = both yields < 100 words (site is unreachable / bot-walled)

Records all SiteProfile fields (url_class, is_spa, seed_word_count,
sitemap_url_count, etc.) so detection methods can be evaluated against
the same scan signal that the production engine sees.

Pinned to a fixed git ref (captured at start) so signals reflect a
stable scan.py / site_class.py snapshot. If the campaign branch lands
edits to those files mid-run, restart the script.

Usage:
    nohup .venv/bin/python bench/local_replica/build_labeled_dataset.py \\
        --output bench/local_replica/labeled_sites.json \\
        --max-sites 171 > /tmp/ds4.log 2>&1 &

Output:
    bench/local_replica/labeled_sites.json  -- full dataset
    bench/local_replica/runs/ds4-static/<slug>/    -- static crawls
    bench/local_replica/runs/ds4-rendered/<slug>/  -- rendered crawls
"""
from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from markcrawl.core import crawl  # noqa: E402
from markcrawl.scan import scan_site  # noqa: E402

REPLICA = Path(__file__).resolve().parent
RUNS = REPLICA / "runs"
SITES_FILES = [REPLICA / "sites_scrape_evals.yaml",
               REPLICA / "sites_hand_curated.yaml"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("ds4")


def load_all_sites() -> List[dict]:
    out = []
    for path in SITES_FILES:
        sites = yaml.safe_load(path.open())["sites"]
        for s in sites:
            out.append({
                "slug": s["slug"], "url": s["base_url"],
                "category": s["category"], "role": s.get("role", "?"),
                "max_pages": int(s.get("max_pages", 50)),
            })
    return out


def page_word_count(page: dict) -> int:
    text = page.get("text") or ""
    return len(text.split())


def yield_metrics(jsonl: Path) -> Dict:
    if not jsonl.is_file():
        return {"n_pages": 0, "total_words": 0, "mean_words_per_page": 0,
                "n_empty_pages": 0}
    pages = [json.loads(l) for l in jsonl.open() if l.strip()]
    counts = [page_word_count(p) for p in pages]
    n_pages = len(pages)
    total = sum(counts)
    n_empty = sum(1 for c in counts if c < 5)
    return {
        "n_pages": n_pages,
        "total_words": total,
        "mean_words_per_page": round(total / n_pages, 1) if n_pages else 0,
        "n_empty_pages": n_empty,
    }


PER_SITE_WALLCLOCK_SEC = 300


def _crawl_inline(url: str, out_dir: Path, render_js: bool, max_pages: int,
                  timeout: int) -> Dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    try:
        result = crawl(
            base_url=url, out_dir=str(out_dir), fmt="markdown",
            max_pages=max_pages, delay=0.0, timeout=timeout,
            show_progress=False, min_words=5, render_js=render_js,
            auto_path_scope=True, auto_path_priority=True, use_sitemap=True,
        )
        wall = time.perf_counter() - t0
        return {
            "pages_saved": result.pages_saved,
            "wallclock_sec": round(wall, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "pages_saved": 0,
            "wallclock_sec": round(time.perf_counter() - t0, 2),
            "error": repr(exc)[:200],
        }


def _crawl_subprocess_target(url, out_dir, render_js, max_pages, timeout, conn):
    try:
        os.setsid()
    except Exception:
        pass
    try:
        result = _crawl_inline(url, Path(out_dir), render_js, max_pages, timeout)
    except BaseException as exc:
        result = {"pages_saved": 0, "wallclock_sec": 0.0,
                  "error": f"subprocess_crash:{exc!r}"[:200]}
    try:
        conn.send(result)
    finally:
        conn.close()


def _kill_tree(pid: int) -> None:
    """Kill pid and all descendants. Best effort — handles missing pgrep."""
    try:
        out = subprocess.check_output(["pgrep", "-P", str(pid)],
                                      text=True, stderr=subprocess.DEVNULL)
        for child in out.split():
            _kill_tree(int(child))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            return
        time.sleep(0.5)


def crawl_one(url: str, out_dir: Path, render_js: bool, max_pages: int = 50,
              timeout: int = 12,
              max_wall_sec: int = PER_SITE_WALLCLOCK_SEC) -> Dict:
    """Run a single crawl in a subprocess so a stuck Playwright render can
    be hard-killed without freezing the campaign.
    """
    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    p = ctx.Process(
        target=_crawl_subprocess_target,
        args=(url, str(out_dir), render_js, max_pages, timeout, child_conn),
        daemon=False,
    )
    t0 = time.perf_counter()
    p.start()
    child_conn.close()
    p.join(max_wall_sec)
    if p.is_alive():
        log.warning("    timeout %ds for %s render_js=%s — killing tree",
                    max_wall_sec, url, render_js)
        _kill_tree(p.pid)
        p.join(10)
        if p.is_alive():
            p.kill()
            p.join(5)
        return {
            "pages_saved": 0,
            "wallclock_sec": round(time.perf_counter() - t0, 2),
            "error": f"wallclock_timeout_{max_wall_sec}s",
        }
    if parent_conn.poll(2):
        try:
            return parent_conn.recv()
        except EOFError:
            pass
    return {
        "pages_saved": 0,
        "wallclock_sec": round(time.perf_counter() - t0, 2),
        "error": f"subprocess_no_result_exit{p.exitcode}",
    }


def label_one(site: dict, static_dir: Path, render_dir: Path) -> Dict:
    """Build the label record for one site, given its two crawl outputs."""
    static_jsonl = static_dir / "pages.jsonl"
    render_jsonl = render_dir / "pages.jsonl"

    static_y = yield_metrics(static_jsonl)
    render_y = yield_metrics(render_jsonl)

    # Yield-ratio rule
    s_words = static_y["total_words"]
    r_words = render_y["total_words"]
    if s_words < 100 and r_words < 100:
        label = "indeterminate"
        ratio = None
    else:
        ratio = r_words / max(s_words, 1)
        label = "needs_render_js" if ratio > 2.0 else "static_ok"

    # Capture scan signals for the cascade methods
    try:
        prof = scan_site(site["url"], timeout=10)
        scan_signals = {
            "url_class": prof.url_class,
            "is_spa": prof.is_spa,
            "seed_word_count": prof.seed_word_count,
            "sitemap_url_count": prof.sitemap_url_count,
            "sitemap_clustered": prof.sitemap_clustered,
            "sitemap_huge": prof.sitemap_huge,
            "seed_outlink_count": prof.seed_outlink_count,
            "seed_outlinks_clustered": prof.seed_outlinks_clustered,
            "empty_seed": prof.empty_seed,
            "fetch_count": prof.fetch_count,
        }
    except Exception as exc:
        scan_signals = {"error": repr(exc)[:200]}

    return {
        "slug": site["slug"],
        "url": site["url"],
        "declared_category": site["category"],
        "role": site["role"],
        "label": label,
        "yield_ratio_render_over_static": round(ratio, 3) if ratio else None,
        "static": static_y,
        "rendered": render_y,
        "scan": scan_signals,
    }


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, help="Path to write labeled_sites.json")
    p.add_argument("--max-sites", type=int, default=171, help="Cap on sites (debug)")
    p.add_argument("--skip-render", action="store_true",
                   help="Skip render_js=True crawl pass (label = unknown but scan signals still recorded)")
    p.add_argument("--resume", action="store_true",
                   help="Skip sites already labeled in --output")
    args = p.parse_args()

    sites = load_all_sites()[:args.max_sites]
    log.info("DS-4 dataset build: %d sites, git_ref=%s", len(sites), git_ref())

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Resume support
    existing: Dict[str, Dict] = {}
    if args.resume and output.is_file():
        prior = json.loads(output.read_text())
        existing = {r["slug"]: r for r in prior.get("sites", [])}
        log.info("resuming with %d existing labels", len(existing))

    static_root = RUNS / "ds4-static"
    render_root = RUNS / "ds4-rendered"

    results: List[Dict] = list(existing.values())
    seen = set(existing.keys())

    for i, site in enumerate(sites, start=1):
        if site["slug"] in seen:
            continue
        log.info("[%d/%d] %s (%s)", i, len(sites), site["slug"], site["category"])
        s_dir = static_root / site["slug"]
        r_dir = render_root / site["slug"]
        s_meta = crawl_one(site["url"], s_dir, render_js=False,
                           max_pages=site["max_pages"])
        log.info("    static: pages=%d (%.1fs)%s",
                 s_meta["pages_saved"], s_meta["wallclock_sec"],
                 f" ERR={s_meta['error']}" if s_meta["error"] else "")
        if not args.skip_render:
            r_meta = crawl_one(site["url"], r_dir, render_js=True,
                               max_pages=site["max_pages"])
            log.info("    render: pages=%d (%.1fs)%s",
                     r_meta["pages_saved"], r_meta["wallclock_sec"],
                     f" ERR={r_meta['error']}" if r_meta["error"] else "")
        rec = label_one(site, s_dir, r_dir)
        rec["static_meta"] = s_meta
        if not args.skip_render:
            rec["rendered_meta"] = r_meta
        results.append(rec)
        log.info("    label=%s ratio=%s", rec["label"],
                 rec["yield_ratio_render_over_static"])

        # Incremental save every 5 sites
        if i % 5 == 0:
            tmp = {"git_ref": git_ref(), "n_sites": len(results), "sites": results}
            output.write_text(json.dumps(tmp, indent=2))

    final = {
        "git_ref": git_ref(),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "n_sites": len(results),
        "label_distribution": {
            "needs_render_js": sum(1 for r in results if r["label"] == "needs_render_js"),
            "static_ok": sum(1 for r in results if r["label"] == "static_ok"),
            "indeterminate": sum(1 for r in results if r["label"] == "indeterminate"),
        },
        "sites": results,
    }
    output.write_text(json.dumps(final, indent=2))
    log.info("DONE -> %s (%d sites, dist=%s)",
             output, len(results), final["label_distribution"])


if __name__ == "__main__":
    main()
