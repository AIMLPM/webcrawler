#!/usr/bin/env python3
"""Retrieval quality benchmark — embed each tool's output, run queries, compare hit rates.

Measures what actually matters for RAG: does the right page surface when you
ask a question?  Uses the same chunking strategy and embedding model for all
tools so the only variable is extraction quality.

Supports four retrieval modes:
  - Embedding-only (cosine similarity)
  - BM25 keyword search
  - Hybrid (embedding + BM25 via Reciprocal Rank Fusion)
  - Reranked (hybrid results reranked by a cross-encoder)

    python benchmarks/benchmark_retrieval.py                        # latest run
    python benchmarks/benchmark_retrieval.py --run run_20260405_221158
    python benchmarks/benchmark_retrieval.py --output my_report.md
    python benchmarks/benchmark_retrieval.py --chunk-sizes 256,512,1024

Requires:
    pip install openai numpy rank_bm25 sentence-transformers
    export OPENAI_API_KEY=sk-...
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BENCH_DIR = Path(__file__).parent
REPO_ROOT = BENCH_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from markcrawl.chunker import Chunk, chunk_markdown

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOOLS = [
    "markcrawl", "crawl4ai", "crawl4ai-raw", "scrapy+md",
    "crawlee", "colly+md", "playwright", "firecrawl",
]

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
TOP_K = 50  # Retrieve top-50 candidates for reranking pipeline
REPORT_AT_K = [1, 3, 5, 10, 20]  # Report hit rates at each K value
CHUNK_MAX_WORDS = 400
CHUNK_OVERLAP = 50

# Chunk size sensitivity: test at multiple configurations
# Each entry is (max_words, overlap_words, label)
CHUNK_CONFIGS = [
    (200, 30, "~256tok"),
    (400, 50, "~512tok"),
    (800, 100, "~1024tok"),
]
DEFAULT_CHUNK_CONFIG = (400, 50, "~512tok")  # Used when not running sensitivity

# Cross-encoder reranking model
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_TOP_N = 20  # Rerank top-N from initial retrieval

# BM25 + Embedding fusion weight (for RRF)
RRF_K = 60  # Reciprocal Rank Fusion constant

# Test queries per site.  Each query has:
#   - query text (what a user would ask)
#   - expected URL substring (identifies the correct source page)
#   - description (what the query tests)
#
# ~50 total queries across 4 sites for statistical significance.
# All url_match values verified against actually-crawled pages.
TEST_QUERIES: Dict[str, List[Dict]] = {
    "quotes-toscrape": [
        {
            "query": "What did Albert Einstein say about thinking and the world?",
            "url_match": "quotes.toscrape.com",
            "page_match": "einstein",
            "description": "Find a specific quote by author",
        },
        {
            "query": "Which quotes are tagged with 'inspirational'?",
            "url_match": "tag/inspirational",
            "page_match": "inspirational",
            "description": "Find content by tag",
        },
        {
            "query": "What did Jane Austen say about novels and reading?",
            "url_match": "author/Jane-Austen",
            "page_match": "austen",
            "description": "Find author-specific content",
        },
        {
            "query": "What quotes are about the truth?",
            "url_match": "tag/truth",
            "page_match": "truth",
            "description": "Find tag page for truth",
        },
        {
            "query": "Which quotes are about humor and being funny?",
            "url_match": "tag/humor",
            "page_match": "humor",
            "description": "Find humor tag page",
        },
        {
            "query": "What did J.K. Rowling say about choices and abilities?",
            "url_match": "author/J-K-Rowling",
            "page_match": "rowling",
            "description": "Find J.K. Rowling author page",
        },
        {
            "query": "What quotes are tagged with 'change'?",
            "url_match": "tag/change",
            "page_match": "change",
            "description": "Find change tag page",
        },
        {
            "query": "What did Steve Martin say about sunshine?",
            "url_match": "author/Steve-Martin",
            "page_match": "steve-martin",
            "description": "Find Steve Martin author page",
        },
        {
            "query": "Which quotes talk about believing in yourself?",
            "url_match": "tag/be-yourself",
            "page_match": "be-yourself",
            "description": "Find be-yourself tag page",
        },
        {
            "query": "What are the quotes about miracles and living life?",
            "url_match": "tag/miracle",
            "page_match": "miracle",
            "description": "Find miracle tag page",
        },
        {
            "query": "What quotes are about thinking deeply?",
            "url_match": "tag/thinking",
            "page_match": "thinking",
            "description": "Find thinking tag page",
        },
        {
            "query": "What quotes talk about living life fully?",
            "url_match": "tag/live",
            "page_match": "live",
            "description": "Find live tag page",
        },
    ],
    "books-toscrape": [
        {
            "query": "What books are available for under 20 pounds?",
            "url_match": "books.toscrape.com",
            "page_match": "",
            "description": "Price-based product search",
        },
        {
            "query": "What mystery and thriller books are in the catalog?",
            "url_match": "mystery",
            "page_match": "mystery",
            "description": "Category-based search",
        },
        {
            "query": "What is the rating of the most expensive book?",
            "url_match": "books.toscrape.com",
            "page_match": "",
            "description": "Find specific product detail",
        },
        {
            "query": "What science fiction books are available?",
            "url_match": "science-fiction",
            "page_match": "science-fiction",
            "description": "Find science fiction category",
        },
        {
            "query": "What horror books are in the catalog?",
            "url_match": "horror",
            "page_match": "horror",
            "description": "Find horror category",
        },
        {
            "query": "What poetry books can I find?",
            "url_match": "poetry",
            "page_match": "poetry",
            "description": "Find poetry category",
        },
        {
            "query": "What romance novels are available?",
            "url_match": "romance",
            "page_match": "romance",
            "description": "Find romance category",
        },
        {
            "query": "What history books are in the collection?",
            "url_match": "history",
            "page_match": "history",
            "description": "Find history category",
        },
        {
            "query": "What philosophy books are available to read?",
            "url_match": "philosophy",
            "page_match": "philosophy",
            "description": "Find philosophy category",
        },
        {
            "query": "What humor and comedy books can I find?",
            "url_match": "humor",
            "page_match": "humor",
            "description": "Find humor category",
        },
        {
            "query": "What fantasy books are in the bookstore?",
            "url_match": "fantasy",
            "page_match": "fantasy",
            "description": "Find fantasy category",
        },
        {
            "query": "What is the book Sharp Objects about?",
            "url_match": "sharp-objects",
            "page_match": "sharp-objects",
            "description": "Find specific book page",
        },
        {
            "query": "What biography books are in the catalog?",
            "url_match": "biography",
            "page_match": "biography",
            "description": "Find biography category",
        },
    ],
    "fastapi-docs": [
        {
            "query": "How do I add authentication to a FastAPI endpoint?",
            "url_match": "security",
            "page_match": "security",
            "description": "Find conceptual/tutorial content",
        },
        {
            "query": "What is the default response status code in FastAPI?",
            "url_match": "fastapi",
            "page_match": "response",
            "description": "Find specific technical detail",
        },
        {
            "query": "How do I define query parameters in the FastAPI reference?",
            "url_match": "reference/fastapi",
            "page_match": "reference",
            "description": "Find API reference content",
        },
        {
            "query": "How does FastAPI handle JSON encoding and base64 bytes?",
            "url_match": "json-base64-bytes",
            "page_match": "json-base64",
            "description": "Find advanced encoding content",
        },
        {
            "query": "What Python types does FastAPI support for request bodies?",
            "url_match": "body",
            "page_match": "body",
            "description": "Find reference content",
        },
        {
            "query": "How do I use OAuth2 with password flow in FastAPI?",
            "url_match": "simple-oauth2",
            "page_match": "oauth2",
            "description": "Find OAuth2 tutorial",
        },
        {
            "query": "How do I use WebSockets in FastAPI?",
            "url_match": "websockets",
            "page_match": "websocket",
            "description": "Find WebSocket documentation",
        },
        {
            "query": "How do I stream data responses in FastAPI?",
            "url_match": "stream-data",
            "page_match": "stream",
            "description": "Find streaming documentation",
        },
        {
            "query": "How do I return additional response types in FastAPI?",
            "url_match": "additional-responses",
            "page_match": "additional-response",
            "description": "Find additional responses docs",
        },
        {
            "query": "How do I write async tests for FastAPI applications?",
            "url_match": "async-tests",
            "page_match": "async-test",
            "description": "Find testing documentation",
        },
        {
            "query": "How do I define nested Pydantic models for request bodies?",
            "url_match": "body-nested-models",
            "page_match": "body-nested",
            "description": "Find nested model tutorial",
        },
        {
            "query": "How do I handle startup and shutdown events in FastAPI?",
            "url_match": "events",
            "page_match": "event",
            "description": "Find lifecycle events docs",
        },
        {
            "query": "How do I use middleware in FastAPI?",
            "url_match": "middleware",
            "page_match": "middleware",
            "description": "Find middleware reference",
        },
        {
            "query": "How do I use Jinja2 templates in FastAPI?",
            "url_match": "templating",
            "page_match": "templat",
            "description": "Find templating reference",
        },
        {
            "query": "How do I deploy FastAPI to the cloud?",
            "url_match": "deployment",
            "page_match": "deploy",
            "description": "Find deployment documentation",
        },
    ],
    "python-docs": [
        {
            "query": "What new features were added in Python 3.10?",
            "url_match": "whatsnew",
            "page_match": "whatsnew",
            "description": "Find release notes content",
        },
        {
            "query": "What does the term 'decorator' mean in Python?",
            "url_match": "glossary",
            "page_match": "glossary",
            "description": "Find glossary definition",
        },
        {
            "query": "How do I report a bug in Python?",
            "url_match": "bugs",
            "page_match": "bugs",
            "description": "Find meta/process content",
        },
        {
            "query": "What is structural pattern matching in Python?",
            "url_match": "whatsnew",
            "page_match": "whatsnew",
            "description": "Find specific feature documentation",
        },
        {
            "query": "What is Python's glossary definition of a generator?",
            "url_match": "glossary",
            "page_match": "glossary",
            "description": "Find glossary generator definition",
        },
        {
            "query": "What are the Python how-to guides about?",
            "url_match": "howto",
            "page_match": "howto",
            "description": "Find how-to index page",
        },
        {
            "query": "What is the Python module index?",
            "url_match": "py-modindex",
            "page_match": "modindex",
            "description": "Find module index page",
        },
        {
            "query": "What Python tutorial topics are available?",
            "url_match": "tutorial",
            "page_match": "tutorial",
            "description": "Find tutorial index page",
        },
        {
            "query": "What is the Python license and copyright?",
            "url_match": "license",
            "page_match": "license",
            "description": "Find license page",
        },
        {
            "query": "What is the table of contents for Python 3.10 documentation?",
            "url_match": "contents",
            "page_match": "contents",
            "description": "Find contents page",
        },
        {
            "query": "What does the term 'iterable' mean in Python?",
            "url_match": "glossary",
            "page_match": "glossary",
            "description": "Find glossary iterable definition",
        },
        {
            "query": "How do I install and configure Python on my system?",
            "url_match": "using",
            "page_match": "using",
            "description": "Find setup/usage guide",
        },
    ],
    # --- New diverse sites (SPA, wiki, API docs, blog) ---
    "react-dev": [
        {
            "query": "How do I manage state in a React component?",
            "url_match": "state",
            "page_match": "state",
            "description": "Find state management docs",
        },
        {
            "query": "What are React hooks and how do I use them?",
            "url_match": "hooks",
            "page_match": "hook",
            "description": "Find hooks introduction",
        },
        {
            "query": "How does the useEffect hook work in React?",
            "url_match": "useEffect",
            "page_match": "effect",
            "description": "Find useEffect reference",
        },
        {
            "query": "How do I handle forms and user input in React?",
            "url_match": "input",
            "page_match": "form",
            "description": "Find form handling docs",
        },
        {
            "query": "How do I create and use context in React?",
            "url_match": "context",
            "page_match": "context",
            "description": "Find context API docs",
        },
        {
            "query": "How do I handle events like clicks in React?",
            "url_match": "event",
            "page_match": "event",
            "description": "Find event handling docs",
        },
        {
            "query": "What is JSX and how does React use it?",
            "url_match": "jsx",
            "page_match": "jsx",
            "description": "Find JSX explanation",
        },
        {
            "query": "How do I render lists and use keys in React?",
            "url_match": "list",
            "page_match": "list",
            "description": "Find list rendering docs",
        },
        {
            "query": "How do I use the useRef hook in React?",
            "url_match": "useRef",
            "page_match": "ref",
            "description": "Find useRef reference",
        },
        {
            "query": "How do I pass props between React components?",
            "url_match": "props",
            "page_match": "props",
            "description": "Find props tutorial",
        },
        {
            "query": "How do I conditionally render content in React?",
            "url_match": "conditional",
            "page_match": "conditional",
            "description": "Find conditional rendering docs",
        },
        {
            "query": "What is the useMemo hook for in React?",
            "url_match": "useMemo",
            "page_match": "memo",
            "description": "Find useMemo reference",
        },
    ],
    "wikipedia-python": [
        {
            "query": "Who created the Python programming language?",
            "url_match": "Python_(programming_language)",
            "page_match": "python",
            "description": "Find Python main article",
        },
        {
            "query": "What is the history and development of Python?",
            "url_match": "Python_(programming_language)",
            "page_match": "python",
            "description": "Find Python history section",
        },
        {
            "query": "What programming paradigms does Python support?",
            "url_match": "Python_(programming_language)",
            "page_match": "python",
            "description": "Find Python paradigm info",
        },
        {
            "query": "What is the Python Software Foundation?",
            "url_match": "Python_Software_Foundation",
            "page_match": "foundation",
            "description": "Find PSF article",
        },
        {
            "query": "What is the syntax and design philosophy of Python?",
            "url_match": "Python_(programming_language)",
            "page_match": "python",
            "description": "Find Python design philosophy",
        },
        {
            "query": "What are Python's standard library modules?",
            "url_match": "Python_(programming_language)",
            "page_match": "python",
            "description": "Find standard library info",
        },
        {
            "query": "Who is Guido van Rossum?",
            "url_match": "Guido_van_Rossum",
            "page_match": "guido",
            "description": "Find Guido bio article",
        },
        {
            "query": "What is CPython and how does it work?",
            "url_match": "CPython",
            "page_match": "cpython",
            "description": "Find CPython article",
        },
        {
            "query": "How does Python compare to other programming languages?",
            "url_match": "Comparison_of_programming_languages",
            "page_match": "comparison",
            "description": "Find language comparison",
        },
        {
            "query": "What are Python Enhancement Proposals (PEPs)?",
            "url_match": "Python_(programming_language)",
            "page_match": "pep",
            "description": "Find PEP information",
        },
    ],
    "stripe-docs": [
        {
            "query": "How do I create a payment intent with Stripe?",
            "url_match": "payment-intent",
            "page_match": "payment",
            "description": "Find payment intent docs",
        },
        {
            "query": "How do I handle webhooks from Stripe?",
            "url_match": "webhook",
            "page_match": "webhook",
            "description": "Find webhook handling docs",
        },
        {
            "query": "How do I set up Stripe subscriptions?",
            "url_match": "subscription",
            "page_match": "subscription",
            "description": "Find subscription docs",
        },
        {
            "query": "How do I authenticate with the Stripe API?",
            "url_match": "authentication",
            "page_match": "auth",
            "description": "Find authentication docs",
        },
        {
            "query": "How do I handle errors in the Stripe API?",
            "url_match": "error",
            "page_match": "error",
            "description": "Find error handling docs",
        },
        {
            "query": "How do I create a customer in Stripe?",
            "url_match": "customer",
            "page_match": "customer",
            "description": "Find customer creation docs",
        },
        {
            "query": "How do I process refunds with Stripe?",
            "url_match": "refund",
            "page_match": "refund",
            "description": "Find refund docs",
        },
        {
            "query": "How do I use Stripe checkout for payments?",
            "url_match": "checkout",
            "page_match": "checkout",
            "description": "Find checkout docs",
        },
        {
            "query": "How do I test Stripe payments in development?",
            "url_match": "test",
            "page_match": "test",
            "description": "Find testing docs",
        },
        {
            "query": "What are Stripe Connect and platform payments?",
            "url_match": "connect",
            "page_match": "connect",
            "description": "Find Connect docs",
        },
    ],
    "blog-engineering": [
        {
            "query": "What are best practices for building reliable distributed systems?",
            "url_match": "blog",
            "page_match": "distribut",
            "description": "Find distributed systems content",
        },
        {
            "query": "How do companies handle database migrations at scale?",
            "url_match": "blog",
            "page_match": "migrat",
            "description": "Find migration content",
        },
        {
            "query": "What monitoring and observability tools do engineering teams use?",
            "url_match": "blog",
            "page_match": "monitor",
            "description": "Find observability content",
        },
        {
            "query": "How do you implement continuous deployment pipelines?",
            "url_match": "blog",
            "page_match": "deploy",
            "description": "Find CI/CD content",
        },
        {
            "query": "What are common microservices architecture patterns?",
            "url_match": "blog",
            "page_match": "microservice",
            "description": "Find microservices content",
        },
        {
            "query": "How do you handle API versioning in production?",
            "url_match": "blog",
            "page_match": "api",
            "description": "Find API design content",
        },
        {
            "query": "What caching strategies work best for web applications?",
            "url_match": "blog",
            "page_match": "cach",
            "description": "Find caching content",
        },
        {
            "query": "How do you design for high availability and fault tolerance?",
            "url_match": "blog",
            "page_match": "availab",
            "description": "Find HA content",
        },
    ],
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EmbeddedChunk:
    text: str
    url: str
    tool: str
    site: str
    chunk_index: int
    vector: List[float] = field(default_factory=list, repr=False)


@dataclass
class QueryResult:
    query: str
    description: str
    expected_url_match: str
    expected_page_match: str
    top_k_urls: List[str]
    top_k_scores: List[float]
    hit: bool
    hit_rank: Optional[int]  # 1-indexed rank where the hit was found, or None


@dataclass
class RetrievalModeResult:
    """Results for a single retrieval mode (embedding, bm25, hybrid, reranked)."""
    mode: str  # "embedding", "bm25", "hybrid", "reranked"
    query_results: List[QueryResult]
    hits_at_k: Dict[int, int] = field(default_factory=dict)
    mrr: float = 0.0  # Mean Reciprocal Rank


@dataclass
class ToolSiteRetrievalResult:
    tool: str
    site: str
    total_queries: int
    hits: int
    hit_rate: float
    total_chunks: int
    total_pages: int
    avg_chunk_words: float
    query_results: List[QueryResult]  # Primary mode results (embedding)
    embed_time: float
    search_time: float
    hits_at_k: Dict[int, int] = field(default_factory=dict)  # {k: hit_count}
    mrr: float = 0.0  # Mean Reciprocal Rank
    mode_results: Dict[str, RetrievalModeResult] = field(default_factory=dict)
    chunk_config_label: str = ""  # e.g. "~512tok"


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def _get_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package required. Install with: pip install openai")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    return OpenAI(api_key=api_key)


MAX_EMBED_TOKENS = 8100  # OpenAI limit is 8192; leave margin
EMBED_TIMEOUT = 30  # seconds per API call
EMBED_RETRIES = 3  # retry on timeout/network error (not retried for 400 errors)
EMBED_CACHE_DIR = BENCH_DIR / "embed_cache"

# Lazy-loaded tiktoken encoder
_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        import tiktoken
        _tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")
    return _tokenizer


def _truncate_to_tokens(text: str, max_tokens: int = MAX_EMBED_TOKENS) -> str:
    """Truncate text to stay under token limit using tiktoken for accuracy."""
    enc = _get_tokenizer()
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


def _embed_cache_key(texts: List[str], model: str) -> str:
    """Compute a stable hash for a batch of texts + model."""
    import hashlib
    h = hashlib.sha256()
    h.update(model.encode())
    for t in texts:
        h.update(t.encode())
    return h.hexdigest()


def _load_embed_cache(cache_key: str) -> Optional[List[List[float]]]:
    """Load cached embeddings if they exist."""
    cache_file = EMBED_CACHE_DIR / f"{cache_key}.json"
    if cache_file.is_file():
        with open(cache_file, "r") as f:
            return json.load(f)
    return None


def _save_embed_cache(cache_key: str, vectors: List[List[float]]) -> None:
    """Save embeddings to disk cache."""
    EMBED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = EMBED_CACHE_DIR / f"{cache_key}.json"
    with open(cache_file, "w") as f:
        json.dump(vectors, f)


def embed_texts(client, texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
    """Embed a batch of texts using OpenAI's API.

    Features:
    - Disk cache: embeddings are cached by content hash, so re-runs are instant
    - Retry with timeout: survives wifi drops (retries 3x with 30s timeout)
    - Batching: sends 100 texts per API call
    """
    # Check full-batch cache first
    cache_key = _embed_cache_key(texts, model)
    cached = _load_embed_cache(cache_key)
    if cached is not None:
        return cached

    batch_size = 100  # 100 texts per API call (well under 2048 input limit)
    max_concurrent = 3  # Parallel API calls (stays under rate limits)

    batches = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch = [_truncate_to_tokens(t) if t.strip() else " " for t in batch]
        batches.append((i, batch))

    def _embed_batch(args):
        idx, batch = args
        for attempt in range(EMBED_RETRIES):
            try:
                response = client.embeddings.create(
                    input=batch, model=model, timeout=EMBED_TIMEOUT,
                )
                return idx, [d.embedding for d in response.data]
            except Exception as exc:
                exc_str = str(exc)
                is_client_error = "400" in exc_str or "BadRequest" in type(exc).__name__
                if is_client_error:
                    raise
                if attempt < EMBED_RETRIES - 1:
                    wait = 2 ** attempt * 2
                    print(f"    Embed API error (attempt {attempt+1}/{EMBED_RETRIES}): {exc}")
                    print(f"    Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    from concurrent.futures import ThreadPoolExecutor
    results = {}
    with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
        for idx, vectors in pool.map(_embed_batch, batches):
            results[idx] = vectors

    # Reassemble in order
    all_vectors = []
    for idx, _ in batches:
        all_vectors.extend(results[idx])

    # Cache the result
    _save_embed_cache(cache_key, all_vectors)
    return all_vectors


# ---------------------------------------------------------------------------
# Cosine similarity (numpy-free fallback included)
# ---------------------------------------------------------------------------

def _cosine_similarity_np(a, b_matrix):
    """Compute cosine similarity between vector a and each row of b_matrix."""
    import numpy as np
    a = np.array(a)
    b = np.array(b_matrix)
    dot = b @ a
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b, axis=1)
    return dot / (norm_a * norm_b + 1e-10)


def _cosine_similarity_pure(a, b_matrix):
    """Pure-Python fallback for cosine similarity."""
    import math

    def _dot(x, y):
        return sum(xi * yi for xi, yi in zip(x, y))

    def _norm(x):
        return math.sqrt(sum(xi * xi for xi in x))

    norm_a = _norm(a)
    results = []
    for b in b_matrix:
        d = _dot(a, b)
        nb = _norm(b)
        results.append(d / (norm_a * nb + 1e-10))
    return results


try:
    import numpy  # noqa: F401
    cosine_similarity = _cosine_similarity_np
except ImportError:
    cosine_similarity = _cosine_similarity_pure


# ---------------------------------------------------------------------------
# BM25 search
# ---------------------------------------------------------------------------

def _build_bm25_index(chunk_texts: List[str]):
    """Build a BM25 index over tokenized chunk texts."""
    from rank_bm25 import BM25Okapi
    tokenized = [text.lower().split() for text in chunk_texts]
    return BM25Okapi(tokenized)


def _bm25_search(bm25_index, query: str, top_k: int) -> List[Tuple[int, float]]:
    """Return (index, score) pairs for top-k BM25 results."""
    tokenized_query = query.lower().split()
    scores = bm25_index.get_scores(tokenized_query)
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)
    return indexed[:top_k]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------

def _reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[int, float]]],
    k: int = RRF_K,
    top_n: int = TOP_K,
) -> List[Tuple[int, float]]:
    """Merge multiple ranked lists using RRF. Each list is [(index, score), ...]."""
    rrf_scores: Dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, (idx, _score) in enumerate(ranked, 1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)
    # Sort by RRF score descending
    merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return merged[:top_n]


# ---------------------------------------------------------------------------
# Cross-encoder reranking
# ---------------------------------------------------------------------------

_reranker = None


def _get_reranker():
    """Lazy-load the cross-encoder reranking model."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print(f"  Loading reranker: {RERANK_MODEL}...")
        _reranker = CrossEncoder(RERANK_MODEL)
        print("  Reranker loaded.")
    return _reranker


