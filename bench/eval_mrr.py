#!/usr/bin/env python3
"""MRR evaluation harness for extraction experiments.

For each fixture with a sibling `.queries.json` file, this runs the extraction
pipeline, chunks the output, embeds each chunk + each query, then computes
the Mean Reciprocal Rank (MRR) of the correct chunk (identified by a ground-
truth answer_span substring) across all queries.

This gives us the ground-truth retrieval signal used to validate autoresearch
experiments — unlike the composite score in autoresearch.py, MRR directly
measures what we care about for RAG.

Query file format (sibling to the .html fixture):

    bench/fixtures/api_docs.queries.json
    [
      {"query": "How do I authenticate?",
       "answer_span": "Authorization header"},
      ...
    ]

Usage:
    python bench/eval_mrr.py                      # default extractor, local embeddings
    python bench/eval_mrr.py --extractor ensemble
    python bench/eval_mrr.py --provider openai    # requires OPENAI_API_KEY
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from markcrawl.chunker import chunk_markdown
from markcrawl.extract_content import (
    html_to_markdown,
    html_to_markdown_ensemble,
    html_to_markdown_trafilatura,
)

DEFAULT_FIXTURES_DIR = Path(__file__).parent / "fixtures"
MRR_LOG_FILE = Path(__file__).parent / "mrr_log.jsonl"

EXTRACTORS = {
    "default": html_to_markdown,
    "trafilatura": html_to_markdown_trafilatura,
    "ensemble": html_to_markdown_ensemble,
}


def load_cases(fixtures_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Load fixtures that have a sibling .queries.json file."""
    fixtures_dir = fixtures_dir or DEFAULT_FIXTURES_DIR
    cases = []
    for html_file in sorted(fixtures_dir.glob("*.html")):
        query_file = html_file.with_suffix(".queries.json")
        if not query_file.exists():
            continue
        queries = json.loads(query_file.read_text())
        cases.append({
            "name": html_file.stem,
            "html": html_file.read_text(encoding="utf-8"),
            "queries": queries,
        })
    return cases


def _embed_local(texts: List[str], model_name: str = "all-MiniLM-L6-v2"):
    """Embed a list of strings with sentence-transformers."""
    import numpy as np
    from sentence_transformers import SentenceTransformer
    model = _embed_local._cache.get(model_name)
    if model is None:
        model = SentenceTransformer(model_name)
        _embed_local._cache[model_name] = model
    vecs = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")

_embed_local._cache = {}  # type: ignore[attr-defined]


