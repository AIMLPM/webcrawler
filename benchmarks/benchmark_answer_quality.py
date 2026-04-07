#!/usr/bin/env python3
"""End-to-end RAG answer quality benchmark.

Measures what actually matters: given the same question, does cleaner crawler
output produce better LLM answers?

For each query × tool:
  1. Retrieve top-10 chunks (embedding similarity)
  2. Send chunks + query to an LLM → generate an answer
  3. Score the answer with an LLM judge on correctness and usefulness

    python benchmarks/benchmark_answer_quality.py
    python benchmarks/benchmark_answer_quality.py --run run_20260406_184709
    python benchmarks/benchmark_answer_quality.py --tools markcrawl,crawl4ai,crawlee

Requires:
    pip install openai numpy
    export OPENAI_API_KEY=sk-...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

BENCH_DIR = Path(__file__).parent
REPO_ROOT = BENCH_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

# Import shared config from retrieval benchmark
from benchmarks.benchmark_retrieval import (  # noqa: E402
    CHUNK_MAX_WORDS,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    TEST_QUERIES,
    TOOLS,
    _get_openai_client,
    cosine_similarity,
    embed_texts,
    find_latest_run,
    load_pages,
)
from markcrawl.chunker import chunk_markdown  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ANSWER_MODEL = "gpt-4o-mini"  # Model for generating answers
JUDGE_MODEL = "gpt-4o-mini"   # Model for judging answers
TOP_K_FOR_ANSWER = 10         # Chunks sent to the answer model
CHECKPOINT_DIR = BENCH_DIR / "answer_quality_checkpoints"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

ANSWER_PROMPT = """Answer the following question using ONLY the provided context.
If the context does not contain enough information to answer, say "I cannot answer this based on the provided context."
Be concise and specific.

## Context

{context}

## Question

{question}

## Answer"""