def _rerank(query: str, chunks: List[EmbeddedChunk], candidate_indices: List[int], top_n: int = RERANK_TOP_N) -> List[Tuple[int, float]]:
    """Rerank candidate chunks using cross-encoder. Returns [(chunk_index, score), ...]."""
    reranker = _get_reranker()
    pairs = [(query, chunks[i].text) for i in candidate_indices]
    scores = reranker.predict(pairs)
    scored = list(zip(candidate_indices, [float(s) for s in scores]))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Hit checking and MRR
# ---------------------------------------------------------------------------

def _check_hit(url_match: str, page_match: str, ranked_urls: List[str]) -> Tuple[bool, Optional[int]]:
    """Check if any URL in ranked list matches. Returns (hit, 1-indexed rank)."""
    for rank, url in enumerate(ranked_urls, 1):
        url_lower = url.lower()
        if url_match and url_match.lower() in url_lower:
            return True, rank
        if page_match and page_match.lower() in url_lower:
            return True, rank
    return False, None


def _compute_mrr(query_results: List[QueryResult]) -> float:
    """Compute Mean Reciprocal Rank from query results."""
    if not query_results:
        return 0.0
    rr_sum = 0.0
    for qr in query_results:
        if qr.hit_rank is not None:
            rr_sum += 1.0 / qr.hit_rank
    return rr_sum / len(query_results)


