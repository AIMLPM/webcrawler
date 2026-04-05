# Head-to-Head Benchmark Plan: MarkCrawl vs Other Crawlers

## Goal

Compare MarkCrawl against Crawl4AI, FireCrawl (self-hosted), and Scrapy on the same sites with equivalent settings, measuring what matters for the "crawl a documentation site for RAG" use case.

If another tool is faster, we say so. The comparison is factual, not promotional.

## Decision: what happens when MarkCrawl loses

We expect MarkCrawl to lose on some metrics. Here's the pre-written narrative for each scenario:

| Scenario | Likely? | Our response |
|---|---|---|
| Scrapy has 2-3x higher throughput | Very likely | Position on simplicity: "Scrapy is faster but requires building spiders, pipelines, and Markdown conversion. MarkCrawl trades peak throughput for one-command simplicity." |
| Scrapy has 5x+ higher throughput | Possible | Investigate async (`httpx`/`aiohttp`) as a roadmap item. Document the gap honestly. |
| Crawl4AI wins on JS-rendered sites | Almost certain | Expected — Crawl4AI is built around Playwright. Note that MarkCrawl's `--render-js` is optional, keeping the core lightweight. |
| Crawl4AI has better extraction quality | Possible | If true, investigate their cleaning approach and consider adopting readability-based extraction. |
| FireCrawl has better Markdown quality | Possible | Analyze their conversion pipeline. They may use a different HTML-to-Markdown library or post-processing. |
| MarkCrawl has the most junk in output | Would be bad | Fix the extraction pipeline before publishing results. This is a quality bug, not a positioning question. |

## What we compare

**Measured:** Fetch HTML → extract clean Markdown → write to disk (the common denominator).

**NOT measured** (different scope, would need separate benchmarks):
- LLM extraction speed (only MarkCrawl and Crawl4AI have this)
- Supabase/vector upload (unique to MarkCrawl)
- FireCrawl SaaS API latency (depends on their servers, not the tool)
- Anti-bot bypass capability

## Tools and settings

**All tools run with equivalent settings:**

| Setting | Value | Why |
|---|---|---|
| Delay | 0 | Isolate processing speed, not politeness policy |
| Primary concurrency | 5 | How these tools are designed to be used in practice |
| Secondary concurrency | 1 | Single-threaded overhead comparison |
| JS rendering | OFF for static sites, ON for JS site | Fair comparison per site type |
| Timeout | 15s per request | Consistent across all |
| Output format | Markdown | Common denominator |
| Iterations | 3 per site, report median + std dev | Network variance is real |
| Warm-up | 1 throwaway run per site before timing | Exclude DNS/TLS cold start |

### How each tool runs

**MarkCrawl:**
```bash
markcrawl --base $URL --out ./results/markcrawl/$SITE --delay 0 --concurrency 5 --max-pages $N
```

**Crawl4AI:**
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
config = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator())
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url=URL, config=config)
    # Write result.markdown to file
```

**FireCrawl (self-hosted via Docker):**
```bash
docker run -p 3002:3002 firecrawl/firecrawl:latest
```
```python
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_url="http://localhost:3002")
result = app.crawl_url(URL, params={"limit": N, "scrapeOptions": {"formats": ["markdown"]}})
```

**Scrapy + markdownify** (fair comparison — Scrapy doesn't output Markdown natively):
```python
# Custom spider + markdownify pipeline item
# Markdown conversion cost is included in the timing
```

## Test sites

| Site | Pages | Type | Structural challenge |
|---|---|---|---|
| http://quotes.toscrape.com | 15 | Paginated content | Link-following, simple HTML |
| http://books.toscrape.com | 60 | E-commerce catalog | Pagination, product cards, categories |
| https://fastapi.tiangolo.com | 25 | API documentation | Code blocks, headings, tabs, admonitions |
| https://docs.python.org/3/library/ | 20 | Standard library docs | Tables, nested lists, cross-references |
| http://quotes.toscrape.com/js/ | 15 | JS-rendered version | Same content, requires browser rendering |

## Metrics

### Performance (automated)

| Metric | How measured | Tool |
|---|---|---|
| Pages/second (concurrent) | Total pages / wall-clock time at concurrency=5 | Script timer |
| Pages/second (sequential) | Same at concurrency=1 | Script timer |
| Time to first page | Time from process start to first .md file written | Script timer |
| Peak memory (RSS) | `psutil.Process().memory_info().rss` sampled every 0.5s during crawl | psutil |
| Output size | Total bytes of all .md files | `os.path.getsize` |

Note: Time to first page includes browser launch for Crawl4AI/FireCrawl. This is intentional — it's what the developer experiences.

### Markdown quality rubric (manual, reproducible)

For each test site, select 5 pages with known structural elements. Score each tool on a binary pass/fail per element:

| Element | Pass criteria | Pages to test |
|---|---|---|
| **Heading preservation** | All `<h1>`-`<h6>` converted to `#`-`######` with correct nesting | FastAPI tutorial page, Python docs module page |
| **Code block accuracy** | Fenced code blocks with language annotation preserved, no broken indentation | FastAPI endpoint examples, Python docs code samples |
| **Table rendering** | HTML tables converted to Markdown tables (or readable text if no table support) | Python docs comparison tables |
| **List structure** | Nested ordered/unordered lists maintain nesting and numbering | FastAPI query params docs |
| **Link preservation** | Internal and external links converted to Markdown `[text](url)` format | Any page with navigation links stripped, content links preserved |
| **Boilerplate removal** | No nav bar, footer, sidebar, cookie banner, or "Edit on GitHub" text in output | All pages — score as count of junk elements found |
| **Code inside paragraphs** | Inline code (`backticks`) preserved within paragraph text | FastAPI type hints documentation |

