# MarkCrawl Head-to-Head Comparison

Generated: 2026-04-05 03:32:21 UTC

## Methodology

Each tool crawled the same sites with equivalent settings:
- **Delay:** 0 (no politeness throttle)
- **Concurrency:** 1 (sequential, single-thread comparison)
- **Iterations:** 3 per tool per site (reporting median + std dev)
- **Warm-up:** 1 throwaway run per site before timing
- **Output:** Markdown files + JSONL index

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
| markcrawl | 15 | 2.2 | ±0.0 | 6.8 | 222 | 28 | 117 |
| crawl4ai | 15 | 6.0 | ±0.2 | 2.5 | 226 | 38 | 86 |
| scrapy+md | 14 | 2.8 | ±0.1 | 5.0 | 141 | 18 | 110 |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 60 | 8.5 | ±0.7 | 7.1 | 332 | 166 | 117 |
| crawl4ai | 60 | 20.8 | ±1.1 | 2.9 | 504 | 534 | 90 |
| scrapy+md | 59 | 7.7 | ±0.7 | 7.8 | 484 | 217 | 73 |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 25 | 6.1 | ±0.1 | 4.1 | 2012 | 445 | 188 |
| crawl4ai | 25 | 20.9 | ±0.3 | 1.2 | 5403 | 1838 | 216 |
| scrapy+md | 21 | 3.7 | ±0.5 | 5.7 | 2717 | 652 | 29 |

### python-docs — Python standard library docs

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 6* | 0.4 | ±0.0 | 13.5 | 213 | 12 | 163 |
| crawl4ai | 20 | 8.5 | ±0.3 | 2.4 | 4900 | 940 | 171 |
| scrapy+md | 19 | 2.3 | ±0.0 | 8.5 | 4302 | 665 | 30 |

\* MarkCrawl found a sitemap with 7 version-root URLs instead of the `/3/library/` subpages. When a sitemap exists, MarkCrawl uses sitemap URLs exclusively and doesn't follow links. Using `--no-sitemap` would crawl via link-following instead. This is a known limitation — hybrid sitemap + link-following is on the roadmap.

## Overall summary

| Tool | Total pages | Total time (s) | Avg pages/sec |
|---|---|---|---|
| markcrawl | 106 | 17.2 | 6.2 |
| crawl4ai | 120 | 56.2 | 2.1 |
| scrapy+md | 113 | 16.5 | 6.9 |

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
