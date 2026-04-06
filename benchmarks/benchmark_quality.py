#!/usr/bin/env python3
"""Extraction quality benchmark — reads crawl output, scores it, writes report.

Completely independent of benchmark_all_tools.py. Reads the pages.jsonl files
written by any benchmark run and produces QUALITY_COMPARISON.md with:

  - Preamble words (nav chrome before first heading — the RAG poison metric)
  - Cross-page repeat rate (sentences recurring across pages — boilerplate detector)
  - Cross-tool consensus precision and recall
  - Side-by-side sample output (first 40 lines per tool for one representative page)

Run after benchmark_all_tools.py completes, or any time you want to re-score
with updated metrics without re-crawling:

    python benchmarks/benchmark_quality.py                        # latest run
    python benchmarks/benchmark_quality.py --run run_20260405_221158
    python benchmarks/benchmark_quality.py --output my_report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).parent
REPO_ROOT = BENCH_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BENCH_DIR))

from quality_scorer import (
    PageQuality,
    generate_quality_report,
    score_consensus,
    score_density,
    score_signals,
)

TOOLS = ["markcrawl", "crawl4ai", "crawl4ai-raw", "scrapy+md", "crawlee", "colly+md", "playwright", "firecrawl"]
SITES = ["quotes-toscrape", "books-toscrape", "fastapi-docs", "python-docs"]

SAMPLE_LINES = 40   # lines of raw output to include in the sample section


def _patch_colly_urls(run_dir: Path, site: str) -> dict[str, str]:
    """Return safe_name → original_url map for colly+md.

    Prefers the _url_map.json written by new runs. Falls back to
    reconstructing from _urls.txt for runs produced before the fix.
    """
    colly_site_dir = run_dir / "colly+md" / site

    map_path = colly_site_dir / "_url_map.json"
    if map_path.exists():
        with open(map_path) as f:
            return json.load(f)

    urls_path = colly_site_dir / "_urls.txt"
    if urls_path.exists():
        url_map: dict[str, str] = {}
        for line in urls_path.read_text().splitlines():
            u = line.strip()
            if u:
                safe = u.replace("://", "_").replace("/", "_")[:80]
                url_map[safe] = u
        return url_map

    return {}


def _fix_colly_jsonl(run_dir: Path, site: str) -> int:
    """Rewrite colly+md pages.jsonl with correct URLs. Returns number of URLs fixed."""
    jsonl_path = run_dir / "colly+md" / site / "pages.jsonl"
    if not jsonl_path.exists():
        return 0

    url_map = _patch_colly_urls(run_dir, site)
    if not url_map:
        return 0

    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    fixed_lines = []
    changed = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        page = json.loads(line)
        current_url = page.get("url", "")
        fixed_url = current_url

        current_safe = current_url.replace("://", "_").replace("/", "_")[:80]
        if current_safe in url_map:
            fixed_url = url_map[current_safe]
        else:
            for safe, original in url_map.items():
                if current_url.replace("/", "_").rstrip("_") in original.replace("/", "_"):
                    fixed_url = original
                    break

        if fixed_url != current_url:
            page["url"] = fixed_url
            changed += 1
        fixed_lines.append(json.dumps(page, ensure_ascii=False))

    if changed:
        jsonl_path.write_text("\n".join(fixed_lines) + "\n", encoding="utf-8")

    return changed


def score_run(run_dir: Path) -> dict[str, dict[str, list[PageQuality]]]:
    """Load all pages.jsonl from a run directory and return scored PageQuality objects."""
    quality_results: dict[str, dict[str, list[PageQuality]]] = {}

    for site in SITES:
        quality_results[site] = {}

        # Fix colly URLs before loading
        fixed = _fix_colly_jsonl(run_dir, site)
        if fixed:
            print(f"  colly+md / {site}: corrected {fixed} URLs")

        # Load all tools' output indexed by URL
        tool_outputs_by_url: dict[str, dict[str, str]] = {}

        for tool in TOOLS:
            jsonl_path = run_dir / tool / site / "pages.jsonl"
            if not jsonl_path.exists():
                continue
            with open(jsonl_path, encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    page = json.loads(raw)
                    url = page.get("url", "").rstrip("/")
                    text = page.get("text", "")
                    if url and text:
                        tool_outputs_by_url.setdefault(url, {})[tool] = text

        # Score each tool
        for tool in TOOLS:
            pages: list[PageQuality] = []
            for url, outputs in tool_outputs_by_url.items():
                if tool not in outputs:
                    continue
                markdown = outputs[tool]
                signal = score_signals(markdown)
                density = score_density(markdown)
                consensus = score_consensus(markdown, outputs, tool)

                # Store first SAMPLE_LINES lines for the sample output section
                raw_sample = "\n".join(markdown.splitlines()[:SAMPLE_LINES])

                pages.append(PageQuality(
                    url=url,
                    tool=tool,
                    signal=signal,
                    density=density,
                    consensus=consensus,
                    raw_text=raw_sample,
                ))
            quality_results[site][tool] = pages

        total = sum(len(p) for p in quality_results[site].values())
        present = [t for t in TOOLS if quality_results[site].get(t)]
        print(f"  {site}: scored {total} pages across {len(present)} tools")

    return quality_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--run", default=None,
        help="Run directory name under benchmarks/runs/ (default: latest)",
    )
    parser.add_argument(
        "--output", default=str(BENCH_DIR / "QUALITY_COMPARISON.md"),
        help="Output path for the quality report (default: benchmarks/QUALITY_COMPARISON.md)",
    )
    args = parser.parse_args()

    runs_dir = BENCH_DIR / "runs"
    if args.run:
        run_dir = runs_dir / args.run
        if not run_dir.exists():
            sys.exit(f"Run directory not found: {run_dir}")
    else:
        run_dirs = sorted(d for d in runs_dir.iterdir() if d.is_dir()) if runs_dir.exists() else []
        if not run_dirs:
            sys.exit("No run directories found under benchmarks/runs/\n"
                     "Run benchmark_all_tools.py first.")
        run_dir = run_dirs[-1]

    print(f"Scoring quality from run: {run_dir.name}")
    quality_results = score_run(run_dir)

    report = generate_quality_report(quality_results, TOOLS)
    Path(args.output).write_text(report, encoding="utf-8")
    print(f"\nQuality report written to: {args.output}")


if __name__ == "__main__":
    main()
