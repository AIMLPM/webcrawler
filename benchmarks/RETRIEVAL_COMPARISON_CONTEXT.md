# Retrieval Quality Comparison

<!-- style: v2, 2026-04-07 -->

Does each tool's output produce embeddings that answer real questions?
This benchmark chunks each tool's crawl output, embeds it with
`text-embedding-3-small`, and measures retrieval across four modes:

- **Embedding**: Cosine similarity on OpenAI embeddings
- **BM25**: Keyword search (Okapi BM25)
- **Hybrid**: Embedding + BM25 fused via Reciprocal Rank Fusion
- **Reranked**: Hybrid candidates reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2`

**92 queries** across 8 sites.
Hit rate = correct source page in top-K results. Higher is better.

## Summary: retrieval modes compared

| Tool | Mode | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR |
|---|---|---|---|---|---|---|---|
| markcrawl | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 0.452 |
| markcrawl | bm25 | 29% (27/92) ±9% | 39% (36/92) ±10% | 43% (40/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 0.355 |
| markcrawl | hybrid | 40% (37/92) ±10% | 49% (45/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.447 |
| markcrawl | reranked | 41% (38/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.452 |
| crawl4ai | embedding | 43% (40/92) ±10% | 46% (42/92) ±10% | 46% (42/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.450 |
| crawl4ai | bm25 | 24% (22/92) ±9% | 30% (28/92) ±9% | 35% (32/92) ±10% | 39% (36/92) ±10% | 50% (46/92) ±10% | 0.290 |
| crawl4ai | hybrid | 42% (39/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.452 |
| crawl4ai | reranked | 40% (37/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.437 |
| crawl4ai-raw | embedding | 43% (40/92) ±10% | 46% (42/92) ±10% | 46% (42/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.450 |
| crawl4ai-raw | bm25 | 24% (22/92) ±9% | 30% (28/92) ±9% | 35% (32/92) ±10% | 39% (36/92) ±10% | 50% (46/92) ±10% | 0.289 |
| crawl4ai-raw | hybrid | 42% (39/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 51% (47/92) ±10% | 0.452 |
| crawl4ai-raw | reranked | 40% (37/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.437 |
| scrapy+md | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.452 |
| scrapy+md | bm25 | 28% (26/92) ±9% | 37% (34/92) ±10% | 42% (39/92) ±10% | 48% (44/92) ±10% | 50% (46/92) ±10% | 0.346 |
| scrapy+md | hybrid | 45% (41/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 50% (46/92) ±10% | 0.462 |
| scrapy+md | reranked | 39% (36/92) ±10% | 49% (45/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.441 |
| crawlee | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.450 |
| crawlee | bm25 | 28% (26/92) ±9% | 36% (33/92) ±10% | 40% (37/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 0.338 |
| crawlee | hybrid | 41% (38/92) ±10% | 46% (42/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.445 |
| crawlee | reranked | 39% (36/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.439 |
| colly+md | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.451 |
| colly+md | bm25 | 27% (25/92) ±9% | 36% (33/92) ±10% | 40% (37/92) ±10% | 45% (41/92) ±10% | 49% (45/92) ±10% | 0.331 |
| colly+md | hybrid | 40% (37/92) ±10% | 46% (42/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.437 |
| colly+md | reranked | 41% (38/92) ±10% | 48% (44/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.450 |
| playwright | embedding | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.452 |
| playwright | bm25 | 28% (26/92) ±9% | 37% (34/92) ±10% | 40% (37/92) ±10% | 46% (42/92) ±10% | 49% (45/92) ±10% | 0.339 |
| playwright | hybrid | 41% (38/92) ±10% | 46% (42/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.444 |
| playwright | reranked | 39% (36/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 51% (47/92) ±10% | 0.438 |


## Summary: embedding-only (hit rate at multiple K values)

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Avg words |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 50% (46/92) ±10% | 0.452 | 2126 | 158 |
| crawl4ai | 43% (40/92) ±10% | 46% (42/92) ±10% | 46% (42/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.450 | 3539 | 154 |
| crawl4ai-raw | 43% (40/92) ±10% | 46% (42/92) ±10% | 46% (42/92) ±10% | 48% (44/92) ±10% | 51% (47/92) ±10% | 0.450 | 3540 | 154 |
| scrapy+md | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.452 | 2574 | 158 |
| crawlee | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.450 | 4422 | 243 |
| colly+md | 43% (40/92) ±10% | 47% (43/92) ±10% | 48% (44/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.451 | 3884 | 231 |
| playwright | 43% (40/92) ±10% | 47% (43/92) ±10% | 47% (43/92) ±10% | 49% (45/92) ±10% | 51% (47/92) ±10% | 0.452 | 4167 | 235 |


## quotes-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 33% (4/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.361 | 24 | 15 |
| crawl4ai | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.417 | 22 | 15 |
| crawl4ai-raw | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.417 | 22 | 15 |
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
| markcrawl | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.457 |
| crawl4ai | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.578 | quotes.toscrape.com/author/Albert-Einstein | 0.556 | quotes.toscrape.com/author/Albert-Einstein | 0.409 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.578 | quotes.toscrape.com/author/Albert-Einstein | 0.556 | quotes.toscrape.com/author/Albert-Einstein | 0.409 |
| scrapy+md | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.574 | quotes.toscrape.com/author/Albert-Einstein/ | 0.574 | quotes.toscrape.com/author/Albert-Einstein/ | 0.457 |
| crawlee | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.457 |
| colly+md | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.570 | quotes.toscrape.com/author/Albert-Einstein/ | 0.558 | quotes.toscrape.com/author/Albert-Einstein/ | 0.453 |
| playwright | #1 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.574 | quotes.toscrape.com/author/Albert-Einstein | 0.457 |


**Q2: Which quotes are tagged with 'inspirational'?**
*(expects URL containing: `tag/inspirational`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/ | 0.583 | quotes.toscrape.com/tag/life/ | 0.575 | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.569 |
| crawl4ai | miss | quotes.toscrape.com/ | 0.581 | quotes.toscrape.com/tag/edison/page/1/ | 0.575 | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.571 |
| crawl4ai-raw | miss | quotes.toscrape.com/ | 0.581 | quotes.toscrape.com/tag/edison/page/1/ | 0.575 | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.571 |
| scrapy+md | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.574 | quotes.toscrape.com/ | 0.572 | quotes.toscrape.com/tag/edison/page/1/ | 0.567 |
| crawlee | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.572 | quotes.toscrape.com/ | 0.572 | quotes.toscrape.com/tag/edison/page/1/ | 0.566 |
| colly+md | miss | quotes.toscrape.com/ | 0.576 | quotes.toscrape.com/tag/edison/page/1/ | 0.572 | quotes.toscrape.com/tag/miracles/page/1/ | 0.568 |
| playwright | miss | quotes.toscrape.com/tag/paraphrased/page/1/ | 0.572 | quotes.toscrape.com/ | 0.572 | quotes.toscrape.com/tag/edison/page/1/ | 0.566 |


**Q3: What did Jane Austen say about novels and reading?**
*(expects URL containing: `author/Jane-Austen`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/author/J-K-Rowling | 0.361 | quotes.toscrape.com/author/J-K-Rowling | 0.334 | quotes.toscrape.com/tag/humor/ | 0.327 |
| crawl4ai | miss | quotes.toscrape.com/author/J-K-Rowling | 0.379 | quotes.toscrape.com/author/J-K-Rowling | 0.329 | quotes.toscrape.com/ | 0.306 |
| crawl4ai-raw | miss | quotes.toscrape.com/author/J-K-Rowling | 0.379 | quotes.toscrape.com/author/J-K-Rowling | 0.329 | quotes.toscrape.com/ | 0.307 |
| scrapy+md | miss | quotes.toscrape.com/author/J-K-Rowling/ | 0.361 | quotes.toscrape.com/author/J-K-Rowling/ | 0.334 | quotes.toscrape.com/tag/humor/ | 0.334 |
| crawlee | miss | quotes.toscrape.com/author/J-K-Rowling | 0.361 | quotes.toscrape.com/author/J-K-Rowling | 0.334 | quotes.toscrape.com/tag/humor/ | 0.324 |
| colly+md | miss | quotes.toscrape.com/author/J-K-Rowling/ | 0.340 | quotes.toscrape.com/author/J-K-Rowling/ | 0.320 | quotes.toscrape.com/tag/humor/ | 0.320 |
| playwright | miss | quotes.toscrape.com/author/J-K-Rowling | 0.361 | quotes.toscrape.com/author/J-K-Rowling | 0.334 | quotes.toscrape.com/tag/humor/ | 0.324 |


**Q4: What quotes are about the truth?**
*(expects URL containing: `tag/truth`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/life/ | 0.493 | quotes.toscrape.com/tag/life/ | 0.479 | quotes.toscrape.com/ | 0.478 |
| crawl4ai | miss | quotes.toscrape.com/ | 0.466 | quotes.toscrape.com/tag/humor/ | 0.456 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.449 |
| crawl4ai-raw | miss | quotes.toscrape.com/ | 0.466 | quotes.toscrape.com/tag/humor/ | 0.456 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.449 |
| scrapy+md | miss | quotes.toscrape.com/tag/life/ | 0.493 | quotes.toscrape.com/ | 0.464 | quotes.toscrape.com/tag/life/ | 0.461 |
| crawlee | miss | quotes.toscrape.com/tag/life/ | 0.493 | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.461 |
| colly+md | miss | quotes.toscrape.com/ | 0.457 | quotes.toscrape.com/tag/life/ | 0.456 | quotes.toscrape.com/tag/friends/ | 0.435 |
| playwright | miss | quotes.toscrape.com/tag/life/ | 0.493 | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/life/ | 0.461 |


**Q5: Which quotes are about humor and being funny?**
*(expects URL containing: `tag/humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/humor/ | 0.531 | quotes.toscrape.com/ | 0.465 | quotes.toscrape.com/tag/life/ | 0.449 |
| crawl4ai | #1 | quotes.toscrape.com/tag/humor/ | 0.518 | quotes.toscrape.com/ | 0.441 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.426 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/humor/ | 0.518 | quotes.toscrape.com/ | 0.441 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.426 |
| scrapy+md | #1 | quotes.toscrape.com/tag/humor/ | 0.519 | quotes.toscrape.com/tag/life/ | 0.449 | quotes.toscrape.com/ | 0.440 |
| crawlee | #1 | quotes.toscrape.com/tag/humor/ | 0.515 | quotes.toscrape.com/tag/life/ | 0.449 | quotes.toscrape.com/ | 0.437 |
| colly+md | #1 | quotes.toscrape.com/tag/humor/ | 0.511 | quotes.toscrape.com/ | 0.434 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.413 |
| playwright | #1 | quotes.toscrape.com/tag/humor/ | 0.515 | quotes.toscrape.com/tag/life/ | 0.449 | quotes.toscrape.com/ | 0.437 |