def _compute_hits_at_k(query_results: List[QueryResult]) -> Dict[int, int]:
    """Compute hit counts at each K threshold."""
    return {
        k: sum(1 for r in query_results if r.hit_rank is not None and r.hit_rank <= k)
        for k in REPORT_AT_K
    }


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_pages(jsonl_path: str) -> List[Dict]:
    """Load pages from a JSONL file."""
    pages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))
    return pages


def _url_to_breadcrumb(url: str) -> str:
    """Convert a URL path to a readable breadcrumb. e.g. '/docs/tutorial/body/' -> 'docs > tutorial > body'"""
    import urllib.parse as up
    path = up.urlsplit(url).path.strip("/")
    if not path:
        return ""
    segments = [seg for seg in path.split("/") if seg]
    # Clean up common URL patterns
    segments = [seg.replace("-", " ").replace("_", " ") for seg in segments]
    return " > ".join(segments)


def _extract_heading(chunk_text: str) -> str:
    """Extract the first markdown heading from a chunk, if any."""
    for line in chunk_text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            # Remove # prefix and any trailing anchors like [¶](#foo)
            heading = re.sub(r"^#{1,6}\s+", "", line)
            heading = re.sub(r"\[¶\].*$", "", heading).strip()
            return heading
    return ""


def _prepend_context(chunk_text: str, title: str, url: str, heading: str) -> str:
    """Prepend contextual metadata to a chunk for better embedding.

    Research shows this improves retrieval by 21-35% (NDCG) by helping
    the embedding model disambiguate chunks from different pages/sections.
    Metadata should be ~10% of chunk text.
    """
    parts = []
    if title:
        parts.append(f"Page: {title}")
    breadcrumb = _url_to_breadcrumb(url)
    if breadcrumb:
        parts.append(f"Path: {breadcrumb}")
    if heading and heading != title:
        parts.append(f"Section: {heading}")

    if not parts:
        return chunk_text

    context_line = " | ".join(parts)
    return f"{context_line}\n\n{chunk_text}"


