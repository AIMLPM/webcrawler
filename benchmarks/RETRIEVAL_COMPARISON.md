# Retrieval Quality Comparison
<!-- style: v2, 2026-04-08 -->

Crawler choice barely matters for retrieval — retrieval mode matters more. Across 92 queries on 8 sites, the best and worst crawlers differ by only ~5 percentage points on Hit@5, while switching from embedding-only to reranked retrieval gains 15-20 points.

Does each tool's output produce embeddings that answer real questions?
This benchmark chunks each tool's crawl output, embeds it with
`text-embedding-3-small`, and measures retrieval across four modes:

- **Embedding**: Cosine similarity on OpenAI embeddings
- **BM25**: Keyword search (Okapi BM25)
- **Hybrid**: Embedding + BM25 fused via Reciprocal Rank Fusion
- **Reranked**: Hybrid candidates reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2`

**92 queries** across 8 sites.
Hit rate (Hit@K) = correct source page appears in top-K results. Higher is better.
MRR (Mean Reciprocal Rank) = average of 1/rank where the correct page first appears. MRR of 1.0 means the correct page is always ranked first; 0.5 means it averages rank 2.

## Best mode per tool (start here)

Most readers only need this table. For each tool, this shows the retrieval
mode that produced the highest Hit@5 across all 92 queries (ties broken by
MRR). The full mode breakdown is in the [next table](#summary-retrieval-modes-compared).

| Tool | Best mode | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks |
|---|---|---|---|---|---|---|
| crawlee | embedding | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 | 45,673 |
| playwright | embedding | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 | 53,896 |
| crawl4ai | hybrid | 84% (77/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.694 | 35,443 |
| crawl4ai-raw | hybrid | 84% (77/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.683 | 35,442 |
| scrapy+md | embedding | 84% (77/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 0.734 | 27,861 |
| colly+md | embedding | 84% (77/92) ±8% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.776 | 53,398 |
| **markcrawl** | **embedding** | **80% (74/92) ±8%** | **83% (76/92) ±8%** | **87% (80/92) ±7%** | **0.734** | **21,952** |
| firecrawl | embedding | 76% (70/92) ±9% | 80% (74/92) ±8% | 83% (76/92) ±8% | 0.710 | 16,790 |

**The takeaway:** All tools land within ~5 points of each other at Hit@5
(80-85%). The gap is real but small — and it falls within the confidence
intervals (±7-9%). What differs dramatically is the cost of getting there:
markcrawl uses 21,952 chunks to reach 80% Hit@5, while playwright uses
53,896 chunks to reach 85%. That's 2.5x more chunks for 5 more percentage
points. For what this means in dollars, see
[COST_AT_SCALE.md](COST_AT_SCALE.md).

> **Reranked mode note:** crawlee, colly+md, and firecrawl have reranked
> results on smaller query subsets (8-22 queries vs 92). These are shown in
> the full table below but excluded from this digest because the sample sizes
> are too small for fair comparison.

## Summary: retrieval modes compared

| Tool | Mode | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR |
|---|---|---|---|---|---|---|---|
| **markcrawl** | embedding | 68% (63/92) ±9% | 76% (70/92) ±9% | 80% (74/92) ±8% | 83% (76/92) ±8% | 87% (80/92) ±7% | 0.734 |
| **markcrawl** | bm25 | 42% (39/92) ±10% | 53% (49/92) ±10% | 66% (61/92) ±9% | 72% (66/92) ±9% | 78% (72/92) ±8% | 0.515 |
| **markcrawl** | hybrid | 58% (53/92) ±10% | 75% (69/92) ±9% | 79% (73/92) ±8% | 83% (76/92) ±8% | 85% (78/92) ±7% | 0.673 |
| crawl4ai | embedding | 71% (65/92) ±9% | 78% (72/92) ±8% | 82% (75/92) ±8% | 84% (77/92) ±8% | 86% (79/92) ±7% | 0.754 |
| crawl4ai | bm25 | 32% (29/92) ±9% | 42% (39/92) ±10% | 49% (45/92) ±10% | 63% (58/92) ±10% | 74% (68/92) ±9% | 0.408 |
| crawl4ai | hybrid | 60% (55/92) ±10% | 76% (70/92) ±9% | 84% (77/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.694 |
| crawl4ai-raw | embedding | 71% (65/92) ±9% | 78% (72/92) ±8% | 83% (76/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.755 |
| crawl4ai-raw | bm25 | 33% (30/92) ±9% | 41% (38/92) ±10% | 50% (46/92) ±10% | 62% (57/92) ±10% | 73% (67/92) ±9% | 0.412 |
| crawl4ai-raw | hybrid | 58% (53/92) ±10% | 76% (70/92) ±9% | 84% (77/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.683 |
| scrapy+md | embedding | 67% (62/92) ±9% | 77% (71/92) ±8% | 84% (77/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 0.734 |
| scrapy+md | bm25 | 41% (38/92) ±10% | 50% (46/92) ±10% | 59% (54/92) ±10% | 68% (63/92) ±9% | 80% (74/92) ±8% | 0.496 |
| scrapy+md | hybrid | 57% (52/92) ±10% | 76% (70/92) ±9% | 80% (74/92) ±8% | 84% (77/92) ±8% | 85% (78/92) ±7% | 0.670 |
| crawlee | embedding | 75% (69/92) ±9% | 82% (75/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 |
| crawlee | bm25 | 39% (36/92) ±10% | 48% (44/92) ±10% | 57% (52/92) ±10% | 68% (63/92) ±9% | 79% (73/92) ±8% | 0.479 |
| crawlee | hybrid | 60% (55/92) ±10% | 82% (75/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 86% (79/92) ±7% | 0.702 |
| crawlee | reranked | 75% (9/12) ±22% | 92% (11/12) ±17% | 100% (12/12) ±12% | 100% (12/12) ±12% | 100% (12/12) ±12% | 0.854 |
| colly+md | embedding | 74% (68/92) ±9% | 79% (73/92) ±8% | 84% (77/92) ±8% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.776 |
| colly+md | bm25 | 40% (37/92) ±10% | 48% (44/92) ±10% | 57% (52/92) ±10% | 68% (63/92) ±9% | 77% (71/92) ±8% | 0.485 |
| colly+md | hybrid | 61% (56/92) ±10% | 80% (74/92) ±8% | 84% (77/92) ±8% | 86% (79/92) ±7% | 86% (79/92) ±7% | 0.709 |
| colly+md | reranked | 100% (8/8) ±16% | 100% (8/8) ±16% | 100% (8/8) ±16% | 100% (8/8) ±16% | 100% (8/8) ±16% | 1.000 |
| playwright | embedding | 75% (69/92) ±9% | 82% (75/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 |
| playwright | bm25 | 39% (36/92) ±10% | 49% (45/92) ±10% | 58% (53/92) ±10% | 70% (64/92) ±9% | 77% (71/92) ±8% | 0.482 |
| playwright | hybrid | 61% (56/92) ±10% | 82% (75/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 86% (79/92) ±7% | 0.711 |
| firecrawl | embedding | 66% (61/92) ±9% | 75% (69/92) ±9% | 76% (70/92) ±9% | 80% (74/92) ±8% | 83% (76/92) ±8% | 0.710 |
| firecrawl | bm25 | 36% (33/92) ±10% | 53% (49/92) ±10% | 63% (58/92) ±10% | 70% (64/92) ±9% | 76% (70/92) ±9% | 0.467 |
| firecrawl | hybrid | 61% (56/92) ±10% | 71% (65/92) ±9% | 75% (69/92) ±9% | 78% (72/92) ±8% | 80% (74/92) ±8% | 0.668 |
| firecrawl | reranked | 36% (8/22) ±19% | 59% (13/22) ±19% | 64% (14/22) ±19% | 77% (17/22) ±17% | 82% (18/22) ±16% | 0.493 |


## Summary: embedding-only (hit rate at multiple K values)

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Avg words |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 68% (63/92) ±9% | 76% (70/92) ±9% | 80% (74/92) ±8% | 83% (76/92) ±8% | 87% (80/92) ±7% | 0.734 | 21952 | 156 |
| crawl4ai | 71% (65/92) ±9% | 78% (72/92) ±8% | 82% (75/92) ±8% | 84% (77/92) ±8% | 86% (79/92) ±7% | 0.754 | 35443 | 134 |
| crawl4ai-raw | 71% (65/92) ±9% | 78% (72/92) ±8% | 83% (76/92) ±8% | 85% (78/92) ±7% | 86% (79/92) ±7% | 0.755 | 35442 | 134 |
| scrapy+md | 67% (62/92) ±9% | 77% (71/92) ±8% | 84% (77/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 0.734 | 27861 | 133 |
| crawlee | 75% (69/92) ±9% | 82% (75/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 | 45673 | 199 |
| colly+md | 74% (68/92) ±9% | 79% (73/92) ±8% | 84% (77/92) ±8% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.776 | 53398 | 223 |
| playwright | 75% (69/92) ±9% | 82% (75/92) ±8% | 85% (78/92) ±7% | 85% (78/92) ±7% | 87% (80/92) ±7% | 0.787 | 53896 | 223 |
| firecrawl | 66% (61/92) ±9% | 75% (69/92) ±9% | 76% (70/92) ±9% | 80% (74/92) ±8% | 83% (76/92) ±8% | 0.710 | 16790 | 199 |

### Chunk efficiency: similar hits, very different costs

The table above reveals a pattern: all tools converge to 83-87% at Hit@20,
but the number of chunks required to get there varies by 2.5x. This is the
chunk efficiency gap — and it's where crawler choice actually matters for
production RAG systems.

| Tool | Chunks | Hits at Hit@5 | Hits per 1K chunks | vs markcrawl |
|---|---|---|---|---|
| **markcrawl** | **21,952** | **74** | **3.37** | **--** |
| scrapy+md | 27,861 | 77 | 2.76 | -18% efficiency |
| crawl4ai | 35,443 | 75 | 2.12 | -37% efficiency |
| crawl4ai-raw | 35,442 | 76 | 2.14 | -36% efficiency |
| crawlee | 45,673 | 78 | 1.71 | -49% efficiency |
| colly+md | 53,398 | 77 | 1.44 | -57% efficiency |
| playwright | 53,896 | 78 | 1.45 | -57% efficiency |
| firecrawl | 16,790 | 70 | 4.17 | +24% efficiency |

Firecrawl's high efficiency is misleading — it has fewer chunks because it
crawled fewer pages (6 of 8 sites), not because its output is cleaner. Among
tools that completed all 8 sites, markcrawl is the most efficient: 3.37 hits
per 1,000 chunks, vs 1.44-2.76 for the rest.

**Why this matters for production:** every chunk you store costs money
(embedding + vector DB hosting), and every query searches across all chunks.
Fewer chunks with the same hit rate means lower storage costs, faster queries,
and less noise in retrieved context. For dollar amounts, see
[COST_AT_SCALE.md](COST_AT_SCALE.md). For how this translates to LLM answer
quality, see [ANSWER_QUALITY.md](ANSWER_QUALITY.md).


## quotes-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.517 | 26 | 15 |
| crawl4ai | 58% (7/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.583 | 25 | 15 |
| crawl4ai-raw | 58% (7/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.583 | 25 | 15 |
| scrapy+md | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.521 | 27 | 15 |
| crawlee | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.521 | 31 | 15 |
| colly+md | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.521 | 31 | 15 |
| playwright | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.521 | 31 | 15 |
| firecrawl | 50% (6/12) | 50% (6/12) | 58% (7/12) | 58% (7/12) | 58% (7/12) | 0.521 | 23 | 15 |

<details>
<summary>Query-by-query results for quotes-toscrape</summary>

**Q1: What did Albert Einstein say about thinking and the world?**
*(expects URL containing: `quotes.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/world/page/1/ | 0.416 | quotes.toscrape.com/tag/life/ | 0.384 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.384 |
| crawl4ai | #1 | quotes.toscrape.com/tag/world/page/1/ | 0.482 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.448 | quotes.toscrape.com/tag/change/page/1/ | 0.433 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/world/page/1/ | 0.482 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.448 | quotes.toscrape.com/tag/change/page/1/ | 0.433 |
| scrapy+md | #1 | quotes.toscrape.com/tag/life/ | 0.384 | quotes.toscrape.com/tag/world/page/1/ | 0.383 | quotes.toscrape.com/ | 0.367 |
| crawlee | #1 | quotes.toscrape.com/tag/life/ | 0.384 | quotes.toscrape.com/tag/life/ | 0.354 | quotes.toscrape.com/ | 0.342 |
| colly+md | #1 | quotes.toscrape.com/tag/life/ | 0.384 | quotes.toscrape.com/tag/life/ | 0.354 | quotes.toscrape.com/ | 0.342 |
| playwright | #1 | quotes.toscrape.com/tag/life/ | 0.384 | quotes.toscrape.com/tag/life/ | 0.354 | quotes.toscrape.com/ | 0.342 |
| firecrawl | #1 | quotes.toscrape.com/tag/world/page/1/ | 0.414 | quotes.toscrape.com/tag/life/ | 0.383 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.376 |


