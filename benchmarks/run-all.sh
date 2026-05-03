#!/usr/bin/env bash
# Markcrawl v3 benchmark runner.
#
# Invokes B1 (CLI parity) + B2 (backoff timing), prints a one-screen summary,
# and writes the consolidated baseline JSON to:
#   benchmarks/baseline-results-<source-version>.json
#
# B3 (designlens integration) is design-only — see b3_designlens_integration.md.
#
# Exit code: 0 if every executable benchmark PASSes (or SOFT_PASSes for B1).
#            1 if any benchmark FAILs.
#
# Env:
#   PYTHON  python interpreter to use (default: ../.venv/bin/python if present,
#                                      else: python3)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BENCH_DIR="$REPO_ROOT/benchmarks"

# Choose Python: prefer the project venv, fall back to system python3.
if [ -z "${PYTHON:-}" ]; then
  if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
  else
    PYTHON="python3"
  fi
fi

# Read the source version so we can name the baseline file deterministically.
VERSION="$(
  "$PYTHON" -c "import tomllib,sys; print(tomllib.load(open('$REPO_ROOT/pyproject.toml','rb'))['project']['version'])"
)"
BASELINE_FILE="$BENCH_DIR/baseline-results-v${VERSION}.json"

B1_OUT="$(mktemp -t b1-XXXXXX.json)"
B2_OUT="$(mktemp -t b2-XXXXXX.json)"
trap 'rm -f "$B1_OUT" "$B2_OUT"' EXIT

echo "=========================================================="
echo " markcrawl v${VERSION} benchmark suite"
echo " python: $PYTHON"
echo "=========================================================="
echo

echo "------ B1: source_vs_binary_parity ------"
"$PYTHON" "$BENCH_DIR/b1_cli_parity.py" --json-out "$B1_OUT"
B1_EXIT=$?
echo

echo "------ B2: backoff_timing_compliance ------"
"$PYTHON" "$BENCH_DIR/b2_backoff_timing.py" --json-out "$B2_OUT"
B2_EXIT=$?
echo

echo "------ B3: designlens_no_fallback ------"
echo "DESIGN_ONLY — see benchmarks/b3_designlens_integration.md"
echo "(executable run gated on PyPI publish of v${VERSION} + designlens setup)"
echo

# Build the consolidated baseline JSON. Wrap each result in a top-level
# envelope keyed by benchmark id so historical baselines remain greppable.
"$PYTHON" - <<PY
import json, pathlib, sys

b1 = json.loads(pathlib.Path("$B1_OUT").read_text())
b2 = json.loads(pathlib.Path("$B2_OUT").read_text())

baseline = {
    "source_version": "$VERSION",
    "captured_by": "benchmarks/run-all.sh",
    "benchmarks": {
        "b1_cli_parity": b1,
        "b2_backoff_timing": b2,
        "b3_designlens_no_fallback": {
            "benchmark": "b3_designlens_no_fallback",
            "result": "DESIGN_ONLY",
            "notes": "executable run gated on PyPI publish + designlens setup; see b3_designlens_integration.md",
        },
    },
}
out = pathlib.Path("$BASELINE_FILE")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(baseline, indent=2) + "\n")
print(f"Wrote baseline: {out}")
PY

echo
echo "=========================================================="
echo " Summary"
echo "=========================================================="
"$PYTHON" - <<PY
import json, pathlib
data = json.loads(pathlib.Path("$BASELINE_FILE").read_text())
def _row(name, env):
    res = env.get("result", "?")
    extra = ""
    if name == "b1_cli_parity":
        extra = f"  diff_lines={env.get('diff_line_count', '?')}"
    elif name == "b2_backoff_timing":
        extra = (
            f"  compliant={env.get('percent_compliant', '?')}%"
            f"  samples={env.get('total_retries_sampled', '?')}"
        )
    print(f"  {name:30s}  {res:11s}{extra}")
for k, v in data["benchmarks"].items():
    _row(k, v)
PY

# B1 SOFT_PASS counts as success. B3 DESIGN_ONLY does not block.
OVERALL=0
if [ "$B1_EXIT" -ne 0 ]; then OVERALL=1; fi
if [ "$B2_EXIT" -ne 0 ]; then OVERALL=1; fi

echo
if [ "$OVERALL" -eq 0 ]; then
  echo "OVERALL: PASS  (baseline written to $BASELINE_FILE)"
else
  echo "OVERALL: FAIL  (baseline written to $BASELINE_FILE)"
fi
exit "$OVERALL"
