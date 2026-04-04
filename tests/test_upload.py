"""Tests for markcrawl.upload — chunking + embedding + Supabase upload with mocked APIs."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from markcrawl.upload import generate_embeddings, load_pages, upload

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_jsonl(path: str, pages: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for page in pages:
            f.write(json.dumps(page, ensure_ascii=False) + "\n")


SAMPLE_PAGES = [
    {
        "url": "https://example.com/",
        "title": "Home",
        "text": " ".join(["word"] * 100),  # 100 words
    },
    {
        "url": "https://example.com/about",
        "title": "About",
        "text": " ".join(["content"] * 50),  # 50 words
    },
]


# ---------------------------------------------------------------------------
# load_pages
# ---------------------------------------------------------------------------

class TestUploadLoadPages:
    def test_loads_pages(self, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)

        pages = load_pages(path)
        assert len(pages) == 2
        assert pages[0]["url"] == "https://example.com/"

    def test_skips_empty_lines(self, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        with open(path, "w") as f:
            f.write(json.dumps(SAMPLE_PAGES[0]) + "\n")
            f.write("\n")  # empty line
            f.write(json.dumps(SAMPLE_PAGES[1]) + "\n")

        pages = load_pages(path)
        assert len(pages) == 2


# ---------------------------------------------------------------------------
# generate_embeddings
# ---------------------------------------------------------------------------

class TestGenerateEmbeddings:
    def test_generates_embeddings_for_texts(self):
        mock_client = MagicMock()

        # Mock embedding response
        mock_item = MagicMock()
        mock_item.embedding = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.data = [mock_item, mock_item]
        mock_client.embeddings.create.return_value = mock_response

        embeddings = generate_embeddings(
            texts=["hello", "world"],
            client=mock_client,
            model="text-embedding-3-small",
        )

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once()

    def test_batches_large_inputs(self):
        mock_client = MagicMock()

        mock_item = MagicMock()
        mock_item.embedding = [0.1]
        mock_response = MagicMock()
        mock_response.data = [mock_item] * 64
        mock_client.embeddings.create.return_value = mock_response

        # 128 texts should result in 2 batches (EMBED_BATCH_SIZE=64)
        texts = [f"text_{i}" for i in range(128)]
        embeddings = generate_embeddings(texts=texts, client=mock_client)

        assert mock_client.embeddings.create.call_count == 2
        assert len(embeddings) == 128


# ---------------------------------------------------------------------------
# upload (integration with mocked OpenAI + Supabase)
# ---------------------------------------------------------------------------

class TestUpload:
    @patch("markcrawl.upload._get_supabase_client")
    @patch("markcrawl.upload._get_openai_client")
    def test_uploads_chunked_pages(self, mock_openai, mock_supabase, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)

        # Mock OpenAI embeddings
        mock_embed_item = MagicMock()
        mock_embed_item.embedding = [0.1] * 1536
        mock_embed_response = MagicMock()
        mock_embed_response.data = [mock_embed_item] * 10  # enough for any batch
        openai_client = MagicMock()
        openai_client.embeddings.create.return_value = mock_embed_response
        mock_openai.return_value = openai_client

        # Mock Supabase
        supabase_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = None
        mock_table.insert.return_value = mock_insert
        supabase_client.table.return_value = mock_table
        mock_supabase.return_value = supabase_client

        inserted = upload(
            jsonl_path=path,
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            table="documents",
            max_words=50,
            overlap_words=10,
        )

        assert inserted > 0
        supabase_client.table.assert_called_with("documents")
        mock_table.insert.assert_called()

    @patch("markcrawl.upload._get_supabase_client")
    @patch("markcrawl.upload._get_openai_client")
    def test_returns_zero_for_empty_input(self, mock_openai, mock_supabase, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, [])

        inserted = upload(
            jsonl_path=path,
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
        )

        assert inserted == 0

    @patch("markcrawl.upload._get_supabase_client")
    @patch("markcrawl.upload._get_openai_client")
    def test_chunks_are_correct_size(self, mock_openai, mock_supabase, tmp_path):
        # Create a page with exactly 200 words
        pages = [{
            "url": "https://example.com/",
            "title": "Test",
            "text": " ".join([f"word{i}" for i in range(200)]),
        }]
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, pages)

        # Track what gets inserted
        inserted_rows = []
        supabase_client = MagicMock()
        mock_table = MagicMock()
        def capture_insert(batch):
            inserted_rows.extend(batch)
            mock_result = MagicMock()
            mock_result.execute.return_value = None
            return mock_result
        mock_table.insert.side_effect = capture_insert
        supabase_client.table.return_value = mock_table
        mock_supabase.return_value = supabase_client

        mock_embed_item = MagicMock()
        mock_embed_item.embedding = [0.1] * 1536
        mock_embed_response = MagicMock()
        mock_embed_response.data = [mock_embed_item] * 50
        openai_client = MagicMock()
        openai_client.embeddings.create.return_value = mock_embed_response
        mock_openai.return_value = openai_client

        upload(
            jsonl_path=path,
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            max_words=100,
            overlap_words=20,
        )

        # 200 words with max_words=100, overlap=20 → should produce multiple chunks
        assert len(inserted_rows) >= 2
        for row in inserted_rows:
            assert "chunk_text" in row
            assert "embedding" in row
            assert "url" in row
            assert row["url"] == "https://example.com/"

    @patch("markcrawl.upload._get_supabase_client")
    @patch("markcrawl.upload._get_openai_client")
    def test_metadata_includes_source_file(self, mock_openai, mock_supabase, tmp_path):
        pages = [{"url": "https://example.com/", "title": "T", "text": " ".join(["w"] * 50), "path": "test.md"}]
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, pages)

        inserted_rows = []
        supabase_client = MagicMock()
        mock_table = MagicMock()
        def capture_insert(batch):
            inserted_rows.extend(batch)
            m = MagicMock()
            m.execute.return_value = None
            return m
        mock_table.insert.side_effect = capture_insert
        supabase_client.table.return_value = mock_table
        mock_supabase.return_value = supabase_client

        mock_embed_item = MagicMock()
        mock_embed_item.embedding = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.data = [mock_embed_item] * 10
        openai_client = MagicMock()
        openai_client.embeddings.create.return_value = mock_resp
        mock_openai.return_value = openai_client

        upload(
            jsonl_path=path,
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
        )

        assert len(inserted_rows) > 0
        assert inserted_rows[0]["metadata"]["source_file"] == "test.md"
