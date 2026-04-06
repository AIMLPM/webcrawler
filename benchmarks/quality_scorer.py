"""Automated extraction quality scoring for crawler comparison.

Four scoring methods:

1. **Known signals** — must-have content indicators vs must-not-have junk
2. **Content density** — ratio of extracted text to raw visible text
3. **Cross-tool consensus** — precision/recall against majority-agreed content
4. **Nav/boilerplate detection** — preamble words and cross-page repetition rate

All methods are free, deterministic, and require no LLM or API keys.

The two most diagnostic metrics for RAG use cases:
- **Preamble words**: words before the first heading — nav chrome that pollutes
  every chunk before the real content starts (crawl4ai: ~200, markcrawl: 0).
- **Repeat rate**: fraction of sentences that appear on >50% of pages — repeated
  nav/footer text that inflates chunk count and degrades retrieval precision.
"""

from __future__ import annotations

import re
from collections import Counter
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
# Signal scoring (Approach 1 + preamble)
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
    preamble_words: int = 0   # words before the first heading — nav chrome indicator


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

    # Preamble: words before the first heading line
    preamble_words = 0
    for line in markdown.splitlines():
        if re.match(r"^#{1,6}\s", line):
            break
        preamble_words += len(line.split())

    return SignalScore(
        junk_found=junk_found,
        junk_rate=junk_rate,
        has_headings=len(headings) > 0,
        heading_count=len(headings),
        has_code_blocks=len(code_blocks) >= 2,
        code_block_count=len(code_blocks) // 2,
        word_count=len(markdown.split()),
        preamble_words=preamble_words,
    )


# ---------------------------------------------------------------------------
# Content density (Approach 2)
# ---------------------------------------------------------------------------

@dataclass
class DensityScore:
    """Content density: extracted words vs raw visible text words."""
    extracted_words: int = 0
    raw_visible_words: int = 0
    density: float = 0.0


