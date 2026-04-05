"""Automated extraction quality scoring for crawler comparison.

Three scoring methods:

1. **Known signals** — must-have content indicators vs must-not-have junk
2. **Content density** — ratio of extracted text to raw visible text
3. **Cross-tool consensus** — precision/recall against content agreed on by all tools

All methods are free, deterministic, and require no LLM or API keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Known junk signals (template chrome, not content)
# ---------------------------------------------------------------------------

JUNK_PHRASES = [
    "previous topic",
    "next topic",
    "table of contents",
    "built with sphinx",
    "edit on github",
    "navigation",
    "skip to content",
    "toggle navigation",
    "search docs",
    "back to top",
    "powered by",
    "cookie policy",
    "accept cookies",
    "privacy policy",
    "terms of service",
    "subscribe to newsletter",
    "follow us on",
    "share this page",
    "report a bug",
    "show source",
    "page source",
    "quick search",
    "created using",
]

# Breadcrumb patterns (e.g., "Home > Library > json")
BREADCRUMB_RE = re.compile(r"(?:home|docs)\s*[>»›/]\s*\w+\s*[>»›/]", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Signal scoring (Approach 1)
# ---------------------------------------------------------------------------

@dataclass
class SignalScore:
    """Scores based on must-have and must-not-have signals."""
    junk_found: List[str] = field(default_factory=list)
    junk_rate: float = 0.0
    has_headings: bool = False
    heading_count: int = 0
    has_code_blocks: bool = False
    code_block_count: int = 0
    word_count: int = 0


def score_signals(markdown: str) -> SignalScore:
    """Score a single page's Markdown for quality signals."""
    text_lower = markdown.lower()

    # Junk detection
    junk_found = []
    for phrase in JUNK_PHRASES:
        if phrase in text_lower:
            junk_found.append(phrase)
    if BREADCRUMB_RE.search(text_lower):
        junk_found.append("breadcrumb pattern")

    junk_rate = len(junk_found) / len(JUNK_PHRASES) if JUNK_PHRASES else 0

    # Structural signals
    headings = re.findall(r"^#{1,6}\s+", markdown, re.MULTILINE)
    code_blocks = re.findall(r"```", markdown)

    return SignalScore(
        junk_found=junk_found,
        junk_rate=junk_rate,
        has_headings=len(headings) > 0,
        heading_count=len(headings),
        has_code_blocks=len(code_blocks) >= 2,  # opening + closing = 1 block
        code_block_count=len(code_blocks) // 2,
        word_count=len(markdown.split()),
    )


# ---------------------------------------------------------------------------
# Content density (Approach 2)
# ---------------------------------------------------------------------------

@dataclass
class DensityScore:
    """Content density: extracted words vs raw visible text words."""
    extracted_words: int = 0
    raw_visible_words: int = 0
    density: float = 0.0  # extracted / raw_visible


def strip_html_to_text(html: str) -> str:
    """Strip HTML tags to get visible text only (no BeautifulSoup dependency)."""
    # Remove script/style content
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_density(markdown: str, raw_html: Optional[str] = None) -> DensityScore:
    """Score content density of extracted Markdown vs raw HTML."""
    extracted_words = len(markdown.split())

    if raw_html:
        visible_text = strip_html_to_text(raw_html)
        raw_visible_words = len(visible_text.split())
    else:
        raw_visible_words = 0

    density = extracted_words / raw_visible_words if raw_visible_words > 0 else 0

    return DensityScore(
        extracted_words=extracted_words,
        raw_visible_words=raw_visible_words,
        density=density,
    )


# ---------------------------------------------------------------------------
# Cross-tool consensus (Approach 3 — the strongest method)
# ---------------------------------------------------------------------------

