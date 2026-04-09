#!/usr/bin/env python3
"""MarkCrawl benchmark suite.

Crawls a set of known public sites and measures:
- Performance: pages/second, total time, avg time per page
- Extraction quality: content-to-HTML ratio, junk detection, title extraction
- Output completeness: citation presence, JSONL field completeness

Usage:
    python benchmarks/benchmark_markcrawl.py
    python benchmarks/benchmark_markcrawl.py --sites httpbin,python-docs
    python benchmarks/benchmark_markcrawl.py --output benchmarks/results.md

Results are written to a Markdown report file.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Add parent dir to path so we can import markcrawl
sys.path.insert(0, str(Path(__file__).parent.parent))

from markcrawl.core import crawl

logger = logging.getLogger(__name__)

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
        "expected_min_pages": 3,
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
# Memory measurement
# ---------------------------------------------------------------------------

def _get_memory_mb() -> float:
    """Get current process RSS in MB."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback for systems without psutil
        import resource
        # resource.getrusage returns KB on Linux, bytes on macOS
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)  # macOS: bytes → MB
        return usage / 1024  # Linux: KB → MB


class MemoryTracker:
    """Track peak memory usage in a background thread."""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.peak_mb: float = 0
        self._running = False
        self._thread = None

    def start(self):
        self.peak_mb = _get_memory_mb()
        self._running = True
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        return self.peak_mb

    def _sample(self):
        while self._running:
            current = _get_memory_mb()
            if current > self.peak_mb:
                self.peak_mb = current
            time.sleep(self.interval)


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
    total_output_kb: float = 0.0  # total size of output files in KB
    peak_memory_mb: float = 0.0  # peak RSS during crawl
    junk_details: List[str] = field(default_factory=list)
    title_extraction_rate: float = 0.0  # % of pages with non-empty titles
    citation_present_rate: float = 0.0  # % of JSONL rows with citation field
    jsonl_complete_rate: float = 0.0  # % of JSONL rows with all required fields
    errors: List[str] = field(default_factory=list)


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks so junk detection doesn't flag code examples."""
    return re.sub(r"```[\s\S]*?```", "", text)


