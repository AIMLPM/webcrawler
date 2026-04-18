# Autoresearch Program — MarkCrawl MRR Optimization

You are optimizing MarkCrawl's extraction + chunking pipeline for **retrieval quality (MRR)**, the metric that most directly affects downstream RAG answer quality.

## Goal

Maximize **overall MRR** reported by `bench/eval_mrr.py`, subject to the guards below.

Current upstream benchmark (v2, 2026-04): MRR 0.698 (3rd), vs leader crawlee 0.733. Local fixture baseline at `max_words=128`: 0.8764. Local fixtures are smaller-scale — do not expect the same absolute number; track the *delta* between a baseline and a candidate.

## Why MRR, not the old composite score

The previous composite (`words × 1/chunks × (1 - nav%) × headings`) rewarded aggressive boilerplate removal and penalized chunk count. It pushed the extractor to strip too much and the chunker to split too little. Result: high content signal (99%) but MRR stuck at 0.698.

MRR directly measures *whether the right chunk shows up at the top of retrieval* — which is the actual downstream KPI.

## Files you may modify

- `markcrawl/extract_content.py` — HTML cleaning, content extraction, markdown conversion
- `markcrawl/chunker.py` — Chunking strategies (`chunk_markdown`, `chunk_text`, `chunk_semantic`)

## Rules

1. Make ONE specific change per experiment
2. All existing tests must pass (`pytest tests/ -q`)
3. Do not add new dependencies
4. Do not change public function signatures
5. Do not remove the extractors (`default`, `trafilatura`, `ensemble`) — you may change their internals
6. Changes must be self-contained and revertible via `git checkout`

## Regression guards (change is rejected if any are violated)

- **MRR must not decrease** vs baseline (allow ±0.005 noise band)
- **Extraction misses** (`answer_span` not in any chunk) must not increase — this protects against the content signal / recall tradeoff going the wrong way
- **Content signal proxy**: `avg_nav_pollution_preamble` must not exceed `max(2.0, 2x baseline)` — keep our #1 ranking on cleanliness
- **Extraction time** must not exceed 1.5x baseline — speed is a headline metric
- **Chunks/page** may increase up to 1.5x baseline (intentionally loosened — splitting answer spans kills MRR)

## High-leverage targets (ranked by expected impact)

1. **Chunk boundaries inside code/table/list blocks.** The current chunker can split inside fenced code blocks, Markdown tables, or list items. Answer spans inside these structures get sliced across chunks, killing MRR. Highest-leverage fix.
2. **Heading-anchored chunk boundaries.** Prefer H2/H3 boundaries over word-count when splitting. Headings are strong retrieval anchors.
3. **Chunk size sweep.** Current benchmark uses 128 words/chunk. Try 160, 200, 256 — smaller chunks risk splitting spans, larger chunks may dilute semantic match.
4. **Heading preservation on sparse pages.** The density heuristic in `clean_dom_for_content()` drops H1–H3 on simple pages (0.9/page on quotes.toscrape vs 2.6 competitors). Keep H1–H3 even when surrounding content is sparse.
5. **Selective rescue of answer-bearing elements.** Code blocks, tables, definition lists should survive even at low density scores. Nav/footer/cookie banners still drop.
6. **Content-type adaptive strategy.** Docs pages, blog posts, and list/catalog pages have different optimal extraction profiles. Only pursue this if 1–5 haven't closed the gap.

## What NOT to change

- Test infrastructure (`tests/`)
- CLI interface (`cli.py`)
- Core crawl loop (`core.py`)
- Fetch layer (`fetch.py`)
- Public API surface
- The MRR eval harness (`bench/eval_mrr.py`) or query files (`bench/fixtures/*.queries.json`) — these define the metric; gaming them invalidates the experiment

## Validation workflow

```bash
# Capture the current state as the baseline
python bench/autoresearch.py --set-baseline

# Make a single change in extract_content.py or chunker.py

# Validate the change
python bench/autoresearch.py --validate --label "never split inside code blocks"

# If ACCEPTED → keep the change, update baseline with --set-baseline
# If REJECTED → revert with `git checkout` and try a different angle
```
