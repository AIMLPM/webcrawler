"""Tests for markcrawl.chunker — text chunking for embeddings."""

from __future__ import annotations

from markcrawl.chunker import chunk_markdown, chunk_text


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
        text = (
            "# Intro\n\nSome content here with enough words to fill a chunk.\n\n"
            "## Details\n\nMore content here with additional words for the second chunk."
        )
        chunks = chunk_markdown(text, max_words=15, page_title="FastAPI Docs")
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.text.startswith("[Page: FastAPI Docs]")

    def test_page_title_single_chunk(self):
        text = "# Title\n\nShort paragraph."
        chunks = chunk_markdown(text, max_words=100, page_title="My Page")
        assert len(chunks) == 1
        assert chunks[0].text.startswith("[Page: My Page]")
        assert "# Title" in chunks[0].text

    def test_no_page_title_no_prefix(self):
        text = "# Title\n\nShort paragraph."
        chunks = chunk_markdown(text, max_words=100)
        assert not chunks[0].text.startswith("[Page:")
