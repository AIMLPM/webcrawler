#!/usr/bin/env python3
"""Autoresearch loop runner — validates extraction experiments against MRR.

This script manages the experiment lifecycle:
1. Capture or load a baseline (MRR + extraction diagnostics)
2. After a code change, run tests + MRR eval + offline benchmark
3. Compare to baseline with regression guards
4. Accept or reject the change
5. Log results

Usage:
    # Capture current code as the baseline
    python bench/autoresearch.py --set-baseline

    # Validate a change against the baseline
    python bench/autoresearch.py --validate --label "never split inside code blocks"

    # View experiment history
    python bench/autoresearch.py --history
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BENCH_DIR = ROOT / "bench"
BASELINE_FILE = BENCH_DIR / "baseline.json"
LOG_FILE = BENCH_DIR / "experiment_log.jsonl"

# MRR is the primary signal. Any decrease beyond this band rejects the change.
MRR_NOISE_BAND = 0.005

# Chunk size used for MRR evaluation — matches the upstream benchmark
MRR_MAX_WORDS = 128


def run_tests() -> bool:
    """Run the test suite. Returns True if all tests pass."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("TESTS FAILED:")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return False
    for line in result.stdout.splitlines():
        if "passed" in line:
            print(f"  Tests: {line.strip()}")
    return True


def run_mrr() -> Dict[str, Any]:
    """Run the MRR eval harness and return results."""
    from bench.eval_mrr import run_eval
    return run_eval(extractor_name="default", provider="local", max_words=MRR_MAX_WORDS)


def run_diagnostics() -> Dict[str, Any]:
    """Run the offline benchmark for diagnostic metrics (nav pollution, time, chunks)."""
    from bench.run_offline import load_fixtures, run_extraction
    fixtures = load_fixtures()
    if not fixtures:
        print("ERROR: No fixtures found in bench/fixtures/")
        sys.exit(1)
    return run_extraction(fixtures, "default")


def check_regression_guards(baseline: Dict, candidate: Dict) -> List[str]:
    """Check regression guards. Returns list of violations (empty = OK)."""
    violations = []

    b_mrr = baseline.get("overall_mrr", 0.0)
    c_mrr = candidate.get("overall_mrr", 0.0)
    if c_mrr < b_mrr - MRR_NOISE_BAND:
        violations.append(f"MRR {c_mrr:.4f} < baseline {b_mrr:.4f} - {MRR_NOISE_BAND}")

    b_miss = baseline.get("extraction_misses", 0)
    c_miss = candidate.get("extraction_misses", 0)
    if c_miss > b_miss:
        violations.append(
            f"Extraction misses {c_miss} > baseline {b_miss} "
            "(answer spans dropped from output — content signal tradeoff failed)"
        )

    b_nav = baseline.get("avg_nav_pollution_preamble", 0)
    c_nav = candidate.get("avg_nav_pollution_preamble", 0)
    nav_ceiling = max(2.0, b_nav * 2.0)
    if c_nav > nav_ceiling:
        violations.append(f"Nav pollution {c_nav:.1f} > ceiling {nav_ceiling:.1f}")

    b_time = baseline.get("total_extraction_ms", 0)
    c_time = candidate.get("total_extraction_ms", 0)
    if b_time > 0 and c_time > b_time * 1.5:
        violations.append(f"Extraction time {c_time:.0f}ms > 1.5x baseline {b_time:.0f}ms")

    b_cpp = baseline.get("chunks_per_page", 0)
    c_cpp = candidate.get("chunks_per_page", 0)
    if b_cpp > 0 and c_cpp > b_cpp * 1.5:
        violations.append(f"Chunks/page {c_cpp:.1f} > 1.5x baseline {b_cpp:.1f}")

    return violations


def capture_metrics() -> Dict[str, Any]:
    """Run MRR + diagnostics and merge into a single baseline-shaped dict."""
    print("  Running MRR eval...")
    mrr_results = run_mrr()
    print(f"    overall_mrr={mrr_results['overall_mrr']}  "
          f"extraction_misses={mrr_results['extraction_misses']}/{mrr_results['total_queries']}")

    print("  Running diagnostics...")
    diag = run_diagnostics()
    print(f"    nav_pollution={diag['avg_nav_pollution_preamble']}  "
          f"chunks/page={diag['chunks_per_page']}  "
          f"extract_ms={diag['total_extraction_ms']}")

    return {
        "overall_mrr": mrr_results["overall_mrr"],
        "extraction_misses": mrr_results["extraction_misses"],
        "total_queries": mrr_results["total_queries"],
        "per_fixture_mrr": {f["fixture"]: f["mrr"] for f in mrr_results["per_fixture"]},
        "total_words": diag["total_words"],
        "total_chunks": diag["total_chunks"],
        "chunks_per_page": diag["chunks_per_page"],
        "total_headings": diag["total_headings"],
        "total_code_blocks": diag["total_code_blocks"],
        "avg_nav_pollution_preamble": diag["avg_nav_pollution_preamble"],
        "total_extraction_ms": diag["total_extraction_ms"],
    }


def set_baseline() -> None:
    """Capture current extraction as the baseline."""
    print("\n--- Capturing baseline ---")
    metrics = capture_metrics()
    baseline = {
        **metrics,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2) + "\n")
    print(f"\nBaseline saved to {BASELINE_FILE}")
    print(f"  MRR: {baseline['overall_mrr']}  "
          f"misses: {baseline['extraction_misses']}/{baseline['total_queries']}  "
          f"nav: {baseline['avg_nav_pollution_preamble']}")