def chunk_pages(
    pages: List[Dict],
    tool: str,
    site: str,
    max_words: int = CHUNK_MAX_WORDS,
    overlap_words: int = CHUNK_OVERLAP,
    add_context_headers: bool = False,
) -> List[EmbeddedChunk]:
    """Chunk all pages using markdown-aware chunking.

    If add_context_headers is True, prepend page title, URL breadcrumb, and
    section heading to each chunk before embedding.
    """
    chunks = []
    for page in pages:
        text = page.get("text", "")
        url = page.get("url", "")
        title = page.get("title", "")
        if not text.strip():
            continue
        page_chunks = chunk_markdown(text, max_words=max_words, overlap_words=overlap_words)
        for c in page_chunks:
            chunk_text = c.text
            if add_context_headers:
                heading = _extract_heading(chunk_text)
                chunk_text = _prepend_context(chunk_text, title, url, heading)
            chunks.append(EmbeddedChunk(
                text=chunk_text,
                url=url,
                tool=tool,
                site=site,
                chunk_index=c.index,
            ))
    return chunks


def _run_single_mode(
    mode: str,
    query_text: str,
    query_vec: List[float],
    chunks: List[EmbeddedChunk],
    vec_matrix,
    bm25_index,
    url_match: str,
    page_match: str,
) -> Tuple[List[str], List[float], bool, Optional[int]]:
    """Run a single retrieval mode and return (urls, scores, hit, hit_rank)."""
    if mode == "embedding":
        scores = cosine_similarity(query_vec, vec_matrix)
        if hasattr(scores, 'argsort'):
            import numpy as np
            top_indices = list(np.argsort(scores)[-TOP_K:][::-1])
        else:
            indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in indexed[:TOP_K]]
        top_urls = [chunks[i].url for i in top_indices]
        top_scores = [float(scores[i]) for i in top_indices]

    elif mode == "bm25":
        bm25_results = _bm25_search(bm25_index, query_text, TOP_K)
        top_indices = [i for i, _ in bm25_results]
        top_urls = [chunks[i].url for i in top_indices]
        top_scores = [s for _, s in bm25_results]

    elif mode == "hybrid":
        # Embedding results
        emb_scores = cosine_similarity(query_vec, vec_matrix)
        if hasattr(emb_scores, 'argsort'):
            import numpy as np
            emb_top = list(np.argsort(emb_scores)[-TOP_K:][::-1])
        else:
            emb_indexed = sorted(enumerate(emb_scores), key=lambda x: x[1], reverse=True)
            emb_top = [i for i, _ in emb_indexed[:TOP_K]]
        emb_ranked = [(i, float(emb_scores[i])) for i in emb_top]

        # BM25 results
        bm25_ranked = _bm25_search(bm25_index, query_text, TOP_K)

        # Fuse with RRF
        fused = _reciprocal_rank_fusion([emb_ranked, bm25_ranked], top_n=TOP_K)
        top_indices = [i for i, _ in fused]
        top_urls = [chunks[i].url for i in top_indices]
        top_scores = [s for _, s in fused]

    elif mode == "reranked":
        # Get hybrid candidates first
        emb_scores = cosine_similarity(query_vec, vec_matrix)
        if hasattr(emb_scores, 'argsort'):
            import numpy as np
            emb_top = list(np.argsort(emb_scores)[-TOP_K:][::-1])
        else:
            emb_indexed = sorted(enumerate(emb_scores), key=lambda x: x[1], reverse=True)
            emb_top = [i for i, _ in emb_indexed[:TOP_K]]
        emb_ranked = [(i, float(emb_scores[i])) for i in emb_top]

        bm25_ranked = _bm25_search(bm25_index, query_text, TOP_K)
        fused = _reciprocal_rank_fusion([emb_ranked, bm25_ranked], top_n=TOP_K)
        candidate_indices = [i for i, _ in fused]

        # Rerank candidates with cross-encoder
        reranked = _rerank(query_text, chunks, candidate_indices, top_n=RERANK_TOP_N)
        top_indices = [i for i, _ in reranked]
        top_urls = [chunks[i].url for i in top_indices]
        top_scores = [s for _, s in reranked]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    hit, hit_rank = _check_hit(url_match, page_match, top_urls)
    return top_urls, top_scores, hit, hit_rank


