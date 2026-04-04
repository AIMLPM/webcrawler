"""MarkCrawl — turn any website into clean Markdown for LLM pipelines."""

from .core import crawl, CrawlResult
from .chunker import chunk_text, Chunk

__all__ = ["crawl", "CrawlResult", "chunk_text", "Chunk"]