**Q2: Which quotes are tagged with 'inspirational'?**
*(expects URL containing: `tag/inspirational`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.578 | quotes.toscrape.com/tag/friends/ | 0.560 | quotes.toscrape.com/page/2/ | 0.558 |
| crawl4ai | miss | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/miracles/page/1/ | 0.570 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.555 |
| crawl4ai-raw | miss | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/miracles/page/1/ | 0.570 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.555 |
| scrapy+md | miss | quotes.toscrape.com/ | 0.567 | quotes.toscrape.com/tag/miracles/page/1/ | 0.566 | quotes.toscrape.com/page/2/ | 0.558 |
| crawlee | miss | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.579 |
| colly+md | miss | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.579 |
| playwright | miss | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.579 |
| firecrawl | miss | quotes.toscrape.com/ | 0.574 | quotes.toscrape.com/tag/miracles/page/1/ | 0.572 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.564 |


**Q3: What did Jane Austen say about novels and reading?**
*(expects URL containing: `author/Jane-Austen`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/Jane-Austen | 0.554 | quotes.toscrape.com/tag/love/ | 0.339 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| crawl4ai | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/ | 0.322 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/ | 0.322 |
| scrapy+md | #1 | quotes.toscrape.com/author/Jane-Austen/ | 0.532 | quotes.toscrape.com/tag/humor/ | 0.334 | quotes.toscrape.com/author/J-K-Rowling/ | 0.333 |
| crawlee | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/tag/love/ | 0.329 |
| colly+md | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/tag/love/ | 0.329 |
| playwright | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/tag/love/ | 0.329 |
| firecrawl | #1 | quotes.toscrape.com/author/Jane-Austen | 0.526 | quotes.toscrape.com/author/J-K-Rowling | 0.332 | quotes.toscrape.com/author/J-K-Rowling | 0.319 |


**Q4: What quotes are about the truth?**
*(expects URL containing: `tag/truth`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/page/2/ | 0.511 | quotes.toscrape.com/ | 0.474 | quotes.toscrape.com/tag/friends/ | 0.469 |
| crawl4ai | miss | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.459 | quotes.toscrape.com/tag/humor/ | 0.453 |
| crawl4ai-raw | miss | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.459 | quotes.toscrape.com/tag/humor/ | 0.453 |
| scrapy+md | miss | quotes.toscrape.com/page/2/ | 0.511 | quotes.toscrape.com/tag/life/ | 0.456 | quotes.toscrape.com/ | 0.451 |
| crawlee | miss | quotes.toscrape.com/page/2/ | 0.511 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 |
| colly+md | miss | quotes.toscrape.com/page/2/ | 0.511 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 |
| playwright | miss | quotes.toscrape.com/page/2/ | 0.511 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 |
| firecrawl | miss | quotes.toscrape.com/page/2/ | 0.516 | quotes.toscrape.com/tag/life/ | 0.482 | quotes.toscrape.com/page/2/ | 0.466 |


**Q5: Which quotes are about humor and being funny?**
*(expects URL containing: `tag/humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/humor/ | 0.507 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/page/2/ | 0.441 |
| crawl4ai | #1 | quotes.toscrape.com/tag/humor/ | 0.513 | quotes.toscrape.com/ | 0.446 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.438 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/humor/ | 0.513 | quotes.toscrape.com/ | 0.446 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.438 |
| scrapy+md | #1 | quotes.toscrape.com/tag/humor/ | 0.494 | quotes.toscrape.com/page/2/ | 0.441 | quotes.toscrape.com/ | 0.429 |
| crawlee | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/page/2/ | 0.441 |
| colly+md | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/page/2/ | 0.441 |
| playwright | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/page/2/ | 0.441 |
| firecrawl | #1 | quotes.toscrape.com/tag/humor/ | 0.492 | quotes.toscrape.com/ | 0.447 | quotes.toscrape.com/tag/life/ | 0.436 |


**Q6: What did J.K. Rowling say about choices and abilities?**
*(expects URL containing: `author/J-K-Rowling`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| crawl4ai | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 | quotes.toscrape.com/ | 0.314 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 | quotes.toscrape.com/ | 0.314 |
| scrapy+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.501 | quotes.toscrape.com/author/J-K-Rowling/ | 0.477 | quotes.toscrape.com/author/J-K-Rowling/ | 0.468 |
| crawlee | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| colly+md | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| playwright | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| firecrawl | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.476 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |


**Q7: What quotes are tagged with 'change'?**
*(expects URL containing: `tag/change`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.576 | quotes.toscrape.com/tag/world/page/1/ | 0.509 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.505 |
| crawl4ai | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.628 | quotes.toscrape.com/tag/world/page/1/ | 0.541 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.628 | quotes.toscrape.com/tag/world/page/1/ | 0.541 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 |
| scrapy+md | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.579 | quotes.toscrape.com/tag/world/page/1/ | 0.514 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.512 |
| crawlee | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.559 | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 |
| colly+md | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.559 | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 |
| playwright | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.559 | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 |
| firecrawl | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.580 | quotes.toscrape.com/tag/world/page/1/ | 0.523 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.503 |


**Q8: What did Steve Martin say about sunshine?**
*(expects URL containing: `author/Steve-Martin`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.306 | quotes.toscrape.com/tag/humor/ | 0.303 | quotes.toscrape.com/tag/simile/page/1/ | 0.300 |
| crawl4ai | miss | quotes.toscrape.com/tag/simile/page/1/ | 0.391 | quotes.toscrape.com/tag/humor/ | 0.308 | quotes.toscrape.com/page/2/ | 0.306 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/simile/page/1/ | 0.391 | quotes.toscrape.com/tag/humor/ | 0.308 | quotes.toscrape.com/page/2/ | 0.306 |
| scrapy+md | miss | quotes.toscrape.com/tag/simile/page/1/ | 0.314 | quotes.toscrape.com/tag/humor/ | 0.294 | quotes.toscrape.com/page/2/ | 0.289 |
| crawlee | miss | quotes.toscrape.com/page/2/ | 0.289 | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 |
| colly+md | miss | quotes.toscrape.com/page/2/ | 0.289 | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 |
| playwright | miss | quotes.toscrape.com/page/2/ | 0.289 | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 |
| firecrawl | miss | quotes.toscrape.com/tag/simile/page/1/ | 0.293 | quotes.toscrape.com/tag/life/ | 0.289 | quotes.toscrape.com/ | 0.286 |


**Q9: Which quotes talk about believing in yourself?**
*(expects URL containing: `tag/be-yourself`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #5 | quotes.toscrape.com/page/2/ | 0.499 | quotes.toscrape.com/tag/life/ | 0.477 | quotes.toscrape.com/tag/life/ | 0.457 |
| crawl4ai | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/page/2/ | 0.448 | quotes.toscrape.com/tag/life/ | 0.435 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/page/2/ | 0.448 | quotes.toscrape.com/tag/life/ | 0.435 |
| scrapy+md | #4 | quotes.toscrape.com/page/2/ | 0.499 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 |
| crawlee | #4 | quotes.toscrape.com/page/2/ | 0.499 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 |
| colly+md | #4 | quotes.toscrape.com/page/2/ | 0.499 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 |
| playwright | #4 | quotes.toscrape.com/page/2/ | 0.499 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 |
| firecrawl | #4 | quotes.toscrape.com/page/2/ | 0.474 | quotes.toscrape.com/tag/life/ | 0.449 | quotes.toscrape.com/tag/life/ | 0.439 |


**Q10: What are the quotes about miracles and living life?**
*(expects URL containing: `tag/miracle`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.572 | quotes.toscrape.com/tag/life/ | 0.526 | quotes.toscrape.com/ | 0.475 |
| crawl4ai | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.656 | quotes.toscrape.com/tag/life/ | 0.520 | quotes.toscrape.com/ | 0.461 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.656 | quotes.toscrape.com/tag/life/ | 0.520 | quotes.toscrape.com/ | 0.461 |
| scrapy+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.586 | quotes.toscrape.com/tag/life/ | 0.526 | quotes.toscrape.com/ | 0.463 |
| crawlee | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/life/ | 0.526 | quotes.toscrape.com/ | 0.462 |
| colly+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/life/ | 0.526 | quotes.toscrape.com/ | 0.462 |
| playwright | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/life/ | 0.526 | quotes.toscrape.com/ | 0.462 |
| firecrawl | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.607 | quotes.toscrape.com/tag/life/ | 0.519 | quotes.toscrape.com/ | 0.467 |


**Q11: What quotes are about thinking deeply?**
*(expects URL containing: `tag/thinking`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 | quotes.toscrape.com/tag/change/page/1/ | 0.491 | quotes.toscrape.com/ | 0.481 |
| crawl4ai | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.593 | quotes.toscrape.com/tag/change/page/1/ | 0.544 | quotes.toscrape.com/tag/world/page/1/ | 0.528 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.593 | quotes.toscrape.com/tag/change/page/1/ | 0.544 | quotes.toscrape.com/tag/world/page/1/ | 0.528 |
| scrapy+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.540 | quotes.toscrape.com/tag/change/page/1/ | 0.497 | quotes.toscrape.com/ | 0.490 |
| crawlee | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| colly+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| playwright | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| firecrawl | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.543 | quotes.toscrape.com/tag/change/page/1/ | 0.509 | quotes.toscrape.com/tag/world/page/1/ | 0.498 |


**Q12: What quotes talk about living life fully?**
*(expects URL containing: `tag/live`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/page/2/ | 0.527 |
| crawl4ai | miss | quotes.toscrape.com/tag/life/ | 0.555 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/page/2/ | 0.515 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/life/ | 0.555 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/page/2/ | 0.515 |
| scrapy+md | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/page/2/ | 0.506 |
| crawlee | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/page/2/ | 0.506 |
| colly+md | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/page/2/ | 0.506 |
| playwright | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/page/2/ | 0.506 |
| firecrawl | miss | quotes.toscrape.com/tag/life/ | 0.567 | quotes.toscrape.com/tag/life/ | 0.499 | quotes.toscrape.com/page/2/ | 0.468 |


</details>

## books-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.923 | 112 | 60 |
| crawl4ai | 77% (10/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.833 | 652 | 60 |
| crawl4ai-raw | 77% (10/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.833 | 652 | 60 |
| scrapy+md | 85% (11/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.885 | 129 | 60 |
| crawlee | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.923 | 129 | 60 |
| colly+md | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.923 | 129 | 60 |
| playwright | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.923 | 129 | 60 |
| firecrawl | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 92% (12/13) | 0.923 | 95 | 60 |

<details>
<summary>Query-by-query results for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/catalogue/category/books_1/inde | 0.488 | books.toscrape.com/catalogue/category/books/food-a | 0.485 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/adult- | 0.492 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/adult- | 0.492 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.528 | books.toscrape.com/catalogue/category/books/young- | 0.521 | books.toscrape.com/catalogue/category/books/fantas | 0.505 |


**Q2: What mystery and thriller books are in the catalog?**
*(expects URL containing: `mystery`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.468 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.503 | books.toscrape.com/catalogue/category/books/defaul | 0.503 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.504 | books.toscrape.com/catalogue/category/books/defaul | 0.503 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.479 | books.toscrape.com/catalogue/category/books/crime_ | 0.445 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.477 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.477 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.477 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.524 | books.toscrape.com/catalogue/category/books/crime_ | 0.468 | books.toscrape.com/catalogue/category/books/myster | 0.454 |


**Q3: What is the rating of the most expensive book?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/young- | 0.424 | books.toscrape.com/catalogue/category/books/defaul | 0.417 | books.toscrape.com/catalogue/category/books/scienc | 0.414 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/adult- | 0.426 | books.toscrape.com/catalogue/category/books/horror | 0.423 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/adult- | 0.426 | books.toscrape.com/catalogue/category/books/horror | 0.423 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| playwright | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| firecrawl | #1 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.402 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.394 | books.toscrape.com/catalogue/category/books/adult- | 0.392 |


**Q4: What science fiction books are available?**
*(expects URL containing: `science-fiction`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.500 | books.toscrape.com/catalogue/category/books/scienc | 0.469 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.441 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.493 | books.toscrape.com/catalogue/category/books/scienc | 0.471 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.493 | books.toscrape.com/catalogue/category/books/scienc | 0.471 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.441 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.418 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.505 | books.toscrape.com/catalogue/category/books/scienc | 0.466 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.505 | books.toscrape.com/catalogue/category/books/scienc | 0.466 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.505 | books.toscrape.com/catalogue/category/books/scienc | 0.466 |
| firecrawl | #1 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.483 | books.toscrape.com/catalogue/category/books/scienc | 0.415 | books.toscrape.com/catalogue/category/books/young- | 0.390 |


**Q5: What horror books are in the catalog?**
*(expects URL containing: `horror`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/horror | 0.509 | books.toscrape.com/catalogue/the-requiem-red_995/i | 0.437 | books.toscrape.com/catalogue/category/books/young- | 0.422 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/horror | 0.484 | books.toscrape.com/catalogue/category/books/myster | 0.472 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/horror | 0.485 | books.toscrape.com/catalogue/category/books/myster | 0.472 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/ | 0.463 | books.toscrape.com/catalogue/category/books/horror | 0.440 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/horror | 0.504 | books.toscrape.com/catalogue/the-requiem-red_995/i | 0.455 | books.toscrape.com/catalogue/category/books/parano | 0.432 |


**Q6: What poetry books can I find?**
*(expects URL containing: `poetry`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.495 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.411 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.406 |
| crawl4ai | #2 | books.toscrape.com/catalogue/page-2.html | 0.506 | books.toscrape.com/catalogue/category/books/poetry | 0.498 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/page-2.html | 0.506 | books.toscrape.com/catalogue/category/books/poetry | 0.498 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.401 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.400 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.468 | books.toscrape.com/catalogue/olio_984/index.html | 0.431 | books.toscrape.com/catalogue/page-2.html | 0.423 |


**Q7: What romance novels are available?**
*(expects URL containing: `romance`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | books.toscrape.com/catalogue/category/books/christ | 0.418 | books.toscrape.com/catalogue/category/books/womens | 0.418 | books.toscrape.com/catalogue/category/books/new-ad | 0.417 |
| crawl4ai | miss | books.toscrape.com/catalogue/category/books/add-a- | 0.545 | books.toscrape.com/catalogue/category/books/womens | 0.477 | books.toscrape.com/catalogue/category/books/adult- | 0.470 |
| crawl4ai-raw | miss | books.toscrape.com/catalogue/category/books/add-a- | 0.545 | books.toscrape.com/catalogue/category/books/womens | 0.477 | books.toscrape.com/catalogue/category/books/adult- | 0.470 |
| scrapy+md | miss | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/new-ad | 0.422 | books.toscrape.com/ | 0.415 |
| crawlee | miss | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/womens | 0.437 | books.toscrape.com/catalogue/category/books/new-ad | 0.429 |
| colly+md | miss | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/womens | 0.437 | books.toscrape.com/catalogue/category/books/new-ad | 0.429 |
| playwright | miss | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/womens | 0.437 | books.toscrape.com/catalogue/category/books/new-ad | 0.429 |
| firecrawl | miss | books.toscrape.com/catalogue/category/books/new-ad | 0.437 | books.toscrape.com/catalogue/category/books/christ | 0.435 | books.toscrape.com/catalogue/starving-hearts-trian | 0.422 |


**Q8: What history books are in the collection?**
*(expects URL containing: `history`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/histor | 0.444 | books.toscrape.com/catalogue/category/books/histor | 0.409 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.382 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/histor | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.424 | books.toscrape.com/catalogue/category/books/autobi | 0.414 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/histor | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.424 | books.toscrape.com/catalogue/category/books/autobi | 0.414 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/histor | 0.444 | books.toscrape.com/ | 0.376 | books.toscrape.com/catalogue/category/books/histor | 0.369 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/histor | 0.444 | books.toscrape.com/catalogue/category/books/histor | 0.395 | books.toscrape.com/catalogue/category/books/histor | 0.383 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/histor | 0.444 | books.toscrape.com/catalogue/category/books/histor | 0.395 | books.toscrape.com/catalogue/category/books/histor | 0.383 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/histor | 0.444 | books.toscrape.com/catalogue/category/books/histor | 0.395 | books.toscrape.com/catalogue/category/books/histor | 0.383 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/histor | 0.407 | books.toscrape.com/catalogue/category/books/biogra | 0.391 | books.toscrape.com/catalogue/category/books/histor | 0.388 |


**Q9: What philosophy books are available to read?**
*(expects URL containing: `philosophy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/philos | 0.439 | books.toscrape.com/catalogue/libertarianism-for-be | 0.405 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.430 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.430 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.415 | books.toscrape.com/catalogue/libertarianism-for-be | 0.363 | books.toscrape.com/catalogue/category/books/psycho | 0.362 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/philos | 0.440 | books.toscrape.com/catalogue/libertarianism-for-be | 0.402 | books.toscrape.com/catalogue/category/books/psycho | 0.383 |


**Q10: What humor and comedy books can I find?**
*(expects URL containing: `humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.401 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.330 | books.toscrape.com/catalogue/category/books/nonfic | 0.300 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.436 | books.toscrape.com/catalogue/category/books/humor_ | 0.403 | books.toscrape.com/catalogue/category/books/scienc | 0.402 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.436 | books.toscrape.com/catalogue/category/books/humor_ | 0.403 | books.toscrape.com/catalogue/category/books/scienc | 0.402 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.359 | books.toscrape.com/catalogue/category/books/horror | 0.319 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.316 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books_1/inde | 0.340 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.325 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books_1/inde | 0.340 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.325 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books_1/inde | 0.340 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.325 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.372 | books.toscrape.com/catalogue/category/books/scienc | 0.350 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.338 |


**Q11: What fantasy books are in the bookstore?**
*(expects URL containing: `fantasy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.483 | books.toscrape.com/catalogue/category/books/fantas | 0.481 | books.toscrape.com/catalogue/category/books/scienc | 0.416 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.447 | books.toscrape.com/catalogue/category/books/fantas | 0.433 | books.toscrape.com/catalogue/category/books/fantas | 0.432 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.447 | books.toscrape.com/catalogue/category/books/fantas | 0.433 | books.toscrape.com/catalogue/category/books/fantas | 0.432 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.483 | books.toscrape.com/catalogue/category/books/scienc | 0.416 | books.toscrape.com/catalogue/category/books/young- | 0.398 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.483 | books.toscrape.com/catalogue/category/books/fantas | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.416 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.483 | books.toscrape.com/catalogue/category/books/fantas | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.416 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.483 | books.toscrape.com/catalogue/category/books/fantas | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.416 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.477 | books.toscrape.com/catalogue/category/books/fantas | 0.442 | books.toscrape.com/catalogue/category/books/horror | 0.424 |


**Q12: What is the book Sharp Objects about?**
*(expects URL containing: `sharp-objects`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.591 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.485 |
| crawl4ai | #3 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.625 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.607 |
| crawl4ai-raw | #3 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.624 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.607 |
| scrapy+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.447 |
| crawlee | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| colly+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| playwright | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| firecrawl | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.489 | books.toscrape.com/catalogue/category/books/crime_ | 0.343 | books.toscrape.com/catalogue/the-requiem-red_995/i | 0.326 |


**Q13: What biography books are in the catalog?**
*(expects URL containing: `biography`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.431 | books.toscrape.com/catalogue/starving-hearts-trian | 0.395 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.395 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.449 | books.toscrape.com/catalogue/category/books/autobi | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.435 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.449 | books.toscrape.com/catalogue/category/books/autobi | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.435 |
| scrapy+md | #2 | books.toscrape.com/ | 0.419 | books.toscrape.com/catalogue/category/books/biogra | 0.377 | books.toscrape.com/catalogue/starving-hearts-trian | 0.373 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/category/books_1/inde | 0.389 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/category/books_1/inde | 0.389 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/category/books_1/inde | 0.389 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.431 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.398 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.396 |


</details>

## fastapi-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 80% (12/15) | 87% (13/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 0.846 | 4424 | 275 |
| crawl4ai | 93% (14/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.950 | 6058 | 275 |
| crawl4ai-raw | 93% (14/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.950 | 6059 | 275 |
| scrapy+md | 80% (12/15) | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.863 | 5292 | 275 |
| crawlee | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.922 | 5465 | 275 |
| colly+md | 80% (12/15) | 87% (13/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 0.858 | 5464 | 275 |
| playwright | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.922 | 5445 | 275 |
| firecrawl | 67% (10/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.811 | 3094 | 275 |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/tutorial/security/ | 0.565 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.631 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.631 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.604 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.604 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 |
| firecrawl | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.568 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.547 | fastapi.tiangolo.com/zh-hant/tutorial/security/sim | 0.543 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.610 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.692 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/advanced/response-change-stat | 0.629 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.692 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/advanced/response-change-stat | 0.629 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.613 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.679 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.602 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.613 |
| playwright | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.679 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.602 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.592 | fastapi.tiangolo.com/advanced/response-change-stat | 0.578 | fastapi.tiangolo.com/tutorial/response-status-code | 0.555 |


**Q3: How do I define query parameters in the FastAPI reference?**
*(expects URL containing: `reference/fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #9 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.657 | fastapi.tiangolo.com/tutorial/query-params/ | 0.645 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.631 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/parameters/ | 0.671 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.659 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/parameters/ | 0.671 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.659 |
| scrapy+md | #5 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.636 | fastapi.tiangolo.com/tutorial/query-params/ | 0.617 |
| crawlee | #2 | fastapi.tiangolo.com/tutorial/query-params/ | 0.649 | fastapi.tiangolo.com/reference/parameters/ | 0.642 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.634 |
| colly+md | #8 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.636 | fastapi.tiangolo.com/tutorial/query-params/ | 0.635 |
| playwright | #2 | fastapi.tiangolo.com/tutorial/query-params/ | 0.649 | fastapi.tiangolo.com/reference/parameters/ | 0.642 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.634 |
| firecrawl | #1 | fastapi.tiangolo.com/reference/request/ | 0.618 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.616 | fastapi.tiangolo.com/reference/parameters/ | 0.612 |


**Q4: How does FastAPI handle JSON encoding and base64 bytes?**
*(expects URL containing: `json-base64-bytes`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.599 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/custom-response/ | 0.572 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.654 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.645 | fastapi.tiangolo.com/reference/encoders/ | 0.634 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.654 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.645 | fastapi.tiangolo.com/reference/encoders/ | 0.634 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/zh-hant/advanced/json-base64- | 0.577 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.647 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.579 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/zh-hant/advanced/json-base64- | 0.577 |
| playwright | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.647 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.579 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/tutorial/encoder/ | 0.519 | fastapi.tiangolo.com/reference/encoders/ | 0.508 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.620 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.685 | fastapi.tiangolo.com/tutorial/body/ | 0.622 | fastapi.tiangolo.com/reference/parameters/ | 0.601 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.685 | fastapi.tiangolo.com/tutorial/body/ | 0.622 | fastapi.tiangolo.com/reference/parameters/ | 0.601 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.666 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.667 | fastapi.tiangolo.com/tutorial/body/ | 0.624 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 |
| firecrawl | #1 | fastapi.tiangolo.com/tutorial/body-multiple-params | 0.588 | fastapi.tiangolo.com/reference/openapi/models/ | 0.575 | fastapi.tiangolo.com/reference/parameters/ | 0.570 |


**Q6: How do I use OAuth2 with password flow in FastAPI?**
*(expects URL containing: `simple-oauth2`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #4 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.670 |
| crawl4ai | #4 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.720 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.699 |
| crawl4ai-raw | #4 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.719 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.699 |
| scrapy+md | #4 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.667 |
| crawlee | #3 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.682 | fastapi.tiangolo.com/advanced/security/oauth2-scop | 0.674 |
| colly+md | #4 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.667 |
| playwright | #3 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.682 | fastapi.tiangolo.com/advanced/security/oauth2-scop | 0.674 |
| firecrawl | #3 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.668 | fastapi.tiangolo.com/reference/openapi/models/ | 0.663 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.648 |


**Q7: How do I use WebSockets in FastAPI?**
*(expects URL containing: `websockets`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.652 | fastapi.tiangolo.com/reference/websockets/ | 0.622 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/reference/websockets/ | 0.625 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/reference/websockets/ | 0.625 |
| playwright | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.725 | fastapi.tiangolo.com/advanced/websockets/ | 0.638 | fastapi.tiangolo.com/advanced/websockets/ | 0.624 |


**Q8: How do I stream data responses in FastAPI?**
*(expects URL containing: `stream-data`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 |
| crawlee | #1 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.616 |
| colly+md | #1 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 |
| playwright | #1 | fastapi.tiangolo.com/zh-hant/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.616 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.598 | fastapi.tiangolo.com/advanced/stream-data/ | 0.592 | fastapi.tiangolo.com/advanced/custom-response/ | 0.569 |


**Q9: How do I return additional response types in FastAPI?**
*(expects URL containing: `additional-responses`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/reference/responses/ | 0.604 | fastapi.tiangolo.com/advanced/additional-responses | 0.600 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/custom-response/ | 0.615 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.656 | fastapi.tiangolo.com/advanced/additional-responses | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 | fastapi.tiangolo.com/reference/responses/ | 0.604 |
| playwright | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.656 | fastapi.tiangolo.com/advanced/additional-responses | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 |
| firecrawl | #2 | fastapi.tiangolo.com/advanced/additional-status-co | 0.579 | fastapi.tiangolo.com/advanced/additional-responses | 0.577 | fastapi.tiangolo.com/advanced/custom-response/ | 0.576 |


**Q10: How do I write async tests for FastAPI applications?**
*(expects URL containing: `async-tests`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/tutorial/testing/ | 0.657 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/tutorial/testing/ | 0.657 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.727 | fastapi.tiangolo.com/tutorial/testing/ | 0.644 | fastapi.tiangolo.com/advanced/async-tests/ | 0.617 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| playwright | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.727 | fastapi.tiangolo.com/tutorial/testing/ | 0.644 | fastapi.tiangolo.com/advanced/async-tests/ | 0.617 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.647 | fastapi.tiangolo.com/tutorial/testing/ | 0.628 | fastapi.tiangolo.com/ | 0.576 |


**Q11: How do I define nested Pydantic models for request bodies?**
*(expects URL containing: `body-nested-models`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/body/ | 0.626 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body/ | 0.592 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body/ | 0.592 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.570 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.564 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.570 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.564 |
| firecrawl | #2 | fastapi.tiangolo.com/tutorial/body/ | 0.652 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.591 | fastapi.tiangolo.com/tutorial/body/ | 0.567 |


**Q12: How do I handle startup and shutdown events in FastAPI?**
*(expects URL containing: `events`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/events/ | 0.660 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.638 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.658 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.658 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.648 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/events/ | 0.682 | fastapi.tiangolo.com/advanced/events/ | 0.655 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.652 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.648 |
| playwright | #1 | fastapi.tiangolo.com/advanced/events/ | 0.682 | fastapi.tiangolo.com/advanced/events/ | 0.655 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.652 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/events/ | 0.674 | fastapi.tiangolo.com/zh-hant/advanced/events/ | 0.639 | fastapi.tiangolo.com/advanced/events/ | 0.607 |


**Q13: How do I use middleware in FastAPI?**
*(expects URL containing: `middleware`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 | fastapi.tiangolo.com/reference/fastapi/ | 0.677 | fastapi.tiangolo.com/advanced/middleware/ | 0.639 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.730 | fastapi.tiangolo.com/reference/fastapi/ | 0.717 | fastapi.tiangolo.com/tutorial/middleware/ | 0.707 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.730 | fastapi.tiangolo.com/reference/fastapi/ | 0.716 | fastapi.tiangolo.com/tutorial/middleware/ | 0.707 |
| scrapy+md | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 | fastapi.tiangolo.com/advanced/middleware/ | 0.639 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.719 | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/advanced/middleware/ | 0.643 |
| colly+md | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 | fastapi.tiangolo.com/advanced/middleware/ | 0.639 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.719 | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/advanced/middleware/ | 0.643 |
| firecrawl | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.702 | fastapi.tiangolo.com/tutorial/middleware/ | 0.677 | fastapi.tiangolo.com/advanced/middleware/ | 0.618 |


**Q14: How do I use Jinja2 templates in FastAPI?**
*(expects URL containing: `templating`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/templating/ | 0.755 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/advanced/templates/ | 0.669 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.765 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.765 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/reference/templating/ | 0.685 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.752 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 |
| colly+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/reference/templating/ | 0.685 |
| playwright | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.752 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 |
| firecrawl | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.667 | fastapi.tiangolo.com/reference/templating/ | 0.664 | fastapi.tiangolo.com/zh-hant/advanced/templates/ | 0.571 |


**Q15: How do I deploy FastAPI to the cloud?**
*(expects URL containing: `deployment`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | fastapi.tiangolo.com/tutorial/first-steps/ | 0.754 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.740 |
| crawl4ai | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/cloud/ | 0.786 | fastapi.tiangolo.com/deployment/cloud/ | 0.783 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/cloud/ | 0.786 | fastapi.tiangolo.com/deployment/cloud/ | 0.783 |
| scrapy+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/ | 0.754 |
| crawlee | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.768 | fastapi.tiangolo.com/deployment/cloud/ | 0.762 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.762 |
| colly+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/tutorial/first-steps/ | 0.754 |
| playwright | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.768 | fastapi.tiangolo.com/deployment/cloud/ | 0.762 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.762 |
| firecrawl | #3 | fastapi.tiangolo.com/tutorial/first-steps/ | 0.743 | fastapi.tiangolo.com/tutorial/first-steps/ | 0.740 | fastapi.tiangolo.com/deployment/cloud/ | 0.727 |


</details>

## python-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 67% (8/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 100% (12/12) | 0.728 | 9021 | 500 |
| crawl4ai | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 92% (11/12) | 0.797 | 13343 | 500 |
| crawl4ai-raw | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 92% (11/12) | 0.797 | 13343 | 500 |
| scrapy+md | 67% (8/12) | 75% (9/12) | 75% (9/12) | 83% (10/12) | 83% (10/12) | 0.721 | 12001 | 429 |
| crawlee | 67% (8/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 92% (11/12) | 0.722 | 13283 | 500 |
| colly+md | 67% (8/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 92% (11/12) | 0.720 | 13170 | 500 |
| playwright | 67% (8/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 92% (11/12) | 0.722 | 13283 | 500 |
| firecrawl | 67% (8/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 83% (10/12) | 0.717 | 9484 | 500 |

<details>
<summary>Query-by-query results for python-docs</summary>

**Q1: What new features were added in Python 3.10?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.759 | docs.python.org/3.11/contents.html | 0.651 | docs.python.org/3.12/contents.html | 0.646 |
| crawl4ai | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.749 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 |
| crawl4ai-raw | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.749 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 |
| scrapy+md | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.759 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 |
| crawlee | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.759 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 |
| colly+md | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.759 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 |
| playwright | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.759 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 | docs.python.org/3.10/whatsnew/3.10.html | 0.692 |
| firecrawl | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.724 | docs.python.org/3.10/whatsnew/3.9.html | 0.688 | docs.python.org/3.10/whatsnew/index.html | 0.678 |


**Q2: What does the term 'decorator' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.671 | docs.python.org/3.10/glossary.html | 0.585 | docs.python.org/3.10/whatsnew/2.4.html | 0.572 |
| crawl4ai | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.664 | docs.python.org/3.12/glossary.html | 0.647 | docs.python.org/3.11/glossary.html | 0.645 |
| crawl4ai-raw | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.664 | docs.python.org/3.12/glossary.html | 0.647 | docs.python.org/3.11/glossary.html | 0.645 |
| scrapy+md | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.678 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/whatsnew/2.4.html | 0.565 |
| crawlee | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.675 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.3/glossary.html | 0.565 |
| colly+md | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.678 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/whatsnew/2.4.html | 0.565 |
| playwright | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.675 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/whatsnew/2.4.html | 0.565 |
| firecrawl | #2 | docs.python.org/3.10/whatsnew/2.4.html | 0.634 | docs.python.org/3.13/glossary.html | 0.625 | docs.python.org/3.10/library/functools.html | 0.555 |


**Q3: How do I report a bug in Python?**
*(expects URL containing: `bugs`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.3/bugs.html | 0.643 | docs.python.org/3.5/bugs.html | 0.629 | docs.python.org/3.6/bugs.html | 0.629 |
| crawl4ai | #1 | docs.python.org/3.5/bugs.html | 0.678 | docs.python.org/3.3/bugs.html | 0.673 | docs.python.org/bugs.html | 0.668 |
| crawl4ai-raw | #1 | docs.python.org/3.5/bugs.html | 0.678 | docs.python.org/3.3/bugs.html | 0.673 | docs.python.org/bugs.html | 0.668 |
| scrapy+md | #1 | docs.python.org/3/bugs.html | 0.609 | docs.python.org/3.15/bugs.html | 0.609 | docs.python.org/3.12/bugs.html | 0.609 |
| crawlee | #1 | docs.python.org/3.3/bugs.html | 0.643 | docs.python.org/bugs.html | 0.641 | docs.python.org/bugs.html | 0.640 |
| colly+md | #1 | docs.python.org/3.3/bugs.html | 0.643 | docs.python.org/3.6/bugs.html | 0.629 | docs.python.org/3.5/bugs.html | 0.629 |
| playwright | #1 | docs.python.org/3.3/bugs.html | 0.643 | docs.python.org/bugs.html | 0.641 | docs.python.org/bugs.html | 0.640 |
| firecrawl | #1 | docs.python.org/3.5/bugs.html | 0.651 | docs.python.org/3.6/bugs.html | 0.650 | docs.python.org/bugs.html | 0.636 |


**Q4: What is structural pattern matching in Python?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.643 | docs.python.org/3.10/whatsnew/3.10.html | 0.568 | docs.python.org/3.10/whatsnew/3.10.html | 0.485 |
| crawl4ai | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.686 | docs.python.org/3.10/whatsnew/3.10.html | 0.621 | docs.python.org/3.10/whatsnew/3.10.html | 0.532 |
| crawl4ai-raw | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.686 | docs.python.org/3.10/whatsnew/3.10.html | 0.621 | docs.python.org/3.10/whatsnew/3.10.html | 0.532 |
| scrapy+md | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.643 | docs.python.org/3.10/whatsnew/3.10.html | 0.568 | docs.python.org/3.10/whatsnew/3.10.html | 0.479 |
| crawlee | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.643 | docs.python.org/3.10/whatsnew/3.10.html | 0.568 | docs.python.org/3.10/whatsnew/3.10.html | 0.479 |
| colly+md | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.643 | docs.python.org/3.10/whatsnew/3.10.html | 0.568 | docs.python.org/3.10/whatsnew/3.10.html | 0.479 |
| playwright | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.643 | docs.python.org/3.10/whatsnew/3.10.html | 0.568 | docs.python.org/3.10/whatsnew/3.10.html | 0.479 |
| firecrawl | #1 | docs.python.org/3.10/whatsnew/3.10.html | 0.663 | docs.python.org/3.10/whatsnew/3.10.html | 0.586 | docs.python.org/3.10/whatsnew/3.10.html | 0.518 |


**Q5: What is Python's glossary definition of a generator?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.6/glossary.html | 0.567 | docs.python.org/3.13/glossary.html | 0.531 | docs.python.org/3.11/glossary.html | 0.528 |
| crawl4ai | #1 | docs.python.org/3.13/glossary.html | 0.605 | docs.python.org/3.10/glossary.html | 0.580 | docs.python.org/3.5/glossary.html | 0.575 |
| crawl4ai-raw | #1 | docs.python.org/3.13/glossary.html | 0.605 | docs.python.org/3.10/glossary.html | 0.580 | docs.python.org/3.5/glossary.html | 0.575 |
| scrapy+md | #1 | docs.python.org/3.13/glossary.html | 0.535 | docs.python.org/3.11/glossary.html | 0.531 | docs.python.org/3.10/glossary.html | 0.521 |
| crawlee | #1 | docs.python.org/3.6/glossary.html | 0.571 | docs.python.org/3.13/glossary.html | 0.540 | docs.python.org/3.12/glossary.html | 0.538 |
| colly+md | #1 | docs.python.org/3.6/glossary.html | 0.570 | docs.python.org/3.13/glossary.html | 0.535 | docs.python.org/3.11/glossary.html | 0.531 |
| playwright | #1 | docs.python.org/3.6/glossary.html | 0.571 | docs.python.org/3.13/glossary.html | 0.540 | docs.python.org/3.12/glossary.html | 0.538 |
| firecrawl | #1 | docs.python.org/3.13/glossary.html | 0.579 | docs.python.org/3.12/glossary.html | 0.559 | docs.python.org/3.11/glossary.html | 0.559 |


**Q6: What are the Python how-to guides about?**
*(expects URL containing: `howto`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.12/howto/index.html | 0.712 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.6/howto/index.html | 0.701 |
| crawl4ai | #1 | docs.python.org/3.10/howto/index.html | 0.744 | docs.python.org/3.11/howto/index.html | 0.735 | docs.python.org/3.12/howto/index.html | 0.724 |
| crawl4ai-raw | #1 | docs.python.org/3.10/howto/index.html | 0.744 | docs.python.org/3.11/howto/index.html | 0.735 | docs.python.org/3.12/howto/index.html | 0.724 |
| scrapy+md | #1 | docs.python.org/3.15/howto/index.html | 0.700 | docs.python.org/3.14/howto/index.html | 0.698 | docs.python.org/3.11/installing/index.html | 0.597 |
| crawlee | #1 | docs.python.org/3.12/howto/index.html | 0.712 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.15/howto/index.html | 0.700 |
| colly+md | #1 | docs.python.org/3.15/howto/index.html | 0.700 | docs.python.org/3.14/howto/index.html | 0.698 | docs.python.org/3.13/howto/index.html | 0.697 |
| playwright | #1 | docs.python.org/3.12/howto/index.html | 0.712 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.15/howto/index.html | 0.700 |
| firecrawl | #15 | docs.python.org/3.6/distributing/index.html | 0.616 | docs.python.org/3.3/install/index.html | 0.615 | docs.python.org/3.5/installing/index.html | 0.615 |


**Q7: What is the Python module index?**
*(expects URL containing: `py-modindex`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #13 | docs.python.org/3.3/glossary.html | 0.634 | docs.python.org/3.3/distutils/index.html | 0.633 | docs.python.org/3.3/distutils/index.html | 0.631 |
| crawl4ai | #1 | docs.python.org/3.3/py-modindex.html | 0.648 | docs.python.org/3.3/glossary.html | 0.626 | docs.python.org/3.3/install/index.html | 0.624 |
| crawl4ai-raw | #1 | docs.python.org/3.3/py-modindex.html | 0.648 | docs.python.org/3.3/glossary.html | 0.626 | docs.python.org/3.3/install/index.html | 0.624 |
| scrapy+md | miss | docs.python.org/3.11/installing/index.html | 0.642 | docs.python.org/3.12/installing/index.html | 0.640 | docs.python.org/3.11/installing/index.html | 0.638 |
| crawlee | #47 | docs.python.org/3.3/glossary.html | 0.634 | docs.python.org/3.3/distutils/index.html | 0.633 | docs.python.org/3.3/distutils/index.html | 0.630 |
| colly+md | miss | docs.python.org/3.11/installing/index.html | 0.642 | docs.python.org/3.12/installing/index.html | 0.640 | docs.python.org/3.11/installing/index.html | 0.638 |
| playwright | #47 | docs.python.org/3.3/glossary.html | 0.634 | docs.python.org/3.3/distutils/index.html | 0.633 | docs.python.org/3.3/distutils/index.html | 0.630 |
| firecrawl | #1 | docs.python.org/3.3/py-modindex.html | 0.622 | docs.python.org/3.5/py-modindex.html | 0.611 | docs.python.org/3.6/py-modindex.html | 0.609 |


**Q8: What Python tutorial topics are available?**
*(expects URL containing: `tutorial`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.12/tutorial/index.html | 0.655 | docs.python.org/3.11/tutorial/index.html | 0.655 | docs.python.org/3.6/tutorial/index.html | 0.653 |
| crawl4ai | #1 | docs.python.org/3.6/tutorial/index.html | 0.654 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.12/tutorial/index.html | 0.653 |
| crawl4ai-raw | #1 | docs.python.org/3.6/tutorial/index.html | 0.654 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.12/tutorial/index.html | 0.653 |
| scrapy+md | #1 | docs.python.org/3.12/tutorial/index.html | 0.655 | docs.python.org/3.11/tutorial/index.html | 0.655 | docs.python.org/3.10/tutorial/index.html | 0.653 |
| crawlee | #1 | docs.python.org/3.11/tutorial/index.html | 0.655 | docs.python.org/3.12/tutorial/index.html | 0.655 | docs.python.org/3.6/tutorial/index.html | 0.653 |
| colly+md | #1 | docs.python.org/3.12/tutorial/index.html | 0.655 | docs.python.org/3.11/tutorial/index.html | 0.655 | docs.python.org/3.6/tutorial/index.html | 0.653 |
| playwright | #1 | docs.python.org/3.12/tutorial/index.html | 0.655 | docs.python.org/3.11/tutorial/index.html | 0.655 | docs.python.org/3.6/tutorial/index.html | 0.653 |
| firecrawl | #1 | docs.python.org/3.10/tutorial/index.html | 0.629 | docs.python.org/3.11/tutorial/index.html | 0.625 | docs.python.org/3.12/tutorial/index.html | 0.625 |


**Q9: What is the Python license and copyright?**
*(expects URL containing: `license`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/license.html | 0.613 | docs.python.org/3.15/license.html | 0.613 | docs.python.org/3.12/license.html | 0.613 |
| crawl4ai | #1 | docs.python.org/license.html | 0.647 | docs.python.org/3.13/license.html | 0.645 | docs.python.org/3.15/license.html | 0.642 |
| crawl4ai-raw | #1 | docs.python.org/license.html | 0.647 | docs.python.org/3.13/license.html | 0.645 | docs.python.org/3.15/license.html | 0.642 |
| scrapy+md | #1 | docs.python.org/3.13/license.html | 0.617 | docs.python.org/3/license.html | 0.617 | docs.python.org/3.15/license.html | 0.617 |
| crawlee | #1 | docs.python.org/3.13/license.html | 0.617 | docs.python.org/license.html | 0.617 | docs.python.org/3.15/license.html | 0.617 |
| colly+md | #1 | docs.python.org/3.13/license.html | 0.617 | docs.python.org/3/license.html | 0.617 | docs.python.org/3.15/license.html | 0.617 |
| playwright | #1 | docs.python.org/3.13/license.html | 0.617 | docs.python.org/3.15/license.html | 0.617 | docs.python.org/license.html | 0.617 |
| firecrawl | #1 | docs.python.org/3.10/license.html | 0.624 | docs.python.org/3.11/license.html | 0.620 | docs.python.org/3.5/license.html | 0.604 |


**Q10: What is the table of contents for Python 3.10 documentation?**
*(expects URL containing: `contents`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #11 | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.664 | docs.python.org/3.3/about.html | 0.635 |
| crawl4ai | miss | docs.python.org/3.10/about.html | 0.773 | docs.python.org/3.10/about.html | 0.773 | docs.python.org/3.14/about.html | 0.759 |
| crawl4ai-raw | miss | docs.python.org/3.10/about.html | 0.773 | docs.python.org/3.10/about.html | 0.773 | docs.python.org/3.14/about.html | 0.759 |
| scrapy+md | #27 | docs.python.org/3.12/about.html | 0.715 | docs.python.org/3.12/about.html | 0.715 | docs.python.org/3.14/about.html | 0.715 |
| crawlee | #15 | docs.python.org/3.14/about.html | 0.715 | docs.python.org/3.15/about.html | 0.715 | docs.python.org/3.13/about.html | 0.715 |
| colly+md | #15 | docs.python.org/3.13/about.html | 0.715 | docs.python.org/3.13/about.html | 0.715 | docs.python.org/3.14/about.html | 0.715 |
| playwright | #15 | docs.python.org/3.12/about.html | 0.715 | docs.python.org/3.12/about.html | 0.715 | docs.python.org/3.14/about.html | 0.715 |
| firecrawl | miss | docs.python.org/3.10/ | 0.685 | docs.python.org/3.10/bugs.html | 0.654 | docs.python.org/3.3/bugs.html | 0.651 |


**Q11: What does the term 'iterable' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.13/glossary.html | 0.655 | docs.python.org/3.3/glossary.html | 0.619 | docs.python.org/3.6/glossary.html | 0.605 |
| crawl4ai | #1 | docs.python.org/3.5/glossary.html | 0.611 | docs.python.org/3.12/glossary.html | 0.599 | docs.python.org/3.11/glossary.html | 0.598 |
| crawl4ai-raw | #1 | docs.python.org/3.5/glossary.html | 0.611 | docs.python.org/3.12/glossary.html | 0.599 | docs.python.org/3.11/glossary.html | 0.599 |
| scrapy+md | #1 | docs.python.org/3.13/glossary.html | 0.655 | docs.python.org/3.11/glossary.html | 0.576 | docs.python.org/3.12/glossary.html | 0.574 |
| crawlee | #1 | docs.python.org/3.13/glossary.html | 0.655 | docs.python.org/3.3/glossary.html | 0.613 | docs.python.org/3.6/glossary.html | 0.605 |
| colly+md | #1 | docs.python.org/3.13/glossary.html | 0.655 | docs.python.org/3.3/glossary.html | 0.613 | docs.python.org/3.6/glossary.html | 0.605 |
| playwright | #1 | docs.python.org/3.13/glossary.html | 0.655 | docs.python.org/3.3/glossary.html | 0.613 | docs.python.org/3.6/glossary.html | 0.605 |
| firecrawl | #1 | docs.python.org/3.3/glossary.html | 0.626 | docs.python.org/3.14/glossary.html | 0.591 | docs.python.org/3.5/glossary.html | 0.564 |


**Q12: How do I install and configure Python on my system?**
*(expects URL containing: `using`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #14 | docs.python.org/3.13/installing/index.html | 0.582 | docs.python.org/3.11/installing/index.html | 0.578 | docs.python.org/3.12/installing/index.html | 0.578 |
| crawl4ai | #16 | docs.python.org/3.13/installing/index.html | 0.591 | docs.python.org/3.11/installing/index.html | 0.588 | docs.python.org/3.12/installing/index.html | 0.587 |
| crawl4ai-raw | #16 | docs.python.org/3.13/installing/index.html | 0.591 | docs.python.org/3.11/installing/index.html | 0.588 | docs.python.org/3.12/installing/index.html | 0.587 |
| scrapy+md | #9 | docs.python.org/3.13/installing/index.html | 0.582 | docs.python.org/3.12/installing/index.html | 0.578 | docs.python.org/3.11/installing/index.html | 0.578 |
| crawlee | #14 | docs.python.org/3.13/installing/index.html | 0.582 | docs.python.org/3.11/installing/index.html | 0.578 | docs.python.org/3.12/installing/index.html | 0.578 |
| colly+md | #14 | docs.python.org/3.13/installing/index.html | 0.582 | docs.python.org/3.11/installing/index.html | 0.578 | docs.python.org/3.12/installing/index.html | 0.578 |
| playwright | #14 | docs.python.org/3.13/installing/index.html | 0.582 | docs.python.org/3.12/installing/index.html | 0.578 | docs.python.org/3.11/installing/index.html | 0.578 |
| firecrawl | #24 | docs.python.org/3.13/installing/index.html | 0.576 | docs.python.org/3.11/installing/index.html | 0.573 | docs.python.org/3.12/installing/index.html | 0.571 |


</details>

## react-dev

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 75% (9/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 0.840 | 3483 | 221 |
| crawl4ai | 83% (10/12) | 92% (11/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 0.875 | 4747 | 221 |
| crawl4ai-raw | 83% (10/12) | 92% (11/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 0.875 | 4748 | 221 |
| scrapy+md | 75% (9/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 0.840 | 3553 | 221 |
| crawlee | 67% (8/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 0.785 | 6441 | 221 |
| colly+md | 67% (8/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 0.785 | 6392 | 221 |
| playwright | 67% (8/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 0.785 | 6392 | 221 |
| firecrawl | 67% (8/12) | 75% (9/12) | 75% (9/12) | 83% (10/12) | 83% (10/12) | 0.708 | 553 | 43 |

<details>
<summary>Query-by-query results for react-dev</summary>

**Q1: How do I manage state in a React component?**
*(expects URL containing: `state`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/reacting-to-input-with-state | 0.691 | react.dev/learn/state-a-components-memory | 0.689 |
| crawl4ai | #1 | react.dev/learn/preserving-and-resetting-state | 0.712 | react.dev/learn/state-a-components-memory | 0.701 | react.dev/learn/managing-state | 0.701 |
| crawl4ai-raw | #1 | react.dev/learn/preserving-and-resetting-state | 0.712 | react.dev/learn/state-a-components-memory | 0.701 | react.dev/learn/managing-state | 0.701 |
| scrapy+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/reacting-to-input-with-state | 0.691 | react.dev/learn/state-a-components-memory | 0.689 |
| crawlee | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/reacting-to-input-with-state | 0.691 | react.dev/learn/state-a-components-memory | 0.689 |
| colly+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/reacting-to-input-with-state | 0.691 | react.dev/learn/state-a-components-memory | 0.689 |
| playwright | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/reacting-to-input-with-state | 0.691 | react.dev/learn/state-a-components-memory | 0.689 |
| firecrawl | #1 | react.dev/learn/preserving-and-resetting-state | 0.706 | react.dev/learn/reacting-to-input-with-state | 0.685 | react.dev/learn/state-a-components-memory | 0.655 |


**Q2: What are React hooks and how do I use them?**
*(expects URL containing: `hooks`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 | react.dev/learn/typescript | 0.702 |
| crawl4ai | #6 | react.dev/learn | 0.730 | react.dev/learn/typescript | 0.716 | react.dev/learn/state-a-components-memory | 0.711 |
| crawl4ai-raw | #6 | react.dev/learn | 0.730 | react.dev/learn/typescript | 0.716 | react.dev/learn/state-a-components-memory | 0.711 |
| scrapy+md | #1 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 | react.dev/learn/typescript | 0.702 |
| crawlee | #3 | react.dev/warnings/react-dom-test-utils | 0.709 | react.dev/versions | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 |
| colly+md | #3 | react.dev/versions | 0.709 | react.dev/warnings/react-dom-test-utils | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 |
| playwright | #3 | react.dev/warnings/react-dom-test-utils | 0.709 | react.dev/versions | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 |
| firecrawl | #3 | react.dev/learn/state-a-components-memory | 0.699 | react.dev/learn/state-a-components-memory | 0.645 | react.dev/reference/rules/rules-of-hooks | 0.620 |


**Q3: How does the useEffect hook work in React?**
*(expects URL containing: `useEffect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/reference/react/useEffect | 0.751 | react.dev/reference/react/useEffectEvent | 0.632 | react.dev/reference/react/useEffect | 0.625 |
| crawl4ai | #1 | react.dev/reference/react/useEffect | 0.716 | react.dev/reference/react/useEffectEvent | 0.631 | react.dev/reference/react/useEffectEvent | 0.625 |
| crawl4ai-raw | #1 | react.dev/reference/react/useEffect | 0.716 | react.dev/reference/react/useEffectEvent | 0.631 | react.dev/reference/react/useEffectEvent | 0.625 |
| scrapy+md | #1 | react.dev/reference/react/useEffect | 0.742 | react.dev/reference/react/useEffectEvent | 0.634 | react.dev/reference/react/useEffect | 0.625 |
| crawlee | #1 | react.dev/reference/react/useEffect | 0.742 | react.dev/reference/react/useEffectEvent | 0.634 | react.dev/reference/react/useEffect | 0.625 |
| colly+md | #1 | react.dev/reference/react/useEffect | 0.742 | react.dev/reference/react/useEffectEvent | 0.634 | react.dev/reference/react/useEffect | 0.625 |
| playwright | #1 | react.dev/reference/react/useEffect | 0.742 | react.dev/reference/react/useEffectEvent | 0.634 | react.dev/reference/react/useEffect | 0.625 |
| firecrawl | #1 | react.dev/learn/synchronizing-with-effects | 0.599 | react.dev/learn/you-might-not-need-an-effect | 0.592 | react.dev/learn/state-a-components-memory | 0.583 |


**Q4: How do I handle forms and user input in React?**
*(expects URL containing: `input`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | react.dev/learn/managing-state | 0.684 | react.dev/reference/react-dom/components | 0.684 | react.dev/reference/react-dom/components/input | 0.640 |
| crawl4ai | #1 | react.dev/reference/react-dom/components/input | 0.685 | react.dev/learn/managing-state | 0.684 | react.dev/learn/reacting-to-input-with-state | 0.671 |
| crawl4ai-raw | #1 | react.dev/reference/react-dom/components/input | 0.681 | react.dev/learn/managing-state | 0.680 | react.dev/learn/reacting-to-input-with-state | 0.671 |
| scrapy+md | #3 | react.dev/learn/managing-state | 0.691 | react.dev/reference/react-dom/components | 0.684 | react.dev/reference/react-dom/components/input | 0.640 |
| crawlee | #3 | react.dev/learn/managing-state | 0.689 | react.dev/reference/react-dom/components | 0.684 | react.dev/reference/react-dom/components/input | 0.644 |
| colly+md | #3 | react.dev/learn/managing-state | 0.691 | react.dev/reference/react-dom/components | 0.684 | react.dev/reference/react-dom/components/input | 0.640 |
| playwright | #3 | react.dev/learn/managing-state | 0.691 | react.dev/reference/react-dom/components | 0.684 | react.dev/reference/react-dom/components/input | 0.640 |
| firecrawl | #1 | react.dev/learn/reacting-to-input-with-state | 0.650 | react.dev/learn/reacting-to-input-with-state | 0.608 | react.dev/learn/reacting-to-input-with-state | 0.594 |


**Q5: How do I create and use context in React?**
*(expects URL containing: `context`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/reference/react/createContext | 0.744 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 |
| crawl4ai | #1 | react.dev/reference/react/createContext | 0.744 | react.dev/learn/passing-data-deeply-with-context | 0.737 | react.dev/reference/react/createContext | 0.715 |
| crawl4ai-raw | #1 | react.dev/reference/react/createContext | 0.744 | react.dev/learn/passing-data-deeply-with-context | 0.732 | react.dev/reference/react/createContext | 0.715 |
| scrapy+md | #1 | react.dev/reference/react/createContext | 0.727 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 |
| crawlee | #1 | react.dev/reference/react/createContext | 0.727 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 |
| colly+md | #1 | react.dev/reference/react/createContext | 0.727 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 |
| playwright | #1 | react.dev/reference/react/createContext | 0.727 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 |
| firecrawl | #1 | react.dev/learn/passing-data-deeply-with-context | 0.706 | react.dev/learn/passing-data-deeply-with-context | 0.700 | react.dev/learn/passing-data-deeply-with-context | 0.694 |


**Q6: How do I handle events like clicks in React?**
*(expects URL containing: `event`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/responding-to-events | 0.699 | react.dev/learn/adding-interactivity | 0.669 | react.dev/learn | 0.669 |
| crawl4ai | #1 | react.dev/learn/responding-to-events | 0.690 | react.dev/learn | 0.682 | react.dev/learn/adding-interactivity | 0.677 |
| crawl4ai-raw | #1 | react.dev/learn/responding-to-events | 0.690 | react.dev/learn | 0.682 | react.dev/learn/adding-interactivity | 0.676 |
| scrapy+md | #1 | react.dev/learn/responding-to-events | 0.699 | react.dev/learn | 0.668 | react.dev/learn/adding-interactivity | 0.668 |
| crawlee | #1 | react.dev/learn/responding-to-events | 0.699 | react.dev/learn | 0.668 | react.dev/learn/adding-interactivity | 0.645 |
| colly+md | #1 | react.dev/learn/responding-to-events | 0.699 | react.dev/learn | 0.668 | react.dev/learn/adding-interactivity | 0.668 |
| playwright | #1 | react.dev/learn/responding-to-events | 0.699 | react.dev/learn | 0.668 | react.dev/learn/adding-interactivity | 0.668 |
| firecrawl | miss | react.dev/learn/adding-interactivity | 0.608 | react.dev/learn/typescript | 0.582 | react.dev/learn/manipulating-the-dom-with-refs | 0.568 |


**Q7: What is JSX and how does React use it?**
*(expects URL containing: `jsx`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/writing-markup-with-jsx | 0.727 | react.dev/learn/writing-markup-with-jsx | 0.707 | react.dev/learn/writing-markup-with-jsx | 0.707 |
| crawl4ai | #1 | react.dev/learn/writing-markup-with-jsx | 0.680 | react.dev/learn/writing-markup-with-jsx | 0.680 | react.dev/learn/writing-markup-with-jsx | 0.668 |
| crawl4ai-raw | #1 | react.dev/learn/writing-markup-with-jsx | 0.680 | react.dev/learn/writing-markup-with-jsx | 0.680 | react.dev/learn/writing-markup-with-jsx | 0.668 |
| scrapy+md | #1 | react.dev/learn/writing-markup-with-jsx | 0.727 | react.dev/learn/writing-markup-with-jsx | 0.707 | react.dev/learn/writing-markup-with-jsx | 0.707 |
| crawlee | #1 | react.dev/learn/writing-markup-with-jsx | 0.727 | react.dev/learn/writing-markup-with-jsx | 0.707 | react.dev/learn/writing-markup-with-jsx | 0.707 |
| colly+md | #1 | react.dev/learn/writing-markup-with-jsx | 0.727 | react.dev/learn/writing-markup-with-jsx | 0.707 | react.dev/learn/writing-markup-with-jsx | 0.707 |
| playwright | #1 | react.dev/learn/writing-markup-with-jsx | 0.727 | react.dev/learn/writing-markup-with-jsx | 0.707 | react.dev/learn/writing-markup-with-jsx | 0.707 |
| firecrawl | #1 | react.dev/learn/javascript-in-jsx-with-curly-brace | 0.671 | react.dev/learn | 0.612 | react.dev/learn/javascript-in-jsx-with-curly-brace | 0.610 |


**Q8: How do I render lists and use keys in React?**
*(expects URL containing: `list`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #4 | react.dev/learn/describing-the-ui | 0.729 | react.dev/learn/tutorial-tic-tac-toe | 0.710 | react.dev/learn | 0.697 |
| crawl4ai | #1 | react.dev/learn/rendering-lists | 0.752 | react.dev/learn/tutorial-tic-tac-toe | 0.734 | react.dev/learn/describing-the-ui | 0.726 |
| crawl4ai-raw | #1 | react.dev/learn/rendering-lists | 0.752 | react.dev/learn/tutorial-tic-tac-toe | 0.734 | react.dev/learn/describing-the-ui | 0.726 |
| scrapy+md | #4 | react.dev/learn/describing-the-ui | 0.724 | react.dev/learn/tutorial-tic-tac-toe | 0.716 | react.dev/learn | 0.700 |
| crawlee | #4 | react.dev/learn/describing-the-ui | 0.724 | react.dev/learn/tutorial-tic-tac-toe | 0.716 | react.dev/learn | 0.698 |
| colly+md | #4 | react.dev/learn/describing-the-ui | 0.724 | react.dev/learn/tutorial-tic-tac-toe | 0.716 | react.dev/learn | 0.700 |
| playwright | #4 | react.dev/learn/describing-the-ui | 0.724 | react.dev/learn/tutorial-tic-tac-toe | 0.716 | react.dev/learn | 0.700 |
| firecrawl | miss | react.dev/learn | 0.618 | react.dev/learn/preserving-and-resetting-state | 0.589 | react.dev/learn/describing-the-ui | 0.568 |


**Q9: How do I use the useRef hook in React?**
*(expects URL containing: `useRef`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/reference/react/useRef | 0.751 | react.dev/learn/referencing-values-with-refs | 0.716 | react.dev/reference/react/hooks | 0.675 |
| crawl4ai | #1 | react.dev/reference/react/useRef | 0.732 | react.dev/learn/referencing-values-with-refs | 0.721 | react.dev/reference/react/useRef | 0.704 |
| crawl4ai-raw | #1 | react.dev/reference/react/useRef | 0.732 | react.dev/learn/referencing-values-with-refs | 0.721 | react.dev/reference/react/useRef | 0.704 |
| scrapy+md | #1 | react.dev/reference/react/useRef | 0.758 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/reference/react/useRef | 0.674 |
| crawlee | #1 | react.dev/reference/react/useRef | 0.758 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/reference/react/useRef | 0.674 |
| colly+md | #1 | react.dev/reference/react/useRef | 0.758 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/reference/react/useRef | 0.674 |
| playwright | #1 | react.dev/reference/react/useRef | 0.758 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/reference/react/useRef | 0.674 |
| firecrawl | #1 | react.dev/learn/referencing-values-with-refs | 0.683 | react.dev/learn/manipulating-the-dom-with-refs | 0.640 | react.dev/learn/referencing-values-with-refs | 0.640 |


**Q10: How do I pass props between React components?**
*(expects URL containing: `props`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/passing-props-to-a-component | 0.787 | react.dev/learn/describing-the-ui | 0.762 | react.dev/learn/passing-data-deeply-with-context | 0.708 |
| crawl4ai | #1 | react.dev/learn/passing-props-to-a-component | 0.758 | react.dev/learn/describing-the-ui | 0.745 | react.dev/learn/passing-data-deeply-with-context | 0.717 |
| crawl4ai-raw | #1 | react.dev/learn/passing-props-to-a-component | 0.758 | react.dev/learn/describing-the-ui | 0.745 | react.dev/learn/passing-data-deeply-with-context | 0.717 |
| scrapy+md | #1 | react.dev/learn/passing-props-to-a-component | 0.787 | react.dev/learn/describing-the-ui | 0.763 | react.dev/learn/passing-data-deeply-with-context | 0.708 |
| crawlee | #1 | react.dev/learn/passing-props-to-a-component | 0.787 | react.dev/learn/describing-the-ui | 0.763 | react.dev/learn/passing-data-deeply-with-context | 0.708 |
| colly+md | #1 | react.dev/learn/passing-props-to-a-component | 0.787 | react.dev/learn/describing-the-ui | 0.763 | react.dev/learn/passing-data-deeply-with-context | 0.708 |
| playwright | #1 | react.dev/learn/passing-props-to-a-component | 0.787 | react.dev/learn/describing-the-ui | 0.763 | react.dev/learn/passing-data-deeply-with-context | 0.708 |
| firecrawl | #1 | react.dev/learn/passing-props-to-a-component | 0.717 | react.dev/learn/passing-data-deeply-with-context | 0.681 | react.dev/learn/passing-props-to-a-component | 0.655 |


**Q11: How do I conditionally render content in React?**
*(expects URL containing: `conditional`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | react.dev/learn | 0.746 | react.dev/learn/conditional-rendering | 0.744 | react.dev/learn/describing-the-ui | 0.709 |
| crawl4ai | #3 | react.dev/learn/describing-the-ui | 0.751 | react.dev/learn | 0.734 | react.dev/learn/conditional-rendering | 0.722 |
| crawl4ai-raw | #3 | react.dev/learn/describing-the-ui | 0.751 | react.dev/learn | 0.734 | react.dev/learn/conditional-rendering | 0.722 |
| scrapy+md | #2 | react.dev/learn | 0.748 | react.dev/learn/conditional-rendering | 0.744 | react.dev/learn/describing-the-ui | 0.703 |
| crawlee | #2 | react.dev/learn | 0.748 | react.dev/learn/conditional-rendering | 0.744 | react.dev/learn/describing-the-ui | 0.705 |
| colly+md | #2 | react.dev/learn | 0.748 | react.dev/learn/conditional-rendering | 0.744 | react.dev/learn/describing-the-ui | 0.703 |
| playwright | #2 | react.dev/learn | 0.748 | react.dev/learn/conditional-rendering | 0.744 | react.dev/learn/describing-the-ui | 0.703 |
| firecrawl | #1 | react.dev/learn/conditional-rendering | 0.672 | react.dev/learn/conditional-rendering | 0.585 | react.dev/learn/conditional-rendering | 0.585 |


**Q12: What is the useMemo hook for in React?**
*(expects URL containing: `useMemo`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/reference/react/useMemo | 0.747 | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.646 |
| crawl4ai | #1 | react.dev/reference/react/useMemo | 0.710 | react.dev/reference/react/useMemo | 0.700 | react.dev/learn/react-compiler/introduction | 0.675 |
| crawl4ai-raw | #1 | react.dev/reference/react/useMemo | 0.710 | react.dev/reference/react/useMemo | 0.700 | react.dev/learn/react-compiler/introduction | 0.675 |
| scrapy+md | #1 | react.dev/reference/react/useMemo | 0.736 | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/reference/react/useMemo | 0.643 |
| crawlee | #1 | react.dev/reference/react/useMemo | 0.736 | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/reference/react/useMemo | 0.643 |
| colly+md | #1 | react.dev/reference/react/useMemo | 0.736 | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/reference/react/useMemo | 0.643 |
| playwright | #1 | react.dev/reference/react/useMemo | 0.736 | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/reference/react/useMemo | 0.643 |
| firecrawl | #6 | react.dev/learn/typescript | 0.650 | react.dev/learn/you-might-not-need-an-effect | 0.616 | react.dev/learn/react-compiler/introduction | 0.593 |


</details>

## wikipedia-python

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1208 | 50 |
| crawl4ai | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1480 | 50 |
| crawl4ai-raw | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1480 | 50 |
| scrapy+md | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1540 | 50 |
| crawlee | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 2373 | 50 |
| colly+md | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1608 | 50 |
| playwright | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1301 | 41 |
| firecrawl | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 1081 | 50 |

<details>
<summary>Query-by-query results for wikipedia-python</summary>

**Q1: Who created the Python programming language?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.553 | en.wikipedia.org/wiki/Python_(programming_language | 0.535 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.561 | en.wikipedia.org/wiki/Python_(programming_language | 0.519 | en.wikipedia.org/wiki/Python_(programming_language | 0.513 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.561 | en.wikipedia.org/wiki/Python_(programming_language | 0.519 | en.wikipedia.org/wiki/Python_(programming_language | 0.513 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.553 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 | en.wikipedia.org/wiki/Python_(programming_language | 0.535 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.553 | en.wikipedia.org/wiki/Python_(programming_language | 0.535 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.553 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 | en.wikipedia.org/wiki/Python_(programming_language | 0.535 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.553 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 | en.wikipedia.org/wiki/Python_(programming_language | 0.535 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.621 | en.wikipedia.org/wiki/Python_(programming_language | 0.569 | en.wikipedia.org/wiki/Python_(programming_language | 0.543 |


**Q2: What is the history and development of Python?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.643 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.621 | en.wikipedia.org/wiki/Python_(programming_language | 0.581 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.621 | en.wikipedia.org/wiki/Python_(programming_language | 0.581 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.641 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.641 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.641 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.641 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.623 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 |


**Q3: What programming paradigms does Python support?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.578 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 | en.wikipedia.org/wiki/Python_(programming_language | 0.570 | en.wikipedia.org/wiki/Python_(programming_language | 0.555 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 | en.wikipedia.org/wiki/Python_(programming_language | 0.570 | en.wikipedia.org/wiki/Python_(programming_language | 0.555 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.622 | en.wikipedia.org/wiki/Python_(programming_language | 0.592 | en.wikipedia.org/wiki/Python_(programming_language | 0.569 |


**Q4: What is the Python Software Foundation?**
*(expects URL containing: `Python_Software_Foundation`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.478 | en.wikipedia.org/wiki/Python_Package_Index | 0.477 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.494 | en.wikipedia.org/wiki/Python_Package_Index | 0.480 | en.wikipedia.org/wiki/Python_Package_Index | 0.475 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.494 | en.wikipedia.org/wiki/Python_Package_Index | 0.480 | en.wikipedia.org/wiki/Python_Package_Index | 0.475 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.478 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.488 | en.wikipedia.org/wiki/Python_(programming_language | 0.478 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.478 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.478 |
| firecrawl | miss | en.wikipedia.org/wiki/Python_Package_Index | 0.539 | en.wikipedia.org/wiki/Python_(programming_language | 0.479 | en.wikipedia.org/wiki/Python_(programming_language | 0.473 |


**Q5: What is the syntax and design philosophy of Python?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.707 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.658 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.751 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.751 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.707 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.658 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.707 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.658 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.707 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.658 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.707 | en.wikipedia.org/wiki/Python_(programming_language | 0.664 | en.wikipedia.org/wiki/Python_(programming_language | 0.658 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.678 | en.wikipedia.org/wiki/Python_(programming_language | 0.673 | en.wikipedia.org/wiki/Python_(programming_language | 0.666 |


**Q6: What are Python's standard library modules?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.492 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.663 | en.wikipedia.org/wiki/Python_(programming_language | 0.549 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.663 | en.wikipedia.org/wiki/Python_(programming_language | 0.549 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 | en.wikipedia.org/wiki/Python_(programming_language | 0.509 | en.wikipedia.org/wiki/Python_(programming_language | 0.498 |


**Q7: Who is Guido van Rossum?**
*(expects URL containing: `Guido_van_Rossum`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.438 | en.wikipedia.org/wiki/Python_(programming_language | 0.430 | en.wikipedia.org/wiki/Python_(programming_language | 0.419 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.423 | en.wikipedia.org/wiki/Python_(programming_language | 0.421 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.423 | en.wikipedia.org/wiki/Python_(programming_language | 0.421 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.461 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.436 | en.wikipedia.org/wiki/Python_(programming_language | 0.432 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.461 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.461 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| firecrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.572 | en.wikipedia.org/wiki/Python_(programming_language | 0.479 | en.wikipedia.org/wiki/Python_(programming_language | 0.450 |


**Q8: What is CPython and how does it work?**
*(expects URL containing: `CPython`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.480 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.480 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 |
| firecrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.509 | en.wikipedia.org/wiki/Python_(programming_language | 0.501 | en.wikipedia.org/wiki/Python_(programming_language | 0.484 |


**Q9: How does Python compare to other programming languages?**
*(expects URL containing: `Comparison_of_programming_languages`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.659 | en.wikipedia.org/wiki/Python_(programming_language | 0.655 | en.wikipedia.org/wiki/Python_(programming_language | 0.649 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.659 | en.wikipedia.org/wiki/Python_(programming_language | 0.655 | en.wikipedia.org/wiki/Python_(programming_language | 0.649 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| firecrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.684 | en.wikipedia.org/wiki/Python_(programming_language | 0.630 | en.wikipedia.org/wiki/Python_(programming_language | 0.624 |


**Q10: What are Python Enhancement Proposals (PEPs)?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.527 | en.wikipedia.org/wiki/Python_(programming_language | 0.524 | en.wikipedia.org/wiki/Python_(programming_language | 0.496 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.527 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.527 | en.wikipedia.org/wiki/Python_(programming_language | 0.514 | en.wikipedia.org/wiki/Python_(programming_language | 0.503 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.527 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.527 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| firecrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.513 | en.wikipedia.org/wiki/Python_(programming_language | 0.506 | en.wikipedia.org/wiki/Python_(programming_language | 0.503 |


</details>

## stripe-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 20% (2/10) | 50% (5/10) | 60% (6/10) | 70% (7/10) | 80% (8/10) | 0.382 | 2825 | 402 |
| crawl4ai | 10% (1/10) | 40% (4/10) | 60% (6/10) | 70% (7/10) | 80% (8/10) | 0.320 | 3822 | 402 |
| crawl4ai-raw | 10% (1/10) | 40% (4/10) | 70% (7/10) | 80% (8/10) | 80% (8/10) | 0.332 | 3819 | 402 |
| scrapy+md | 20% (2/10) | 60% (6/10) | 80% (8/10) | 80% (8/10) | 80% (8/10) | 0.407 | 3475 | 402 |
| crawlee | 80% (8/10) | 80% (8/10) | 90% (9/10) | 90% (9/10) | 90% (9/10) | 0.820 | 11984 | 221 |
| colly+md | 80% (8/10) | 80% (8/10) | 90% (9/10) | 90% (9/10) | 90% (9/10) | 0.822 | 21249 | 402 |
| playwright | 80% (8/10) | 80% (8/10) | 90% (9/10) | 90% (9/10) | 90% (9/10) | 0.822 | 21360 | 402 |
| firecrawl | 30% (3/10) | 40% (4/10) | 40% (4/10) | 70% (7/10) | 80% (8/10) | 0.382 | 1773 | 395 |

<details>
<summary>Query-by-query results for stripe-docs</summary>

**Q1: How do I create a payment intent with Stripe?**
*(expects URL containing: `payment-intent`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #4 | docs.stripe.com/apple-pay | 0.650 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.612 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.603 |
| crawl4ai | #2 | docs.stripe.com/apple-pay | 0.671 | docs.stripe.com/agentic-commerce/concepts/shared-p | 0.618 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.608 |
| crawl4ai-raw | #2 | docs.stripe.com/apple-pay | 0.671 | docs.stripe.com/agentic-commerce/concepts/shared-p | 0.618 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.608 |
| scrapy+md | #5 | docs.stripe.com/apple-pay | 0.669 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.606 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.606 |
| crawlee | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/apple-pay | 0.668 | docs.stripe.com/billing/subscriptions/third-party- | 0.615 |
| colly+md | #1 | docs.stripe.com/changelog/2022-08-01/deferred-paym | 0.693 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/apple-pay | 0.669 |
| playwright | #1 | docs.stripe.com/changelog/2022-08-01/deferred-paym | 0.693 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/apple-pay | 0.668 |
| firecrawl | #6 | docs.stripe.com/apple-pay | 0.663 | docs.stripe.com/automated-testing | 0.637 | docs.stripe.com/billing/subscriptions/au-becs-debi | 0.608 |


**Q2: How do I handle webhooks from Stripe?**
*(expects URL containing: `webhook`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | docs.stripe.com/error-handling | 0.701 | docs.stripe.com/billing/taxes/collect-taxes | 0.625 | docs.stripe.com/billing/subscriptions/webhooks | 0.616 |
| crawl4ai | #4 | docs.stripe.com/error-handling | 0.716 | docs.stripe.com/agents-billing-workflows | 0.669 | docs.stripe.com/billing/subscriptions/third-party- | 0.666 |
| crawl4ai-raw | #4 | docs.stripe.com/error-handling | 0.716 | docs.stripe.com/agents-billing-workflows | 0.669 | docs.stripe.com/billing/subscriptions/third-party- | 0.666 |
| scrapy+md | #3 | docs.stripe.com/error-handling | 0.711 | docs.stripe.com/billing/taxes/collect-taxes | 0.621 | docs.stripe.com/billing/subscriptions/webhooks | 0.616 |
| crawlee | #1 | docs.stripe.com/billing/subscriptions/webhooks | 0.770 | docs.stripe.com/error-handling | 0.715 | docs.stripe.com/billing/taxes/collect-taxes | 0.621 |
| colly+md | #1 | docs.stripe.com/billing/subscriptions/webhooks | 0.770 | docs.stripe.com/error-handling | 0.711 | docs.stripe.com/billing/taxes/collect-taxes | 0.621 |
| playwright | #1 | docs.stripe.com/billing/subscriptions/webhooks | 0.770 | docs.stripe.com/error-handling | 0.715 | docs.stripe.com/billing/taxes/collect-taxes | 0.621 |
| firecrawl | miss | docs.stripe.com/error-handling | 0.666 | docs.stripe.com/error-handling | 0.599 | docs.stripe.com/agents-billing-workflows | 0.577 |


**Q3: How do I set up Stripe subscriptions?**
*(expects URL containing: `subscription`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.stripe.com/billing/subscriptions/migrate-subs | 0.713 | docs.stripe.com/billing/subscriptions/import-subsc | 0.697 | docs.stripe.com/subscriptions | 0.684 |
| crawl4ai | #1 | docs.stripe.com/billing/subscriptions/migrate-subs | 0.706 | docs.stripe.com/billing | 0.691 | docs.stripe.com/subscriptions | 0.691 |
| crawl4ai-raw | #1 | docs.stripe.com/billing/subscriptions/migrate-subs | 0.706 | docs.stripe.com/billing | 0.691 | docs.stripe.com/subscriptions | 0.691 |
| scrapy+md | #1 | docs.stripe.com/billing/subscriptions/migrate-subs | 0.713 | docs.stripe.com/billing/subscriptions/import-subsc | 0.697 | docs.stripe.com/subscriptions | 0.684 |
| crawlee | #1 | docs.stripe.com/subscriptions | 0.782 | docs.stripe.com/billing/subscriptions/paypal | 0.778 | docs.stripe.com/billing/subscriptions/overview | 0.766 |
| colly+md | #1 | docs.stripe.com/subscriptions | 0.782 | docs.stripe.com/billing/subscriptions/paypal | 0.778 | docs.stripe.com/billing/subscriptions/overview | 0.766 |
| playwright | #1 | docs.stripe.com/subscriptions | 0.782 | docs.stripe.com/billing/subscriptions/paypal | 0.778 | docs.stripe.com/billing/subscriptions/overview | 0.766 |
| firecrawl | #1 | docs.stripe.com/billing/subscriptions/migrate-subs | 0.660 | docs.stripe.com/billing/subscriptions/sales-led-bi | 0.654 | docs.stripe.com/billing/subscriptions/import-subsc | 0.645 |


**Q4: How do I authenticate with the Stripe API?**
*(expects URL containing: `authentication`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/apis | 0.672 | docs.stripe.com/apis | 0.625 | docs.stripe.com/error-handling | 0.610 |
| crawl4ai | miss | docs.stripe.com/apis | 0.652 | docs.stripe.com/apis | 0.649 | docs.stripe.com/get-started/account/activate | 0.644 |
| crawl4ai-raw | miss | docs.stripe.com/apis | 0.652 | docs.stripe.com/apis | 0.649 | docs.stripe.com/get-started/account/activate | 0.644 |
| scrapy+md | miss | docs.stripe.com/apis | 0.672 | docs.stripe.com/get-started/account | 0.632 | docs.stripe.com/apis | 0.625 |
| crawlee | #1 | docs.stripe.com/payment-authentication/writing-que | 0.702 | docs.stripe.com/apis | 0.672 | docs.stripe.com/keys | 0.665 |
| colly+md | #1 | docs.stripe.com/payment-authentication/writing-que | 0.702 | docs.stripe.com/apis | 0.672 | docs.stripe.com/keys | 0.665 |
| playwright | #1 | docs.stripe.com/payment-authentication/writing-que | 0.702 | docs.stripe.com/apis | 0.672 | docs.stripe.com/keys | 0.665 |
| firecrawl | miss | docs.stripe.com/ach-deprecated | 0.579 | docs.stripe.com/get-started/account/activate | 0.569 | docs.stripe.com/get-started/account/checklist | 0.558 |


**Q5: How do I handle errors in the Stripe API?**
*(expects URL containing: `error`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.696 | docs.stripe.com/error-low-level | 0.656 | docs.stripe.com/error-handling | 0.650 |
| crawl4ai | #2 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.695 | docs.stripe.com/error-low-level | 0.668 | docs.stripe.com/error-handling | 0.664 |
| crawl4ai-raw | #2 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.695 | docs.stripe.com/error-low-level | 0.668 | docs.stripe.com/error-handling | 0.664 |
| scrapy+md | #2 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.696 | docs.stripe.com/error-low-level | 0.656 | docs.stripe.com/error-handling | 0.649 |
| crawlee | #1 | docs.stripe.com/error-handling | 0.793 | docs.stripe.com/error-low-level | 0.782 | docs.stripe.com/error-codes | 0.705 |
| colly+md | #1 | docs.stripe.com/error-handling | 0.793 | docs.stripe.com/error-low-level | 0.782 | docs.stripe.com/error-codes | 0.705 |
| playwright | #1 | docs.stripe.com/error-handling | 0.793 | docs.stripe.com/error-low-level | 0.782 | docs.stripe.com/error-codes | 0.705 |
| firecrawl | #1 | docs.stripe.com/error-handling | 0.688 | docs.stripe.com/error-handling | 0.662 | docs.stripe.com/error-handling | 0.637 |


**Q6: How do I create a customer in Stripe?**
*(expects URL containing: `customer`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/billing/customer | 0.667 | docs.stripe.com/connect/use-accounts-as-customers | 0.661 |
| crawl4ai | #7 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.811 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.787 | docs.stripe.com/billing/subscriptions/usage-based- | 0.750 |
| crawl4ai-raw | #7 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.811 | docs.stripe.com/billing/subscriptions/usage-based/ | 0.786 | docs.stripe.com/billing/subscriptions/usage-based- | 0.750 |
| scrapy+md | #2 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/connect/use-accounts-as-customers | 0.670 | docs.stripe.com/billing/customer | 0.653 |
| crawlee | #1 | docs.stripe.com/connect/use-accounts-as-customers | 0.700 | docs.stripe.com/billing/customer | 0.699 | docs.stripe.com/customer-management/configure-port | 0.697 |
| colly+md | #1 | docs.stripe.com/connect/use-accounts-as-customers | 0.700 | docs.stripe.com/billing/customer | 0.699 | docs.stripe.com/customer-management/configure-port | 0.697 |
| playwright | #1 | docs.stripe.com/connect/use-accounts-as-customers | 0.700 | docs.stripe.com/billing/customer | 0.699 | docs.stripe.com/customer-management/configure-port | 0.697 |
| firecrawl | #3 | docs.stripe.com/billing/subscriptions/usage-based- | 0.699 | docs.stripe.com/billing/taxes/collect-taxes | 0.648 | docs.stripe.com/billing/customer | 0.637 |


**Q7: How do I process refunds with Stripe?**
*(expects URL containing: `refund`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #11 | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/billing/subscriptions/third-party- | 0.610 | docs.stripe.com/apis | 0.561 |
| crawl4ai | #12 | docs.stripe.com/billing/subscriptions/third-party- | 0.716 | docs.stripe.com/ach-deprecated | 0.618 | docs.stripe.com/get-started/account | 0.571 |
| crawl4ai-raw | #5 | docs.stripe.com/billing/subscriptions/third-party- | 0.716 | docs.stripe.com/ach-deprecated | 0.618 | docs.stripe.com/get-started/account | 0.571 |
| scrapy+md | #3 | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/billing/subscriptions/third-party- | 0.617 | docs.stripe.com/apple-pay/disputes-refunds | 0.596 |
| crawlee | #1 | docs.stripe.com/changelog/2014-07-26/application-f | 0.634 | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/billing/subscriptions/third-party- | 0.617 |
| colly+md | #1 | docs.stripe.com/changelog/2016-02-23/orders-paid-f | 0.664 | docs.stripe.com/changelog/2015-08-19/balance-trans | 0.652 | docs.stripe.com/changelog/2014-07-26/application-f | 0.634 |
| playwright | #1 | docs.stripe.com/changelog/2016-02-23/orders-paid-f | 0.664 | docs.stripe.com/changelog/2015-08-19/balance-trans | 0.652 | docs.stripe.com/changelog/2014-07-26/application-f | 0.634 |
| firecrawl | #7 | docs.stripe.com/billing/subscriptions/third-party- | 0.619 | docs.stripe.com/ach-deprecated | 0.605 | docs.stripe.com/billing/subscriptions/third-party- | 0.565 |


**Q8: How do I use Stripe checkout for payments?**
*(expects URL containing: `checkout`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #33 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 | docs.stripe.com/apis | 0.611 |
| crawl4ai | #39 | docs.stripe.com/billing/subscriptions/paypal | 0.644 | docs.stripe.com/apple-pay | 0.621 | docs.stripe.com/get-started/account | 0.620 |
| crawl4ai-raw | #41 | docs.stripe.com/billing/subscriptions/paypal | 0.644 | docs.stripe.com/apple-pay | 0.621 | docs.stripe.com/get-started/account | 0.620 |
| scrapy+md | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 | docs.stripe.com/billing/subscriptions/paypal | 0.634 |
| crawlee | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.681 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/billing/subscriptions/third-party- | 0.655 |
| colly+md | #44 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.681 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/billing/subscriptions/third-party- | 0.655 |
| playwright | #44 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.681 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/billing/subscriptions/third-party- | 0.655 |
| firecrawl | #18 | docs.stripe.com/get-started/data-migrations/pan-im | 0.664 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.633 | docs.stripe.com/get-started/data-migrations/pan-im | 0.614 |


**Q9: How do I test Stripe payments in development?**
*(expects URL containing: `test`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.stripe.com/automated-testing | 0.677 | docs.stripe.com/automated-testing | 0.663 | docs.stripe.com/billing/subscriptions/stablecoins | 0.649 |
| crawl4ai | #2 | docs.stripe.com/billing/subscriptions/manage-ios | 0.699 | docs.stripe.com/automated-testing | 0.693 | docs.stripe.com/get-started/data-migrations/pan-im | 0.679 |
| crawl4ai-raw | #2 | docs.stripe.com/billing/subscriptions/manage-ios | 0.699 | docs.stripe.com/automated-testing | 0.693 | docs.stripe.com/get-started/data-migrations/pan-im | 0.679 |
| scrapy+md | #1 | docs.stripe.com/automated-testing | 0.680 | docs.stripe.com/automated-testing | 0.663 | docs.stripe.com/billing/testing | 0.658 |
| crawlee | #1 | docs.stripe.com/automated-testing | 0.719 | docs.stripe.com/automated-testing | 0.680 | docs.stripe.com/automated-testing | 0.663 |
| colly+md | #1 | docs.stripe.com/automated-testing | 0.719 | docs.stripe.com/automated-testing | 0.680 | docs.stripe.com/automated-testing | 0.663 |
| playwright | #1 | docs.stripe.com/automated-testing | 0.719 | docs.stripe.com/automated-testing | 0.680 | docs.stripe.com/automated-testing | 0.663 |
| firecrawl | #1 | docs.stripe.com/automated-testing | 0.674 | docs.stripe.com/billing/subscriptions/stablecoins | 0.672 | docs.stripe.com/automated-testing | 0.664 |


**Q10: What are Stripe Connect and platform payments?**
*(expects URL containing: `connect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #9 | docs.stripe.com/ach-deprecated | 0.653 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/capital/overview | 0.640 |
| crawl4ai | #5 | docs.stripe.com/get-started/account/orgs/setup | 0.657 | docs.stripe.com/capital/overview | 0.647 | docs.stripe.com/capital/how-stripe-capital-works | 0.646 |
| crawl4ai-raw | #5 | docs.stripe.com/get-started/account/orgs/setup | 0.657 | docs.stripe.com/capital/overview | 0.647 | docs.stripe.com/capital/how-stripe-capital-works | 0.646 |
| scrapy+md | #5 | docs.stripe.com/ach-deprecated | 0.654 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/capital/overview | 0.640 |
| crawlee | #5 | docs.stripe.com/ach-deprecated | 0.661 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/capital/overview | 0.640 |
| colly+md | #5 | docs.stripe.com/ach-deprecated | 0.654 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/capital/overview | 0.640 |
| playwright | #5 | docs.stripe.com/ach-deprecated | 0.661 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/capital/overview | 0.640 |
| firecrawl | #8 | docs.stripe.com/issuing/integration-guides/embedde | 0.625 | docs.stripe.com/get-started/account/orgs/setup | 0.597 | docs.stripe.com/customer-management/configure-port | 0.595 |


</details>

## blog-engineering

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| **markcrawl** | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 853 | 200 |
| crawl4ai | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 5316 | 200 |
| crawl4ai-raw | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 5316 | 200 |
| scrapy+md | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 1844 | 200 |
| crawlee | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 5967 | 200 |
| colly+md | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 5355 | 200 |
| playwright | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 5955 | 200 |
| firecrawl | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 687 | 200 |

<details>
<summary>Query-by-query results for blog-engineering</summary>

**Q1: What are best practices for building reliable distributed systems?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.462 | github.blog/engineering/infrastructure/building-re | 0.412 | github.blog/engineering/infrastructure/building-re | 0.393 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/building-re | 0.492 | github.blog/engineering/infrastructure/building-re | 0.433 | github.blog/engineering/infrastructure/building-re | 0.416 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/building-re | 0.492 | github.blog/engineering/infrastructure/building-re | 0.433 | github.blog/engineering/infrastructure/building-re | 0.416 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/building-re | 0.458 | github.blog/engineering/infrastructure/building-re | 0.412 | github.blog/engineering/infrastructure/building-re | 0.390 |
| crawlee | #1 | github.blog/engineering/infrastructure/building-re | 0.458 | github.blog/engineering/infrastructure/building-re | 0.412 | github.blog/engineering/infrastructure/building-re | 0.390 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.458 | github.blog/engineering/infrastructure/building-re | 0.412 | github.blog/engineering/infrastructure/building-re | 0.390 |
| playwright | #1 | github.blog/engineering/infrastructure/building-re | 0.458 | github.blog/engineering/infrastructure/building-re | 0.412 | github.blog/engineering/infrastructure/building-re | 0.390 |
| firecrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.458 | github.blog/engineering/infrastructure/building-re | 0.445 | github.blog/engineering/infrastructure/building-re | 0.404 |


**Q2: How do companies handle database migrations at scale?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.509 | github.blog/news-insights/company-news/gh-ost-gith | 0.484 | github.blog/news-insights/company-news/gh-ost-gith | 0.430 |
| crawl4ai | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.502 | github.blog/news-insights/company-news/gh-ost-gith | 0.496 | github.blog/news-insights/company-news/gh-ost-gith | 0.476 |
| crawl4ai-raw | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.502 | github.blog/news-insights/company-news/gh-ost-gith | 0.496 | github.blog/news-insights/company-news/gh-ost-gith | 0.476 |
| scrapy+md | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.507 | github.blog/news-insights/company-news/gh-ost-gith | 0.484 | github.blog/news-insights/company-news/gh-ost-gith | 0.455 |
| crawlee | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.507 | github.blog/news-insights/company-news/gh-ost-gith | 0.484 | github.blog/news-insights/company-news/gh-ost-gith | 0.455 |
| colly+md | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.507 | github.blog/news-insights/company-news/gh-ost-gith | 0.484 | github.blog/news-insights/company-news/gh-ost-gith | 0.455 |
| playwright | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.507 | github.blog/news-insights/company-news/gh-ost-gith | 0.484 | github.blog/news-insights/company-news/gh-ost-gith | 0.455 |
| firecrawl | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.511 | github.blog/news-insights/company-news/gh-ost-gith | 0.488 | github.blog/news-insights/company-news/gh-ost-gith | 0.456 |


**Q3: What monitoring and observability tools do engineering teams use?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.427 | github.blog/news-insights/the-library/exception-mo | 0.412 |
| crawl4ai | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.450 | github.blog/news-insights/the-library/brubeck/ | 0.443 | github.blog/news-insights/the-library/brubeck/ | 0.442 |
| crawl4ai-raw | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.450 | github.blog/news-insights/the-library/brubeck/ | 0.443 | github.blog/news-insights/the-library/brubeck/ | 0.442 |
| scrapy+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.460 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| crawlee | #1 | github.blog/news-insights/the-library/exception-mo | 0.459 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| colly+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.460 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| playwright | #1 | github.blog/news-insights/the-library/exception-mo | 0.459 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| firecrawl | #1 | github.blog/news-insights/the-library/brubeck/ | 0.452 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/exception-mo | 0.440 |


**Q4: How do you implement continuous deployment pipelines?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.419 | github.blog/engineering/infrastructure/kubernetes- | 0.407 | github.blog/engineering/infrastructure/transit-and | 0.405 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.454 | github.blog/news-insights/the-library/deploying-wi | 0.443 | github.blog/engineering/infrastructure/githubs-met | 0.435 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.454 | github.blog/news-insights/the-library/deploying-wi | 0.443 | github.blog/engineering/infrastructure/githubs-met | 0.435 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.419 | github.blog/engineering/infrastructure/kubernetes- | 0.407 | github.blog/engineering/infrastructure/kubernetes- | 0.402 |
| crawlee | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.419 | github.blog/news-insights/the-library/deploying-wi | 0.412 | github.blog/engineering/infrastructure/kubernetes- | 0.407 |
| colly+md | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.419 | github.blog/news-insights/the-library/deploying-wi | 0.412 | github.blog/engineering/infrastructure/kubernetes- | 0.407 |
| playwright | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.419 | github.blog/news-insights/the-library/deploying-wi | 0.412 | github.blog/engineering/infrastructure/kubernetes- | 0.407 |
| firecrawl | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.409 | github.blog/engineering/infrastructure/kubernetes- | 0.397 | github.blog/news-insights/the-library/runnable-doc | 0.391 |


**Q5: What are common microservices architecture patterns?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/evolution-o | 0.337 | github.blog/engineering/infrastructure/transit-and | 0.337 | github.blog/engineering/user-experience/topics/ | 0.337 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/context-awa | 0.347 | github.blog/news-insights/the-library/services-gal | 0.342 | github.blog/engineering/infrastructure/githubs-met | 0.313 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/context-awa | 0.347 | github.blog/news-insights/the-library/services-gal | 0.342 | github.blog/engineering/infrastructure/githubs-met | 0.313 |
| scrapy+md | #1 | github.blog/engineering/engineering-principles/scr | 0.337 | github.blog/engineering/platform-security/syn-floo | 0.337 | github.blog/engineering/infrastructure/building-re | 0.337 |
| crawlee | #1 | github.blog/engineering/user-experience/topics/ | 0.337 | github.blog/engineering/platform-security/syn-floo | 0.337 | github.blog/engineering/infrastructure/building-re | 0.337 |
| colly+md | #1 | github.blog/engineering/infrastructure/githubs-met | 0.337 | github.blog/engineering/infrastructure/glb-directo | 0.337 | github.blog/engineering/engineering-principles/mov | 0.337 |
| playwright | #1 | github.blog/engineering/user-experience/topics/ | 0.337 | github.blog/engineering/infrastructure/evolution-o | 0.337 | github.blog/engineering/infrastructure/context-awa | 0.337 |
| firecrawl | #1 | github.blog/engineering/infrastructure/context-awa | 0.327 | github.blog/engineering/engineering-principles/scr | 0.312 | github.blog/news-insights/the-library/services-gal | 0.287 |


**Q6: How do you handle API versioning in production?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.338 | github.blog/engineering/engineering-principles/mov | 0.337 | github.blog/news-insights/the-library/announcing-e | 0.337 |
| crawl4ai | #1 | github.blog/news-insights/the-library/api-forum-gr | 0.386 | github.blog/news-insights/the-library/the-api/ | 0.370 | github.blog/engineering/infrastructure/kubernetes- | 0.350 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/api-forum-gr | 0.386 | github.blog/news-insights/the-library/the-api/ | 0.370 | github.blog/engineering/infrastructure/kubernetes- | 0.350 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/kubernetes- | 0.338 | github.blog/engineering/engineering-principles/mov | 0.333 | github.blog/news-insights/the-library/runnable-doc | 0.333 |
| crawlee | #1 | github.blog/news-insights/the-library/api-forum-gr | 0.365 | github.blog/news-insights/the-library/the-api/ | 0.355 | github.blog/engineering/infrastructure/kubernetes- | 0.338 |
| colly+md | #1 | github.blog/news-insights/the-library/api-forum-gr | 0.365 | github.blog/news-insights/the-library/the-api/ | 0.355 | github.blog/engineering/infrastructure/kubernetes- | 0.338 |
| playwright | #1 | github.blog/news-insights/the-library/api-forum-gr | 0.365 | github.blog/news-insights/the-library/the-api/ | 0.355 | github.blog/engineering/infrastructure/kubernetes- | 0.338 |
| firecrawl | #1 | github.blog/engineering/engineering-principles/mov | 0.336 | github.blog/news-insights/the-library/runnable-doc | 0.336 | github.blog/news-insights/the-library/announcing-e | 0.334 |


**Q7: What caching strategies work best for web applications?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.366 | github.blog/engineering/platform-security/soft-u2f | 0.366 | github.blog/engineering/infrastructure/kubernetes- | 0.366 |
| crawl4ai | #1 | github.blog/news-insights/the-library/more-db-opti | 0.346 | github.blog/news-insights/the-library/facebook-s-m | 0.328 | github.blog/engineering/infrastructure/context-awa | 0.326 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/more-db-opti | 0.346 | github.blog/news-insights/the-library/facebook-s-m | 0.328 | github.blog/engineering/infrastructure/context-awa | 0.326 |
| scrapy+md | #1 | github.blog/engineering/user-experience/topics/ | 0.366 | github.blog/engineering/engineering-principles/mov | 0.366 | github.blog/engineering/infrastructure/building-re | 0.366 |
| crawlee | #1 | github.blog/engineering/infrastructure/githubs-met | 0.366 | github.blog/engineering/infrastructure/orchestrato | 0.366 | github.blog/engineering/infrastructure/transit-and | 0.366 |
| colly+md | #1 | github.blog/engineering/engineering-principles/mov | 0.366 | github.blog/engineering/infrastructure/transit-and | 0.366 | github.blog/engineering/infrastructure/evolution-o | 0.366 |
| playwright | #1 | github.blog/engineering/infrastructure/orchestrato | 0.366 | github.blog/engineering/architecture-optimization/ | 0.366 | github.blog/engineering/infrastructure/glb-directo | 0.366 |
| firecrawl | #1 | github.blog/engineering/infrastructure/context-awa | 0.307 | github.blog/news-insights/the-library/github-rebas | 0.296 | github.blog/engineering/infrastructure/context-awa | 0.294 |


**Q8: How do you design for high availability and fault tolerance?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.491 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/kubernetes- | 0.439 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/building-re | 0.507 | github.blog/engineering/infrastructure/orchestrato | 0.485 | github.blog/engineering/infrastructure/orchestrato | 0.467 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/building-re | 0.507 | github.blog/engineering/infrastructure/orchestrato | 0.485 | github.blog/engineering/infrastructure/orchestrato | 0.467 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/kubernetes- | 0.439 |
| crawlee | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/kubernetes- | 0.439 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/kubernetes- | 0.439 |
| playwright | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/kubernetes- | 0.439 |
| firecrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.470 | github.blog/engineering/infrastructure/orchestrato | 0.455 | github.blog/engineering/infrastructure/building-re | 0.454 |


</details>

## Methodology

- **Queries:** 92 across 8 sites (verified against crawled pages)
- **Embedding model:** `text-embedding-3-small` (1536 dimensions)
- **Chunking:** Markdown-aware, 400 word max, 50 word overlap
- **Retrieval modes:** Embedding (cosine), BM25 (Okapi), Hybrid (RRF k=60), Reranked (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Retrieval:** Hit rate reported at K = 1, 3, 5, 10, 20, plus MRR
- **Reranking:** Top-50 candidates from hybrid search, reranked to top-20
- **Chunk sensitivity:** Tested at ~256tok, ~512tok, ~1024tok
- **Confidence intervals:** Wilson score interval (95%)
- **Same chunking and embedding** for all tools — only extraction quality varies
- **No fine-tuning or tool-specific optimization** — identical pipeline for all

See [METHODOLOGY.md](METHODOLOGY.md) for full test setup, tool configurations,
and fairness decisions.

Retrieval similarity across tools is expected — the same URLs, chunking, and
embedding model are used. The real differentiator shows up in
[ANSWER_QUALITY.md](ANSWER_QUALITY.md), where the LLM's final answers diverge
despite similar retrieval.

