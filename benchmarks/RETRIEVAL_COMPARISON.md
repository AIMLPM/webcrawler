# Retrieval Quality Comparison

Does each tool's output produce embeddings that answer real questions?
This benchmark chunks each tool's crawl output, embeds it with
`text-embedding-3-small`, and runs the same retrieval queries against each.

**52 queries** across 4 sites.
Hit rate = correct source page in top-K results. Higher is better.

## Summary: hit rate at multiple K values

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Chunks | Avg words |
|---|---|---|---|---|---|---|
| markcrawl | 85% (44/52) ±10% | 94% (49/52) ±7% | 94% (49/52) ±7% | 98% (51/52) ±5% | 1030 | 130 |
| crawl4ai | 83% (43/52) ±10% | 94% (49/52) ±7% | 96% (50/52) ±6% | 96% (50/52) ±6% | 1857 | 105 |
| crawl4ai-raw | 83% (43/52) ±10% | 94% (49/52) ±7% | 96% (50/52) ±6% | 96% (50/52) ±6% | 1857 | 105 |
| scrapy+md | 81% (42/52) ±11% | 92% (48/52) ±8% | 92% (48/52) ±8% | 94% (49/52) ±7% | 1230 | 133 |
| crawlee | 83% (43/52) ±10% | 94% (49/52) ±7% | 96% (50/52) ±6% | 96% (50/52) ±6% | 1279 | 137 |
| colly+md | 83% (43/52) ±10% | 92% (48/52) ±8% | 94% (49/52) ±7% | 94% (49/52) ±7% | 1269 | 137 |
| playwright | 83% (43/52) ±10% | 96% (50/52) ±6% | 96% (50/52) ±6% | 96% (50/52) ±6% | 1279 | 137 |
| firecrawl | 10% (5/52) ±8% | 12% (6/52) ±9% | 13% (7/52) ±9% | 15% (8/52) ±10% | 1623 | 144 |


