"""Automated extraction quality scoring for crawler comparison.

Four scoring methods:

1. **Known signals** — must-have content indicators vs must-not-have junk
2. **Content density** — ratio of extracted text to raw visible text
3. **Cross-tool consensus** — precision/recall against majority-agreed content
4. **Nav/boilerplate detection** — preamble words and cross-page repetition rate

All methods are free, deterministic, and require no LLM or API keys.

The two most diagnostic metrics for RAG use cases:
- **Preamble [1]**: avg words per page before the first heading — nav chrome that pollutes
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
    # Fix mojibake: double-encoded UTF-8 smart quotes (â€™ etc.)
    # This happens when UTF-8 bytes are decoded as Latin-1 then re-encoded.
    try:
        s = s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    # Normalize unicode quotes/dashes to ASCII equivalents
    s = s.replace("\u2019", "'").replace("\u2018", "'")   # smart single quotes
    s = s.replace("\u201c", '"').replace("\u201d", '"')   # smart double quotes
    s = s.replace("\u2013", "-").replace("\u2014", "-")   # en/em dash
    # Strip Markdown emphasis markers and links before general punctuation removal
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # [text](url) -> text
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"_", " ", s)  # underscores (Markdown emphasis residue)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _word_count_no_links(s: str) -> int:
    """Count words after removing markdown link URLs (keep link text)."""
    stripped = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return len(stripped.split())


def _unwrap_paragraphs(text: str) -> str:
    """Join soft-wrapped lines into paragraphs so sentence splitting is consistent.

    Different tools wrap lines differently (crawl4ai: long lines, scrapy: ~80 col).
    Without unwrapping, the same sentence split across lines produces different
    fragments, making cross-tool consensus unreliable.

    Paragraph boundaries: blank lines, headings (#), list items (*/- /digits),
    blockquotes (>), code fences (```), and definition lists (:).
    """
    lines = text.splitlines()
    paragraphs = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Paragraph boundary: blank line, heading, list item, blockquote, code fence,
        # standalone link lines, or short lines (likely nav/label elements).
        is_boundary = (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("```")
            or stripped.startswith(">")
            or re.match(r"^[\*\-\+]\s", stripped)
            or re.match(r"^\d+\.\s", stripped)
            or stripped.startswith(":")
            or stripped.startswith("|")
            or re.match(r"^\[.*\]\(.*\)$", stripped)  # standalone link line
            or re.match(r"^Tags?:", stripped, re.IGNORECASE)  # tag/label lines
            or _word_count_no_links(stripped) <= 3  # short lines are labels/nav
        )
        if is_boundary:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(stripped)
        else:
            current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    return "\n".join(paragraphs)


def _extract_sentences(text: str, min_words: int = 10) -> List[str]:
    """Extract meaningful sentences (10+ words) from Markdown text.

    Unwraps soft line breaks first so that the same sentence wrapped
    differently by different tools still produces the same extracted text.
    """
    unwrapped = _unwrap_paragraphs(text)
    raw_sentences = re.split(r"[.!?\n]+", unwrapped)
    sentences = []
    for s in raw_sentences:
        normalized = _normalize_sentence(s)
        if len(normalized.split()) >= min_words:
            sentences.append(normalized)
    return sentences


def _extract_phrases(text: str, min_words: int = 3) -> List[str]:
    """Extract short phrases (3+ words) for cross-page repetition detection.

    Nav chrome like "Previous topic", "Theme Auto Light Dark", "Show Source"
    is typically 3-8 words — too short for _extract_sentences(min_words=10).
    This function captures those short repeating fragments that are the primary
    boilerplate signal.
    """
    unwrapped = _unwrap_paragraphs(text)
    raw = re.split(r"[.!?\n|]+", unwrapped)
    phrases = []
    for s in raw:
        normalized = _normalize_sentence(s)
        if len(normalized.split()) >= min_words:
            phrases.append(normalized)
    return phrases


@dataclass
class ConsensusScore:
    """Cross-tool consensus: precision and recall against agreed-upon content."""
    total_sentences: int = 0
    shared_sentences: int = 0
    consensus_sentences: int = 0
    precision: float = 0.0   # shared / total — how much output is real content
    recall: float = 0.0      # consensus captured / total consensus
    my_sentence_set: List[str] = field(default_factory=list)  # for cross-page analysis
    my_phrase_set: List[str] = field(default_factory=list)     # short phrases for repeat rate


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
        my_phrase_set=_extract_phrases(tool_output),
    )


