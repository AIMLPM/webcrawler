#!/usr/bin/env python3
"""Cross-report data consistency checker.

Validates that key numbers (speed rankings, chunks/page, answer quality,
annual costs) are consistent across README, SPEED_COMPARISON.md,
COST_AT_SCALE.md, and ANSWER_QUALITY.md.

Run before committing any report changes:

    python benchmarks/self_improvement/check_cross_report_consistency.py

Exit code 0 = all checks pass. Non-zero = mismatches found.

Implements the automation recommended after the Spec 05 audit found that
README data inconsistencies were the only CRITICAL finding — and Spec 05
was entirely manual at that time.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARKS = ROOT / "benchmarks"
README = ROOT / "README.md"

failures = []
passes = []


def check(check_id: str, description: str, passed: bool, detail: str = ""):
    if passed:
        passes.append(f"  PASS  {check_id}: {description}")
    else:
        msg = f"  FAIL  {check_id}: {description}"
        if detail:
            msg += f" -- {detail}"
        failures.append(msg)


# ---------------------------------------------------------------------------
# Markdown table parsing
# ---------------------------------------------------------------------------

def parse_md_table(text: str, header_pattern: str) -> list[dict[str, str]]:
    """Find the first markdown table whose header matches *header_pattern*
    and return rows as list-of-dicts keyed by column header."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.search(header_pattern, line, re.IGNORECASE) and "|" in line:
            # Header row
            headers = [h.strip().strip("*") for h in line.split("|")[1:-1]]
            # Skip separator row
            if i + 2 >= len(lines):
                return []
            rows = []
            for row_line in lines[i + 2:]:
                if not row_line.strip().startswith("|"):
                    break
                cells = [c.strip().strip("*") for c in row_line.split("|")[1:-1]]
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
            return rows
    return []


def clean_tool_name(name: str) -> str:
    """Normalize tool name: strip bold markers and whitespace."""
    return name.strip().strip("*").strip()


def clean_number(val: str) -> float | None:
    """Extract a float from a table cell, stripping $, commas, %, bold."""
    val = val.strip().strip("*").strip()
    val = val.replace("$", "").replace(",", "").replace("%", "")
    val = val.replace("--", "").replace("—", "").strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def get_readme_benchmark_table(text: str) -> list[dict]:
    """Extract the RAG answer quality table from the README <details> section."""
    # Find the benchmark details section
    details_start = text.find("How it compares")
    if details_start < 0:
        return []
    section = text[details_start:]
    details_end = section.find("</details>")
    if details_end > 0:
        section = section[:details_end]
    return parse_md_table(section, r"Tool.*Chunks/page")


def get_readme_speed_claims(text: str) -> dict[str, float]:
    """Extract speed claims like 'scrapy+md is fastest (9.1 pages/sec)'."""
    results = {}
    # The unit "pages/sec" may only appear on the first mention
    pattern = r"(\w[\w+\-]*)\s+(?:is fastest|second|third|fourth|fifth|sixth|seventh|slowest)[^(]*\(([\d.]+)"
    for m in re.finditer(pattern, text):
        tool = clean_tool_name(m.group(1))
        results[tool] = float(m.group(2))
    return results


def get_speed_summary(text: str) -> list[dict]:
    """Parse the overall summary table from SPEED_COMPARISON.md."""
    return parse_md_table(text, r"Tool.*Total pages.*Avg pages/sec")


def get_cost_source_data(text: str) -> list[dict]:
    """Parse the source data table from COST_AT_SCALE.md."""
    return parse_md_table(text, r"Tool.*Chunks/page.*Answer quality")


def get_cost_scenario_b(text: str) -> list[dict]:
    """Parse Scenario B table (100K pages, 1K q/day) from COST_AT_SCALE.md."""
    # Find Scenario B section
    marker = "Scenario B"
    pos = text.find(marker)
    if pos < 0:
        return []
    section = text[pos:]
    return parse_md_table(section, r"Tool.*Total/yr")


def get_answer_quality_summary(text: str) -> list[dict]:
    """Parse the summary table from ANSWER_QUALITY.md."""
    return parse_md_table(text, r"Tool.*Overall.*Queries")


# ---------------------------------------------------------------------------
# Comparison checks
# ---------------------------------------------------------------------------