## quotes-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|---|---|
| markcrawl | 83% (10/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 21 | 15 | 1.0s |
| crawl4ai | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 20 | 15 | 0.6s |
| crawl4ai-raw | 92% (11/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 20 | 15 | 0.5s |
| scrapy+md | 83% (10/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 22 | 15 | 0.7s |
| crawlee | 75% (9/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 24 | 15 | 0.5s |
| colly+md | 75% (9/12) | 92% (11/12) | 100% (12/12) | 100% (12/12) | 24 | 15 | 0.5s |
| playwright | 75% (9/12) | 100% (12/12) | 100% (12/12) | 100% (12/12) | 24 | 15 | 0.3s |
| firecrawl | 8% (1/12) | 8% (1/12) | 8% (1/12) | 8% (1/12) | 18 | 15 | 0.4s |

<details>
<summary>Query-by-query results for quotes-toscrape</summary>

**Q1: What did Albert Einstein say about thinking and the world?**
*(expects URL containing: `quotes.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.421 | quotes.toscrape.com/tag/change/page/1/ | 0.379 | quotes.toscrape.com/ | 0.379 |
| crawl4ai | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.481 | quotes.toscrape.com/tag/change/page/1/ | 0.435 | quotes.toscrape.com/tag/live/page/1/ | 0.361 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.481 | quotes.toscrape.com/tag/change/page/1/ | 0.433 | quotes.toscrape.com/tag/live/page/1/ | 0.362 |
| scrapy+md | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.405 | quotes.toscrape.com/ | 0.367 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 |
| crawlee | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| colly+md | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| playwright | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| firecrawl | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.544 | quotes.toscrape.com/author/Albert-Einstein/ | 0.535 | quotes.toscrape.com/author/Albert-Einstein/ | 0.465 |


**Q2: Which quotes are tagged with 'inspirational'?**
*(expects URL containing: `tag/inspirational`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.584 | quotes.toscrape.com/ | 0.578 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.558 |
| crawl4ai | #2 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.580 | quotes.toscrape.com/tag/live/page/1/ | 0.575 |
| crawl4ai-raw | #2 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.580 | quotes.toscrape.com/tag/live/page/1/ | 0.575 |
| scrapy+md | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.584 | quotes.toscrape.com/ | 0.567 | quotes.toscrape.com/tag/miracles/page/1/ | 0.566 |
| crawlee | #5 | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/tag/live/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| colly+md | #5 | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/tag/live/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| playwright | #2 | quotes.toscrape.com/tag/miracles/page/1/ | 0.586 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| firecrawl | miss | quotes.toscrape.com | 0.576 | quotes.toscrape.com/page/683/ | 0.535 | quotes.toscrape.com/page/539/ | 0.535 |


**Q3: What did Jane Austen say about novels and reading?**
*(expects URL containing: `author/Jane-Austen`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/Jane-Austen | 0.554 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.379 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| crawl4ai | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/page/1/ | 0.321 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/page/1/ | 0.322 |
| scrapy+md | #1 | quotes.toscrape.com/author/Jane-Austen/ | 0.532 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/tag/humor/page/1/ | 0.334 |
| crawlee | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| colly+md | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| playwright | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| firecrawl | miss | quotes.toscrape.com | 0.293 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.280 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.249 |


**Q4: What quotes are about the truth?**
*(expects URL containing: `tag/truth`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/truth/ | 0.564 | quotes.toscrape.com/ | 0.474 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.451 |
| crawl4ai | #1 | quotes.toscrape.com/tag/truth/ | 0.594 | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.453 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/truth/ | 0.594 | quotes.toscrape.com/ | 0.463 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.453 |
| scrapy+md | #1 | quotes.toscrape.com/tag/truth/ | 0.561 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.451 | quotes.toscrape.com/ | 0.451 |
| crawlee | #1 | quotes.toscrape.com/tag/truth/ | 0.552 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.451 |
| colly+md | #1 | quotes.toscrape.com/tag/truth/ | 0.552 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.451 |
| playwright | #1 | quotes.toscrape.com/tag/truth/ | 0.552 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.451 |
| firecrawl | miss | quotes.toscrape.com | 0.466 | quotes.toscrape.com/tableful/tag/christianity/page | 0.420 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.418 |


**Q5: Which quotes are about humor and being funny?**
*(expects URL containing: `tag/humor`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.507 | quotes.toscrape.com/ | 0.462 | quotes.toscrape.com/tag/truth/ | 0.428 |
| crawl4ai | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.513 | quotes.toscrape.com/author/Steve-Martin | 0.468 | quotes.toscrape.com/ | 0.446 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.513 | quotes.toscrape.com/author/Steve-Martin | 0.468 | quotes.toscrape.com/ | 0.446 |
| scrapy+md | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.494 | quotes.toscrape.com/author/Steve-Martin/ | 0.450 | quotes.toscrape.com/ | 0.429 |
| crawlee | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.499 | quotes.toscrape.com/author/Steve-Martin | 0.470 | quotes.toscrape.com/ | 0.444 |
| colly+md | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.499 | quotes.toscrape.com/author/Steve-Martin | 0.471 | quotes.toscrape.com/ | 0.444 |
| playwright | #1 | quotes.toscrape.com/tag/humor/page/1/ | 0.499 | quotes.toscrape.com/author/Steve-Martin | 0.471 | quotes.toscrape.com/ | 0.444 |
| firecrawl | miss | quotes.toscrape.com | 0.451 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.383 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.374 |


**Q6: What did J.K. Rowling say about choices and abilities?**
*(expects URL containing: `author/J-K-Rowling`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| crawl4ai | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.418 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.529 | quotes.toscrape.com/author/J-K-Rowling | 0.509 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.418 |
| scrapy+md | #1 | quotes.toscrape.com/author/J-K-Rowling/ | 0.501 | quotes.toscrape.com/author/J-K-Rowling/ | 0.477 | quotes.toscrape.com/author/J-K-Rowling/ | 0.468 |
| crawlee | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| colly+md | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| playwright | #1 | quotes.toscrape.com/author/J-K-Rowling | 0.501 | quotes.toscrape.com/author/J-K-Rowling | 0.477 | quotes.toscrape.com/author/J-K-Rowling | 0.468 |
| firecrawl | miss | quotes.toscrape.com | 0.305 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.304 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.192 |


**Q7: What quotes are tagged with 'change'?**
*(expects URL containing: `tag/change`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.576 | quotes.toscrape.com/tag/thinking/page/1/ | 0.504 | quotes.toscrape.com/ | 0.489 |
| crawl4ai | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.628 | quotes.toscrape.com/tag/thinking/page/1/ | 0.525 | quotes.toscrape.com/ | 0.487 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.628 | quotes.toscrape.com/tag/thinking/page/1/ | 0.525 | quotes.toscrape.com/ | 0.487 |
| scrapy+md | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.579 | quotes.toscrape.com/tag/thinking/page/1/ | 0.517 | quotes.toscrape.com/ | 0.484 |
| crawlee | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.558 | quotes.toscrape.com/tag/thinking/page/1/ | 0.504 | quotes.toscrape.com/ | 0.489 |
| colly+md | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.559 | quotes.toscrape.com/tag/thinking/page/1/ | 0.504 | quotes.toscrape.com/ | 0.489 |
| playwright | #1 | quotes.toscrape.com/tag/change/page/1/ | 0.559 | quotes.toscrape.com/tag/thinking/page/1/ | 0.504 | quotes.toscrape.com/ | 0.489 |
| firecrawl | miss | quotes.toscrape.com | 0.478 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.422 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.416 |


**Q8: What did Steve Martin say about sunshine?**
*(expects URL containing: `author/Steve-Martin`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/Steve-Martin | 0.558 | quotes.toscrape.com/tag/obvious/page/1/ | 0.353 | quotes.toscrape.com/ | 0.306 |
| crawl4ai | #1 | quotes.toscrape.com/author/Steve-Martin | 0.553 | quotes.toscrape.com/tag/obvious/page/1/ | 0.457 | quotes.toscrape.com/tag/humor/page/1/ | 0.308 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Steve-Martin | 0.553 | quotes.toscrape.com/tag/obvious/page/1/ | 0.455 | quotes.toscrape.com/tag/humor/page/1/ | 0.308 |
| scrapy+md | #1 | quotes.toscrape.com/author/Steve-Martin/ | 0.538 | quotes.toscrape.com/tag/obvious/page/1/ | 0.367 | quotes.toscrape.com/tag/humor/page/1/ | 0.294 |
| crawlee | #1 | quotes.toscrape.com/author/Steve-Martin | 0.464 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.287 | quotes.toscrape.com/tag/obvious/page/1/ | 0.285 |
| colly+md | #1 | quotes.toscrape.com/author/Steve-Martin | 0.464 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.287 | quotes.toscrape.com/tag/obvious/page/1/ | 0.285 |
| playwright | #1 | quotes.toscrape.com/author/Steve-Martin | 0.464 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.287 | quotes.toscrape.com/tag/obvious/page/1/ | 0.285 |
| firecrawl | miss | quotes.toscrape.com/tableful/tag/christianity/page | 0.303 | quotes.toscrape.com | 0.293 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.227 |


**Q9: Which quotes talk about believing in yourself?**
*(expects URL containing: `tag/be-yourself`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.459 | quotes.toscrape.com/ | 0.417 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.416 |
| crawl4ai | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.435 | quotes.toscrape.com/ | 0.422 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.475 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.435 | quotes.toscrape.com/ | 0.422 |
| scrapy+md | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.459 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.417 | quotes.toscrape.com/ | 0.416 |
| crawlee | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.459 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 | quotes.toscrape.com/ | 0.422 |
| colly+md | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.459 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 | quotes.toscrape.com/ | 0.422 |
| playwright | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.461 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.428 | quotes.toscrape.com/ | 0.422 |
| firecrawl | miss | quotes.toscrape.com | 0.405 | quotes.toscrape.com/tableful/tag/christianity/page | 0.395 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.369 |


**Q10: What are the quotes about miracles and living life?**
*(expects URL containing: `tag/miracle`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.572 | quotes.toscrape.com/tag/miracle/page/1/ | 0.570 | quotes.toscrape.com/tag/live/page/1/ | 0.549 |
| crawl4ai | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.656 | quotes.toscrape.com/tag/miracle/page/1/ | 0.653 | quotes.toscrape.com/tag/live/page/1/ | 0.624 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.656 | quotes.toscrape.com/tag/miracle/page/1/ | 0.653 | quotes.toscrape.com/tag/live/page/1/ | 0.623 |
| scrapy+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.586 | quotes.toscrape.com/tag/miracle/page/1/ | 0.586 | quotes.toscrape.com/tag/live/page/1/ | 0.554 |
| crawlee | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/miracle/page/1/ | 0.559 | quotes.toscrape.com/tag/live/page/1/ | 0.541 |
| colly+md | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/miracle/page/1/ | 0.559 | quotes.toscrape.com/tag/live/page/1/ | 0.541 |
| playwright | #1 | quotes.toscrape.com/tag/miracles/page/1/ | 0.567 | quotes.toscrape.com/tag/miracle/page/1/ | 0.559 | quotes.toscrape.com/tag/live/page/1/ | 0.541 |
| firecrawl | miss | quotes.toscrape.com | 0.480 | quotes.toscrape.com/tableful/tag/christianity/page | 0.426 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.392 |


**Q11: What quotes are about thinking deeply?**
*(expects URL containing: `tag/thinking`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.536 | quotes.toscrape.com/tag/change/page/1/ | 0.491 | quotes.toscrape.com/ | 0.481 |
| crawl4ai | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.594 | quotes.toscrape.com/tag/change/page/1/ | 0.544 | quotes.toscrape.com/ | 0.496 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.594 | quotes.toscrape.com/tag/change/page/1/ | 0.544 | quotes.toscrape.com/ | 0.497 |
| scrapy+md | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.546 | quotes.toscrape.com/tag/change/page/1/ | 0.497 | quotes.toscrape.com/ | 0.490 |
| crawlee | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.531 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| colly+md | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.531 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| playwright | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.531 | quotes.toscrape.com/tag/change/page/1/ | 0.494 | quotes.toscrape.com/ | 0.491 |
| firecrawl | miss | quotes.toscrape.com | 0.468 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.415 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.401 |


**Q12: What quotes talk about living life fully?**
*(expects URL containing: `tag/live`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.503 | quotes.toscrape.com/ | 0.455 | quotes.toscrape.com/tag/live/page/1/ | 0.451 |
| crawl4ai | #1 | quotes.toscrape.com/tag/live/page/1/ | 0.511 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.495 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.464 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/live/page/1/ | 0.510 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.495 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.464 |
| scrapy+md | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.503 | quotes.toscrape.com/tag/live/page/1/ | 0.464 | quotes.toscrape.com/ | 0.449 |
| crawlee | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.503 | quotes.toscrape.com/tag/live/page/1/ | 0.469 | quotes.toscrape.com/ | 0.455 |
| colly+md | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.503 | quotes.toscrape.com/tag/live/page/1/ | 0.469 | quotes.toscrape.com/ | 0.455 |
| playwright | #2 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.503 | quotes.toscrape.com/tag/live/page/1/ | 0.469 | quotes.toscrape.com/ | 0.455 |
| firecrawl | miss | quotes.toscrape.com | 0.452 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.392 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.376 |


</details>

## books-toscrape

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|---|---|
| markcrawl | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 114 | 60 | 1.3s |
| crawl4ai | 77% (10/13) | 92% (12/13) | 100% (13/13) | 100% (13/13) | 675 | 60 | 4.7s |
| crawl4ai-raw | 77% (10/13) | 92% (12/13) | 100% (13/13) | 100% (13/13) | 675 | 60 | 4.6s |
| scrapy+md | 92% (12/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 127 | 60 | 1.7s |
| crawlee | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 131 | 60 | 1.5s |
| colly+md | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 131 | 60 | 0.8s |
| playwright | 100% (13/13) | 100% (13/13) | 100% (13/13) | 100% (13/13) | 131 | 60 | 1.9s |
| firecrawl | 15% (2/13) | 23% (3/13) | 23% (3/13) | 23% (3/13) | 538 | 60 | 3.9s |

<details>
<summary>Query-by-query results for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/catalogue/category/books_1/inde | 0.488 | books.toscrape.com/catalogue/category/books/food-a | 0.485 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/novels | 0.491 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/novels | 0.491 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.495 | books.toscrape.com | 0.494 | books.toscrape.com/catalogue/jane-eyre_27/index.ht | 0.481 |


**Q2: What mystery and thriller books are in the catalog?**
*(expects URL containing: `mystery`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.468 |
| crawl4ai | #2 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.503 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.503 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.479 | books.toscrape.com/catalogue/category/books/sequen | 0.460 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| firecrawl | miss | books.toscrape.com/catalogue/in-her-wake_980/index | 0.524 | books.toscrape.com/catalogue/far-from-true-promise | 0.489 | books.toscrape.com/catalogue/the-murder-of-roger-a | 0.464 |


**Q3: What is the rating of the most expensive book?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/young- | 0.424 | books.toscrape.com/catalogue/category/books/defaul | 0.417 | books.toscrape.com/catalogue/category/books/scienc | 0.414 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/horror | 0.423 | books.toscrape.com/catalogue/category/books_1/inde | 0.410 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/horror | 0.423 | books.toscrape.com/catalogue/category/books_1/inde | 0.410 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| playwright | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| firecrawl | #1 | books.toscrape.com/catalogue/the-giver-the-giver-q | 0.425 | books.toscrape.com/catalogue/ways-of-seeing_94/ind | 0.414 | books.toscrape.com/catalogue/the-bhagavad-gita_60/ | 0.412 |


**Q4: What science fiction books are available?**
*(expects URL containing: `science-fiction`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.469 | books.toscrape.com/catalogue/libertarianism-for-be | 0.410 | books.toscrape.com/catalogue/category/books/fantas | 0.375 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/category/books/scienc | 0.471 | books.toscrape.com/catalogue/its-only-the-himalaya | 0.465 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.533 | books.toscrape.com/catalogue/category/books/scienc | 0.471 | books.toscrape.com/catalogue/its-only-the-himalaya | 0.465 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/libertarianism-for-be | 0.404 | books.toscrape.com/catalogue/category/books/scienc | 0.394 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/category/books/scienc | 0.466 | books.toscrape.com/catalogue/libertarianism-for-be | 0.404 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/category/books/scienc | 0.466 | books.toscrape.com/catalogue/libertarianism-for-be | 0.404 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/scienc | 0.510 | books.toscrape.com/catalogue/category/books/scienc | 0.466 | books.toscrape.com/catalogue/libertarianism-for-be | 0.404 |
| firecrawl | miss | books.toscrape.com/catalogue/foundation-foundation | 0.484 | books.toscrape.com/catalogue/the-last-girl-the-dom | 0.480 | books.toscrape.com/catalogue/shtum_733/index.html | 0.411 |


**Q5: What horror books are in the catalog?**
*(expects URL containing: `horror`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/horror | 0.509 | books.toscrape.com/catalogue/category/books/sequen | 0.464 | books.toscrape.com/catalogue/the-requiem-red_995/i | 0.437 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/horror | 0.484 | books.toscrape.com/catalogue/category/books/thrill | 0.473 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/horror | 0.492 | books.toscrape.com/catalogue/category/books/horror | 0.484 | books.toscrape.com/catalogue/category/books/thrill | 0.473 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/ | 0.463 | books.toscrape.com/catalogue/category/books/sequen | 0.458 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/horror | 0.515 | books.toscrape.com/catalogue/category/books/horror | 0.511 | books.toscrape.com/ | 0.468 |
| firecrawl | miss | books.toscrape.com/catalogue/counting-thyme_142/in | 0.476 | books.toscrape.com/catalogue/in-her-wake_980/index | 0.470 | books.toscrape.com/catalogue/this-is-where-it-ends | 0.460 |


**Q6: What poetry books can I find?**
*(expects URL containing: `poetry`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.495 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.411 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.406 |
| crawl4ai | #2 | books.toscrape.com/catalogue/page-2.html | 0.506 | books.toscrape.com/catalogue/category/books/poetry | 0.497 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/page-2.html | 0.506 | books.toscrape.com/catalogue/category/books/poetry | 0.498 | books.toscrape.com/catalogue/category/books/poetry | 0.487 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/shakespeares-sonnets_ | 0.401 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.400 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/poetry | 0.545 | books.toscrape.com/catalogue/category/books/poetry | 0.472 | books.toscrape.com/catalogue/a-light-in-the-attic_ | 0.413 |
| firecrawl | miss | books.toscrape.com/catalogue/slow-states-of-collap | 0.503 | books.toscrape.com/catalogue/slow-states-of-collap | 0.453 | books.toscrape.com/catalogue/slow-states-of-collap | 0.445 |


**Q7: What romance novels are available?**
*(expects URL containing: `romance`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.489 | books.toscrape.com/catalogue/category/books/romanc | 0.458 | books.toscrape.com/catalogue/category/books/christ | 0.418 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.520 | books.toscrape.com/catalogue/category/books/womens | 0.477 | books.toscrape.com/catalogue/category/books/romanc | 0.471 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.520 | books.toscrape.com/catalogue/category/books/womens | 0.477 | books.toscrape.com/catalogue/category/books/romanc | 0.471 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.489 | books.toscrape.com/catalogue/category/books/womens | 0.457 | books.toscrape.com/catalogue/category/books/romanc | 0.421 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.488 | books.toscrape.com/catalogue/category/books/womens | 0.457 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.489 | books.toscrape.com/catalogue/category/books/womens | 0.457 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/romanc | 0.493 | books.toscrape.com/catalogue/category/books/romanc | 0.489 | books.toscrape.com/catalogue/category/books/womens | 0.457 |
| firecrawl | miss | books.toscrape.com/catalogue/more-than-music-chasi | 0.494 | books.toscrape.com/catalogue/a-walk-to-remember_31 | 0.485 | books.toscrape.com/catalogue/the-purest-hook-secon | 0.418 |


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
| firecrawl | #2 | books.toscrape.com/catalogue/category/books/histor | 0.453 | books.toscrape.com/catalogue/greek-mythic-history_ | 0.432 | books.toscrape.com/catalogue/political-suicide-mis | 0.429 |


**Q9: What philosophy books are available to read?**
*(expects URL containing: `philosophy`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/philos | 0.439 | books.toscrape.com/catalogue/libertarianism-for-be | 0.405 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.429 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/philos | 0.454 | books.toscrape.com/catalogue/category/books/philos | 0.430 | books.toscrape.com/catalogue/category/books/philos | 0.425 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.415 | books.toscrape.com/catalogue/libertarianism-for-be | 0.363 | books.toscrape.com/catalogue/category/books/psycho | 0.362 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/philos | 0.449 | books.toscrape.com/catalogue/libertarianism-for-be | 0.387 | books.toscrape.com/catalogue/category/books/psycho | 0.380 |
| firecrawl | miss | books.toscrape.com/catalogue/thinking-fast-and-slo | 0.444 | books.toscrape.com/catalogue/becoming-wise-an-inqu | 0.421 | books.toscrape.com/catalogue/greek-mythic-history_ | 0.403 |


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
| firecrawl | miss | books.toscrape.com/catalogue/slow-states-of-collap | 0.389 | books.toscrape.com/catalogue/political-suicide-mis | 0.379 | books.toscrape.com/catalogue/david-and-goliath-und | 0.364 |


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
| firecrawl | miss | books.toscrape.com/catalogue/the-rose-the-dagger-t | 0.505 | books.toscrape.com/catalogue/vampire-girl-vampire- | 0.492 | books.toscrape.com/catalogue/carry-on-warrior-thou | 0.455 |


**Q12: What is the book Sharp Objects about?**
*(expects URL containing: `sharp-objects`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.591 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.485 |
| crawl4ai | #4 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 | books.toscrape.com/catalogue/the-dirty-little-secr | 0.648 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.625 |
| crawl4ai-raw | #4 | books.toscrape.com/catalogue/the-coming-woman-a-no | 0.648 | books.toscrape.com/catalogue/the-dirty-little-secr | 0.648 | books.toscrape.com/catalogue/the-black-maria_991/i | 0.625 |
| scrapy+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.447 |
| crawlee | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| colly+md | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.607 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| playwright | #1 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.606 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.533 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.481 |
| firecrawl | miss | books.toscrape.com/catalogue/bright-lines_11/index | 0.397 | books.toscrape.com/catalogue/the-shack_576/index.h | 0.370 | books.toscrape.com/catalogue/david-and-goliath-und | 0.358 |


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
| firecrawl | miss | books.toscrape.com/catalogue/benjamin-franklin-an- | 0.440 | books.toscrape.com/catalogue/category/books/histor | 0.434 | books.toscrape.com/catalogue/category/books/nonfic | 0.422 |


</details>

## fastapi-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|---|---|
| markcrawl | 80% (12/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 736 | 25 | 4.4s |
| crawl4ai | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 863 | 25 | 6.7s |
| crawl4ai-raw | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 863 | 25 | 6.0s |
| scrapy+md | 80% (12/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 801 | 25 | 6.5s |
| crawlee | 80% (12/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 821 | 25 | 8.1s |
| colly+md | 80% (12/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 821 | 25 | 8.2s |
| playwright | 80% (12/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 821 | 25 | 5.6s |
| firecrawl | 13% (2/15) | 13% (2/15) | 20% (3/15) | 27% (4/15) | 348 | 25 | 3.4s |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/ | 0.565 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 | fastapi.tiangolo.com/tutorial/security/ | 0.570 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 | fastapi.tiangolo.com/tutorial/security/ | 0.570 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| firecrawl | #5 | fastapi.tiangolo.com/alternatives/ | 0.533 | fastapi.tiangolo.com/features/ | 0.514 | fastapi.tiangolo.com/features/ | 0.511 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| playwright | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| firecrawl | #1 | fastapi.tiangolo.com/es/tutorial/path-operation-co | 0.558 | fastapi.tiangolo.com/alternatives/ | 0.548 | fastapi.tiangolo.com/features/ | 0.497 |


**Q3: How do I define query parameters in the FastAPI reference?**
*(expects URL containing: `reference/fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.585 | fastapi.tiangolo.com/reference/ | 0.553 | fastapi.tiangolo.com/reference/fastapi/ | 0.541 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/ | 0.563 | fastapi.tiangolo.com/reference/ | 0.549 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/ | 0.564 | fastapi.tiangolo.com/reference/ | 0.549 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.590 | fastapi.tiangolo.com/reference/fastapi/ | 0.540 | fastapi.tiangolo.com/reference/fastapi/ | 0.517 |
| crawlee | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/fastapi/ | 0.540 | fastapi.tiangolo.com/reference/openapi/models/ | 0.523 |
| colly+md | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.590 | fastapi.tiangolo.com/reference/fastapi/ | 0.541 | fastapi.tiangolo.com/reference/fastapi/ | 0.517 |
| playwright | #1 | fastapi.tiangolo.com/reference/fastapi/ | 0.593 | fastapi.tiangolo.com/reference/fastapi/ | 0.541 | fastapi.tiangolo.com/reference/openapi/models/ | 0.523 |
| firecrawl | #1 | fastapi.tiangolo.com/de/reference/parameters/ | 0.657 | fastapi.tiangolo.com/de/reference/parameters/ | 0.598 | fastapi.tiangolo.com/alternatives/ | 0.550 |


**Q4: How does FastAPI handle JSON encoding and base64 bytes?**
*(expects URL containing: `json-base64-bytes`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.599 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.557 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.655 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.643 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.655 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.645 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.572 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.647 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.579 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.572 |
| playwright | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.647 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.578 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.544 | fastapi.tiangolo.com/features/ | 0.533 | fastapi.tiangolo.com | 0.515 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/reference/openapi/models/ | 0.539 | fastapi.tiangolo.com/reference/openapi/models/ | 0.529 |
| crawl4ai | #3 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/ | 0.548 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.548 |
| crawl4ai-raw | #3 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/ | 0.548 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.548 |
| scrapy+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.555 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.534 |
| crawlee | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.545 | fastapi.tiangolo.com/ | 0.532 |
| colly+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.555 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.541 |
| playwright | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.545 | fastapi.tiangolo.com/ | 0.532 |
| firecrawl | #9 | fastapi.tiangolo.com/de/reference/parameters/ | 0.603 | fastapi.tiangolo.com/features/ | 0.558 | fastapi.tiangolo.com/alternatives/ | 0.555 |


**Q6: How do I use OAuth2 with password flow in FastAPI?**
*(expects URL containing: `simple-oauth2`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.603 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.594 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.672 | fastapi.tiangolo.com/reference/openapi/models/ | 0.672 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.648 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.672 | fastapi.tiangolo.com/reference/openapi/models/ | 0.672 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.648 |
| scrapy+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.603 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.594 |
| crawlee | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.669 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.653 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.644 |
| colly+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.603 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.594 |
| playwright | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.669 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.653 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.644 |
| firecrawl | miss | fastapi.tiangolo.com/zh/tutorial/security/ | 0.506 | fastapi.tiangolo.com/zh/tutorial/security/ | 0.503 | fastapi.tiangolo.com/features/ | 0.503 |


**Q7: How do I use WebSockets in FastAPI?**
*(expects URL containing: `websockets`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.652 | fastapi.tiangolo.com/advanced/websockets/ | 0.597 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/advanced/websockets/ | 0.613 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/advanced/websockets/ | 0.613 |
| playwright | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.551 | fastapi.tiangolo.com/features/ | 0.507 | fastapi.tiangolo.com/alternatives/ | 0.506 |


**Q8: How do I stream data responses in FastAPI?**
*(expects URL containing: `stream-data`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.610 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.655 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 | fastapi.tiangolo.com/advanced/stream-data/ | 0.625 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 | fastapi.tiangolo.com/advanced/stream-data/ | 0.625 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.609 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.616 | fastapi.tiangolo.com/advanced/stream-data/ | 0.607 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.610 |
| playwright | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.616 | fastapi.tiangolo.com/advanced/stream-data/ | 0.607 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.570 | fastapi.tiangolo.com/features/ | 0.538 | fastapi.tiangolo.com | 0.513 |


**Q9: How do I return additional response types in FastAPI?**
*(expects URL containing: `additional-responses`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/additional-responses | 0.600 | fastapi.tiangolo.com/reference/fastapi/ | 0.573 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/additional-responses | 0.617 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/additional-responses | 0.617 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 | fastapi.tiangolo.com/reference/fastapi/ | 0.573 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.656 | fastapi.tiangolo.com/advanced/additional-responses | 0.612 | fastapi.tiangolo.com/reference/fastapi/ | 0.573 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 | fastapi.tiangolo.com/reference/fastapi/ | 0.573 |
| playwright | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.656 | fastapi.tiangolo.com/advanced/additional-responses | 0.612 | fastapi.tiangolo.com/reference/fastapi/ | 0.573 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.561 | fastapi.tiangolo.com/features/ | 0.551 | fastapi.tiangolo.com | 0.548 |


**Q10: How do I write async tests for FastAPI applications?**
*(expects URL containing: `async-tests`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.586 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 | fastapi.tiangolo.com/ | 0.620 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 | fastapi.tiangolo.com/ | 0.620 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.586 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.727 | fastapi.tiangolo.com/advanced/async-tests/ | 0.617 | fastapi.tiangolo.com/advanced/async-tests/ | 0.596 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.586 |
| playwright | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.727 | fastapi.tiangolo.com/advanced/async-tests/ | 0.617 | fastapi.tiangolo.com/advanced/async-tests/ | 0.597 |
| firecrawl | miss | fastapi.tiangolo.com | 0.600 | fastapi.tiangolo.com/alternatives/ | 0.568 | fastapi.tiangolo.com/features/ | 0.552 |


**Q11: How do I define nested Pydantic models for request bodies?**
*(expects URL containing: `body-nested-models`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.562 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.571 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.571 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.562 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.560 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.562 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.560 |
| firecrawl | miss | fastapi.tiangolo.com/features/ | 0.467 | fastapi.tiangolo.com/de/reference/parameters/ | 0.437 | fastapi.tiangolo.com/de/tutorial/body-multiple-par | 0.431 |


**Q12: How do I handle startup and shutdown events in FastAPI?**
*(expects URL containing: `events`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/events/ | 0.660 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/advanced/events/ | 0.603 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/advanced/events/ | 0.633 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/advanced/events/ | 0.633 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/advanced/events/ | 0.621 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/events/ | 0.682 | fastapi.tiangolo.com/advanced/events/ | 0.655 | fastapi.tiangolo.com/advanced/events/ | 0.623 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/advanced/events/ | 0.621 |
| playwright | #1 | fastapi.tiangolo.com/advanced/events/ | 0.682 | fastapi.tiangolo.com/advanced/events/ | 0.655 | fastapi.tiangolo.com/advanced/events/ | 0.623 |
| firecrawl | miss | fastapi.tiangolo.com/features/ | 0.497 | fastapi.tiangolo.com/alternatives/ | 0.489 | fastapi.tiangolo.com | 0.481 |


**Q13: How do I use middleware in FastAPI?**
*(expects URL containing: `middleware`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.677 | fastapi.tiangolo.com/reference/middleware/ | 0.610 | fastapi.tiangolo.com/reference/fastapi/ | 0.584 |
| crawl4ai | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.717 | fastapi.tiangolo.com/reference/middleware/ | 0.651 | fastapi.tiangolo.com/reference/fastapi/ | 0.604 |
| crawl4ai-raw | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.716 | fastapi.tiangolo.com/reference/middleware/ | 0.651 | fastapi.tiangolo.com/reference/fastapi/ | 0.604 |
| scrapy+md | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/reference/middleware/ | 0.610 | fastapi.tiangolo.com/reference/fastapi/ | 0.591 |
| crawlee | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/middleware/ | 0.623 | fastapi.tiangolo.com/reference/fastapi/ | 0.602 |
| colly+md | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/reference/middleware/ | 0.610 | fastapi.tiangolo.com/reference/fastapi/ | 0.591 |
| playwright | #2 | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/reference/middleware/ | 0.623 | fastapi.tiangolo.com/reference/fastapi/ | 0.602 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.589 | fastapi.tiangolo.com/features/ | 0.523 | fastapi.tiangolo.com/fastapi-people/ | 0.489 |


**Q14: How do I use Jinja2 templates in FastAPI?**
*(expects URL containing: `templating`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/templating/ | 0.755 | fastapi.tiangolo.com/reference/templating/ | 0.655 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.513 |
| crawl4ai | #1 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 | fastapi.tiangolo.com/reference/templating/ | 0.678 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 | fastapi.tiangolo.com/reference/templating/ | 0.678 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/reference/templating/ | 0.685 | fastapi.tiangolo.com/reference/templating/ | 0.517 |
| crawlee | #1 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 | fastapi.tiangolo.com/reference/templating/ | 0.535 |
| colly+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/reference/templating/ | 0.685 | fastapi.tiangolo.com/reference/templating/ | 0.583 |
| playwright | #1 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 | fastapi.tiangolo.com/reference/templating/ | 0.577 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.582 | fastapi.tiangolo.com/features/ | 0.537 | fastapi.tiangolo.com/project-generation/ | 0.504 |


**Q15: How do I deploy FastAPI to the cloud?**
*(expects URL containing: `deployment`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #2 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.740 | fastapi.tiangolo.com/ | 0.717 |
| crawl4ai | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.772 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.770 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.772 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.770 |
| scrapy+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/ | 0.754 |
| crawlee | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.768 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.762 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.748 |
| colly+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/ | 0.754 |
| playwright | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.768 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.762 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.748 |
| firecrawl | miss | fastapi.tiangolo.com | 0.753 | fastapi.tiangolo.com | 0.717 | fastapi.tiangolo.com | 0.712 |


</details>

## python-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|---|---|
| markcrawl | 75% (9/12) | 75% (9/12) | 75% (9/12) | 92% (11/12) | 159 | 20 | 10.0s |
| crawl4ai | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 299 | 20 | 4.1s |
| crawl4ai-raw | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 299 | 20 | 2.1s |
| scrapy+md | 67% (8/12) | 67% (8/12) | 67% (8/12) | 75% (9/12) | 280 | 16 | 2.3s |
| crawlee | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 303 | 20 | 3.4s |
| colly+md | 75% (9/12) | 75% (9/12) | 75% (9/12) | 75% (9/12) | 293 | 20 | 2.7s |
| playwright | 75% (9/12) | 83% (10/12) | 83% (10/12) | 83% (10/12) | 303 | 20 | 2.3s |
| firecrawl | 0% (0/12) | 0% (0/12) | 0% (0/12) | 0% (0/12) | 719 | 20 | 4.5s |

<details>
<summary>Query-by-query results for python-docs</summary>

**Q1: What new features were added in Python 3.10?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #7 | docs.python.org/3.10/contents.html | 0.636 | docs.python.org/3.10/ | 0.596 | docs.python.org/3.10/contents.html | 0.588 |
| crawl4ai | #1 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/contents.html | 0.649 |
| crawl4ai-raw | #1 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/contents.html | 0.649 |
| scrapy+md | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| crawlee | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| colly+md | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| playwright | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| firecrawl | miss | docs.python.org/3/library/ | 0.481 | docs.python.org/3/library/stdtypes.html | 0.451 | docs.python.org/3/library/ | 0.448 |


**Q2: What does the term 'decorator' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/glossary.html | 0.585 | docs.python.org/3.10/glossary.html | 0.367 | docs.python.org/3.10/glossary.html | 0.364 |
| crawl4ai | #1 | docs.python.org/3.10/glossary.html | 0.541 | docs.python.org/3.10/glossary.html | 0.397 | docs.python.org/3.10/glossary.html | 0.371 |
| crawl4ai-raw | #1 | docs.python.org/3.10/glossary.html | 0.541 | docs.python.org/3.10/glossary.html | 0.397 | docs.python.org/3.10/glossary.html | 0.371 |
| scrapy+md | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.376 | docs.python.org/3.10/glossary.html | 0.367 |
| crawlee | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.378 | docs.python.org/3.10/glossary.html | 0.367 |
| colly+md | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.376 | docs.python.org/3.10/glossary.html | 0.367 |
| playwright | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.378 | docs.python.org/3.10/glossary.html | 0.367 |
| firecrawl | miss | docs.python.org/3/library/stdtypes.html | 0.434 | docs.python.org/3/library/functions.html | 0.351 | docs.python.org/3/library/multiprocessing.html | 0.330 |


**Q3: How do I report a bug in Python?**
*(expects URL containing: `bugs`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/bugs.html | 0.609 | docs.python.org/bugs.html | 0.585 | docs.python.org/bugs.html | 0.561 |
| crawl4ai | #1 | docs.python.org/bugs.html | 0.668 | docs.python.org/bugs.html | 0.659 | docs.python.org/bugs.html | 0.652 |
| crawl4ai-raw | #1 | docs.python.org/bugs.html | 0.668 | docs.python.org/bugs.html | 0.659 | docs.python.org/bugs.html | 0.652 |
| scrapy+md | #1 | docs.python.org/3/bugs.html | 0.609 | docs.python.org/3.10/using/index.html | 0.588 | docs.python.org/3.10/using/index.html | 0.588 |
| crawlee | #1 | docs.python.org/bugs.html | 0.641 | docs.python.org/bugs.html | 0.640 | docs.python.org/bugs.html | 0.609 |
| colly+md | #1 | docs.python.org/3/bugs.html | 0.609 | docs.python.org/3.10/using/index.html | 0.588 | docs.python.org/3.10/using/index.html | 0.588 |
| playwright | #1 | docs.python.org/bugs.html | 0.642 | docs.python.org/bugs.html | 0.640 | docs.python.org/bugs.html | 0.609 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.573 | docs.python.org/3/library/ | 0.565 | docs.python.org/3/library/exceptions.html | 0.544 |


**Q4: What is structural pattern matching in Python?**
*(expects URL containing: `whatsnew`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/py-modindex.html | 0.360 | docs.python.org/3.10/contents.html | 0.339 | docs.python.org/3.10/glossary.html | 0.330 |
| crawl4ai | miss | docs.python.org/3.10/glossary.html | 0.383 | docs.python.org/3.10/glossary.html | 0.363 | docs.python.org/3.10/contents.html | 0.350 |
| crawl4ai-raw | miss | docs.python.org/3.10/glossary.html | 0.383 | docs.python.org/3.10/glossary.html | 0.363 | docs.python.org/3.10/contents.html | 0.350 |
| scrapy+md | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| crawlee | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| colly+md | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| playwright | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| firecrawl | miss | docs.python.org/3/library/struct.html | 0.390 | docs.python.org/3/library/struct.html | 0.339 | docs.python.org/3/library/ctypes.html | 0.325 |


**Q5: What is Python's glossary definition of a generator?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/glossary.html | 0.513 | docs.python.org/3.10/glossary.html | 0.446 | docs.python.org/3.10/glossary.html | 0.420 |
| crawl4ai | #1 | docs.python.org/3.10/glossary.html | 0.580 | docs.python.org/3.10/glossary.html | 0.478 | docs.python.org/3.10/glossary.html | 0.456 |
| crawl4ai-raw | #1 | docs.python.org/3.10/glossary.html | 0.580 | docs.python.org/3.10/glossary.html | 0.478 | docs.python.org/3.10/glossary.html | 0.456 |
| scrapy+md | #1 | docs.python.org/3.10/glossary.html | 0.521 | docs.python.org/3.10/glossary.html | 0.440 | docs.python.org/3.10/glossary.html | 0.420 |
| crawlee | #1 | docs.python.org/3.10/glossary.html | 0.518 | docs.python.org/3.10/glossary.html | 0.440 | docs.python.org/3.10/glossary.html | 0.420 |
| colly+md | #1 | docs.python.org/3.10/glossary.html | 0.521 | docs.python.org/3.10/glossary.html | 0.440 | docs.python.org/3.10/glossary.html | 0.420 |
| playwright | #1 | docs.python.org/3.10/glossary.html | 0.518 | docs.python.org/3.10/glossary.html | 0.440 | docs.python.org/3.10/glossary.html | 0.420 |
| firecrawl | miss | docs.python.org/3/library/stdtypes.html | 0.524 | docs.python.org/3/library/multiprocessing.html | 0.482 | docs.python.org/3/library/stdtypes.html | 0.450 |


**Q6: What are the Python how-to guides about?**
*(expects URL containing: `howto`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.10/contents.html | 0.593 | docs.python.org/3.10/tutorial/index.html | 0.586 |
| crawl4ai | #1 | docs.python.org/3.10/howto/index.html | 0.744 | docs.python.org/3.10/tutorial/index.html | 0.605 | docs.python.org/3.10/contents.html | 0.600 |
| crawl4ai-raw | #1 | docs.python.org/3.10/howto/index.html | 0.744 | docs.python.org/3.10/tutorial/index.html | 0.605 | docs.python.org/3.10/contents.html | 0.600 |
| scrapy+md | miss | docs.python.org/3.10/tutorial/index.html | 0.586 | docs.python.org/3.10/contents.html | 0.582 | docs.python.org/3.10/contents.html | 0.575 |
| crawlee | #1 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.10/tutorial/index.html | 0.586 | docs.python.org/3.10/contents.html | 0.582 |
| colly+md | #1 | docs.python.org/3.10/howto/index.html | 0.587 | docs.python.org/3.10/tutorial/index.html | 0.586 | docs.python.org/3.10/contents.html | 0.582 |
| playwright | #1 | docs.python.org/3.10/howto/index.html | 0.704 | docs.python.org/3.10/tutorial/index.html | 0.586 | docs.python.org/3.10/contents.html | 0.582 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.522 | docs.python.org/3/library/ | 0.518 | docs.python.org/3/library/intro.html | 0.510 |


**Q7: What is the Python module index?**
*(expects URL containing: `py-modindex`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/py-modindex.html | 0.610 | docs.python.org/3.1/ | 0.582 | docs.python.org/3.2/ | 0.574 |
| crawl4ai | #1 | docs.python.org/3.10/py-modindex.html | 0.579 | docs.python.org/3.10/py-modindex.html | 0.561 | docs.python.org/3.9/ | 0.560 |
| crawl4ai-raw | #1 | docs.python.org/3.10/py-modindex.html | 0.579 | docs.python.org/3.10/py-modindex.html | 0.561 | docs.python.org/3.9/ | 0.560 |
| scrapy+md | miss | docs.python.org/3.10/download.html | 0.608 | docs.python.org/3.10/glossary.html | 0.599 | docs.python.org/3.14/ | 0.598 |
| crawlee | #2 | docs.python.org/3.9/ | 0.582 | docs.python.org/3.10/py-modindex.html | 0.581 | docs.python.org/3.10/download.html | 0.580 |
| colly+md | miss | docs.python.org/3.9/ | 0.614 | docs.python.org/3.10/download.html | 0.608 | docs.python.org/3.10/glossary.html | 0.599 |
| playwright | #2 | docs.python.org/3.9/ | 0.582 | docs.python.org/3.10/py-modindex.html | 0.580 | docs.python.org/3.10/download.html | 0.580 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.535 | docs.python.org/3/library/struct.html | 0.533 | docs.python.org/3/library/struct.html | 0.533 |


**Q8: What Python tutorial topics are available?**
*(expects URL containing: `tutorial`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/howto/index.html | 0.562 | docs.python.org/3.10/contents.html | 0.532 |
| crawl4ai | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/howto/index.html | 0.592 | docs.python.org/3.12/ | 0.548 |
| crawl4ai-raw | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/howto/index.html | 0.592 | docs.python.org/3.12/ | 0.548 |
| scrapy+md | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.12/ | 0.537 | docs.python.org/3.11/ | 0.537 |
| crawlee | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/howto/index.html | 0.562 | docs.python.org/3.12/ | 0.537 |
| colly+md | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/ | 0.537 | docs.python.org/3.11/ | 0.537 |
| playwright | #1 | docs.python.org/3.10/tutorial/index.html | 0.653 | docs.python.org/3.10/howto/index.html | 0.562 | docs.python.org/3.10/ | 0.537 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.535 | docs.python.org/3/library/ | 0.519 | docs.python.org/3/library/ | 0.515 |


**Q9: What is the Python license and copyright?**
*(expects URL containing: `license`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/license.html | 0.613 | docs.python.org/license.html | 0.606 | docs.python.org/license.html | 0.592 |
| crawl4ai | #1 | docs.python.org/license.html | 0.647 | docs.python.org/license.html | 0.626 | docs.python.org/license.html | 0.626 |
| crawl4ai-raw | #1 | docs.python.org/license.html | 0.647 | docs.python.org/license.html | 0.626 | docs.python.org/license.html | 0.626 |
| scrapy+md | #1 | docs.python.org/3/license.html | 0.617 | docs.python.org/3/license.html | 0.613 | docs.python.org/3/license.html | 0.592 |
| crawlee | #1 | docs.python.org/license.html | 0.617 | docs.python.org/license.html | 0.613 | docs.python.org/license.html | 0.592 |
| colly+md | #1 | docs.python.org/3/license.html | 0.617 | docs.python.org/3/license.html | 0.613 | docs.python.org/3/license.html | 0.592 |
| playwright | #1 | docs.python.org/license.html | 0.617 | docs.python.org/license.html | 0.613 | docs.python.org/license.html | 0.592 |
| firecrawl | miss | docs.python.org/3/library/ | 0.405 | docs.python.org/3/library/intro.html | 0.376 | docs.python.org/3/library/ | 0.372 |


**Q10: What is the table of contents for Python 3.10 documentation?**
*(expects URL containing: `contents`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #9 | docs.python.org/3.10/ | 0.710 | docs.python.org/3.5/ | 0.664 | docs.python.org/3.9/ | 0.619 |
| crawl4ai | miss | docs.python.org/3.10/ | 0.686 | docs.python.org/bugs.html | 0.658 | docs.python.org/bugs.html | 0.658 |
| crawl4ai-raw | miss | docs.python.org/3.10/ | 0.686 | docs.python.org/bugs.html | 0.658 | docs.python.org/bugs.html | 0.658 |
| scrapy+md | #9 | docs.python.org/3.10/ | 0.710 | docs.python.org/3.10/download.html | 0.654 | docs.python.org/3/bugs.html | 0.614 |
| crawlee | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.10/download.html | 0.654 | docs.python.org/3.5/ | 0.628 |
| colly+md | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.10/download.html | 0.654 | docs.python.org/3.5/ | 0.636 |
| playwright | miss | docs.python.org/3.10/ | 0.710 | docs.python.org/3.10/download.html | 0.654 | docs.python.org/3.5/ | 0.628 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.646 | docs.python.org/3/library/struct.html | 0.578 | docs.python.org/3/library/logging.html | 0.560 |


**Q11: What does the term 'iterable' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/glossary.html | 0.551 | docs.python.org/3.10/glossary.html | 0.451 | docs.python.org/3.10/glossary.html | 0.433 |
| crawl4ai | #1 | docs.python.org/3.10/glossary.html | 0.597 | docs.python.org/3.10/glossary.html | 0.482 | docs.python.org/3.10/glossary.html | 0.463 |
| crawl4ai-raw | #1 | docs.python.org/3.10/glossary.html | 0.597 | docs.python.org/3.10/glossary.html | 0.482 | docs.python.org/3.10/glossary.html | 0.463 |
| scrapy+md | #1 | docs.python.org/3.10/glossary.html | 0.551 | docs.python.org/3.10/glossary.html | 0.451 | docs.python.org/3.10/glossary.html | 0.439 |
| crawlee | #1 | docs.python.org/3.10/glossary.html | 0.551 | docs.python.org/3.10/glossary.html | 0.451 | docs.python.org/3.10/glossary.html | 0.439 |
| colly+md | #1 | docs.python.org/3.10/glossary.html | 0.551 | docs.python.org/3.10/glossary.html | 0.451 | docs.python.org/3.10/glossary.html | 0.439 |
| playwright | #1 | docs.python.org/3.10/glossary.html | 0.551 | docs.python.org/3.10/glossary.html | 0.451 | docs.python.org/3.10/glossary.html | 0.439 |
| firecrawl | miss | docs.python.org/3/library/functions.html | 0.485 | docs.python.org/3/library/stdtypes.html | 0.485 | docs.python.org/3/library/stdtypes.html | 0.484 |


**Q12: How do I install and configure Python on my system?**
*(expects URL containing: `using`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/using/index.html | 0.509 | docs.python.org/3.10/using/index.html | 0.476 | docs.python.org/3.10/contents.html | 0.456 |
| crawl4ai | #2 | docs.python.org/3.10/contents.html | 0.485 | docs.python.org/3.10/using/index.html | 0.482 | docs.python.org/3.10/glossary.html | 0.482 |
| crawl4ai-raw | #2 | docs.python.org/3.10/contents.html | 0.485 | docs.python.org/3.10/using/index.html | 0.482 | docs.python.org/3.10/glossary.html | 0.482 |
| scrapy+md | #1 | docs.python.org/3.10/using/index.html | 0.509 | docs.python.org/3.10/glossary.html | 0.472 | docs.python.org/3.10/glossary.html | 0.472 |
| crawlee | #1 | docs.python.org/3.10/using/index.html | 0.509 | docs.python.org/3.10/glossary.html | 0.472 | docs.python.org/3.10/glossary.html | 0.472 |
| colly+md | #1 | docs.python.org/3.10/using/index.html | 0.509 | docs.python.org/3.10/glossary.html | 0.472 | docs.python.org/3.10/glossary.html | 0.472 |
| playwright | #1 | docs.python.org/3.10/using/index.html | 0.509 | docs.python.org/3.10/glossary.html | 0.472 | docs.python.org/3.10/glossary.html | 0.472 |
| firecrawl | miss | docs.python.org/3/library/ | 0.437 | docs.python.org/3/library/ | 0.375 | docs.python.org/3/library/intro.html | 0.371 |


</details>

## Methodology

- **Queries:** 52 across 4 sites (verified against crawled pages)
- **Embedding model:** `text-embedding-3-small` (1536 dimensions)
- **Chunking:** Markdown-aware, 400 word max, 50 word overlap
- **Retrieval:** Cosine similarity, hit rate reported at K = 1, 3, 5, 10
- **Confidence intervals:** Wilson score interval (95%)
- **Same chunking and embedding** for all tools — only extraction quality varies
- **No fine-tuning or tool-specific optimization** — identical pipeline for all

