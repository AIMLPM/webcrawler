#!/usr/bin/env python3
"""MarkCrawl benchmark suite.

Crawls a set of known public sites and measures:
- Performance: pages/second, total time, avg time per page
- Extraction quality: content-to-HTML ratio, junk detection, title extraction
- Output completeness: citation presence, JSONL field completeness

Usage:
    python benchmarks/run_benchmarks.py
    python benchmarks/run_benchmarks.py --sites httpbin,python-docs
    python benchmarks/run_benchmarks.py --output benchmarks/results.md

Results are written to a Markdown report file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Add parent dir to path so we can import markcrawl
sys.path.insert(0, str(Path(__file__).parent.parent))

from markcrawl.core import crawl

# ---------------------------------------------------------------------------
# Benchmark sites — known public sites with predictable content
# ---------------------------------------------------------------------------

BENCHMARK_SITES = {
    # --- SMALL (1-5 pages) — quick validation ---
    "httpbin": {
        "url": "https://httpbin.org",
        "max_pages": 5,
        "description": "Simple HTTP test service (minimal HTML, 1-2 pages)",
        "expected_min_pages": 1,
        "tier": "small",
    },
    "scrapethissite": {
        "url": "https://www.scrapethissite.com",
        "max_pages": 5,
        "description": "Scraping practice site (structured data tables)",
        "expected_min_pages": 1,
        "tier": "small",
    },

    # --- MEDIUM (15-30 pages) — real doc sites ---
    "fastapi-docs": {
        "url": "https://fastapi.tiangolo.com",
        "max_pages": 25,
        "description": "FastAPI framework docs (API docs with code examples, tutorials)",
        "expected_min_pages": 10,
        "tier": "medium",
    },
    "python-docs": {
        "url": "https://docs.python.org/3/library/",
        "max_pages": 20,
        "description": "Python standard library index + module pages",
        "expected_min_pages": 10,
        "tier": "medium",
    },
    "quotes-toscrape": {
        "url": "http://quotes.toscrape.com",
        "max_pages": 15,
        "description": "Paginated quotes (tests link-following across 10+ pages)",
        "expected_min_pages": 10,
        "tier": "medium",
    },

    # --- LARGE (50-100 pages) — scale test ---
    "books-toscrape": {
        "url": "http://books.toscrape.com",
        "max_pages": 60,
        "description": "E-commerce catalog (50+ product pages, pagination, categories)",
        "expected_min_pages": 30,
        "tier": "large",
    },
    "quotes-toscrape-large": {
        "url": "http://quotes.toscrape.com",
        "max_pages": 100,
        "description": "Paginated quotes (100 page deep crawl, link-following stress test)",
        "expected_min_pages": 50,
        "tier": "large",
    },
}


# ---------------------------------------------------------------------------
# Quality metrics
# ---------------------------------------------------------------------------

# Common junk patterns that should NOT appear in extracted content
JUNK_PATTERNS = [
    r"<script",
    r"<style",
    r"<nav[\s>]",
    r"<footer[\s>]",
    r"<header[\s>]",
    r"cookie.?banner",
    r"cookie.?consent",
    r"accept.?cookies",
    r"privacy policy",
    r"©\s*\d{4}.*all rights reserved",  # copyright + all rights reserved together
    r"all rights reserved",
    r"subscribe to our newsletter",
    r"follow us on",
]

REQUIRED_JSONL_FIELDS = ["url", "title", "path", "crawled_at", "citation", "tool", "text"]


@dataclass
class SiteResult:
    name: str
    url: str
    description: str
    tier: str
    pages_saved: int
    expected_min_pages: int
    crawl_time_seconds: float
    pages_per_second: float
    avg_content_words: float
    avg_html_to_content_ratio: float  # content words / raw HTML words — higher is better
    junk_detections: int  # count of junk patterns found across all pages
    junk_details: List[str] = field(default_factory=list)
    title_extraction_rate: float = 0.0  # % of pages with non-empty titles
    citation_present_rate: float = 0.0  # % of JSONL rows with citation field
    jsonl_complete_rate: float = 0.0  # % of JSONL rows with all required fields
    errors: List[str] = field(default_factory=list)


def count_junk(text: str) -> tuple[int, list[str]]:
    """Count junk pattern matches in extracted text."""
    text_lower = text.lower()
    count = 0
    details = []
    for pattern in JUNK_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            count += len(matches)
            details.append(f"{pattern}: {len(matches)} match(es)")
    return count, details


def analyze_jsonl(jsonl_path: str) -> dict:
    """Analyze a pages.jsonl file for quality metrics."""
    pages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))

    if not pages:
        return {
            "pages": [],
            "avg_content_words": 0,
            "avg_html_ratio": 0,
            "total_junk": 0,
            "junk_details": [],
            "title_rate": 0,
            "citation_rate": 0,
            "complete_rate": 0,
        }

    total_words = 0
    total_junk = 0
    all_junk_details = []
    titles_present = 0
    citations_present = 0
    complete_rows = 0

    for page in pages:
        text = page.get("text", "")
        words = len(text.split())
        total_words += words

        # Junk detection
        junk_count, junk_detail = count_junk(text)
        total_junk += junk_count
        all_junk_details.extend(junk_detail)

        # Title extraction
        if page.get("title", "").strip():
            titles_present += 1

        # Citation presence
        if page.get("citation", "").strip():
            citations_present += 1

        # Field completeness
        if all(page.get(f) for f in REQUIRED_JSONL_FIELDS):
            complete_rows += 1

    n = len(pages)
    return {
        "pages": pages,
        "avg_content_words": total_words / n if n else 0,
        "total_junk": total_junk,
        "junk_details": all_junk_details,
        "title_rate": titles_present / n if n else 0,
        "citation_rate": citations_present / n if n else 0,
        "complete_rate": complete_rows / n if n else 0,
    }


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_site_benchmark(name: str, config: dict, output_base: str) -> SiteResult:
    """Run benchmark for a single site."""
    out_dir = os.path.join(output_base, name)
    os.makedirs(out_dir, exist_ok=True)

    url = config["url"]
    max_pages = config["max_pages"]
    description = config["description"]
    expected_min = config["expected_min_pages"]
    tier = config.get("tier", "small")

    print(f"  [{tier}] Crawling {name} ({url}, max={max_pages})...", end=" ", flush=True)

    errors = []
    start = time.time()
    try:
        result = crawl(
            base_url=url,
            out_dir=out_dir,
            fmt="markdown",
            max_pages=max_pages,
            delay=0.3,
            timeout=15,
            show_progress=False,
            min_words=5,
        )
        pages_saved = result.pages_saved
    except Exception as exc:
        pages_saved = 0
        errors.append(str(exc))

    elapsed = time.time() - start
    pps = pages_saved / elapsed if elapsed > 0 else 0

    print(f"{pages_saved} pages in {elapsed:.1f}s ({pps:.1f} p/s)")

    # Analyze output quality
    jsonl_path = os.path.join(out_dir, "pages.jsonl")
    if os.path.isfile(jsonl_path):
        analysis = analyze_jsonl(jsonl_path)
    else:
        analysis = {
            "avg_content_words": 0,
            "total_junk": 0,
            "junk_details": [],
            "title_rate": 0,
            "citation_rate": 0,
            "complete_rate": 0,
        }
        if not errors:
            errors.append("No pages.jsonl produced")

    return SiteResult(
        name=name,
        url=url,
        description=description,
        tier=tier,
        pages_saved=pages_saved,
        expected_min_pages=expected_min,
        crawl_time_seconds=elapsed,
        pages_per_second=pps,
        avg_content_words=analysis["avg_content_words"],
        avg_html_to_content_ratio=0,  # Would need raw HTML size to compute
        junk_detections=analysis["total_junk"],
        junk_details=analysis["junk_details"],
        title_extraction_rate=analysis["title_rate"],
        citation_present_rate=analysis["citation_rate"],
        jsonl_complete_rate=analysis["complete_rate"],
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(results: List[SiteResult], output_path: str) -> str:
    """Generate a Markdown benchmark report."""
    lines = [
        "# MarkCrawl Benchmark Results",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
        "## Summary",
        "",
    ]

    # Summary table
    total_pages = sum(r.pages_saved for r in results)
    total_time = sum(r.crawl_time_seconds for r in results)
    total_junk = sum(r.junk_detections for r in results)
    avg_title_rate = sum(r.title_extraction_rate for r in results) / len(results) if results else 0
    avg_citation_rate = sum(r.citation_present_rate for r in results) / len(results) if results else 0
    avg_complete_rate = sum(r.jsonl_complete_rate for r in results) / len(results) if results else 0

    lines.extend([
        f"- **Sites tested:** {len(results)}",
        f"- **Total pages crawled:** {total_pages}",
        f"- **Total time:** {total_time:.1f}s",
        f"- **Overall pages/second:** {total_pages / total_time:.2f}" if total_time > 0 else "- **Overall pages/second:** N/A",
        "",
        "## Performance",
        "",
    ])

    # Group by tier
    tiers = ["small", "medium", "large"]
    tier_labels = {"small": "Small (1-5 pages)", "medium": "Medium (15-30 pages)", "large": "Large (50-100 pages)"}

    for tier in tiers:
        tier_results = [r for r in results if r.tier == tier]
        if not tier_results:
            continue
        tier_pages = sum(r.pages_saved for r in tier_results)
        tier_time = sum(r.crawl_time_seconds for r in tier_results)
        tier_pps = tier_pages / tier_time if tier_time > 0 else 0

        lines.extend([
            f"### {tier_labels.get(tier, tier)} — {tier_pages} pages in {tier_time:.1f}s ({tier_pps:.1f} p/s)",
            "",
            "| Site | Description | Pages | Time (s) | Pages/sec | Avg words |",
            "|---|---|---|---|---|---|",
        ])

        for r in tier_results:
            status = " *" if r.errors else ""
            lines.append(
                f"| {r.name}{status} | {r.description} | {r.pages_saved} | "
                f"{r.crawl_time_seconds:.1f} | {r.pages_per_second:.2f} | {r.avg_content_words:.0f} |"
            )
        lines.append("")

    lines.extend([
        "",
        "## Extraction Quality",
        "",
        "| Site | Junk detected | Title rate | Citation rate | JSONL complete |",
        "|---|---|---|---|---|",
    ])

    for r in results:
        lines.append(
            f"| {r.name} | {r.junk_detections} | {r.title_extraction_rate:.0%} | "
            f"{r.citation_present_rate:.0%} | {r.jsonl_complete_rate:.0%} |"
        )

    # Quality score
    lines.extend([
        "",
        "## Quality Scores",
        "",
        "| Metric | Score | Target | Status |",
        "|---|---|---|---|",
        f"| Title extraction rate | {avg_title_rate:.0%} | >90% | {'PASS' if avg_title_rate > 0.9 else 'NEEDS WORK'} |",
        f"| Citation completeness | {avg_citation_rate:.0%} | 100% | {'PASS' if avg_citation_rate >= 1.0 else 'NEEDS WORK'} |",
        f"| JSONL field completeness | {avg_complete_rate:.0%} | 100% | {'PASS' if avg_complete_rate >= 1.0 else 'NEEDS WORK'} |",
        f"| Junk in output | {total_junk} matches | 0 | {'PASS' if total_junk == 0 else 'NEEDS WORK'} |",
        f"| Min pages crawled | {'all met' if all(r.pages_saved >= r.expected_min_pages for r in results) else 'some failed'} | all sites | {'PASS' if all(r.pages_saved >= r.expected_min_pages for r in results) else 'NEEDS WORK'} |",
    ])

    # Errors
    error_results = [r for r in results if r.errors]
    if error_results:
        lines.extend(["", "## Errors", ""])
        for r in error_results:
            lines.append(f"### {r.name}")
            for err in r.errors:
                lines.append(f"- {err}")
            lines.append("")

    # Junk details
    junk_results = [r for r in results if r.junk_details]
    if junk_results:
        lines.extend(["", "## Junk Detection Details", ""])
        for r in junk_results:
            lines.append(f"### {r.name}")
            for detail in r.junk_details[:10]:  # limit to 10
                lines.append(f"- {detail}")
            lines.append("")

    lines.extend([
        "",
        "## What these metrics mean",
        "",
        "- **Pages/sec**: Crawl throughput (higher is better). Affected by network, server response time, and `--delay`.",
        "- **Avg words/page**: Average extracted content size. Very low values may indicate extraction issues.",
        "- **Junk detected**: Count of navigation, footer, script, or cookie text found in extracted Markdown. Should be 0.",
        "- **Title rate**: Percentage of pages where a `<title>` was successfully extracted.",
        "- **Citation rate**: Percentage of JSONL rows with a complete citation string.",
        "- **JSONL complete**: Percentage of JSONL rows with all required fields (url, title, path, crawled_at, citation, tool, text).",
        "",
        "## Reproducing these results",
        "",
        "```bash",
        "pip install markcrawl",
        "python benchmarks/run_benchmarks.py",
        "```",
    ])

    report = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run MarkCrawl benchmarks")
    parser.add_argument(
        "--sites",
        default=None,
        help="Comma-separated site names to test (default: all). Available: " + ", ".join(BENCHMARK_SITES.keys()),
    )
    parser.add_argument(
        "--output",
        default="benchmarks/RESULTS.md",
        help="Output report path (default: benchmarks/RESULTS.md)",
    )
    args = parser.parse_args()

    # Select sites
    if args.sites:
        site_names = [s.strip() for s in args.sites.split(",")]
        sites = {k: v for k, v in BENCHMARK_SITES.items() if k in site_names}
        if not sites:
            print(f"No valid sites found. Available: {', '.join(BENCHMARK_SITES.keys())}")
            sys.exit(1)
    else:
        sites = BENCHMARK_SITES

    print(f"MarkCrawl Benchmark — {len(sites)} site(s)")
    print("=" * 50)

    # Create temp output directory
    output_base = tempfile.mkdtemp(prefix="markcrawl_bench_")

    results = []
    for name, config in sites.items():
        result = run_site_benchmark(name, config, output_base)
        results.append(result)

    print()
    print("=" * 50)

    # Generate report
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    generate_report(results, args.output)

    print(f"Report saved to: {args.output}")
    print()

    # Print summary to stdout
    total_pages = sum(r.pages_saved for r in results)
    total_junk = sum(r.junk_detections for r in results)
    avg_title = sum(r.title_extraction_rate for r in results) / len(results) if results else 0
    avg_citation = sum(r.citation_present_rate for r in results) / len(results) if results else 0

    print(f"Total pages: {total_pages}")
    print(f"Junk detections: {total_junk}")
    print(f"Avg title rate: {avg_title:.0%}")
    print(f"Avg citation rate: {avg_citation:.0%}")

    # Cleanup
    shutil.rmtree(output_base, ignore_errors=True)


if __name__ == "__main__":
    main()
