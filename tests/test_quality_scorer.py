"""Tests for benchmarks/quality_scorer.py — consensus scoring, preamble detection,
repeat-rate calculation, content signal, and normalization helpers."""

from __future__ import annotations

import sys
from pathlib import Path

# benchmarks/ is not a package, so add it to sys.path for import.
_benchmarks_dir = str(Path(__file__).resolve().parent.parent / "benchmarks")
if _benchmarks_dir not in sys.path:
    sys.path.insert(0, _benchmarks_dir)

from quality_scorer import (  # noqa: E402
    ConsensusScore,
    DensityScore,
    PageQuality,
    SignalScore,
    _extract_phrases,
    _extract_sentences,
    _normalize_sentence,
    _unwrap_paragraphs,
    _word_count_no_links,
    compute_repetition_rate,
    score_consensus,
    score_density,
    score_signals,
    strip_html_to_text,
)

# =========================================================================
# _normalize_sentence
# =========================================================================

class TestNormalizeSentence:
    def test_lowercases(self):
        assert _normalize_sentence("Hello World") == "hello world"

    def test_strips_whitespace(self):
        assert _normalize_sentence("  hello  ") == "hello"

    def test_strips_punctuation(self):
        assert _normalize_sentence("hello, world!") == "hello world"

    def test_strips_markdown_links(self):
        result = _normalize_sentence("see [the docs](https://example.com) for details")
        assert "httpexamplecom" not in result
        assert "the docs" in result

    def test_underscores_become_spaces(self):
        result = _normalize_sentence("hello_world_test")
        assert result == "hello world test"

    def test_smart_quotes_normalized(self):
        result = _normalize_sentence("it\u2019s a \u201ctest\u201d")
        assert "its" in result
        assert "test" in result

    def test_en_em_dash_normalized(self):
        result = _normalize_sentence("foo\u2013bar\u2014baz")
        assert result == "foobarbaz"

    def test_empty_string(self):
        assert _normalize_sentence("") == ""

    def test_only_punctuation(self):
        assert _normalize_sentence("!!!...???") == ""

    def test_mojibake_fix(self):
        # Simulate double-encoded UTF-8: the smart apostrophe U+2019 encoded
        # as UTF-8 bytes (e2 80 99) then interpreted as Latin-1.
        smart_apostrophe_utf8 = "\u2019".encode("utf-8")
        mojibake = smart_apostrophe_utf8.decode("latin-1")  # produces â€™
        result = _normalize_sentence(f"it{mojibake}s fine")
        assert "its fine" == result


# =========================================================================
# _word_count_no_links
# =========================================================================

class TestWordCountNoLinks:
    def test_plain_text(self):
        assert _word_count_no_links("hello world foo") == 3

    def test_strips_link_url(self):
        assert _word_count_no_links("[click here](https://example.com/long/path)") == 2

    def test_multiple_links(self):
        text = "see [docs](http://a.com) and [api](http://b.com) pages"
        assert _word_count_no_links(text) == 5

    def test_empty(self):
        assert _word_count_no_links("") == 0


# =========================================================================
# _unwrap_paragraphs
# =========================================================================

class TestUnwrapParagraphs:
    def test_joins_continuation_lines(self):
        text = "This is a long sentence that\ncontinues on the next line without a break."
        result = _unwrap_paragraphs(text)
        assert "that continues" in result

    def test_heading_is_boundary(self):
        text = "some text\n# Heading\nmore text"
        result = _unwrap_paragraphs(text)
        lines = result.splitlines()
        assert any(line.startswith("# Heading") for line in lines)

    def test_blank_line_is_boundary(self):
        text = "paragraph one\n\nparagraph two"
        result = _unwrap_paragraphs(text)
        assert "paragraph one" in result
        assert "paragraph two" in result
        # They should NOT be joined
        assert "paragraph one paragraph two" not in result

    def test_list_item_is_boundary(self):
        text = "intro text\n- item one\n- item two"
        result = _unwrap_paragraphs(text)
        assert "- item one" in result

    def test_code_fence_is_boundary(self):
        text = "before\n```python\ncode here\n```\nafter"
        result = _unwrap_paragraphs(text)
        assert "before" in result
        assert "```python" in result

    def test_standalone_link_is_boundary(self):
        text = "some text\n[Link](http://example.com)\nmore text"
        result = _unwrap_paragraphs(text)
        assert "some text [Link]" not in result

    def test_short_lines_are_boundaries(self):
        # Lines with 3 or fewer words (after link stripping) are boundaries.
        text = "This is a longer line of real content\nNav\nAnother real content line here"
        result = _unwrap_paragraphs(text)
        assert "content Nav" not in result

    def test_empty_input(self):
        assert _unwrap_paragraphs("") == ""