**Scoring per tool per site:** X/7 elements passing. Report as a percentage.

**Blind review:** Rename output directories to tool-A/tool-B/tool-C/tool-D before manual review to avoid bias.

### Junk detection (automated)

Same junk patterns as our existing benchmarks, applied to all tools equally:
- `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` tags in output
- Cookie banner/consent text
- "All rights reserved" boilerplate
- "Subscribe to newsletter" / "Follow us on" text

Count per tool across all pages. Lower is better.

## Report format

### Summary table

```markdown
| Tool | Pages/sec (c=5) | Pages/sec (c=1) | Quality score | Junk count | Output KB | Peak RAM MB | Install time |
|---|---|---|---|---|---|---|---|
| MarkCrawl | X.X | X.X | X/7 | X | XX | XX | Xs |
| Crawl4AI | X.X | X.X | X/7 | X | XX | XX | Xs |
| FireCrawl | X.X | X.X | X/7 | X | XX | XX | Xs |
| Scrapy+md | X.X | X.X | X/7 | X | XX | XX | Xs |
```

### Per-site breakdown

One table per site with all metrics.

### Side-by-side output samples

For each site, show the same page's Markdown output from all 4 tools. Let the reader judge quality directly.

### Developer experience table (separate)

| Tool | Install command | Install time | Dependencies | First crawl command |
|---|---|---|---|---|
| MarkCrawl | `pip install markcrawl` | Xs | 4 (bs4, markdownify, requests, certifi) | `markcrawl --base URL --out ./output` |
| Crawl4AI | `pip install crawl4ai && playwright install` | Xs | Heavy (Playwright, Chromium) | Python script required |
| FireCrawl | `docker run ...` | Xs | Docker + Node.js | API call or SDK |
| Scrapy | `pip install scrapy markdownify` | Xs | Scrapy framework | Write spider class |

## Reproducibility

All benchmarks will be runnable via a single script:

```bash
python benchmarks/run_comparison.py
```

This script:
1. Checks that all tools are installed (exits with clear error if not)
2. Runs warm-up pass for each site
3. Runs 3 iterations per tool per site
4. Measures memory via psutil sampling
5. Generates `benchmarks/COMPARISON.md` with all tables and statistics
6. Saves raw Markdown output from each tool for manual quality review

Anyone can re-run it and verify our numbers. If our results are biased, the community can check.

## Benchmark 2: MarkCrawl full pipeline (end-to-end)

This is a **separate, MarkCrawl-only benchmark** that times the complete RAG pipeline that no other single tool offers. It answers: "If I crawl 50 pages, extract structured fields, and upload to Supabase, how long does the whole thing take?"

### What we time (per stage)

```
Stage 1: Crawl           → pages.jsonl + .md files       (no API keys needed)
Stage 2: Extract fields  → extracted.jsonl                (needs OPENAI_API_KEY or similar)
Stage 3: Chunk + embed   → embedding vectors              (needs OPENAI_API_KEY)
Stage 4: Upload          → rows in Supabase               (needs SUPABASE_URL + KEY)
```

