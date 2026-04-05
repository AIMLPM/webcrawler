"""MarkCrawl — turn any website into clean Markdown for LLM pipelines."""

from .chunker import Chunk, chunk_markdown, chunk_text
from .core import CrawlResult, crawl

__all__ = ["crawl", "CrawlResult", "chunk_text", "chunk_markdown", "Chunk"]
