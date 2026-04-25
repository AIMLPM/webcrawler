"""Tests for markcrawl.chunker — text chunking for embeddings."""

from __future__ import annotations

from markcrawl.chunker import _estimate_adaptive_max_words, _find_sentence_boundary, chunk_markdown, chunk_text


class TestChunkText:
    def test_empty_string_returns_empty(self):
        assert chunk_text("") == []

    def test_short_text_returns_single_chunk(self):
        text = "Hello world this is a test"
        chunks = chunk_text(text, max_words=100)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
        assert chunks[0].total == 1

    def test_splits_long_text(self):
        words = ["word"] * 100
        text = " ".join(words)
        chunks = chunk_text(text, max_words=30, overlap_words=5)
        assert len(chunks) > 1
        # Each chunk should have at most 30 words
        for chunk in chunks:
            assert len(chunk.text.split()) <= 30

    def test_overlap_creates_shared_words(self):
        words = [f"w{i}" for i in range(60)]
        text = " ".join(words)
        chunks = chunk_text(text, max_words=30, overlap_words=10)
        assert len(chunks) == 3

        # Last 10 words of chunk 0 should be first 10 words of chunk 1
        c0_words = chunks[0].text.split()
        c1_words = chunks[1].text.split()
        assert c0_words[-10:] == c1_words[:10]

    def test_index_and_total_are_correct(self):
        words = ["word"] * 200
        text = " ".join(words)
        chunks = chunk_text(text, max_words=50, overlap_words=10)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert chunk.total == len(chunks)

    def test_all_words_are_covered(self):
        words = [f"w{i}" for i in range(85)]
        text = " ".join(words)
        chunks = chunk_text(text, max_words=30, overlap_words=5)

        # First word should be in first chunk
        assert "w0" in chunks[0].text
        # Last word should be in last chunk
        assert "w84" in chunks[-1].text

    def test_exact_boundary(self):
        words = ["word"] * 30
        text = " ".join(words)
        chunks = chunk_text(text, max_words=30, overlap_words=5)
        assert len(chunks) == 1

    def test_one_over_boundary(self):
        words = ["word"] * 31
        text = " ".join(words)
        chunks = chunk_text(text, max_words=30, overlap_words=5)
        assert len(chunks) == 2


