"""Tests for markcrawl.chunker — text chunking for embeddings."""

from __future__ import annotations

from markcrawl.chunker import Chunk, chunk_text


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
