"""Read crawl output and upload chunked + embedded rows to Supabase."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chunker import chunk_text

logger = logging.getLogger(__name__)

# Embedding defaults
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
EMBED_BATCH_SIZE = 64  # OpenAI allows up to 2048, but 64 keeps requests small


def _get_openai_client() -> Any:
    try:
        import openai  # noqa: F811
    except ImportError:
        sys.exit(
            "The 'openai' package is required for embedding generation.\n"
            "Install it with:  pip install openai"
        )
    return openai.OpenAI()


def _get_supabase_client(url: str, key: str) -> Any:
    try:
        from supabase import create_client  # noqa: F811
    except ImportError:
        sys.exit(
            "The 'supabase' package is required for uploading.\n"
            "Install it with:  pip install supabase"
        )
    return create_client(url, key)


def generate_embeddings(
    texts: List[str],
    client: Any,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[List[float]]:
    """Generate embeddings for a batch of texts using OpenAI."""
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        response = client.embeddings.create(input=batch, model=model)
        all_embeddings.extend([item.embedding for item in response.data])
        if i + EMBED_BATCH_SIZE < len(texts):
            time.sleep(0.25)  # light rate-limit buffer
    return all_embeddings


def load_pages(jsonl_path: str) -> List[Dict[str, str]]:
    """Load pages from a crawl-produced JSONL file."""
    pages: List[Dict[str, str]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))
    return pages


def upload(
    jsonl_path: str,
    supabase_url: str,
    supabase_key: str,
    table: str = "documents",
    max_words: int = 400,
    overlap_words: int = 50,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    show_progress: bool = False,
    batch_size: int = 50,
) -> int:
    """Chunk, embed, and upload crawl output to Supabase.

    Returns the number of rows inserted.
    """
    pages = load_pages(jsonl_path)
    if not pages:
        logger.warning("No pages found in %s", jsonl_path)
        return 0

    openai_client = _get_openai_client()
    supabase = _get_supabase_client(supabase_url, supabase_key)

    # Build all rows with chunked text
    rows: List[Dict[str, Any]] = []
    for page in pages:
        chunks = chunk_text(page.get("text", ""), max_words=max_words, overlap_words=overlap_words)
        for chunk in chunks:
            rows.append(
                {
                    "url": page.get("url", ""),
                    "title": page.get("title", ""),
                    "chunk_text": chunk.text,
                    "chunk_index": chunk.index,
                    "chunk_total": chunk.total,
                    "metadata": {
                        "source_file": page.get("path", ""),
                    },
                }
            )

    if not rows:
        logger.warning("No chunks produced from %s", jsonl_path)
        return 0

    if show_progress:
        print(f"[info] {len(pages)} page(s) -> {len(rows)} chunk(s)")
        print(f"[info] generating embeddings with {embedding_model}...")

    # Generate embeddings for all chunks
    texts = [r["chunk_text"] for r in rows]
    embeddings = generate_embeddings(texts, openai_client, model=embedding_model)

    for row, embedding in zip(rows, embeddings):
        row["embedding"] = embedding

    # Insert in batches
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table(table).insert(batch).execute()
        inserted += len(batch)
        if show_progress:
            print(f"[prog] inserted {inserted}/{len(rows)} row(s)")

    return inserted
