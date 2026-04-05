# MarkCrawl Head-to-Head Comparison

Generated: 2026-04-05 22:11:58 UTC

## Methodology

**Two-phase approach** for a fair comparison:

1. **URL Discovery** — MarkCrawl crawls each site once to build a URL list
2. **Benchmarking** — All tools fetch the **identical URLs** (no discovery, pure fetch+convert speed)

Settings:
- **Delay:** 0 (no politeness throttle)
- **Concurrency:** 1 (sequential, single-thread comparison)
- **Iterations:** 3 per tool per site (reporting median + std dev)
- **Warm-up:** 1 throwaway run per site before timing
- **Output:** Markdown files + JSONL index
- **URL list:** Identical for all tools (discovered in Phase 1)

See [METHODOLOGY.md](METHODOLOGY.md) for full methodology.

## Tools tested

| Tool | Available | Notes |
|---|---|---|
| markcrawl | Yes | requests + BeautifulSoup + markdownify — [AIMLPM/markcrawl](https://github.com/AIMLPM/markcrawl) |
| crawl4ai | Yes | Playwright + built-in extraction — [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) |
| scrapy+md | Yes | Scrapy async + markdownify — [scrapy/scrapy](https://github.com/scrapy/scrapy) |
| crawlee | Yes | Playwright + markdownify — [apify/crawlee-python](https://github.com/apify/crawlee-python) |
| colly+md | Yes | Go fetch (Colly) + Python markdownify — [gocolly/colly](https://github.com/gocolly/colly) |
| playwright | Yes | Raw Playwright baseline + markdownify (no framework) |
| firecrawl | Yes | Self-hosted Docker — [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) |

## Results by site

### quotes-toscrape — Paginated quotes (simple HTML, link-following)

Max pages: 15

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 15 | 3.3 | ±0.2 | 4.6 | 253 | 32 | 103 |
| crawl4ai | 15 | 7.0 | ±0.4 | 2.1 | 237 | 41 | 181 |
| scrapy+md | 15 | 4.6 | ±0.2 | 3.3 | 237 | 31 | 83 |
| crawlee | 15 | 6.8 | ±0.4 | 2.2 | 261 | 34 | 22 |
| colly+md | 15 | 1.9 | ±0.6 | 7.8 | 261 | 34 | 35 |
| playwright | 15 | 6.6 | ±0.6 | 2.3 | 261 | 34 | 93 |
| firecrawl | 15 | 15.0 | ±0.0 | 1.0 | 91 | 18 | 42 |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 60 | 16.5 | ±5.0 | 3.6 | 328 | 163 | 128 |
| crawl4ai | 59 | 269.1 | ±293.0 | 0.2 | 493 | 461 | 78 |
| scrapy+md | 60 | 10.8 | ±1.5 | 5.5 | 389 | 248 | 23 |
| crawlee | 60 | 14.3 | ±5.0 | 4.2 | 418 | 263 | 22 |
| colly+md | 60 | 4.0 | ±0.3 | 15.0 | 418 | 263 | 115 |
| playwright | 60 | 21.7 | ±2.2 | 2.8 | 418 | 263 | 116 |
| firecrawl | — | — | — | — | — | — | error: Rate Limit Exceeded: Failed to start crawl. Rate l |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 25 | 8.8 | ±0.5 | 2.8 | 3865 | 886 | 221 |
| crawl4ai | 25 | 25.9 | ±1.3 | 1.0 | 5424 | 1608 | 155 |
| scrapy+md | 25 | 5.6 | ±0.2 | 4.4 | 4676 | 1197 | 29 |
| crawlee | 25 | 75.4 | ±329.3 | 0.3 | 4965 | 1542 | 28 |
| colly+md | 25 | 5.6 | ±0.2 | 4.4 | 5000 | 1322 | 186 |
| playwright | 25 | 22.2 | ±1.4 | 1.1 | 4975 | 1545 | 205 |
| firecrawl | — | — | — | — | — | — | error: Rate Limit Exceeded: Failed to start crawl. Rate l |

### python-docs — Python standard library docs

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 20 | 2.9 | ±0.1 | 6.9 | 2846 | 684 | 188 |
| crawl4ai | 20 | 9.8 | ±1.4 | 2.0 | 3268 | 989 | 152 |
| scrapy+md | 18 | 3.1 | ±0.0 | 5.9 | 3418 | 732 | 30 |
| crawlee | 20 | 6.3 | ±0.9 | 3.2 | 3214 | 760 | 22 |
| colly+md | 20 | 2.5 | ±0.4 | 8.0 | 3125 | 740 | 179 |
| playwright | 20 | 10.6 | ±0.2 | 1.9 | 3214 | 760 | 160 |
| firecrawl | — | — | — | — | — | — | error: Rate Limit Exceeded: Failed to start crawl. Rate l |

## Overall summary

| Tool | Total pages | Total time (s) | Avg pages/sec |
|---|---|---|---|
| markcrawl | 120 | 31.6 | 3.8 |
| crawl4ai | 119 | 311.8 | 0.4 |
| scrapy+md | 118 | 24.1 | 4.9 |
| crawlee | 120 | 102.8 | 1.2 |
| colly+md | 120 | 14.0 | 8.6 |
| playwright | 120 | 61.1 | 2.0 |
| firecrawl | 15 | 15.0 | 1.0 |

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