**Q6: What did J.K. Rowling say about choices and abilities?**
*(expects URL containing: `author/J-K-Rowling`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.534 | quotes.toscrape.com/tag/abilities/page/1/ | 0.534 | quotes.toscrape.com/author/J-K-Rowling | 0.527 |
| crawl4ai | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.548 | quotes.toscrape.com/author/J-K-Rowling | 0.526 | quotes.toscrape.com/tag/abilities/page/1/ | 0.506 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.548 | quotes.toscrape.com/author/J-K-Rowling | 0.526 | quotes.toscrape.com/tag/abilities/page/1/ | 0.506 |
| scrapy+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.534 | quotes.toscrape.com/author/J-K-Rowling/ | 0.527 | quotes.toscrape.com/tag/abilities/page/1/ | 0.522 |
| crawlee | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.534 | quotes.toscrape.com/author/J-K-Rowling | 0.527 | quotes.toscrape.com/tag/abilities/page/1/ | 0.496 |
| colly+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.527 | quotes.toscrape.com/author/J-K-Rowling/ | 0.517 | quotes.toscrape.com/tag/abilities/page/1/ | 0.485 |
| playwright | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.534 | quotes.toscrape.com/author/J-K-Rowling | 0.527 | quotes.toscrape.com/tag/abilities/page/1/ | 0.496 |


**Q7: What quotes are tagged with 'change'?**
*(expects URL containing: `tag/change`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/world/page/1/ | 0.514 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.504 | quotes.toscrape.com/ | 0.489 |
| crawl4ai | miss | quotes.toscrape.com/tag/world/page/1/ | 0.532 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.521 | quotes.toscrape.com/ | 0.492 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/world/page/1/ | 0.531 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.521 | quotes.toscrape.com/ | 0.492 |
| scrapy+md | miss | quotes.toscrape.com/tag/world/page/1/ | 0.523 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.515 | quotes.toscrape.com/ | 0.489 |
| crawlee | miss | quotes.toscrape.com/tag/world/page/1/ | 0.514 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.506 | quotes.toscrape.com/ | 0.489 |
| colly+md | miss | quotes.toscrape.com/tag/world/page/1/ | 0.508 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.505 | quotes.toscrape.com/ | 0.488 |
| playwright | miss | quotes.toscrape.com/tag/world/page/1/ | 0.514 | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.506 | quotes.toscrape.com/ | 0.489 |


**Q8: What did Steve Martin say about sunshine?**
*(expects URL containing: `author/Steve-Martin`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/simile/ | 0.338 | quotes.toscrape.com/tag/humor/ | 0.326 | quotes.toscrape.com/ | 0.314 |
| crawl4ai | miss | quotes.toscrape.com/tag/simile/ | 0.355 | quotes.toscrape.com/tag/humor/ | 0.306 | quotes.toscrape.com/author/Albert-Einstein | 0.282 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/simile/ | 0.355 | quotes.toscrape.com/tag/humor/ | 0.306 | quotes.toscrape.com/author/Albert-Einstein | 0.282 |
| scrapy+md | miss | quotes.toscrape.com/tag/simile/ | 0.354 | quotes.toscrape.com/tag/humor/ | 0.313 | quotes.toscrape.com/ | 0.295 |
| crawlee | miss | quotes.toscrape.com/tag/simile/ | 0.335 | quotes.toscrape.com/tag/humor/ | 0.306 | quotes.toscrape.com/ | 0.289 |
| colly+md | miss | quotes.toscrape.com/tag/simile/ | 0.326 | quotes.toscrape.com/tag/humor/ | 0.302 | quotes.toscrape.com/ | 0.289 |
| playwright | miss | quotes.toscrape.com/tag/simile/ | 0.335 | quotes.toscrape.com/tag/humor/ | 0.306 | quotes.toscrape.com/ | 0.289 |


**Q9: Which quotes talk about believing in yourself?**
*(expects URL containing: `tag/be-yourself`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | quotes.toscrape.com/tag/life/ | 0.518 | quotes.toscrape.com/tag/life/ | 0.492 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.452 |
| crawl4ai | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.474 | quotes.toscrape.com/tag/life/ | 0.444 | quotes.toscrape.com/tag/abilities/page/1/ | 0.441 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.474 | quotes.toscrape.com/tag/life/ | 0.444 | quotes.toscrape.com/tag/abilities/page/1/ | 0.441 |
| scrapy+md | #3 | quotes.toscrape.com/tag/life/ | 0.503 | quotes.toscrape.com/tag/life/ | 0.492 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.455 |
| crawlee | #3 | quotes.toscrape.com/tag/life/ | 0.503 | quotes.toscrape.com/tag/life/ | 0.492 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.448 |
| colly+md | #3 | quotes.toscrape.com/tag/life/ | 0.452 | quotes.toscrape.com/tag/life/ | 0.450 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.448 |
| playwright | #3 | quotes.toscrape.com/tag/life/ | 0.503 | quotes.toscrape.com/tag/life/ | 0.492 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.448 |


**Q10: What are the quotes about miracles and living life?**
*(expects URL containing: `tag/miracle`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.621 | quotes.toscrape.com/tag/life/ | 0.575 | quotes.toscrape.com/tag/life/ | 0.518 |
| crawl4ai | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.651 | quotes.toscrape.com/tag/life/ | 0.522 | quotes.toscrape.com/tag/life/ | 0.482 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.651 | quotes.toscrape.com/tag/life/ | 0.522 | quotes.toscrape.com/tag/life/ | 0.482 |
| scrapy+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.634 | quotes.toscrape.com/tag/life/ | 0.575 | quotes.toscrape.com/tag/life/ | 0.511 |
| crawlee | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.631 | quotes.toscrape.com/tag/life/ | 0.575 | quotes.toscrape.com/tag/life/ | 0.511 |
| colly+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.625 | quotes.toscrape.com/tag/life/ | 0.545 | quotes.toscrape.com/ | 0.465 |
| playwright | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.631 | quotes.toscrape.com/tag/life/ | 0.575 | quotes.toscrape.com/tag/life/ | 0.511 |


**Q11: What quotes are about thinking deeply?**
*(expects URL containing: `tag/thinking`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.551 | quotes.toscrape.com/tag/life/ | 0.501 | quotes.toscrape.com/ | 0.489 |
| crawl4ai | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.579 | quotes.toscrape.com/tag/world/page/1/ | 0.512 | quotes.toscrape.com/ | 0.497 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.579 | quotes.toscrape.com/tag/world/page/1/ | 0.512 | quotes.toscrape.com/ | 0.497 |
| scrapy+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.565 | quotes.toscrape.com/ | 0.502 | quotes.toscrape.com/tag/world/page/1/ | 0.500 |
| crawlee | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.555 | quotes.toscrape.com/ | 0.500 | quotes.toscrape.com/tag/world/page/1/ | 0.494 |
| colly+md | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.563 | quotes.toscrape.com/ | 0.490 | quotes.toscrape.com/tag/world/page/1/ | 0.477 |
| playwright | miss | quotes.toscrape.com/tag/deep-thoughts/page/1/ | 0.555 | quotes.toscrape.com/ | 0.500 | quotes.toscrape.com/tag/world/page/1/ | 0.494 |


**Q12: What quotes talk about living life fully?**
*(expects URL containing: `tag/live`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | quotes.toscrape.com/tag/life/ | 0.609 | quotes.toscrape.com/tag/life/ | 0.596 | quotes.toscrape.com/ | 0.467 |
| crawl4ai | miss | quotes.toscrape.com/tag/life/ | 0.572 | quotes.toscrape.com/tag/life/ | 0.531 | quotes.toscrape.com/tag/life/ | 0.493 |
| crawl4ai-raw | miss | quotes.toscrape.com/tag/life/ | 0.572 | quotes.toscrape.com/tag/life/ | 0.531 | quotes.toscrape.com/tag/life/ | 0.493 |
| scrapy+md | miss | quotes.toscrape.com/tag/life/ | 0.604 | quotes.toscrape.com/tag/life/ | 0.596 | quotes.toscrape.com/ | 0.467 |
| crawlee | miss | quotes.toscrape.com/tag/life/ | 0.604 | quotes.toscrape.com/tag/life/ | 0.596 | quotes.toscrape.com/tag/life/ | 0.530 |
| colly+md | miss | quotes.toscrape.com/tag/life/ | 0.561 | quotes.toscrape.com/tag/life/ | 0.553 | quotes.toscrape.com/tag/life/ | 0.524 |
| playwright | miss | quotes.toscrape.com/tag/life/ | 0.604 | quotes.toscrape.com/tag/life/ | 0.596 | quotes.toscrape.com/tag/life/ | 0.530 |


</details>

## books-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 124 | 60 |
| crawl4ai | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 667 | 60 |
| crawl4ai-raw | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 667 | 60 |
| scrapy+md | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |
| crawlee | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |
| colly+md | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |
| playwright | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 1.000 | 135 | 60 |

<details>
<summary>Query-by-query results for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.504 | books.toscrape.com/ | 0.484 | books.toscrape.com/catalogue/category/books/young- | 0.481 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/young- | 0.489 | books.toscrape.com/catalogue/category/books/young- | 0.489 | books.toscrape.com/catalogue/category/books/young- | 0.489 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/young- | 0.489 | books.toscrape.com/catalogue/category/books/young- | 0.489 | books.toscrape.com/catalogue/category/books/young- | 0.489 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.504 | books.toscrape.com/ | 0.492 | books.toscrape.com/catalogue/category/books/young- | 0.483 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.500 | books.toscrape.com/ | 0.492 | books.toscrape.com/catalogue/category/books/young- | 0.490 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/young- | 0.505 | books.toscrape.com/catalogue/category/books/defaul | 0.502 | books.toscrape.com/ | 0.480 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.500 | books.toscrape.com/ | 0.492 | books.toscrape.com/catalogue/category/books/young- | 0.490 |


**Q2: What mystery and thriller books are in the catalog?**
*(expects URL containing: `mystery`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.601 | books.toscrape.com/catalogue/category/books/myster | 0.576 | books.toscrape.com/catalogue/category/books/myster | 0.550 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.644 | books.toscrape.com/catalogue/category/books/myster | 0.643 | books.toscrape.com/catalogue/category/books/myster | 0.637 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.644 | books.toscrape.com/catalogue/category/books/myster | 0.643 | books.toscrape.com/catalogue/category/books/myster | 0.637 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.581 | books.toscrape.com/catalogue/category/books/myster | 0.563 | books.toscrape.com/catalogue/category/books/myster | 0.550 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/myster | 0.593 | books.toscrape.com/catalogue/category/books/myster | 0.562 | books.toscrape.com/catalogue/category/books/myster | 0.539 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.594 | books.toscrape.com/catalogue/category/books/myster | 0.574 | books.toscrape.com/catalogue/category/books/myster | 0.572 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/myster | 0.593 | books.toscrape.com/catalogue/category/books/myster | 0.562 | books.toscrape.com/catalogue/category/books/myster | 0.539 |


**Q3: What is the rating of the most expensive book?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.410 | books.toscrape.com/catalogue/category/books/young- | 0.400 | books.toscrape.com/ | 0.394 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/adult- | 0.433 | books.toscrape.com/catalogue/soumission_998/index. | 0.391 | books.toscrape.com/catalogue/category/books/suspen | 0.390 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/adult- | 0.433 | books.toscrape.com/catalogue/soumission_998/index. | 0.391 | books.toscrape.com/catalogue/category/books/suspen | 0.390 |
| scrapy+md | #1 | books.toscrape.com/ | 0.415 | books.toscrape.com/catalogue/category/books/adult- | 0.411 | books.toscrape.com/catalogue/category/books/defaul | 0.410 |
| crawlee | #1 | books.toscrape.com/ | 0.415 | books.toscrape.com/catalogue/category/books/defaul | 0.415 | books.toscrape.com/catalogue/category/books/young- | 0.411 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/young- | 0.421 | books.toscrape.com/catalogue/category/books/defaul | 0.419 | books.toscrape.com/catalogue/category/books/adult- | 0.413 |
| playwright | #1 | books.toscrape.com/ | 0.415 | books.toscrape.com/catalogue/category/books/defaul | 0.415 | books.toscrape.com/catalogue/category/books/young- | 0.411 |


**Q4: What science fiction books are available?**
*(expects URL containing: `science-fiction`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.523 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.491 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.473 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.584 | books.toscrape.com/catalogue/category/books/scienc | 0.574 | books.toscrape.com/catalogue/category/books/scienc | 0.570 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.584 | books.toscrape.com/catalogue/category/books/scienc | 0.574 | books.toscrape.com/catalogue/category/books/scienc | 0.570 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.528 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.491 | books.toscrape.com/catalogue/category/books/scienc | 0.487 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.521 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.491 | books.toscrape.com/catalogue/category/books/scienc | 0.491 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.551 | books.toscrape.com/catalogue/category/books/scienc | 0.494 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.470 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.521 | books.toscrape.com/catalogue/mesaerion-the-best-sc | 0.491 | books.toscrape.com/catalogue/category/books/scienc | 0.491 |


**Q5: What horror books are in the catalog?**
*(expects URL containing: `horror`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/horror | 0.587 | books.toscrape.com/catalogue/category/books/suspen | 0.475 | books.toscrape.com/catalogue/category/books/thrill | 0.459 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/horror | 0.652 | books.toscrape.com/catalogue/category/books/horror | 0.647 | books.toscrape.com/catalogue/category/books/horror | 0.633 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/horror | 0.654 | books.toscrape.com/catalogue/category/books/horror | 0.648 | books.toscrape.com/catalogue/category/books/horror | 0.634 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.575 | books.toscrape.com/catalogue/category/books/horror | 0.567 | books.toscrape.com/ | 0.469 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/horror | 0.587 | books.toscrape.com/catalogue/category/books/horror | 0.561 | books.toscrape.com/ | 0.470 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.600 | books.toscrape.com/catalogue/category/books/horror | 0.600 | books.toscrape.com/catalogue/category/books/suspen | 0.485 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/horror | 0.587 | books.toscrape.com/catalogue/category/books/horror | 0.561 | books.toscrape.com/ | 0.470 |


**Q6: What poetry books can I find?**
*(expects URL containing: `poetry`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.564 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.399 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.386 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.586 | books.toscrape.com/catalogue/category/books/poetry | 0.580 | books.toscrape.com/catalogue/category/books/poetry | 0.579 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.586 | books.toscrape.com/catalogue/category/books/poetry | 0.580 | books.toscrape.com/catalogue/category/books/poetry | 0.579 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.565 | books.toscrape.com/catalogue/category/books/poetry | 0.506 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.402 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.554 | books.toscrape.com/catalogue/category/books/poetry | 0.511 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.409 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.586 | books.toscrape.com/catalogue/category/books/poetry | 0.527 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.413 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.554 | books.toscrape.com/catalogue/category/books/poetry | 0.511 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.409 |


**Q7: What romance novels are available?**
*(expects URL containing: `romance`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.538 | books.toscrape.com/catalogue/category/books/romanc | 0.522 | books.toscrape.com/catalogue/category/books/romanc | 0.512 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.575 | books.toscrape.com/catalogue/category/books/romanc | 0.570 | books.toscrape.com/catalogue/category/books/romanc | 0.565 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.575 | books.toscrape.com/catalogue/category/books/romanc | 0.570 | books.toscrape.com/catalogue/category/books/romanc | 0.565 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.522 | books.toscrape.com/catalogue/category/books/romanc | 0.512 | books.toscrape.com/catalogue/category/books/romanc | 0.507 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.546 | books.toscrape.com/catalogue/category/books/romanc | 0.508 | books.toscrape.com/catalogue/category/books/romanc | 0.503 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.529 | books.toscrape.com/catalogue/category/books/romanc | 0.519 | books.toscrape.com/catalogue/category/books/romanc | 0.512 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.546 | books.toscrape.com/catalogue/category/books/romanc | 0.508 | books.toscrape.com/catalogue/category/books/romanc | 0.503 |


**Q8: What history books are in the collection?**
*(expects URL containing: `history`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/histor | 0.513 | books.toscrape.com/catalogue/category/books/histor | 0.505 | books.toscrape.com/catalogue/category/books/histor | 0.481 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/histor | 0.530 | books.toscrape.com/catalogue/category/books/histor | 0.523 | books.toscrape.com/catalogue/category/books/histor | 0.521 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/histor | 0.530 | books.toscrape.com/catalogue/category/books/histor | 0.523 | books.toscrape.com/catalogue/category/books/histor | 0.521 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/histor | 0.481 | books.toscrape.com/catalogue/category/books/histor | 0.480 | books.toscrape.com/catalogue/category/books/histor | 0.463 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/histor | 0.477 | books.toscrape.com/catalogue/category/books/histor | 0.476 | books.toscrape.com/catalogue/category/books/histor | 0.470 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/histor | 0.497 | books.toscrape.com/catalogue/category/books/histor | 0.467 | books.toscrape.com/catalogue/category/books/histor | 0.465 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/histor | 0.477 | books.toscrape.com/catalogue/category/books/histor | 0.476 | books.toscrape.com/catalogue/category/books/histor | 0.470 |


**Q9: What philosophy books are available to read?**
*(expects URL containing: `philosophy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/philos | 0.521 | books.toscrape.com/catalogue/libertarianism-for-be | 0.402 | books.toscrape.com/catalogue/libertarianism-for-be | 0.398 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/philos | 0.580 | books.toscrape.com/catalogue/category/books/philos | 0.568 | books.toscrape.com/catalogue/category/books/philos | 0.568 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/philos | 0.580 | books.toscrape.com/catalogue/category/books/philos | 0.568 | books.toscrape.com/catalogue/category/books/philos | 0.568 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.462 | books.toscrape.com/catalogue/libertarianism-for-be | 0.402 | books.toscrape.com/catalogue/libertarianism-for-be | 0.388 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/philos | 0.475 | books.toscrape.com/catalogue/libertarianism-for-be | 0.402 | books.toscrape.com/catalogue/category/books/psycho | 0.389 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.491 | books.toscrape.com/catalogue/libertarianism-for-be | 0.404 | books.toscrape.com/catalogue/category/books/psycho | 0.403 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/philos | 0.475 | books.toscrape.com/catalogue/libertarianism-for-be | 0.402 | books.toscrape.com/catalogue/category/books/psycho | 0.389 |


**Q10: What humor and comedy books can I find?**
*(expects URL containing: `humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.483 | books.toscrape.com/catalogue/category/books/nonfic | 0.303 | books.toscrape.com/catalogue/category/books/psycho | 0.298 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.556 | books.toscrape.com/catalogue/category/books/humor_ | 0.553 | books.toscrape.com/catalogue/category/books/humor_ | 0.531 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.556 | books.toscrape.com/catalogue/category/books/humor_ | 0.552 | books.toscrape.com/catalogue/category/books/humor_ | 0.531 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.424 | books.toscrape.com/ | 0.311 | books.toscrape.com/catalogue/category/books/poetry | 0.310 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.439 | books.toscrape.com/catalogue/category/books/poetry | 0.316 | books.toscrape.com/catalogue/category/books/nonfic | 0.312 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.473 | books.toscrape.com/catalogue/category/books/poetry | 0.322 | books.toscrape.com/catalogue/category/books/psycho | 0.319 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/humor_ | 0.439 | books.toscrape.com/catalogue/category/books/poetry | 0.316 | books.toscrape.com/catalogue/category/books/nonfic | 0.312 |


**Q11: What fantasy books are in the bookstore?**
*(expects URL containing: `fantasy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.539 | books.toscrape.com/catalogue/category/books/fantas | 0.535 | books.toscrape.com/catalogue/category/books/fantas | 0.517 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.582 | books.toscrape.com/catalogue/category/books/fantas | 0.581 | books.toscrape.com/catalogue/category/books/fantas | 0.578 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.582 | books.toscrape.com/catalogue/category/books/fantas | 0.581 | books.toscrape.com/catalogue/category/books/fantas | 0.578 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.532 | books.toscrape.com/catalogue/category/books/fantas | 0.517 | books.toscrape.com/catalogue/category/books/fantas | 0.472 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.515 | books.toscrape.com/catalogue/category/books/fantas | 0.506 | books.toscrape.com/catalogue/category/books/fantas | 0.483 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.541 | books.toscrape.com/catalogue/category/books/fantas | 0.534 | books.toscrape.com/catalogue/category/books/fantas | 0.488 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/fantas | 0.515 | books.toscrape.com/catalogue/category/books/fantas | 0.506 | books.toscrape.com/catalogue/category/books/fantas | 0.483 |


**Q12: What is the book Sharp Objects about?**
*(expects URL containing: `sharp-objects`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.686 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.612 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.559 |
| crawl4ai | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.691 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.591 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.586 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.691 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.591 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.586 |
| scrapy+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.686 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.563 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.559 |
| crawlee | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.686 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.559 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.551 |
| colly+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.631 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.535 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.469 |
| playwright | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.686 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.559 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.551 |


**Q13: What biography books are in the catalog?**
*(expects URL containing: `biography`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.527 | books.toscrape.com/catalogue/category/books/autobi | 0.432 | books.toscrape.com/catalogue/category/books/histor | 0.427 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.525 | books.toscrape.com/catalogue/category/books/biogra | 0.520 | books.toscrape.com/catalogue/category/books/biogra | 0.498 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.525 | books.toscrape.com/catalogue/category/books/biogra | 0.520 | books.toscrape.com/catalogue/category/books/biogra | 0.498 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.444 | books.toscrape.com/ | 0.415 | books.toscrape.com/catalogue/category/books/histor | 0.406 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.453 | books.toscrape.com/catalogue/category/books/histor | 0.418 | books.toscrape.com/ | 0.416 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.500 | books.toscrape.com/catalogue/category/books/nonfic | 0.443 | books.toscrape.com/catalogue/category/books/histor | 0.443 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/biogra | 0.453 | books.toscrape.com/catalogue/category/books/histor | 0.417 | books.toscrape.com/ | 0.416 |


</details>

## fastapi-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 549 | 25 |
| crawl4ai | 20% (3/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 33% (5/15) | 0.243 | 676 | 25 |
| crawl4ai-raw | 20% (3/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.239 | 676 | 25 |
| scrapy+md | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.273 | 617 | 25 |
| crawlee | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 638 | 25 |
| colly+md | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 33% (5/15) | 0.274 | 639 | 25 |
| playwright | 27% (4/15) | 27% (4/15) | 27% (4/15) | 27% (4/15) | 33% (5/15) | 0.272 | 638 | 25 |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/security/ | 0.663 | fastapi.tiangolo.com/reference/security/ | 0.632 | fastapi.tiangolo.com/reference/security/ | 0.607 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/security/ | 0.685 | fastapi.tiangolo.com/reference/security/ | 0.658 | fastapi.tiangolo.com/reference/security/ | 0.637 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/security/ | 0.685 | fastapi.tiangolo.com/reference/security/ | 0.658 | fastapi.tiangolo.com/reference/security/ | 0.637 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/security/ | 0.663 | fastapi.tiangolo.com/reference/security/ | 0.632 | fastapi.tiangolo.com/reference/security/ | 0.625 |
| crawlee | #1 | fastapi.tiangolo.com/reference/security/ | 0.685 | fastapi.tiangolo.com/reference/security/ | 0.658 | fastapi.tiangolo.com/reference/security/ | 0.637 |
| colly+md | #1 | fastapi.tiangolo.com/reference/security/ | 0.555 | fastapi.tiangolo.com/reference/security/ | 0.555 | fastapi.tiangolo.com/reference/security/ | 0.549 |
| playwright | #1 | fastapi.tiangolo.com/reference/security/ | 0.685 | fastapi.tiangolo.com/reference/security/ | 0.658 | fastapi.tiangolo.com/reference/security/ | 0.637 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/status/ | 0.626 | fastapi.tiangolo.com/reference/status/ | 0.610 | fastapi.tiangolo.com/reference/status/ | 0.601 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/reference/status/ | 0.629 | fastapi.tiangolo.com/reference/status/ | 0.627 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/reference/status/ | 0.629 | fastapi.tiangolo.com/reference/status/ | 0.627 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/status/ | 0.626 | fastapi.tiangolo.com/reference/status/ | 0.615 | fastapi.tiangolo.com/reference/status/ | 0.608 |
| crawlee | #1 | fastapi.tiangolo.com/reference/status/ | 0.652 | fastapi.tiangolo.com/reference/status/ | 0.635 | fastapi.tiangolo.com/reference/status/ | 0.611 |
| colly+md | #1 | fastapi.tiangolo.com/reference/status/ | 0.595 | fastapi.tiangolo.com/advanced/custom-response/ | 0.554 | fastapi.tiangolo.com/reference/status/ | 0.538 |
| playwright | #1 | fastapi.tiangolo.com/reference/status/ | 0.652 | fastapi.tiangolo.com/reference/status/ | 0.635 | fastapi.tiangolo.com/reference/status/ | 0.611 |


**Q3: How do I define query parameters in the FastAPI reference?**
*(expects URL containing: `reference/fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/security/ | 0.602 | fastapi.tiangolo.com/reference/websockets/ | 0.592 | fastapi.tiangolo.com/reference/fastapi/ | 0.591 |
| crawl4ai | #2 | fastapi.tiangolo.com/tutorial/cookie-params/ | 0.624 | fastapi.tiangolo.com/reference/websockets/ | 0.614 | fastapi.tiangolo.com/reference/security/ | 0.607 |
| crawl4ai-raw | #2 | fastapi.tiangolo.com/tutorial/cookie-params/ | 0.624 | fastapi.tiangolo.com/reference/websockets/ | 0.614 | fastapi.tiangolo.com/reference/security/ | 0.607 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.620 | fastapi.tiangolo.com/reference/security/ | 0.601 | fastapi.tiangolo.com/tutorial/cookie-params/ | 0.598 |
| crawlee | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.632 | fastapi.tiangolo.com/tutorial/cookie-params/ | 0.625 | fastapi.tiangolo.com/reference/security/ | 0.608 |
| colly+md | #1 | fastapi.tiangolo.com/reference/security/ | 0.608 | fastapi.tiangolo.com/reference/fastapi/ | 0.603 | fastapi.tiangolo.com/reference/fastapi/ | 0.582 |
| playwright | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.632 | fastapi.tiangolo.com/tutorial/cookie-params/ | 0.625 | fastapi.tiangolo.com/reference/security/ | 0.608 |


**Q4: How does FastAPI handle JSON encoding and base64 bytes?**
*(expects URL containing: `json-base64-bytes`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/encoders/ | 0.573 | fastapi.tiangolo.com/advanced/custom-response/ | 0.538 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.524 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/encoders/ | 0.618 | fastapi.tiangolo.com/reference/encoders/ | 0.591 | fastapi.tiangolo.com/reference/encoders/ | 0.558 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/encoders/ | 0.618 | fastapi.tiangolo.com/reference/encoders/ | 0.591 | fastapi.tiangolo.com/reference/encoders/ | 0.560 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/encoders/ | 0.579 | fastapi.tiangolo.com/reference/encoders/ | 0.573 | fastapi.tiangolo.com/reference/encoders/ | 0.550 |
| crawlee | miss | fastapi.tiangolo.com/reference/encoders/ | 0.591 | fastapi.tiangolo.com/reference/encoders/ | 0.586 | fastapi.tiangolo.com/reference/encoders/ | 0.586 |
| colly+md | miss | fastapi.tiangolo.com/reference/encoders/ | 0.543 | fastapi.tiangolo.com/advanced/custom-response/ | 0.534 | fastapi.tiangolo.com/reference/encoders/ | 0.531 |
| playwright | miss | fastapi.tiangolo.com/reference/encoders/ | 0.591 | fastapi.tiangolo.com/reference/encoders/ | 0.589 | fastapi.tiangolo.com/reference/encoders/ | 0.586 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.596 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.587 | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.579 |
| crawl4ai | miss | fastapi.tiangolo.com/tutorial/request-forms/ | 0.601 | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.601 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.582 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/tutorial/request-forms/ | 0.601 | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.601 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.582 |
| scrapy+md | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.596 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.587 | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.579 |
| crawlee | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.601 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.588 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.575 |
| colly+md | miss | fastapi.tiangolo.com/tutorial/request-forms/ | 0.547 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.541 | fastapi.tiangolo.com/ | 0.538 |
| playwright | miss | fastapi.tiangolo.com/how-to/custom-request-and-rou | 0.601 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.588 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.575 |


**Q6: How do I use OAuth2 with password flow in FastAPI?**
*(expects URL containing: `simple-oauth2`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.706 | fastapi.tiangolo.com/reference/security/ | 0.677 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/security/ | 0.761 | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.671 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/security/ | 0.761 | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.671 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.706 | fastapi.tiangolo.com/reference/security/ | 0.677 |
| crawlee | miss | fastapi.tiangolo.com/reference/security/ | 0.761 | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.677 |
| colly+md | miss | fastapi.tiangolo.com/reference/security/ | 0.639 | fastapi.tiangolo.com/reference/security/ | 0.634 | fastapi.tiangolo.com/reference/security/ | 0.633 |
| playwright | miss | fastapi.tiangolo.com/reference/security/ | 0.761 | fastapi.tiangolo.com/reference/security/ | 0.731 | fastapi.tiangolo.com/reference/security/ | 0.677 |


**Q7: How do I use WebSockets in FastAPI?**
*(expects URL containing: `websockets`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.691 | fastapi.tiangolo.com/reference/websockets/ | 0.618 | fastapi.tiangolo.com/reference/websockets/ | 0.586 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.693 | fastapi.tiangolo.com/reference/websockets/ | 0.684 | fastapi.tiangolo.com/reference/websockets/ | 0.659 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.693 | fastapi.tiangolo.com/reference/websockets/ | 0.684 | fastapi.tiangolo.com/reference/websockets/ | 0.626 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.699 | fastapi.tiangolo.com/reference/websockets/ | 0.672 | fastapi.tiangolo.com/reference/websockets/ | 0.650 |
| crawlee | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.684 | fastapi.tiangolo.com/reference/websockets/ | 0.646 | fastapi.tiangolo.com/reference/websockets/ | 0.630 |
| colly+md | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.643 | fastapi.tiangolo.com/reference/websockets/ | 0.637 | fastapi.tiangolo.com/reference/websockets/ | 0.548 |
| playwright | #1 | fastapi.tiangolo.com/reference/websockets/ | 0.684 | fastapi.tiangolo.com/reference/websockets/ | 0.646 | fastapi.tiangolo.com/reference/websockets/ | 0.630 |


**Q8: How do I stream data responses in FastAPI?**
*(expects URL containing: `stream-data`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.596 | fastapi.tiangolo.com/advanced/custom-response/ | 0.579 | fastapi.tiangolo.com/advanced/custom-response/ | 0.577 |
| crawl4ai | miss | fastapi.tiangolo.com/ | 0.611 | fastapi.tiangolo.com/advanced/custom-response/ | 0.602 | fastapi.tiangolo.com/advanced/custom-response/ | 0.599 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/ | 0.611 | fastapi.tiangolo.com/advanced/custom-response/ | 0.602 | fastapi.tiangolo.com/advanced/custom-response/ | 0.599 |
| scrapy+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.601 | fastapi.tiangolo.com/advanced/custom-response/ | 0.583 | fastapi.tiangolo.com/advanced/custom-response/ | 0.579 |
| crawlee | miss | fastapi.tiangolo.com/ | 0.611 | fastapi.tiangolo.com/advanced/custom-response/ | 0.604 | fastapi.tiangolo.com/advanced/custom-response/ | 0.593 |
| colly+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.545 | fastapi.tiangolo.com/advanced/dataclasses/ | 0.544 | fastapi.tiangolo.com/advanced/custom-response/ | 0.536 |
| playwright | miss | fastapi.tiangolo.com/ | 0.611 | fastapi.tiangolo.com/advanced/custom-response/ | 0.604 | fastapi.tiangolo.com/advanced/custom-response/ | 0.593 |


**Q9: How do I return additional response types in FastAPI?**
*(expects URL containing: `additional-responses`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.648 | fastapi.tiangolo.com/reference/fastapi/ | 0.608 | fastapi.tiangolo.com/reference/fastapi/ | 0.608 |
| crawl4ai | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.676 | fastapi.tiangolo.com/tutorial/response-model/ | 0.646 | fastapi.tiangolo.com/tutorial/response-model/ | 0.633 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.676 | fastapi.tiangolo.com/tutorial/response-model/ | 0.646 | fastapi.tiangolo.com/tutorial/response-model/ | 0.633 |
| scrapy+md | miss | fastapi.tiangolo.com/tutorial/response-model/ | 0.621 | fastapi.tiangolo.com/reference/fastapi/ | 0.608 | fastapi.tiangolo.com/reference/fastapi/ | 0.608 |
| crawlee | miss | fastapi.tiangolo.com/tutorial/response-model/ | 0.622 | fastapi.tiangolo.com/advanced/custom-response/ | 0.616 | fastapi.tiangolo.com/tutorial/response-model/ | 0.615 |
| colly+md | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.584 | fastapi.tiangolo.com/tutorial/response-model/ | 0.582 | fastapi.tiangolo.com/advanced/custom-response/ | 0.577 |
| playwright | miss | fastapi.tiangolo.com/tutorial/response-model/ | 0.622 | fastapi.tiangolo.com/advanced/custom-response/ | 0.616 | fastapi.tiangolo.com/tutorial/response-model/ | 0.615 |


**Q10: How do I write async tests for FastAPI applications?**
*(expects URL containing: `async-tests`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/ | 0.605 | fastapi.tiangolo.com/contributing/ | 0.551 | fastapi.tiangolo.com/ | 0.541 |
| crawl4ai | miss | fastapi.tiangolo.com/ | 0.639 | fastapi.tiangolo.com/benchmarks/ | 0.583 | fastapi.tiangolo.com/contributing/ | 0.574 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/ | 0.639 | fastapi.tiangolo.com/benchmarks/ | 0.583 | fastapi.tiangolo.com/contributing/ | 0.574 |
| scrapy+md | miss | fastapi.tiangolo.com/ | 0.585 | fastapi.tiangolo.com/contributing/ | 0.551 | fastapi.tiangolo.com/ | 0.542 |
| crawlee | miss | fastapi.tiangolo.com/ | 0.603 | fastapi.tiangolo.com/contributing/ | 0.572 | fastapi.tiangolo.com/ | 0.570 |
| colly+md | miss | fastapi.tiangolo.com/ | 0.577 | fastapi.tiangolo.com/deployment/versions/ | 0.517 | fastapi.tiangolo.com/ | 0.511 |
| playwright | miss | fastapi.tiangolo.com/ | 0.603 | fastapi.tiangolo.com/contributing/ | 0.572 | fastapi.tiangolo.com/ | 0.570 |


**Q11: How do I define nested Pydantic models for request bodies?**
*(expects URL containing: `body-nested-models`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.562 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.560 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.538 |
| crawl4ai | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.581 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.570 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.537 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.581 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.570 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.537 |
| scrapy+md | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.556 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.555 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.489 |
| crawlee | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.575 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.560 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.490 |
| colly+md | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.587 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.558 | fastapi.tiangolo.com/features/ | 0.495 |
| playwright | miss | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.575 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.560 | fastapi.tiangolo.com/tutorial/request-form-models/ | 0.490 |


**Q12: How do I handle startup and shutdown events in FastAPI?**
*(expects URL containing: `events`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.563 | fastapi.tiangolo.com/reference/fastapi/ | 0.499 | fastapi.tiangolo.com/reference/fastapi/ | 0.497 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.570 | fastapi.tiangolo.com/reference/fastapi/ | 0.503 | fastapi.tiangolo.com/reference/fastapi/ | 0.503 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.570 | fastapi.tiangolo.com/reference/fastapi/ | 0.503 | fastapi.tiangolo.com/reference/fastapi/ | 0.503 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.574 | fastapi.tiangolo.com/reference/fastapi/ | 0.512 | fastapi.tiangolo.com/reference/fastapi/ | 0.497 |
| crawlee | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.577 | fastapi.tiangolo.com/reference/fastapi/ | 0.511 | fastapi.tiangolo.com/reference/fastapi/ | 0.497 |
| colly+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.548 | fastapi.tiangolo.com/reference/fastapi/ | 0.502 | fastapi.tiangolo.com/ | 0.462 |
| playwright | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.577 | fastapi.tiangolo.com/reference/fastapi/ | 0.511 | fastapi.tiangolo.com/reference/fastapi/ | 0.497 |


**Q13: How do I use middleware in FastAPI?**
*(expects URL containing: `middleware`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.690 | fastapi.tiangolo.com/reference/fastapi/ | 0.618 | fastapi.tiangolo.com/reference/fastapi/ | 0.516 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/fastapi/ | 0.628 | fastapi.tiangolo.com/reference/fastapi/ | 0.561 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/fastapi/ | 0.628 | fastapi.tiangolo.com/reference/fastapi/ | 0.561 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.719 | fastapi.tiangolo.com/reference/fastapi/ | 0.626 | fastapi.tiangolo.com/reference/fastapi/ | 0.525 |
| crawlee | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.722 | fastapi.tiangolo.com/reference/fastapi/ | 0.627 | fastapi.tiangolo.com/ | 0.551 |
| colly+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/fastapi/ | 0.618 | fastapi.tiangolo.com/reference/fastapi/ | 0.538 |
| playwright | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.722 | fastapi.tiangolo.com/reference/fastapi/ | 0.627 | fastapi.tiangolo.com/ | 0.551 |


**Q14: How do I use Jinja2 templates in FastAPI?**
*(expects URL containing: `templating`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/ | 0.531 | fastapi.tiangolo.com/ | 0.527 | fastapi.tiangolo.com/features/ | 0.500 |
| crawl4ai | miss | fastapi.tiangolo.com/ | 0.565 | fastapi.tiangolo.com/ | 0.533 | fastapi.tiangolo.com/features/ | 0.525 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/ | 0.565 | fastapi.tiangolo.com/ | 0.532 | fastapi.tiangolo.com/features/ | 0.525 |
| scrapy+md | miss | fastapi.tiangolo.com/ | 0.531 | fastapi.tiangolo.com/ | 0.527 | fastapi.tiangolo.com/reference/fastapi/ | 0.504 |
| crawlee | miss | fastapi.tiangolo.com/ | 0.565 | fastapi.tiangolo.com/ | 0.542 | fastapi.tiangolo.com/features/ | 0.518 |
| colly+md | miss | fastapi.tiangolo.com/ | 0.526 | fastapi.tiangolo.com/features/ | 0.494 | fastapi.tiangolo.com/reference/fastapi/ | 0.491 |
| playwright | miss | fastapi.tiangolo.com/ | 0.565 | fastapi.tiangolo.com/ | 0.542 | fastapi.tiangolo.com/features/ | 0.518 |


**Q15: How do I deploy FastAPI to the cloud?**
*(expects URL containing: `deployment`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #12 | fastapi.tiangolo.com/ | 0.767 | fastapi.tiangolo.com/ | 0.719 | fastapi.tiangolo.com/ | 0.717 |
| crawl4ai | #7 | fastapi.tiangolo.com/ | 0.775 | fastapi.tiangolo.com/ | 0.735 | fastapi.tiangolo.com/ | 0.723 |
| crawl4ai-raw | #11 | fastapi.tiangolo.com/ | 0.775 | fastapi.tiangolo.com/ | 0.735 | fastapi.tiangolo.com/ | 0.723 |
| scrapy+md | #11 | fastapi.tiangolo.com/ | 0.767 | fastapi.tiangolo.com/ | 0.723 | fastapi.tiangolo.com/ | 0.717 |
| crawlee | #12 | fastapi.tiangolo.com/ | 0.768 | fastapi.tiangolo.com/ | 0.724 | fastapi.tiangolo.com/ | 0.720 |
| colly+md | #9 | fastapi.tiangolo.com/ | 0.741 | fastapi.tiangolo.com/ | 0.704 | fastapi.tiangolo.com/ | 0.689 |
| playwright | #12 | fastapi.tiangolo.com/ | 0.768 | fastapi.tiangolo.com/ | 0.724 | fastapi.tiangolo.com/ | 0.720 |


</details>

## python-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 8% (1/12) | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.104 | 75 | 20 |
| crawl4ai | 8% (1/12) | 8% (1/12) | 8% (1/12) | 8% (1/12) | 17% (2/12) | 0.091 | 207 | 20 |
| crawl4ai-raw | 8% (1/12) | 8% (1/12) | 8% (1/12) | 8% (1/12) | 17% (2/12) | 0.091 | 207 | 20 |
| scrapy+md | 8% (1/12) | 8% (1/12) | 8% (1/12) | 17% (2/12) | 17% (2/12) | 0.095 | 192 | 14 |
| crawlee | 8% (1/12) | 8% (1/12) | 8% (1/12) | 17% (2/12) | 17% (2/12) | 0.095 | 198 | 20 |
| colly+md | 8% (1/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 17% (2/12) | 0.111 | 198 | 20 |
| playwright | 8% (1/12) | 8% (1/12) | 8% (1/12) | 17% (2/12) | 17% (2/12) | 0.095 | 198 | 20 |

<details>
<summary>Query-by-query results for python-docs</summary>

**Q1: What new features were added in Python 3.10?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/ | 0.571 | docs.python.org/3.10/library/index.html | 0.561 | docs.python.org/3.10/library/index.html | 0.532 |
| crawl4ai | miss | docs.python.org/3.10/ | 0.588 | docs.python.org/3.10/library/index.html | 0.576 | docs.python.org/3.10/library/index.html | 0.563 |
| crawl4ai-raw | miss | docs.python.org/3.10/ | 0.588 | docs.python.org/3.10/library/index.html | 0.576 | docs.python.org/3.10/library/index.html | 0.563 |
| scrapy+md | miss | docs.python.org/3.10/ | 0.571 | docs.python.org/3.10/library/index.html | 0.564 | docs.python.org/3.10/ | 0.545 |
| crawlee | miss | docs.python.org/3.10/ | 0.571 | docs.python.org/3.10/library/index.html | 0.564 | docs.python.org/3.10/ | 0.545 |
| colly+md | miss | docs.python.org/3.10/ | 0.573 | docs.python.org/3.10/ | 0.532 | docs.python.org/3.10/ | 0.532 |
| playwright | miss | docs.python.org/3.10/ | 0.571 | docs.python.org/3.10/library/index.html | 0.564 | docs.python.org/3.10/ | 0.545 |


**Q2: What does the term 'decorator' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/installing/index.html | 0.318 | docs.python.org/3.10/extending/index.html | 0.306 | docs.python.org/3.10/extending/index.html | 0.278 |
| crawl4ai | miss | docs.python.org/3.10/installing/index.html | 0.330 | docs.python.org/3.10/faq/index.html | 0.322 | docs.python.org/3.10/faq/index.html | 0.322 |
| crawl4ai-raw | miss | docs.python.org/3.10/installing/index.html | 0.330 | docs.python.org/3.10/faq/index.html | 0.322 | docs.python.org/3.10/faq/index.html | 0.322 |
| scrapy+md | miss | docs.python.org/3.10/installing/index.html | 0.318 | docs.python.org/3.10/extending/index.html | 0.306 | docs.python.org/3.10/extending/index.html | 0.306 |
| crawlee | miss | docs.python.org/3.10/installing/index.html | 0.318 | docs.python.org/3.10/extending/index.html | 0.307 | docs.python.org/3.10/extending/index.html | 0.306 |
| colly+md | miss | docs.python.org/3.10/extending/index.html | 0.304 | docs.python.org/3.10/installing/index.html | 0.294 | docs.python.org/3.10/c-api/index.html | 0.277 |
| playwright | miss | docs.python.org/3.10/installing/index.html | 0.318 | docs.python.org/3.10/extending/index.html | 0.307 | docs.python.org/3.10/extending/index.html | 0.306 |


**Q3: How do I report a bug in Python?**
*(expects URL containing: `bugs`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/faq/index.html | 0.404 | docs.python.org/2.6/ | 0.355 | docs.python.org/3.1/ | 0.354 |
| crawl4ai | miss | docs.python.org/3.10/faq/index.html | 0.516 | docs.python.org/3.10/faq/index.html | 0.514 | docs.python.org/3.10/reference/index.html | 0.491 |
| crawl4ai-raw | miss | docs.python.org/3.10/faq/index.html | 0.516 | docs.python.org/3.10/faq/index.html | 0.514 | docs.python.org/3.10/reference/index.html | 0.491 |
| scrapy+md | miss | docs.python.org/3.10/reference/index.html | 0.537 | docs.python.org/3.10/reference/index.html | 0.537 | docs.python.org/3.10/library/index.html | 0.520 |
| crawlee | miss | docs.python.org/3.10/reference/index.html | 0.537 | docs.python.org/3.10/library/index.html | 0.520 | docs.python.org/3.10/reference/index.html | 0.520 |
| colly+md | miss | docs.python.org/3.10/library/index.html | 0.532 | docs.python.org/3.10/library/index.html | 0.532 | docs.python.org/3.10/c-api/index.html | 0.522 |
| playwright | miss | docs.python.org/3.10/reference/index.html | 0.537 | docs.python.org/3.10/library/index.html | 0.520 | docs.python.org/3.10/reference/index.html | 0.520 |


**Q4: What is structural pattern matching in Python?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/reference/index.html | 0.301 | docs.python.org/3.10/library/index.html | 0.279 | docs.python.org/3.10/c-api/index.html | 0.272 |
| crawl4ai | miss | docs.python.org/3.10/reference/index.html | 0.305 | docs.python.org/3.10/faq/index.html | 0.302 | docs.python.org/3.10/faq/index.html | 0.302 |
| crawl4ai-raw | miss | docs.python.org/3.10/reference/index.html | 0.305 | docs.python.org/3.10/faq/index.html | 0.302 | docs.python.org/3.10/faq/index.html | 0.302 |
| scrapy+md | miss | docs.python.org/3.10/reference/index.html | 0.290 | docs.python.org/3.10/library/index.html | 0.288 | docs.python.org/3.10/library/index.html | 0.288 |
| crawlee | miss | docs.python.org/3.10/reference/index.html | 0.290 | docs.python.org/3.10/library/index.html | 0.288 | docs.python.org/3.10/library/index.html | 0.288 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.279 | docs.python.org/3.13/ | 0.279 | docs.python.org/3.12/ | 0.279 |
| playwright | miss | docs.python.org/3.10/reference/index.html | 0.290 | docs.python.org/3.10/library/index.html | 0.288 | docs.python.org/3.10/library/index.html | 0.288 |


**Q5: What is Python's glossary definition of a generator?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/reference/index.html | 0.375 | docs.python.org/3.10/reference/index.html | 0.360 | docs.python.org/3.10/library/index.html | 0.349 |
| crawl4ai | miss | docs.python.org/3.10/library/index.html | 0.395 | docs.python.org/3.10/library/index.html | 0.395 | docs.python.org/3.10/reference/index.html | 0.374 |
| crawl4ai-raw | miss | docs.python.org/3.10/library/index.html | 0.395 | docs.python.org/3.10/library/index.html | 0.395 | docs.python.org/3.10/reference/index.html | 0.374 |
| scrapy+md | miss | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/reference/index.html | 0.371 |
| crawlee | miss | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/reference/index.html | 0.371 |
| colly+md | miss | docs.python.org/3.10/reference/index.html | 0.358 | docs.python.org/3.10/license.html | 0.338 | docs.python.org/3.10/extending/index.html | 0.334 |
| playwright | miss | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/library/index.html | 0.400 | docs.python.org/3.10/reference/index.html | 0.371 |


**Q6: What are the Python how-to guides about?**
*(expects URL containing: `howto`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.11/ | 0.569 | docs.python.org/3.10/faq/index.html | 0.567 | docs.python.org/3.5/ | 0.561 |
| crawl4ai | miss | docs.python.org/3.11/ | 0.571 | docs.python.org/3.11/ | 0.569 | docs.python.org/3.10/ | 0.566 |
| crawl4ai-raw | miss | docs.python.org/3.11/ | 0.571 | docs.python.org/3.11/ | 0.569 | docs.python.org/3.10/ | 0.566 |
| scrapy+md | miss | docs.python.org/3.11/ | 0.574 | docs.python.org/3.10/ | 0.571 | docs.python.org/3.10/ | 0.571 |
| crawlee | miss | docs.python.org/3.11/ | 0.574 | docs.python.org/3.10/ | 0.571 | docs.python.org/3.12/ | 0.570 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.584 | docs.python.org/3.10/installing/index.html | 0.584 | docs.python.org/3.10/installing/index.html | 0.569 |
| playwright | miss | docs.python.org/3.11/ | 0.574 | docs.python.org/3.10/ | 0.571 | docs.python.org/3.12/ | 0.570 |


**Q7: What is the Python module index?**
*(expects URL containing: `py-modindex`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/c-api/index.html | 0.580 | docs.python.org/3.1/ | 0.579 | docs.python.org/2.6/ | 0.577 |
| crawl4ai | miss | docs.python.org/3.10/installing/index.html | 0.613 | docs.python.org/3.10/installing/index.html | 0.605 | docs.python.org/3.10/installing/index.html | 0.590 |
| crawl4ai-raw | miss | docs.python.org/3.10/installing/index.html | 0.613 | docs.python.org/3.10/installing/index.html | 0.605 | docs.python.org/3.10/installing/index.html | 0.590 |
| scrapy+md | miss | docs.python.org/3.10/installing/index.html | 0.633 | docs.python.org/3.10/installing/index.html | 0.609 | docs.python.org/3.10/installing/index.html | 0.589 |
| crawlee | miss | docs.python.org/3.10/installing/index.html | 0.625 | docs.python.org/3.10/installing/index.html | 0.608 | docs.python.org/3.10/installing/index.html | 0.589 |
| colly+md | miss | docs.python.org/3.10/installing/index.html | 0.572 | docs.python.org/3.10/installing/index.html | 0.572 | docs.python.org/3.10/library/index.html | 0.566 |
| playwright | miss | docs.python.org/3.10/installing/index.html | 0.625 | docs.python.org/3.10/installing/index.html | 0.608 | docs.python.org/3.10/installing/index.html | 0.589 |


**Q8: What Python tutorial topics are available?**
*(expects URL containing: `tutorial`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.11/ | 0.522 | docs.python.org/3.12/ | 0.522 | docs.python.org/2.7/ | 0.519 |
| crawl4ai | miss | docs.python.org/3.11/ | 0.540 | docs.python.org/3.11/ | 0.538 | docs.python.org/3.10/ | 0.538 |
| crawl4ai-raw | miss | docs.python.org/3.11/ | 0.540 | docs.python.org/3.11/ | 0.538 | docs.python.org/3.10/ | 0.538 |
| scrapy+md | miss | docs.python.org/3.11/ | 0.544 | docs.python.org/3.10/ | 0.542 | docs.python.org/3.10/ | 0.542 |
| crawlee | miss | docs.python.org/3.11/ | 0.544 | docs.python.org/3.10/ | 0.542 | docs.python.org/3.12/ | 0.538 |
| colly+md | miss | docs.python.org/3.12/ | 0.547 | docs.python.org/3.10/ | 0.545 | docs.python.org/3.10/ | 0.545 |
| playwright | miss | docs.python.org/3.11/ | 0.544 | docs.python.org/3.10/ | 0.542 | docs.python.org/3.12/ | 0.538 |


**Q9: What is the Python license and copyright?**
*(expects URL containing: `license`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/license.html | 0.660 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.626 |
| crawl4ai | #1 | docs.python.org/3.10/license.html | 0.670 | docs.python.org/3.10/license.html | 0.652 | docs.python.org/3.10/license.html | 0.652 |
| crawl4ai-raw | #1 | docs.python.org/3.10/license.html | 0.670 | docs.python.org/3.10/license.html | 0.652 | docs.python.org/3.10/license.html | 0.652 |
| scrapy+md | #1 | docs.python.org/3.10/license.html | 0.660 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.634 |
| crawlee | #1 | docs.python.org/3.10/license.html | 0.660 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.634 |
| colly+md | #1 | docs.python.org/3.10/license.html | 0.652 | docs.python.org/3.10/license.html | 0.617 | docs.python.org/3.10/license.html | 0.614 |
| playwright | #1 | docs.python.org/3.10/license.html | 0.660 | docs.python.org/3.10/license.html | 0.638 | docs.python.org/3.10/license.html | 0.634 |


**Q10: What is the table of contents for Python 3.10 documentation?**
*(expects URL containing: `contents`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/ | 0.705 | docs.python.org/3.5/ | 0.666 | docs.python.org/3.11/ | 0.610 |
| crawl4ai | miss | docs.python.org/3.10/ | 0.684 | docs.python.org/3.10/reference/index.html | 0.624 | docs.python.org/3.10/reference/index.html | 0.617 |
| crawl4ai-raw | miss | docs.python.org/3.10/ | 0.684 | docs.python.org/3.10/reference/index.html | 0.624 | docs.python.org/3.10/reference/index.html | 0.617 |
| scrapy+md | miss | docs.python.org/3.10/ | 0.705 | docs.python.org/3.10/reference/index.html | 0.613 | docs.python.org/3.11/ | 0.610 |
| crawlee | miss | docs.python.org/3.10/ | 0.705 | docs.python.org/3.5/ | 0.613 | docs.python.org/3.10/reference/index.html | 0.611 |
| colly+md | miss | docs.python.org/3.10/ | 0.708 | docs.python.org/3.5/ | 0.603 | docs.python.org/3.11/ | 0.602 |
| playwright | miss | docs.python.org/3.10/ | 0.705 | docs.python.org/3.5/ | 0.613 | docs.python.org/3.10/reference/index.html | 0.611 |


**Q11: What does the term 'iterable' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/extending/index.html | 0.344 | docs.python.org/3.10/extending/index.html | 0.327 | docs.python.org/3.10/reference/index.html | 0.309 |
| crawl4ai | miss | docs.python.org/3.10/reference/index.html | 0.373 | docs.python.org/3.10/reference/index.html | 0.373 | docs.python.org/3.10/extending/index.html | 0.367 |
| crawl4ai-raw | miss | docs.python.org/3.10/reference/index.html | 0.373 | docs.python.org/3.10/reference/index.html | 0.373 | docs.python.org/3.10/extending/index.html | 0.367 |
| scrapy+md | miss | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/reference/index.html | 0.353 |
| crawlee | miss | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/reference/index.html | 0.353 |
| colly+md | miss | docs.python.org/3.10/extending/index.html | 0.332 | docs.python.org/3.10/extending/index.html | 0.317 | docs.python.org/3.10/extending/index.html | 0.315 |
| playwright | miss | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/extending/index.html | 0.359 | docs.python.org/3.10/reference/index.html | 0.353 |


**Q12: How do I install and configure Python on my system?**
*(expects URL containing: `using`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #4 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.519 | docs.python.org/3.10/installing/index.html | 0.477 |
| crawl4ai | #11 | docs.python.org/3.10/installing/index.html | 0.541 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.491 |
| crawl4ai-raw | #11 | docs.python.org/3.10/installing/index.html | 0.541 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.491 |
| scrapy+md | #7 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.519 | docs.python.org/3.10/installing/index.html | 0.480 |
| crawlee | #7 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.519 | docs.python.org/3.10/installing/index.html | 0.480 |
| colly+md | #3 | docs.python.org/3.10/installing/index.html | 0.565 | docs.python.org/3.10/installing/index.html | 0.535 | docs.python.org/3.10/using/index.html | 0.476 |
| playwright | #7 | docs.python.org/3.10/installing/index.html | 0.530 | docs.python.org/3.10/installing/index.html | 0.519 | docs.python.org/3.10/installing/index.html | 0.480 |


</details>

## react-dev

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 25% (3/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 0.310 | 452 | 30 |
| crawl4ai | 25% (3/12) | 33% (4/12) | 33% (4/12) | 42% (5/12) | 50% (6/12) | 0.296 | 547 | 30 |
| crawl4ai-raw | 25% (3/12) | 33% (4/12) | 33% (4/12) | 42% (5/12) | 50% (6/12) | 0.294 | 548 | 30 |
| scrapy+md | 25% (3/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 50% (6/12) | 0.324 | 452 | 30 |
| crawlee | 25% (3/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 50% (6/12) | 0.310 | 840 | 30 |
| colly+md | 25% (3/12) | 33% (4/12) | 33% (4/12) | 33% (4/12) | 50% (6/12) | 0.288 | 812 | 30 |
| playwright | 25% (3/12) | 42% (5/12) | 42% (5/12) | 42% (5/12) | 50% (6/12) | 0.325 | 812 | 30 |

<details>
<summary>Query-by-query results for react-dev</summary>

**Q1: How do I manage state in a React component?**
*(expects URL containing: `state`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/preserving-and-resetting-state | 0.687 | react.dev/learn/preserving-and-resetting-state | 0.672 | react.dev/learn/preserving-and-resetting-state | 0.663 |
| crawl4ai | #1 | react.dev/learn/preserving-and-resetting-state | 0.679 | react.dev/learn/preserving-and-resetting-state | 0.670 | react.dev/learn/preserving-and-resetting-state | 0.668 |
| crawl4ai-raw | #1 | react.dev/learn/preserving-and-resetting-state | 0.679 | react.dev/learn/preserving-and-resetting-state | 0.673 | react.dev/learn/preserving-and-resetting-state | 0.668 |
| scrapy+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.687 | react.dev/learn/preserving-and-resetting-state | 0.676 | react.dev/learn/preserving-and-resetting-state | 0.663 |
| crawlee | #1 | react.dev/learn/preserving-and-resetting-state | 0.687 | react.dev/learn/preserving-and-resetting-state | 0.653 | react.dev/learn/state-as-a-snapshot | 0.651 |
| colly+md | #1 | react.dev/learn/preserving-and-resetting-state | 0.666 | react.dev/learn/preserving-and-resetting-state | 0.658 | react.dev/reference/react/useState | 0.618 |
| playwright | #1 | react.dev/learn/preserving-and-resetting-state | 0.687 | react.dev/learn/preserving-and-resetting-state | 0.663 | react.dev/learn/state-as-a-snapshot | 0.651 |


**Q2: What are React hooks and how do I use them?**
*(expects URL containing: `hooks`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | react.dev/learn/typescript | 0.716 | react.dev/learn | 0.716 | react.dev/learn/reusing-logic-with-custom-hooks | 0.691 |
| crawl4ai | #3 | react.dev/learn | 0.734 | react.dev/learn/typescript | 0.724 | react.dev/learn/reusing-logic-with-custom-hooks | 0.696 |
| crawl4ai-raw | #3 | react.dev/learn | 0.734 | react.dev/learn/typescript | 0.724 | react.dev/learn/reusing-logic-with-custom-hooks | 0.696 |
| scrapy+md | #3 | react.dev/learn/typescript | 0.716 | react.dev/learn | 0.716 | react.dev/learn/reusing-logic-with-custom-hooks | 0.691 |
| crawlee | #3 | react.dev/learn/typescript | 0.716 | react.dev/learn | 0.716 | react.dev/learn/reusing-logic-with-custom-hooks | 0.691 |
| colly+md | #3 | react.dev/learn/typescript | 0.694 | react.dev/learn | 0.683 | react.dev/learn/reusing-logic-with-custom-hooks | 0.673 |
| playwright | #3 | react.dev/learn/typescript | 0.716 | react.dev/learn | 0.716 | react.dev/learn/reusing-logic-with-custom-hooks | 0.691 |


**Q3: How does the useEffect hook work in React?**
*(expects URL containing: `useEffect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #21 | react.dev/learn/reusing-logic-with-custom-hooks | 0.612 | react.dev/learn/reusing-logic-with-custom-hooks | 0.607 | react.dev/learn/reusing-logic-with-custom-hooks | 0.604 |
| crawl4ai | #18 | react.dev/learn/reusing-logic-with-custom-hooks | 0.618 | react.dev/learn/reusing-logic-with-custom-hooks | 0.601 | react.dev/learn/reusing-logic-with-custom-hooks | 0.598 |
| crawl4ai-raw | #18 | react.dev/learn/reusing-logic-with-custom-hooks | 0.618 | react.dev/learn/reusing-logic-with-custom-hooks | 0.601 | react.dev/learn/reusing-logic-with-custom-hooks | 0.598 |
| scrapy+md | #20 | react.dev/learn/reusing-logic-with-custom-hooks | 0.617 | react.dev/learn/reusing-logic-with-custom-hooks | 0.604 | react.dev/learn/reusing-logic-with-custom-hooks | 0.599 |
| crawlee | #18 | react.dev/learn/reusing-logic-with-custom-hooks | 0.615 | react.dev/learn/reusing-logic-with-custom-hooks | 0.604 | react.dev/learn/reusing-logic-with-custom-hooks | 0.601 |
| colly+md | #18 | react.dev/learn/reusing-logic-with-custom-hooks | 0.598 | react.dev/learn/reusing-logic-with-custom-hooks | 0.589 | react.dev/learn/reusing-logic-with-custom-hooks | 0.579 |
| playwright | #16 | react.dev/learn/reusing-logic-with-custom-hooks | 0.617 | react.dev/learn/reusing-logic-with-custom-hooks | 0.604 | react.dev/learn/reusing-logic-with-custom-hooks | 0.601 |


**Q4: How do I handle forms and user input in React?**
*(expects URL containing: `input`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/reference/react/useState | 0.596 | react.dev/ | 0.557 | react.dev/learn/preserving-and-resetting-state | 0.555 |
| crawl4ai | miss | react.dev/reference/react/useState | 0.590 | react.dev/learn/preserving-and-resetting-state | 0.572 | react.dev/learn/manipulating-the-dom-with-refs | 0.567 |
| crawl4ai-raw | miss | react.dev/reference/react/useState | 0.590 | react.dev/learn/preserving-and-resetting-state | 0.578 | react.dev/learn/manipulating-the-dom-with-refs | 0.573 |
| scrapy+md | miss | react.dev/reference/react/useState | 0.596 | react.dev/learn/preserving-and-resetting-state | 0.569 | react.dev/ | 0.557 |
| crawlee | miss | react.dev/reference/react/useState | 0.598 | react.dev/learn/preserving-and-resetting-state | 0.570 | react.dev/ | 0.557 |
| colly+md | miss | react.dev/reference/react/useState | 0.586 | react.dev/reference/react/useState | 0.550 | react.dev/learn/preserving-and-resetting-state | 0.540 |
| playwright | miss | react.dev/reference/react/useState | 0.596 | react.dev/learn/preserving-and-resetting-state | 0.569 | react.dev/ | 0.557 |


**Q5: How do I create and use context in React?**
*(expects URL containing: `context`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/passing-data-deeply-with-context | 0.690 | react.dev/learn/passing-data-deeply-with-context | 0.689 | react.dev/learn/passing-data-deeply-with-context | 0.688 |
| crawl4ai | #1 | react.dev/learn/passing-data-deeply-with-context | 0.721 | react.dev/learn/passing-data-deeply-with-context | 0.702 | react.dev/learn/passing-data-deeply-with-context | 0.698 |
| crawl4ai-raw | #1 | react.dev/learn/passing-data-deeply-with-context | 0.717 | react.dev/learn/passing-data-deeply-with-context | 0.702 | react.dev/learn/passing-data-deeply-with-context | 0.691 |
| scrapy+md | #1 | react.dev/learn/passing-data-deeply-with-context | 0.694 | react.dev/learn/passing-data-deeply-with-context | 0.688 | react.dev/learn/passing-data-deeply-with-context | 0.688 |
| crawlee | #1 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.691 | react.dev/learn/passing-data-deeply-with-context | 0.688 |
| colly+md | #1 | react.dev/learn/passing-data-deeply-with-context | 0.705 | react.dev/learn/passing-data-deeply-with-context | 0.681 | react.dev/learn/passing-data-deeply-with-context | 0.667 |
| playwright | #1 | react.dev/learn/passing-data-deeply-with-context | 0.709 | react.dev/learn/passing-data-deeply-with-context | 0.691 | react.dev/learn/passing-data-deeply-with-context | 0.688 |


**Q6: How do I handle events like clicks in React?**
*(expects URL containing: `event`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | react.dev/learn | 0.667 | react.dev/learn | 0.563 | react.dev/learn/separating-events-from-effects | 0.563 |
| crawl4ai | #6 | react.dev/learn | 0.663 | react.dev/learn/typescript | 0.589 | react.dev/learn/manipulating-the-dom-with-refs | 0.567 |
| crawl4ai-raw | #7 | react.dev/learn | 0.664 | react.dev/learn/typescript | 0.589 | react.dev/learn/manipulating-the-dom-with-refs | 0.568 |
| scrapy+md | #2 | react.dev/learn | 0.661 | react.dev/learn/separating-events-from-effects | 0.560 | react.dev/learn/separating-events-from-effects | 0.560 |
| crawlee | #3 | react.dev/learn | 0.661 | react.dev/learn | 0.562 | react.dev/learn/separating-events-from-effects | 0.560 |
| colly+md | #14 | react.dev/learn | 0.639 | react.dev/learn/typescript | 0.559 | react.dev/reference/react/useState | 0.540 |
| playwright | #2 | react.dev/learn | 0.661 | react.dev/learn/separating-events-from-effects | 0.560 | react.dev/learn | 0.560 |


**Q7: What is JSX and how does React use it?**
*(expects URL containing: `jsx`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.651 | react.dev/ | 0.637 | react.dev/learn | 0.625 |
| crawl4ai | miss | react.dev/learn | 0.655 | react.dev/ | 0.642 | react.dev/learn | 0.621 |
| crawl4ai-raw | miss | react.dev/learn | 0.655 | react.dev/ | 0.642 | react.dev/learn | 0.620 |
| scrapy+md | miss | react.dev/learn | 0.648 | react.dev/ | 0.637 | react.dev/learn | 0.619 |
| crawlee | miss | react.dev/learn | 0.648 | react.dev/ | 0.637 | react.dev/learn | 0.620 |
| colly+md | miss | react.dev/learn | 0.645 | react.dev/ | 0.626 | react.dev/learn | 0.591 |
| playwright | miss | react.dev/learn | 0.648 | react.dev/ | 0.637 | react.dev/learn | 0.619 |


**Q8: How do I render lists and use keys in React?**
*(expects URL containing: `list`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.688 | react.dev/learn/preserving-and-resetting-state | 0.590 | react.dev/ | 0.554 |
| crawl4ai | miss | react.dev/learn | 0.689 | react.dev/learn/preserving-and-resetting-state | 0.599 | react.dev/ | 0.566 |
| crawl4ai-raw | miss | react.dev/learn | 0.690 | react.dev/learn/preserving-and-resetting-state | 0.596 | react.dev/ | 0.566 |
| scrapy+md | miss | react.dev/learn | 0.689 | react.dev/learn/preserving-and-resetting-state | 0.595 | react.dev/ | 0.554 |
| crawlee | miss | react.dev/learn | 0.687 | react.dev/learn/preserving-and-resetting-state | 0.595 | react.dev/learn | 0.582 |
| colly+md | miss | react.dev/learn | 0.677 | react.dev/learn/preserving-and-resetting-state | 0.591 | react.dev/learn | 0.578 |
| playwright | miss | react.dev/learn | 0.689 | react.dev/learn/preserving-and-resetting-state | 0.595 | react.dev/learn | 0.582 |


**Q9: How do I use the useRef hook in React?**
*(expects URL containing: `useRef`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | react.dev/learn/referencing-values-with-refs | 0.680 | react.dev/learn/manipulating-the-dom-with-refs | 0.659 | react.dev/learn/referencing-values-with-refs | 0.649 |
| crawl4ai | #1 | react.dev/learn/manipulating-the-dom-with-refs | 0.679 | react.dev/learn/referencing-values-with-refs | 0.678 | react.dev/learn/referencing-values-with-refs | 0.664 |
| crawl4ai-raw | #1 | react.dev/learn/manipulating-the-dom-with-refs | 0.679 | react.dev/learn/referencing-values-with-refs | 0.678 | react.dev/learn/referencing-values-with-refs | 0.661 |
| scrapy+md | #1 | react.dev/learn/referencing-values-with-refs | 0.683 | react.dev/learn/manipulating-the-dom-with-refs | 0.661 | react.dev/learn/referencing-values-with-refs | 0.651 |
| crawlee | #1 | react.dev/learn/referencing-values-with-refs | 0.683 | react.dev/learn/manipulating-the-dom-with-refs | 0.661 | react.dev/learn/referencing-values-with-refs | 0.651 |
| colly+md | #1 | react.dev/learn/referencing-values-with-refs | 0.669 | react.dev/learn/manipulating-the-dom-with-refs | 0.647 | react.dev/learn/manipulating-the-dom-with-refs | 0.644 |
| playwright | #1 | react.dev/learn/referencing-values-with-refs | 0.683 | react.dev/learn/manipulating-the-dom-with-refs | 0.661 | react.dev/learn/referencing-values-with-refs | 0.651 |


**Q10: How do I pass props between React components?**
*(expects URL containing: `props`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn/passing-data-deeply-with-context | 0.678 | react.dev/learn/passing-data-deeply-with-context | 0.672 | react.dev/learn/passing-data-deeply-with-context | 0.632 |
| crawl4ai | miss | react.dev/learn/passing-data-deeply-with-context | 0.685 | react.dev/learn/passing-data-deeply-with-context | 0.665 | react.dev/learn/passing-data-deeply-with-context | 0.660 |
| crawl4ai-raw | miss | react.dev/learn/passing-data-deeply-with-context | 0.685 | react.dev/learn/passing-data-deeply-with-context | 0.665 | react.dev/learn/passing-data-deeply-with-context | 0.660 |
| scrapy+md | miss | react.dev/learn/passing-data-deeply-with-context | 0.678 | react.dev/learn/passing-data-deeply-with-context | 0.672 | react.dev/learn/passing-data-deeply-with-context | 0.633 |
| crawlee | miss | react.dev/learn/passing-data-deeply-with-context | 0.678 | react.dev/learn/passing-data-deeply-with-context | 0.672 | react.dev/learn/passing-data-deeply-with-context | 0.637 |
| colly+md | miss | react.dev/learn/passing-data-deeply-with-context | 0.671 | react.dev/learn/passing-data-deeply-with-context | 0.621 | react.dev/learn/passing-data-deeply-with-context | 0.599 |
| playwright | miss | react.dev/learn/passing-data-deeply-with-context | 0.678 | react.dev/learn/passing-data-deeply-with-context | 0.672 | react.dev/learn/passing-data-deeply-with-context | 0.637 |


**Q11: How do I conditionally render content in React?**
*(expects URL containing: `conditional`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn | 0.700 | react.dev/ | 0.558 | react.dev/reference/react/useState | 0.507 |
| crawl4ai | miss | react.dev/learn | 0.695 | react.dev/ | 0.576 | react.dev/reference/react/useState | 0.519 |
| crawl4ai-raw | miss | react.dev/learn | 0.695 | react.dev/ | 0.576 | react.dev/reference/react/useState | 0.519 |
| scrapy+md | miss | react.dev/learn | 0.700 | react.dev/ | 0.558 | react.dev/reference/react/useState | 0.507 |
| crawlee | miss | react.dev/learn | 0.700 | react.dev/ | 0.558 | react.dev/reference/react/useState | 0.533 |
| colly+md | miss | react.dev/learn | 0.710 | react.dev/reference/react/useState | 0.540 | react.dev/ | 0.540 |
| playwright | miss | react.dev/learn | 0.700 | react.dev/ | 0.558 | react.dev/reference/react/useState | 0.533 |


**Q12: What is the useMemo hook for in React?**
*(expects URL containing: `useMemo`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | react.dev/learn/react-compiler/introduction | 0.645 | react.dev/learn/typescript | 0.610 | react.dev/learn/react-compiler/introduction | 0.591 |
| crawl4ai | miss | react.dev/learn/react-compiler/introduction | 0.664 | react.dev/learn/typescript | 0.652 | react.dev/learn/react-compiler/introduction | 0.584 |
| crawl4ai-raw | miss | react.dev/learn/react-compiler/introduction | 0.664 | react.dev/learn/typescript | 0.652 | react.dev/learn/react-compiler/introduction | 0.584 |
| scrapy+md | miss | react.dev/learn/react-compiler/introduction | 0.645 | react.dev/learn/typescript | 0.603 | react.dev/learn/react-compiler/introduction | 0.595 |
| crawlee | miss | react.dev/learn/react-compiler/introduction | 0.645 | react.dev/learn/typescript | 0.603 | react.dev/learn/react-compiler/introduction | 0.595 |
| colly+md | miss | react.dev/learn/react-compiler/introduction | 0.633 | react.dev/learn/typescript | 0.600 | react.dev/learn/typescript | 0.583 |
| playwright | miss | react.dev/learn/react-compiler/introduction | 0.645 | react.dev/learn/typescript | 0.603 | react.dev/learn/react-compiler/introduction | 0.595 |


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
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.531 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.519 | en.wikipedia.org/wiki/Python_(programming_language | 0.517 | en.wikipedia.org/wiki/Python_(programming_language | 0.511 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.519 | en.wikipedia.org/wiki/Python_(programming_language | 0.517 | en.wikipedia.org/wiki/Python_(programming_language | 0.511 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.565 | en.wikipedia.org/wiki/Python_(programming_language | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.530 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.559 | en.wikipedia.org/wiki/Python_(programming_language | 0.532 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.565 | en.wikipedia.org/wiki/Python_(programming_language | 0.536 | en.wikipedia.org/wiki/Python_(programming_language | 0.521 |


**Q2: What is the history and development of Python?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.634 | en.wikipedia.org/wiki/Python_(programming_language | 0.586 | en.wikipedia.org/wiki/Python_(programming_language | 0.584 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.591 | en.wikipedia.org/wiki/Python_(programming_language | 0.574 | en.wikipedia.org/wiki/Python_(programming_language | 0.560 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.591 | en.wikipedia.org/wiki/Python_(programming_language | 0.574 | en.wikipedia.org/wiki/Python_(programming_language | 0.560 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.637 | en.wikipedia.org/wiki/Python_(programming_language | 0.586 | en.wikipedia.org/wiki/Python_(programming_language | 0.584 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.637 | en.wikipedia.org/wiki/Python_(programming_language | 0.586 | en.wikipedia.org/wiki/Python_(programming_language | 0.584 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.643 | en.wikipedia.org/wiki/Python_(programming_language | 0.578 | en.wikipedia.org/wiki/Python_(programming_language | 0.573 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.637 | en.wikipedia.org/wiki/Python_(programming_language | 0.586 | en.wikipedia.org/wiki/Python_(programming_language | 0.584 |


**Q3: What programming paradigms does Python support?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.599 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/Python_(programming_language | 0.559 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.632 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.632 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/Python_(programming_language | 0.542 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.599 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/List_comprehensions | 0.534 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.599 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/List_comprehensions | 0.533 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.591 | en.wikipedia.org/wiki/Python_(programming_language | 0.563 | en.wikipedia.org/wiki/List_comprehensions | 0.540 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.599 | en.wikipedia.org/wiki/Python_(programming_language | 0.567 | en.wikipedia.org/wiki/List_comprehensions | 0.534 |


**Q4: What is the Python Software Foundation?**
*(expects URL containing: `Python_Software_Foundation`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.486 | en.wikipedia.org/wiki/Python_(programming_language | 0.474 | en.wikipedia.org/wiki/Python_(programming_language | 0.460 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.505 | en.wikipedia.org/wiki/Python_(programming_language | 0.471 | en.wikipedia.org/wiki/Python_(programming_language | 0.453 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.505 | en.wikipedia.org/wiki/Python_(programming_language | 0.471 | en.wikipedia.org/wiki/Python_(programming_language | 0.453 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.498 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 | en.wikipedia.org/wiki/Python_(programming_language | 0.474 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.496 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 | en.wikipedia.org/wiki/Python_(programming_language | 0.474 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.501 | en.wikipedia.org/wiki/Python_(programming_language | 0.484 | en.wikipedia.org/wiki/Python_(programming_language | 0.469 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.498 | en.wikipedia.org/wiki/Python_(programming_language | 0.486 | en.wikipedia.org/wiki/Python_(programming_language | 0.474 |


**Q5: What is the syntax and design philosophy of Python?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.690 | en.wikipedia.org/wiki/Python_(programming_language | 0.640 | en.wikipedia.org/wiki/Python_(programming_language | 0.616 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.724 | en.wikipedia.org/wiki/Python_(programming_language | 0.644 | en.wikipedia.org/wiki/Python_(programming_language | 0.604 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.724 | en.wikipedia.org/wiki/Python_(programming_language | 0.644 | en.wikipedia.org/wiki/Python_(programming_language | 0.604 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.690 | en.wikipedia.org/wiki/Python_(programming_language | 0.640 | en.wikipedia.org/wiki/Python_(programming_language | 0.616 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.690 | en.wikipedia.org/wiki/Python_(programming_language | 0.640 | en.wikipedia.org/wiki/Python_(programming_language | 0.616 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.694 | en.wikipedia.org/wiki/Python_(programming_language | 0.639 | en.wikipedia.org/wiki/Python_(programming_language | 0.614 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.690 | en.wikipedia.org/wiki/Python_(programming_language | 0.640 | en.wikipedia.org/wiki/Python_(programming_language | 0.616 |


**Q6: What are Python's standard library modules?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.657 | en.wikipedia.org/wiki/Python_(programming_language | 0.499 | en.wikipedia.org/wiki/Python_(programming_language | 0.494 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.653 | en.wikipedia.org/wiki/Python_(programming_language | 0.552 | en.wikipedia.org/wiki/Biopython | 0.537 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.653 | en.wikipedia.org/wiki/Python_(programming_language | 0.552 | en.wikipedia.org/wiki/Biopython | 0.537 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.657 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Biopython | 0.529 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.657 | en.wikipedia.org/wiki/Python_(programming_language | 0.541 | en.wikipedia.org/wiki/Biopython | 0.529 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.643 | en.wikipedia.org/wiki/Python_(programming_language | 0.534 | en.wikipedia.org/wiki/Biopython | 0.529 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.657 | en.wikipedia.org/wiki/Python_(programming_language | 0.533 | en.wikipedia.org/wiki/Biopython | 0.529 |


**Q7: Who is Guido van Rossum?**
*(expects URL containing: `Guido_van_Rossum`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.441 | en.wikipedia.org/wiki/Python_(programming_language | 0.438 | en.wikipedia.org/wiki/Python_(programming_language | 0.421 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.475 | en.wikipedia.org/wiki/Python_(programming_language | 0.413 | en.wikipedia.org/wiki/Python_(programming_language | 0.400 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.475 | en.wikipedia.org/wiki/Python_(programming_language | 0.413 | en.wikipedia.org/wiki/Python_(programming_language | 0.400 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.481 | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.416 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.452 | en.wikipedia.org/wiki/Python_(programming_language | 0.422 | en.wikipedia.org/wiki/Python_(programming_language | 0.416 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.472 | en.wikipedia.org/wiki/Python_(programming_language | 0.460 | en.wikipedia.org/wiki/Python_(programming_language | 0.417 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.481 | en.wikipedia.org/wiki/Python_(programming_language | 0.470 | en.wikipedia.org/wiki/Python_(programming_language | 0.416 |


**Q8: What is CPython and how does it work?**
*(expects URL containing: `CPython`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.493 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.521 | en.wikipedia.org/wiki/Python_(programming_language | 0.511 | en.wikipedia.org/wiki/Python_(programming_language | 0.482 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.521 | en.wikipedia.org/wiki/Python_(programming_language | 0.511 | en.wikipedia.org/wiki/Python_(programming_language | 0.482 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.493 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.493 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.521 | en.wikipedia.org/wiki/Python_(programming_language | 0.501 | en.wikipedia.org/wiki/Python_(programming_language | 0.477 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 | en.wikipedia.org/wiki/Python_(programming_language | 0.493 |


**Q9: How does Python compare to other programming languages?**
*(expects URL containing: `Comparison_of_programming_languages`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.626 | en.wikipedia.org/wiki/Python_(programming_language | 0.620 |
| crawl4ai | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.662 | en.wikipedia.org/wiki/Python_(programming_language | 0.636 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| crawl4ai-raw | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.662 | en.wikipedia.org/wiki/Python_(programming_language | 0.636 | en.wikipedia.org/wiki/Python_(programming_language | 0.629 |
| scrapy+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.626 | en.wikipedia.org/wiki/Python_(programming_language | 0.620 |
| crawlee | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.626 | en.wikipedia.org/wiki/Python_(programming_language | 0.620 |
| colly+md | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.656 | en.wikipedia.org/wiki/Python_(programming_language | 0.587 | en.wikipedia.org/wiki/Python_(programming_language | 0.580 |
| playwright | miss | en.wikipedia.org/wiki/Python_(programming_language | 0.670 | en.wikipedia.org/wiki/Python_(programming_language | 0.626 | en.wikipedia.org/wiki/Python_(programming_language | 0.620 |


**Q10: What are Python Enhancement Proposals (PEPs)?**
*(expects URL containing: `Python_(programming_language)`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.518 | en.wikipedia.org/wiki/Python_(programming_language | 0.504 |
| crawl4ai | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.512 | en.wikipedia.org/wiki/Python_(programming_language | 0.491 | en.wikipedia.org/wiki/Python_(programming_language | 0.475 |
| crawl4ai-raw | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.512 | en.wikipedia.org/wiki/Python_(programming_language | 0.491 | en.wikipedia.org/wiki/Python_(programming_language | 0.475 |
| scrapy+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.539 | en.wikipedia.org/wiki/Python_(programming_language | 0.518 | en.wikipedia.org/wiki/Python_(programming_language | 0.498 |
| crawlee | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.520 | en.wikipedia.org/wiki/Python_(programming_language | 0.518 | en.wikipedia.org/wiki/Python_(programming_language | 0.508 |
| colly+md | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.537 | en.wikipedia.org/wiki/Python_(programming_language | 0.528 | en.wikipedia.org/wiki/Python_(programming_language | 0.492 |
| playwright | #1 | en.wikipedia.org/wiki/Python_(programming_language | 0.539 | en.wikipedia.org/wiki/Python_(programming_language | 0.518 | en.wikipedia.org/wiki/Python_(programming_language | 0.498 |


</details>

## stripe-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.117 | 290 | 25 |
| crawl4ai | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.114 | 352 | 25 |
| crawl4ai-raw | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.114 | 352 | 25 |
| scrapy+md | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.114 | 306 | 25 |
| crawlee | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.111 | 1189 | 25 |
| colly+md | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 20% (2/10) | 0.125 | 1138 | 25 |
| playwright | 10% (1/10) | 10% (1/10) | 10% (1/10) | 20% (2/10) | 20% (2/10) | 0.110 | 1192 | 25 |

<details>
<summary>Query-by-query results for stripe-docs</summary>

**Q1: How do I create a payment intent with Stripe?**
*(expects URL containing: `payment-intent`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.611 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.594 |
| crawl4ai | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.621 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.610 | docs.stripe.com/get-started/data-migrations/pan-im | 0.580 |
| crawl4ai-raw | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.622 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.610 | docs.stripe.com/get-started/data-migrations/pan-im | 0.580 |
| scrapy+md | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.611 | docs.stripe.com/get-started/account/add-funds | 0.589 |
| crawlee | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.634 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.611 |
| colly+md | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.632 | docs.stripe.com/get-started/account | 0.596 | docs.stripe.com/get-started/data-migrations/map-pa | 0.582 |
| playwright | #1 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.634 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.619 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.611 |


**Q2: How do I handle webhooks from Stripe?**
*(expects URL containing: `webhook`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/agents-billing-workflows | 0.567 | docs.stripe.com/ach-deprecated | 0.545 | docs.stripe.com/ach-deprecated | 0.523 |
| crawl4ai | miss | docs.stripe.com/agents-billing-workflows | 0.650 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.573 | docs.stripe.com/ach-deprecated | 0.551 |
| crawl4ai-raw | miss | docs.stripe.com/agents-billing-workflows | 0.650 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.573 | docs.stripe.com/ach-deprecated | 0.551 |
| scrapy+md | miss | docs.stripe.com/agents-billing-workflows | 0.568 | docs.stripe.com/ach-deprecated | 0.550 | docs.stripe.com/ach-deprecated | 0.524 |
| crawlee | miss | docs.stripe.com/agents-billing-workflows | 0.568 | docs.stripe.com/ach-deprecated | 0.556 | docs.stripe.com/agents-billing-workflows | 0.532 |
| colly+md | miss | docs.stripe.com/agents-billing-workflows | 0.564 | docs.stripe.com/agents-billing-workflows | 0.529 | docs.stripe.com/ach-deprecated | 0.524 |
| playwright | miss | docs.stripe.com/agents-billing-workflows | 0.568 | docs.stripe.com/ach-deprecated | 0.556 | docs.stripe.com/agents-billing-workflows | 0.531 |


**Q3: How do I set up Stripe subscriptions?**
*(expects URL containing: `subscription`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/orgs/sharing/c | 0.589 | docs.stripe.com/get-started/account/add-funds | 0.571 | docs.stripe.com/get-started/account/orgs/setup | 0.570 |
| crawl4ai | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.603 | docs.stripe.com/get-started/account | 0.600 | docs.stripe.com/get-started/account/add-funds | 0.598 |
| crawl4ai-raw | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.603 | docs.stripe.com/get-started/account | 0.600 | docs.stripe.com/get-started/account/add-funds | 0.598 |
| scrapy+md | miss | docs.stripe.com/get-started/account | 0.601 | docs.stripe.com/get-started/account/add-funds | 0.592 | docs.stripe.com/get-started/account/orgs/setup | 0.589 |
| crawlee | miss | docs.stripe.com/get-started/account | 0.615 | docs.stripe.com/get-started/account | 0.601 | docs.stripe.com/get-started/account/add-funds | 0.593 |
| colly+md | miss | docs.stripe.com/get-started/account | 0.652 | docs.stripe.com/get-started/account | 0.651 | docs.stripe.com/get-started/account/orgs/sharing/c | 0.634 |
| playwright | miss | docs.stripe.com/get-started/account | 0.615 | docs.stripe.com/get-started/account | 0.601 | docs.stripe.com/get-started/account/add-funds | 0.592 |


**Q4: How do I authenticate with the Stripe API?**
*(expects URL containing: `authentication`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/activate | 0.607 | docs.stripe.com/get-started/account/activate | 0.581 | docs.stripe.com/get-started/account/orgs/team | 0.581 |
| crawl4ai | miss | docs.stripe.com/get-started/account/activate | 0.605 | docs.stripe.com/get-started/account/orgs/team | 0.591 | docs.stripe.com/get-started/account/activate | 0.587 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account/activate | 0.605 | docs.stripe.com/get-started/account/orgs/team | 0.591 | docs.stripe.com/get-started/account/activate | 0.587 |
| scrapy+md | miss | docs.stripe.com/get-started/account/activate | 0.607 | docs.stripe.com/get-started/account/activate | 0.581 | docs.stripe.com/get-started/account/orgs/team | 0.581 |
| crawlee | miss | docs.stripe.com/get-started/account/activate | 0.607 | docs.stripe.com/get-started/account/activate | 0.581 | docs.stripe.com/get-started/account/orgs/team | 0.581 |
| colly+md | miss | docs.stripe.com/get-started/account/activate | 0.599 | docs.stripe.com/get-started/account | 0.595 | docs.stripe.com/get-started/account/orgs/team | 0.592 |
| playwright | miss | docs.stripe.com/get-started/account/activate | 0.607 | docs.stripe.com/get-started/account/activate | 0.582 | docs.stripe.com/get-started/account/orgs/team | 0.581 |


**Q5: How do I handle errors in the Stripe API?**
*(expects URL containing: `error`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/checklist | 0.517 | docs.stripe.com/get-started/account/checklist | 0.511 | docs.stripe.com/ach-deprecated | 0.498 |
| crawl4ai | miss | docs.stripe.com/get-started/account/checklist | 0.551 | docs.stripe.com/get-started/account/checklist | 0.531 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.528 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account/checklist | 0.551 | docs.stripe.com/get-started/account/checklist | 0.531 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.528 |
| scrapy+md | miss | docs.stripe.com/get-started/account/checklist | 0.507 | docs.stripe.com/get-started/account/add-funds | 0.500 | docs.stripe.com/agents-billing-workflows | 0.498 |
| crawlee | miss | docs.stripe.com/get-started/account/checklist | 0.507 | docs.stripe.com/ach-deprecated | 0.500 | docs.stripe.com/get-started/account/add-funds | 0.499 |
| colly+md | miss | docs.stripe.com/get-started/account/checklist | 0.501 | docs.stripe.com/ach-deprecated | 0.497 | docs.stripe.com/get-started/data-migrations/pan-im | 0.492 |
| playwright | miss | docs.stripe.com/get-started/account/checklist | 0.507 | docs.stripe.com/ach-deprecated | 0.500 | docs.stripe.com/get-started/account/add-funds | 0.499 |


**Q6: How do I create a customer in Stripe?**
*(expects URL containing: `customer`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #6 | docs.stripe.com/get-started/data-migrations/pan-im | 0.604 | docs.stripe.com/get-started/account/activate | 0.592 | docs.stripe.com/get-started/account/activate | 0.591 |
| crawl4ai | #7 | docs.stripe.com/get-started/account | 0.620 | docs.stripe.com/get-started/account/add-funds | 0.611 | docs.stripe.com/get-started/account | 0.609 |
| crawl4ai-raw | #7 | docs.stripe.com/get-started/account | 0.620 | docs.stripe.com/get-started/account/add-funds | 0.611 | docs.stripe.com/get-started/account | 0.609 |
| scrapy+md | #7 | docs.stripe.com/get-started/account | 0.622 | docs.stripe.com/get-started/account | 0.618 | docs.stripe.com/get-started/account/add-funds | 0.614 |
| crawlee | #9 | docs.stripe.com/get-started/account | 0.643 | docs.stripe.com/get-started/account | 0.622 | docs.stripe.com/get-started/account | 0.620 |
| colly+md | #4 | docs.stripe.com/get-started/account | 0.659 | docs.stripe.com/get-started/account | 0.643 | docs.stripe.com/get-started/data-migrations/pan-im | 0.637 |
| playwright | #10 | docs.stripe.com/get-started/account | 0.643 | docs.stripe.com/get-started/account | 0.622 | docs.stripe.com/get-started/account | 0.618 |


**Q7: How do I process refunds with Stripe?**
*(expects URL containing: `refund`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/ach-deprecated | 0.624 | docs.stripe.com/ach-deprecated | 0.586 | docs.stripe.com/get-started/account/add-funds | 0.579 |
| crawl4ai | miss | docs.stripe.com/ach-deprecated | 0.624 | docs.stripe.com/ach-deprecated | 0.594 | docs.stripe.com/get-started/account/add-funds | 0.583 |
| crawl4ai-raw | miss | docs.stripe.com/ach-deprecated | 0.624 | docs.stripe.com/ach-deprecated | 0.594 | docs.stripe.com/get-started/account/add-funds | 0.583 |
| scrapy+md | miss | docs.stripe.com/ach-deprecated | 0.623 | docs.stripe.com/ach-deprecated | 0.586 | docs.stripe.com/get-started/account/add-funds | 0.574 |
| crawlee | miss | docs.stripe.com/ach-deprecated | 0.624 | docs.stripe.com/ach-deprecated | 0.586 | docs.stripe.com/get-started/account/add-funds | 0.574 |
| colly+md | miss | docs.stripe.com/ach-deprecated | 0.601 | docs.stripe.com/ach-deprecated | 0.558 | docs.stripe.com/get-started/account/add-funds | 0.540 |
| playwright | miss | docs.stripe.com/ach-deprecated | 0.624 | docs.stripe.com/ach-deprecated | 0.586 | docs.stripe.com/get-started/account/add-funds | 0.574 |


**Q8: How do I use Stripe checkout for payments?**
*(expects URL containing: `checkout`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.679 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.625 | docs.stripe.com/get-started/account/add-funds | 0.601 |
| crawl4ai | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.648 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.622 | docs.stripe.com/get-started/account/add-funds | 0.620 |
| crawl4ai-raw | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.648 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.622 | docs.stripe.com/get-started/account/add-funds | 0.620 |
| scrapy+md | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.679 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.625 | docs.stripe.com/get-started/account/add-funds | 0.616 |
| crawlee | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.679 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.638 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.625 |
| colly+md | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.648 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.621 | docs.stripe.com/get-started/account | 0.610 |
| playwright | miss | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.679 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.638 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.625 |


**Q9: How do I test Stripe payments in development?**
*(expects URL containing: `test`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/ach-deprecated | 0.574 | docs.stripe.com/ach-deprecated | 0.567 | docs.stripe.com/agents-billing-workflows | 0.556 |
| crawl4ai | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.648 | docs.stripe.com/ach-deprecated | 0.572 | docs.stripe.com/ach-deprecated | 0.554 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/data-migrations/pan-im | 0.648 | docs.stripe.com/ach-deprecated | 0.572 | docs.stripe.com/ach-deprecated | 0.554 |
| scrapy+md | miss | docs.stripe.com/ach-deprecated | 0.577 | docs.stripe.com/ach-deprecated | 0.567 | docs.stripe.com/get-started/account/checklist | 0.543 |
| crawlee | miss | docs.stripe.com/ach-deprecated | 0.573 | docs.stripe.com/ach-deprecated | 0.567 | docs.stripe.com/get-started/account/checklist | 0.540 |
| colly+md | miss | docs.stripe.com/ach-deprecated | 0.590 | docs.stripe.com/get-started/account | 0.552 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.543 |
| playwright | miss | docs.stripe.com/ach-deprecated | 0.573 | docs.stripe.com/ach-deprecated | 0.567 | docs.stripe.com/get-started/account/checklist | 0.543 |


**Q10: What are Stripe Connect and platform payments?**
*(expects URL containing: `connect`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.stripe.com/get-started/account/orgs/setup | 0.651 | docs.stripe.com/ach-deprecated | 0.626 | docs.stripe.com/agentic-commerce/apps/accept-payme | 0.577 |
| crawl4ai | miss | docs.stripe.com/get-started/account/orgs/setup | 0.648 | docs.stripe.com/ach-deprecated | 0.596 | docs.stripe.com/get-started/account/orgs/setup | 0.586 |
| crawl4ai-raw | miss | docs.stripe.com/get-started/account/orgs/setup | 0.648 | docs.stripe.com/ach-deprecated | 0.596 | docs.stripe.com/get-started/account/orgs/setup | 0.586 |
| scrapy+md | miss | docs.stripe.com/get-started/account/orgs/setup | 0.651 | docs.stripe.com/ach-deprecated | 0.628 | docs.stripe.com/get-started/account/orgs/setup | 0.569 |
| crawlee | miss | docs.stripe.com/get-started/account/orgs/setup | 0.651 | docs.stripe.com/ach-deprecated | 0.631 | docs.stripe.com/get-started/account/orgs/setup | 0.582 |
| colly+md | miss | docs.stripe.com/get-started/account/orgs/setup | 0.640 | docs.stripe.com/ach-deprecated | 0.610 | docs.stripe.com/get-started/account/add-funds | 0.552 |
| playwright | miss | docs.stripe.com/get-started/account/orgs/setup | 0.651 | docs.stripe.com/ach-deprecated | 0.631 | docs.stripe.com/get-started/account/orgs/setup | 0.582 |


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
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.468 | github.blog/engineering/infrastructure/building-re | 0.426 | github.blog/engineering/infrastructure/building-re | 0.420 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/building-re | 0.477 | github.blog/engineering/infrastructure/building-re | 0.439 | github.blog/engineering/infrastructure/building-re | 0.427 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/building-re | 0.477 | github.blog/engineering/infrastructure/building-re | 0.439 | github.blog/engineering/infrastructure/building-re | 0.427 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/building-re | 0.466 | github.blog/engineering/infrastructure/building-re | 0.426 | github.blog/engineering/infrastructure/building-re | 0.417 |
| crawlee | #1 | github.blog/engineering/infrastructure/building-re | 0.466 | github.blog/engineering/infrastructure/building-re | 0.426 | github.blog/engineering/infrastructure/building-re | 0.417 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.474 | github.blog/engineering/infrastructure/building-re | 0.426 | github.blog/engineering/infrastructure/building-re | 0.417 |
| playwright | #1 | github.blog/engineering/infrastructure/building-re | 0.466 | github.blog/engineering/infrastructure/building-re | 0.426 | github.blog/engineering/infrastructure/building-re | 0.417 |


**Q2: How do companies handle database migrations at scale?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.506 | github.blog/news-insights/company-news/gh-ost-gith | 0.494 | github.blog/news-insights/company-news/gh-ost-gith | 0.472 |
| crawl4ai | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.505 | github.blog/news-insights/company-news/gh-ost-gith | 0.499 | github.blog/news-insights/company-news/gh-ost-gith | 0.477 |
| crawl4ai-raw | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.505 | github.blog/news-insights/company-news/gh-ost-gith | 0.499 | github.blog/news-insights/company-news/gh-ost-gith | 0.477 |
| scrapy+md | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.504 | github.blog/news-insights/company-news/gh-ost-gith | 0.494 | github.blog/news-insights/company-news/gh-ost-gith | 0.475 |
| crawlee | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.504 | github.blog/news-insights/company-news/gh-ost-gith | 0.494 | github.blog/news-insights/company-news/gh-ost-gith | 0.475 |
| colly+md | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.508 | github.blog/news-insights/company-news/gh-ost-gith | 0.499 | github.blog/news-insights/company-news/gh-ost-gith | 0.463 |
| playwright | #1 | github.blog/news-insights/company-news/gh-ost-gith | 0.504 | github.blog/news-insights/company-news/gh-ost-gith | 0.494 | github.blog/news-insights/company-news/gh-ost-gith | 0.475 |


**Q3: What monitoring and observability tools do engineering teams use?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/the-library/exception-mo | 0.446 | github.blog/news-insights/the-library/exception-mo | 0.409 | github.blog/news-insights/the-library/brubeck/ | 0.406 |
| crawl4ai | #1 | github.blog/news-insights/the-library/exception-mo | 0.460 | github.blog/news-insights/the-library/exception-mo | 0.458 | github.blog/news-insights/the-library/benchmarking | 0.447 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/exception-mo | 0.460 | github.blog/news-insights/the-library/exception-mo | 0.458 | github.blog/news-insights/the-library/benchmarking | 0.447 |
| scrapy+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.448 | github.blog/news-insights/the-library/exception-mo | 0.437 | github.blog/news-insights/the-library/brubeck/ | 0.412 |
| crawlee | #1 | github.blog/news-insights/the-library/exception-mo | 0.448 | github.blog/news-insights/the-library/exception-mo | 0.447 | github.blog/news-insights/the-library/exception-mo | 0.441 |
| colly+md | #1 | github.blog/news-insights/the-library/exception-mo | 0.445 | github.blog/news-insights/the-library/exception-mo | 0.445 | github.blog/engineering/user-experience/like-injec | 0.438 |
| playwright | #1 | github.blog/news-insights/the-library/exception-mo | 0.448 | github.blog/news-insights/the-library/exception-mo | 0.447 | github.blog/news-insights/the-library/exception-mo | 0.441 |


**Q4: How do you implement continuous deployment pipelines?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/engineering-principles/scr | 0.384 | github.blog/engineering/infrastructure/githubs-met | 0.382 | github.blog/engineering/architecture-optimization/ | 0.381 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/githubs-met | 0.399 | github.blog/news-insights/the-library/git-concurre | 0.399 | github.blog/engineering/infrastructure/building-re | 0.398 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/git-concurre | 0.399 | github.blog/engineering/infrastructure/githubs-met | 0.399 | github.blog/engineering/infrastructure/building-re | 0.398 |
| scrapy+md | #1 | github.blog/news-insights/the-library/runnable-doc | 0.376 | github.blog/engineering/architecture-optimization/ | 0.369 | github.blog/engineering/engineering-principles/scr | 0.369 |
| crawlee | #1 | github.blog/engineering/infrastructure/context-awa | 0.398 | github.blog/news-insights/the-library/git-concurre | 0.396 | github.blog/engineering/engineering-principles/scr | 0.395 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.389 | github.blog/engineering/engineering-principles/scr | 0.384 | github.blog/engineering/engineering-principles/scr | 0.384 |
| playwright | #1 | github.blog/engineering/infrastructure/context-awa | 0.398 | github.blog/news-insights/the-library/git-concurre | 0.396 | github.blog/engineering/engineering-principles/scr | 0.395 |


**Q5: What are common microservices architecture patterns?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/engineering-principles/scr | 0.301 | github.blog/engineering/infrastructure/building-re | 0.288 | github.blog/engineering/infrastructure/orchestrato | 0.288 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/context-awa | 0.297 | github.blog/engineering/engineering-principles/scr | 0.290 | github.blog/engineering/infrastructure/githubs-met | 0.281 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/context-awa | 0.297 | github.blog/engineering/engineering-principles/scr | 0.290 | github.blog/engineering/infrastructure/githubs-met | 0.281 |
| scrapy+md | #1 | github.blog/engineering/engineering-principles/scr | 0.301 | github.blog/engineering/infrastructure/building-re | 0.288 | github.blog/engineering/infrastructure/orchestrato | 0.288 |
| crawlee | #1 | github.blog/engineering/engineering-principles/scr | 0.301 | github.blog/engineering/infrastructure/building-re | 0.288 | github.blog/engineering/infrastructure/orchestrato | 0.288 |
| colly+md | #1 | github.blog/engineering/user-experience/like-injec | 0.328 | github.blog/engineering/infrastructure/githubs-met | 0.326 | github.blog/engineering/infrastructure/context-awa | 0.321 |
| playwright | #1 | github.blog/engineering/engineering-principles/scr | 0.301 | github.blog/engineering/infrastructure/building-re | 0.288 | github.blog/engineering/infrastructure/orchestrato | 0.288 |


**Q6: How do you handle API versioning in production?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/engineering/engineering-principles/mov | 0.320 | github.blog/news-insights/the-library/runnable-doc | 0.320 |
| crawl4ai | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/news-insights/the-library/runnable-doc | 0.335 | github.blog/engineering/engineering-principles/mov | 0.330 |
| crawl4ai-raw | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/news-insights/the-library/runnable-doc | 0.335 | github.blog/engineering/engineering-principles/mov | 0.330 |
| scrapy+md | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/engineering/engineering-principles/mov | 0.321 | github.blog/news-insights/the-library/runnable-doc | 0.320 |
| crawlee | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/engineering/engineering-principles/mov | 0.321 | github.blog/news-insights/the-library/runnable-doc | 0.320 |
| colly+md | #1 | github.blog/news-insights/the-library/runnable-doc | 0.333 | github.blog/latest/ | 0.314 | github.blog/news-insights/the-library/runnable-doc | 0.312 |
| playwright | #1 | github.blog/news-insights/the-library/runnable-doc | 0.340 | github.blog/engineering/engineering-principles/mov | 0.321 | github.blog/news-insights/the-library/runnable-doc | 0.320 |


**Q7: What caching strategies work best for web applications?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/context-awa | 0.320 | github.blog/engineering/infrastructure/context-awa | 0.315 | github.blog/engineering/user-experience/like-injec | 0.314 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/context-awa | 0.321 | github.blog/engineering/infrastructure/context-awa | 0.317 | github.blog/engineering/infrastructure/context-awa | 0.315 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/context-awa | 0.321 | github.blog/engineering/infrastructure/context-awa | 0.317 | github.blog/engineering/infrastructure/context-awa | 0.315 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/context-awa | 0.315 | github.blog/engineering/user-experience/like-injec | 0.314 | github.blog/engineering/infrastructure/context-awa | 0.310 |
| crawlee | #1 | github.blog/engineering/infrastructure/context-awa | 0.315 | github.blog/engineering/user-experience/like-injec | 0.314 | github.blog/engineering/infrastructure/context-awa | 0.310 |
| colly+md | #1 | github.blog/engineering/user-experience/like-injec | 0.386 | github.blog/engineering/infrastructure/context-awa | 0.375 | github.blog/engineering/infrastructure/context-awa | 0.324 |
| playwright | #1 | github.blog/engineering/infrastructure/context-awa | 0.315 | github.blog/engineering/user-experience/like-injec | 0.314 | github.blog/engineering/infrastructure/context-awa | 0.310 |


**Q8: How do you design for high availability and fault tolerance?**
*(expects URL containing: `blog`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | github.blog/engineering/infrastructure/building-re | 0.464 | github.blog/engineering/infrastructure/building-re | 0.450 | github.blog/engineering/infrastructure/building-re | 0.444 |
| crawl4ai | #1 | github.blog/engineering/infrastructure/building-re | 0.469 | github.blog/engineering/infrastructure/building-re | 0.457 | github.blog/engineering/infrastructure/building-re | 0.452 |
| crawl4ai-raw | #1 | github.blog/engineering/infrastructure/building-re | 0.469 | github.blog/engineering/infrastructure/building-re | 0.457 | github.blog/engineering/infrastructure/building-re | 0.452 |
| scrapy+md | #1 | github.blog/engineering/infrastructure/building-re | 0.461 | github.blog/engineering/infrastructure/building-re | 0.450 | github.blog/engineering/infrastructure/building-re | 0.444 |
| crawlee | #1 | github.blog/engineering/infrastructure/building-re | 0.461 | github.blog/engineering/infrastructure/building-re | 0.450 | github.blog/engineering/infrastructure/building-re | 0.444 |
| colly+md | #1 | github.blog/engineering/infrastructure/building-re | 0.503 | github.blog/engineering/infrastructure/building-re | 0.460 | github.blog/engineering/infrastructure/building-re | 0.457 |
| playwright | #1 | github.blog/engineering/infrastructure/building-re | 0.461 | github.blog/engineering/infrastructure/building-re | 0.450 | github.blog/engineering/infrastructure/building-re | 0.444 |


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