def _embed_openai(texts: List[str], model_name: str = "text-embedding-3-small"):
    """Embed a list of strings with OpenAI — matches upstream benchmark methodology."""
    import numpy as np
    from openai import OpenAI
    client = OpenAI()
    resp = client.embeddings.create(model=model_name, input=texts)
    vecs = np.asarray([d.embedding for d in resp.data], dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / (norms + 1e-12)


def _find_correct_chunk(chunks: List[str], answer_span: str) -> int:
    """Return the index of the first chunk containing answer_span (case-insensitive).

    Returns -1 if no chunk contains the span — a "miss" at the extraction layer,
    before retrieval even runs. These count as rank=infinity (reciprocal = 0).
    """
    needle = answer_span.lower()
    for i, chunk in enumerate(chunks):
        if needle in chunk.lower():
            return i
    return -1


def evaluate_case(
    case: Dict[str, Any],
    extractor: Callable,
    embed_fn: Callable,
    max_words: int = 400,
) -> Dict[str, Any]:
    """Run MRR evaluation on a single fixture with its queries."""
    import numpy as np

    title, markdown, _ = extractor(case["html"])
    chunks_obj = chunk_markdown(markdown, max_words=max_words, overlap_words=50,
                                 page_title=title, adaptive=True)
    chunks = [c.text for c in chunks_obj]
    if not chunks:
        return {
            "fixture": case["name"], "chunks": 0, "queries": len(case["queries"]),
            "hits": 0, "misses_extraction": len(case["queries"]), "mrr": 0.0,
            "per_query": [],
        }

    chunk_vecs = embed_fn(chunks)

    per_query: List[Dict[str, Any]] = []
    reciprocals: List[float] = []
    misses_extraction = 0
    for q in case["queries"]:
        query_text = q["query"]
        answer_span = q["answer_span"]
        correct_idx = _find_correct_chunk(chunks, answer_span)
        if correct_idx < 0:
            misses_extraction += 1
            per_query.append({
                "query": query_text, "rank": None, "reciprocal": 0.0,
                "status": "extraction_miss",
            })
            reciprocals.append(0.0)
            continue
        query_vec = embed_fn([query_text])[0]
        sims = chunk_vecs @ query_vec  # cosine — vectors are unit-normalized
        order = np.argsort(-sims)
        rank = int(np.where(order == correct_idx)[0][0]) + 1
        reciprocal = 1.0 / rank
        per_query.append({
            "query": query_text, "rank": rank, "reciprocal": round(reciprocal, 4),
            "correct_chunk_idx": correct_idx, "status": "ok",
        })
        reciprocals.append(reciprocal)

    mrr = sum(reciprocals) / max(len(reciprocals), 1)
    hits = sum(1 for r in reciprocals if r > 0)
    return {
        "fixture": case["name"],
        "chunks": len(chunks),
        "queries": len(case["queries"]),
        "hits": hits,
        "misses_extraction": misses_extraction,
        "mrr": round(mrr, 4),
        "per_query": per_query,
    }


def run_eval(
    extractor_name: str = "default",
    provider: str = "local",
    max_words: int = 400,
    fixtures_dir: Path | None = None,
) -> Dict[str, Any]:
    """Run MRR evaluation across all fixtures with query files."""
    fixtures_dir = fixtures_dir or DEFAULT_FIXTURES_DIR
    cases = load_cases(fixtures_dir)
    if not cases:
        print(f"No fixtures with .queries.json files found in {fixtures_dir}/")
        sys.exit(1)

    extractor = EXTRACTORS[extractor_name]
    embed_fn = _embed_openai if provider == "openai" else _embed_local

    start = time.perf_counter()
    per_fixture: List[Dict[str, Any]] = []
    all_reciprocals: List[float] = []
    total_misses = 0
    for case in cases:
        result = evaluate_case(case, extractor, embed_fn, max_words=max_words)
        per_fixture.append(result)
        for entry in result["per_query"]:
            all_reciprocals.append(entry["reciprocal"])
        total_misses += result["misses_extraction"]
    elapsed = time.perf_counter() - start

    overall_mrr = sum(all_reciprocals) / max(len(all_reciprocals), 1)
    return {
        "extractor": extractor_name,
        "provider": provider,
        "max_words": max_words,
        "fixtures": len(cases),
        "total_queries": len(all_reciprocals),
        "extraction_misses": total_misses,
        "overall_mrr": round(overall_mrr, 4),
        "elapsed_s": round(elapsed, 2),
        "per_fixture": per_fixture,
    }


def print_report(results: Dict[str, Any]) -> None:
    print()
    print("=" * 64)
    print(f"MRR EVALUATION  —  extractor: {results['extractor']}  provider: {results['provider']}")
    print("=" * 64)
    print(f"Fixtures:            {results['fixtures']}")
    print(f"Total queries:       {results['total_queries']}")
    print(f"Extraction misses:   {results['extraction_misses']}  "
          f"(answer_span not in any chunk — {results['extraction_misses']/max(results['total_queries'],1)*100:.0f}%)")
    print(f"Overall MRR:         {results['overall_mrr']}")
    print(f"Elapsed:             {results['elapsed_s']}s")
    print()
    print(f"{'Fixture':<20s} {'Chunks':>7s} {'Queries':>8s} {'Hits':>5s} {'MissExtr':>9s} {'MRR':>7s}")
    print("-" * 64)
    for f in results["per_fixture"]:
        print(f"  {f['fixture']:<18s} {f['chunks']:>7d} {f['queries']:>8d} {f['hits']:>5d} "
              f"{f['misses_extraction']:>9d} {f['mrr']:>7.4f}")
    print()


def log_eval(results: Dict[str, Any], label: str = "") -> None:
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "label": label,
        "extractor": results["extractor"],
        "provider": results["provider"],
        "max_words": results["max_words"],
        "overall_mrr": results["overall_mrr"],
        "extraction_misses": results["extraction_misses"],
        "total_queries": results["total_queries"],
        "per_fixture_mrr": {f["fixture"]: f["mrr"] for f in results["per_fixture"]},
    }
    with open(MRR_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="MRR evaluation harness")
    parser.add_argument("--extractor", default="default", choices=list(EXTRACTORS.keys()))
    parser.add_argument("--provider", default="local", choices=["local", "openai"],
                        help="Embedding provider (local = sentence-transformers, openai = text-embedding-3-small)")
    parser.add_argument("--max-words", type=int, default=400)
    parser.add_argument("--dir", default=None,
                        help="Fixture directory (default: bench/fixtures). "
                             "Use bench/heldout to run held-out validation.")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--label", default="")
    parser.add_argument("--json", action="store_true", help="Emit JSON only (for scripting)")
    args = parser.parse_args()

    if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: --provider openai requires OPENAI_API_KEY to be set.")
        sys.exit(2)

    fixtures_dir = Path(args.dir) if args.dir else None
    results = run_eval(args.extractor, args.provider, args.max_words, fixtures_dir=fixtures_dir)
    if args.json:
        print(json.dumps({k: v for k, v in results.items() if k != "per_fixture"}, indent=2))
    else:
        print_report(results)
    if args.log:
        log_eval(results, label=args.label)
        print(f"Logged to {MRR_LOG_FILE}")


if __name__ == "__main__":
    main()