def load_baseline() -> Optional[Dict[str, Any]]:
    if not BASELINE_FILE.exists():
        return None
    return json.loads(BASELINE_FILE.read_text())


def validate_change(label: str = "") -> None:
    baseline = load_baseline()
    if baseline is None:
        print("No baseline found. Run --set-baseline first.")
        sys.exit(1)

    print("\n--- Step 1: Running tests ---")
    if not run_tests():
        log_experiment(baseline, None, label, "REJECTED", "Tests failed")
        print("\nREJECTED: Tests failed. Revert the change.")
        sys.exit(1)

    print("\n--- Step 2: Capturing candidate metrics ---")
    candidate = capture_metrics()

    print("\n--- Step 3: Checking regression guards ---")
    violations = check_regression_guards(baseline, candidate)
    if violations:
        for v in violations:
            print(f"  VIOLATION: {v}")
        log_experiment(baseline, candidate, label, "REJECTED", f"Regressions: {'; '.join(violations)}")
        print(f"\nREJECTED: Regression guard violation(s). "
              f"MRR: {candidate['overall_mrr']:.4f} (baseline: {baseline['overall_mrr']:.4f})")
        sys.exit(1)

    b_mrr = baseline["overall_mrr"]
    c_mrr = candidate["overall_mrr"]
    delta = c_mrr - b_mrr
    delta_pct = (delta / b_mrr * 100) if b_mrr else 0.0

    print("\n--- Results ---")
    print(f"  Baseline MRR:  {b_mrr:.4f}")
    print(f"  Candidate MRR: {c_mrr:.4f}")
    print(f"  Delta:         {delta:+.4f} ({delta_pct:+.2f}%)")
    for fixture, fixture_mrr in candidate["per_fixture_mrr"].items():
        b_fix = baseline["per_fixture_mrr"].get(fixture, 0.0)
        marker = "↑" if fixture_mrr > b_fix else ("↓" if fixture_mrr < b_fix else "=")
        print(f"    {fixture:<18s}  {b_fix:.4f} → {fixture_mrr:.4f}  {marker}")

    if c_mrr > b_mrr + MRR_NOISE_BAND:
        log_experiment(baseline, candidate, label, "ACCEPTED", f"MRR {delta:+.4f}")
        print(f"\nACCEPTED: MRR improved by {delta:+.4f}. Update baseline with --set-baseline.")
    elif abs(delta) <= MRR_NOISE_BAND:
        log_experiment(baseline, candidate, label, "NEUTRAL", f"MRR {delta:+.4f} within noise band")
        print(f"\nNEUTRAL: MRR change {delta:+.4f} within noise band ({MRR_NOISE_BAND}). "
              "Prefer reverting to keep the code simple.")
    else:
        log_experiment(baseline, candidate, label, "REJECTED", f"MRR {delta:+.4f}")
        print(f"\nREJECTED: MRR decreased by {abs(delta):.4f}. Revert the change.")


def log_experiment(baseline: Dict, candidate: Optional[Dict], label: str, status: str, reason: str) -> None:
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "label": label,
        "status": status,
        "reason": reason,
        "baseline_mrr": baseline.get("overall_mrr", 0.0),
    }
    if candidate:
        entry.update({
            "candidate_mrr": candidate.get("overall_mrr", 0.0),
            "candidate_extraction_misses": candidate.get("extraction_misses", 0),
            "candidate_chunks_per_page": candidate.get("chunks_per_page", 0),
            "candidate_nav_pollution": candidate.get("avg_nav_pollution_preamble", 0),
            "candidate_extraction_ms": candidate.get("total_extraction_ms", 0),
        })
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def show_history() -> None:
    if not LOG_FILE.exists():
        print("No experiment history yet.")
        return
    print(f"{'Time':<20s} {'Status':<10s} {'MRR':>8s} {'Δ':>9s}  {'Label'}")
    print("-" * 90)
    for line in LOG_FILE.read_text().splitlines():
        entry = json.loads(line)
        mrr = entry.get("candidate_mrr", entry.get("baseline_mrr", "?"))
        base = entry.get("baseline_mrr", 0.0)
        if isinstance(mrr, float):
            delta = mrr - base if isinstance(base, (int, float)) else 0.0
            mrr_s = f"{mrr:.4f}"
            delta_s = f"{delta:+.4f}"
        else:
            mrr_s = str(mrr)
            delta_s = ""
        print(f"{entry.get('timestamp', '?'):<20s} {entry.get('status', '?'):<10s} "
              f"{mrr_s:>8s} {delta_s:>9s}  {entry.get('label', '')}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Autoresearch experiment runner (MRR-driven)")
    parser.add_argument("--set-baseline", action="store_true", help="Capture current code as baseline")
    parser.add_argument("--validate", action="store_true", help="Validate a change against baseline")
    parser.add_argument("--label", default="", help="Label for this experiment")
    parser.add_argument("--history", action="store_true", help="Show experiment history")
    args = parser.parse_args()

    if args.set_baseline:
        set_baseline()
    elif args.validate:
        validate_change(label=args.label)
    elif args.history:
        show_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