### Report format

```markdown
## Full Pipeline: FastAPI docs (25 pages)

| Stage | Time (s) | Cost | Output |
|---|---|---|---|
| Crawl (25 pages) | 4.8 | free | 25 .md files, 687 KB |
| Extract (5 fields) | 18.2 | ~$0.50 | extracted.jsonl |
| Chunk + embed | 3.1 | ~$0.003 | 89 chunks, 89 vectors |
| Upload to Supabase | 1.4 | free | 89 rows inserted |
| **Total** | **27.5** | **~$0.50** | **End-to-end RAG pipeline** |
```

### How it handles missing credentials

The script runs as much as possible without requiring setup:

| What's available | What runs |
|---|---|
| Nothing (just `pip install markcrawl`) | Stage 1 only — crawl timing |
| `OPENAI_API_KEY` set | Stages 1-3 — crawl + extract + embed |
| `OPENAI_API_KEY` + `SUPABASE_URL` + `SUPABASE_KEY` | All 4 stages — full pipeline |

Stages that can't run due to missing credentials are reported as "skipped (no API key)" rather than failing. This way anyone can run the benchmark and see at least the crawl timing.

### Mocked upload option

For users who want full pipeline timing without a real Supabase instance, the script offers a `--mock-upload` flag that:
- Runs the real chunking and embedding (measures actual OpenAI API time)
- Replaces the Supabase insert with a no-op (measures everything except network latency to Supabase)
- Reports the upload stage as "mocked — actual insert time depends on network to your Supabase instance"

### Script

```bash
# Crawl only (no API keys needed)
python benchmarks/run_pipeline.py

# With extraction (needs OPENAI_API_KEY)
python benchmarks/run_pipeline.py --extract

# Full pipeline with mock upload
python benchmarks/run_pipeline.py --extract --mock-upload

# Full pipeline with real Supabase
python benchmarks/run_pipeline.py --extract --upload
```

### Stage 5: Retrieval quality check (the real test)

The pipeline benchmark ends with a quality check that answers: "If I ask a question about the content I just crawled, do I get the right answer back?"

**How it works:**

1. After embedding, store all chunks + vectors in memory
2. Embed 5 test queries using the same embedding model
3. Compute cosine similarity between each query and all chunks
4. Check if the top-3 most similar chunks contain the correct source page
5. Report hit rate: "X/5 queries returned the correct page in top 3"

**Test queries for FastAPI docs (example):**

| Query | Expected source page | What it tests |
|---|---|---|
| "How do I add authentication to a FastAPI endpoint?" | Security/OAuth2 tutorial page | Can it find conceptual content? |
| "What is the default response status code?" | Response model docs | Can it find specific technical details? |
| "How do I define query parameters?" | Query parameters tutorial | Can it find tutorial content? |
| "What Python types does FastAPI support for request bodies?" | Request body docs | Can it find reference content? |
| "How do I handle file uploads?" | File upload tutorial | Can it find procedural content? |

**Why this is the most important metric:**

Pages/second measures how fast the pipe runs. Retrieval accuracy measures whether the pipe produces useful output. A crawler that's 10x faster but produces chunks that can't answer questions is worthless for RAG. This single metric — "does retrieval work?" — validates the entire pipeline: crawl quality, cleaning quality, chunk coherence, and embedding usefulness.

**No Supabase needed:** The similarity search runs in memory using numpy. The test is self-contained and reproducible.

```python
# Pseudocode for retrieval test
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

for query, expected_url in test_queries:
    query_vec = embed(query)
    scores = [(cosine_similarity(query_vec, chunk.vec), chunk) for chunk in all_chunks]
    top_3 = sorted(scores, reverse=True)[:3]
    hit = any(expected_url in chunk.url for _, chunk in top_3)
```

### Why this matters for positioning

No other single tool in the comparison offers this pipeline. The message isn't "we're faster at crawling" — it's "we're the only tool where `pip install markcrawl` gets you from URL to searchable vector database in 3 commands." The pipeline benchmark quantifies that value with real numbers.

## Where results are published

- Full results: `benchmarks/COMPARISON.md` (separate doc, not in README)
- README: one-line link — "See [benchmark comparison](benchmarks/COMPARISON.md) for performance data against other crawlers."
- No benchmark tables in the README — keeps the README about the tool, not about competition.
