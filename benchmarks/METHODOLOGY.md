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
| Warm-up | 1 throwaway run per site before timing | Exclude DNS/TLS cold start (see validation below) |
| Tool order | Randomized per site per run | Eliminate CDN/DNS cache bias from fixed ordering |

### Why we keep the warmup run

We validated that the warmup run meaningfully improves benchmark stability.
The experiment (`benchmarks/warmup_validation/test_warmup_impact.py`) runs
each tool twice on the same site — once cold and once with a throwaway warmup
— and compares medians, standard deviations, and first-iteration outliers.

**Results (books-toscrape, 60 pages, concurrency=5, 4 iterations each):**

|                   | Median | Std dev | 1st iter | Range        |
|-------------------|--------|---------|----------|--------------|
| markcrawl (cold)  | 8.89s  | 0.59s   | 9.72s    | 8.32 – 9.72s |
| markcrawl (warm)  | 7.84s  | 0.32s   | 7.72s    | 7.64 – 8.36s |
| crawl4ai (cold)   | 5.67s  | 0.73s   | 6.95s    | 5.34 – 6.95s |
| crawl4ai (warm)   | 5.71s  | 0.40s   | 6.09s    | 5.28 – 6.09s |

**Key findings:**

1. **Variance drops ~47%** with warmup for both requests-based and
   browser-based tools. Lower variance means fewer iterations are needed
   to get a reliable median.

2. **The first cold iteration is 22–24% slower** than the warmed median
   for both tools, due to DNS resolution, TCP/TLS handshake, server-side
   CDN cache warming, and Python import/JIT effects.

3. **For markcrawl, warmup also shifts the median 13% faster**, likely
   because HTTP keep-alive and connection pooling benefit subsequent
   requests to the same host.

4. **With only 2 timed iterations** (our default), a cold first-run
   outlier has outsized impact on the median. Warmup eliminates this bias.

**Decision:** warmup is enabled by default. The cost is 1 extra run per
tool-site pair. The benefit is ~47% less measurement noise, which makes
the difference between "noisy numbers that could go either way" and
"stable numbers readers can trust."

To reproduce: `python benchmarks/warmup_validation/test_warmup_impact.py`

Full results: `benchmarks/warmup_validation/results_2026-04-07.txt`

### How each tool runs

> **Important:** No tool in this benchmark runs purely "out of the box." Every tool requires
> custom glue code for URL dispatch, output serialization, and integration with the benchmark
> harness. The table below documents exactly what custom code each tool uses so readers can
> judge how representative the results are.

| Tool | Custom code written | What crawl4ai/scrapy/etc. provides natively |
|---|---|---|
| **markcrawl** | Direct `CrawlEngine` API calls with per-URL fetch + process loop | CLI is out-of-box, but benchmark uses the Python API for URL-list mode |
| **crawl4ai** | `arun_many()` batch dispatch, custom file I/O (`.md` + `.jsonl`) | `AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`, built-in markdown conversion. Also has `BFSDeepCrawlStrategy` for link discovery (unused) |
| **crawl4ai-raw** | Sequential `arun()` calls, same file I/O glue | Same as crawl4ai but without `arun_many()` batching — the simplest possible usage |
| **scrapy+md** | Full custom `Spider` class with `markdownify` in `parse()`, subprocess isolation | Scrapy provides the crawler framework; markdown conversion is custom |
| **crawlee** | Separate `crawlee_worker.py` subprocess with custom `PlaywrightCrawler` handler | Crawlee provides the crawler/queue; markdown conversion + file I/O is custom |
| **colly+md** | Go binary for HTML fetch + Python `markdownify` post-processing | Colly provides HTTP fetching; everything else is custom |
| **playwright** | Raw `page.goto()` + `page.content()` + `markdownify` | Playwright provides the browser; markdown conversion is entirely custom |
| **firecrawl** | API client with retry-with-backoff for rate limits, rate-limit wait subtracted from timing | FireCrawl API handles crawling + markdown conversion natively |

