# MarkCrawl Head-to-Head Comparison

Generated: 2026-04-05 04:26:10 UTC

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
| markcrawl | 15 | 2.0 | ±0.2 | 7.4 | 198 | 28 | 151 |
| crawl4ai | 15 | 5.5 | ±0.1 | 2.7 | 182 | 37 | 126 |
| scrapy+md | 15 | 2.4 | ±0.0 | 6.2 | 182 | 26 | 75 |

### books-toscrape — E-commerce catalog (60 pages, pagination)

Max pages: 60

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 60 | 8.6 | ±0.8 | 7.0 | 329 | 166 | 117 |
| crawl4ai | 60 | 21.3 | ±0.2 | 2.8 | 508 | 499 | 90 |
| scrapy+md | 60 | 6.7 | ±0.6 | 9.0 | 397 | 258 | 27 |

### fastapi-docs — API documentation (code blocks, headings, tutorials)

Max pages: 25

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 25 | 4.1 | ±0.2 | 6.2 | 1859 | 376 | 187 |
| crawl4ai | 25 | 19.0 | ±2.1 | 1.3 | 3245 | 913 | 160 |
| scrapy+md | 25 | 2.9 | ±0.1 | 8.6 | 2593 | 634 | 31 |

### python-docs — Python standard library docs

Max pages: 20

| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| markcrawl | 20 | 1.3 | ±0.1 | 15.3 | 712 | 132 | 174 |
| crawl4ai | 20 | 6.8 | ±0.0 | 2.9 | 1083 | 255 | 96 |
| scrapy+md | 16 | 1.8 | ±0.1 | 9.1 | 1066 | 162 | 30 |

## Overall summary

| Tool | Total pages | Total time (s) | Avg pages/sec |
|---|---|---|---|
| markcrawl | 120 | 16.0 | 7.5 |
| crawl4ai | 120 | 52.6 | 2.3 |
| scrapy+md | 116 | 13.8 | 8.4 |

## Analysis

### Crawl4AI: 3x slower (expected)

Crawl4AI launches headless Chromium for every page. On static HTML sites, this is pure overhead. This gap would narrow on JavaScript-heavy SPAs where browser rendering is necessary.

### MarkCrawl vs Scrapy: Scrapy is ~12% faster overall

With identical URLs, Scrapy's async Twisted engine edges out MarkCrawl's synchronous `requests` by about 12% (8.4 vs 7.5 pages/sec). This is a real difference, not noise — the standard deviations are small enough to confirm it.

However, the results are site-dependent:
- **Python docs: MarkCrawl wins** (15.3 vs 9.1 p/s) — lightweight HTTP client shines on fast servers
- **Books-toscrape: Scrapy wins** (9.0 vs 7.0 p/s) — Scrapy's async engine handles larger crawls better
- **Quotes-toscrape: MarkCrawl wins** (7.4 vs 6.2 p/s) — close, but consistent across iterations
- **FastAPI docs: Scrapy wins** (8.6 vs 6.2 p/s) — larger pages favor Scrapy's streaming

### Page coverage

MarkCrawl found all 120 target URLs. Scrapy found 116 — it missed 4 pages on python-docs, likely due to robots.txt handling differences or URL normalization.

### What we claim

- "3x faster than browser-based crawlers on static sites" — **grounded**
- "Comparable to Scrapy, faster on some sites, slower on others" — **grounded**
- "Better page coverage" (120 vs 116) — **grounded, but small margin**
- "Simpler to use: one command vs writing a spider class" — **always true**

### What we don't claim

- "Fastest Python crawler" — Scrapy is faster overall, and would pull further ahead at high concurrency
- "Better extraction quality" — not measured in this benchmark; needs manual quality review

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