# =========================================================================
# _extract_sentences
# =========================================================================

class TestExtractSentences:
    def test_filters_short_sentences(self):
        text = "Short. This is a sentence with more than ten words in it for sure."
        sentences = _extract_sentences(text)
        assert len(sentences) == 1
        assert "short" not in sentences[0]

    def test_splits_on_period(self):
        text = (
            "This is the first sentence with enough words to pass the filter. "
            "This is the second sentence also with enough words to pass easily."
        )
        sentences = _extract_sentences(text)
        assert len(sentences) == 2

    def test_empty_input(self):
        assert _extract_sentences("") == []

    def test_no_qualifying_sentences(self):
        assert _extract_sentences("too short") == []

    def test_custom_min_words(self):
        text = "Three word sentence. Five words are here now."
        sentences = _extract_sentences(text, min_words=3)
        assert len(sentences) >= 1

    def test_normalization_applied(self):
        text = "This [linked text](http://example.com) is a sentence with enough words to be extracted here."
        sentences = _extract_sentences(text)
        assert len(sentences) == 1
        assert "httpexamplecom" not in sentences[0]


# =========================================================================
# _extract_phrases
# =========================================================================

class TestExtractPhrases:
    def test_extracts_short_phrases(self):
        text = "Previous topic\nNext topic\nTable of contents"
        phrases = _extract_phrases(text, min_words=2)
        assert len(phrases) >= 2

    def test_filters_below_min_words(self):
        text = "Hi\nOk\nYes"
        phrases = _extract_phrases(text, min_words=3)
        assert len(phrases) == 0

    def test_splits_on_pipe(self):
        text = "Home | About | Contact us here"
        phrases = _extract_phrases(text, min_words=2)
        assert any("contact" in p for p in phrases)

    def test_empty_input(self):
        assert _extract_phrases("") == []


# =========================================================================
# score_signals
# =========================================================================

class TestScoreSignals:
    def test_detects_junk_phrases(self):
        md = "Skip to content\n\n# Real heading\n\nSome content here."
        score = score_signals(md)
        assert "skip to content" in score.junk_found
        assert score.junk_rate > 0

    def test_detects_breadcrumbs(self):
        md = "Home > Library > json\n\n# JSON Module\n\nContent."
        score = score_signals(md)
        assert "breadcrumb pattern" in score.junk_found

    def test_no_junk(self):
        md = "# Clean Page\n\nJust some nice content here."
        score = score_signals(md)
        assert score.junk_found == []
        assert score.junk_rate == 0.0

    def test_heading_detection(self):
        md = "# H1\n## H2\n### H3"
        score = score_signals(md)
        assert score.has_headings is True
        assert score.heading_count == 3

    def test_no_headings(self):
        md = "No headings here, just plain text."
        score = score_signals(md)
        assert score.has_headings is False
        assert score.heading_count == 0

    def test_code_blocks(self):
        md = "# Code\n\n```python\nprint('hi')\n```"
        score = score_signals(md)
        assert score.has_code_blocks is True
        assert score.code_block_count == 1

    def test_code_blocks_need_pairs(self):
        # Single ``` doesn't count as a complete code block
        md = "# Broken\n\n```\nunclosed"
        score = score_signals(md)
        assert score.has_code_blocks is False
        assert score.code_block_count == 0

    def test_word_count(self):
        md = "one two three four five"
        score = score_signals(md)
        assert score.word_count == 5

    def test_empty_input(self):
        score = score_signals("")
        assert score.word_count == 0
        assert score.preamble_words == 0
        assert score.has_headings is False


# =========================================================================
# Preamble detection (via score_signals)
# =========================================================================

