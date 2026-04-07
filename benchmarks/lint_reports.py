#!/usr/bin/env python3
"""Lint benchmark reports against the CLAUDE.md style guide.

Checks each benchmark .md file for structural compliance:
- Style guide version tag present and current
- One-line answer after the title
- Metric context section before first table
- Summary table with all tools
- Cross-references to related reports
- Formatting rules (sorted tables, consistent units, bold markcrawl row)

Usage:
    python benchmarks/lint_reports.py              # lint all reports
    python benchmarks/lint_reports.py --fix-tags   # add/update style version tags
    python benchmarks/lint_reports.py SPEED_COMPARISON.md  # lint one file
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Current style guide version — update this when CLAUDE.md style guide changes
STYLE_VERSION = "v2"

# Reports that should be linted (relative to benchmarks/)
REPORT_FILES = [
    "SPEED_COMPARISON.md",
    "QUALITY_COMPARISON.md",
    "RETRIEVAL_COMPARISON.md",
    "ANSWER_QUALITY.md",
    "COST_AT_SCALE.md",
    "MARKCRAWL_RESULTS.md",
    "METHODOLOGY.md",
    "RETRIEVAL_FASTAPI_200.md",
    "RETRIEVAL_COMPARISON_CONTEXT.md",
]

# Expected cross-references per report (report -> must link to)
CROSS_REFS = {
    "SPEED_COMPARISON.md": ["QUALITY_COMPARISON.md", "METHODOLOGY.md", "COST_AT_SCALE.md"],
    "QUALITY_COMPARISON.md": ["RETRIEVAL_COMPARISON.md", "METHODOLOGY.md"],
    "RETRIEVAL_COMPARISON.md": ["ANSWER_QUALITY.md", "METHODOLOGY.md"],
    "ANSWER_QUALITY.md": ["COST_AT_SCALE.md", "RETRIEVAL_COMPARISON.md", "METHODOLOGY.md"],
    "COST_AT_SCALE.md": ["ANSWER_QUALITY.md", "SPEED_COMPARISON.md"],
    "MARKCRAWL_RESULTS.md": ["SPEED_COMPARISON.md"],
}

# All 7 tools that should appear in comparative reports
ALL_TOOLS = {"markcrawl", "scrapy+md", "crawl4ai", "crawl4ai-raw", "colly+md", "playwright", "crawlee"}

# Reports that are comparative (should show all tools)
COMPARATIVE_REPORTS = {
    "SPEED_COMPARISON.md",
    "QUALITY_COMPARISON.md",
    "RETRIEVAL_COMPARISON.md",
    "ANSWER_QUALITY.md",
    "COST_AT_SCALE.md",
}

# Style version tag pattern
STYLE_TAG_RE = re.compile(r"<!--\s*style:\s*(v\d+),\s*(\d{4}-\d{2}-\d{2})\s*-->")


def lint_file(filepath: Path) -> list[str]:
    """Lint a single report file. Returns list of warning strings."""
    warnings = []
    name = filepath.name

    if not filepath.exists():
        return [f"{name}: file not found"]

    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # --- 1. Style version tag ---
    tag_match = STYLE_TAG_RE.search(text)
    if not tag_match:
        warnings.append(f"{name}: missing style version tag (<!-- style: {STYLE_VERSION}, YYYY-MM-DD -->)")
    else:
        version = tag_match.group(1)
        if version != STYLE_VERSION:
            warnings.append(
                f"{name}: style tag is {version} but current guide is {STYLE_VERSION} — "
                f"review against current guide and update tag"
            )

    # --- 2. Title ---
    has_title = any(line.startswith("# ") and not line.startswith("## ") for line in lines[:5])
    if not has_title:
        warnings.append(f"{name}: no H1 title found in first 5 lines")

    # --- 3. One-line answer (text between title and first ## or first table) ---
    title_idx = None
    first_h2_idx = None
    first_table_idx = None
    for i, line in enumerate(lines):
        if title_idx is None and line.startswith("# ") and not line.startswith("## "):
            title_idx = i
        elif title_idx is not None and first_h2_idx is None and line.startswith("## "):
            first_h2_idx = i
        elif title_idx is not None and first_table_idx is None and line.startswith("|"):
            first_table_idx = i

    # METHODOLOGY.md is a reference doc, not a findings report — exempt from one-line answer
    if title_idx is not None and name != "METHODOLOGY.md":
        # Check for substantive text between title and first section/table
        end_idx = min(
            first_h2_idx if first_h2_idx else len(lines),
            first_table_idx if first_table_idx else len(lines),
        )
        intro_text = "\n".join(lines[title_idx + 1 : end_idx]).strip()
        # Remove style tag, Generated: lines, and blank lines
        intro_clean = STYLE_TAG_RE.sub("", intro_text).strip()
        intro_clean = re.sub(r"Generated:.*", "", intro_clean).strip()
        if len(intro_clean) < 20:
            warnings.append(
                f"{name}: no one-line answer found after title — "
                f"should state the finding, not describe what the report measures"
            )

    # --- 4. Cross-references ---
    if name in CROSS_REFS:
        for ref in CROSS_REFS[name]:
            if ref not in text:
                warnings.append(f"{name}: missing cross-reference to {ref}")

    # --- 5. All tools in comparative reports ---
    if name in COMPARATIVE_REPORTS:
        text_lower = text.lower()
        for tool in ALL_TOOLS:
            if tool not in text_lower:
                warnings.append(f"{name}: tool '{tool}' not found in report — all 7 tools should appear")

    # --- 6. Bold markcrawl row in summary tables ---
    if name in COMPARATIVE_REPORTS:
        # Look for table rows containing markcrawl — at least one should be bolded
        mc_rows = [line for line in lines if line.startswith("|") and "markcrawl" in line.lower()]
        has_bold_mc = any("**markcrawl**" in row or "**markcrawl" in row for row in mc_rows)
        if mc_rows and not has_bold_mc:
            warnings.append(f"{name}: markcrawl row in tables should be bolded with **")

    # --- 7. No emojis (except in code blocks or as data markers) ---
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]"
    )
    in_code_block = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if emoji_pattern.search(line):
            # Allow warning emoji and checkmarks used as data markers
            cleaned = line.replace("\u26a0", "").replace("\u26a0\ufe0f", "")
            cleaned = cleaned.replace("\u2713", "").replace("\u2717", "")
            cleaned = cleaned.replace("\u2714", "").replace("\u2718", "")
            cleaned = cleaned.replace("\u2705", "").replace("\u274c", "")
            if emoji_pattern.search(cleaned):
                warnings.append(f"{name}:{i+1}: emoji found — reports should not contain emojis")
                break

    # --- 8. Methodology section or link ---
    if name not in ("METHODOLOGY.md",):
        has_methodology_section = any("## methodology" in line.lower() or "## reproduc" in line.lower() for line in lines)
        has_methodology_link = "METHODOLOGY.md" in text
        if not has_methodology_section and not has_methodology_link:
            warnings.append(f"{name}: no methodology section or link to METHODOLOGY.md")

    return warnings


def fix_tags(filepath: Path) -> bool:
    """Add or update style version tag in a report. Returns True if changed."""
    import datetime

    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    today = datetime.date.today().isoformat()
    new_tag = f"<!-- style: {STYLE_VERSION}, {today} -->"

    # Find existing tag
    existing = STYLE_TAG_RE.search(text)
    if existing:
        old_tag = existing.group(0)
        if STYLE_VERSION in old_tag:
            return False  # Already current
        text = text.replace(old_tag, new_tag)
        filepath.write_text(text, encoding="utf-8")
        return True

    # Insert after title line
    for i, line in enumerate(lines):
        if line.startswith("# ") and not line.startswith("## "):
            lines.insert(i + 1, "")
            lines.insert(i + 2, new_tag)
            filepath.write_text("\n".join(lines), encoding="utf-8")
            return True

    return False


def main():
    fix_mode = "--fix-tags" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        files = [SCRIPT_DIR / a for a in args]
    else:
        files = [SCRIPT_DIR / f for f in REPORT_FILES]

    if fix_mode:
        for f in files:
            if not f.exists():
                continue
            if fix_tags(f):
                print(f"  Updated: {f.name}")
            else:
                print(f"  OK:      {f.name}")
        return

    all_warnings = []
    for f in files:
        warnings = lint_file(f)
        all_warnings.extend(warnings)

    if all_warnings:
        print(f"\n{len(all_warnings)} issue(s) found:\n")
        for w in all_warnings:
            print(f"  - {w}")
        print(f"\nRun with --fix-tags to add/update style version tags.")
        sys.exit(1)
    else:
        print(f"All {len(files)} reports pass lint checks.")


if __name__ == "__main__":
    main()
