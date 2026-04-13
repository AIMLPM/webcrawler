# MarkCrawl Benchmarks

> **Summary:** Across 7 open-source crawlers tested on 8 sites and 93 queries, MarkCrawl is the fastest (14.0 pages/sec), produces the cleanest output (4 words of nav pollution vs 275+ for others), generates the fewest chunks per page (10.1 — roughly half the next closest), and delivers the highest LLM answer quality on the full query set (3.91/5). This translates to the lowest total RAG pipeline cost at every scale tested.
>
> **Where MarkCrawl is not first:** Raw retrieval recall (Hit@5) is 80% vs 85% for crawlee, which captures more content at the cost of 5x more nav pollution and 2x more chunks. See the full breakdown below.

*Last run: April 2026. Reproducible via [llm-crawler-benchmarks](https://github.com/AIMLPM/llm-crawler-benchmarks).*

---

## Speed

| Tool | Pages/sec |
|---|---|
| **markcrawl** | **14.0** |
| scrapy+md | 9.3 |
| colly+md | 6.6 |
| crawl4ai | 2.0 |
| crawlee | 1.4 |

MarkCrawl uses native async I/O (httpx) with concurrent fetching and process-pool HTML extraction. Playwright-based tools (crawl4ai, crawlee) are inherently slower due to full browser rendering per page.

## Output cleanliness

| Tool | Nav pollution (words) | Recall |
|---|---|---|
| **markcrawl** | **4** | 84% |
| scrapy+md | 275 | 91% |
| crawl4ai | 329 | 95% |
| crawlee | 398 | 97% |

Nav pollution = boilerplate words (navigation, footer, cookie banners) that leak into extracted content. Lower is better — less junk means cleaner embeddings and fewer wasted tokens.

The tradeoff: crawlee captures 97% of page content but includes ~400 words of boilerplate per page. MarkCrawl captures 84% with almost zero pollution. For RAG pipelines, the cleaner output produces better embeddings and higher answer quality despite the lower recall.

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

**Reading this table:**
- **Chunks/page** — fewer = less redundancy, lower embedding costs. MarkCrawl produces 2x fewer chunks than crawlee for the same sites.
- **Answer Quality** — LLM-judged score for answers generated from retrieved chunks. MarkCrawl leads on the full 92-query set.
- **Hit@5 / Hit@20** — what percentage of queries find a relevant chunk in the top 5 or 20 results. Crawlee leads Hit@5 (85% vs 80%) due to higher recall, but the gap closes at Hit@20 (tied at 87%).

## Total cost of ownership

Annual cost estimate for a complete RAG pipeline: crawling + embedding + vector storage + query-time retrieval.

| Scale | markcrawl | scrapy+md | firecrawl | crawl4ai | crawlee |
|---|---|---|---|---|---|
| 100K pages, 1K queries/day | **$4,505** | $5,464 | $5,835 | $6,960 | $7,467 |

MarkCrawl's cost advantage comes from chunk efficiency — same content, fewer and cleaner chunks means fewer embedding API calls and less vector storage. At scale, this compounds: 2x fewer chunks = roughly half the embedding and storage costs.

For the complete cost analysis across all scales (100 to 1M pages), see [COST_AT_SCALE.md](https://github.com/AIMLPM/llm-crawler-benchmarks/blob/main/reports/COST_AT_SCALE.md) in the benchmarks repo.

## Why these numbers matter

For a RAG pipeline, the crawler is stage 1 — everything downstream (chunking, embedding, retrieval, LLM generation) depends on the quality of what the crawler produces.

- **Fewer chunks per page** = lower embedding costs, less vector DB storage, faster retrieval
- **Less nav pollution** = cleaner embeddings that match user queries instead of "Home | About | Login"
- **Higher answer quality** = the LLM gets better source material and produces more accurate answers

The total cost difference between the cheapest and most expensive tools is $2,962/year at 100K pages. At 1M pages the gap widens further.

## Methodology

All benchmarks run on the same hardware, same sites, same queries, with reproducible scripts. No tool receives special treatment or configuration beyond its defaults. The full methodology, raw data, and reproduction instructions are in the [llm-crawler-benchmarks](https://github.com/AIMLPM/llm-crawler-benchmarks) repo.