class TestChunkMarkdown:
    def test_empty_returns_empty(self):
        assert chunk_markdown("") == []

    def test_short_text_returns_single_chunk(self):
        text = "# Title\n\nShort paragraph."
        chunks = chunk_markdown(text, max_words=100)
        assert len(chunks) == 1
        assert "Title" in chunks[0].text

    def test_splits_on_headings(self):
        text = (
            "# Section One\n\nContent for section one with enough words.\n\n"
            "## Section Two\n\nContent for section two with enough words.\n\n"
            "## Section Three\n\nContent for section three with enough words."
        )
        chunks = chunk_markdown(text, max_words=20)
        assert len(chunks) == 3
        assert "Section One" in chunks[0].text
        assert "Section Two" in chunks[1].text
        assert "Section Three" in chunks[2].text

    def test_keeps_small_sections_together(self):
        text = (
            "# Intro\n\nShort intro.\n\n"
            "## Details\n\nShort details."
        )
        # Both sections are small enough to fit in one chunk
        chunks = chunk_markdown(text, max_words=100)
        assert len(chunks) == 1

    def test_splits_large_section_on_paragraphs(self):
        paragraphs = [f"Paragraph {i} " + " ".join(["word"] * 30) for i in range(5)]
        text = "# Big Section\n\n" + "\n\n".join(paragraphs)
        chunks = chunk_markdown(text, max_words=50)
        # Should split into multiple chunks, but not mid-paragraph
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text.split()) <= 55  # allow some flexibility

    def test_preserves_code_blocks(self):
        text = (
            "# API Guide\n\n"
            "Here's how to authenticate:\n\n"
            "```python\n"
            "import requests\n"
            "client = requests.Session()\n"
            "client.headers['Authorization'] = 'Bearer token'\n"
            "response = client.get('https://api.example.com/users')\n"
            "print(response.json())\n"
            "```\n\n"
            "## Next Steps\n\nContinue with the tutorial."
        )
        chunks = chunk_markdown(text, max_words=100)
        # Code block should stay intact in one chunk
        code_chunks = [c for c in chunks if "```python" in c.text]
        assert len(code_chunks) == 1
        assert "client.get" in code_chunks[0].text

    def test_falls_back_to_word_split_for_huge_paragraph(self):
        huge_para = " ".join(["word"] * 500)
        text = f"# Title\n\n{huge_para}"
        chunks = chunk_markdown(text, max_words=100, overlap_words=20)
        assert len(chunks) > 1

    def test_index_and_total_correct(self):
        text = (
            "# A\n\nContent A words here.\n\n"
            "# B\n\nContent B words here.\n\n"
            "# C\n\nContent C words here."
        )
        chunks = chunk_markdown(text, max_words=10)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert chunk.total == len(chunks)

    def test_no_headings_falls_back_to_paragraphs(self):
        text = "First paragraph with enough words.\n\nSecond paragraph with enough words.\n\nThird paragraph."
        chunks = chunk_markdown(text, max_words=8)
        assert len(chunks) >= 2

    def test_heading_carried_forward_on_paragraph_split(self):
        # A section too large to fit in one chunk should carry its heading
        paragraphs = [f"Paragraph {i} " + " ".join(["word"] * 20) for i in range(4)]
        text = "## API Reference\n\n" + "\n\n".join(paragraphs)
        chunks = chunk_markdown(text, max_words=30)
        assert len(chunks) > 1
        # First chunk naturally has the heading
        assert chunks[0].text.startswith("## API Reference")
        # Subsequent chunks should also carry the heading
        for chunk in chunks[1:]:
            assert "## API Reference" in chunk.text

    def test_heading_carried_forward_on_word_split(self):
        # A single huge paragraph under a heading
        huge = " ".join(["word"] * 200)
        text = f"## Big Section\n\n{huge}"
        chunks = chunk_markdown(text, max_words=50, overlap_words=10)
        assert len(chunks) > 1
        # All chunks should carry the heading
        for chunk in chunks:
            assert "## Big Section" in chunk.text

    def test_page_title_prepended(self):
        # Non-H1 chunks get a `Section: Page > H1 > H2` breadcrumb so retrieval
        # has full ancestor context. H1 chunks skip it — the H1 is already
        # distinctive, and doubling up inflates similarity on generic
        # page-topic queries.
        text = (
            "# Intro\n\nSome content here with enough words to fill a chunk.\n\n"
            "## Details\n\nMore content here with additional words for the second chunk."
        )
        chunks = chunk_markdown(text, max_words=15, page_title="FastAPI Docs")
        assert len(chunks) >= 2
        h1_chunks = [c for c in chunks if c.text.lstrip().startswith("# ")]
        other_chunks = [c for c in chunks if not c.text.lstrip().startswith("# ")]
        assert h1_chunks, "expected at least one H1 chunk"
        assert other_chunks, "expected at least one non-H1 chunk"
        for chunk in other_chunks:
            assert chunk.text.startswith("Section: FastAPI Docs")
        for chunk in h1_chunks:
            assert not chunk.text.startswith("Section:")

    def test_breadcrumb_includes_ancestor_headings(self):
        text = (
            "# Intro\n\n" + " ".join(["intro"] * 30) + "\n\n"
            "## Details\n\n" + " ".join(["detail"] * 30)
        )
        chunks = chunk_markdown(text, max_words=40, page_title="FastAPI Docs")
        detail_chunks = [c for c in chunks if "detail" in c.text and not c.text.lstrip().startswith("# ")]
        assert detail_chunks, "expected a chunk under Details"
        # The breadcrumb's first line should include the Intro ancestor
        for c in detail_chunks:
            first_line = c.text.split("\n", 1)[0]
            assert "Intro" in first_line and "Details" in first_line

    def test_page_title_single_chunk(self):
        text = "# Title\n\nShort paragraph."
        chunks = chunk_markdown(text, max_words=100, page_title="My Page")
        assert len(chunks) == 1
        # H1 present → breadcrumb prefix is skipped to avoid redundancy.
        assert chunks[0].text.startswith("# Title")
        assert not chunks[0].text.startswith("Section:")

    def test_page_title_single_chunk_without_h1(self):
        text = "Short paragraph without any heading."
        chunks = chunk_markdown(text, max_words=100, page_title="My Page")
        assert len(chunks) == 1
        assert chunks[0].text.startswith("Section: My Page")

    def test_no_page_title_no_prefix(self):
        text = "# Title\n\nShort paragraph."
        chunks = chunk_markdown(text, max_words=100)
        assert not chunks[0].text.startswith("Section:")