JUDGE_PROMPT = """You are evaluating the quality of a RAG (Retrieval-Augmented Generation) system's answer.

Given a question and the answer produced by the system, rate the answer on these criteria:

1. **Correctness** (1-5): Is the answer factually accurate based on what a knowledgeable person would expect?
2. **Relevance** (1-5): Does the answer directly address the question asked?
3. **Completeness** (1-5): Does the answer cover the key aspects of the question?
4. **Usefulness** (1-5): Would a user find this answer helpful?

If the system said it cannot answer, score based on whether that was the right call:
- If the question is genuinely unanswerable from typical web content, give 3-4 for correctness (honest about limitations)
- If a good answer should have been possible, give 1-2 for all criteria

Respond ONLY with a JSON object (no markdown, no explanation):
{{"correctness": N, "relevance": N, "completeness": N, "usefulness": N}}

## Question
{question}

## System's Answer
{answer}

## Your Rating (JSON only)"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AnswerResult:
    query: str
    tool: str
    site: str
    answer: str
    chunks_used: int
    chunk_words_total: int
    correctness: int
    relevance: int
    completeness: int
    usefulness: int
    overall: float  # average of all scores


@dataclass
class ToolAnswerSummary:
    tool: str
    total_queries: int
    avg_correctness: float
    avg_relevance: float
    avg_completeness: float
    avg_usefulness: float
    avg_overall: float
    total_chunks: int
    avg_chunk_words: float
    results: List[AnswerResult]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _generate_answer(client, question: str, chunks: List[str]) -> str:
    """Generate an answer from retrieved chunks using the LLM."""
    context = "\n\n---\n\n".join(chunks[:TOP_K_FOR_ANSWER])
    prompt = ANSWER_PROMPT.format(context=context, question=question)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=ANSWER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0,
                timeout=30,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            if "400" in str(exc) or "BadRequest" in type(exc).__name__:
                raise
            if attempt < 2:
                time.sleep(2 ** attempt * 2)
            else:
                raise


def _judge_answer(client, question: str, answer: str) -> Dict[str, int]:
    """Score an answer using the LLM judge."""
    prompt = JUDGE_PROMPT.format(question=question, answer=answer)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0,
                timeout=30,
            )
            text = response.choices[0].message.content.strip()
            # Parse JSON from response (handle markdown wrapping)
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            scores = json.loads(text)
            return {
                "correctness": int(scores.get("correctness", 3)),
                "relevance": int(scores.get("relevance", 3)),
                "completeness": int(scores.get("completeness", 3)),
                "usefulness": int(scores.get("usefulness", 3)),
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            if attempt < 2:
                time.sleep(1)
            else:
                return {"correctness": 3, "relevance": 3, "completeness": 3, "usefulness": 3}
        except Exception as exc:
            if "400" in str(exc) or "BadRequest" in type(exc).__name__:
                raise
            if attempt < 2:
                time.sleep(2 ** attempt * 2)
            else:
                raise


def _checkpoint_key(run_name: str, tool: str, site: str) -> str:
    return f"{run_name}__{tool}__{site}".replace("/", "_")


def _save_checkpoint(run_name: str, tool: str, site: str, results: List[AnswerResult]) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    key = _checkpoint_key(run_name, tool, site)
    data = [
        {
            "query": r.query, "tool": r.tool, "site": r.site,
            "answer": r.answer, "chunks_used": r.chunks_used,
            "chunk_words_total": r.chunk_words_total,
            "correctness": r.correctness, "relevance": r.relevance,
            "completeness": r.completeness, "usefulness": r.usefulness,
            "overall": r.overall,
        }
        for r in results
    ]
    with open(CHECKPOINT_DIR / f"{key}.json", "w") as f:
        json.dump(data, f)


def _load_checkpoint(run_name: str, tool: str, site: str) -> Optional[List[AnswerResult]]:
    key = _checkpoint_key(run_name, tool, site)
    path = CHECKPOINT_DIR / f"{key}.json"
    if not path.is_file():
        return None
    with open(path) as f:
        data = json.load(f)
    return [
        AnswerResult(
            query=d["query"], tool=d["tool"], site=d["site"],
            answer=d["answer"], chunks_used=d["chunks_used"],
            chunk_words_total=d["chunk_words_total"],
            correctness=d["correctness"], relevance=d["relevance"],
            completeness=d["completeness"], usefulness=d["usefulness"],
            overall=d["overall"],
        )
        for d in data
    ]


def run_answer_quality_test(
    client,
    pages: List[Dict],
    queries: List[Dict],
    tool: str,
    site: str,
    query_vectors: List[List[float]],
) -> List[AnswerResult]:
    """For each query, retrieve chunks, generate answer, judge quality."""
    # Chunk pages
    chunks = []
    chunk_texts = []
    chunk_urls = []
    for page in pages:
        text = page.get("text", "")
        url = page.get("url", "")
        if not text.strip():
            continue
        page_chunks = chunk_markdown(text, max_words=CHUNK_MAX_WORDS, overlap_words=CHUNK_OVERLAP)
        for c in page_chunks:
            chunks.append(c)
            chunk_texts.append(c.text)
            chunk_urls.append(url)

    if not chunk_texts:
        return []

    # Embed chunks
    print(f"    Embedding {len(chunk_texts)} chunks...")
    chunk_vectors = embed_texts(client, chunk_texts)
    vec_matrix = chunk_vectors

    results = []
    for qi, q in enumerate(queries):
        query_text = q["query"]
        query_vec = query_vectors[qi]

        # Retrieve top-K chunks
        scores = cosine_similarity(query_vec, vec_matrix)
        if hasattr(scores, "argsort"):
            import numpy as np
            top_indices = list(np.argsort(scores)[-TOP_K_FOR_ANSWER:][::-1])
        else:
            indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in indexed[:TOP_K_FOR_ANSWER]]

        retrieved_texts = [chunk_texts[i] for i in top_indices]
        total_words = sum(len(t.split()) for t in retrieved_texts)

        # Generate answer
        answer = _generate_answer(client, query_text, retrieved_texts)

        # Judge answer
        scores_dict = _judge_answer(client, query_text, answer)
        overall = sum(scores_dict.values()) / len(scores_dict)

        result = AnswerResult(
            query=query_text,
            tool=tool,
            site=site,
            answer=answer,
            chunks_used=len(retrieved_texts),
            chunk_words_total=total_words,
            correctness=scores_dict["correctness"],
            relevance=scores_dict["relevance"],
            completeness=scores_dict["completeness"],
            usefulness=scores_dict["usefulness"],
            overall=overall,
        )
        results.append(result)

        status = f"{overall:.1f}/5"
        print(f"      Q{qi+1}: {status}  {query_text[:55]}...")

    return results


def generate_report(
    all_results: Dict[str, Dict[str, List[AnswerResult]]],
    tool_names: List[str],
) -> str:
    """Generate ANSWER_QUALITY.md report."""
    lines = [
        "# End-to-End RAG Answer Quality",
        "",
        "Does cleaner crawler output produce better LLM answers?",
        f"Each tool's crawled content is chunked, embedded, retrieved (top-{TOP_K_FOR_ANSWER}),",
        f"and sent to `{ANSWER_MODEL}` to generate an answer. Answers are scored by",
        f"`{JUDGE_MODEL}` on correctness, relevance, completeness, and usefulness (1-5 each).",
        "",
    ]

    # Aggregate per tool
    tool_summaries: Dict[str, ToolAnswerSummary] = {}
    for tool in tool_names:
        all_tool_results: List[AnswerResult] = []
        for site_results in all_results.values():
            if tool in site_results:
                all_tool_results.extend(site_results[tool])

        if not all_tool_results:
            continue

        n = len(all_tool_results)
        tool_summaries[tool] = ToolAnswerSummary(
            tool=tool,
            total_queries=n,
            avg_correctness=sum(r.correctness for r in all_tool_results) / n,
            avg_relevance=sum(r.relevance for r in all_tool_results) / n,
            avg_completeness=sum(r.completeness for r in all_tool_results) / n,
            avg_usefulness=sum(r.usefulness for r in all_tool_results) / n,
            avg_overall=sum(r.overall for r in all_tool_results) / n,
            total_chunks=sum(r.chunks_used for r in all_tool_results),
            avg_chunk_words=sum(r.chunk_words_total for r in all_tool_results) / n,
            results=all_tool_results,
        )

    # Summary table
    total_q = max((s.total_queries for s in tool_summaries.values()), default=0)
    lines.extend([
        f"## Summary ({total_q} queries across {len(all_results)} sites)",
        "",
        "| Tool | Correctness | Relevance | Completeness | Usefulness | **Overall** | Avg tokens/query |",
        "|---|---|---|---|---|---|---|",
    ])

    for tool in tool_names:
        s = tool_summaries.get(tool)
        if not s:
            continue
        avg_tokens = int(s.avg_chunk_words * 1.33)
        lines.append(
            f"| {tool} "
            f"| {s.avg_correctness:.2f} "
            f"| {s.avg_relevance:.2f} "
            f"| {s.avg_completeness:.2f} "
            f"| {s.avg_usefulness:.2f} "
            f"| **{s.avg_overall:.2f}** "
            f"| {avg_tokens:,} |"
        )

    lines.extend(["", ""])

    # Per-site breakdown
    for site, site_results in all_results.items():
        queries = TEST_QUERIES.get(site, [])
        if not queries or not site_results:
            continue

        lines.extend([f"## {site}", ""])
        lines.append("| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |")
        lines.append("|---|---|---|---|---|---|")

        for tool in tool_names:
            results = site_results.get(tool)
            if not results:
                continue
            n = len(results)
            lines.append(
                f"| {tool} "
                f"| {sum(r.correctness for r in results)/n:.2f} "
                f"| {sum(r.relevance for r in results)/n:.2f} "
                f"| {sum(r.completeness for r in results)/n:.2f} "
                f"| {sum(r.usefulness for r in results)/n:.2f} "
                f"| {sum(r.overall for r in results)/n:.2f} |"
            )

        lines.append("")

        # Per-query detail
        lines.append("<details>")
        lines.append(f"<summary>Query-by-query scores for {site}</summary>")
        lines.append("")

        for qi, q in enumerate(queries):
            lines.append(f"**Q{qi+1}: {q['query']}**")
            lines.append("")
            lines.append("| Tool | Score | Answer (truncated) |")
            lines.append("|---|---|---|")
            for tool in tool_names:
                results = site_results.get(tool)
                if not results or qi >= len(results):
                    continue
                r = results[qi]
                short_answer = r.answer[:100].replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {tool} | {r.overall:.1f} | {short_answer}... |")
            lines.append("")

        lines.extend(["</details>", ""])

    # Methodology
    lines.extend([
        "## Methodology",
        "",
        f"- **Answer generation:** `{ANSWER_MODEL}` with temperature=0, max_tokens=500",
        f"- **Answer judging:** `{JUDGE_MODEL}` scores correctness, relevance, completeness, usefulness (1-5)",
        f"- **Retrieval:** Top-{TOP_K_FOR_ANSWER} chunks by cosine similarity (same as retrieval benchmark)",
        f"- **Chunking:** Markdown-aware, {CHUNK_MAX_WORDS} word max, {CHUNK_OVERLAP} word overlap",
        f"- **Embedding:** `{EMBEDDING_MODEL}`",
        "- **Same pipeline for all tools** — only crawler output quality varies",
        "",
    ])

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="End-to-end RAG answer quality benchmark")
    parser.add_argument("--run", default=None, help="Specific run directory name")
    parser.add_argument("--output", default=str(BENCH_DIR / "ANSWER_QUALITY.md"))
    parser.add_argument("--sites", default=None, help="Comma-separated sites")
    parser.add_argument("--tools", default=None, help="Comma-separated tools")
    parser.add_argument("--fresh", action="store_true", help="Clear checkpoints")
    args = parser.parse_args()

    runs_dir = BENCH_DIR / "runs"
    run_dir = runs_dir / args.run if args.run else find_latest_run(runs_dir)

    if not run_dir or not run_dir.is_dir():
        print(f"ERROR: No benchmark run found at {run_dir}")
        sys.exit(1)

    print(f"Using benchmark run: {run_dir.name}")

    if args.fresh:
        import shutil
        if CHECKPOINT_DIR.is_dir():
            shutil.rmtree(CHECKPOINT_DIR)
            print("Cleared answer quality checkpoints.")

    sites = args.sites.split(",") if args.sites else [s for s in TEST_QUERIES.keys()]
    tools = args.tools.split(",") if args.tools else TOOLS

    # Filter to sites with queries and tools with data
    sites = [s for s in sites if s in TEST_QUERIES]
    available_tools = []
    for tool in tools:
        for site in sites:
            jsonl = run_dir / tool / site / "pages.jsonl"
            if jsonl.is_file() and jsonl.stat().st_size > 0:
                available_tools.append(tool)
                break
    available_tools = list(dict.fromkeys(available_tools))  # dedupe preserving order

    print(f"Tools: {', '.join(available_tools)}")
    print(f"Sites: {', '.join(sites)}")

    client = _get_openai_client()

    # Verify API
    print("Verifying OpenAI API...")
    try:
        embed_texts(client, ["test"])
        print("  OK")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        sys.exit(1)

    # Count total work
    total_combos = sum(
        1 for site in sites for tool in available_tools
        if (run_dir / tool / site / "pages.jsonl").is_file()
    )
    total_queries = sum(len(TEST_QUERIES.get(s, [])) for s in sites)
    print(f"\n{total_combos} tool×site combos, {total_queries} queries per tool")
    print(f"Estimated API cost: ~${total_queries * len(available_tools) * 0.002:.2f}")

    all_results: Dict[str, Dict[str, List[AnswerResult]]] = {}
    run_name = run_dir.name

    for site in sites:
        queries = TEST_QUERIES.get(site)
        if not queries:
            continue

        print(f"\n{'='*60}")
        print(f"Site: {site} ({len(queries)} queries)")
        print(f"{'='*60}")

        site_results: Dict[str, List[AnswerResult]] = {}

        # Pre-embed queries once per site
        query_vectors: Optional[List[List[float]]] = None
        needs_work = any(
            _load_checkpoint(run_name, t, site) is None
            and (run_dir / t / site / "pages.jsonl").is_file()
            for t in available_tools
        )
        if needs_work:
            query_texts = [q["query"] for q in queries]
            print(f"  Embedding {len(query_texts)} queries...")
            query_vectors = embed_texts(client, query_texts)

        for tool in available_tools:
            # Check checkpoint
            cached = _load_checkpoint(run_name, tool, site)
            if cached is not None:
                site_results[tool] = cached
                avg = sum(r.overall for r in cached) / len(cached)
                print(f"\n  {tool}: RESUMED — avg score {avg:.2f}/5")
                continue

            jsonl_path = run_dir / tool / site / "pages.jsonl"
            if not jsonl_path.is_file() or jsonl_path.stat().st_size == 0:
                continue

            print(f"\n  {tool}:")
            pages = load_pages(str(jsonl_path))
            print(f"    {len(pages)} pages")

            results = run_answer_quality_test(
                client, pages, queries, tool, site, query_vectors,
            )

            if results:
                site_results[tool] = results
                _save_checkpoint(run_name, tool, site, results)
                avg = sum(r.overall for r in results) / len(results)
                print(f"    Average: {avg:.2f}/5")

        all_results[site] = site_results

    # Generate report
    report = generate_report(all_results, available_tools)
    with open(args.output, "w") as f:
        f.write(report)
    print(f"\nReport written to: {args.output}")

    # Print summary
    print("\n" + "=" * 60)
    print("ANSWER QUALITY SUMMARY")
    print("=" * 60)
    print(f"{'Tool':>15} | {'Correct':>8} | {'Relevant':>8} | {'Complete':>8} | {'Useful':>8} | {'Overall':>8}")
    for tool in available_tools:
        all_tool = []
        for sr in all_results.values():
            all_tool.extend(sr.get(tool, []))
        if not all_tool:
            continue
        n = len(all_tool)
        print(
            f"{tool:>15} | "
            f"{sum(r.correctness for r in all_tool)/n:>8.2f} | "
            f"{sum(r.relevance for r in all_tool)/n:>8.2f} | "
            f"{sum(r.completeness for r in all_tool)/n:>8.2f} | "
            f"{sum(r.usefulness for r in all_tool)/n:>8.2f} | "
            f"{sum(r.overall for r in all_tool)/n:>8.2f}"
        )


if __name__ == "__main__":
    main()
