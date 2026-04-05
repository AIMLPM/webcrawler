# MarkCrawl Benchmark Results

Generated: 2026-04-05 01:59:19 UTC

## Summary

- **Sites tested:** 7
- **Total pages crawled:** 213
- **Total time:** 110.4s
- **Overall pages/second:** 1.93

## Performance

### Small (1-5 pages) — 7 pages in 4.1s (1.7 p/s)

| Site | Description | Pages | Time (s) | Pages/sec | Avg words |
|---|---|---|---|---|---|
| httpbin | Simple HTTP test service (minimal HTML, 1-2 pages) | 2 | 1.2 | 1.71 | 37 |
| scrapethissite | Scraping practice site (structured data tables) | 5 | 2.9 | 1.74 | 579 |

### Medium (15-30 pages) — 46 pages in 22.9s (2.0 p/s)

| Site | Description | Pages | Time (s) | Pages/sec | Avg words |
|---|---|---|---|---|---|
| fastapi-docs | FastAPI framework docs (API docs with code examples, tutorials) | 25 | 13.3 | 1.88 | 1573 |
| python-docs | Python standard library index + module pages | 6 | 2.8 | 2.11 | 190 |
| quotes-toscrape | Paginated quotes (tests link-following across 10+ pages) | 15 | 6.7 | 2.22 | 150 |

### Large (50-100 pages) — 160 pages in 83.5s (1.9 p/s)

| Site | Description | Pages | Time (s) | Pages/sec | Avg words |
|---|---|---|---|---|---|
| books-toscrape | E-commerce catalog (50+ product pages, pagination, categories) | 60 | 30.9 | 1.94 | 291 |
| quotes-toscrape-large | Paginated quotes (100 page deep crawl, link-following stress test) | 100 | 52.5 | 1.90 | 176 |


## Extraction Quality

| Site | Junk detected | Title rate | Citation rate | JSONL complete |
|---|---|---|---|---|
| httpbin | 0 | 50% | 100% | 50% |
| scrapethissite | 0 | 100% | 100% | 100% |
| fastapi-docs | 0 | 100% | 100% | 100% |
| python-docs | 0 | 100% | 100% | 100% |
| quotes-toscrape | 0 | 100% | 100% | 100% |
| books-toscrape | 0 | 100% | 100% | 100% |
| quotes-toscrape-large | 0 | 100% | 100% | 100% |

## Quality Scores

| Metric | Score | Target | Status |
|---|---|---|---|
| Title extraction rate | 93% | >90% | PASS |
| Citation completeness | 100% | 100% | PASS |
| JSONL field completeness | 93% | 100% | NEEDS WORK |
| Junk in output | 0 matches | 0 | PASS |
| Min pages crawled | some failed | all sites | NEEDS WORK |

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
python benchmarks/run_benchmarks.py
```