def _normalize_sentence(s: str) -> str:
    """Normalize a sentence for fuzzy matching."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)  # remove punctuation
    s = re.sub(r"\s+", " ", s)
    return s


def _extract_sentences(text: str, min_words: int = 10) -> List[str]:
    """Extract meaningful sentences (10+ words) from text."""
    # Split on sentence boundaries
    raw_sentences = re.split(r"[.!?\n]+", text)
    sentences = []
    for s in raw_sentences:
        normalized = _normalize_sentence(s)
        if len(normalized.split()) >= min_words:
            sentences.append(normalized)
    return sentences


@dataclass
class ConsensusScore:
    """Cross-tool consensus: precision and recall against agreed-upon content."""
    total_sentences: int = 0
    shared_sentences: int = 0  # also in at least one other tool
    consensus_sentences: int = 0  # in ALL tools
    precision: float = 0.0  # shared / total (how much of our output is real content)
    recall: float = 0.0  # consensus in our output / total consensus


def score_consensus(
    tool_output: str,
    all_tool_outputs: Dict[str, str],
    tool_name: str,
) -> ConsensusScore:
    """Score one tool's output against cross-tool consensus.

    Args:
        tool_output: This tool's Markdown for one page.
        all_tool_outputs: Dict of {tool_name: markdown} for all tools on this page.
        tool_name: Name of the tool being scored.
    """
    my_sentences = set(_extract_sentences(tool_output))
    if not my_sentences:
        return ConsensusScore()

    # Get sentences from all other tools
    other_tools = {k: v for k, v in all_tool_outputs.items() if k != tool_name}
    other_sentence_sets = {
        name: set(_extract_sentences(output))
        for name, output in other_tools.items()
    }

    # Shared: sentences that appear in at least one other tool
    shared = set()
    for other_set in other_sentence_sets.values():
        shared |= (my_sentences & other_set)

    # Consensus: sentences that appear in ALL tools
    if other_sentence_sets:
        consensus_pool = my_sentences.copy()
        for other_set in other_sentence_sets.values():
            consensus_pool &= other_set
    else:
        consensus_pool = my_sentences

    total = len(my_sentences)
    precision = len(shared) / total if total > 0 else 0
    recall = len(consensus_pool & my_sentences) / len(consensus_pool) if consensus_pool else 0

    return ConsensusScore(
        total_sentences=total,
        shared_sentences=len(shared),
        consensus_sentences=len(consensus_pool),
        precision=precision,
        recall=recall,
    )


# ---------------------------------------------------------------------------
# Combined quality report for one page
# ---------------------------------------------------------------------------

@dataclass
class PageQuality:
    url: str
    tool: str
    signal: SignalScore
    density: DensityScore
    consensus: Optional[ConsensusScore] = None

    @property
    def quality_score(self) -> float:
        """Combined quality score: (1 - junk_rate) * structure_bonus * consensus_precision."""
        structure = 1.0
        if self.signal.has_headings:
            structure += 0.1
        if self.signal.has_code_blocks:
            structure += 0.1
        structure = min(structure, 1.2)

        junk_penalty = 1.0 - self.signal.junk_rate
        consensus_factor = self.consensus.precision if self.consensus else 0.5

        return junk_penalty * structure * consensus_factor


def generate_quality_report(
    results: Dict[str, Dict[str, List[PageQuality]]],
    tool_names: List[str],
) -> str:
    """Generate a Markdown quality comparison report.

    Args:
        results: {site_name: {tool_name: [PageQuality per page]}}
        tool_names: ordered list of tool names
    """
    lines = [
        "# Extraction Quality Comparison",
        "",
        "## Methodology",
        "",
        "Three automated quality metrics, no LLM or human review needed:",
        "",
        "1. **Junk detection** — known boilerplate phrases (nav, footer, breadcrumbs) found in output",
        "2. **Structure preservation** — heading count and code block count in Markdown",
        "3. **Cross-tool consensus** — sentences shared with other tools (precision) vs sentences all tools agree on (recall)",
        "",
        "Precision answers: \"How much of this tool's output is real content?\"",
        "Recall answers: \"How much of the agreed-upon content did this tool capture?\"",
        "",
    ]

    # Per-site summary
    for site_name, site_data in results.items():
        lines.extend([f"## {site_name}", ""])

        # Summary table
        lines.extend([
            "| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |",
            "|---|---|---|---|---|---|---|",
        ])

        for tool in tool_names:
            pages = site_data.get(tool, [])
            if not pages:
                lines.append(f"| {tool} | — | — | — | — | — | — |")
                continue

            avg_words = sum(p.signal.word_count for p in pages) / len(pages)
            total_junk = sum(len(p.signal.junk_found) for p in pages)
            avg_headings = sum(p.signal.heading_count for p in pages) / len(pages)
            avg_code = sum(p.signal.code_block_count for p in pages) / len(pages)
            avg_precision = sum(p.consensus.precision for p in pages if p.consensus) / max(1, sum(1 for p in pages if p.consensus))
            avg_recall = sum(p.consensus.recall for p in pages if p.consensus) / max(1, sum(1 for p in pages if p.consensus))

            lines.append(
                f"| {tool} | {avg_words:.0f} | {total_junk} | {avg_headings:.1f} | "
                f"{avg_code:.1f} | {avg_precision:.0%} | {avg_recall:.0%} |"
            )

        lines.append("")

        # Per-page word count comparison
        lines.extend([
            "<details>",
            "<summary>Per-page word counts</summary>",
            "",
            "| URL | " + " | ".join(tool_names) + " |",
            "|---" + "|---" * len(tool_names) + "|",
        ])

        # Get all URLs from any tool
        all_urls = set()
        for tool_pages in site_data.values():
            for p in tool_pages:
                all_urls.add(p.url)

        for url in sorted(all_urls):
            short_url = url.split("//")[-1][:60]
            row = f"| {short_url} "
            for tool in tool_names:
                pages = site_data.get(tool, [])
                page = next((p for p in pages if p.url == url), None)
                if page:
                    row += f"| {page.signal.word_count} "
                else:
                    row += "| — "
            row += "|"
            lines.append(row)

        lines.extend(["", "</details>", ""])

    return "\n".join(lines) + "\n"
