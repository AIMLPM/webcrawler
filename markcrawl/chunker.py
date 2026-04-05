"""Split text into chunks for embedding and vector search.

Two strategies are available:

- :func:`chunk_text` — simple word-count splitting with overlap (fast, works
  on any text).
- :func:`chunk_markdown` — section-aware splitting that respects Markdown
  headings, then falls back to paragraph and word boundaries.  Produces
  more coherent chunks for RAG retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    text: str
    index: int
    total: int


# ---------------------------------------------------------------------------
# Word-based chunking (original, simple)
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    max_words: int = 400,
    overlap_words: int = 50,
) -> List[Chunk]:
    """Split *text* into word-based chunks with overlap.

    This is a simple, fast splitter that works on any text.  It does not
    respect semantic boundaries — it may split mid-sentence or mid-code-block.
    For Markdown content, prefer :func:`chunk_markdown`.

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


# ---------------------------------------------------------------------------
# Section-aware Markdown chunking
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)


def _split_on_headings(text: str) -> List[str]:
    """Split Markdown text on heading boundaries (# through ######).

    Each returned section starts with its heading line (except possibly
    the first section if the text begins without a heading).
    """
    positions = [m.start() for m in _HEADING_RE.finditer(text)]
    if not positions:
        return [text]

    sections: List[str] = []
    # Content before the first heading (if any)
    if positions[0] > 0:
        preamble = text[: positions[0]].strip()
        if preamble:
            sections.append(preamble)

    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        section = text[pos:end].strip()
        if section:
            sections.append(section)

    return sections


def _split_on_paragraphs(text: str) -> List[str]:
    """Split text on blank-line paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_markdown(
    text: str,
    max_words: int = 400,
    overlap_words: int = 50,
) -> List[Chunk]:
    """Split Markdown text into semantically coherent chunks.

    Splitting strategy (in order of preference):

    1. **Headings** — split on ``#`` through ``######`` boundaries so each
       section stays together.
    2. **Paragraphs** — if a section exceeds *max_words*, split on blank
       lines (paragraph boundaries).
    3. **Word count** — if a single paragraph still exceeds *max_words*,
       fall back to :func:`chunk_text` word-count splitting with overlap.

    This produces chunks that respect document structure, keeping code
    blocks, tables, and sentences intact whenever possible.

    Parameters
    ----------
    text:
        Markdown source text.
    max_words:
        Target maximum words per chunk.
    overlap_words:
        Overlap words used when falling back to word-count splitting.

    Returns
    -------
    List[Chunk]
        Ordered chunks with their index and the total count.
    """
    text = text.strip()
    if not text:
        return []

    if _word_count(text) <= max_words:
        return [Chunk(text=text, index=0, total=1)]

    # Step 1: split on headings
    sections = _split_on_headings(text)

    # Step 2: for oversized sections, split on paragraphs
    fragments: List[str] = []
    for section in sections:
        if _word_count(section) <= max_words:
            fragments.append(section)
        else:
            paragraphs = _split_on_paragraphs(section)
            # Try to merge small consecutive paragraphs into one chunk
            current = ""
            for para in paragraphs:
                if current and _word_count(current + "\n\n" + para) > max_words:
                    fragments.append(current)
                    current = para
                else:
                    current = (current + "\n\n" + para) if current else para
            if current:
                fragments.append(current)

    # Step 3: for oversized fragments, fall back to word-count splitting
    final_chunks: List[str] = []
    for fragment in fragments:
        if _word_count(fragment) <= max_words:
            final_chunks.append(fragment)
        else:
            # Use word-count chunking as last resort
            sub_chunks = chunk_text(fragment, max_words=max_words, overlap_words=overlap_words)
            final_chunks.extend(c.text for c in sub_chunks)

    total = len(final_chunks)
    return [Chunk(text=c, index=i, total=total) for i, c in enumerate(final_chunks)]