def strip_html_to_text(html: str) -> str:
    """Strip HTML tags to get visible text only (no BeautifulSoup dependency)."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
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
# Cross-tool consensus (Approach 3)
# ---------------------------------------------------------------------------

def _normalize_sentence(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _extract_sentences(text: str, min_words: int = 10) -> List[str]:
    """Extract meaningful sentences (10+ words) from Markdown text."""
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
    shared_sentences: int = 0
    consensus_sentences: int = 0
    precision: float = 0.0   # shared / total — how much output is real content
    recall: float = 0.0      # consensus captured / total consensus
    my_sentence_set: List[str] = field(default_factory=list)  # for cross-page analysis


def score_consensus(
    tool_output: str,
    all_tool_outputs: Dict[str, str],
    tool_name: str,
) -> ConsensusScore:
    """Score one tool's output against cross-tool consensus.

    Precision: fraction of this tool's sentences that appear in at least one
    other tool. Measures how much of the output is real content vs unique noise.

    Recall: fraction of the majority-consensus pool (built from OTHER tools only)
    that this tool captured. A tool that misses commonly-agreed content scores
    below 100%. The pool is independent of the tool being scored, so recall is
    a genuine measure rather than trivially 100%.
    """
    my_sentences = set(_extract_sentences(tool_output))
    if not my_sentences:
        return ConsensusScore()

    other_tools = {k: v for k, v in all_tool_outputs.items() if k != tool_name}
    other_sentence_sets = {
        name: set(_extract_sentences(output))
        for name, output in other_tools.items()
    }

    # Precision: sentences in my output found in at least one other tool
    shared: set = set()
    for other_set in other_sentence_sets.values():
        shared |= (my_sentences & other_set)

    # Recall: consensus pool built from OTHER tools only (majority threshold)
    if other_sentence_sets:
        counts: Counter = Counter()
        for other_set in other_sentence_sets.values():
            counts.update(other_set)
        threshold = max(1, len(other_sentence_sets) // 2)
        consensus_pool = {s for s, n in counts.items() if n >= threshold}
    else:
        consensus_pool = set()

    total = len(my_sentences)
    precision = len(shared) / total if total > 0 else 0
    recall = len(consensus_pool & my_sentences) / len(consensus_pool) if consensus_pool else 0

    return ConsensusScore(
        total_sentences=total,
        shared_sentences=len(shared),
        consensus_sentences=len(consensus_pool),
        precision=precision,
        recall=recall,
        my_sentence_set=list(my_sentences),
    )


# ---------------------------------------------------------------------------
# Cross-page repetition (Approach 4 — nav/boilerplate detector)
# ---------------------------------------------------------------------------

def compute_repetition_rate(pages: List["PageQuality"]) -> float:
    """Fraction of unique sentences that appear on more than half of all pages.

    Nav chrome (prev/next links, version selectors, language pickers) repeats
    on every page. Real content appears on at most a handful of pages.
    A high repeat rate means the tool is carrying boilerplate into every chunk,
    which degrades RAG retrieval precision.

    Returns a float in [0, 1]. 0 = no repetition, 1 = everything repeats.
    """
    if len(pages) < 2:
        return 0.0

    threshold = len(pages) * 0.5
    sentence_counts: Counter = Counter()
    for page in pages:
        if page.consensus and page.consensus.my_sentence_set:
            for s in set(page.consensus.my_sentence_set):
                sentence_counts[s] += 1

    if not sentence_counts:
        return 0.0

    repeated = sum(1 for count in sentence_counts.values() if count > threshold)
    return repeated / len(sentence_counts)


# ---------------------------------------------------------------------------
# Combined quality record for one page
# ---------------------------------------------------------------------------

@dataclass
class PageQuality:
    url: str
    tool: str
    signal: SignalScore
    density: DensityScore
    consensus: Optional[ConsensusScore] = None
    raw_text: str = ""   # first 600 chars, for sample output in report

    @property
    def quality_score(self) -> float:
        """Combined quality score: (1 - junk_rate) * structure_bonus * precision."""
        structure = 1.0
        if self.signal.has_headings:
            structure += 0.1
        if self.signal.has_code_blocks:
            structure += 0.1
        structure = min(structure, 1.2)
        junk_penalty = 1.0 - self.signal.junk_rate
        consensus_factor = self.consensus.precision if self.consensus else 0.5
        return junk_penalty * structure * consensus_factor


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_quality_report(
    results: Dict[str, Dict[str, List[PageQuality]]],
    tool_names: List[str],
    sample_outputs: Optional[Dict[str, Dict[str, str]]] = None,
) -> str:
    """Generate a Markdown quality comparison report.

    Args:
        results: {site_name: {tool_name: [PageQuality per page]}}
        tool_names: ordered list of tool names
        sample_outputs: optional {site_name: {tool_name: first_500_chars}} for
            the sample output section. Populated automatically from PageQuality.raw_text
            if not supplied.
    """
    lines = [
        "# Extraction Quality Comparison",
        "",
        "## Methodology",
        "",
        "Four automated quality metrics — no LLM or human review needed:",
        "",
        "1. **Junk phrases** — known boilerplate strings (nav, footer, breadcrumbs) found in output",
        "2. **Preamble words** — words appearing *before* the first heading on each page.",
        "   Nav chrome (version selectors, language pickers, prev/next links) lives here.",
        "   A tool with a high preamble count is injecting site chrome into every chunk.",
        "3. **Cross-page repeat rate** — fraction of sentences that appear on >50% of pages.",
        "   Real content appears on at most a few pages; nav text repeats everywhere.",
        "   High repeat rate = nav boilerplate polluting every chunk in the RAG index.",
        "4. **Cross-tool consensus** — precision (how much output is agreed real content?)",
        "   and recall (how much agreed content did this tool capture?).",
        "",
        "> **Why preamble + repeat rate matter for RAG:** A tool that embeds 200 words of",
        "> nav chrome before each article degrades retrieval in two ways: (1) chunks contain",
        "> irrelevant tokens that dilute semantic similarity, and (2) the same nav sentences",
        "> match queries on every page, flooding results with false positives.",
        "",
    ]

    for site_name, site_data in results.items():
        lines.extend([f"## {site_name}", ""])

        # Compute repeat rate per tool (needs all pages for that tool)
        repeat_rates: Dict[str, float] = {}
        for tool in tool_names:
            pages = site_data.get(tool, [])
            repeat_rates[tool] = compute_repetition_rate(pages) if pages else 0.0

        # Summary table — includes the two new columns
        lines.extend([
            "| Tool | Avg words | Preamble words | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |",
            "|---|---|---|---|---|---|---|---|---|",
        ])

        for tool in tool_names:
            pages = site_data.get(tool, [])
            if not pages:
                lines.append(f"| {tool} | — | — | — | — | — | — | — | — |")
                continue

            avg_words = sum(p.signal.word_count for p in pages) / len(pages)
            avg_preamble = sum(p.signal.preamble_words for p in pages) / len(pages)
            repeat_rate = repeat_rates[tool]
            total_junk = sum(len(p.signal.junk_found) for p in pages)
            avg_headings = sum(p.signal.heading_count for p in pages) / len(pages)
            avg_code = sum(p.signal.code_block_count for p in pages) / len(pages)
            scored = [p for p in pages if p.consensus]
            avg_precision = sum(p.consensus.precision for p in scored) / len(scored) if scored else 0
            avg_recall = sum(p.consensus.recall for p in scored) / len(scored) if scored else 0

            # Flag high preamble (>50 words) and high repeat rate (>20%) with ⚠
            preamble_flag = " ⚠" if avg_preamble > 50 else ""
            repeat_flag = " ⚠" if repeat_rate > 0.20 else ""

            lines.append(
                f"| {tool} | {avg_words:.0f} | {avg_preamble:.0f}{preamble_flag} | "
                f"{repeat_rate:.0%}{repeat_flag} | {total_junk} | {avg_headings:.1f} | "
                f"{avg_code:.1f} | {avg_precision:.0%} | {avg_recall:.0%} |"
            )

        lines.append("")
        lines.append(
            "> ⚠ = likely nav/boilerplate problem. "
            "Preamble >50 words means nav chrome before first heading. "
            "Repeat rate >20% means sentences recurring across pages."
        )
        lines.append("")

        # Sample output section — first 500 chars per tool for a representative page
        # Pick the page with the most words (most content to compare)
        all_urls: set = set()
        for tool_pages in site_data.values():
            for p in tool_pages:
                all_urls.add(p.url)

        if all_urls:
            # Pick URL present in most tools with most content
            best_url = max(
                all_urls,
                key=lambda u: sum(
                    1 for t in tool_names
                    if any(p.url == u for p in site_data.get(t, []))
                )
            )
            short_url = best_url.split("//")[-1]

            lines.extend([
                "<details>",
                f"<summary>Sample output — first 40 lines of <code>{short_url}</code></summary>",
                "",
                "This shows what each tool outputs at the *top* of the same page.",
                "Nav boilerplate appears here before the real content starts.",
                "",
            ])

            for tool in tool_names:
                pages = site_data.get(tool, [])
                page = next((p for p in pages if p.url == best_url), None)
                if page and page.raw_text:
                    sample = "\n".join(page.raw_text.splitlines()[:40])
                    lines.extend([
                        f"**{tool}**",
                        "```",
                        sample,
                        "```",
                        "",
                    ])
                elif page:
                    lines.extend([f"**{tool}** — output present but sample not stored", ""])
                else:
                    lines.extend([f"**{tool}** — no output for this URL", ""])

            lines.extend(["</details>", ""])

        # Per-page detail table
        lines.extend([
            "<details>",
            "<summary>Per-page word counts and preamble</summary>",
            "",
            "| URL | " + " | ".join(f"{t} words / preamble" for t in tool_names) + " |",
            "|---" + "|---" * len(tool_names) + "|",
        ])

        for url in sorted(all_urls):
            short = url.split("//")[-1][:55]
            row = f"| {short} "
            for tool in tool_names:
                pages = site_data.get(tool, [])
                page = next((p for p in pages if p.url == url), None)
                if page:
                    row += f"| {page.signal.word_count} / {page.signal.preamble_words} "
                else:
                    row += "| — "
            row += "|"
            lines.append(row)

        lines.extend(["", "</details>", ""])

    return "\n".join(lines) + "\n"
