#!/usr/bin/env python3
"""Retrieval quality benchmark — embed each tool's output, run queries, compare hit rates.

Measures what actually matters for RAG: does the right page surface when you
ask a question?  Uses the same chunking strategy and embedding model for all
tools so the only variable is extraction quality.

    python benchmarks/benchmark_retrieval.py                        # latest run
    python benchmarks/benchmark_retrieval.py --run run_20260405_221158
    python benchmarks/benchmark_retrieval.py --output my_report.md

Requires:
    pip install openai numpy
    export OPENAI_API_KEY=sk-...
"""
from __future__ import annotations

import argparse
import json
import os
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
TOP_K = 3
CHUNK_MAX_WORDS = 400
CHUNK_OVERLAP = 50

# Test queries per site.  Each query has:
#   - query text (what a user would ask)
#   - expected URL substring (identifies the correct source page)
#   - description (what the query tests)
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
            "query": "How do I define query parameters in FastAPI?",
            "url_match": "query-parameter",
            "page_match": "query",
            "description": "Find tutorial content",
        },
        {
            "query": "How do I handle file uploads in FastAPI?",
            "url_match": "request-files",
            "page_match": "file",
            "description": "Find procedural content",
        },
        {
            "query": "What Python types does FastAPI support for request bodies?",
            "url_match": "body",
            "page_match": "body",
            "description": "Find reference content",
        },
    ],
    "python-docs": [
        {
            "query": "How do I read and write files in Python?",
            "url_match": "functions",
            "page_match": "open",
            "description": "Find built-in function docs",
        },
        {
            "query": "How does Python's garbage collector work?",
            "url_match": "gc",
            "page_match": "gc",
            "description": "Find module documentation",
        },
        {
            "query": "What data structures does the collections module provide?",
            "url_match": "collections",
            "page_match": "collections",
            "description": "Find standard library module",
        },
        {
            "query": "How do I use regular expressions in Python?",
            "url_match": "re",
            "page_match": "re",
            "description": "Find regex documentation",
        },
        {
            "query": "How do I parse JSON in Python?",
            "url_match": "json",
            "page_match": "json",
            "description": "Find data format module",
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
class ToolSiteRetrievalResult:
    tool: str
    site: str
    total_queries: int
    hits: int
    hit_rate: float
    total_chunks: int
    total_pages: int
    avg_chunk_words: float
    query_results: List[QueryResult]
    embed_time: float
    search_time: float


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


def embed_texts(client, texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
    """Embed a batch of texts using OpenAI's API. Handles batching for large inputs."""
    all_vectors = []
    batch_size = 100  # OpenAI limit is 2048, but 100 keeps requests reasonable

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Replace empty strings with a space (API rejects empty)
        batch = [t if t.strip() else " " for t in batch]
        response = client.embeddings.create(input=batch, model=model)
        all_vectors.extend([d.embedding for d in response.data])

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


def chunk_pages(pages: List[Dict], tool: str, site: str) -> List[EmbeddedChunk]:
    """Chunk all pages using markdown-aware chunking."""
    chunks = []
    for page in pages:
        text = page.get("text", "")
        url = page.get("url", "")
        if not text.strip():
            continue
        page_chunks = chunk_markdown(text, max_words=CHUNK_MAX_WORDS, overlap_words=CHUNK_OVERLAP)
        for c in page_chunks:
            chunks.append(EmbeddedChunk(
                text=c.text,
                url=url,
                tool=tool,
                site=site,
                chunk_index=c.index,
            ))
    return chunks


def run_retrieval_test(
    client,
    chunks: List[EmbeddedChunk],
    queries: List[Dict],
    tool: str,
    site: str,
) -> ToolSiteRetrievalResult:
    """Embed chunks, run queries, compute hit rates."""
    # Embed all chunks
    chunk_texts = [c.text for c in chunks]
    print(f"    Embedding {len(chunk_texts)} chunks for {tool}/{site}...")
    embed_start = time.time()
    vectors = embed_texts(client, chunk_texts)
    embed_time = time.time() - embed_start
    print(f"    Embedded in {embed_time:.1f}s")

    for chunk, vec in zip(chunks, vectors):
        chunk.vector = vec

    # Build vector matrix for fast similarity
    vec_matrix = [c.vector for c in chunks]

    # Run queries
    search_start = time.time()
    query_results = []
    for q in queries:
        query_vec = embed_texts(client, [q["query"]])[0]
        scores = cosine_similarity(query_vec, vec_matrix)

        # Get top-K indices
        if hasattr(scores, 'argsort'):
            # numpy
            import numpy as np
            top_indices = np.argsort(scores)[-TOP_K:][::-1]
        else:
            # pure python
            indexed = list(enumerate(scores))
            indexed.sort(key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in indexed[:TOP_K]]

        top_k_urls = [chunks[i].url for i in top_indices]
        top_k_scores = [float(scores[i]) for i in top_indices]

        # Check for hit: does any top-K chunk's URL match expected?
        url_match = q.get("url_match", "")
        page_match = q.get("page_match", "")
        hit = False
        hit_rank = None
        for rank, url in enumerate(top_k_urls, 1):
            url_lower = url.lower()
            if url_match and url_match.lower() in url_lower:
                hit = True
                hit_rank = rank
                break
            if page_match and page_match.lower() in url_lower:
                hit = True
                hit_rank = rank
                break

        query_results.append(QueryResult(
            query=q["query"],
            description=q["description"],
            expected_url_match=url_match,
            expected_page_match=page_match,
            top_k_urls=top_k_urls,
            top_k_scores=top_k_scores,
            hit=hit,
            hit_rank=hit_rank,
        ))

    search_time = time.time() - search_start

    total_pages = len(set(c.url for c in chunks))
    avg_words = sum(len(c.text.split()) for c in chunks) / len(chunks) if chunks else 0
    hits = sum(1 for r in query_results if r.hit)

    return ToolSiteRetrievalResult(
        tool=tool,
        site=site,
        total_queries=len(queries),
        hits=hits,
        hit_rate=hits / len(queries) if queries else 0,
        total_chunks=len(chunks),
        total_pages=total_pages,
        avg_chunk_words=avg_words,
        query_results=query_results,
        embed_time=embed_time,
        search_time=search_time,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_retrieval_report(
    results: Dict[str, Dict[str, ToolSiteRetrievalResult]],
    tool_names: List[str],
) -> str:
    """Generate the RETRIEVAL_COMPARISON.md report."""
    lines = [
        "# Retrieval Quality Comparison",
        "",
        "Does each tool's output produce embeddings that answer real questions?",
        "This benchmark chunks each tool's crawl output, embeds it with",
        f"`{EMBEDDING_MODEL}`, and runs the same retrieval queries against each.",
        "",
        "**What matters:** Hit rate — does the correct source page appear in the",
        f"top {TOP_K} results? Higher is better.",
        "",
        "## Summary",
        "",
        f"| Tool | Queries | Hits | Hit rate | Chunks | Avg chunk words |",
        "|---|---|---|---|---|---|",
    ]

    # Aggregate across all sites per tool
    for tool in tool_names:
        total_queries = 0
        total_hits = 0
        total_chunks = 0
        total_chunk_words = 0
        has_data = False

        for site_results in results.values():
            r = site_results.get(tool)
            if r:
                has_data = True
                total_queries += r.total_queries
                total_hits += r.hits
                total_chunks += r.total_chunks
                total_chunk_words += r.avg_chunk_words * r.total_chunks

        if not has_data:
            lines.append(f"| {tool} | — | — | — | — | — |")
            continue

        hit_rate = total_hits / total_queries if total_queries else 0
        avg_words = total_chunk_words / total_chunks if total_chunks else 0
        lines.append(
            f"| {tool} | {total_queries} | {total_hits} | "
            f"{hit_rate:.0%} | {total_chunks} | {avg_words:.0f} |"
        )

    lines.extend(["", ""])

    # Per-site breakdown
    for site, site_results in results.items():
        queries = TEST_QUERIES.get(site, [])
        if not queries:
            continue

        lines.extend([f"## {site}", ""])

        # Hit rate table
        lines.extend([
            f"| Tool | Hit rate | Hits/{len(queries)} | Chunks | Pages | Embed time |",
            "|---|---|---|---|---|---|",
        ])

        for tool in tool_names:
            r = site_results.get(tool)
            if not r:
                lines.append(f"| {tool} | — | — | — | — | — |")
                continue
            lines.append(
                f"| {tool} | {r.hit_rate:.0%} | {r.hits}/{r.total_queries} | "
                f"{r.total_chunks} | {r.total_pages} | {r.embed_time:.1f}s |"
            )

        lines.append("")

        # Per-query detail
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
                hit_marker = f"#{qr.hit_rank}" if qr.hit else "miss"
                row = f"| {tool} | {hit_marker} "
                for i in range(TOP_K):
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

    # Methodology note
    lines.extend([
        "## Methodology",
        "",
        f"- **Embedding model:** `{EMBEDDING_MODEL}` ({EMBEDDING_DIMENSIONS} dimensions)",
        f"- **Chunking:** Markdown-aware, {CHUNK_MAX_WORDS} word max, {CHUNK_OVERLAP} word overlap",
        f"- **Retrieval:** Cosine similarity, top-{TOP_K} results checked for expected URL",
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

def main():
    parser = argparse.ArgumentParser(description="Retrieval quality benchmark — embed and compare")
    parser.add_argument("--run", default=None, help="Specific run directory name (e.g. run_20260405_221158)")
    parser.add_argument("--output", default=str(BENCH_DIR / "RETRIEVAL_COMPARISON.md"),
                        help="Output path for the retrieval report")
    parser.add_argument("--sites", default=None, help="Comma-separated sites to test")
    parser.add_argument("--tools", default=None, help="Comma-separated tools to test")
    args = parser.parse_args()

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

    # Run retrieval tests
    all_results: Dict[str, Dict[str, ToolSiteRetrievalResult]] = {}

    for site in sites:
        queries = TEST_QUERIES.get(site)
        if not queries:
            print(f"\n  Skipping {site}: no test queries defined")
            continue

        print(f"\n{'='*60}")
        print(f"Site: {site} ({len(queries)} queries)")
        print(f"{'='*60}")

        site_results: Dict[str, ToolSiteRetrievalResult] = {}

        for tool in available_tools:
            jsonl_path = run_dir / tool / site / "pages.jsonl"
            if not jsonl_path.is_file() or jsonl_path.stat().st_size == 0:
                print(f"  {tool}: no data, skipping")
                continue

            print(f"\n  {tool}:")
            pages = load_pages(str(jsonl_path))
            print(f"    {len(pages)} pages loaded")

            chunks = chunk_pages(pages, tool, site)
            print(f"    {len(chunks)} chunks created")

            if not chunks:
                print(f"    WARNING: no chunks created, skipping")
                continue

            result = run_retrieval_test(client, chunks, queries, tool, site)
            site_results[tool] = result

            print(f"    Hit rate: {result.hits}/{result.total_queries} ({result.hit_rate:.0%})")
            for qr in result.query_results:
                status = f"HIT (rank #{qr.hit_rank})" if qr.hit else "MISS"
                print(f"      {status}: {qr.query[:60]}...")

        all_results[site] = site_results

    # Generate report
    report = generate_retrieval_report(all_results, available_tools)
    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nRetrieval report written to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for tool in available_tools:
        total_hits = sum(
            r.hits for site_results in all_results.values()
            for t, r in site_results.items() if t == tool
        )
        total_queries = sum(
            r.total_queries for site_results in all_results.values()
            for t, r in site_results.items() if t == tool
        )
        if total_queries:
            print(f"  {tool}: {total_hits}/{total_queries} ({total_hits/total_queries:.0%})")


if __name__ == "__main__":
    main()