class TestSentenceBoundary:
    def test_finds_period_boundary(self):
        words = "The quick brown fox jumped. The lazy dog slept. More words here now".split()
        # words: [The(0) quick(1) brown(2) fox(3) jumped.(4) The(5) lazy(6) dog(7) slept.(8) More(9) ...]
        # target=10, search back: words[9]="More" no, words[8]="slept." yes → return 9
        result = _find_sentence_boundary(words, 10, window=5)
        assert result == 9

    def test_finds_question_mark(self):
        words = "Is this working? Yes it is working fine now".split()
        result = _find_sentence_boundary(words, 6, window=5)
        # words[2] is "working?" — boundary at index 3
        assert result == 3

    def test_finds_exclamation(self):
        words = "Watch out! The bridge is falling down quickly now".split()
        result = _find_sentence_boundary(words, 7, window=5)
        # words[1] is "out!" — boundary at index 2
        assert result == 2

    def test_strips_trailing_quote(self):
        words = ['He', 'said', '"hello."', 'Then', 'he', 'left', 'quickly', 'after']
        result = _find_sentence_boundary(words, 6, window=5)
        # words[2] is '"hello."' — stripped gives 'hello.' ends in .
        assert result == 3

    def test_no_boundary_returns_target(self):
        words = "one two three four five six seven eight nine ten".split()
        result = _find_sentence_boundary(words, 8, window=5)
        assert result == 8

    def test_respects_min_pos(self):
        words = "Done. one two three four five six seven".split()
        # "Done." is at index 0, boundary at 1, but min_pos=3
        result = _find_sentence_boundary(words, 6, window=10, min_pos=3)
        assert result == 6  # Falls back to target

    def test_chunk_text_snaps_to_sentence(self):
        # Build text where sentence boundary falls within the search window
        s1 = "The quick brown fox jumped over the lazy dog."  # 9 words
        s2 = "Another sentence with several words in it."  # 7 words
        s3 = "A third sentence that continues on and on."  # 9 words
        text = f"{s1} {s2} {s3}"
        chunks = chunk_text(text, max_words=12, overlap_words=2)
        # First chunk should end at a sentence boundary (9 or 16 words)
        # With max_words=12, target is 12, search back finds "dog." at 9
        assert chunks[0].text.endswith("dog.")

    def test_chunk_text_all_content_preserved(self):
        sentences = [f"Sentence number {i} has some words in it." for i in range(10)]
        text = " ".join(sentences)
        chunks = chunk_text(text, max_words=20, overlap_words=3)
        # All sentences should appear somewhere in the chunks
        all_text = " ".join(c.text for c in chunks)
        for i in range(10):
            assert f"Sentence number {i}" in all_text

    def test_chunk_text_no_sentence_enders_still_works(self):
        # Text with no sentence-ending punctuation falls back to word boundary
        words = [f"w{i}" for i in range(50)]
        text = " ".join(words)
        chunks = chunk_text(text, max_words=20, overlap_words=3)
        assert len(chunks) > 1
        assert "w0" in chunks[0].text
        assert "w49" in chunks[-1].text

    def test_smart_overlap_skipped_at_sentence_boundary(self):
        # When splits land on sentence boundaries, overlap is skipped
        sentences = [f"Sentence {i} has exactly seven words here." for i in range(6)]
        text = " ".join(sentences)
        # max_words=10, overlap=3 — each sentence is 7 words
        # With sentence splits: chunk 1 = S0 (7w), chunk 2 = S1 (7w), etc.
        # Without smart overlap, chunks would contain overlapping words
        chunks = chunk_text(text, max_words=10, overlap_words=3)
        # With smart overlap, no repeated words between consecutive chunks
        for i in range(len(chunks) - 1):
            c1_last_3 = chunks[i].text.split()[-3:]
            c2_first_3 = chunks[i + 1].text.split()[:3]
            # The first words of chunk 2 should NOT be the last words of chunk 1
            assert c1_last_3 != c2_first_3

    def test_overlap_still_applied_without_sentence_boundary(self):
        # When no sentence boundary found, overlap is applied as before
        words = [f"w{i}" for i in range(60)]
        text = " ".join(words)
        chunks = chunk_text(text, max_words=20, overlap_words=5)
        assert len(chunks) > 1
        # Last 5 words of chunk 0 should be first 5 of chunk 1 (overlap applied)
        c0_words = chunks[0].text.split()
        c1_words = chunks[1].text.split()
        assert c0_words[-5:] == c1_words[:5]


