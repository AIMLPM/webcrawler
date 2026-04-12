# Autoresearch Program — MarkCrawl Extraction Optimization

You are optimizing MarkCrawl's content extraction pipeline for RAG retrieval quality.

## Goal

Maximize the composite score:
```
score = total_words * (1 / chunks_per_page) * (1 - avg_nav_pollution / 100) * headings_preserved
```

Higher is better: more words extracted, fewer chunks, less nav pollution, more structural headings.

## Files you may modify

- `markcrawl/extract_content.py` — HTML cleaning, content extraction, markdown conversion
- `markcrawl/chunker.py` — Text chunking strategies

## Rules

1. Make ONE specific change per experiment
2. All existing tests must pass (`pytest tests/ -q`)
3. Do not add new dependencies
4. Do not change the function signatures (they are public API)
5. Do not remove the extractors (default, trafilatura, ensemble) — you may change their internals
6. Changes must be self-contained and revertible via `git checkout`

## Regression guards

- Nav pollution must not increase >2x from baseline
- Chunks per page must not increase >20% from baseline
- Total headings must not decrease >10% from baseline
- Extraction time must not increase >3x from baseline

## What to optimize

- Content density scoring thresholds in `clean_dom_for_content()`
- Tag stripping heuristics (which elements to keep/remove)
- Markdown conversion options (heading style, escaping, code handling)
- Chunk boundary detection (sentence-aware, heading-aware splitting)
- Adaptive chunk sizing parameters

## What NOT to change

- Test infrastructure (tests/)
- CLI interface (cli.py)
- Core crawl loop (core.py)
- Fetch layer (fetch.py)
- Public API surface
