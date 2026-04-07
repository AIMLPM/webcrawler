#!/usr/bin/env python3
"""Test whether a warmup run improves benchmark stability.

Runs each tool twice on the same site: once cold (no warmup) and once
with a throwaway warmup run before the timed iterations. Compares
medians, standard deviations, and first-iteration outlier effects.

Usage:
    python benchmarks/warmup_validation/test_warmup_impact.py
    python benchmarks/warmup_validation/test_warmup_impact.py --site fastapi-docs --iterations 6
    python benchmarks/warmup_validation/test_warmup_impact.py --tools markcrawl,scrapy+md

Results are printed to stdout and saved to
benchmarks/warmup_validation/results_<timestamp>.txt
"""

from __future__ import annotations

import argparse
import os
import sys
import shutil
import statistics
import tempfile
import time
from pathlib import Path

# Auto-relaunch inside .venv if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_VENV_PYTHON = _REPO_ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python3")
if sys.prefix == sys.base_prefix and _VENV_PYTHON.exists():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "benchmarks"))

from benchmark_all_tools import (
    COMPARISON_SITES,
    TOOLS,
    discover_urls,
    run_single,
)


def run_test(
    tool_name: str,
    site_name: str,
    urls: list[str],
    iterations: int,
    concurrency: int,
) -> dict:
    """Run cold and warm tests, return comparison data."""
    run_fn = TOOLS[tool_name]["run"]
    site_config = COMPARISON_SITES[site_name]
    base_dir = tempfile.mkdtemp(prefix=f"warmup_test_{tool_name}_")

    results = {"tool": tool_name, "site": site_name, "iterations": iterations}

    # --- WITHOUT warmup ---
    cold_times = []
    cold_pages = []
    for i in range(iterations):
        r = run_single(tool_name, run_fn, site_name, site_config, base_dir,
                        url_list=urls, concurrency=concurrency)
        cold_times.append(r.time_seconds)
        cold_pages.append(r.pages)

    results["cold"] = {
        "times": cold_times,
        "pages": cold_pages,
        "median": statistics.median(cold_times),
        "stddev": statistics.stdev(cold_times) if len(cold_times) > 1 else 0,
    }

    # --- WITH warmup ---
    warmup_r = run_single(tool_name, run_fn, site_name, site_config, base_dir,
                           url_list=urls, concurrency=concurrency)
    results["warmup_time"] = warmup_r.time_seconds

    warm_times = []
    warm_pages = []
    for i in range(iterations):
        r = run_single(tool_name, run_fn, site_name, site_config, base_dir,
                        url_list=urls, concurrency=concurrency)
        warm_times.append(r.time_seconds)
        warm_pages.append(r.pages)

    results["warm"] = {
        "times": warm_times,
        "pages": warm_pages,
        "median": statistics.median(warm_times),
        "stddev": statistics.stdev(warm_times) if len(warm_times) > 1 else 0,
    }

    shutil.rmtree(base_dir, ignore_errors=True)

    # Derived metrics
    cold_med = results["cold"]["median"]
    warm_med = results["warm"]["median"]
    results["median_diff_pct"] = abs(cold_med - warm_med) / warm_med * 100 if warm_med > 0 else 0
    results["first_vs_warm_pct"] = abs(cold_times[0] - warm_med) / warm_med * 100 if warm_med > 0 else 0
    cold_std = results["cold"]["stddev"]
    warm_std = results["warm"]["stddev"]
    results["variance_reduction_pct"] = (1 - warm_std / cold_std) * 100 if cold_std > 0 else 0

    return results