class TestAdaptiveChunking:
    def test_code_heavy_gets_smaller_chunks(self):
        # Mostly code blocks, minimal prose
        code_text = "# API Reference\n\n" + "\n\n".join(
            f"```python\ndef func_{i}(x, y):\n    result = x + y * {i}\n    return result\n```"
            for i in range(20)
        )
        result = _estimate_adaptive_max_words(code_text, base=400)
        # Code-heavy → should be below base
        assert result < 400

    def test_narrative_gets_larger_chunks(self):
        # Long prose paragraphs, no code, no lists, few headings
        prose = "# Introduction\n\n" + "\n\n".join(
            f"This is paragraph {i} of a long article about a complex topic that "
            "requires careful explanation and nuanced discussion with many details "
            "woven into the narrative that builds understanding over multiple sentences."
            for i in range(8)
        )
        result = _estimate_adaptive_max_words(prose, base=400)
        # Narrative → should be above base (low density)
        assert result >= 400

    def test_list_heavy_gets_smaller_chunks(self):
        # Almost entirely list items
        list_text = "# Config\n\n## Options\n\n" + "\n".join(
            f"- option_{i}: value" for i in range(50)
        ) + "\n\n## Flags\n\n" + "\n".join(
            f"- flag_{i}: on" for i in range(50)
        )
        result = _estimate_adaptive_max_words(list_text, base=400)
        assert result < 400

    def test_floor_at_100(self):
        # Even extreme density shouldn't go below 100
        extreme = "```\n" + "\n".join("x" for _ in range(100)) + "\n```"
        result = _estimate_adaptive_max_words(extreme, base=100)
        assert result >= 100

    def test_adaptive_flag_changes_chunk_count(self):
        # Code-heavy content should produce more (smaller) chunks with adaptive=True
        code_text = "# API\n\n" + "\n\n".join(
            f"```python\ndef func_{i}():\n    return {i}\n```\n\nDescription {i} with enough words to fill up space."
            for i in range(15)
        )
        fixed = chunk_markdown(code_text, max_words=400, adaptive=False)
        adaptive = chunk_markdown(code_text, max_words=400, adaptive=True)
        # Adaptive should produce at least as many chunks (smaller size → more chunks)
        assert len(adaptive) >= len(fixed)
