# Retrieval Quality Comparison

<!-- style: v2, 2026-04-07 -->

Does crawler choice affect retrieval quality? Mostly no. All seven tools land between 42–43% at Hit@1 and converge to 51% at Hit@20 — differences that fall within confidence intervals. Your retrieval mode (embedding vs. BM25 vs. hybrid vs. reranked) matters far more than which crawler fetched the pages.

## How to read this report

This report tests 92 real queries across 8 sites using four retrieval strategies and seven crawlers. Before diving into the tables, here is what the metrics mean.

**Hit@K** -- "did the correct page appear in the top K results?" Hit@1 means the correct page was the very first result returned. Hit@5 means it appeared somewhere in the top 5. Higher K gives the system more chances to surface the right page. All numbers are averaged over 92 queries, so "42% (39/92)" means 39 of 92 queries returned the correct page at that position or better.

**MRR (Mean Reciprocal Rank)** -- a single score that captures not just whether the right page appeared, but how high it ranked. If the correct page is always rank 1, MRR = 1.0. If it is always rank 2, MRR = 0.5. An MRR of 0.45 means the correct page tends to land near the top when it is found at all. Higher MRR = fewer results a user has to scroll past.

**Confidence intervals** -- all Hit@K figures carry approximately ±10% at 95% confidence (Wilson interval, n=92). Differences smaller than ~5 percentage points between tools are within the noise and should not be treated as meaningful wins.

Three readers should be able to use this report without reading end-to-end:

- **Junior developer choosing a crawler for a first RAG project:** read the best-mode-per-tool table below and the takeaway after it. Short answer: pick any of the top five tools and use embedding search.
- **Senior/principal engineer evaluating rigor:** check the full 28-row table, the confidence intervals, and the [methodology](METHODOLOGY.md). Sample size is 92 queries; tool-to-tool differences at Hit@1 are 1 percentage point among the top five and within the ±10% confidence band.
- **Engineering manager or executive deciding whether to pay for reranking:** reranking adds cross-encoder inference cost but does not consistently beat plain embedding search on Hit@1. The benefit shows up in MRR and at Hit@3+, which matters if your pipeline uses multiple retrieved chunks. See [COST_AT_SCALE.md](COST_AT_SCALE.md) for dollar estimates.

## Best mode per tool

This digest shows each tool's strongest retrieval mode so most readers can stop here. For all tools, embedding search or reranking is the best or near-best choice at Hit@1.

| Tool | Best mode | Hit@1 | MRR | Notes |
|---|---|---|---|---|
| crawlee | embedding | 43% (40/92) ±10% | 0.452 | Tied top Hit@1; hybrid also strong |
| colly+md | embedding | 43% (40/92) ±10% | 0.452 | Tied top Hit@1 |
| playwright | embedding | 43% (40/92) ±10% | 0.452 | Tied top Hit@1 |
| **markcrawl** | **reranked** | **42% (39/92) ±10%** | **0.457** | **Highest MRR of all 28 rows** |
| scrapy+md | embedding | 42% (39/92) ±10% | 0.446 | Tied with markcrawl at Hit@1 |
| crawl4ai | reranked | 36% (33/92) ±10% | 0.419 | 4-7 pt lower at Hit@1; converges by Hit@10 |
| crawl4ai-raw | reranked | 36% (33/92) ±10% | 0.415 | Same as crawl4ai (identical crawl output) |

> Sorted by Hit@1 descending, then MRR. Differences between the top five tools are within confidence intervals.

## Why the tools perform so similarly

All seven crawlers retrieve the same underlying URLs from the same sites. The embedding model (`text-embedding-3-small`) sees essentially the same content regardless of which tool fetched it. The small differences that do exist -- crawl4ai slightly lower at Hit@1, crawlee/colly/playwright a point or two higher -- are within confidence intervals and disappear entirely by Hit@20, where every tool converges to 51% (47/92).

The real variable is **retrieval mode**, not the crawler. Embedding search and reranking both outperform BM25 by 15-20 percentage points at Hit@1. If you are choosing a crawler primarily because you think it will produce better retrieval, the data says that time is better spent upgrading your search strategy.

Although retrieval quality is similar across tools, answer quality is not. Cleaner Markdown with less navigation chrome produces better LLM answers even when the same pages are retrieved. See [ANSWER_QUALITY.md](ANSWER_QUALITY.md) for that comparison and [METHODOLOGY.md](METHODOLOGY.md) for the full test setup.

## All tools x all modes (28 rows)

The table below shows all 4 retrieval modes for all 7 tools. It is the complete picture for engineers who want to compare a specific tool-mode combination. For most readers, the best-mode table above is sufficient.