RETRIEVAL_MODES = ["embedding", "bm25", "hybrid", "reranked"]


def run_retrieval_test(
    client,
    chunks: List[EmbeddedChunk],
    queries: List[Dict],
    tool: str,
    site: str,
    chunk_config_label: str = "",
    query_vectors: Optional[List[List[float]]] = None,
) -> ToolSiteRetrievalResult:
    """Embed chunks, run queries across all retrieval modes, compute hit rates + MRR.

    If query_vectors is provided, skip embedding queries (reuse from prior tool).
    """
    # Embed all chunks
    chunk_texts = [c.text for c in chunks]
    print(f"    Embedding {len(chunk_texts)} chunks for {tool}/{site}...")
    embed_start = time.time()
    vectors = embed_texts(client, chunk_texts)
    embed_time = time.time() - embed_start
    print(f"    Embedded in {embed_time:.1f}s")

    for chunk, vec in zip(chunks, vectors):
        chunk.vector = vec

    vec_matrix = [c.vector for c in chunks]

    # Build BM25 index
    bm25_index = _build_bm25_index(chunk_texts)

    # Embed queries if not provided (batch all at once)
    if query_vectors is None:
        query_texts = [q["query"] for q in queries]
        print(f"    Embedding {len(query_texts)} queries...")
        query_vectors = embed_texts(client, query_texts)

    # Run queries across all modes
    search_start = time.time()
    mode_query_results: Dict[str, List[QueryResult]] = {m: [] for m in RETRIEVAL_MODES}

    for qi, q in enumerate(queries):
        query_vec = query_vectors[qi]
        url_match = q.get("url_match", "")
        page_match = q.get("page_match", "")

        for mode in RETRIEVAL_MODES:
            top_urls, top_scores, hit, hit_rank = _run_single_mode(
                mode, q["query"], query_vec, chunks, vec_matrix, bm25_index,
                url_match, page_match,
            )
            mode_query_results[mode].append(QueryResult(
                query=q["query"],
                description=q["description"],
                expected_url_match=url_match,
                expected_page_match=page_match,
                top_k_urls=top_urls,
                top_k_scores=top_scores,
                hit=hit,
                hit_rank=hit_rank,
            ))

    search_time = time.time() - search_start

    total_pages = len(set(c.url for c in chunks))
    avg_words = sum(len(c.text.split()) for c in chunks) / len(chunks) if chunks else 0

    # Build mode results
    mode_results: Dict[str, RetrievalModeResult] = {}
    for mode in RETRIEVAL_MODES:
        qrs = mode_query_results[mode]
        hits_at_k = _compute_hits_at_k(qrs)
        mrr = _compute_mrr(qrs)
        mode_results[mode] = RetrievalModeResult(
            mode=mode,
            query_results=qrs,
            hits_at_k=hits_at_k,
            mrr=mrr,
        )

    # Primary result uses embedding mode for backward compatibility
    emb = mode_results["embedding"]
    max_k = max(REPORT_AT_K)
    hits = emb.hits_at_k.get(max_k, 0)

    return ToolSiteRetrievalResult(
        tool=tool,
        site=site,
        total_queries=len(queries),
        hits=hits,
        hit_rate=hits / len(queries) if queries else 0,
        total_chunks=len(chunks),
        total_pages=total_pages,
        avg_chunk_words=avg_words,
        query_results=emb.query_results,
        embed_time=embed_time,
        search_time=search_time,
        hits_at_k=emb.hits_at_k,
        mrr=emb.mrr,
        mode_results=mode_results,
        chunk_config_label=chunk_config_label,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _compute_confidence_interval(hits: int, total: int) -> Tuple[float, float]:
    """Wilson score interval for binomial proportion (95% confidence)."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.96  # 95% CI
    p_hat = hits / total
    denom = 1 + z * z / total
    center = (p_hat + z * z / (2 * total)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * total)) / total) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def _fmt_rate(hits: int, total: int, show_ci: bool = True) -> str:
    """Format hit rate with optional CI."""
    rate = hits / total if total else 0
    base = f"{rate:.0%} ({hits}/{total})"
    if show_ci:
        lo, hi = _compute_confidence_interval(hits, total)
        base += f" ±{(hi-lo)/2:.0%}"
    return base


def generate_retrieval_report(
    results: Dict[str, Dict[str, ToolSiteRetrievalResult]],
    tool_names: List[str],
    chunk_sensitivity_results: Optional[Dict] = None,
) -> str:
    """Generate the RETRIEVAL_COMPARISON.md report."""
    total_queries_count = sum(
        len(TEST_QUERIES.get(site, []))
        for site in results.keys()
    )
    lines = [
        "# Retrieval Quality Comparison",
        "",
        "Does each tool's output produce embeddings that answer real questions?",
        "This benchmark chunks each tool's crawl output, embeds it with",
        f"`{EMBEDDING_MODEL}`, and measures retrieval across four modes:",
        "",
        "- **Embedding**: Cosine similarity on OpenAI embeddings",
        "- **BM25**: Keyword search (Okapi BM25)",
        "- **Hybrid**: Embedding + BM25 fused via Reciprocal Rank Fusion",
        f"- **Reranked**: Hybrid candidates reranked by `{RERANK_MODEL}`",
        "",
        f"**{total_queries_count} queries** across {len(results)} sites.",
        "Hit rate = correct source page in top-K results. Higher is better.",
        "",
    ]

    # ============================================================
    # Section 1: Multi-mode summary (embedding vs hybrid vs reranked)
    # ============================================================
    lines.extend(["## Summary: retrieval modes compared", ""])

    # Build header: Tool | Mode | Hit@K... | MRR
    k_headers = " | ".join(f"Hit@{k}" for k in REPORT_AT_K)
    lines.append(f"| Tool | Mode | {k_headers} | MRR |")
    lines.append("|---" + "|---" * len(REPORT_AT_K) + "|---|---|")

    for tool in tool_names:
        for mode in RETRIEVAL_MODES:
            total_queries = 0
            has_data = False
            agg_hits: Dict[int, int] = {k: 0 for k in REPORT_AT_K}
            rr_sum = 0.0

            for site_results in results.values():
                r = site_results.get(tool)
                if r and mode in r.mode_results:
                    has_data = True
                    mr = r.mode_results[mode]
                    total_queries += r.total_queries
                    for k in REPORT_AT_K:
                        agg_hits[k] += mr.hits_at_k.get(k, 0)
                    rr_sum += mr.mrr * r.total_queries

            if not has_data:
                continue

            mrr = rr_sum / total_queries if total_queries else 0
            k_cols = []
            for k in REPORT_AT_K:
                k_cols.append(_fmt_rate(agg_hits[k], total_queries))
            lines.append(
                f"| {tool} | {mode} | " + " | ".join(k_cols) +
                f" | {mrr:.3f} |"
            )

    lines.extend(["", ""])

    # ============================================================
    # Section 2: Embedding-only summary (backward compatible)
    # ============================================================
    lines.extend(["## Summary: embedding-only (hit rate at multiple K values)", ""])

    k_headers = " | ".join(f"Hit@{k}" for k in REPORT_AT_K)
    lines.append(f"| Tool | {k_headers} | MRR | Chunks | Avg words |")
    lines.append("|---" + "|---" * len(REPORT_AT_K) + "|---|---|---|")

    for tool in tool_names:
        total_queries = 0
        total_chunks = 0
        total_chunk_words = 0
        has_data = False
        agg_hits: Dict[int, int] = {k: 0 for k in REPORT_AT_K}
        rr_sum = 0.0

        for site_results in results.values():
            r = site_results.get(tool)
            if r:
                has_data = True
                total_queries += r.total_queries
                total_chunks += r.total_chunks
                total_chunk_words += r.avg_chunk_words * r.total_chunks
                for k in REPORT_AT_K:
                    agg_hits[k] += r.hits_at_k.get(k, 0)
                rr_sum += r.mrr * r.total_queries

        if not has_data:
            cols = " | ".join("—" for _ in REPORT_AT_K)
            lines.append(f"| {tool} | {cols} | — | — | — |")
            continue

        avg_words = total_chunk_words / total_chunks if total_chunks else 0
        mrr = rr_sum / total_queries if total_queries else 0
        k_cols = [_fmt_rate(agg_hits[k], total_queries) for k in REPORT_AT_K]
        lines.append(
            f"| {tool} | " + " | ".join(k_cols) +
            f" | {mrr:.3f} | {total_chunks} | {avg_words:.0f} |"
        )

    lines.extend(["", ""])

    # ============================================================
    # Section 3: Chunk size sensitivity (if available)
    # ============================================================
    if chunk_sensitivity_results:
        lines.extend(["## Chunk size sensitivity analysis", ""])
        lines.append(
            "Does clean crawler output produce better retrieval *regardless* of chunk size? "
            "Each tool tested at three chunk configurations."
        )
        lines.append("")

        # Table: Tool | Config | Hit@5 | Hit@10 | Hit@20 | MRR
        lines.append("| Tool | Chunk size | Hit@5 | Hit@10 | Hit@20 | MRR |")
        lines.append("|---|---|---|---|---|---|")

        for tool in tool_names:
            for config_label, config_results in chunk_sensitivity_results.items():
                total_q = 0
                agg_5 = 0
                agg_10 = 0
                agg_20 = 0
                rr_sum = 0.0
                has = False
                for site_results in config_results.values():
                    r = site_results.get(tool)
                    if r:
                        has = True
                        emb = r.mode_results.get("embedding")
                        if emb:
                            total_q += r.total_queries
                            agg_5 += emb.hits_at_k.get(5, 0)
                            agg_10 += emb.hits_at_k.get(10, 0)
                            agg_20 += emb.hits_at_k.get(20, 0)
                            rr_sum += emb.mrr * r.total_queries
                if not has or total_q == 0:
                    continue
                mrr = rr_sum / total_q
                lines.append(
                    f"| {tool} | {config_label} "
                    f"| {_fmt_rate(agg_5, total_q, False)} "
                    f"| {_fmt_rate(agg_10, total_q, False)} "
                    f"| {_fmt_rate(agg_20, total_q, False)} "
                    f"| {mrr:.3f} |"
                )

        lines.extend(["", ""])

    # ============================================================
    # Section 4: Per-site breakdown
    # ============================================================
    for site, site_results in results.items():
        queries = TEST_QUERIES.get(site, [])
        if not queries:
            continue

        lines.extend([f"## {site}", ""])

        # Hit rate table with multi-K (embedding mode)
        k_headers = " | ".join(f"Hit@{k}" for k in REPORT_AT_K)
        lines.extend([
            f"| Tool | {k_headers} | MRR | Chunks | Pages |",
            "|---" + "|---" * len(REPORT_AT_K) + "|---|---|---|",
        ])

        for tool in tool_names:
            r = site_results.get(tool)
            if not r:
                cols = " | ".join("—" for _ in REPORT_AT_K)
                lines.append(f"| {tool} | {cols} | — | — | — |")
                continue
            k_cols = []
            for k in REPORT_AT_K:
                h = r.hits_at_k.get(k, 0)
                rate = h / r.total_queries if r.total_queries else 0
                k_cols.append(f"{rate:.0%} ({h}/{r.total_queries})")
            lines.append(
                f"| {tool} | " + " | ".join(k_cols) +
                f" | {r.mrr:.3f} | {r.total_chunks} | {r.total_pages} |"
            )

        lines.append("")

        # Per-query detail (show top-3 only for readability)
        detail_k = 3
        lines.append("<details>")
        lines.append(f"<summary>Query-by-query results for {site}</summary>")
        lines.append("")

        for qi, q in enumerate(queries):
            lines.extend([
                f"**Q{qi+1}: {q['query']}**",
                f"*(expects URL containing: `{q.get('url_match', '')}`)*",
                "",
                f"| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |",
                "|---|---|---|---|---|---|---|---|",
            ])

            for tool in tool_names:
                r = site_results.get(tool)
                if not r:
                    lines.append(f"| {tool} | — | — | — | — | — | — | — |")
                    continue

                qr = r.query_results[qi]
                hit_marker = f"#{qr.hit_rank}" if qr.hit_rank is not None else "miss"
                row = f"| {tool} | {hit_marker} "
                for i in range(detail_k):
                    if i < len(qr.top_k_urls):
                        short_url = qr.top_k_urls[i].split("//")[-1][:50]
                        score = qr.top_k_scores[i]
                        row += f"| {short_url} | {score:.3f} "
                    else:
                        row += "| — | — "
                row += "|"
                lines.append(row)

            lines.extend(["", ""])

        lines.extend(["</details>", ""])

    # ============================================================
    # Methodology
    # ============================================================
    k_list = ", ".join(str(k) for k in REPORT_AT_K)
    config_list = ", ".join(f"{lbl}" for _, _, lbl in CHUNK_CONFIGS)
    lines.extend([
        "## Methodology",
        "",
        f"- **Queries:** {total_queries_count} across {len(results)} sites (verified against crawled pages)",
        f"- **Embedding model:** `{EMBEDDING_MODEL}` ({EMBEDDING_DIMENSIONS} dimensions)",
        f"- **Chunking:** Markdown-aware, {CHUNK_MAX_WORDS} word max, {CHUNK_OVERLAP} word overlap",
        f"- **Retrieval modes:** Embedding (cosine), BM25 (Okapi), Hybrid (RRF k={RRF_K}), Reranked (`{RERANK_MODEL}`)",
        f"- **Retrieval:** Hit rate reported at K = {k_list}, plus MRR",
        f"- **Reranking:** Top-{TOP_K} candidates from hybrid search, reranked to top-{RERANK_TOP_N}",
        f"- **Chunk sensitivity:** Tested at {config_list}",
        f"- **Confidence intervals:** Wilson score interval (95%)",
        "- **Same chunking and embedding** for all tools — only extraction quality varies",
        "- **No fine-tuning or tool-specific optimization** — identical pipeline for all",
        "",
    ])

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Find latest run
# ---------------------------------------------------------------------------

def find_latest_run(runs_dir: Path) -> Optional[Path]:
    """Find the most recent benchmark run directory."""
    if not runs_dir.is_dir():
        return None
    runs = sorted(runs_dir.glob("run_*"), reverse=True)
    return runs[0] if runs else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKPOINT_DIR = BENCH_DIR / "retrieval_checkpoints"


def _checkpoint_key(run_name: str, tool: str, site: str, config_label: str) -> str:
    """Stable key for a checkpoint file."""
    safe = f"{run_name}__{tool}__{site}__{config_label}".replace("/", "_")
    return safe


def _save_checkpoint(run_name: str, tool: str, site: str, config_label: str, result: ToolSiteRetrievalResult) -> None:
    """Save a completed tool/site result to disk."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    key = _checkpoint_key(run_name, tool, site, config_label)
    data = {
        "tool": result.tool,
        "site": result.site,
        "total_queries": result.total_queries,
        "hits": result.hits,
        "hit_rate": result.hit_rate,
        "total_chunks": result.total_chunks,
        "total_pages": result.total_pages,
        "avg_chunk_words": result.avg_chunk_words,
        "embed_time": result.embed_time,
        "search_time": result.search_time,
        "hits_at_k": result.hits_at_k,
        "mrr": result.mrr,
        "chunk_config_label": result.chunk_config_label,
        "mode_results": {},
        "query_results": [],  # primary (embedding) mode
    }
    # Save each mode's results
    for mode, mr in result.mode_results.items():
        mode_data = {
            "mode": mr.mode,
            "hits_at_k": mr.hits_at_k,
            "mrr": mr.mrr,
            "query_results": [],
        }
        for qr in mr.query_results:
            mode_data["query_results"].append({
                "query": qr.query,
                "description": qr.description,
                "expected_url_match": qr.expected_url_match,
                "expected_page_match": qr.expected_page_match,
                "top_k_urls": qr.top_k_urls[:20],  # save top-20 only to limit size
                "top_k_scores": qr.top_k_scores[:20],
                "hit": qr.hit,
                "hit_rank": qr.hit_rank,
            })
        data["mode_results"][mode] = mode_data

    # Primary query results
    for qr in result.query_results:
        data["query_results"].append({
            "query": qr.query,
            "description": qr.description,
            "expected_url_match": qr.expected_url_match,
            "expected_page_match": qr.expected_page_match,
            "top_k_urls": qr.top_k_urls[:20],
            "top_k_scores": qr.top_k_scores[:20],
            "hit": qr.hit,
            "hit_rank": qr.hit_rank,
        })

    path = CHECKPOINT_DIR / f"{key}.json"
    with open(path, "w") as f:
        json.dump(data, f)


def _load_checkpoint(run_name: str, tool: str, site: str, config_label: str) -> Optional[ToolSiteRetrievalResult]:
    """Load a checkpoint if it exists."""
    key = _checkpoint_key(run_name, tool, site, config_label)
    path = CHECKPOINT_DIR / f"{key}.json"
    if not path.is_file():
        return None

    with open(path, "r") as f:
        data = json.load(f)

    def _load_qrs(qr_list):
        return [
            QueryResult(
                query=q["query"],
                description=q["description"],
                expected_url_match=q["expected_url_match"],
                expected_page_match=q["expected_page_match"],
                top_k_urls=q["top_k_urls"],
                top_k_scores=q["top_k_scores"],
                hit=q["hit"],
                hit_rank=q["hit_rank"],
            )
            for q in qr_list
        ]

    mode_results = {}
    for mode, md in data.get("mode_results", {}).items():
        mode_results[mode] = RetrievalModeResult(
            mode=md["mode"],
            query_results=_load_qrs(md["query_results"]),
            hits_at_k={int(k): v for k, v in md["hits_at_k"].items()},
            mrr=md["mrr"],
        )

    return ToolSiteRetrievalResult(
        tool=data["tool"],
        site=data["site"],
        total_queries=data["total_queries"],
        hits=data["hits"],
        hit_rate=data["hit_rate"],
        total_chunks=data["total_chunks"],
        total_pages=data["total_pages"],
        avg_chunk_words=data["avg_chunk_words"],
        query_results=_load_qrs(data["query_results"]),
        embed_time=data["embed_time"],
        search_time=data["search_time"],
        hits_at_k={int(k): v for k, v in data["hits_at_k"].items()},
        mrr=data["mrr"],
        mode_results=mode_results,
        chunk_config_label=data.get("chunk_config_label", ""),
    )


def _run_benchmark_for_config(
    client,
    run_dir: Path,
    sites: List[str],
    available_tools: List[str],
    max_words: int,
    overlap_words: int,
    config_label: str,
    verbose: bool = True,
    add_context_headers: bool = False,
) -> Dict[str, Dict[str, ToolSiteRetrievalResult]]:
    """Run the full retrieval benchmark for a single chunk configuration.

    Supports resuming: completed tool/site results are checkpointed to disk
    and reloaded on restart, so wifi drops only lose the in-progress item.
    """
    run_name = run_dir.name
    all_results: Dict[str, Dict[str, ToolSiteRetrievalResult]] = {}

    for site in sites:
        queries = TEST_QUERIES.get(site)
        if not queries:
            if verbose:
                print(f"\n  Skipping {site}: no test queries defined")
            continue

        if verbose:
            print(f"\n{'='*60}")
            print(f"Site: {site} ({len(queries)} queries) [{config_label}]")
            print(f"{'='*60}")

        site_results: Dict[str, ToolSiteRetrievalResult] = {}

        # Pre-embed queries once per site (reused across all tools)
        query_vectors: Optional[List[List[float]]] = None
        needs_embedding = any(
            _load_checkpoint(run_name, t, site, config_label) is None
            and (run_dir / t / site / "pages.jsonl").is_file()
            for t in available_tools
        )
        if needs_embedding:
            query_texts = [q["query"] for q in queries]
            if verbose:
                print(f"\n  Embedding {len(query_texts)} queries for {site} (shared across tools)...")
            query_vectors = embed_texts(client, query_texts)

        for tool in available_tools:
            # Check for checkpoint first
            cached_result = _load_checkpoint(run_name, tool, site, config_label)
            if cached_result is not None:
                site_results[tool] = cached_result
                if verbose:
                    emb = cached_result.mode_results.get("embedding")
                    h10 = emb.hits_at_k.get(10, 0) if emb else 0
                    print(f"\n  {tool}: RESUMED from checkpoint — Hit@10: {h10}/{cached_result.total_queries}")
                continue

            jsonl_path = run_dir / tool / site / "pages.jsonl"
            if not jsonl_path.is_file() or jsonl_path.stat().st_size == 0:
                if verbose:
                    print(f"  {tool}: no data, skipping")
                continue

            if verbose:
                print(f"\n  {tool}:")
            pages = load_pages(str(jsonl_path))
            if verbose:
                print(f"    {len(pages)} pages loaded")

            chunks = chunk_pages(pages, tool, site, max_words=max_words, overlap_words=overlap_words, add_context_headers=add_context_headers)
            if verbose:
                print(f"    {len(chunks)} chunks created")

            if not chunks:
                if verbose:
                    print(f"    WARNING: no chunks created, skipping")
                continue

            result = run_retrieval_test(client, chunks, queries, tool, site, config_label, query_vectors)
            site_results[tool] = result

            # Checkpoint immediately after each tool/site completes
            _save_checkpoint(run_name, tool, site, config_label, result)

            if verbose:
                emb = result.mode_results.get("embedding")
                reranked = result.mode_results.get("reranked")
                if emb:
                    h10 = emb.hits_at_k.get(10, 0)
                    print(f"    Embedding  Hit@10: {h10}/{result.total_queries} ({h10/result.total_queries:.0%})  MRR: {emb.mrr:.3f}")
                if reranked:
                    h10 = reranked.hits_at_k.get(10, 0)
                    print(f"    Reranked   Hit@10: {h10}/{result.total_queries} ({h10/result.total_queries:.0%})  MRR: {reranked.mrr:.3f}")

        all_results[site] = site_results

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Retrieval quality benchmark — embed and compare")
    parser.add_argument("--run", default=None, help="Specific run directory name (e.g. run_20260405_221158)")
    parser.add_argument("--output", default=str(BENCH_DIR / "RETRIEVAL_COMPARISON.md"),
                        help="Output path for the retrieval report")
    parser.add_argument("--sites", default=None, help="Comma-separated sites to test")
    parser.add_argument("--tools", default=None, help="Comma-separated tools to test")
    parser.add_argument("--chunk-sensitivity", action="store_true",
                        help="Run chunk size sensitivity analysis at multiple configurations")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Skip cross-encoder reranking (faster but less complete)")
    parser.add_argument("--context-headers", action="store_true",
                        help="Prepend page title, section heading, and URL path to each chunk")
    parser.add_argument("--fresh", action="store_true",
                        help="Clear checkpoints and embedding cache — start from scratch")
    args = parser.parse_args()

    # If --no-rerank, remove reranked from modes
    global RETRIEVAL_MODES
    if args.no_rerank:
        RETRIEVAL_MODES = [m for m in RETRIEVAL_MODES if m != "reranked"]

    # Clear caches if --fresh
    if args.fresh:
        import shutil
        if CHECKPOINT_DIR.is_dir():
            shutil.rmtree(CHECKPOINT_DIR)
            print("Cleared retrieval checkpoints.")
        if EMBED_CACHE_DIR.is_dir():
            shutil.rmtree(EMBED_CACHE_DIR)
            print("Cleared embedding cache.")

    runs_dir = BENCH_DIR / "runs"

    if args.run:
        run_dir = runs_dir / args.run
    else:
        run_dir = find_latest_run(runs_dir)

    if not run_dir or not run_dir.is_dir():
        print(f"ERROR: No benchmark run found at {run_dir}")
        sys.exit(1)

    print(f"Using benchmark run: {run_dir.name}")

    # Determine sites and tools to test
    sites = args.sites.split(",") if args.sites else list(TEST_QUERIES.keys())
    tools = args.tools.split(",") if args.tools else TOOLS

    # Only test sites that have queries defined
    sites = [s for s in sites if s in TEST_QUERIES]

    # Check which tools have data
    available_tools = []
    for tool in tools:
        has_any_data = False
        for site in sites:
            jsonl = run_dir / tool / site / "pages.jsonl"
            if jsonl.is_file() and jsonl.stat().st_size > 0:
                has_any_data = True
                break
        if has_any_data:
            available_tools.append(tool)
        else:
            print(f"  Skipping {tool}: no data in this run")

    if not available_tools:
        print("ERROR: No tools have data for the selected sites")
        sys.exit(1)

    print(f"Tools with data: {', '.join(available_tools)}")
    print(f"Sites: {', '.join(sites)}")
    print(f"Retrieval modes: {', '.join(RETRIEVAL_MODES)}")

    # Initialize OpenAI client
    client = _get_openai_client()

    # Verify API works with a tiny test
    print("Verifying OpenAI API key...")
    try:
        embed_texts(client, ["test"])
        print("  OK")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        sys.exit(1)

    # Run primary benchmark (default chunk config)
    max_words, overlap_words, config_label = DEFAULT_CHUNK_CONFIG
    all_results = _run_benchmark_for_config(
        client, run_dir, sites, available_tools,
        max_words, overlap_words, config_label,
        add_context_headers=args.context_headers,
    )

    # Run chunk sensitivity analysis if requested
    chunk_sensitivity_results: Optional[Dict[str, Dict[str, Dict[str, ToolSiteRetrievalResult]]]] = None
    if args.chunk_sensitivity:
        chunk_sensitivity_results = {}
        for mw, ow, label in CHUNK_CONFIGS:
            if (mw, ow, label) == DEFAULT_CHUNK_CONFIG:
                # Reuse primary results
                chunk_sensitivity_results[label] = all_results
            else:
                print(f"\n\n{'#'*60}")
                print(f"# Chunk sensitivity: {label} (max_words={mw}, overlap={ow})")
                print(f"{'#'*60}")
                chunk_sensitivity_results[label] = _run_benchmark_for_config(
                    client, run_dir, sites, available_tools,
                    mw, ow, label, verbose=True,
                    add_context_headers=args.context_headers,
                )

    # Generate report
    report = generate_retrieval_report(all_results, available_tools, chunk_sensitivity_results)
    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nRetrieval report written to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY (all retrieval modes)")
    print("=" * 60)
    for mode in RETRIEVAL_MODES:
        print(f"\n  --- {mode.upper()} ---")
        k_header = " | ".join(f"Hit@{k:>2}" for k in REPORT_AT_K)
        print(f"  {'Tool':>15}  {k_header}  |  MRR")
        for tool in available_tools:
            total_queries = 0
            agg_hits: Dict[int, int] = {k: 0 for k in REPORT_AT_K}
            rr_sum = 0.0

            for site_results in all_results.values():
                r = site_results.get(tool)
                if r and mode in r.mode_results:
                    mr = r.mode_results[mode]
                    total_queries += r.total_queries
                    for k in REPORT_AT_K:
                        agg_hits[k] += mr.hits_at_k.get(k, 0)
                    rr_sum += mr.mrr * r.total_queries

            if not total_queries:
                continue
            mrr = rr_sum / total_queries
            k_vals = []
            for k in REPORT_AT_K:
                h = agg_hits[k]
                k_vals.append(f"{h}/{total_queries} ({h/total_queries:.0%})")
            print(f"  {tool:>15}  {'  '.join(k_vals)}  |  {mrr:.3f}")


if __name__ == "__main__":
    main()
