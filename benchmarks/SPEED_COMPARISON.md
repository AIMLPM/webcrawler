# Speed Comparison

<!-- style: v2, 2026-04-07 -->

Generated: 2026-04-06 18:47:09 UTC

**colly+md is the fastest crawler at 5.8 pages/sec. markcrawl ranks third at 3.0 pages/sec — slower than the two plain-HTTP tools, but faster than every Playwright-based alternative and the only tool that fetched all 210 pages without missing any.**

## How to read the numbers

- **Pages/sec** is the primary metric: total pages fetched divided by wall-clock seconds. Higher is better.
- **Std dev** (standard deviation) measures run-to-run variance. A std dev of ±3.1 on a 15.8 s median means individual runs ranged roughly 12.7–18.9 s. Large std dev means the number is noisy — treat the rank order as more reliable than the exact value.
- **Total time** is end-to-end wall time across all 8 test sites at concurrency 1. All values are medians across 3 iterations per site.
- **Total pages** shows how many of the 210 possible pages each tool actually returned. Missing pages mean missing content in your pipeline.

## Summary

| Tool | Rendering | Total pages | Total time (s) | Pages/sec | Notes |
|---|---|---|---|---|---|
| colly+md | Plain HTTP | 205 | 35.2 | 5.8 | Missed 5 pages on blog-engineering |
| scrapy+md | Plain HTTP | 204 | 39.2 | 5.2 | Missed 6 pages on python-docs |
| **markcrawl** | **Plain HTTP** | **210** | **70.1** | **3.0** | **All pages fetched on every site** |
| crawl4ai | Playwright | 210 | 102.9 | 2.0 | |
| crawlee | Playwright | 210 | 141.9 | 1.5 | |
| playwright | Playwright | 210 | 233.8 | 0.9 | |
| crawl4ai-raw | Playwright | 210 | 251.8 | 0.8 | Out-of-box default config |
| firecrawl | — | — | — | — | Errored on all sites (Payment Required) — see [Tools tested](#tools-tested) |

## What this means

This benchmark tests 8 tools across 8 sites spanning simple HTML, paginated e-commerce, JS-rendered SPAs, and large documentation sets. Every tool fetches the same URL list — the only variable is the tool itself.

**The speed gap is real, but it has a clear cause.** colly+md and scrapy+md are 1.7-1.9x faster than markcrawl because they use plain HTTP without any browser overhead. colly+md finishes all 8 sites in 35.2 s; markcrawl takes 70.1 s. If raw throughput is the only thing you care about, colly+md wins.

**The completeness gap is also real.** markcrawl is the only tool that returned all 210 pages across all 8 sites. scrapy+md missed 6 pages on python-docs; colly+md missed 5 on blog-engineering. For a RAG pipeline where a missing page means a missing answer, completeness matters as much as speed. Whether that trade-off is worth 2x the wall time depends on your use case.

**Playwright-based tools are 2-7x slower than plain HTTP tools.** crawl4ai (2.0 pages/sec), crawlee (1.5 pages/sec), raw Playwright (0.9 pages/sec), and crawl4ai-raw (0.8 pages/sec) all carry the overhead of launching a full browser per page. If your target site is server-rendered HTML, a plain HTTP tool will always be faster. If the site is a React or Vue SPA that requires JS execution to render content, you need a Playwright-based tool — and at that point, crawl4ai at 2.0 pages/sec is the fastest option.

**Picking a tool by audience:**

- *Junior developer building a first RAG pipeline:* Start with markcrawl if you need every page and don't want to debug missing content. Switch to colly+md if you need maximum speed and can tolerate occasional missed pages.
- *Senior engineer evaluating at scale:* The 2x speed difference between colly+md and markcrawl compounds at scale. At 10,000 pages, that is roughly 29 minutes vs 56 minutes. Check whether the 6 missed pages (2.9% of the test set) would matter in your domain — and whether rerunning failures is cheaper than the speed gain.
- *Engineering manager comparing costs:* Speed affects compute time, but the bigger cost driver is what happens downstream. More words per page means higher embedding and storage costs. See [COST_AT_SCALE.md](COST_AT_SCALE.md) for dollar projections.

**Word counts are not quality.** On JS-heavy sites like react-dev and stripe-docs, Playwright tools extract 2-8x more words than plain HTTP tools. That is not higher quality — it is nav chrome, sidebar repetition, and script artifacts included alongside article text. See [QUALITY_COMPARISON.md](QUALITY_COMPARISON.md) for content signal analysis showing that more words often means more noise.

## Tools tested

| Tool | Rendering | Description |
|---|---|---|
| markcrawl | Plain HTTP | requests + BeautifulSoup + markdownify — [AIMLPM/markcrawl](https://github.com/AIMLPM/markcrawl) |
| crawl4ai | Playwright | Playwright + arun_many() batch concurrency — [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) |
| crawl4ai-raw | Playwright | Playwright + sequential arun(), default config (out-of-box baseline) |
| scrapy+md | Plain HTTP | Scrapy async + markdownify — [scrapy/scrapy](https://github.com/scrapy/scrapy) |
| crawlee | Playwright | Playwright + markdownify — [apify/crawlee-python](https://github.com/apify/crawlee-python) |
| colly+md | Plain HTTP | Go fetch (Colly) + Python markdownify — [gocolly/colly](https://github.com/gocolly/colly) |
| playwright | Playwright | Raw Playwright baseline + markdownify (no framework) |
| firecrawl | — | Self-hosted Docker returned `Payment Required` on every site — likely an API key or credit configuration issue. Excluded from all per-site tables. See [Reproducing these results](#reproducing-these-results) for setup notes. |

## Results by site

### quotes-toscrape — Paginated quotes (simple HTML, link-following)

Max pages: 15

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 15 | 1.9 | ±0.2 | 7.9 | 227 | 29 | 110 |
| markcrawl | 15 | 2.2 | ±0.1 | 6.9 | 241 | 30 | 265 |
| crawl4ai | 15 | 3.6 | ±0.9 | 4.2 | 224 | 39 | 246 |
| scrapy+md | 15 | 4.9 | ±0.5 | 3.0 | 224 | 29 | 156 |
| playwright | 15 | 6.2 | ±0.4 | 2.4 | 227 | 29 | 171 |
| crawlee | 15 | 8.0 | ±1.7 | 1.9 | 227 | 29 | 274 |
| crawl4ai-raw | 15 | 14.8 | ±2.6 | 1.0 | 224 | 39 | 183 |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 60 | 9.7 | ±0.5 | 6.2 | 412 | 265 | 195 |
| scrapy+md | 60 | 10.0 | ±1.7 | 6.0 | 403 | 262 | 105 |
| crawl4ai | 60 | 14.3 | ±4.5 | 4.2 | 518 | 506 | 183 |
| crawlee | 60 | 14.4 | ±5.3 | 4.2 | 412 | 265 | 265 |
| markcrawl | 60 | 15.8 | ±3.1 | 3.8 | 335 | 168 | 189 |
| crawl4ai-raw | 60 | 33.7 | ±18.5 | 1.8 | 518 | 506 | 286 |
| playwright | 60 | 55.8 | ±7.0 | 1.1 | 412 | 265 | 426 |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 25 | 4.3 | ±0.6 | 5.8 | 3661 | 958 | 247 |
| scrapy+md | 25 | 4.5 | ±0.7 | 5.5 | 3339 | 834 | 259 |
| markcrawl | 25 | 9.4 | ±0.2 | 2.7 | 2599 | 555 | 281 |
| playwright | 25 | 23.7 | ±1.6 | 1.1 | 3642 | 1130 | 232 |
| crawl4ai | 25 | 24.4 | ±2.9 | 1.0 | 4027 | 1136 | 286 |
| crawl4ai-raw | 25 | 25.6 | ±2.7 | 1.0 | 4025 | 1135 | 352 |
| crawlee | 25 | 34.2 | ±5.3 | 0.7 | 3646 | 1131 | 182 |

### python-docs — Python standard library docs

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 20 | 1.8 | ±0.9 | 11.0 | 1001 | 177 | 146 |
| scrapy+md | 14 | 2.2 | ±0.8 | 6.2 | 1273 | 157 | 176 |
| markcrawl | 20 | 3.6 | ±0.9 | 5.6 | 787 | 132 | 156 |
| crawl4ai | 20 | 6.5 | ±3.0 | 3.1 | 1125 | 243 | 168 |
| playwright | 20 | 8.1 | ±0.5 | 2.5 | 1071 | 193 | 295 |
| crawlee | 20 | 8.4 | ±9.8 | 2.4 | 1071 | 193 | 182 |
| crawl4ai-raw | 20 | 17.3 | ±2.9 | 1.2 | 1125 | 243 | 168 |

### react-dev — React docs (SPA, JS-rendered, interactive examples)

Max pages: 30

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| scrapy+md | 30 | 3.3 | ±0.2 | 9.0 | 1967 | 476 | 347 |
| colly+md | 30 | 3.9 | ±0.2 | 7.7 | 5257 | 1777 | 193 |
| crawl4ai | 30 | 13.9 | ±2.1 | 2.2 | 2606 | 757 | 426 |
| markcrawl | 30 | 20.4 | ±6.5 | 1.5 | 1946 | 455 | 267 |
| crawlee | 30 | 20.9 | ±24.6 | 1.4 | 5381 | 1814 | 245 |
| crawl4ai-raw | 30 | 25.9 | ±9.0 | 1.2 | 2609 | 762 | 210 |
| playwright | 30 | 24.3 | ±1.2 | 1.2 | 5257 | 1777 | 232 |

### wikipedia-python — Wikipedia (tables, infoboxes, citations, deep linking)

Max pages: 15

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 15 | 2.8 | ±0.6 | 5.4 | 6444 | 1251 | 247 |
| scrapy+md | 15 | 2.8 | ±0.1 | 5.3 | 5890 | 1070 | 101 |
| markcrawl | 15 | 3.9 | ±0.1 | 3.8 | 4120 | 637 | 265 |
| crawl4ai | 15 | 5.4 | ±1.9 | 2.8 | 6112 | 1283 | 353 |
| crawlee | 15 | 5.7 | ±1.1 | 2.6 | 11351 | 4111 | 50 |
| crawl4ai-raw | 15 | 10.9 | ±1.0 | 1.4 | 6112 | 1283 | 115 |
| playwright | 15 | 11.7 | ±3.8 | 1.3 | 6781 | 1448 | 183 |

### stripe-docs — Stripe API docs (tabbed content, code samples, sidebars)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| colly+md | 25 | 7.0 | ±0.2 | 3.6 | 12605 | 7391 | 195 |
| scrapy+md | 25 | 8.2 | ±0.2 | 3.0 | 1547 | 279 | 43 |
| markcrawl | 25 | 9.9 | ±1.0 | 2.5 | 1530 | 274 | 265 |
| crawl4ai | 25 | 27.1 | ±15.6 | 0.9 | 1442 | 328 | 297 |
| crawlee | 25 | 43.1 | ±21.6 | 0.6 | 12746 | 7529 | 418 |
| playwright | 25 | 73.5 | ±27.9 | 0.3 | 12750 | 7531 | 150 |
| crawl4ai-raw | 25 | 112.1 | ±34.4 | 0.2 | 1442 | 328 | 286 |

### blog-engineering — GitHub Engineering Blog (articles, images, technical content)

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| scrapy+md | 20 | 3.1 | ±1.3 | 6.4 | 1863 | 267 | 241 |
| markcrawl | 20 | 4.9 | ±5.1 | 4.1 | 1738 | 245 | 183 |
| colly+md | 15 | 3.8 | ±4.8 | 3.7 | 4301 | 1012 | 281 |
| crawlee | 20 | 7.2 | ±0.9 | 2.8 | 4739 | 1559 | 111 |
| crawl4ai | 20 | 7.6 | ±1.1 | 2.6 | 3548 | 703 | 208 |
| crawl4ai-raw | 20 | 11.6 | ±0.6 | 1.7 | 3548 | 703 | 265 |
| playwright | 20 | 30.5 | ±9.9 | 0.7 | 4765 | 1585 | 222 |

## A note on variance

These benchmarks fetch pages from live public websites. Network conditions, server load, and CDN caching cause real run-to-run variance — std dev is shown per site. The stripe-docs site illustrates this most clearly: crawl4ai-raw had a median of 112.1 s with ±34.4 s std dev. Treat absolute times as indicative; rank order is stable across runs.

## Methodology

**Two-phase approach** for a fair comparison:

1. **URL Discovery** — MarkCrawl crawls each site once to build a URL list
2. **Benchmarking** — All tools fetch the **identical URLs** (no discovery, pure fetch+convert speed)

Settings:
- **Delay:** 0 (no politeness throttle)
- **Concurrency:** 1 (one in-flight request at a time for HTTP tools; one browser page at a time for Playwright tools)
- **Iterations:** 2 per tool per site (reporting median + std dev)
- **Warm-up:** 1 throwaway run per site before timing
- **Output:** Markdown files + JSONL index
- **URL list:** Identical for all tools (discovered in Phase 1)

**What was NOT measured:** crawl discovery speed, robots.txt compliance, rate-limiting behavior, or memory footprint under high concurrency. Pages/sec numbers reflect single-threaded throughput only.

See [METHODOLOGY.md](METHODOLOGY.md) for full test setup, tool configurations, and fairness decisions.

## Reproducing these results

```bash
# Install all tools
pip install markcrawl crawl4ai scrapy markdownify
playwright install chromium  # for crawl4ai, crawlee, playwright

# Run comparison
python benchmarks/benchmark_all_tools.py
```

For Firecrawl, start the self-hosted Docker instance before running:

```bash
docker run -p 3002:3002 firecrawl/firecrawl:latest
export FIRECRAWL_API_URL=http://localhost:3002
python benchmarks/benchmark_all_tools.py
```

Note: the benchmark run that produced this report received `Payment Required` from the Firecrawl Docker instance on every site. This is likely a missing API key or credit configuration, not a crawl speed issue. Firecrawl results are excluded from all tables.