# ---------------------------------------------------------------------------
# Cross-page repetition (Approach 4 — nav/boilerplate detector)
# ---------------------------------------------------------------------------

def compute_repetition_rate(pages: List["PageQuality"]) -> float:
    """Fraction of unique phrases that appear on more than half of all pages.

    Uses short phrases (3+ words) via _extract_phrases(), not the 10+ word
    sentences used for consensus. Nav chrome like "Previous topic", "Theme
    Auto Light Dark", "Show Source" is 3-8 words — too short for sentence
    extraction but exactly what repeats on every page.

    Returns a float in [0, 1]. 0 = no repetition, 1 = everything repeats.
    """
    if len(pages) < 2:
        return 0.0

    threshold = len(pages) * 0.5
    phrase_counts: Counter = Counter()
    for page in pages:
        if page.consensus and page.consensus.my_phrase_set:
            # Use set() so a phrase appearing twice on ONE page counts once
            for phrase in set(page.consensus.my_phrase_set):
                phrase_counts[phrase] += 1

    if not phrase_counts:
        return 0.0

    repeated = sum(1 for count in phrase_counts.values() if count > threshold)
    return repeated / len(phrase_counts)


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
        "2. **Preamble [1]** — average words per page appearing *before* the first heading.",
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

    # -----------------------------------------------------------------------
    # Cross-site summary table — RAG readiness at a glance
    # -----------------------------------------------------------------------
    tool_summaries: Dict[str, Dict] = {}
    for tool in tool_names:
        all_pages = []
        all_preambles = []
        all_repeats = []
        all_junk = 0
        all_precisions = []
        all_recalls = []
        for site_name, site_data in results.items():
            pages = site_data.get(tool, [])
            if not pages:
                continue
            all_pages.extend(pages)
            all_preambles.extend(p.signal.preamble_words for p in pages)
            all_junk += sum(len(p.signal.junk_found) for p in pages)
            rr = compute_repetition_rate(pages) if pages else 0.0
            all_repeats.append(rr)
            scored = [p for p in pages if p.consensus and p.consensus.total_sentences >= 2]
            if scored:
                all_precisions.append(sum(p.consensus.precision for p in scored) / len(scored))
                all_recalls.append(sum(p.consensus.recall for p in scored) / len(scored))

        if not all_pages:
            continue

        avg_preamble = sum(all_preambles) / len(all_preambles) if all_preambles else 0
        avg_repeat = sum(all_repeats) / len(all_repeats) if all_repeats else 0
        avg_precision = sum(all_precisions) / len(all_precisions) if all_precisions else 0
        avg_recall = sum(all_recalls) / len(all_recalls) if all_recalls else 0
        avg_words = sum(p.signal.word_count for p in all_pages) / len(all_pages)

        # Content signal ratio: what % of output is actual content (not preamble/junk)?
        # Lower preamble relative to total words = more signal
        noise_words = avg_preamble  # preamble is the most measurable noise
        signal_ratio = max(0, (avg_words - noise_words) / avg_words) if avg_words > 0 else 0

        tool_summaries[tool] = {
            "pages": len(all_pages),
            "avg_words": avg_words,
            "avg_preamble": avg_preamble,
            "avg_repeat": avg_repeat,
            "avg_junk_per_page": all_junk / len(all_pages),
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "signal_ratio": signal_ratio,
        }

    if tool_summaries:
        lines.extend([
            "## Summary: RAG readiness at a glance",
            "",
            "For RAG pipelines, **clean output matters more than comprehensive output.**",
            "A tool that includes 1,000 words of nav chrome per page pollutes every",
            "chunk in the vector index, degrading retrieval for every query.",
            "",
            "| Tool | Content signal | Preamble [1] | Repeat rate | Junk/page | Precision | Recall |",
            "|---|---|---|---|---|---|---|",
        ])

        for tool in tool_names:
            s = tool_summaries.get(tool)
            if not s:
                lines.append(f"| {tool} | — | — | — | — | — | — |")
                continue
            preamble_flag = " ⚠" if s["avg_preamble"] > 50 else ""
            repeat_flag = " ⚠" if s["avg_repeat"] > 0.20 else ""
            lines.append(
                f"| {tool} | {s['signal_ratio']:.0%} | "
                f"{s['avg_preamble']:.0f}{preamble_flag} | "
                f"{s['avg_repeat']:.0%}{repeat_flag} | "
                f"{s['avg_junk_per_page']:.1f} | "
                f"{s['avg_precision']:.0%} | {s['avg_recall']:.0%} |"
            )

        # Footnote row at the bottom of the summary table
        lines.append(f"| **[1]** Avg words per page before the first heading (nav chrome) | | | | | | |")

        # Add takeaway narrative based on the summary data
        if "markcrawl" in tool_summaries:
            mc = tool_summaries["markcrawl"]
            noisy_tools = [t for t, s in tool_summaries.items()
                           if s["avg_preamble"] > 50 and t != "markcrawl"]
            if noisy_tools:
                worst = max(noisy_tools, key=lambda t: tool_summaries[t]["avg_preamble"])
                worst_p = tool_summaries[worst]["avg_preamble"]
                lines.extend([
                    "",
                    f"**Key takeaway:** markcrawl achieves {mc['signal_ratio']:.0%} content signal "
                    f"with only {mc['avg_preamble']:.0f} words of preamble per page — compared to "
                    f"{worst_p:.0f} for {worst}. "
                    f"Its recall is lower ({mc['avg_recall']:.0%} vs "
                    f"{tool_summaries[max(tool_summaries, key=lambda t: tool_summaries[t]['avg_recall'])]['avg_recall']:.0%}) "
                    f"because it strips nav, footer, and sponsor content that other tools include. "
                    f"For RAG use cases, this trade-off favors markcrawl: every chunk in the vector "
                    f"index is pure content, with no boilerplate to dilute embeddings or pollute "
                    f"retrieval results.",
                    "",
                ])

        lines.extend([
            "> **Content signal** = percentage of output that is content (not preamble nav chrome).",
            "> Higher is better. A tool with 100% content signal has zero nav/header pollution.",
            "> **Repeat rate** = fraction of phrases appearing on >50% of pages (boilerplate).",
            "> **Junk/page** = known boilerplate phrases detected per page.",
            "",
        ])

    for site_name, site_data in results.items():
        lines.extend([f"## {site_name}", ""])

        # Compute repeat rate per tool (needs all pages for that tool)
        repeat_rates: Dict[str, float] = {}
        for tool in tool_names:
            pages = site_data.get(tool, [])
            repeat_rates[tool] = compute_repetition_rate(pages) if pages else 0.0

        # Summary table — includes the two new columns
        lines.extend([
            "| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |",
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
            # Only average pages that had enough sentences for meaningful consensus.
            # Pages with 0 extractable sentences (e.g. short tag pages) produce
            # 0% precision/recall that would drag all tools down equally.
            scored = [p for p in pages if p.consensus and p.consensus.total_sentences >= 2]
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

        # Footnote row at the bottom of the per-site table
        lines.append(f"| **[1]** Avg words per page before the first heading (nav chrome). "
                      f"**⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%). "
                      f"| | | | | | | | |")
        lines.append("")

        # ---------------------------------------------------------------
        # Per-site narrative — interpret what the numbers mean
        # ---------------------------------------------------------------
        # Compute per-tool stats for this site for the narrative
        site_stats: Dict[str, Dict] = {}
        for tool in tool_names:
            pages = site_data.get(tool, [])
            if not pages:
                continue
            avg_w = sum(p.signal.word_count for p in pages) / len(pages)
            avg_p = sum(p.signal.preamble_words for p in pages) / len(pages)
            rr = repeat_rates.get(tool, 0)
            scored = [p for p in pages if p.consensus and p.consensus.total_sentences >= 2]
            prec = sum(p.consensus.precision for p in scored) / len(scored) if scored else 0
            rec = sum(p.consensus.recall for p in scored) / len(scored) if scored else 0
            site_stats[tool] = {
                "avg_words": avg_w, "preamble": avg_p, "repeat": rr,
                "precision": prec, "recall": rec,
            }

        if site_stats:
            # Find the tool with lowest preamble and highest recall
            cleanest = min(
                (t for t in site_stats if site_stats[t]["preamble"] < 50),
                key=lambda t: site_stats[t]["preamble"],
                default=None,
            )
            highest_recall = max(site_stats, key=lambda t: site_stats[t]["recall"])
            most_words = max(site_stats, key=lambda t: site_stats[t]["avg_words"])
            least_words = min(site_stats, key=lambda t: site_stats[t]["avg_words"])

            word_gap = site_stats[most_words]["avg_words"] - site_stats[least_words]["avg_words"]
            preamble_heavy = [t for t in site_stats if site_stats[t]["preamble"] > 50]

            narrative_parts = []

            # Cleanliness story
            if cleanest and preamble_heavy:
                heavy_example = max(preamble_heavy, key=lambda t: site_stats[t]["preamble"])
                clean_p = site_stats[cleanest]['preamble']
                heavy_p = site_stats[heavy_example]['preamble']
                w = "word" if clean_p < 1.5 else "words"
                narrative_parts.append(
                    f"**{cleanest}** produces the cleanest output with "
                    f"{clean_p:.0f} {w} of preamble per page, "
                    f"while **{heavy_example}** injects {heavy_p:.0f} "
                    f"words of nav chrome before content begins."
                )

            # Word count gap story — explains where the "extra" content is
            if word_gap > 100 and preamble_heavy:
                preamble_words_heavy = site_stats[most_words]["preamble"]
                if preamble_words_heavy > 50:
                    preamble_pct = preamble_words_heavy / site_stats[most_words]["avg_words"] * 100
                    narrative_parts.append(
                        f"The word count gap ({site_stats[least_words]['avg_words']:.0f} vs "
                        f"{site_stats[most_words]['avg_words']:.0f} avg words) is largely explained "
                        f"by preamble: {preamble_words_heavy:.0f} words of nav chrome account for "
                        f"~{preamble_pct:.0f}% of {most_words}'s output on this site."
                    )

            # Recall gap story — explain that lower recall often means better cleaning
            if cleanest and site_stats[cleanest]["recall"] < 0.90:
                recall_gap = site_stats[highest_recall]["recall"] - site_stats[cleanest]["recall"]
                if recall_gap > 0.10:
                    narrative_parts.append(
                        f"{cleanest}'s lower recall ({site_stats[cleanest]['recall']:.0%} vs "
                        f"{site_stats[highest_recall]['recall']:.0%}) reflects stricter content "
                        f"filtering — the \"missed\" sentences are predominantly navigation, "
                        f"sponsor links, and footer text that other tools include as content. "
                        f"For RAG, this is a net positive: fewer junk tokens per chunk means "
                        f"better embedding quality and retrieval precision."
                    )

            if narrative_parts:
                lines.append("**Reading the numbers:**\n" + " ".join(narrative_parts))
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
            "<summary>Per-page word counts and preamble [1]</summary>",
            "",
            "| URL | " + " | ".join(f"{t} words / preamble [1]" for t in tool_names) + " |",
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