def check_readme_vs_speed():
    """Verify README speed claims match SPEED_COMPARISON.md."""
    readme = load_file(README)
    speed = load_file(BENCHMARKS / "SPEED_COMPARISON.md")

    speed_table = get_speed_summary(speed)
    if not speed_table:
        check("X1", "SPEED_COMPARISON.md has summary table", False, "table not found")
        return

    # Build lookup: tool -> pages/sec from speed report
    speed_lookup = {}
    speed_ranking = []
    for row in speed_table:
        tool = clean_tool_name(row.get("Tool", ""))
        pps = clean_number(row.get("Avg pages/sec", ""))
        if tool and pps is not None:
            speed_lookup[tool] = pps
            speed_ranking.append(tool)

    # Check README speed claims
    readme_speeds = get_readme_speed_claims(readme)
    if not readme_speeds:
        check("X1", "README has speed claims", False, "no speed claims found")
        return

    for tool, readme_pps in readme_speeds.items():
        report_pps = speed_lookup.get(tool)
        if report_pps is None:
            check(f"X1-{tool}", f"README speed for {tool} exists in report",
                  False, f"{tool} not found in SPEED_COMPARISON.md")
        else:
            check(f"X1-{tool}", f"README speed for {tool} matches report",
                  abs(readme_pps - report_pps) < 0.15,
                  f"README={readme_pps}, report={report_pps}")


def check_readme_vs_cost():
    """Verify README chunks/page and annual cost match COST_AT_SCALE.md."""
    readme = load_file(README)
    cost = load_file(BENCHMARKS / "COST_AT_SCALE.md")

    readme_table = get_readme_benchmark_table(readme)
    if not readme_table:
        check("X2", "README has benchmark table", False, "table not found")
        return

    # Chunks/page from COST source data
    source_data = get_cost_source_data(cost)
    source_lookup = {}
    for row in source_data:
        tool = clean_tool_name(row.get("Tool", ""))
        cpp = clean_number(row.get("Chunks/page", ""))
        if tool and cpp is not None:
            source_lookup[tool] = cpp

    # Annual cost from Scenario B
    scenario_b = get_cost_scenario_b(cost)
    cost_lookup = {}
    for row in scenario_b:
        tool = clean_tool_name(row.get("Tool", ""))
        total = clean_number(row.get("Total/yr", ""))
        if tool and total is not None:
            cost_lookup[tool] = total

    for row in readme_table:
        tool = clean_tool_name(row.get("Tool", ""))
        if not tool:
            continue

        # Check chunks/page
        readme_cpp = clean_number(row.get("Chunks/page", ""))
        source_cpp = source_lookup.get(tool)
        if readme_cpp is not None and source_cpp is not None:
            check(f"X2-cpp-{tool}",
                  f"README chunks/page for {tool} matches COST_AT_SCALE source",
                  abs(readme_cpp - source_cpp) < 0.15,
                  f"README={readme_cpp}, COST={source_cpp}")

        # Check annual cost
        readme_cost = clean_number(row.get("Annual cost (100K pages, 1K queries/day)", ""))
        source_cost = cost_lookup.get(tool)
        if readme_cost is not None and source_cost is not None:
            check(f"X2-cost-{tool}",
                  f"README annual cost for {tool} matches COST_AT_SCALE Scenario B",
                  abs(readme_cost - source_cost) < 1.0,
                  f"README=${readme_cost:,.0f}, COST=${source_cost:,.0f}")


def check_readme_vs_answer_quality():
    """Verify README answer quality scores match ANSWER_QUALITY.md."""
    readme = load_file(README)
    aq = load_file(BENCHMARKS / "ANSWER_QUALITY.md")

    readme_table = get_readme_benchmark_table(readme)
    if not readme_table:
        return  # Already flagged by X2

    aq_table = get_answer_quality_summary(aq)
    if not aq_table:
        check("X3", "ANSWER_QUALITY.md has summary table", False, "table not found")
        return

    aq_lookup = {}
    for row in aq_table:
        tool = clean_tool_name(row.get("Tool", ""))
        score = clean_number(row.get("Overall", ""))
        if tool and score is not None:
            aq_lookup[tool] = score

    for row in readme_table:
        tool = clean_tool_name(row.get("Tool", ""))
        readme_score = clean_number(row.get("Answer Quality (/5)", ""))
        source_score = aq_lookup.get(tool)
        if tool and readme_score is not None and source_score is not None:
            check(f"X3-{tool}",
                  f"README answer quality for {tool} matches ANSWER_QUALITY.md",
                  abs(readme_score - source_score) < 0.015,
                  f"README={readme_score}, AQ={source_score}")


