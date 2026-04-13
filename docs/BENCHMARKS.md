# MarkCrawl Benchmarks

Benchmark results from the [llm-crawler-benchmarks](https://github.com/AIMLPM/llm-crawler-benchmarks) suite — 7 tools, 8 sites, 93 queries.

## Speed

| Tool | Pages/sec |
|---|---|
| **markcrawl** | **14.0** |
| scrapy+md | 9.3 |
| colly+md | 6.6 |
| crawl4ai | 2.0 |
| crawlee | 1.4 |

MarkCrawl uses native async I/O (httpx) with concurrent fetching and process-pool HTML extraction. Playwright-based tools are inherently slower due to full browser rendering.

## Output cleanliness

| Tool | Nav pollution (words) | Recall |
|---|---|---|
| **markcrawl** | **4** | 84% |
| scrapy+md | 275 | 91% |
| crawl4ai | 329 | 95% |
| crawlee | 398 | 97% |

Nav pollution = boilerplate words (navigation, footer, cookie banners) that leak into extracted content. Lower is better — less junk means cleaner embeddings and fewer wasted tokens.

## RAG answer quality

| Tool | Chunks/page | Answer Quality (/5) | Hit@5 | Hit@20 |
|---|---|---|---|---|
| **markcrawl** | **10.1** | **3.91** | 80% | 87% |
| scrapy+md | 12.6 | 3.86 | 78% | 85% |
| firecrawl | 13.0 | 4.04* | 82% | 86% |
| crawl4ai | 16.9 | 3.82 | 79% | 85% |
| colly+md | 19.0 | 3.83 | 76% | 84% |
| playwright | 19.8 | 3.74 | 74% | 82% |
| crawlee | 21.1 | 3.80 | 85% | 87% |

*FireCrawl scored on a smaller query set (70 vs 92 queries) due to incomplete crawl coverage.

**Fewer chunks = lower cost.** Each chunk requires an embedding call and vector storage. MarkCrawl produces 2x fewer chunks than crawlee for the same content, cutting embedding and storage costs roughly in half.

## Total cost of ownership

Annual cost estimate for a RAG pipeline: crawling + embedding + vector storage + query-time retrieval.

| Scale | markcrawl | scrapy+md | firecrawl | crawl4ai | crawlee |
|---|---|---|---|---|---|
| 100K pages, 1K queries/day | **$4,505** | $5,464 | $5,835 | $6,960 | $7,467 |

MarkCrawl's cost advantage comes from chunk efficiency — same content coverage with fewer, cleaner chunks means fewer embedding API calls and less vector storage.

For the complete cost analysis across all scales (100 to 1M pages) with full methodology, see [COST_AT_SCALE.md](https://github.com/AIMLPM/llm-crawler-benchmarks/blob/main/reports/COST_AT_SCALE.md) in the benchmarks repo.

## Why these numbers matter

For a RAG pipeline, the crawler is stage 1 — everything downstream (chunking, embedding, retrieval, LLM generation) depends on the quality of what the crawler produces.

- **Fewer chunks per page** = lower embedding costs, less vector DB storage, faster retrieval
- **Less nav pollution** = cleaner embeddings that match user queries instead of "Home | About | Login"
- **Higher answer quality** = the LLM gets better source material and produces more accurate answers

## Methodology

All benchmarks run on the same hardware, same sites, same queries, with reproducible scripts. The full methodology, raw data, and reproduction instructions are in the [llm-crawler-benchmarks](https://github.com/AIMLPM/llm-crawler-benchmarks) repo.
