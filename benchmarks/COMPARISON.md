# MarkCrawl Head-to-Head Comparison

Generated: 2026-04-05 11:39:24 UTC

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

See [COMPARISON_PLAN.md](COMPARISON_PLAN.md) for full methodology.

## Tools tested

| Tool | Available | Notes |
|---|---|---|
| markcrawl | Yes | requests + BeautifulSoup + markdownify |
| crawl4ai | Yes | Playwright (headless Chromium) + built-in extraction |
| scrapy+md | Yes | Scrapy async framework + markdownify pipeline |
| firecrawl | Not installed | Self-hosted Docker (set FIRECRAWL_API_URL) |

## Results by site

### quotes-toscrape — Paginated quotes (simple HTML, link-following)

Max pages: 15

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 15 | 2.4 | ±0.0 | 6.2 | 279 | 32 | 106 |
| crawl4ai | 15 | 7.8 | ±0.0 | 1.9 | 262 | 37 | 104 |
| scrapy+md | 15 | 3.0 | ±0.0 | 5.0 | 262 | 30 | 75 |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | — | — | — | — | — | — | — |
| crawl4ai | — | — | — | — | — | — | — |
| scrapy+md | — | — | — | — | — | — | — |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | — | — | — | — | — | — | — |
| crawl4ai | — | — | — | — | — | — | — |
| scrapy+md | — | — | — | — | — | — | — |

### python-docs — Python standard library docs

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | — | — | — | — | — | — | — |
| crawl4ai | — | — | — | — | — | — | — |
| scrapy+md | — | — | — | — | — | — | — |

## Overall summary

| Tool | Total pages | Total time (s) | Avg pages/sec |
|---|---|---|---|
| markcrawl | 15 | 2.4 | 6.2 |
| crawl4ai | 15 | 7.8 | 1.9 |
| scrapy+md | 15 | 3.0 | 5.0 |

## Reproducing these results

```bash
# Install all tools
pip install markcrawl crawl4ai scrapy markdownify
playwright install chromium  # for crawl4ai

# Run comparison
python benchmarks/run_comparison.py
```

For FireCrawl, also run:
```bash
docker run -p 3002:3002 firecrawl/firecrawl:latest
export FIRECRAWL_API_URL=http://localhost:3002
python benchmarks/run_comparison.py
```
