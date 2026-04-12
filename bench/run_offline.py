#!/usr/bin/env python3
"""Offline benchmark runner for extraction experiments.

Reads cached HTML fixtures from bench/fixtures/, runs the extraction
pipeline, and outputs quality metrics.  No network access required.

Usage:
    python bench/run_offline.py [--extractor default|trafilatura|ensemble]
    python bench/run_offline.py --compare default ensemble
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from markcrawl.chunker import chunk_markdown
from markcrawl.extract_content import (
    html_to_markdown,
    html_to_markdown_ensemble,
    html_to_markdown_trafilatura,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LOG_FILE = Path(__file__).parent / "experiment_log.jsonl"

EXTRACTORS = {
    "default": html_to_markdown,
    "trafilatura": html_to_markdown_trafilatura,
    "ensemble": html_to_markdown_ensemble,
}


def load_fixtures() -> List[Dict[str, Any]]:
    """Load all HTML fixtures from the fixtures directory."""
    fixtures = []
    for html_file in sorted(FIXTURES_DIR.glob("*.html")):
        fixtures.append({
            "name": html_file.stem,
            "path": str(html_file),
            "html": html_file.read_text(encoding="utf-8"),
        })
    return fixtures


def run_extraction(fixtures: List[Dict], extractor_name: str) -> Dict[str, Any]:
    """Run extraction on all fixtures and return metrics."""
    extractor = EXTRACTORS[extractor_name]
    results = []
    total_start = time.perf_counter()

    for fixture in fixtures:
        start = time.perf_counter()
        title, markdown, links = extractor(fixture["html"])
        elapsed = time.perf_counter() - start

        chunks = chunk_markdown(markdown, max_words=400, overlap_words=50, page_title=title, adaptive=True)

        words = markdown.split()
        word_count = len(words)

        # Nav pollution: count link-reference-style markers in first 100 words
        first_100 = " ".join(words[:100])
        link_refs = len(re.findall(r"\[.*?\]\(.*?\)", first_100))

        # Content structure indicators
        heading_count = len(re.findall(r"^#{1,6}\s+", markdown, re.MULTILINE))
        code_blocks = len(re.findall(r"```", markdown)) // 2
        has_paragraphs = "\n\n" in markdown

        results.append({
            "fixture": fixture["name"],
            "title": title,
            "word_count": word_count,
            "chunk_count": len(chunks),
            "heading_count": heading_count,
            "code_blocks": code_blocks,
            "has_paragraphs": has_paragraphs,
            "link_refs_in_preamble": link_refs,
            "links_found": len(links),
            "extraction_ms": round(elapsed * 1000, 1),
        })

    total_elapsed = time.perf_counter() - total_start

    # Aggregate metrics
    total_words = sum(r["word_count"] for r in results)
    total_chunks = sum(r["chunk_count"] for r in results)
    total_headings = sum(r["heading_count"] for r in results)
    total_code_blocks = sum(r["code_blocks"] for r in results)
    avg_nav_pollution = sum(r["link_refs_in_preamble"] for r in results) / max(len(results), 1)

    return {
        "extractor": extractor_name,
        "fixture_count": len(fixtures),
        "total_words": total_words,
        "total_chunks": total_chunks,
        "chunks_per_page": round(total_chunks / max(len(results), 1), 1),
        "words_per_chunk": round(total_words / max(total_chunks, 1), 1),
        "total_headings": total_headings,
        "total_code_blocks": total_code_blocks,
        "avg_nav_pollution_preamble": round(avg_nav_pollution, 1),
        "total_extraction_ms": round(total_elapsed * 1000, 1),
        "per_page_results": results,
    }


def log_experiment(metrics: Dict[str, Any], label: str = "") -> None:
    """Append an experiment result to the log file."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "label": label,
        **{k: v for k, v in metrics.items() if k != "per_page_results"},
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def print_results(metrics: Dict[str, Any]) -> None:
    """Print a human-readable summary."""
    print(f"\n{'=' * 60}")
    print(f"Extractor: {metrics['extractor']}")
    print(f"{'=' * 60}")
    print(f"Fixtures processed:     {metrics['fixture_count']}")
    print(f"Total words extracted:  {metrics['total_words']}")
    print(f"Total chunks:           {metrics['total_chunks']}")
    print(f"Chunks per page:        {metrics['chunks_per_page']}")
    print(f"Words per chunk:        {metrics['words_per_chunk']}")
    print(f"Headings preserved:     {metrics['total_headings']}")
    print(f"Code blocks preserved:  {metrics['total_code_blocks']}")
    print(f"Avg nav pollution:      {metrics['avg_nav_pollution_preamble']} link refs in first 100 words")
    print(f"Total extraction time:  {metrics['total_extraction_ms']}ms")
    print()

    for r in metrics["per_page_results"]:
        print(f"  {r['fixture']:20s}  {r['word_count']:5d} words  {r['chunk_count']:2d} chunks  "
              f"{r['heading_count']:2d} headings  {r['code_blocks']:2d} code blocks  "
              f"{r['extraction_ms']:6.1f}ms")
    print()


def compare_extractors(names: List[str], fixtures: List[Dict]) -> None:
    """Run multiple extractors and print a comparison table."""
    all_metrics = []
    for name in names:
        if name not in EXTRACTORS:
            print(f"Unknown extractor: {name}. Available: {list(EXTRACTORS.keys())}")
            return
        metrics = run_extraction(fixtures, name)
        all_metrics.append(metrics)
        print_results(metrics)

    # Comparison table
    print(f"\n{'=' * 60}")
    print("COMPARISON")
    print(f"{'=' * 60}")
    header = f"{'Metric':<30s}" + "".join(f"{m['extractor']:>15s}" for m in all_metrics)
    print(header)
    print("-" * len(header))
    for key in ["total_words", "total_chunks", "chunks_per_page", "words_per_chunk",
                 "total_headings", "total_code_blocks", "avg_nav_pollution_preamble",
                 "total_extraction_ms"]:
        row = f"{key:<30s}" + "".join(f"{m[key]:>15}" for m in all_metrics)
        print(row)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline extraction benchmark")
    parser.add_argument("--extractor", default="default", choices=list(EXTRACTORS.keys()))
    parser.add_argument("--compare", nargs="+", metavar="EXTRACTOR",
                        help="Compare multiple extractors side by side")
    parser.add_argument("--log", action="store_true", help="Log results to experiment_log.jsonl")
    parser.add_argument("--label", default="", help="Label for the experiment log entry")
    args = parser.parse_args()

    fixtures = load_fixtures()
    if not fixtures:
        print(f"No HTML fixtures found in {FIXTURES_DIR}/")
        print("Add .html files to bench/fixtures/ to run the benchmark.")
        sys.exit(1)

    if args.compare:
        compare_extractors(args.compare, fixtures)
    else:
        metrics = run_extraction(fixtures, args.extractor)
        print_results(metrics)
        if args.log:
            log_experiment(metrics, label=args.label)
            print(f"Logged to {LOG_FILE}")


if __name__ == "__main__":
    main()