class TestPreamble:
    def test_no_preamble_heading_first(self):
        md = "# Title\n\nContent after heading."
        score = score_signals(md)
        assert score.preamble_words == 0

    def test_preamble_before_heading(self):
        md = "Navigation menu items here\nAnother nav line\n\n# Real Title\n\nContent."
        score = score_signals(md)
        assert score.preamble_words > 0

    def test_preamble_counts_all_words_before_heading(self):
        md = "word1 word2 word3\nword4 word5\n# Heading"
        score = score_signals(md)
        assert score.preamble_words == 5

    def test_no_heading_entire_doc_is_preamble(self):
        md = "This entire document has no headings at all just plain text."
        score = score_signals(md)
        assert score.preamble_words == len(md.split())

    def test_empty_lines_before_heading(self):
        md = "\n\n\n# Heading\nContent"
        score = score_signals(md)
        assert score.preamble_words == 0

    def test_heading_levels(self):
        # All heading levels (##, ###, etc.) should stop preamble counting.
        for level in range(1, 7):
            hashes = "#" * level
            md = f"preamble text here\n{hashes} Heading"
            score = score_signals(md)
            assert score.preamble_words == 3, f"Failed for h{level}"


# =========================================================================
# score_density
# =========================================================================

class TestScoreDensity:
    def test_no_html(self):
        d = score_density("hello world", None)
        assert d.extracted_words == 2
        assert d.raw_visible_words == 0
        assert d.density == 0

    def test_with_html(self):
        html = "<p>Hello world</p>"
        d = score_density("Hello world", html)
        assert d.extracted_words == 2
        assert d.raw_visible_words == 2
        assert d.density == 1.0

    def test_density_ratio(self):
        html = "<p>one two three four</p>"
        d = score_density("one two", html)
        assert d.density == 0.5

    def test_empty_markdown(self):
        d = score_density("", "<p>content</p>")
        assert d.extracted_words == 0
        assert d.density == 0


# =========================================================================
# strip_html_to_text
# =========================================================================

class TestStripHtmlToText:
    def test_removes_tags(self):
        assert strip_html_to_text("<p>Hello</p>") == "Hello"

    def test_removes_script(self):
        html = "<script>var x = 1;</script><p>Visible</p>"
        assert "var" not in strip_html_to_text(html)
        assert "Visible" in strip_html_to_text(html)

    def test_removes_style(self):
        html = "<style>body{color:red}</style><p>Text</p>"
        result = strip_html_to_text(html)
        assert "color" not in result
        assert "Text" in result

    def test_collapses_whitespace(self):
        html = "<p>hello</p>   <p>world</p>"
        assert strip_html_to_text(html) == "hello world"

    def test_empty(self):
        assert strip_html_to_text("") == ""


# =========================================================================
# score_consensus
# =========================================================================

class TestScoreConsensus:
    """Test consensus scoring with cross-tool agreement."""

    # A sentence long enough to pass the 10-word min filter.
    SENT_A = "This is a shared sentence that appears in multiple tools for testing purposes."
    SENT_B = "Another different sentence that is also long enough to be extracted here."
    SENT_C = "A unique sentence that only one single tool has in its complete output here."

    def test_perfect_agreement(self):
        """All tools have the same content -> precision 1.0, recall 1.0."""
        outputs = {
            "tool_a": self.SENT_A,
            "tool_b": self.SENT_A,
            "tool_c": self.SENT_A,
        }
        result = score_consensus(self.SENT_A, outputs, "tool_a")
        assert result.precision == 1.0
        assert result.recall == 1.0

    def test_unique_content_low_precision(self):
        """Tool with unique content has lower precision."""
        shared = self.SENT_A
        unique = self.SENT_C
        outputs = {
            "target": f"{shared} {unique}",
            "other1": shared,
            "other2": shared,
        }
        result = score_consensus(f"{shared} {unique}", outputs, "target")
        # One of two sentences is shared -> precision = 0.5
        assert result.precision == 0.5

    def test_missing_content_low_recall(self):
        """Tool missing consensus content has lower recall."""
        outputs = {
            "target": self.SENT_A,
            "other1": f"{self.SENT_A} {self.SENT_B}",
            "other2": f"{self.SENT_A} {self.SENT_B}",
        }
        result = score_consensus(self.SENT_A, outputs, "target")
        # Target is missing SENT_B which is in the consensus pool
        assert result.recall < 1.0
        assert result.precision == 1.0  # everything target has IS shared

    def test_empty_input(self):
        result = score_consensus("", {"a": "hello", "b": "world"}, "a")
        assert result.total_sentences == 0
        assert result.precision == 0.0
        assert result.recall == 0.0

    def test_single_tool(self):
        """With only one tool, no 'other' tools exist."""
        outputs = {"only": self.SENT_A}
        result = score_consensus(self.SENT_A, outputs, "only")
        # No other tools -> shared is empty, consensus pool is empty
        assert result.precision == 0.0
        assert result.recall == 0.0

    def test_two_tools_agreement(self):
        outputs = {
            "a": self.SENT_A,
            "b": self.SENT_A,
        }
        result = score_consensus(self.SENT_A, outputs, "a")
        assert result.precision == 1.0
        assert result.recall == 1.0

    def test_populates_phrase_set(self):
        text = "Previous topic. Next topic. Some actual content here."
        outputs = {"a": text, "b": text}
        result = score_consensus(text, outputs, "a")
        assert isinstance(result.my_phrase_set, list)

    def test_populates_sentence_set(self):
        outputs = {"a": self.SENT_A, "b": self.SENT_A}
        result = score_consensus(self.SENT_A, outputs, "a")
        assert len(result.my_sentence_set) == 1

    def test_excludes_self_from_other_tools(self):
        """The tool being scored should not appear in 'other_tools'."""
        # If self were included, precision would be inflated.
        unique_to_target = self.SENT_C
        outputs = {
            "target": unique_to_target,
            "other": self.SENT_A,
        }
        result = score_consensus(unique_to_target, outputs, "target")
        # The unique sentence is NOT in any other tool -> precision = 0
        assert result.precision == 0.0