def count_junk(text: str) -> tuple[int, list[str]]:
    """Count junk pattern matches in extracted text (excluding code blocks)."""
    # Don't flag <script> or <style> references inside code examples
    text_no_code = _strip_code_blocks(text)
    text_lower = text_no_code.lower()
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
                try:
                    pages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

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
        if all(f in page for f in REQUIRED_JSONL_FIELDS):
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

    logger.info(f"  [{tier}] Crawling {name} ({url}, max={max_pages})...")

    errors = []
    mem_tracker = MemoryTracker(interval=0.5)
    mem_tracker.start()
    start = time.time()
    try:
        result = crawl(
            base_url=url,
            out_dir=out_dir,
            fmt="markdown",
            max_pages=max_pages,
            delay=0,
            timeout=15,
            show_progress=False,
            min_words=5,
        )
        pages_saved = result.pages_saved
    except Exception as exc:
        pages_saved = 0
        errors.append(str(exc))
    peak_mem = mem_tracker.stop()

    elapsed = time.time() - start
    pps = pages_saved / elapsed if elapsed > 0 else 0

    logger.info(f"    {pages_saved} pages in {elapsed:.1f}s ({pps:.1f} p/s)")

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

    # Calculate total output size
    total_bytes = 0
    for f in Path(out_dir).glob("*"):
        if f.is_file():
            total_bytes += f.stat().st_size
    total_kb = total_bytes / 1024

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
        avg_html_to_content_ratio=0,
        total_output_kb=total_kb,
        peak_memory_mb=peak_mem,
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
        "# MarkCrawl Self-Benchmark (MarkCrawl only — no competitors)",
        "",
        "> **Looking for the head-to-head comparison vs Crawl4AI and Scrapy?** See [SPEED_COMPARISON.md](SPEED_COMPARISON.md).",
        "",
        "This report measures MarkCrawl's own performance and extraction quality across test sites.",
        "No other tools are involved — this is a self-assessment of speed, content quality, and output completeness.",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
        "## What this measures",
        "",
        "Each benchmark runs the **full MarkCrawl pipeline** end-to-end:",
        "",
        "```",
        "1. Discover URLs     — fetch robots.txt, parse sitemap or follow links",
        "2. Fetch pages       — HTTP GET each URL (adaptive throttle, delay=0 base)",
        "3. Clean HTML        — strip <nav>, <footer>, <script>, <style>, cookie banners",
        "4. Convert to Markdown — transform cleaned HTML via markdownify",
        "5. Write .md files   — one file per page with citation header",
        "6. Write JSONL index — append url, title, crawled_at, citation, text per page",
        "```",
        "",
        "**Pages/second** includes all six steps — network fetch is typically the",
        "bottleneck, not HTML parsing or Markdown conversion. Benchmarks run with",
        "`delay=0` (adaptive throttle only). MarkCrawl automatically backs off",
        "if the server is slow or returns 429 rate-limit responses.",
        "",
        "Source: [`benchmarks/benchmark_markcrawl.py`](benchmark_markcrawl.py)",
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

        tier_kb = sum(r.total_output_kb for r in tier_results)
        lines.extend([
            f"### {tier_labels.get(tier, tier)} — {tier_pages} pages in {tier_time:.1f}s ({tier_pps:.1f} p/s), {tier_kb:.0f} KB output",
            "",
            "| Site | Description | Pages | Time (s) | Pages/sec | Avg words | Output KB | Peak MB |",
            "|---|---|---|---|---|---|---|---|",
        ])

        for r in tier_results:
            status = " *" if r.errors else ""
            lines.append(
                f"| {r.name}{status} | {r.description} | {r.pages_saved} | "
                f"{r.crawl_time_seconds:.1f} | {r.pages_per_second:.2f} | "
                f"{r.avg_content_words:.0f} | {r.total_output_kb:.0f} | {r.peak_memory_mb:.0f} |"
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
        "python benchmarks/benchmark_markcrawl.py",
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
        default="benchmarks/MARKCRAWL_RESULTS.md",
        help="Output report path (default: benchmarks/MARKCRAWL_RESULTS.md)",
    )
    args = parser.parse_args()

    # Select sites
    if args.sites:
        site_names = [s.strip() for s in args.sites.split(",")]
        sites = {k: v for k, v in BENCHMARK_SITES.items() if k in site_names}
        if not sites:
            logger.error(f"No valid sites found. Available: {', '.join(BENCHMARK_SITES.keys())}")
            sys.exit(1)
    else:
        sites = BENCHMARK_SITES

    logger.info(f"MarkCrawl Benchmark -- {len(sites)} site(s)")
    logger.info("=" * 50)

    # Create temp output directory
    output_base = tempfile.mkdtemp(prefix="markcrawl_bench_")

    results = []
    for name, config in sites.items():
        result = run_site_benchmark(name, config, output_base)
        results.append(result)

    logger.info("")
    logger.info("=" * 50)

    # Generate report
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    generate_report(results, args.output)

    logger.info(f"Report saved to: {args.output}")
    logger.info("")

    # Print summary to stdout
    total_pages = sum(r.pages_saved for r in results)
    total_junk = sum(r.junk_detections for r in results)
    avg_title = sum(r.title_extraction_rate for r in results) / len(results) if results else 0
    avg_citation = sum(r.citation_present_rate for r in results) / len(results) if results else 0

    logger.info(f"Total pages: {total_pages}")
    logger.info(f"Junk detections: {total_junk}")
    logger.info(f"Avg title rate: {avg_title:.0%}")
    logger.info(f"Avg citation rate: {avg_citation:.0%}")

    # Cleanup
    shutil.rmtree(output_base, ignore_errors=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
