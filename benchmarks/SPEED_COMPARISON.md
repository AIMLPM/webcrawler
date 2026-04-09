# MarkCrawl Head-to-Head Comparison

<!-- style: v2, 2026-04-08 -->

Scrapy+md is the fastest tool overall (9.1 pages/sec), followed by colly+md (5.8 pages/sec). Markcrawl ranks third at 2.9 pages/sec. Firecrawl is the slowest, averaging 0.8 pages/sec across sites it completed, and failed to crawl 2 of 8 sites entirely.

Higher word counts do not mean higher quality -- see [QUALITY_COMPARISON.md](QUALITY_COMPARISON.md) for why markcrawl's lower word counts reflect cleaner extraction, not missing content.

Generated: 2026-04-08 09:43:02 UTC

## Methodology

**Two-phase approach** for a fair comparison:

1. **URL Discovery** — MarkCrawl crawls each site once to build a URL list
2. **Benchmarking** — All tools fetch the **identical URLs** (no discovery, pure fetch+convert speed)

Settings:
- **Delay:** 0 (no politeness throttle)
- **Concurrency:** 5
- **Iterations:** 3 per tool per site (reporting median + std dev)
- **Warm-up:** 1 throwaway run per site before timing
- **Output:** Markdown files + JSONL index
- **URL list:** Identical for all tools (discovered in Phase 1)

See [METHODOLOGY.md](METHODOLOGY.md) for full methodology.

## Tools tested