| Tool | Mode | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR |
|---|---|---|---|---|---|---|---|
| crawlee | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 |
| colly+md | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 |
| playwright | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 |
| **markcrawl** | **reranked** | **42% (39/92) ±10%** | **49% (45/92) ±10%** | **50% (46/92) ±10%** | **50% (46/92) ±10%** | **51% (47/92) ±10%** | **0.457** |
| **markcrawl** | **embedding** | **42% (39/92) ±10%** | **47% (43/92) ±10%** | **48% (44/92) ±10%** | **50% (46/92) ±10%** | **51% (47/92) ±10%** | **0.448** |
| scrapy+md | embedding | 42% (39/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.446 |
| colly+md | reranked | 40% (37/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.438 |
| crawlee | reranked | 40% (37/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.439 |
| playwright | reranked | 40% (37/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.439 |
| colly+md | hybrid | 41% (38/92) ±10% | 46% (42/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 0.440 |
| **markcrawl** | **hybrid** | **40% (37/92) ±10%** | **43% (40/92) ±10%** | **48% (44/92) ±10%** | **51% (47/92) ±10%** | **51% (47/92) ±10%** | **0.432** |
| playwright | hybrid | 40% (37/92) ±10% | 46% (42/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 0.433 |
| crawlee | hybrid | 40% (37/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.438 |
| scrapy+md | hybrid | 38% (35/92) ±10% | 46% (42/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.421 |
| crawl4ai | hybrid | 37% (34/92) ±10% | 45% (41/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.411 |
| crawl4ai-raw | hybrid | 37% (34/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.414 |
| crawl4ai | reranked | 36% (33/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.419 |
| crawl4ai-raw | reranked | 36% (33/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.415 |
| scrapy+md | reranked | 35% (32/92) ±10% | 45% (41/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.403 |
| **markcrawl** | **bm25** | **27% (25/92) ±9%** | **35% (32/92) ±10%** | **38% (35/92) ±10%** | **48% (44/92) ±10%** | **50% (46/92) ±10%** | **0.330** |
| crawlee | bm25 | 27% (25/92) ±9% | 32% (29/92) ±9% | 37% (34/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 0.318 |
| colly+md | bm25 | 26% (24/92) ±9% | 32% (29/92) ±9% | 37% (34/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 0.312 |
| playwright | bm25 | 26% (24/92) ±9% | 32% (29/92) ±9% | 37% (34/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 0.312 |
| scrapy+md | bm25 | 25% (23/92) ±9% | 32% (29/92) ±9% | 35% (32/92) ±10% | 46% (42/92) ±10% | 50% (46/92) ±10% | 0.304 |
| crawl4ai-raw | bm25 | 23% (21/92) ±8% | 28% (26/92) ±9% | 33% (30/92) ±9% | 38% (35/92) ±10% | 42% (39/92) ±10% | 0.274 |
| crawl4ai | bm25 | 22% (20/92) ±8% | 28% (26/92) ±9% | 33% (30/92) ±9% | 38% (35/92) ±10% | 42% (39/92) ±10% | 0.269 |

> Sorted by Hit@1 descending, then MRR. BM25 alone performs 15-20 percentage points worse than embedding search at Hit@1 across all tools.

## Retrieval modes explained

The four modes tested represent a spectrum from simple to sophisticated:

- **Embedding** -- each page chunk is converted to a vector by `text-embedding-3-small`, and
  the query is matched by cosine similarity. Fast, general-purpose, language-aware. This is
  the default for most RAG pipelines.

- **BM25** -- keyword search based on term frequency (the algorithm behind classic search
  engines). No semantic understanding: "car" and "automobile" are different terms. Works well
  when queries use the same vocabulary as the source text; poorly when they don't. BM25 stands
  for Best Match 25, a probabilistic ranking function.

- **Hybrid** -- runs both embedding and BM25, then merges their ranked lists using Reciprocal
  Rank Fusion (RRF). RRF combines rankings by giving each document a score of 1/(rank+60) and
  summing across lists -- so a document ranked 1st in both gets a much higher score than one
  ranked 1st in only one. Hybrid typically outperforms either method alone on diverse query
  types.

- **Reranked** -- starts with hybrid candidates, then runs a cross-encoder model
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`) that scores each query-document pair directly.
  Unlike the embedding model, which encodes query and document separately, a cross-encoder
  reads them together and is more accurate -- but too slow to rank millions of documents, so
  it is only applied to the top candidates from hybrid.

## Embedding-only summary (chunks and efficiency)

This table isolates embedding mode to show how chunk counts and average word lengths vary across tools. Tools with fewer, more focused chunks achieve comparable retrieval with a more compact index.

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Avg words |
|---|---|---|---|---|---|---|---|---|
| crawlee | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 | 4422 | 217 |
| colly+md | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 | 3884 | 213 |
| playwright | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.452 | 4167 | 208 |
| **markcrawl** | **42% (39/92) ±10%** | **47% (43/92) ±10%** | **48% (44/92) ±10%** | **50% (46/92) ±10%** | **51% (47/92) ±10%** | **0.448** | **2126** | **139** |
| scrapy+md | 42% (39/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.446 | 2574 | 140 |
| crawl4ai | 38% (35/92) ±10% | 43% (40/92) ±10% | 47% (43/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.417 | 3539 | 126 |
| crawl4ai-raw | 38% (35/92) ±10% | 43% (40/92) ±10% | 47% (43/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.417 | 3540 | 126 |

> Sorted by MRR descending. markcrawl achieves comparable Hit@1 to the top tools with 40-50% fewer chunks, meaning its retrieval index is more compact.

## quotes-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 25% (3/12) | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.312 | 24 | 15 |
| crawl4ai | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.375 | 22 | 15 |
| crawl4ai-raw | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.375 | 22 | 15 |
| scrapy+md | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.361 | 26 | 15 |
| crawlee | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.361 | 29 | 15 |
| colly+md | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.361 | 29 | 15 |
| playwright | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.361 | 29 | 15 |

<details>
<summary>Query-by-query results for quotes-toscrape</summary>

**Q1: What did Albert Einstein say about thinking and the world?**
*(expects URL containing: `quotes.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.544 | quotes.toscrape.com/author/Albert-Einstein | 0.535 | quotes.toscrape.com/author/Albert-Einstein | 0.468 |
| crawl4ai | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.571 | quotes.toscrape.com/author/Albert-Einstein | 0.558 | quotes.toscrape.com/tag/world/page/1/ | 0.482 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.571 | quotes.toscrape.com/author/Albert-Einstein | 0.558 | quotes.toscrape.com/tag/world/page/1/ | 0.482 |
| scrapy+md | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.544 | quotes.toscrape.com/author/Albert-Einstein/ | 0.535 | quotes.toscrape.com/author/Albert-Einstein/ | 0.468 |
| crawlee | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.544 | quotes.toscrape.com/author/Albert-Einstein | 0.535 | quotes.toscrape.com/author/Albert-Einstein | 0.468 |
| colly+md | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.544 | quotes.toscrape.com/author/Albert-Einstein/ | 0.535 | quotes.toscrape.com/author/Albert-Einstein/ | 0.468 |
| playwright | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.544 | quotes.toscrape.com/author/Albert-Einstein | 0.535 | quotes.toscrape.com/author/Albert-Einstein | 0.468 |


**Q2: Which quotes are tagged with 'inspirational'?**
*(expects URL containing: `tag/inspirational`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.578 | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.573 | quotes.toscrape.com/tag/friends/ | 0.560 |
| crawl4ai | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.582 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/edison/page/1/ | 0.572 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.582 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/edison/page/1/ | 0.572 |
| scrapy+md | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.580 | quotes.toscrape.com/ | 0.567 | quotes.toscrape.com/tag/miracles/page/1/ | 0.566 |
| crawlee | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.592 | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 |
| colly+md | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.592 | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 |
| playwright | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.592 | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/ | 0.586 |


**Q3: What did Jane Austen say about novels and reading?**
*(expects URL containing: `author/Jane-Austen`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/tag/humor/ | 0.327 | quotes.toscrape.com/ | 0.319 |
| crawl4ai | miss | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/ | 0.322 | quotes.toscrape.com/ | 0.313 |
| crawl4ai-raw | miss | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/ | 0.322 | quotes.toscrape.com/ | 0.313 |
| scrapy+md | miss | quotes.toscrape.com/tag/humor/ | 0.334 | quotes.toscrape.com/author/J-K-Rowling/ | 0.333 | quotes.toscrape.com/ | 0.324 |
| crawlee | miss | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/author/J-K-Rowling | 0.319 | quotes.toscrape.com/ | 0.306 |
| colly+md | miss | quotes.toscrape.com/author/J-K-Rowling/ | 0.334 | quotes.toscrape.com/author/J-K-Rowling/ | 0.319 | quotes.toscrape.com/ | 0.306 |
| playwright | miss | quotes.toscrape.com/author/J-K-Rowling | 0.333 | quotes.toscrape.com/author/J-K-Rowling | 0.319 | quotes.toscrape.com/ | 0.306 |


**Q4: What quotes are about the truth?**
*(expects URL containing: `tag/truth`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.474 | quotes.toscrape.com/tag/friends/ | 0.469 | quotes.toscrape.com/tag/life/ | 0.456 |
| crawl4ai | miss | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.459 | quotes.toscrape.com/tag/humor/ | 0.453 |
| crawl4ai-raw | miss | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.459 | quotes.toscrape.com/tag/humor/ | 0.453 |
| scrapy+md | miss | quotes.toscrape.com/tag/life/ | 0.456 | quotes.toscrape.com/ | 0.451 | quotes.toscrape.com/tag/friends/ | 0.442 |
| crawlee | miss | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 | quotes.toscrape.com/tag/life/ | 0.456 |
| colly+md | miss | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 | quotes.toscrape.com/tag/life/ | 0.456 |
| playwright | miss | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/friends/ | 0.456 | quotes.toscrape.com/tag/life/ | 0.456 |


**Q5: Which quotes are about humor and being funny?**
*(expects URL containing: `tag/humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/humor/ | 0.507 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/life/ | 0.425 |
| crawl4ai | #1 | quotes.toscrape.com/tag/humor/ | 0.513 | quotes.toscrape.com/ | 0.446 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.438 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/humor/ | 0.513 | quotes.toscrape.com/ | 0.446 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.438 |
| scrapy+md | #1 | quotes.toscrape.com/tag/humor/ | 0.494 | quotes.toscrape.com/ | 0.429 | quotes.toscrape.com/tag/life/ | 0.425 |
| crawlee | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/tag/simile/ | 0.429 |
| colly+md | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/tag/simile/ | 0.429 |
| playwright | #1 | quotes.toscrape.com/tag/humor/ | 0.499 | quotes.toscrape.com/ | 0.444 | quotes.toscrape.com/tag/simile/ | 0.429 |


**Q6: What did J.K. Rowling say about choices and abilities?**
*(expects URL containing: `author/J-K-Rowling`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | quotes.toscrape.com/tag/abilities/page/1/ | 0.506 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 |
| crawl4ai | #2 | quotes.toscrape.com/tag/abilities/page/1/ | 0.566 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 |
| crawl4ai-raw | #2 | quotes.toscrape.com/tag/abilities/page/1/ | 0.566 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 |
| scrapy+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.501 | quotes.toscrape.com/tag/abilities/page/1/ | 0.497 | quotes.toscrape.com/author/J-K-Rowling/ | 0.477 |
| crawlee | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| colly+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.501 | quotes.toscrape.com/author/J-K-Rowling/ | 0.477 | quotes.toscrape.com/author/J-K-Rowling/ | 0.468 |
| playwright | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |


**Q7: What quotes are tagged with 'change'?**
*(expects URL containing: `tag/change`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/world/page/1/ | 0.509 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.505 | quotes.toscrape.com/ | 0.488 |
| crawl4ai | miss | quotes.toscrape.com/tag/world/page/1/ | 0.541 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 | quotes.toscrape.com/ | 0.487 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/world/page/1/ | 0.541 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 | quotes.toscrape.com/ | 0.487 |
| scrapy+md | miss | quotes.toscrape.com/tag/world/page/1/ | 0.514 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.512 | quotes.toscrape.com/ | 0.484 |
| crawlee | miss | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 | quotes.toscrape.com/ | 0.489 |
| colly+md | miss | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 | quotes.toscrape.com/ | 0.489 |
| playwright | miss | quotes.toscrape.com/tag/world/page/1/ | 0.507 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.497 | quotes.toscrape.com/ | 0.489 |


**Q8: What did Steve Martin say about sunshine?**
*(expects URL containing: `author/Steve-Martin`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.306 | quotes.toscrape.com/tag/humor/ | 0.303 | quotes.toscrape.com/tag/simile/ | 0.300 |
| crawl4ai | miss | quotes.toscrape.com/tag/simile/ | 0.391 | quotes.toscrape.com/tag/humor/ | 0.308 | quotes.toscrape.com/tag/life/ | 0.287 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/simile/ | 0.391 | quotes.toscrape.com/tag/humor/ | 0.308 | quotes.toscrape.com/tag/life/ | 0.287 |
| scrapy+md | miss | quotes.toscrape.com/tag/simile/ | 0.314 | quotes.toscrape.com/tag/humor/ | 0.294 | quotes.toscrape.com/ | 0.284 |
| crawlee | miss | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 | quotes.toscrape.com/tag/life/ | 0.280 |
| colly+md | miss | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 | quotes.toscrape.com/tag/life/ | 0.280 |
| playwright | miss | quotes.toscrape.com/ | 0.284 | quotes.toscrape.com/tag/humor/ | 0.283 | quotes.toscrape.com/tag/life/ | 0.280 |


**Q9: Which quotes talk about believing in yourself?**
*(expects URL containing: `tag/be-yourself`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #4 | quotes.toscrape.com/tag/life/ | 0.477 | quotes.toscrape.com/tag/life/ | 0.457 | quotes.toscrape.com/ | 0.416 |
| crawl4ai | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/tag/abilities/page/1/ | 0.444 | quotes.toscrape.com/tag/life/ | 0.435 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/tag/abilities/page/1/ | 0.444 | quotes.toscrape.com/tag/life/ | 0.435 |
| scrapy+md | #3 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.417 |
| crawlee | #3 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 |
| colly+md | #3 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 |
| playwright | #3 | quotes.toscrape.com/tag/life/ | 0.470 | quotes.toscrape.com/tag/life/ | 0.457 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 |


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


**Q11: What quotes are about thinking deeply?**
*(expects URL containing: `tag/thinking`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.525 | quotes.toscrape.com/ | 0.481 | quotes.toscrape.com/tag/world/page/1/ | 0.466 |
| crawl4ai | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.593 | quotes.toscrape.com/tag/world/page/1/ | 0.528 | quotes.toscrape.com/ | 0.497 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.593 | quotes.toscrape.com/tag/world/page/1/ | 0.528 | quotes.toscrape.com/ | 0.497 |
| scrapy+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.540 | quotes.toscrape.com/ | 0.490 | quotes.toscrape.com/tag/world/page/1/ | 0.476 |
| crawlee | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/ | 0.491 | quotes.toscrape.com/tag/world/page/1/ | 0.479 |
| colly+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/ | 0.491 | quotes.toscrape.com/tag/world/page/1/ | 0.480 |
| playwright | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.528 | quotes.toscrape.com/ | 0.491 | quotes.toscrape.com/tag/world/page/1/ | 0.479 |


**Q12: What quotes talk about living life fully?**
*(expects URL containing: `tag/live`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/ | 0.455 |
| crawl4ai | miss | quotes.toscrape.com/tag/life/ | 0.555 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.464 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/life/ | 0.555 | quotes.toscrape.com/tag/life/ | 0.529 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.464 |
| scrapy+md | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/ | 0.449 |
| crawlee | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/ | 0.455 |
| colly+md | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/ | 0.455 |
| playwright | miss | quotes.toscrape.com/tag/life/ | 0.559 | quotes.toscrape.com/tag/life/ | 0.528 | quotes.toscrape.com/ | 0.455 |


</details>

## books-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 124 | 60 |
| crawl4ai | 69% (9/13) | 92% (12/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 0.810 | 667 | 60 |
| crawl4ai-raw | 69% (9/13) | 92% (12/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 0.810 | 667 | 60 |
| scrapy+md | 92% (12/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 0.962 | 135 | 60 |
| crawlee | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |
| colly+md | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |
| playwright | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |

<details>
<summary>Query-by-query results for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/catalogue/category/books/food-a | 0.485 | books.toscrape.com/catalogue/category/books/young- | 0.483 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/histor | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/adult- | 0.492 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/histor | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/adult- | 0.492 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books/young- | 0.485 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books/young- | 0.485 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books/young- | 0.485 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books/young- | 0.485 |


**Q2: What mystery and thriller books are in the catalog?**
*(expects URL containing: `mystery`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/suspen | 0.471 |
| crawl4ai | #3 | books.toscrape.com/catalogue/category/books/suspen | 0.538 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 |
| crawl4ai-raw | #3 | books.toscrape.com/catalogue/category/books/suspen | 0.538 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.479 | books.toscrape.com/catalogue/category/books/suspen | 0.460 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.482 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.482 |


**Q3: What is the rating of the most expensive book?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/young- | 0.424 | books.toscrape.com/catalogue/category/books/defaul | 0.417 | books.toscrape.com/catalogue/category/books/scienc | 0.414 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/adult- | 0.426 | books.toscrape.com/catalogue/category/books/horror | 0.423 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/adult- | 0.426 | books.toscrape.com/catalogue/category/books/horror | 0.423 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 | books.toscrape.com/catalogue/category/books/defaul | 0.417 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 | books.toscrape.com/catalogue/category/books/defaul | 0.417 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 | books.toscrape.com/catalogue/category/books/defaul | 0.417 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 | books.toscrape.com/catalogue/category/books/defaul | 0.417 |


**Q4: What science fiction books are available?**
*(expects URL containing: `science-fiction`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.500 | books.toscrape.com/catalogue/category/books/scienc | 0.469 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.441 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.493 | books.toscrape.com/catalogue/category/books/scienc | 0.471 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.493 | books.toscrape.com/catalogue/category/books/scienc | 0.471 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.441 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.418 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.504 | books.toscrape.com/catalogue/category/books/scienc | 0.467 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.504 | books.toscrape.com/catalogue/category/books/scienc | 0.466 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.504 | books.toscrape.com/catalogue/category/books/scienc | 0.467 |


**Q5: What horror books are in the catalog?**
*(expects URL containing: `horror`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/horror | 0.509 | books.toscrape.com/catalogue/category/books/sequen | 0.464 | books.toscrape.com/catalogue/category/books/suspen | 0.441 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/suspen | 0.489 | books.toscrape.com/catalogue/category/books/horror | 0.484 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/suspen | 0.489 | books.toscrape.com/catalogue/category/books/horror | 0.485 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/ | 0.463 | books.toscrape.com/catalogue/category/books/sequen | 0.458 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |


**Q6: What poetry books can I find?**
*(expects URL containing: `poetry`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.495 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.406 | books.toscrape.com/catalogue/olio_984/index.html | 0.397 |
| crawl4ai | #2 | books.toscrape.com/catalogue/page-2.html | 0.506 | books.toscrape.com/catalogue/category/books/poetry | 0.498 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/page-2.html | 0.507 | books.toscrape.com/catalogue/category/books/poetry | 0.498 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.401 | books.toscrape.com/catalogue/category/books/poetry | 0.389 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.412 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.412 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.412 |


**Q7: What romance novels are available?**
*(expects URL containing: `romance`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/romanc | 0.458 | books.toscrape.com/catalogue/category/books/womens | 0.418 |
| crawl4ai | #2 | books.toscrape.com/catalogue/category/books/add-a- | 0.545 | books.toscrape.com/catalogue/category/books/romanc | 0.520 | books.toscrape.com/catalogue/category/books/womens | 0.477 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/category/books/add-a- | 0.545 | books.toscrape.com/catalogue/category/books/romanc | 0.520 | books.toscrape.com/catalogue/category/books/womens | 0.477 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/new-ad | 0.422 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/womens | 0.457 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/womens | 0.457 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/womens | 0.457 |


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


**Q9: What philosophy books are available to read?**
*(expects URL containing: `philosophy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/philos | 0.439 | books.toscrape.com/catalogue/libertarianism-for-be | 0.405 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.429 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.429 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.415 | books.toscrape.com/catalogue/libertarianism-for-be | 0.363 | books.toscrape.com/catalogue/category/books/psycho | 0.362 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |


**Q10: What humor and comedy books can I find?**
*(expects URL containing: `humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.401 | books.toscrape.com/catalogue/category/books/nonfic | 0.300 | books.toscrape.com/catalogue/its-only-the-himalaya | 0.297 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.436 | books.toscrape.com/catalogue/category/books/humor_ | 0.403 | books.toscrape.com/catalogue/category/books/scienc | 0.402 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.436 | books.toscrape.com/catalogue/category/books/humor_ | 0.403 | books.toscrape.com/catalogue/category/books/scienc | 0.402 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.359 | books.toscrape.com/catalogue/category/books/horror | 0.319 | books.toscrape.com/catalogue/page-2.html | 0.315 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books/poetry | 0.325 | books.toscrape.com/catalogue/category/books/nonfic | 0.322 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books/poetry | 0.325 | books.toscrape.com/catalogue/category/books/nonfic | 0.322 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.390 | books.toscrape.com/catalogue/category/books/poetry | 0.325 | books.toscrape.com/catalogue/category/books/nonfic | 0.322 |


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


**Q12: What is the book Sharp Objects about?**
*(expects URL containing: `sharp-objects`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.591 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.485 |
| crawl4ai | #5 | books.toscrape.com/catalogue/the-dirty-little-secr | 0.648 | books.toscrape.com/catalogue/the-boys-in-the-boat- | 0.648 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 |
| crawl4ai-raw | #5 | books.toscrape.com/catalogue/the-dirty-little-secr | 0.648 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 | books.toscrape.com/catalogue/the-boys-in-the-boat- | 0.648 |
| scrapy+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.447 |
| crawlee | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| colly+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| playwright | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |


**Q13: What biography books are in the catalog?**
*(expects URL containing: `biography`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.431 | books.toscrape.com/catalogue/starving-hearts-trian | 0.395 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.395 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.449 | books.toscrape.com/catalogue/category/books/autobi | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.435 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.449 | books.toscrape.com/catalogue/category/books/autobi | 0.441 | books.toscrape.com/catalogue/category/books/histor | 0.435 |
| scrapy+md | #2 | books.toscrape.com/ | 0.419 | books.toscrape.com/catalogue/category/books/biogra | 0.377 | books.toscrape.com/catalogue/starving-hearts-trian | 0.373 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/page-2.html | 0.374 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/page-2.html | 0.374 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.419 | books.toscrape.com/ | 0.416 | books.toscrape.com/catalogue/page-2.html | 0.374 |


</details>

## fastapi-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 549 | 25 |
| crawl4ai | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 33% (5/15) | 0.278 | 676 | 25 |
| crawl4ai-raw | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 33% (5/15) | 0.276 | 676 | 25 |
| scrapy+md | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 33% (5/15) | 0.274 | 617 | 25 |
| crawlee | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 638 | 25 |
| colly+md | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.271 | 639 | 25 |
| playwright | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 638 | 25 |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/security/ | 0.521 | fastapi.tiangolo.com/reference/security/ | 0.519 | fastapi.tiangolo.com/reference/security/ | 0.518 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/security/ | 0.553 | fastapi.tiangolo.com/reference/security/ | 0.550 | fastapi.tiangolo.com/reference/security/ | 0.535 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/security/ | 0.553 | fastapi.tiangolo.com/reference/security/ | 0.550 | fastapi.tiangolo.com/reference/security/ | 0.536 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/security/ | 0.549 | fastapi.tiangolo.com/reference/security/ | 0.544 | fastapi.tiangolo.com/reference/security/ | 0.538 |
| crawlee | #1 | fastapi.tiangolo.com/reference/security/ | 0.556 | fastapi.tiangolo.com/reference/security/ | 0.552 | fastapi.tiangolo.com/reference/security/ | 0.550 |
| colly+md | #1 | fastapi.tiangolo.com/reference/security/ | 0.549 | fastapi.tiangolo.com/reference/security/ | 0.544 | fastapi.tiangolo.com/reference/security/ | 0.538 |
| playwright | #1 | fastapi.tiangolo.com/reference/security/ | 0.556 | fastapi.tiangolo.com/reference/security/ | 0.552 | fastapi.tiangolo.com/reference/security/ | 0.550 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/reference/status/ | 0.568 | fastapi.tiangolo.com/advanced/custom-response/ | 0.565 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/advanced/custom-response/ | 0.583 | fastapi.tiangolo.com/reference/status/ | 0.583 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/reference/status/ | 0.584 | fastapi.tiangolo.com/advanced/custom-response/ | 0.583 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/reference/status/ | 0.572 | fastapi.tiangolo.com/advanced/custom-response/ | 0.571 |
| crawlee | #1 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/reference/status/ | 0.580 | fastapi.tiangolo.com/advanced/custom-response/ | 0.573 |
| colly+md | #1 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/reference/status/ | 0.572 | fastapi.tiangolo.com/advanced/custom-response/ | 0.571 |
| playwright | #1 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/reference/status/ | 0.580 | fastapi.tiangolo.com/advanced/custom-response/ | 0.573 |


**Q3: How do I define query parameters in the FastAPI reference?**
*(expects URL containing: `reference/fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.585 | fastapi.tiangolo.com/reference/security/ | 0.573 | fastapi.tiangolo.com/reference/security/ | 0.540 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/security/ | 0.580 | fastapi.tiangolo.com/reference/security/ | 0.553 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/security/ | 0.580 | fastapi.tiangolo.com/reference/security/ | 0.553 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.590 | fastapi.tiangolo.com/reference/security/ | 0.574 | fastapi.tiangolo.com/reference/websockets/ | 0.574 |
| crawlee | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/websockets/ | 0.584 | fastapi.tiangolo.com/reference/security/ | 0.568 |
| colly+md | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.590 | fastapi.tiangolo.com/reference/security/ | 0.574 | fastapi.tiangolo.com/reference/websockets/ | 0.574 |
| playwright | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/websockets/ | 0.584 | fastapi.tiangolo.com/reference/security/ | 0.568 |


**Q4: How does FastAPI handle JSON encoding and base64 bytes?**
*(expects URL containing: `json-base64-bytes`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.572 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.533 | fastapi.tiangolo.com/features/ | 0.504 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/encoders/ | 0.634 | fastapi.tiangolo.com/advanced/custom-response/ | 0.581 | fastapi.tiangolo.com/reference/encoders/ | 0.558 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/encoders/ | 0.634 | fastapi.tiangolo.com/advanced/custom-response/ | 0.581 | fastapi.tiangolo.com/reference/encoders/ | 0.556 |
| scrapy+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.572 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.533 | fastapi.tiangolo.com/reference/encoders/ | 0.509 |
| crawlee | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.560 | fastapi.tiangolo.com/features/ | 0.533 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.527 |
| colly+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.572 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.533 | fastapi.tiangolo.com/reference/encoders/ | 0.521 |
| playwright | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.560 | fastapi.tiangolo.com/features/ | 0.534 | fastapi.tiangolo.com/reference/encoders/ | 0.532 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.567 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.537 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.533 |
| crawl4ai | miss | fastapi.tiangolo.com/features/ | 0.575 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.573 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.573 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/features/ | 0.575 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.573 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.573 |
| scrapy+md | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.567 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.546 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.536 |
| crawlee | miss | fastapi.tiangolo.com/features/ | 0.559 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.559 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.542 |
| colly+md | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.567 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.536 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.533 |
| playwright | miss | fastapi.tiangolo.com/features/ | 0.559 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.559 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.542 |


**Q6: How do I use OAuth2 with password flow in FastAPI?**
*(expects URL containing: `simple-oauth2`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/reference/security/ | 0.635 | fastapi.tiangolo.com/reference/security/ | 0.628 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/reference/security/ | 0.661 | fastapi.tiangolo.com/reference/security/ | 0.656 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/reference/security/ | 0.661 | fastapi.tiangolo.com/reference/security/ | 0.656 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/reference/security/ | 0.645 | fastapi.tiangolo.com/reference/security/ | 0.640 |
| crawlee | miss | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/reference/security/ | 0.673 | fastapi.tiangolo.com/reference/security/ | 0.652 |
| colly+md | miss | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/reference/security/ | 0.645 | fastapi.tiangolo.com/reference/security/ | 0.640 |
| playwright | miss | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/reference/security/ | 0.673 | fastapi.tiangolo.com/reference/security/ | 0.652 |


**Q7: How do I use WebSockets in FastAPI?**
*(expects URL containing: `websockets`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.622 | fastapi.tiangolo.com/reference/websockets/ | 0.563 | fastapi.tiangolo.com/reference/websockets/ | 0.523 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.636 | fastapi.tiangolo.com/reference/websockets/ | 0.601 | fastapi.tiangolo.com/reference/websockets/ | 0.600 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.636 | fastapi.tiangolo.com/reference/websockets/ | 0.601 | fastapi.tiangolo.com/reference/websockets/ | 0.581 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.625 | fastapi.tiangolo.com/reference/websockets/ | 0.604 | fastapi.tiangolo.com/reference/websockets/ | 0.572 |
| crawlee | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.611 | fastapi.tiangolo.com/reference/websockets/ | 0.605 | fastapi.tiangolo.com/reference/websockets/ | 0.520 |
| colly+md | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.625 | fastapi.tiangolo.com/reference/websockets/ | 0.604 | fastapi.tiangolo.com/reference/websockets/ | 0.524 |
| playwright | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.611 | fastapi.tiangolo.com/reference/websockets/ | 0.604 | fastapi.tiangolo.com/reference/websockets/ | 0.520 |


**Q8: How do I stream data responses in FastAPI?**
*(expects URL containing: `stream-data`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.561 | fastapi.tiangolo.com/advanced/custom-response/ | 0.549 | fastapi.tiangolo.com/features/ | 0.521 |
| crawl4ai | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.596 | fastapi.tiangolo.com/advanced/custom-response/ | 0.564 | fastapi.tiangolo.com/tutorial/response-model/ | 0.562 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.596 | fastapi.tiangolo.com/advanced/custom-response/ | 0.564 | fastapi.tiangolo.com/tutorial/response-model/ | 0.562 |
| scrapy+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.561 | fastapi.tiangolo.com/advanced/custom-response/ | 0.549 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.544 |
| crawlee | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.571 | fastapi.tiangolo.com/advanced/custom-response/ | 0.559 | fastapi.tiangolo.com/reference/fastapi/ | 0.550 |
| colly+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.561 | fastapi.tiangolo.com/advanced/custom-response/ | 0.549 | fastapi.tiangolo.com/reference/fastapi/ | 0.538 |
| playwright | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.571 | fastapi.tiangolo.com/advanced/custom-response/ | 0.559 | fastapi.tiangolo.com/reference/fastapi/ | 0.550 |


**Q9: How do I return additional response types in FastAPI?**
*(expects URL containing: `additional-responses`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.599 | fastapi.tiangolo.com/advanced/custom-response/ | 0.587 | fastapi.tiangolo.com/tutorial/response-model/ | 0.580 |
| crawl4ai | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 | fastapi.tiangolo.com/advanced/custom-response/ | 0.632 | fastapi.tiangolo.com/advanced/custom-response/ | 0.604 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 | fastapi.tiangolo.com/advanced/custom-response/ | 0.632 | fastapi.tiangolo.com/advanced/custom-response/ | 0.604 |
| scrapy+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.615 | fastapi.tiangolo.com/advanced/custom-response/ | 0.599 | fastapi.tiangolo.com/advanced/custom-response/ | 0.587 |
| crawlee | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.592 | fastapi.tiangolo.com/tutorial/response-model/ | 0.584 |
| colly+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.599 | fastapi.tiangolo.com/advanced/custom-response/ | 0.587 | fastapi.tiangolo.com/tutorial/response-model/ | 0.577 |
| playwright | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.592 | fastapi.tiangolo.com/tutorial/response-model/ | 0.584 |


**Q10: How do I write async tests for FastAPI applications?**
*(expects URL containing: `async-tests`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/ | 0.575 | fastapi.tiangolo.com/deployment/versions/ | 0.564 | fastapi.tiangolo.com/features/ | 0.526 |
| crawl4ai | miss | fastapi.tiangolo.com/ | 0.620 | fastapi.tiangolo.com/deployment/versions/ | 0.573 | fastapi.tiangolo.com/features/ | 0.557 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/ | 0.620 | fastapi.tiangolo.com/deployment/versions/ | 0.573 | fastapi.tiangolo.com/features/ | 0.557 |
| scrapy+md | miss | fastapi.tiangolo.com/deployment/versions/ | 0.564 | fastapi.tiangolo.com/ | 0.535 | fastapi.tiangolo.com/contributing/ | 0.526 |
| crawlee | miss | fastapi.tiangolo.com/deployment/versions/ | 0.564 | fastapi.tiangolo.com/ | 0.563 | fastapi.tiangolo.com/reference/fastapi/ | 0.551 |
| colly+md | miss | fastapi.tiangolo.com/deployment/versions/ | 0.564 | fastapi.tiangolo.com/ | 0.535 | fastapi.tiangolo.com/features/ | 0.526 |
| playwright | miss | fastapi.tiangolo.com/deployment/versions/ | 0.564 | fastapi.tiangolo.com/ | 0.563 | fastapi.tiangolo.com/reference/fastapi/ | 0.551 |


**Q11: How do I define nested Pydantic models for request bodies?**
*(expects URL containing: `body-nested-models`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.569 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.538 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.532 |
| crawl4ai | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.581 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.568 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.530 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.581 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.568 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.530 |
| scrapy+md | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.565 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.528 | fastapi.tiangolo.com/features/ | 0.467 |
| crawlee | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.560 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.554 | fastapi.tiangolo.com/features/ | 0.467 |
| colly+md | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.565 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.528 | fastapi.tiangolo.com/features/ | 0.467 |
| playwright | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.560 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.555 | fastapi.tiangolo.com/features/ | 0.467 |


**Q12: How do I handle startup and shutdown events in FastAPI?**
*(expects URL containing: `events`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.513 | fastapi.tiangolo.com/reference/fastapi/ | 0.502 | fastapi.tiangolo.com/features/ | 0.487 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.526 | fastapi.tiangolo.com/features/ | 0.506 | fastapi.tiangolo.com/reference/fastapi/ | 0.501 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.526 | fastapi.tiangolo.com/features/ | 0.506 | fastapi.tiangolo.com/reference/fastapi/ | 0.501 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.525 | fastapi.tiangolo.com/reference/fastapi/ | 0.513 | fastapi.tiangolo.com/features/ | 0.487 |
| crawlee | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.529 | fastapi.tiangolo.com/reference/fastapi/ | 0.515 | fastapi.tiangolo.com/features/ | 0.496 |
| colly+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.525 | fastapi.tiangolo.com/reference/fastapi/ | 0.513 | fastapi.tiangolo.com/features/ | 0.487 |
| playwright | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.529 | fastapi.tiangolo.com/reference/fastapi/ | 0.515 | fastapi.tiangolo.com/features/ | 0.496 |


**Q13: How do I use middleware in FastAPI?**
*(expects URL containing: `middleware`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.677 | fastapi.tiangolo.com/reference/fastapi/ | 0.584 | fastapi.tiangolo.com/reference/fastapi/ | 0.513 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.716 | fastapi.tiangolo.com/reference/fastapi/ | 0.604 | fastapi.tiangolo.com/features/ | 0.534 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.716 | fastapi.tiangolo.com/reference/fastapi/ | 0.604 | fastapi.tiangolo.com/features/ | 0.534 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/reference/fastapi/ | 0.591 | fastapi.tiangolo.com/reference/fastapi/ | 0.530 |
| crawlee | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/fastapi/ | 0.602 | fastapi.tiangolo.com/reference/fastapi/ | 0.533 |
| colly+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/reference/fastapi/ | 0.591 | fastapi.tiangolo.com/reference/fastapi/ | 0.530 |
| playwright | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/fastapi/ | 0.602 | fastapi.tiangolo.com/reference/fastapi/ | 0.533 |


**Q14: How do I use Jinja2 templates in FastAPI?**
*(expects URL containing: `templating`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/features/ | 0.519 | fastapi.tiangolo.com/ | 0.508 | fastapi.tiangolo.com/reference/fastapi/ | 0.475 |
| crawl4ai | miss | fastapi.tiangolo.com/features/ | 0.548 | fastapi.tiangolo.com/reference/openapi/ | 0.512 | fastapi.tiangolo.com/ | 0.510 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/features/ | 0.548 | fastapi.tiangolo.com/reference/openapi/ | 0.512 | fastapi.tiangolo.com/ | 0.510 |
| scrapy+md | miss | fastapi.tiangolo.com/features/ | 0.519 | fastapi.tiangolo.com/ | 0.503 | fastapi.tiangolo.com/reference/fastapi/ | 0.495 |
| crawlee | miss | fastapi.tiangolo.com/features/ | 0.535 | fastapi.tiangolo.com/ | 0.512 | fastapi.tiangolo.com/reference/fastapi/ | 0.504 |
| colly+md | miss | fastapi.tiangolo.com/features/ | 0.519 | fastapi.tiangolo.com/ | 0.503 | fastapi.tiangolo.com/reference/fastapi/ | 0.495 |
| playwright | miss | fastapi.tiangolo.com/features/ | 0.535 | fastapi.tiangolo.com/ | 0.512 | fastapi.tiangolo.com/reference/fastapi/ | 0.504 |


**Q15: How do I deploy FastAPI to the cloud?**
*(expects URL containing: `deployment`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #13 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/ | 0.717 | fastapi.tiangolo.com/ | 0.700 |
| crawl4ai | #6 | fastapi.tiangolo.com/ | 0.757 | fastapi.tiangolo.com/ | 0.738 | fastapi.tiangolo.com/ | 0.710 |
| crawl4ai-raw | #7 | fastapi.tiangolo.com/ | 0.757 | fastapi.tiangolo.com/ | 0.738 | fastapi.tiangolo.com/ | 0.710 |
| scrapy+md | #9 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/ | 0.717 | fastapi.tiangolo.com/ | 0.709 |
| crawlee | #12 | fastapi.tiangolo.com/ | 0.748 | fastapi.tiangolo.com/ | 0.718 | fastapi.tiangolo.com/ | 0.708 |
| colly+md | #15 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/ | 0.717 | fastapi.tiangolo.com/ | 0.709 |
| playwright | #12 | fastapi.tiangolo.com/ | 0.748 | fastapi.tiangolo.com/ | 0.718 | fastapi.tiangolo.com/ | 0.709 |


</details>

## python-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 75 | 20 |
| crawl4ai | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 207 | 20 |
| crawl4ai-raw | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 207 | 20 |
| scrapy+md | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 192 | 14 |
| crawlee | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 198 | 20 |
| colly+md | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 198 | 20 |
| playwright | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 198 | 20 |

<details>
<summary>Query-by-query results for python-docs</summary>

**Q1: What new features were added in Python 3.10?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/ | 0.596 | docs.python.org/3.5/ | 0.540 | docs.python.org/3.11/ | 0.508 |
| crawl4ai | miss | docs.python.org/3.10/ | 0.614 | docs.python.org/3.11/ | 0.532 | docs.python.org/3.5/ | 0.525 |
| crawl4ai-raw | miss | docs.python.org/3.10/ | 0.614 | docs.python.org/3.11/ | 0.532 | docs.python.org/3.5/ | 0.525 |
| scrapy+md | miss | docs.python.org/3.10/ | 0.596 | docs.python.org/3.11/ | 0.508 | docs.python.org/3.10/license.html | 0.489 |
| crawlee | miss | docs.python.org/3.10/ | 0.596 | docs.python.org/3.5/ | 0.514 | docs.python.org/3.11/ | 0.508 |
| colly+md | miss | docs.python.org/3.10/ | 0.596 | docs.python.org/3.5/ | 0.518 | docs.python.org/3.11/ | 0.508 |
| playwright | miss | docs.python.org/3.10/ | 0.596 | docs.python.org/3.5/ | 0.514 | docs.python.org/3.11/ | 0.508 |


**Q2: What does the term 'decorator' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/extending/index.html | 0.308 | docs.python.org/3.10/license.html | 0.303 | docs.python.org/3.10/installing/index.html | 0.303 |
| crawl4ai | miss | docs.python.org/3.10/extending/index.html | 0.324 | docs.python.org/3.10/installing/index.html | 0.316 | docs.python.org/3.10/installing/index.html | 0.312 |
| crawl4ai-raw | miss | docs.python.org/3.10/extending/index.html | 0.324 | docs.python.org/3.10/installing/index.html | 0.316 | docs.python.org/3.10/installing/index.html | 0.312 |
| scrapy+md | miss | docs.python.org/3.14/ | 0.317 | docs.python.org/3.10/ | 0.317 | docs.python.org/3.11/ | 0.317 |
| crawlee | miss | docs.python.org/3.14/ | 0.317 | docs.python.org/3.15/ | 0.317 | docs.python.org/3.10/ | 0.317 |
| colly+md | miss | docs.python.org/3.10/ | 0.317 | docs.python.org/3.13/ | 0.317 | docs.python.org/3.14/ | 0.317 |
| playwright | miss | docs.python.org/3.12/ | 0.317 | docs.python.org/3.11/ | 0.317 | docs.python.org/3.13/ | 0.317 |


**Q3: How do I report a bug in Python?**
*(expects URL containing: `bugs`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/faq/index.html | 0.400 | docs.python.org/2.6/ | 0.363 | docs.python.org/3.1/ | 0.360 |
| crawl4ai | miss | docs.python.org/3.10/faq/index.html | 0.641 | docs.python.org/3.10/faq/index.html | 0.631 | docs.python.org/3.10/installing/index.html | 0.626 |
| crawl4ai-raw | miss | docs.python.org/3.10/faq/index.html | 0.641 | docs.python.org/3.10/faq/index.html | 0.631 | docs.python.org/3.10/installing/index.html | 0.626 |
| scrapy+md | miss | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/library/index.html | 0.589 |
| crawlee | miss | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/installing/index.html | 0.592 | docs.python.org/3.10/library/index.html | 0.590 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/library/index.html | 0.589 |
| playwright | miss | docs.python.org/3.10/installing/index.html | 0.594 | docs.python.org/3.10/installing/index.html | 0.592 | docs.python.org/3.10/library/index.html | 0.590 |


**Q4: What is structural pattern matching in Python?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/license.html | 0.300 | docs.python.org/3.10/c-api/index.html | 0.291 | docs.python.org/3.10/library/index.html | 0.286 |
| crawl4ai | miss | docs.python.org/3.10/reference/index.html | 0.317 | docs.python.org/3.10/reference/index.html | 0.312 | docs.python.org/3.10/library/index.html | 0.310 |
| crawl4ai-raw | miss | docs.python.org/3.10/reference/index.html | 0.317 | docs.python.org/3.10/reference/index.html | 0.312 | docs.python.org/3.10/library/index.html | 0.310 |
| scrapy+md | miss | docs.python.org/3.10/license.html | 0.300 | docs.python.org/3.11/ | 0.289 | docs.python.org/3.14/ | 0.289 |
| crawlee | miss | docs.python.org/3.10/license.html | 0.300 | docs.python.org/3.12/ | 0.289 | docs.python.org/3.11/ | 0.289 |
| colly+md | miss | docs.python.org/3.10/license.html | 0.300 | docs.python.org/3.14/ | 0.289 | docs.python.org/3.11/ | 0.289 |
| playwright | miss | docs.python.org/3.10/license.html | 0.300 | docs.python.org/3.13/ | 0.289 | docs.python.org/3.10/ | 0.289 |


**Q5: What is Python's glossary definition of a generator?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/license.html | 0.366 | docs.python.org/2.6/ | 0.359 | docs.python.org/3.10/license.html | 0.357 |
| crawl4ai | miss | docs.python.org/3.10/faq/index.html | 0.371 | docs.python.org/3.10/faq/index.html | 0.371 | docs.python.org/3.10/reference/index.html | 0.358 |
| crawl4ai-raw | miss | docs.python.org/3.10/faq/index.html | 0.371 | docs.python.org/3.10/faq/index.html | 0.371 | docs.python.org/3.10/reference/index.html | 0.358 |
| scrapy+md | miss | docs.python.org/3.10/library/index.html | 0.394 | docs.python.org/3.10/library/index.html | 0.381 | docs.python.org/3.10/license.html | 0.366 |
| crawlee | miss | docs.python.org/3.10/library/index.html | 0.367 | docs.python.org/3.10/license.html | 0.366 | docs.python.org/3.10/license.html | 0.357 |
| colly+md | miss | docs.python.org/3.10/library/index.html | 0.394 | docs.python.org/3.10/library/index.html | 0.381 | docs.python.org/3.10/license.html | 0.366 |
| playwright | miss | docs.python.org/3.10/library/index.html | 0.366 | docs.python.org/3.10/license.html | 0.366 | docs.python.org/3.10/license.html | 0.357 |


**Q6: What are the Python how-to guides about?**
*(expects URL containing: `howto`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/faq/index.html | 0.572 | docs.python.org/2.7/ | 0.572 | docs.python.org/3.5/ | 0.565 |
| crawl4ai | miss | docs.python.org/3.10/installing/index.html | 0.603 | docs.python.org/3.10/installing/index.html | 0.603 | docs.python.org/3.11/ | 0.580 |
| crawl4ai-raw | miss | docs.python.org/3.10/installing/index.html | 0.603 | docs.python.org/3.10/installing/index.html | 0.603 | docs.python.org/3.11/ | 0.580 |
| scrapy+md | miss | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.11/ | 0.566 |
| crawlee | miss | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.15/ | 0.566 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.10/ | 0.566 |
| playwright | miss | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.10/installing/index.html | 0.597 | docs.python.org/3.14/ | 0.566 |


**Q7: What is the Python module index?**
*(expects URL containing: `py-modindex`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/2.6/ | 0.585 | docs.python.org/3.1/ | 0.582 | docs.python.org/3.2/ | 0.574 |
| crawl4ai | miss | docs.python.org/3.10/installing/index.html | 0.581 | docs.python.org/3.10/installing/index.html | 0.581 | docs.python.org/3.10/installing/index.html | 0.570 |
| crawl4ai-raw | miss | docs.python.org/3.10/installing/index.html | 0.581 | docs.python.org/3.10/installing/index.html | 0.581 | docs.python.org/3.10/installing/index.html | 0.570 |
| scrapy+md | miss | docs.python.org/3.10/installing/index.html | 0.627 | docs.python.org/3.10/installing/index.html | 0.624 | docs.python.org/3.14/ | 0.597 |
| crawlee | miss | docs.python.org/3.10/installing/index.html | 0.605 | docs.python.org/3.10/installing/index.html | 0.602 | docs.python.org/3.15/ | 0.574 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.627 | docs.python.org/3.10/installing/index.html | 0.624 | docs.python.org/3.14/ | 0.597 |
| playwright | miss | docs.python.org/3.10/installing/index.html | 0.605 | docs.python.org/3.10/installing/index.html | 0.602 | docs.python.org/3.15/ | 0.574 |


**Q8: What Python tutorial topics are available?**
*(expects URL containing: `tutorial`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/2.7/ | 0.528 | docs.python.org/3.12/ | 0.526 | docs.python.org/3.5/ | 0.517 |
| crawl4ai | miss | docs.python.org/3.10/installing/index.html | 0.558 | docs.python.org/3.10/installing/index.html | 0.558 | docs.python.org/3.12/ | 0.548 |
| crawl4ai-raw | miss | docs.python.org/3.10/installing/index.html | 0.558 | docs.python.org/3.10/installing/index.html | 0.558 | docs.python.org/3.12/ | 0.548 |
| scrapy+md | miss | docs.python.org/3.11/ | 0.537 | docs.python.org/3.10/ | 0.537 | docs.python.org/3.14/ | 0.537 |
| crawlee | miss | docs.python.org/3.15/ | 0.537 | docs.python.org/3.13/ | 0.537 | docs.python.org/3.11/ | 0.537 |
| colly+md | miss | docs.python.org/3.10/ | 0.537 | docs.python.org/3.11/ | 0.537 | docs.python.org/3.10/ | 0.537 |
| playwright | miss | docs.python.org/3.13/ | 0.537 | docs.python.org/3.14/ | 0.537 | docs.python.org/3.10/ | 0.537 |


**Q9: What is the Python license and copyright?**
*(expects URL containing: `license`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/license.html | 0.613 | docs.python.org/3.10/license.html | 0.593 | docs.python.org/3.10/license.html | 0.559 |
| crawl4ai | #1 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.632 | docs.python.org/3.10/license.html | 0.618 |
| crawl4ai-raw | #1 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.632 | docs.python.org/3.10/license.html | 0.618 |
| scrapy+md | #1 | docs.python.org/3.10/license.html | 0.613 | docs.python.org/3.10/license.html | 0.593 | docs.python.org/3.10/license.html | 0.577 |
| crawlee | #1 | docs.python.org/3.10/license.html | 0.613 | docs.python.org/3.10/license.html | 0.593 | docs.python.org/3.10/license.html | 0.577 |
| colly+md | #1 | docs.python.org/3.10/license.html | 0.613 | docs.python.org/3.10/license.html | 0.593 | docs.python.org/3.10/license.html | 0.577 |
| playwright | #1 | docs.python.org/3.10/license.html | 0.613 | docs.python.org/3.10/license.html | 0.593 | docs.python.org/3.10/license.html | 0.577 |


**Q10: What is the table of contents for Python 3.10 documentation?**
*(expects URL containing: `contents`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.664 | docs.python.org/3.7/ | 0.610 |
| crawl4ai | miss | docs.python.org/3.10/ | 0.686 | docs.python.org/3.10/installing/index.html | 0.610 | docs.python.org/3.10/installing/index.html | 0.610 |
| crawl4ai-raw | miss | docs.python.org/3.10/ | 0.686 | docs.python.org/3.10/installing/index.html | 0.610 | docs.python.org/3.10/installing/index.html | 0.610 |
| scrapy+md | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.11/ | 0.603 | docs.python.org/3.14/ | 0.589 |
| crawlee | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.628 | docs.python.org/3.11/ | 0.603 |
| colly+md | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.636 | docs.python.org/3.11/ | 0.603 |
| playwright | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.628 | docs.python.org/3.11/ | 0.603 |


**Q11: What does the term 'iterable' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/license.html | 0.331 | docs.python.org/3.10/extending/index.html | 0.330 | docs.python.org/3.10/extending/index.html | 0.317 |
| crawl4ai | miss | docs.python.org/3.10/extending/index.html | 0.392 | docs.python.org/3.10/extending/index.html | 0.392 | docs.python.org/3.10/c-api/index.html | 0.360 |
| crawl4ai-raw | miss | docs.python.org/3.10/extending/index.html | 0.392 | docs.python.org/3.10/extending/index.html | 0.392 | docs.python.org/3.10/c-api/index.html | 0.360 |
| scrapy+md | miss | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/license.html | 0.331 |
| crawlee | miss | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/license.html | 0.331 |
| colly+md | miss | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/license.html | 0.331 |
| playwright | miss | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/extending/index.html | 0.355 | docs.python.org/3.10/license.html | 0.331 |


**Q12: How do I install and configure Python on my system?**
*(expects URL containing: `using`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | docs.python.org/3.10/installing/index.html | 0.568 | docs.python.org/3.10/installing/index.html | 0.529 | docs.python.org/3.10/using/index.html | 0.509 |
| crawl4ai | #3 | docs.python.org/3.10/installing/index.html | 0.582 | docs.python.org/3.10/installing/index.html | 0.546 | docs.python.org/3.10/using/index.html | 0.482 |
| crawl4ai-raw | #3 | docs.python.org/3.10/installing/index.html | 0.582 | docs.python.org/3.10/installing/index.html | 0.546 | docs.python.org/3.10/using/index.html | 0.482 |
| scrapy+md | #3 | docs.python.org/3.10/installing/index.html | 0.568 | docs.python.org/3.10/installing/index.html | 0.529 | docs.python.org/3.10/using/index.html | 0.509 |
| crawlee | #3 | docs.python.org/3.10/installing/index.html | 0.568 | docs.python.org/3.10/installing/index.html | 0.529 | docs.python.org/3.10/using/index.html | 0.509 |
| colly+md | #3 | docs.python.org/3.10/installing/index.html | 0.568 | docs.python.org/3.10/installing/index.html | 0.529 | docs.python.org/3.10/using/index.html | 0.509 |
| playwright | #3 | docs.python.org/3.10/installing/index.html | 0.568 | docs.python.org/3.10/installing/index.html | 0.529 | docs.python.org/3.10/using/index.html | 0.509 |


</details>

## react-dev

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 33% (4/12) | 33% (4/12) | 33% (4/12) | 50% (6/12) | 50% (6/12) | 0.351 | 452 | 30 |
| crawl4ai | 25% (3/12) | 25% (3/12) | 33% (4/12) | 50% (6/12) | 50% (6/12) | 0.291 | 547 | 30 |
| crawl4ai-raw | 25% (3/12) | 25% (3/12) | 33% (4/12) | 50% (6/12) | 50% (6/12) | 0.291 | 548 | 30 |
| scrapy+md | 33% (4/12) | 33% (4/12) | 33% (4/12) | 42% (5/12) | 50% (6/12) | 0.350 | 452 | 30 |
| crawlee | 25% (3/12) | 33% (4/12) | 33% (4/12) | 33% (4/12) | 50% (6/12) | 0.306 | 840 | 30 |
| colly+md | 25% (3/12) | 33% (4/12) | 33% (4/12) | 33% (4/12) | 50% (6/12) | 0.306 | 812 | 30 |
| playwright | 25% (3/12) | 33% (4/12) | 33% (4/12) | 33% (4/12) | 50% (6/12) | 0.306 | 812 | 30 |

<details>
<summary>Query-by-query results for react-dev</summary>

**Q1: How do I manage state in a React component?**
*(expects URL containing: `state`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/preserving-and-resetting-state | 0.660 | react.dev/learn/preserving-and-resetting-state | 0.653 |
| crawl4ai | #1 | react.dev/learn/preserving-and-resetting-state | 0.712 | react.dev/learn/preserving-and-resetting-state | 0.663 | react.dev/learn/preserving-and-resetting-state | 0.654 |
| crawl4ai-raw | #1 | react.dev/learn/preserving-and-resetting-state | 0.712 | react.dev/learn/preserving-and-resetting-state | 0.663 | react.dev/learn/preserving-and-resetting-state | 0.658 |
| scrapy+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/passing-data-deeply-with-context | 0.686 | react.dev/learn/preserving-and-resetting-state | 0.686 |
| crawlee | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/preserving-and-resetting-state | 0.653 | react.dev/learn/preserving-and-resetting-state | 0.649 |
| colly+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/preserving-and-resetting-state | 0.661 | react.dev/learn/preserving-and-resetting-state | 0.653 |
| playwright | #1 | react.dev/learn/preserving-and-resetting-state | 0.736 | react.dev/learn/preserving-and-resetting-state | 0.661 | react.dev/learn/preserving-and-resetting-state | 0.653 |


**Q2: What are React hooks and how do I use them?**
*(expects URL containing: `hooks`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 | react.dev/learn/typescript | 0.702 |
| crawl4ai | #4 | react.dev/learn | 0.730 | react.dev/learn/typescript | 0.716 | react.dev/versions | 0.711 |
| crawl4ai-raw | #4 | react.dev/learn | 0.730 | react.dev/learn/typescript | 0.716 | react.dev/versions | 0.711 |
| scrapy+md | #1 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 | react.dev/learn/typescript | 0.702 |
| crawlee | #2 | react.dev/versions | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 |
| colly+md | #2 | react.dev/versions | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 |
| playwright | #2 | react.dev/versions | 0.709 | react.dev/learn/reusing-logic-with-custom-hooks | 0.708 | react.dev/learn | 0.705 |


**Q3: How does the useEffect hook work in React?**
*(expects URL containing: `useEffect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #10 | react.dev/learn/reusing-logic-with-custom-hooks | 0.613 | react.dev/learn/reusing-logic-with-custom-hooks | 0.603 | react.dev/learn | 0.590 |
| crawl4ai | #10 | react.dev/learn | 0.624 | react.dev/learn/reusing-logic-with-custom-hooks | 0.612 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 |
| crawl4ai-raw | #10 | react.dev/learn | 0.624 | react.dev/learn/reusing-logic-with-custom-hooks | 0.612 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 |
| scrapy+md | #8 | react.dev/learn/reusing-logic-with-custom-hooks | 0.613 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 | react.dev/learn | 0.590 |
| crawlee | #12 | react.dev/learn/reusing-logic-with-custom-hooks | 0.613 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 | react.dev/learn | 0.590 |
| colly+md | #12 | react.dev/learn/reusing-logic-with-custom-hooks | 0.613 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 | react.dev/learn | 0.590 |
| playwright | #12 | react.dev/learn/reusing-logic-with-custom-hooks | 0.613 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 | react.dev/learn | 0.590 |


**Q4: How do I handle forms and user input in React?**
*(expects URL containing: `input`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn/state-as-a-snapshot | 0.582 | react.dev/reference/react/useState | 0.574 | react.dev/ | 0.565 |
| crawl4ai | miss | react.dev/learn/state-as-a-snapshot | 0.592 | react.dev/learn/manipulating-the-dom-with-refs | 0.589 | react.dev/reference/react/useState | 0.588 |
| crawl4ai-raw | miss | react.dev/learn/manipulating-the-dom-with-refs | 0.593 | react.dev/learn/state-as-a-snapshot | 0.592 | react.dev/reference/react/useState | 0.589 |
| scrapy+md | miss | react.dev/learn/state-as-a-snapshot | 0.582 | react.dev/learn/manipulating-the-dom-with-refs | 0.575 | react.dev/reference/react/useState | 0.575 |
| crawlee | miss | react.dev/learn/state-as-a-snapshot | 0.582 | react.dev/reference/react/useState | 0.580 | react.dev/ | 0.565 |
| colly+md | miss | react.dev/learn/state-as-a-snapshot | 0.582 | react.dev/learn/manipulating-the-dom-with-refs | 0.575 | react.dev/reference/react/useState | 0.575 |
| playwright | miss | react.dev/learn/state-as-a-snapshot | 0.582 | react.dev/learn/manipulating-the-dom-with-refs | 0.575 | react.dev/reference/react/useState | 0.575 |


**Q5: How do I create and use context in React?**
*(expects URL containing: `context`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 | react.dev/learn/passing-data-deeply-with-context | 0.675 |
| crawl4ai | #1 | react.dev/learn/passing-data-deeply-with-context | 0.737 | react.dev/learn/passing-data-deeply-with-context | 0.712 | react.dev/learn/passing-data-deeply-with-context | 0.709 |
| crawl4ai-raw | #1 | react.dev/learn/passing-data-deeply-with-context | 0.732 | react.dev/learn/passing-data-deeply-with-context | 0.712 | react.dev/learn/passing-data-deeply-with-context | 0.702 |
| scrapy+md | #1 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 | react.dev/learn/passing-data-deeply-with-context | 0.673 |
| crawlee | #1 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 |
| colly+md | #1 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 |
| playwright | #1 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.701 |


**Q6: How do I handle events like clicks in React?**
*(expects URL containing: `event`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #9 | react.dev/learn | 0.669 | react.dev/learn/typescript | 0.568 | react.dev/learn/manipulating-the-dom-with-refs | 0.563 |
| crawl4ai | #7 | react.dev/learn | 0.682 | react.dev/learn/typescript | 0.605 | react.dev/learn/manipulating-the-dom-with-refs | 0.582 |
| crawl4ai-raw | #7 | react.dev/learn | 0.682 | react.dev/learn/typescript | 0.606 | react.dev/learn/manipulating-the-dom-with-refs | 0.583 |
| scrapy+md | #13 | react.dev/learn | 0.668 | react.dev/learn/typescript | 0.571 | react.dev/learn/manipulating-the-dom-with-refs | 0.566 |
| crawlee | #11 | react.dev/learn | 0.668 | react.dev/learn/typescript | 0.571 | react.dev/reference/react/useState | 0.560 |
| colly+md | #11 | react.dev/learn | 0.668 | react.dev/learn/typescript | 0.571 | react.dev/learn/manipulating-the-dom-with-refs | 0.566 |
| playwright | #11 | react.dev/learn | 0.668 | react.dev/learn/typescript | 0.571 | react.dev/learn/manipulating-the-dom-with-refs | 0.566 |


**Q7: What is JSX and how does React use it?**
*(expects URL containing: `jsx`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.656 | react.dev/ | 0.642 | react.dev/learn | 0.623 |
| crawl4ai | miss | react.dev/learn | 0.666 | react.dev/ | 0.652 | react.dev/learn | 0.618 |
| crawl4ai-raw | miss | react.dev/learn | 0.666 | react.dev/ | 0.652 | react.dev/learn | 0.618 |
| scrapy+md | miss | react.dev/learn | 0.653 | react.dev/ | 0.642 | react.dev/learn | 0.622 |
| crawlee | miss | react.dev/learn | 0.653 | react.dev/ | 0.642 | react.dev/learn | 0.625 |
| colly+md | miss | react.dev/learn | 0.653 | react.dev/ | 0.642 | react.dev/learn | 0.622 |
| playwright | miss | react.dev/learn | 0.653 | react.dev/ | 0.642 | react.dev/learn | 0.622 |


**Q8: How do I render lists and use keys in React?**
*(expects URL containing: `list`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.697 | react.dev/learn/preserving-and-resetting-state | 0.579 | react.dev/ | 0.568 |
| crawl4ai | miss | react.dev/learn | 0.716 | react.dev/learn/preserving-and-resetting-state | 0.594 | react.dev/ | 0.584 |
| crawl4ai-raw | miss | react.dev/learn | 0.715 | react.dev/learn/preserving-and-resetting-state | 0.590 | react.dev/ | 0.584 |
| scrapy+md | miss | react.dev/learn | 0.700 | react.dev/learn/preserving-and-resetting-state | 0.584 | react.dev/ | 0.568 |
| crawlee | miss | react.dev/learn | 0.698 | react.dev/learn/preserving-and-resetting-state | 0.585 | react.dev/learn | 0.573 |
| colly+md | miss | react.dev/learn | 0.700 | react.dev/learn/preserving-and-resetting-state | 0.584 | react.dev/learn | 0.573 |
| playwright | miss | react.dev/learn | 0.700 | react.dev/learn/preserving-and-resetting-state | 0.584 | react.dev/learn | 0.573 |


**Q9: How do I use the useRef hook in React?**
*(expects URL containing: `useRef`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/referencing-values-with-refs | 0.716 | react.dev/learn/manipulating-the-dom-with-refs | 0.648 | react.dev/learn/manipulating-the-dom-with-refs | 0.631 |
| crawl4ai | #1 | react.dev/learn/referencing-values-with-refs | 0.721 | react.dev/learn/manipulating-the-dom-with-refs | 0.651 | react.dev/learn/referencing-values-with-refs | 0.648 |
| crawl4ai-raw | #1 | react.dev/learn/referencing-values-with-refs | 0.721 | react.dev/learn/manipulating-the-dom-with-refs | 0.651 | react.dev/learn/referencing-values-with-refs | 0.648 |
| scrapy+md | #1 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/learn/manipulating-the-dom-with-refs | 0.655 | react.dev/learn/manipulating-the-dom-with-refs | 0.630 |
| crawlee | #1 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/learn/manipulating-the-dom-with-refs | 0.655 | react.dev/learn/manipulating-the-dom-with-refs | 0.648 |
| colly+md | #1 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/learn/manipulating-the-dom-with-refs | 0.655 | react.dev/learn/manipulating-the-dom-with-refs | 0.648 |
| playwright | #1 | react.dev/learn/referencing-values-with-refs | 0.719 | react.dev/learn/manipulating-the-dom-with-refs | 0.655 | react.dev/learn/manipulating-the-dom-with-refs | 0.648 |


**Q10: How do I pass props between React components?**
*(expects URL containing: `props`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn/passing-data-deeply-with-context | 0.708 | react.dev/learn/passing-data-deeply-with-context | 0.607 | react.dev/learn | 0.581 |
| crawl4ai | miss | react.dev/learn/passing-data-deeply-with-context | 0.717 | react.dev/learn/passing-data-deeply-with-context | 0.671 | react.dev/learn/passing-data-deeply-with-context | 0.656 |
| crawl4ai-raw | miss | react.dev/learn/passing-data-deeply-with-context | 0.717 | react.dev/learn/passing-data-deeply-with-context | 0.671 | react.dev/learn/passing-data-deeply-with-context | 0.656 |
| scrapy+md | miss | react.dev/learn/passing-data-deeply-with-context | 0.708 | react.dev/learn/passing-data-deeply-with-context | 0.607 | react.dev/learn/reusing-logic-with-custom-hooks | 0.587 |
| crawlee | miss | react.dev/learn/passing-data-deeply-with-context | 0.708 | react.dev/learn/passing-data-deeply-with-context | 0.620 | react.dev/learn/passing-data-deeply-with-context | 0.607 |
| colly+md | miss | react.dev/learn/passing-data-deeply-with-context | 0.708 | react.dev/learn/passing-data-deeply-with-context | 0.620 | react.dev/learn/passing-data-deeply-with-context | 0.607 |
| playwright | miss | react.dev/learn/passing-data-deeply-with-context | 0.708 | react.dev/learn/passing-data-deeply-with-context | 0.620 | react.dev/learn/passing-data-deeply-with-context | 0.607 |


**Q11: How do I conditionally render content in React?**
*(expects URL containing: `conditional`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.746 | react.dev/ | 0.555 | react.dev/learn/react-compiler/introduction | 0.522 |
| crawl4ai | miss | react.dev/learn | 0.734 | react.dev/ | 0.579 | react.dev/reference/react/useState | 0.511 |
| crawl4ai-raw | miss | react.dev/learn | 0.734 | react.dev/ | 0.579 | react.dev/reference/react/useState | 0.511 |
| scrapy+md | miss | react.dev/learn | 0.748 | react.dev/ | 0.555 | react.dev/learn/react-compiler/introduction | 0.510 |
| crawlee | miss | react.dev/learn | 0.748 | react.dev/ | 0.555 | react.dev/reference/react/useState | 0.522 |
| colly+md | miss | react.dev/learn | 0.748 | react.dev/ | 0.555 | react.dev/reference/react/useState | 0.522 |
| playwright | miss | react.dev/learn | 0.748 | react.dev/ | 0.555 | react.dev/reference/react/useState | 0.522 |


**Q12: What is the useMemo hook for in React?**
*(expects URL containing: `useMemo`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.646 | react.dev/learn/react-compiler/introduction | 0.635 |
| crawl4ai | miss | react.dev/learn/react-compiler/introduction | 0.675 | react.dev/learn/typescript | 0.645 | react.dev/learn/react-compiler/introduction | 0.598 |
| crawl4ai-raw | miss | react.dev/learn/react-compiler/introduction | 0.675 | react.dev/learn/typescript | 0.644 | react.dev/learn/react-compiler/introduction | 0.598 |
| scrapy+md | miss | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.642 | react.dev/learn/react-compiler/introduction | 0.636 |
| crawlee | miss | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.642 | react.dev/learn/react-compiler/introduction | 0.636 |
| colly+md | miss | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.642 | react.dev/learn/react-compiler/introduction | 0.636 |
| playwright | miss | react.dev/learn/react-compiler/introduction | 0.649 | react.dev/learn/typescript | 0.642 | react.dev/learn/react-compiler/introduction | 0.636 |


</details>

## wikipedia-python

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 327 | 15 |
| crawl4ai | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 416 | 15 |
| crawl4ai-raw | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 416 | 15 |
| scrapy+md | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 432 | 15 |
| crawlee | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 684 | 15 |
| colly+md | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 452 | 15 |
| playwright | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 60% (6/10) | 0.600 | 452 | 15 |

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


**Q2: What is the history and development of Python?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.642 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.621 | en.wikipedia.org/wiki/Python_(programming_language | 0.579 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.621 | en.wikipedia.org/wiki/Python_(programming_language | 0.579 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.641 | en.wikipedia.org/wiki/Python_(programming_language | 0.602 | en.wikipedia.org/wiki/Python_(programming_language | 0.572 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.631 | en.wikipedia.org/wiki/Python_(programming_language | 0.592 | en.wikipedia.org/wiki/Python_(programming_language | 0.560 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.631 | en.wikipedia.org/wiki/Python_(programming_language | 0.592 | en.wikipedia.org/wiki/Python_(programming_language | 0.560 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.631 | en.wikipedia.org/wiki/Python_(programming_language | 0.592 | en.wikipedia.org/wiki/Python_(programming_language | 0.560 |


**Q3: What programming paradigms does Python support?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.578 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 | en.wikipedia.org/wiki/List_comprehensions | 0.593 | en.wikipedia.org/wiki/Python_(programming_language | 0.570 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.651 | en.wikipedia.org/wiki/List_comprehensions | 0.593 | en.wikipedia.org/wiki/Python_(programming_language | 0.570 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.603 | en.wikipedia.org/wiki/Python_(programming_language | 0.576 | en.wikipedia.org/wiki/Python_(programming_language | 0.571 |


**Q4: What is the Python Software Foundation?**
*(expects URL containing: `Python_Software_Foundation`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.479 | en.wikipedia.org/wiki/Open-source_hardware | 0.460 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.492 | en.wikipedia.org/wiki/Python_(programming_language | 0.466 | en.wikipedia.org/wiki/Python_(programming_language | 0.462 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.492 | en.wikipedia.org/wiki/Python_(programming_language | 0.466 | en.wikipedia.org/wiki/Python_(programming_language | 0.462 |
| scrapy+md | miss | en.wikipedia.org/wiki/Biopython | 0.514 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 |
| crawlee | miss | en.wikipedia.org/wiki/Biopython | 0.506 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.488 |
| colly+md | miss | en.wikipedia.org/wiki/Biopython | 0.514 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 |
| playwright | miss | en.wikipedia.org/wiki/Biopython | 0.514 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 | en.wikipedia.org/wiki/Python_(programming_language | 0.490 |


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


**Q6: What are Python's standard library modules?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.492 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.663 | en.wikipedia.org/wiki/Python_(programming_language | 0.549 | en.wikipedia.org/wiki/Biopython | 0.546 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.663 | en.wikipedia.org/wiki/Python_(programming_language | 0.549 | en.wikipedia.org/wiki/Biopython | 0.546 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Biopython | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.672 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 | en.wikipedia.org/wiki/Biopython | 0.536 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Biopython | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.672 | en.wikipedia.org/wiki/Biopython | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 |


**Q7: Who is Guido van Rossum?**
*(expects URL containing: `Guido_van_Rossum`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.438 | en.wikipedia.org/wiki/Python_(programming_language | 0.430 | en.wikipedia.org/wiki/Python_(programming_language | 0.419 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.423 | en.wikipedia.org/wiki/Python_(programming_language | 0.421 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.423 | en.wikipedia.org/wiki/Python_(programming_language | 0.421 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.461 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.436 | en.wikipedia.org/wiki/Python_(programming_language | 0.432 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.460 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.460 | en.wikipedia.org/wiki/Python_(programming_language | 0.456 | en.wikipedia.org/wiki/Python_(programming_language | 0.426 |


**Q8: What is CPython and how does it work?**
*(expects URL containing: `CPython`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.485 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.505 | en.wikipedia.org/wiki/Python_(programming_language | 0.480 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.516 | en.wikipedia.org/wiki/Python_(programming_language | 0.505 | en.wikipedia.org/wiki/Python_(programming_language | 0.480 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.485 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.485 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.485 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.485 |


**Q9: How does Python compare to other programming languages?**
*(expects URL containing: `Comparison_of_programming_languages`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.659 | en.wikipedia.org/wiki/Python_(programming_language | 0.655 | en.wikipedia.org/wiki/Python_(programming_language | 0.649 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.659 | en.wikipedia.org/wiki/Python_(programming_language | 0.655 | en.wikipedia.org/wiki/Python_(programming_language | 0.649 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.671 | en.wikipedia.org/wiki/Python_(programming_language | 0.665 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |


**Q10: What are Python Enhancement Proposals (PEPs)?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.524 | en.wikipedia.org/wiki/Python_(programming_language | 0.496 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.515 | en.wikipedia.org/wiki/Python_(programming_language | 0.500 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.514 | en.wikipedia.org/wiki/Python_(programming_language | 0.503 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Python_(programming_language | 0.526 | en.wikipedia.org/wiki/Python_(programming_language | 0.489 |


</details>

## stripe-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 0% (0/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.083 | 290 | 25 |
| crawl4ai | 0% (0/10) | 0% (0/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.037 | 352 | 25 |
| crawl4ai-raw | 0% (0/10) | 0% (0/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.037 | 352 | 25 |
| scrapy+md | 0% (0/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.058 | 306 | 25 |
| crawlee | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.120 | 1189 | 25 |
| colly+md | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.120 | 1138 | 25 |
| playwright | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.120 | 1192 | 25 |

<details>
<summary>Query-by-query results for stripe-docs</summary>

**Q1: How do I create a payment intent with Stripe?**
*(expects URL containing: `payment-intent`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | docs.stripe.com/get-started/data-migrations/pan-im | 0.570 | docs.stripe.com/get-started/account/add-funds | 0.570 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.567 |
| crawl4ai | #8 | docs.stripe.com/get-started/data-migrations/pan-im | 0.586 | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/get-started/data-migrations/pan-im | 0.563 |
| crawl4ai-raw | #8 | docs.stripe.com/get-started/data-migrations/pan-im | 0.586 | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/get-started/data-migrations/pan-im | 0.564 |
| scrapy+md | #4 | docs.stripe.com/get-started/account | 0.575 | docs.stripe.com/get-started/data-migrations/pan-im | 0.570 | docs.stripe.com/get-started/account/add-funds | 0.570 |
| crawlee | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/get-started/data-migrations/paymen | 0.609 | docs.stripe.com/get-started/data-migrations/pan-im | 0.588 |
| colly+md | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/get-started/data-migrations/paymen | 0.609 | docs.stripe.com/get-started/data-migrations/pan-im | 0.588 |
| playwright | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.676 | docs.stripe.com/get-started/data-migrations/paymen | 0.609 | docs.stripe.com/get-started/data-migrations/pan-im | 0.588 |


**Q2: How do I handle webhooks from Stripe?**
*(expects URL containing: `webhook`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/agents-billing-workflows | 0.582 | docs.stripe.com/get-started/account/teams | 0.547 | docs.stripe.com/ach-deprecated | 0.522 |
| crawl4ai | miss | docs.stripe.com/agents-billing-workflows | 0.669 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.600 | docs.stripe.com/get-started/account/teams | 0.572 |
| crawl4ai-raw | miss | docs.stripe.com/agents-billing-workflows | 0.669 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.600 | docs.stripe.com/get-started/account/teams | 0.572 |
| scrapy+md | miss | docs.stripe.com/agents-billing-workflows | 0.585 | docs.stripe.com/get-started/account | 0.561 | docs.stripe.com/get-started/account/teams | 0.547 |
| crawlee | miss | docs.stripe.com/agents-billing-workflows | 0.585 | docs.stripe.com/get-started/account | 0.561 | docs.stripe.com/get-started/account/teams | 0.547 |
| colly+md | miss | docs.stripe.com/agents-billing-workflows | 0.585 | docs.stripe.com/get-started/account | 0.561 | docs.stripe.com/get-started/account/teams | 0.547 |
| playwright | miss | docs.stripe.com/agents-billing-workflows | 0.585 | docs.stripe.com/get-started/account | 0.561 | docs.stripe.com/get-started/account/teams | 0.547 |


**Q3: How do I set up Stripe subscriptions?**
*(expects URL containing: `subscription`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/orgs/sharing/c | 0.611 | docs.stripe.com/get-started/data-migrations/pan-im | 0.575 | docs.stripe.com/get-started/account/orgs/setup | 0.564 |
| crawl4ai | miss | docs.stripe.com/get-started/account | 0.644 | docs.stripe.com/get-started/account/activate | 0.612 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.608 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account | 0.644 | docs.stripe.com/get-started/account/activate | 0.612 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.608 |
| scrapy+md | miss | docs.stripe.com/get-started/account | 0.651 | docs.stripe.com/get-started/account/orgs/sharing/c | 0.621 | docs.stripe.com/get-started/account/orgs/setup | 0.585 |
| crawlee | miss | docs.stripe.com/get-started/account | 0.651 | docs.stripe.com/get-started/account/orgs/setup | 0.615 | docs.stripe.com/get-started/account/teams | 0.609 |
| colly+md | miss | docs.stripe.com/get-started/account | 0.651 | docs.stripe.com/get-started/account/orgs/sharing/c | 0.621 | docs.stripe.com/get-started/account/orgs/setup | 0.615 |
| playwright | miss | docs.stripe.com/get-started/account | 0.651 | docs.stripe.com/get-started/account/orgs/setup | 0.615 | docs.stripe.com/get-started/account/teams | 0.609 |


**Q4: How do I authenticate with the Stripe API?**
*(expects URL containing: `authentication`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/activate | 0.609 | docs.stripe.com/get-started/account/orgs/team | 0.604 | docs.stripe.com/get-started/account/linked-externa | 0.581 |
| crawl4ai | miss | docs.stripe.com/get-started/account/activate | 0.643 | docs.stripe.com/get-started/account/orgs/team | 0.627 | docs.stripe.com/get-started/account | 0.626 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account/activate | 0.643 | docs.stripe.com/get-started/account/orgs/team | 0.627 | docs.stripe.com/get-started/account | 0.626 |
| scrapy+md | miss | docs.stripe.com/get-started/account | 0.632 | docs.stripe.com/get-started/account/activate | 0.609 | docs.stripe.com/get-started/account/orgs/team | 0.604 |
| crawlee | miss | docs.stripe.com/get-started/account | 0.632 | docs.stripe.com/get-started/account/activate | 0.622 | docs.stripe.com/get-started/account/activate | 0.609 |
| colly+md | miss | docs.stripe.com/get-started/account | 0.632 | docs.stripe.com/get-started/account/activate | 0.622 | docs.stripe.com/get-started/account/activate | 0.609 |
| playwright | miss | docs.stripe.com/get-started/account | 0.632 | docs.stripe.com/get-started/account/activate | 0.622 | docs.stripe.com/get-started/account/activate | 0.609 |


**Q5: How do I handle errors in the Stripe API?**
*(expects URL containing: `error`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/checklist | 0.527 | docs.stripe.com/get-started/account/checklist | 0.520 | docs.stripe.com/get-started/account/activate | 0.520 |
| crawl4ai | miss | docs.stripe.com/get-started/account | 0.566 | docs.stripe.com/get-started/account/checklist | 0.562 | docs.stripe.com/get-started/account | 0.539 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account | 0.566 | docs.stripe.com/get-started/account/checklist | 0.562 | docs.stripe.com/get-started/account | 0.539 |
| scrapy+md | miss | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/get-started/account/activate | 0.520 | docs.stripe.com/get-started/account | 0.519 |
| crawlee | miss | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.569 | docs.stripe.com/get-started/account/statement-desc | 0.531 |
| colly+md | miss | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.569 | docs.stripe.com/get-started/account/statement-desc | 0.531 |
| playwright | miss | docs.stripe.com/get-started/account | 0.572 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.569 | docs.stripe.com/get-started/account/statement-desc | 0.531 |


**Q6: How do I create a customer in Stripe?**
*(expects URL containing: `customer`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/get-started/account/orgs/sharing/c | 0.627 | docs.stripe.com/get-started/data-migrations/pan-co | 0.609 |
| crawl4ai | #4 | docs.stripe.com/get-started/data-migrations/pan-im | 0.685 | docs.stripe.com/get-started/data-migrations/pan-im | 0.647 | docs.stripe.com/get-started/account | 0.640 |
| crawl4ai-raw | #4 | docs.stripe.com/get-started/data-migrations/pan-im | 0.685 | docs.stripe.com/get-started/data-migrations/pan-im | 0.647 | docs.stripe.com/get-started/account | 0.640 |
| scrapy+md | #3 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/get-started/account | 0.649 | docs.stripe.com/get-started/account/orgs/sharing/c | 0.629 |
| crawlee | #5 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/get-started/account/teams | 0.650 | docs.stripe.com/get-started/account | 0.649 |
| colly+md | #5 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/get-started/account/teams | 0.650 | docs.stripe.com/get-started/account | 0.649 |
| playwright | #5 | docs.stripe.com/get-started/data-migrations/pan-im | 0.689 | docs.stripe.com/get-started/account/teams | 0.650 | docs.stripe.com/get-started/account | 0.649 |


**Q7: How do I process refunds with Stripe?**
*(expects URL containing: `refund`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/get-started/account/add-funds | 0.555 | docs.stripe.com/get-started/account/add-funds | 0.522 |
| crawl4ai | miss | docs.stripe.com/ach-deprecated | 0.618 | docs.stripe.com/get-started/account | 0.571 | docs.stripe.com/get-started/account/add-funds | 0.561 |
| crawl4ai-raw | miss | docs.stripe.com/ach-deprecated | 0.618 | docs.stripe.com/get-started/account | 0.571 | docs.stripe.com/get-started/account/add-funds | 0.561 |
| scrapy+md | miss | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/get-started/account | 0.582 | docs.stripe.com/get-started/account/add-funds | 0.554 |
| crawlee | miss | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/get-started/account | 0.582 | docs.stripe.com/ach-deprecated | 0.558 |
| colly+md | miss | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/get-started/account | 0.582 | docs.stripe.com/ach-deprecated | 0.558 |
| playwright | miss | docs.stripe.com/ach-deprecated | 0.621 | docs.stripe.com/get-started/account | 0.582 | docs.stripe.com/ach-deprecated | 0.558 |


**Q8: How do I use Stripe checkout for payments?**
*(expects URL containing: `checkout`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 | docs.stripe.com/get-started/data-migrations/pan-im | 0.597 |
| crawl4ai | miss | docs.stripe.com/get-started/account | 0.620 | docs.stripe.com/get-started/account/activate | 0.616 | docs.stripe.com/get-started/data-migrations/pan-im | 0.615 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account | 0.620 | docs.stripe.com/get-started/account/activate | 0.616 | docs.stripe.com/get-started/data-migrations/pan-im | 0.615 |
| scrapy+md | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 | docs.stripe.com/get-started/account | 0.615 |
| crawlee | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.680 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 |
| colly+md | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.680 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 |
| playwright | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.680 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.663 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 |


**Q9: How do I test Stripe payments in development?**
*(expects URL containing: `test`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.619 | docs.stripe.com/ach-deprecated | 0.586 | docs.stripe.com/get-started/account/activate | 0.583 |
| crawl4ai | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.679 | docs.stripe.com/get-started/account/activate | 0.597 | docs.stripe.com/get-started/account | 0.584 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.679 | docs.stripe.com/get-started/account/activate | 0.597 | docs.stripe.com/get-started/account | 0.584 |
| scrapy+md | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.619 | docs.stripe.com/get-started/account | 0.586 | docs.stripe.com/ach-deprecated | 0.583 |
| crawlee | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.595 | docs.stripe.com/get-started/account | 0.586 |
| colly+md | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.595 | docs.stripe.com/get-started/account | 0.586 |
| playwright | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.595 | docs.stripe.com/get-started/account | 0.586 |


**Q10: What are Stripe Connect and platform payments?**
*(expects URL containing: `connect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/ach-deprecated | 0.653 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.564 |
| crawl4ai | miss | docs.stripe.com/get-started/account/orgs/setup | 0.657 | docs.stripe.com/ach-deprecated | 0.631 | docs.stripe.com/get-started/account/add-funds | 0.585 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account/orgs/setup | 0.657 | docs.stripe.com/ach-deprecated | 0.631 | docs.stripe.com/get-started/account/add-funds | 0.585 |
| scrapy+md | miss | docs.stripe.com/ach-deprecated | 0.654 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/get-started/account/add-funds | 0.590 |
| crawlee | miss | docs.stripe.com/ach-deprecated | 0.661 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/get-started/account/add-funds | 0.590 |
| colly+md | miss | docs.stripe.com/ach-deprecated | 0.654 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/get-started/account/add-funds | 0.590 |
| playwright | miss | docs.stripe.com/ach-deprecated | 0.661 | docs.stripe.com/get-started/account/orgs/setup | 0.646 | docs.stripe.com/get-started/account/add-funds | 0.590 |


</details>

## blog-engineering

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 285 | 20 |
| crawl4ai | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 652 | 20 |
| crawl4ai-raw | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 652 | 20 |
| scrapy+md | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 414 | 20 |
| crawlee | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 709 | 20 |
| colly+md | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 481 | 15 |
| playwright | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 1.000 | 711 | 20 |

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


**Q3: What monitoring and observability tools do engineering teams use?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.427 | github.blog/news-insights/the-library/exception-mo | 0.412 |
| crawl4ai | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.450 | github.blog/news-insights/the-library/brubeck/ | 0.443 | github.blog/news-insights/the-library/brubeck/ | 0.442 |
| crawl4ai-raw | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.450 | github.blog/news-insights/the-library/brubeck/ | 0.443 | github.blog/news-insights/the-library/brubeck/ | 0.442 |
| scrapy+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.459 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| crawlee | #1 | github.blog/news-insights/the-library/exception-mo | 0.459 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| colly+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.459 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |
| playwright | #1 | github.blog/news-insights/the-library/exception-mo | 0.460 | github.blog/news-insights/company-news/gh-ost-gith | 0.444 | github.blog/news-insights/the-library/brubeck/ | 0.424 |


**Q4: How do you implement continuous deployment pipelines?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/context-awa | 0.405 | github.blog/engineering/infrastructure/building-re | 0.405 | github.blog/engineering/infrastructure/githubs-met | 0.405 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/githubs-met | 0.435 | github.blog/news-insights/the-library/runnable-doc | 0.398 | github.blog/news-insights/the-library/cross-platfo | 0.398 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/githubs-met | 0.435 | github.blog/news-insights/the-library/runnable-doc | 0.398 | github.blog/engineering/engineering-principles/mov | 0.398 |
| scrapy+md | #1 | github.blog/news-insights/the-library/runnable-doc | 0.377 | github.blog/engineering/platform-security/syn-floo | 0.375 | github.blog/engineering/infrastructure/building-re | 0.375 |
| crawlee | #1 | github.blog/engineering/infrastructure/githubs-met | 0.393 | github.blog/news-insights/the-library/cross-platfo | 0.393 | github.blog/engineering/infrastructure/context-awa | 0.393 |
| colly+md | #1 | github.blog/latest/ | 0.385 | github.blog/engineering/infrastructure/githubs-met | 0.385 | github.blog/engineering/user-experience/like-injec | 0.385 |
| playwright | #1 | github.blog/engineering/infrastructure/context-awa | 0.393 | github.blog/news-insights/the-library/brubeck/ | 0.393 | github.blog/engineering/infrastructure/githubs-met | 0.393 |


**Q5: What are common microservices architecture patterns?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/latest/ | 0.350 | github.blog/engineering/architecture-optimization/ | 0.337 | github.blog/engineering/user-experience/like-injec | 0.337 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/context-awa | 0.347 | github.blog/engineering/infrastructure/githubs-met | 0.313 | github.blog/engineering/engineering-principles/scr | 0.304 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/context-awa | 0.347 | github.blog/engineering/infrastructure/githubs-met | 0.313 | github.blog/engineering/engineering-principles/scr | 0.304 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/context-awa | 0.337 | github.blog/engineering/engineering-principles/scr | 0.337 | github.blog/engineering/user-experience/like-injec | 0.337 |
| crawlee | #1 | github.blog/engineering/architecture-optimization/ | 0.337 | github.blog/engineering/user-experience/like-injec | 0.337 | github.blog/engineering/infrastructure/building-re | 0.337 |
| colly+md | #1 | github.blog/engineering/infrastructure/githubs-met | 0.337 | github.blog/engineering/platform-security/syn-floo | 0.337 | github.blog/engineering/user-experience/like-injec | 0.337 |
| playwright | #1 | github.blog/engineering/platform-security/syn-floo | 0.337 | github.blog/engineering/infrastructure/context-awa | 0.337 | github.blog/engineering/infrastructure/orchestrato | 0.337 |


**Q6: How do you handle API versioning in production?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/engineering-principles/mov | 0.337 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/engineering/infrastructure/orchestrato | 0.330 |
| crawl4ai | #1 | github.blog/news-insights/the-library/runnable-doc | 0.349 | github.blog/engineering/engineering-principles/mov | 0.347 | github.blog/engineering/engineering-principles/mov | 0.342 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/runnable-doc | 0.349 | github.blog/engineering/engineering-principles/mov | 0.347 | github.blog/engineering/engineering-principles/mov | 0.342 |
| scrapy+md | #1 | github.blog/engineering/engineering-principles/mov | 0.333 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/engineering/infrastructure/orchestrato | 0.330 |
| crawlee | #1 | github.blog/engineering/engineering-principles/mov | 0.333 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/engineering/infrastructure/orchestrato | 0.330 |
| colly+md | #1 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/news-insights/the-library/exception-mo | 0.329 | github.blog/news-insights/company-news/gh-ost-gith | 0.328 |
| playwright | #1 | github.blog/engineering/engineering-principles/mov | 0.333 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/engineering/infrastructure/orchestrato | 0.330 |


**Q7: What caching strategies work best for web applications?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/latest/ | 0.412 | github.blog/engineering/user-experience/like-injec | 0.366 | github.blog/engineering/infrastructure/context-awa | 0.366 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/context-awa | 0.326 | github.blog/news-insights/company-news/gh-ost-gith | 0.315 | github.blog/security/subresource-integrity/ | 0.308 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/context-awa | 0.326 | github.blog/news-insights/company-news/gh-ost-gith | 0.315 | github.blog/security/subresource-integrity/ | 0.308 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/githubs-met | 0.366 | github.blog/engineering/engineering-principles/mov | 0.366 | github.blog/engineering/user-experience/like-injec | 0.366 |
| crawlee | #1 | github.blog/engineering/engineering-principles/mov | 0.366 | github.blog/engineering/engineering-principles/scr | 0.366 | github.blog/engineering/infrastructure/context-awa | 0.366 |
| colly+md | #1 | github.blog/engineering/engineering-principles/scr | 0.366 | github.blog/engineering/infrastructure/context-awa | 0.366 | github.blog/engineering/infrastructure/building-re | 0.366 |
| playwright | #1 | github.blog/engineering/engineering-principles/mov | 0.366 | github.blog/engineering/infrastructure/githubs-met | 0.366 | github.blog/engineering/infrastructure/building-re | 0.366 |


**Q8: How do you design for high availability and fault tolerance?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.491 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/orchestrato | 0.434 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/building-re | 0.507 | github.blog/engineering/infrastructure/orchestrato | 0.485 | github.blog/engineering/infrastructure/orchestrato | 0.467 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/building-re | 0.507 | github.blog/engineering/infrastructure/orchestrato | 0.485 | github.blog/engineering/infrastructure/orchestrato | 0.467 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/orchestrato | 0.434 |
| crawlee | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/orchestrato | 0.434 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/context-awa | 0.430 | github.blog/engineering/infrastructure/building-re | 0.428 |
| playwright | #1 | github.blog/engineering/infrastructure/building-re | 0.487 | github.blog/engineering/infrastructure/orchestrato | 0.450 | github.blog/engineering/infrastructure/orchestrato | 0.434 |


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

