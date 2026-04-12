#!/usr/bin/env python3
"""Autoresearch loop runner — validates extraction experiments.

This script manages the experiment lifecycle:
1. Capture or load a baseline
2. After a code change, run tests + benchmark
3. Compare to baseline with regression guards
4. Accept or reject the change
5. Log results

Usage:
    # Capture current code as the baseline
    python bench/autoresearch.py --set-baseline

    # Validate a change against the baseline
    python bench/autoresearch.py --validate --label "widened aside keep heuristic"

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

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BENCH_DIR = ROOT / "bench"
BASELINE_FILE = BENCH_DIR / "baseline.json"
LOG_FILE = BENCH_DIR / "experiment_log.jsonl"


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
        print(result.stdout)
        print(result.stderr)
        return False
    # Extract pass count
    for line in result.stdout.splitlines():
        if "passed" in line:
            print(f"  Tests: {line.strip()}")
    return True


def run_benchmark(extractor: str = "default") -> Dict[str, Any]:
    """Run the offline benchmark and return metrics."""
    from bench.run_offline import load_fixtures, run_extraction
    fixtures = load_fixtures()
    if not fixtures:
        print("ERROR: No fixtures found in bench/fixtures/")
        sys.exit(1)
    return run_extraction(fixtures, extractor)


def compute_composite_score(metrics: Dict[str, Any]) -> float:
    """Compute the composite optimization score."""
    total_words = metrics.get("total_words", 0)
    chunks_per_page = max(metrics.get("chunks_per_page", 1), 0.1)
    nav_pollution = metrics.get("avg_nav_pollution_preamble", 0)
    headings = max(metrics.get("total_headings", 1), 1)

    return total_words * (1.0 / chunks_per_page) * (1.0 - nav_pollution / 100.0) * headings


def check_regression_guards(baseline: Dict, candidate: Dict) -> List[str]:
    """Check regression guards. Returns list of violations (empty = OK)."""
    violations = []

    b_nav = baseline.get("avg_nav_pollution_preamble", 0)
    c_nav = candidate.get("avg_nav_pollution_preamble", 0)
    if b_nav > 0 and c_nav > b_nav * 2:
        violations.append(f"Nav pollution {c_nav:.1f} > 2x baseline {b_nav:.1f}")
    elif b_nav == 0 and c_nav > 5:
        violations.append(f"Nav pollution {c_nav:.1f} > 5 (baseline was 0)")

    b_cpp = baseline.get("chunks_per_page", 0)
    c_cpp = candidate.get("chunks_per_page", 0)
    if b_cpp > 0 and c_cpp > b_cpp * 1.2:
        violations.append(f"Chunks/page {c_cpp:.1f} > 1.2x baseline {b_cpp:.1f}")

    b_head = baseline.get("total_headings", 0)
    c_head = candidate.get("total_headings", 0)
    if b_head > 0 and c_head < b_head * 0.9:
        violations.append(f"Headings {c_head} < 0.9x baseline {b_head}")

    b_time = baseline.get("total_extraction_ms", 0)
    c_time = candidate.get("total_extraction_ms", 0)
    if b_time > 0 and c_time > b_time * 3:
        violations.append(f"Extraction time {c_time:.0f}ms > 3x baseline {b_time:.0f}ms")

    return violations


def set_baseline() -> None:
    """Capture current extraction as the baseline."""
    print("Running benchmark to capture baseline...")
    metrics = run_benchmark()
    score = compute_composite_score(metrics)
    baseline = {
        **{k: v for k, v in metrics.items() if k != "per_page_results"},
        "composite_score": score,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2) + "\n")
    print(f"Baseline saved to {BASELINE_FILE}")
    print(f"  Composite score: {score:.1f}")
    print(f"  Words: {baseline['total_words']}, Chunks/page: {baseline['chunks_per_page']}")
    print(f"  Nav pollution: {baseline['avg_nav_pollution_preamble']}, Headings: {baseline['total_headings']}")


def load_baseline() -> Optional[Dict[str, Any]]:
    """Load the saved baseline."""
    if not BASELINE_FILE.exists():
        return None
    return json.loads(BASELINE_FILE.read_text())


def validate_change(label: str = "") -> None:
    """Validate a code change against the baseline."""
    baseline = load_baseline()
    if baseline is None:
        print("No baseline found. Run --set-baseline first.")
        sys.exit(1)

    # Step 1: Run tests
    print("\n--- Step 1: Running tests ---")
    if not run_tests():
        log_experiment(baseline, None, label, "REJECTED", "Tests failed")
        print("\nREJECTED: Tests failed. Revert the change.")
        sys.exit(1)

    # Step 2: Run benchmark
    print("\n--- Step 2: Running benchmark ---")
    metrics = run_benchmark()
    candidate_score = compute_composite_score(metrics)
    baseline_score = baseline.get("composite_score", 0)

    # Step 3: Check regression guards
    print("\n--- Step 3: Checking regression guards ---")
    violations = check_regression_guards(baseline, metrics)
    if violations:
        for v in violations:
            print(f"  VIOLATION: {v}")
        log_experiment(baseline, metrics, label, "REJECTED", f"Regressions: {'; '.join(violations)}")
        print(f"\nREJECTED: Regression guard violation(s). Score: {candidate_score:.1f} (baseline: {baseline_score:.1f})")
        sys.exit(1)

    # Step 4: Compare scores
    delta = candidate_score - baseline_score
    delta_pct = (delta / baseline_score * 100) if baseline_score else 0

    print("\n--- Results ---")
    print(f"  Baseline score:  {baseline_score:.1f}")
    print(f"  Candidate score: {candidate_score:.1f}")
    print(f"  Delta:           {delta:+.1f} ({delta_pct:+.1f}%)")

    if candidate_score > baseline_score:
        log_experiment(baseline, metrics, label, "ACCEPTED", f"+{delta_pct:.1f}%")
        print(f"\nACCEPTED: Score improved by {delta_pct:.1f}%. Update baseline with --set-baseline.")
    elif candidate_score == baseline_score:
        log_experiment(baseline, metrics, label, "NEUTRAL", "No change in score")
        print("\nNEUTRAL: No improvement. Consider reverting to keep the code simple.")
    else:
        log_experiment(baseline, metrics, label, "REJECTED", f"{delta_pct:.1f}%")
        print(f"\nREJECTED: Score decreased by {abs(delta_pct):.1f}%. Revert the change.")
        sys.exit(1)


def log_experiment(baseline: Dict, candidate: Optional[Dict], label: str, status: str, reason: str) -> None:
    """Append experiment to the log."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "label": label,
        "status": status,
        "reason": reason,
        "baseline_score": baseline.get("composite_score", 0),
    }
    if candidate:
        entry["candidate_score"] = compute_composite_score(candidate)
        entry["candidate_words"] = candidate.get("total_words", 0)
        entry["candidate_chunks_per_page"] = candidate.get("chunks_per_page", 0)
        entry["candidate_nav_pollution"] = candidate.get("avg_nav_pollution_preamble", 0)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def show_history() -> None:
    """Print experiment history."""
    if not LOG_FILE.exists():
        print("No experiment history yet.")
        return
    print(f"{'Time':<20s} {'Status':<10s} {'Score':>8s} {'Label'}")
    print("-" * 70)
    for line in LOG_FILE.read_text().splitlines():
        entry = json.loads(line)
        score = entry.get("candidate_score", entry.get("baseline_score", "?"))
        if isinstance(score, float):
            score = f"{score:.1f}"
        print(f"{entry.get('timestamp', '?'):<20s} {entry.get('status', '?'):<10s} {score:>8s} {entry.get('label', '')}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Autoresearch experiment runner")
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