| Tool | Fetch method | Notes |
|---|---|---|
| markcrawl | HTTP (requests) | BeautifulSoup + markdownify — [AIMLPM/markcrawl](https://github.com/AIMLPM/markcrawl) |
| crawl4ai | JS (Playwright) | arun_many() batch concurrency — [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) |
| crawl4ai-raw | JS (Playwright) | sequential arun(), default config (out-of-box baseline) |
| scrapy+md | HTTP (async) | Scrapy + markdownify — [scrapy/scrapy](https://github.com/scrapy/scrapy) |
| crawlee | JS (Playwright) | Playwright + markdownify — [apify/crawlee-python](https://github.com/apify/crawlee-python) |
| colly+md | HTTP (Go) | Colly + Python markdownify — [gocolly/colly](https://github.com/gocolly/colly) |
| playwright | JS (Playwright) | Raw Playwright baseline + markdownify (no framework) |
| firecrawl | JS (Playwright) | Self-hosted Docker (API+worker+Redis) — [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) |

> **Why HTTP tools are faster:** Tools using plain HTTP (markcrawl, scrapy+md, colly+md) skip browser startup and JavaScript execution, making them 2-5x faster than Playwright-based tools on static content. The trade-off: they can't render JS-heavy SPAs.

## Results by site

### quotes-toscrape — Paginated quotes (simple HTML, link-following)

Max pages: 15

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 15 | 2.1 | ±0.0 | 7.2 | 305 | 37 | 312 |
| crawl4ai | 15 | 1.7 | ±0.1 | 8.9 | 289 | 46 | 210 |
| crawl4ai-raw | 15 | 5.4 | ±0.4 | 2.8 | 289 | 46 | 335 |
| scrapy+md | 15 | 1.2 | ±0.1 | 12.6 | 289 | 35 | 1513 |
| crawlee | 15 | 3.7 | ±0.0 | 4.0 | 292 | 35 | 1200 |
| colly+md | 15 | 1.9 | ±0.0 | 7.8 | 292 | 35 | 1203 |
| playwright | 15 | 3.4 | ±0.4 | 4.4 | 292 | 35 | 490 |
| firecrawl | 15 | 134.8 | — | 0.1 | 203 | 34 | — |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 60 | 8.4 | ±1.2 | 7.2 | 326 | 165 | 1221 |
| crawl4ai | 60 | 5.0 | ±0.7 | 12.1 | 508 | 500 | 1330 |
| crawl4ai-raw | 60 | 22.5 | ±0.6 | 2.7 | 508 | 500 | 1299 |
| scrapy+md | 60 | 11.4 | ±0.1 | 5.3 | 395 | 259 | 1204 |
| crawlee | 60 | 13.7 | ±0.7 | 4.4 | 403 | 261 | 304 |
| colly+md | 60 | 7.0 | ±0.2 | 8.6 | 403 | 262 | 312 |
| playwright | 60 | 23.1 | ±1.0 | 2.6 | 403 | 261 | 335 |
| firecrawl | 60 | 97.3 | — | 0.7 | 328 | 298 | — |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 500

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 275 | 54.7 | ±3.1 | 5.0 | 1503 | 4307 | 279 |
| crawl4ai | 275 | 213.5 | ±4.5 | 1.3 | 2815 | 10533 | 1454 |
| crawl4ai-raw | 275 | 298.1 | ±11.8 | 0.9 | 2814 | 10529 | 1482 |
| scrapy+md | 275 | 26.7 | ±1.4 | 10.3 | 2158 | 7202 | 1519 |
| crawlee | 275 | 209.6 | ±2.1 | 1.3 | 2463 | 10533 | 316 |
| colly+md | 275 | 37.2 | ±3.3 | 7.4 | 2480 | 8567 | 305 |
| playwright | 275 | 138.8 | ±6.0 | 2.0 | 2468 | 10547 | 1499 |
| firecrawl | 499 | 563.8 | — | 0.9 | 1964 | 10971 | — |

Firecrawl crawled 499 of 500 URLs (near-complete). All other tools were capped at 275 URLs discovered in Phase 1.

### python-docs — Python standard library docs

Max pages: 500

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 500 | 107.0 | ±32.1 | 4.9 | 3772 | 20069 | 1553 |
| crawl4ai | 500 | 49.1 | ±1.1 | 10.2 | 4190 | 27341 | 913 |
| crawl4ai-raw | 500 | 181.5 | ±1.7 | 2.8 | 4190 | 27341 | 1430 |
| scrapy+md | 429 | 36.8 | ±0.9 | 11.7 | 4262 | 19298 | 1514 |
| crawlee | 500 | 56.0 | ±1.1 | 8.9 | 4132 | 21889 | 279 |
| colly+md | 500 | 43.6 | ±5.4 | 11.6 | 4044 | 21397 | 315 |
| playwright | 500 | 94.7 | ±2.0 | 5.3 | 4132 | 21889 | 511 |
| firecrawl | 320 | 64.3 | — | 5.1 | 3077 | 10330 | — |

Firecrawl crawled 320 of 500 URLs (partial). All other tools crawled 429-500.

### react-dev — React docs (SPA, JS-rendered, interactive examples)

Max pages: 500

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 221 | 31.3 | ±0.3 | 7.1 | 1579 | 2767 | 1430 |
| crawl4ai | 221 | 33.5 | ±3.2 | 6.6 | 2275 | 5666 | 1203 |
| crawl4ai-raw | 221 | 112.1 | ±25.6 | 2.0 | 2279 | 5683 | 315 |
| scrapy+md | 221 | 62.2 | ±1.8 | 3.6 | 1601 | 2914 | 1250 |
| crawlee | 70 | 50.8 | ±3.9 | 1.4 | 2423 | 4007 | 1556 |
| colly+md | 221 | 22.2 | ±1.4 | 10.0 | 4294 | 11566 | 1220 |
| playwright | 221 | 68.5 | ±12.6 | 3.3 | 4295 | 11567 | 1514 |
| firecrawl | 0 | — | — | — | — | — | — |

Firecrawl returned 0 usable pages for react-dev. This JS-heavy SPA requires client-side rendering that Firecrawl's pipeline did not handle.

### wikipedia-python — Wikipedia (tables, infoboxes, citations, deep linking)

Max pages: 50

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 50 | 10.2 | ±0.5 | 4.9 | 4601 | 2286 | 215 |
| crawl4ai | 50 | 7.9 | ±0.1 | 6.3 | 6549 | 4455 | 461 |
| crawl4ai-raw | 50 | 24.7 | ±0.5 | 2.0 | 6573 | 4467 | 340 |
| scrapy+md | 50 | 6.7 | ±0.5 | 7.5 | 6300 | 3651 | 1497 |
| crawlee | 50 | 36.7 | ±27.6 | 1.9 | 11778 | 13894 | 1519 |
| colly+md | 50 | 18.2 | ±13.7 | 3.8 | 6843 | 4248 | 1514 |
| playwright | 42 | 21.8 | ±13.8 | 2.4 | 6715 | 3542 | 1496 |
| firecrawl | 1 | 26.4 | — | 0.0 | 14636 | 198 | — |

Firecrawl returned only 1 of 50 Wikipedia pages.

### stripe-docs — Stripe API docs (tabbed content, code samples, sidebars)

Max pages: 500

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 402 | 359.7 | ±33.7 | 1.1 | 945 | 3612 | 1268 |
| crawl4ai | 402 | 397.8 | ±27.5 | 1.0 | 969 | 4758 | 1327 |
| crawl4ai-raw | 402 | 573.3 | ±26.0 | 0.7 | 966 | 4747 | 1322 |
| scrapy+md | 402 | 33.6 | ±5.0 | 12.1 | 958 | 3667 | 304 |
| crawlee | 0 | 300.0 | ±0.0 | 0.0 | — | — | — |
| colly+md | 402 | 133.9 | ±3.2 | 3.0 | 15651 | 182367 | 1226 |
| playwright | 402 | 390.7 | ±11.9 | 1.0 | 15742 | 184441 | 1532 |
| firecrawl | 0 | — | — | — | — | — | — |

Firecrawl failed on stripe-docs with connection reset errors (anti-bot protection).

### blog-engineering — GitHub Engineering Blog (articles, images, technical content)

Max pages: 200

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 200 | 11.9 | ±0.0 | 16.8 | 557 | 892 | 1299 |
| crawl4ai | 200 | 29.1 | ±2.0 | 6.9 | 2325 | 5306 | 857 |
| crawl4ai-raw | 200 | 78.5 | ±0.9 | 2.5 | 2325 | 5305 | 1430 |
| scrapy+md | 200 | 3.4 | ±0.2 | 58.3 | 672 | 1096 | 1203 |
| crawlee | 200 | 28.6 | ±9.4 | 7.4 | 3585 | 14379 | 1484 |
| colly+md | 25 | 3.4 | ±0.0 | 7.4 | 3125 | 1472 | 1220 |
| playwright | 200 | 55.7 | ±4.4 | 3.6 | 3581 | 14339 | 1299 |
| firecrawl | 183 | 443.0 | — | 0.4 | 1854 | 2987 | — |

Firecrawl crawled 183 of 200 blog pages (91% complete).

## Overall summary

| Tool | Total pages | Total time (s) | Avg pages/sec | Notes |
|---|---|---|---|---|
| scrapy+md | 1652 | 182.0 | 9.1 | |
| colly+md | 1548 | 267.4 | 5.8 | |
| **markcrawl** | **1723** | **585.2** | **2.9** | |
| crawl4ai | 1723 | 737.4 | 2.3 | |
| playwright | 1716 | 796.8 | 2.2 | |
| crawlee | 1170 | 699.1 | 1.7 | Missing 553 pages (crawlee failed on stripe-docs, partial react-dev) |
| crawl4ai-raw | 1723 | 1296.2 | 1.3 | |
| firecrawl | 1078 | 1329.6 | 0.8 | Failed on stripe-docs and react-dev; partial on 3 other sites |

> **Note on variance:** These benchmarks fetch pages from live public websites.
> Network conditions, server load, and CDN caching can cause significant
> run-to-run variance (std dev shown per site). For the most reliable comparison,
> run multiple iterations and compare medians.

Speed is only one dimension. Higher word counts do not indicate better quality --
see [QUALITY_COMPARISON.md](QUALITY_COMPARISON.md) for extraction quality and
[COST_AT_SCALE.md](COST_AT_SCALE.md) for how chunk efficiency affects RAG costs
at scale. See [METHODOLOGY.md](METHODOLOGY.md) for full test setup.

## Reproducing these results

```bash
# Install all tools
pip install markcrawl crawl4ai scrapy markdownify
playwright install chromium  # for crawl4ai

# Run comparison
python benchmarks/benchmark_all_tools.py
```

For FireCrawl, also run:
```bash
docker run -p 3002:3002 firecrawl/firecrawl:latest
export FIRECRAWL_API_URL=http://localhost:3002
python benchmarks/benchmark_all_tools.py
```
