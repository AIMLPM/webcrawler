# MarkCrawl Self-Benchmark (MarkCrawl only — no competitors)

<!-- style: v2, 2026-04-07 -->

> **Looking for the head-to-head comparison vs Crawl4AI and Scrapy?** See [SPEED_COMPARISON.md](SPEED_COMPARISON.md).

This report measures MarkCrawl's own performance and extraction quality across 7 test sites. No other tools are involved — this is a self-assessment of speed, content quality, and output completeness.

Generated: 2026-04-05 03:46:44 UTC

## What this measures

Each benchmark runs the **full MarkCrawl pipeline** end-to-end (no other tools):

```
1. Discover URLs     — fetch robots.txt, parse sitemap or follow links
2. Fetch pages       — HTTP GET each URL (adaptive throttle, delay=0 base)
3. Clean HTML        — strip <nav>, <footer>, <script>, <style>, cookie banners
4. Convert to Markdown — transform cleaned HTML via markdownify
5. Write .md files   — one file per page with citation header
6. Write JSONL index — append url, title, crawled_at, citation, text per page
```

**Pages/second** includes all six steps — network fetch is typically the
bottleneck, not HTML parsing or Markdown conversion. Benchmarks run with
`delay=0` (adaptive throttle only). MarkCrawl automatically backs off
if the server is slow or returns 429 rate-limit responses.

Source: [`benchmarks/benchmark_markcrawl.py`](benchmark_markcrawl.py)

## Summary

- **Sites tested:** 7
- **Total pages crawled:** 227
- **Total time:** 37.9s
- **Overall pages/second:** 5.99

## Performance

### Small (1-5 pages) — 7 pages in 2.5s (2.8 p/s), 56 KB output

| Site | Description | Pages | Time (s) | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| httpbin | Simple HTTP test service (minimal HTML, 1-2 pages) | 2 | 1.0 | 1.98 | 37 | 2 | 47 |
| scrapethissite | Scraping practice site (structured data tables) | 5 | 1.5 | 3.31 | 570 | 54 | 46 |

### Medium (15-30 pages) — 60 pages in 12.7s (4.7 p/s), 2280 KB output

| Site | Description | Pages | Time (s) | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| fastapi-docs | FastAPI framework docs (API docs with code examples, tutorials) | 25 | 7.6 | 3.27 | 3383 | 1741 | 143 |
| python-docs | Python standard library index + module pages | 20 | 2.5 | 7.91 | 1004 | 464 | 101 |
| quotes-toscrape | Paginated quotes (tests link-following across 10+ pages) | 15 | 2.5 | 5.94 | 225 | 75 | 101 |

### Large (50-100 pages) — 160 pages in 22.7s (7.1 p/s), 847 KB output

| Site | Description | Pages | Time (s) | Pages/sec | Avg words | Output KB | Peak MB |
|---|---|---|---|---|---|---|---|
| books-toscrape | E-commerce catalog (50+ product pages, pagination, categories) | 60 | 8.1 | 7.43 | 288 | 492 | 98 |
| quotes-toscrape-large | Paginated quotes (100 page deep crawl, link-following stress test) | 100 | 14.6 | 6.84 | 170 | 355 | 70 |


## Extraction Quality

| Site | Junk detected | Title rate | Citation rate | JSONL complete |
|---|---|---|---|---|
| httpbin | 0 | 50% | 100% | 100% |
| scrapethissite | 0 | 100% | 100% | 100% |
| fastapi-docs | 0 | 100% | 100% | 100% |
| python-docs | 6 | 100% | 100% | 100% |
| quotes-toscrape | 0 | 100% | 100% | 100% |
| books-toscrape | 0 | 100% | 100% | 100% |
| quotes-toscrape-large | 0 | 100% | 100% | 100% |

## Quality Scores

| Metric | Score | Target | Status |
|---|---|---|---|
| Title extraction rate | 93% | >90% | PASS |
| Citation completeness | 100% | 100% | PASS |
| JSONL field completeness | 100% | 100% | PASS |
| Junk in output | 6 matches | 0 | NEEDS WORK |
| Min pages crawled | all met | all sites | PASS |

## Junk Detection Details

### python-docs
- ©\s*\d{4}.*all rights reserved: 3 match(es)
- all rights reserved: 3 match(es)


## What these metrics mean

- **Pages/sec**: Crawl throughput (higher is better). Affected by network, server response time, and `--delay`.
- **Avg words/page**: Average extracted content size. Very low values may indicate extraction issues.
- **Junk detected**: Count of navigation, footer, script, or cookie text found in extracted Markdown. Should be 0.
- **Title rate**: Percentage of pages where a `<title>` was successfully extracted.
- **Citation rate**: Percentage of JSONL rows with a complete citation string.
- **JSONL complete**: Percentage of JSONL rows with all required fields (url, title, path, crawled_at, citation, tool, text).

## Reproducing these results

```bash
pip install markcrawl
python benchmarks/benchmark_markcrawl.py
```