def format_results(all_results: list[dict], site_name: str, num_urls: int) -> str:
    """Format results into a readable report."""
    lines = [
        f"Warmup Impact Validation — {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "=" * 60,
        "",
        f"Site: {site_name} ({num_urls} pages)",
        f"Machine: {sys.platform}",
        "",
    ]

    for r in all_results:
        tool = r["tool"]
        cold = r["cold"]
        warm = r["warm"]

        lines.append(f"=== {tool}: WITHOUT warmup ===")
        for i, (t, p) in enumerate(zip(cold["times"], cold["pages"])):
            lines.append(f"  iter {i+1}: {t:.2f}s ({p} pages, {p/t:.1f} p/s)")

        lines.append(f"=== {tool}: WITH warmup ===")
        lines.append(f"  warmup: {r['warmup_time']:.2f}s (discarded)")
        for i, (t, p) in enumerate(zip(warm["times"], warm["pages"])):
            lines.append(f"  iter {i+1}: {t:.2f}s ({p} pages, {p/t:.1f} p/s)")

        lines.append("")
        lines.append(f"--- {tool} comparison ---")
        lines.append(
            f"  Without warmup: median={cold['median']:.2f}s, "
            f"stddev={cold['stddev']:.2f}s, "
            f"first={cold['times'][0]:.2f}s, "
            f"range=[{min(cold['times']):.2f}-{max(cold['times']):.2f}]"
        )
        lines.append(
            f"  With warmup:    median={warm['median']:.2f}s, "
            f"stddev={warm['stddev']:.2f}s, "
            f"first={warm['times'][0]:.2f}s, "
            f"range=[{min(warm['times']):.2f}-{max(warm['times']):.2f}]"
        )
        lines.append(f"  Median difference: {r['median_diff_pct']:.1f}%")
        lines.append(f"  Variance reduction: {r['variance_reduction_pct']:.0f}%")
        lines.append(f"  Cold first iter vs warm median: {r['first_vs_warm_pct']:.1f}%")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Test warmup impact on benchmark stability")
    parser.add_argument("--site", default="books-toscrape",
                        help="Site to test (default: books-toscrape)")
    parser.add_argument("--tools", default="markcrawl,crawl4ai",
                        help="Comma-separated tools to test (default: markcrawl,crawl4ai)")
    parser.add_argument("--iterations", type=int, default=4,
                        help="Timed iterations per condition (default: 4)")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="Concurrency level (default: 5)")
    args = parser.parse_args()

    site_name = args.site
    tool_names = [t.strip() for t in args.tools.split(",")]

    if site_name not in COMPARISON_SITES:
        print(f"Unknown site: {site_name}")
        print(f"Available: {', '.join(COMPARISON_SITES.keys())}")
        sys.exit(1)

    for t in tool_names:
        if t not in TOOLS:
            print(f"Unknown tool: {t}")
            print(f"Available: {', '.join(TOOLS.keys())}")
            sys.exit(1)

    site_config = COMPARISON_SITES[site_name]
    print(f"Discovering URLs for {site_name}...", end=" ", flush=True)
    urls = discover_urls(
        site_name=site_name,
        url=site_config["url"],
        max_pages=site_config["max_pages"],
        skip_patterns=site_config.get("skip_patterns"),
    )
    print(f"{len(urls)} URLs")
    print()

    all_results = []
    for tool_name in tool_names:
        check_fn = TOOLS[tool_name]["check"]
        if not check_fn():
            print(f"Skipping {tool_name} (not available)")
            continue

        print(f"Testing {tool_name} ({args.iterations} iterations per condition)...")
        r = run_test(tool_name, site_name, urls, args.iterations, args.concurrency)
        all_results.append(r)

        # Print summary immediately
        cold_med = r["cold"]["median"]
        warm_med = r["warm"]["median"]
        print(f"  Cold median: {cold_med:.2f}s | Warm median: {warm_med:.2f}s | "
              f"Diff: {r['median_diff_pct']:.1f}% | Variance reduction: {r['variance_reduction_pct']:.0f}%")
        print()

    if not all_results:
        print("No tools available to test.")
        sys.exit(1)

    report = format_results(all_results, site_name, len(urls))
    print("\n" + report)

    # Save results
    out_dir = Path(__file__).parent
    timestamp = time.strftime("%Y-%m-%d_%H%M%S", time.gmtime())
    out_path = out_dir / f"results_{timestamp}.txt"
    with open(out_path, "w") as f:
        f.write(report + "\n")
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