#### crawl4ai vs crawl4ai-raw

We run Crawl4AI in two configurations to show the impact of custom optimization:

- **crawl4ai** uses `arun_many()` which dispatches all URLs in a single batch call,
  letting crawl4ai manage browser tab concurrency internally. This is a performance
  optimization that requires knowing the URL list upfront.
- **crawl4ai-raw** uses sequential `arun()` calls with default `CrawlerRunConfig()` —
  the simplest possible crawl4ai usage. This represents what a developer gets with
  minimal effort.

Both use `result.markdown` directly (crawl4ai's built-in HTML-to-markdown conversion).
Neither uses crawl4ai's advanced features like `BFSDeepCrawlStrategy`, `FilterChain`,
content scoring, or LLM-based extraction.

#### Code samples

**MarkCrawl:**
```bash
markcrawl --base $URL --out ./results/markcrawl/$SITE --delay 0 --concurrency 5 --max-pages $N
```

**Crawl4AI (optimized):**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
    results = await crawler.arun_many(urls=url_list, config=CrawlerRunConfig())
    for result in results:
        # Write result.markdown to .md file + pages.jsonl
```

**Crawl4AI (raw baseline):**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
    for url in url_list:
        result = await crawler.arun(url=url, config=CrawlerRunConfig())
        # Write result.markdown to .md file + pages.jsonl
```

**Scrapy + markdownify:**
```python
# Custom Spider subclass with markdownify in parse()
# Markdown conversion cost is included in the timing
```

**FireCrawl:**
```python
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key=KEY)
result = app.crawl(url, limit=N, scrape_formats=["markdown"])
```

### Concurrency model comparison

Each tool handles concurrency differently. This affects how throughput scales and what limits apply.

| | MarkCrawl | Crawl4AI | Scrapy+md | Crawlee | FireCrawl |
|---|---|---|---|---|---|
| **Concurrency model** | Local threads (`--concurrency N`) | Async browser tabs (`arun_many`) | Async Twisted reactor (`CONCURRENT_REQUESTS`) | Async browser tabs (Playwright pool) | Remote browsers (server-side, tied to account tier) |
| **Default** | 1 (sequential) | 1 tab per `arun()`, batch via `arun_many()` | 16 | Automatic | 2 (free) to 100 (growth) |
| **Max practical** | Limited by target server's tolerance | Limited by local machine RAM/CPU | Limited by target server's tolerance | Limited by local machine RAM/CPU | Limited by your account tier |
| **Cost** | Free (your machine) | Free (your machine) | Free (your machine) | Free (your machine) | Pay for more browsers |
| **JS rendering** | Optional (`--render-js`, single Playwright) | Always (Playwright built-in) | No (HTTP only) | Always (Playwright built-in) | Always (remote Chromium) |
| **Scaling 1,000+ pages** | Increase `--concurrency`, add delay for politeness | Use `arun_many()` with dispatcher config | Increase `CONCURRENT_REQUESTS` | Configure crawler pool size | Upgrade account tier |

> **Note on FireCrawl tiers:** FireCrawl's crawl speed is directly tied to your account tier.
> Free accounts get 2 concurrent browsers, Hobby gets 5, Standard gets 50, and Growth gets 100.
> Per-page processing speed is the same across tiers — the difference is how many pages are
> processed simultaneously. A 100-page crawl that takes ~150s on free could finish in ~6s on Standard.

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

### Quality scorer normalizations

The automated quality scorer (`quality_scorer.py`) applies several normalizations to
compare tool outputs fairly. These are **scoring-layer customizations**, not crawler
customizations — they don't change what any tool produces, only how we measure it.

| Normalization | What it does | Why it's needed |
|---|---|---|
| **URL trailing-slash stripping** | `url.rstrip("/")` when matching pages across tools | Scrapy records `/author/Jane-Austen/`, others record `/author/Jane-Austen`. Without this, the same page is treated as two different pages and consensus breaks. |
| **Paragraph unwrapping** | Joins soft line-wrapped lines into single sentences before splitting | The same sentence wrapped at column 80 (scrapy) vs column 200 (crawl4ai) would split into different fragments, making identical content look different. |
| **Markdown link stripping** | `[text](url)` → `text` before comparing sentences | URL text like `comlogin` or `comtagworldpage1` would contaminate sentence matching. |
| **Underscore normalization** | `_` → space | Markdown emphasis residue (`_keyword_`) kept underscores because `\w` matches `_`. |
| **Sparse page exclusion** | Pages with <2 extractable sentences excluded from precision/recall average | Short pages (e.g. a tag page with one quote) produce 0% for all tools, dragging every average down equally and hiding real differences. |

These normalizations are applied equally to all tools. Without them, the precision/recall
numbers are dominated by formatting artifacts rather than content quality differences.

### Retrieval quality (embedding comparison)

The quality metrics above measure extraction quality — how well each tool converts HTML to
Markdown. But for RAG pipelines, the downstream question is more important: **does the
extracted content produce useful embeddings?**

A tool that includes nav boilerplate in every page might still score well on precision
(the boilerplate is "shared" across tools) but produce poor embeddings because the same
navigation text dilutes the semantic signal in every chunk.

We measure this by running the same retrieval pipeline across all tools, using **four
retrieval modes** to test under realistic production conditions:

1. **Chunk** each tool's output using markdown-aware chunking (default: 400 word max, 50 word overlap)
2. **Embed** all chunks using OpenAI `text-embedding-3-small` (1536 dimensions)
3. **Index** chunks for both embedding (cosine similarity) and keyword (BM25 Okapi) search
4. **Query** — run 92 test queries across 8 sites against each tool's index
5. **Score** — measure Hit@K at K=1,3,5,10,20 plus MRR across four retrieval modes:
   - **Embedding**: Cosine similarity only
   - **BM25**: Keyword search only (Okapi BM25)
   - **Hybrid**: Embedding + BM25 fused via Reciprocal Rank Fusion (RRF, k=60)
   - **Reranked**: Top-50 hybrid candidates reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2`

**Chunk size sensitivity**: Optionally runs at three chunk configurations (~256tok, ~512tok,
~1024tok) to verify that quality differences hold regardless of chunking parameters.

The chunking, embedding, and retrieval pipeline is identical for all tools — the only
variable is extraction quality. This isolates the question: does cleaner extraction produce
better retrieval?

**Test sites** (8 sites, 92 queries):
| Site | Type | Queries | Why included |
|---|---|---|---|
| quotes-toscrape | Simple HTML | 12 | Paginated content, tag/author pages |
| books-toscrape | E-commerce | 13 | Category pages, product detail |
| fastapi-docs | API documentation | 15 | Code blocks, tutorials, reference |
| python-docs | Standard library docs | 12 | Glossary, release notes, how-tos |
| react-dev | SPA (JS-rendered) | 12 | Tests JS rendering, interactive docs |
| wikipedia-python | Wiki | 10 | Tables, infoboxes, citations |
| stripe-docs | API docs (tabbed) | 10 | Tabbed content, code samples |
| blog-engineering | Tech blog | 8 | Article extraction, images |

Results are published in [RETRIEVAL_COMPARISON.md](RETRIEVAL_COMPARISON.md).

To run the retrieval benchmark:

```bash
source .env  # needs OPENAI_API_KEY
python benchmarks/benchmark_retrieval.py                       # default config
python benchmarks/benchmark_retrieval.py --chunk-sensitivity   # + size analysis
python benchmarks/benchmark_retrieval.py --no-rerank           # skip cross-encoder (faster)
```

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

### Prerequisites

Before running the comparison, run the pre-flight script. It checks every dependency, installs anything missing, and tells you exactly what's ready:

```bash
python benchmarks/preflight.py --install
```

This handles everything automatically:
- Creates a `.venv` virtual environment if needed (avoids macOS system Python restrictions)
- Installs all Python packages (`markcrawl`, `crawl4ai`, `scrapy`, `crawlee`, `playwright`, `firecrawl-py`, `psutil`, etc.)
- Installs the Playwright Chromium browser
- Installs Go via Homebrew (if needed) and compiles the `colly+md` binary
- Checks all 4 test sites are reachable
- Prints a final ready status board showing green ✓ or red ✗ for every component

After it completes, activate the venv and run:

```bash
source .venv/bin/activate
python benchmarks/benchmark_all_tools.py
```

**FireCrawl (optional — skipped by default)**

FireCrawl requires one of:

- `FIRECRAWL_API_KEY` — use the FireCrawl SaaS API (free tier available at firecrawl.dev)
- `FIRECRAWL_API_URL` — point to a self-hosted instance

Add either to `.env` in the project root. The script auto-loads it — no need to `source .env` manually.

Self-hosting requires docker-compose (not a single container):

```bash
# See https://github.com/mendableai/firecrawl for the compose file
# Add to .env:
# FIRECRAWL_API_URL=http://localhost:3002
```

If neither env var is set, firecrawl is skipped and the other 6 tools run normally.

<details>
<summary>Manual setup reference (if you prefer not to use --install)</summary>

Python tools and their packages:

| Tool | Package(s) |
|---|---|
| markcrawl | `pip install -e .` (from repo root) |
| crawl4ai | `crawl4ai` 0.8.6+ |
| scrapy+md | `scrapy` + `markdownify` |
| crawlee | `crawlee[playwright]` 1.6.1+ |
| playwright | `playwright` 1.58.0+ |
| firecrawl | `firecrawl-py` 4.22.0+ (v2 API — `crawl()` not `crawl_url()`) |

`psutil` is also required for memory tracking.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
pip install crawl4ai scrapy markdownify crawlee playwright firecrawl-py psutil
playwright install chromium
```

For the Colly binary (Go 1.18+ required):

```bash
cd benchmarks/colly_crawler
go build -o colly_crawler .
cd ../..
```

The script checks for the binary at `benchmarks/colly_crawler/colly_crawler` and skips `colly+md` if it is not found.

</details>

### Running the benchmark

```bash
source .venv/bin/activate
python benchmarks/benchmark_all_tools.py
```

This script:
1. Checks that all tools are installed (exits with clear error if not)
2. Runs warm-up pass for each site
3. Runs 3 iterations per tool per site
4. Measures memory via psutil sampling
5. Generates `benchmarks/SPEED_COMPARISON.md` with all tables and statistics
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

### A note on fairness

The retrieval quality check is the most important part of the pipeline benchmark — and it's designed to be critical of our own tool, not to give us an unfair advantage.

The retrieval check validates the entire pipeline end-to-end: if the crawl missed content, the chunks split badly, or the embeddings are poor, the test catches it. It's the metric that actually matters for RAG, and it's self-contained (no Supabase required).

We publish this test against MarkCrawl's own output because no other tool in the comparison offers the full crawl-to-retrieval pipeline. This isn't a competitive claim — it's a self-assessment. If our retrieval accuracy is 3/5 or worse, that's a signal our chunking or extraction needs work, and we'll say so. The purpose is to hold ourselves accountable to the end-to-end quality bar, not to declare victory in a category where we're the only entrant.

If other tools add similar end-to-end pipelines in the future, we'd welcome running the same retrieval queries against their output for a direct comparison.

### Why this matters for positioning

No other single tool in the comparison offers this pipeline. The message isn't "we're faster at crawling" — it's "we're the only tool where `pip install markcrawl` gets you from URL to searchable vector database in 3 commands." The pipeline benchmark quantifies that value with real numbers.

## Where results are published

- Full results: `benchmarks/SPEED_COMPARISON.md` (separate doc, not in README)
- README: one-line link — "See [benchmark comparison](benchmarks/SPEED_COMPARISON.md) for performance data against other crawlers."
- No benchmark tables in the README — keeps the README about the tool, not about competition.
