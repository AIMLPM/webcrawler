#!/usr/bin/env python3
"""Invariant checker for self-improvement reviews.

Validates structural invariants that must always be true after any change.
Run this before committing self-improvement changes:

    python benchmarks/self_improvement/check_invariants.py

Exit code 0 = all checks pass. Non-zero = failures found.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARKS = ROOT / "benchmarks"
README = ROOT / "README.md"

REPORT_FILES = [
    "SPEED_COMPARISON.md",
    "QUALITY_COMPARISON.md",
    "RETRIEVAL_COMPARISON.md",
    "ANSWER_QUALITY.md",
    "COST_AT_SCALE.md",
    "MARKCRAWL_RESULTS.md",
]

ALL_TOOLS = {
    "markcrawl",
    "crawl4ai",
    "crawl4ai-raw",
    "scrapy+md",
    "crawlee",
    "colly+md",
    "playwright",
    "firecrawl",
}

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


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def report_text(name: str) -> str:
    return (BENCHMARKS / name).read_text(encoding="utf-8")


# --- README invariants ---

def check_readme():
    text = readme_text()

    check("R1", "README has Common Recipes section",
          "## Common Recipes" in text)

    check("R2", "README shows --no-sitemap --max-pages 1 recipe",
          "--no-sitemap" in text and "--max-pages 1" in text)

    check("R3", "README shows --render-js in a recipe",
          "--render-js" in text)

    # Check tagline (first few lines)
    first_lines = "\n".join(text.split("\n")[:5])
    check("R4", "README tagline contains 'webpage'",
          "webpage" in first_lines.lower())

    # LLM_PROMPT.md must appear before ## Quickstart
    quickstart_pos = text.find("## Quickstart")
    llm_prompt_pos = text.find("LLM_PROMPT.md")
    check("R5", "README links LLM_PROMPT.md before Quickstart",
          0 < llm_prompt_pos < quickstart_pos if quickstart_pos > 0 and llm_prompt_pos > 0 else False)

    check("R6", "README has 'When NOT to use' section",
          "When NOT to use" in text)

    check("R7", "README has benchmark summary in <details>",
          "How it compares" in text and "<details>" in text)


# --- Report invariants ---

def check_reports():
    for name in REPORT_FILES:
        path = BENCHMARKS / name
        if not path.exists():
            check(f"P1-{name}", f"{name} exists", False, "file missing")
            continue

        text = report_text(name)

        # P1: Style version tag
        check(f"P1-{name}", f"{name} has style version tag",
              "<!-- style:" in text)

        # P4: No emojis in editorial text (skip quoted content blocks
        # and lines that are clearly scraped page output)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002600-\U000026FF"
            "\U00002700-\U000027BF"
            "]+",
            flags=re.UNICODE,
        )
        editorial_emojis = []
        in_code_block = False
        for line in text.split("\n"):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            # Skip lines that are clearly quoted crawl output
            if line.startswith(">") or line.startswith("    "):
                continue
            found = emoji_pattern.findall(line)
            if found:
                editorial_emojis.extend(found)
        check(f"P4-{name}", f"{name} has no emojis in editorial text",
              len(editorial_emojis) == 0,
              f"found: {editorial_emojis[:3]}" if editorial_emojis else "")

    # P5: Cross-references resolve
    for name in REPORT_FILES:
        path = BENCHMARKS / name
        if not path.exists():
            continue
        text = report_text(name)
        # Find markdown links to .md files
        links = re.findall(r"\[.*?\]\(([^)]+\.md)\)", text)
        for link in links:
            # Resolve relative to benchmarks/
            target = (BENCHMARKS / link).resolve()
            check(f"P5-{name}", f"{name} link to {link} resolves",
                  target.exists(),
                  f"{target} not found" if not target.exists() else "")


# --- Code invariants ---

def check_code():
    # C1: markcrawl --help (use CLI entry point, not -m)
    result = subprocess.run(
        [sys.executable, "-m", "markcrawl.cli", "--help"],
        capture_output=True, timeout=10,
    )
    # Also try the installed entry point if the module approach fails
    if result.returncode != 0:
        result = subprocess.run(
            ["markcrawl", "--help"],
            capture_output=True, timeout=10,
        )
    check("C1", "markcrawl --help exits 0",
          result.returncode == 0,
          f"exit code {result.returncode}" if result.returncode != 0 else "")

    # C2: import markcrawl
    result = subprocess.run(
        [sys.executable, "-c", "import markcrawl"],
        capture_output=True, timeout=10,
    )
    check("C2", "import markcrawl succeeds",
          result.returncode == 0,
          result.stderr.decode()[:200] if result.returncode != 0 else "")

    # C3: lint_reports.py
    lint_script = BENCHMARKS / "lint_reports.py"
    if lint_script.exists():
        result = subprocess.run(
            [sys.executable, str(lint_script)],
            capture_output=True, timeout=30,
        )
        check("C3", "lint_reports.py passes",
              result.returncode == 0,
              result.stdout.decode()[:300] if result.returncode != 0 else "")
    else:
        check("C3", "lint_reports.py exists", False, "file missing")


# --- Feedback registry ---

def check_registry():
    registry = BENCHMARKS / "self_improvement" / "feedback_registry.md"
    check("F1", "Feedback registry exists",
          registry.exists())

    if registry.exists():
        text = registry.read_text(encoding="utf-8")
        entries = re.findall(r"### FR-\d+", text)
        check("F2", "Feedback registry has entries",
              len(entries) > 0,
              f"found {len(entries)} entries")


def main():
    print("Running invariant checks...\n")

    check_readme()
    check_reports()
    check_code()
    check_registry()

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