# =========================================================================
# compute_repetition_rate
# =========================================================================

class TestComputeRepetitionRate:
    def _make_page(self, phrases: list[str]) -> PageQuality:
        """Helper to create a PageQuality with a specific phrase set."""
        consensus = ConsensusScore(my_phrase_set=phrases)
        return PageQuality(
            url="http://example.com",
            tool="test",
            signal=SignalScore(),
            density=DensityScore(),
            consensus=consensus,
        )

    def test_no_repetition(self):
        pages = [
            self._make_page(["unique phrase one"]),
            self._make_page(["unique phrase two"]),
            self._make_page(["unique phrase three"]),
        ]
        rate = compute_repetition_rate(pages)
        assert rate == 0.0

    def test_all_repeated(self):
        phrase = "this phrase repeats everywhere"
        pages = [
            self._make_page([phrase]),
            self._make_page([phrase]),
            self._make_page([phrase]),
            self._make_page([phrase]),
        ]
        rate = compute_repetition_rate(pages)
        assert rate == 1.0

    def test_partial_repetition(self):
        repeated = "this phrase repeats on most pages"
        unique = "this phrase is unique to one page"
        pages = [
            self._make_page([repeated, unique]),
            self._make_page([repeated]),
            self._make_page([repeated]),
            self._make_page([repeated]),
        ]
        rate = compute_repetition_rate(pages)
        # 'repeated' appears 4/4 > 2.0 threshold, 'unique' appears 1/4 <= 2.0
        # 1 repeated out of 2 unique phrases = 0.5
        assert rate == 0.5

    def test_single_page_returns_zero(self):
        pages = [self._make_page(["some phrase here"])]
        assert compute_repetition_rate(pages) == 0.0

    def test_empty_list_returns_zero(self):
        assert compute_repetition_rate([]) == 0.0

    def test_no_phrases_returns_zero(self):
        pages = [
            self._make_page([]),
            self._make_page([]),
        ]
        assert compute_repetition_rate(pages) == 0.0

    def test_no_consensus_returns_zero(self):
        page = PageQuality(
            url="http://example.com",
            tool="test",
            signal=SignalScore(),
            density=DensityScore(),
            consensus=None,
        )
        assert compute_repetition_rate([page, page]) == 0.0

    def test_duplicate_phrase_on_same_page_counted_once(self):
        """A phrase appearing twice on ONE page should only count once for that page."""
        phrase = "this phrase appears twice on same page"
        pages = [
            self._make_page([phrase, phrase]),  # duplicate on same page
            self._make_page(["other unique phrase here"]),
            self._make_page(["another unique phrase here"]),
        ]
        rate = compute_repetition_rate(pages)
        # phrase appears on 1/3 pages (counted once despite duplicate), threshold is 1.5
        # 1 < 1.5 so it's not repeated
        assert rate == 0.0

    def test_threshold_is_half_pages(self):
        """Phrase must appear on MORE than 50% of pages to count as repeated."""
        phrase = "borderline phrase for threshold test"
        # 4 pages, threshold = 2.0. Phrase on exactly 2 pages -> NOT repeated (needs >2).
        pages = [
            self._make_page([phrase]),
            self._make_page([phrase]),
            self._make_page(["unique one phrase here"]),
            self._make_page(["unique two phrase here"]),
        ]
        rate = compute_repetition_rate(pages)
        assert rate == 0.0

        # 3 out of 4 -> repeated (3 > 2.0)
        pages_with_more = [
            self._make_page([phrase]),
            self._make_page([phrase]),
            self._make_page([phrase]),
            self._make_page(["unique one phrase here"]),
        ]
        rate2 = compute_repetition_rate(pages_with_more)
        assert rate2 > 0.0


