"""Split text into overlapping chunks for embedding and vector search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    text: str
    index: int
    total: int


def chunk_text(
    text: str,
    max_words: int = 400,
    overlap_words: int = 50,
) -> List[Chunk]:
    """Split *text* into word-based chunks with overlap.

    Parameters
    ----------
    text:
        The source text to split.
    max_words:
        Target maximum words per chunk.
    overlap_words:
        Number of words to repeat at the start of each subsequent chunk
        so that context is not lost at boundaries.

    Returns
    -------
    List[Chunk]
        Ordered chunks with their index and the total count.
    """
    words = text.split()
    if not words:
        return []

    if len(words) <= max_words:
        return [Chunk(text=text.strip(), index=0, total=1)]

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap_words

    total = len(chunks)
    return [Chunk(text=c, index=i, total=total) for i, c in enumerate(chunks)]
