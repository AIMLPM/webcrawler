"""Read crawl output and upload chunked + embedded rows to Supabase."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from .chunker import chunk_markdown, chunk_text
from .exceptions import MarkcrawlConfigError, MarkcrawlDependencyError
from .utils import load_pages

logger = logging.getLogger(__name__)

# Embedding defaults
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
EMBED_BATCH_SIZE = 64  # OpenAI allows up to 2048, but 64 keeps requests small


def _get_openai_client() -> Any:
    try:
        import openai  # noqa: F811
    except ImportError:
        raise MarkcrawlDependencyError(
            "The 'openai' package is required for embedding generation.\n"
            "Install it with:  pip install openai"
        )
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        raise MarkcrawlConfigError("OPENAI_API_KEY environment variable is required for embedding generation")
    return openai.OpenAI()


def _get_supabase_client(url: str, key: str) -> Any:
    try:
        from supabase import create_client  # noqa: F811
    except ImportError:
        raise MarkcrawlDependencyError(
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
    if not supabase_url:
        raise MarkcrawlConfigError("SUPABASE_URL is required")
    if not supabase_key:
        raise MarkcrawlConfigError("SUPABASE_KEY is required")

    pages = load_pages(jsonl_path)
    if not pages:
        logger.warning("No pages found in %s", jsonl_path)
        return 0

    openai_client = _get_openai_client()
    supabase = _get_supabase_client(supabase_url, supabase_key)

    # Build all rows with chunked text
    rows: List[Dict[str, Any]] = []
    for page in pages:
        # Use section-aware chunking for Markdown, word-count for plain text
        page_text = page.get("text", "")
        page_title = page.get("title", "") or None
        if page.get("path", "").endswith(".md") or page_text.startswith("#"):
            chunks = chunk_markdown(page_text, max_words=max_words, overlap_words=overlap_words, page_title=page_title)
        else:
            chunks = chunk_text(page_text, max_words=max_words, overlap_words=overlap_words)
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

    # Insert in batches with retry
    inserted = 0
    total_batches = (len(rows) + batch_size - 1) // batch_size
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            _insert_with_retry(supabase, table, batch)
        except Exception as exc:
            logger.error(
                "Failed at batch %d/%d (%d rows inserted so far): %s",
                i // batch_size + 1, total_batches, inserted, exc,
            )
            raise
        inserted += len(batch)
        if show_progress:
            print(f"[prog] inserted {inserted}/{len(rows)} row(s)")

    return inserted


_RETRY_MAX = 3
_RETRY_BASE_DELAY = 1.0


def _insert_with_retry(supabase, table: str, batch: list, max_retries: int = _RETRY_MAX) -> None:
    """Insert a batch into Supabase with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            supabase.table(table).insert(batch).execute()
            return
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            delay = _RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "Insert failed (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1, max_retries, delay, exc,
            )
            time.sleep(delay)