# =========================================================================
# PageQuality.quality_score
# =========================================================================

class TestPageQualityScore:
    def test_basic_quality_score(self):
        signal = SignalScore(
            has_headings=True,
            has_code_blocks=True,
            junk_rate=0.0,
        )
        consensus = ConsensusScore(precision=1.0)
        page = PageQuality(
            url="http://example.com",
            tool="test",
            signal=signal,
            density=DensityScore(),
            consensus=consensus,
        )
        # (1 - 0) * min(1 + 0.1 + 0.1, 1.2) * 1.0 = 1.2
        assert page.quality_score == 1.2

    def test_junk_penalty(self):
        signal = SignalScore(junk_rate=0.5)
        consensus = ConsensusScore(precision=1.0)
        page = PageQuality(
            url="http://example.com",
            tool="test",
            signal=signal,
            density=DensityScore(),
            consensus=consensus,
        )
        # (1 - 0.5) * 1.0 * 1.0 = 0.5
        assert page.quality_score == 0.5

    def test_no_consensus_uses_default(self):
        signal = SignalScore()
        page = PageQuality(
            url="http://example.com",
            tool="test",
            signal=signal,
            density=DensityScore(),
            consensus=None,
        )
        # No consensus -> consensus_factor = 0.5
        assert page.quality_score == 0.5

    def test_structure_bonus_capped(self):
        signal = SignalScore(has_headings=True, has_code_blocks=True)
        consensus = ConsensusScore(precision=1.0)
        page = PageQuality(
            url="http://example.com",
            tool="test",
            signal=signal,
            density=DensityScore(),
            consensus=consensus,
        )
        # structure = min(1.0 + 0.1 + 0.1, 1.2) = 1.2
        assert page.quality_score == 1.2


# =========================================================================
# Integration: score_signals -> consensus -> repetition pipeline
# =========================================================================

class TestIntegration:
    def test_full_pipeline(self):
        """Run signals + consensus + repetition on synthetic data."""
        md_a = "# Page Title\n\nThis is a well-structured page with enough words to pass the sentence filter easily."
        md_b = "# Page Title\n\nThis is a well-structured page with enough words to pass the sentence filter easily."
        md_c = "Nav junk\nSkip to content\n# Page Title\n\nThis is a well-structured page with enough words to pass the sentence filter easily."

        outputs = {"clean": md_a, "also_clean": md_b, "noisy": md_c}

        # Score signals
        sig_a = score_signals(md_a)
        sig_c = score_signals(md_c)
        assert sig_a.preamble_words == 0
        assert sig_c.preamble_words > 0
        assert "skip to content" in sig_c.junk_found

        # Consensus
        cons_a = score_consensus(md_a, outputs, "clean")
        cons_c = score_consensus(md_c, outputs, "noisy")
        assert cons_a.precision > 0
        assert cons_c.precision > 0

    def test_all_identical_output(self):
        """When all tools produce identical output, precision and recall are 1.0."""
        content = "# Title\n\nThis is a perfectly identical sentence with more than ten words for the extraction filter."
        outputs = {f"tool_{i}": content for i in range(5)}
        for name in outputs:
            result = score_consensus(content, outputs, name)
            assert result.precision == 1.0
            assert result.recall == 1.0