def check_cost_vs_answer_quality():
    """Verify COST_AT_SCALE answer quality scores match ANSWER_QUALITY.md."""
    cost = load_file(BENCHMARKS / "COST_AT_SCALE.md")
    aq = load_file(BENCHMARKS / "ANSWER_QUALITY.md")

    source_data = get_cost_source_data(cost)
    if not source_data:
        check("X4", "COST_AT_SCALE.md has source data table", False, "table not found")
        return

    aq_table = get_answer_quality_summary(aq)
    aq_lookup = {}
    for row in aq_table:
        tool = clean_tool_name(row.get("Tool", ""))
        score = clean_number(row.get("Overall", ""))
        if tool and score is not None:
            aq_lookup[tool] = score

    for row in source_data:
        tool = clean_tool_name(row.get("Tool", ""))
        cost_score = clean_number(row.get("Answer quality (/5)", ""))
        aq_score = aq_lookup.get(tool)
        if tool and cost_score is not None and aq_score is not None:
            check(f"X4-{tool}",
                  f"COST_AT_SCALE answer quality for {tool} matches ANSWER_QUALITY.md",
                  abs(cost_score - aq_score) < 0.015,
                  f"COST={cost_score}, AQ={aq_score}")


def check_speed_ranking_order():
    """Verify README states the correct speed ranking order."""
    readme = load_file(README)
    speed = load_file(BENCHMARKS / "SPEED_COMPARISON.md")

    speed_table = get_speed_summary(speed)
    if not speed_table:
        return  # Already flagged

    # Get top 3 from report (table is sorted by pages/sec descending)
    report_top3 = []
    for row in speed_table[:3]:
        tool = clean_tool_name(row.get("Tool", ""))
        if tool:
            report_top3.append(tool)

    # Check that README mentions the correct tools in order
    # Look for the speed line
    for line in readme.split("\n"):
        if "fastest" in line.lower() and "pages/sec" in line.lower():
            # Extract tool names in order from this line
            readme_order = []
            for m in re.finditer(r"(\w[\w+\-]*)\s+(?:is fastest|second|third)", line):
                readme_order.append(clean_tool_name(m.group(1)))

            for i, (readme_tool, report_tool) in enumerate(
                zip(readme_order, report_top3)
            ):
                rank = ["fastest", "second", "third"][i] if i < 3 else f"#{i+1}"
                check(f"X5-rank{i+1}",
                      f"README speed rank {rank} matches report",
                      readme_tool == report_tool,
                      f"README={readme_tool}, report={report_tool}")
            break


def check_readme_tools_complete():
    """Verify README benchmark table includes all tools from ANSWER_QUALITY."""
    readme = load_file(README)
    aq = load_file(BENCHMARKS / "ANSWER_QUALITY.md")

    readme_table = get_readme_benchmark_table(readme)
    aq_table = get_answer_quality_summary(aq)

    readme_tools = {clean_tool_name(r.get("Tool", "")) for r in readme_table}
    aq_tools = {clean_tool_name(r.get("Tool", "")) for r in aq_table}

    # README may intentionally omit crawl4ai-raw from the summary table
    # but should include all other tools
    missing = aq_tools - readme_tools - {"crawl4ai-raw"}
    check("X6", "README benchmark table includes all major tools",
          len(missing) == 0,
          f"missing: {', '.join(sorted(missing))}" if missing else "")


def main():
    print("Running cross-report consistency checks...\n")

    missing_files = []
    for name in ["SPEED_COMPARISON.md", "COST_AT_SCALE.md", "ANSWER_QUALITY.md"]:
        if not (BENCHMARKS / name).exists():
            missing_files.append(name)
    if not README.exists():
        missing_files.append("README.md")

    if missing_files:
        print(f"  SKIP  Missing files: {', '.join(missing_files)}")
        print("\nCannot run consistency checks with missing files.")
        return 1

    check_readme_vs_speed()
    check_readme_vs_cost()
    check_readme_vs_answer_quality()
    check_cost_vs_answer_quality()
    check_speed_ranking_order()
    check_readme_tools_complete()

    print("\n".join(passes))
    if failures:
        print()
        print("\n".join(failures))
        print(f"\n{len(failures)} FAILED, {len(passes)} passed")
        return 1
    else:
        print(f"\nAll {len(passes)} checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
