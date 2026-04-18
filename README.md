# MarkCrawl by iD8 🕷️📝
### Turn any webpage or website into clean Markdown for LLM pipelines — in one command.

[![CI](https://github.com/AIMLPM/markcrawl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AIMLPM/markcrawl/actions/workflows/ci.yml)
![PyPI Version](https://img.shields.io/pypi/v/markcrawl)
![License](https://img.shields.io/github/license/AIMLPM/markcrawl)
[![MCP Server](https://img.shields.io/badge/MCP-AA-green?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiA3bDEwIDUgMTAtNS0xMC01ek0yIDE3bDEwIDUgMTAtNS0xMC01LTEwIDV6TTIgMTJsMTAgNSAxMC01LTEwLTUtMTAgNXoiIGZpbGw9IndoaXRlIi8+PC9zdmc+)](https://glama.ai/mcp/servers/AIMLPM/markcrawl)

```bash
pip install markcrawl
markcrawl --base https://docs.example.com --out ./output --show-progress
```

MarkCrawl is a crawl-and-structure engine. It fetches one page or crawls an entire website, strips navigation/scripts/boilerplate, and writes clean Markdown files with a structured JSONL index. Every page includes a citation with the access date. No API keys needed.

Everything else — LLM extraction, Supabase upload, MCP server, LangChain tools — is optional and installed separately.

> **Want a hosted API instead of running locally?** [Join the waitlist](https://github.com/AIMLPM/markcrawl/issues/13) — we're gauging interest.

**LLM agents:** Load [docs/LLM_PROMPT.md](docs/LLM_PROMPT.md) as a system prompt to generate correct MarkCrawl commands automatically.

## Quickstart (2 minutes)

```bash
pip install markcrawl
markcrawl --base https://quotes.toscrape.com --out ./demo --max-pages 5 --show-progress
```

Your `./demo` folder now contains:

```text
demo/
├── index__a4f3b2c1d0.md    ← clean Markdown of the page
├── page-2__b7e2d1f0a3.md
├── ...
└── pages.jsonl              ← structured index (one JSON line per page)
```

Each line in `pages.jsonl`:

```json
{
  "url": "https://quotes.toscrape.com/",
  "title": "Quotes to Scrape",
  "crawled_at": "2026-04-04T12:30:00Z",
  "citation": "Quotes to Scrape. quotes.toscrape.com. Available at: https://quotes.toscrape.com/ [Accessed April 04, 2026].",
  "tool": "markcrawl",
  "text": "# Quotes to Scrape\n\n> "The world as we have created it is a process of our thinking..." — Albert Einstein\n\nTags: change, deep-thoughts, thinking, world..."
}
```

## Common Recipes

**Scrape a single page:**

```bash
markcrawl --base https://example.com/pricing --no-sitemap --max-pages 1
```

**Scrape a single JS-rendered page** (React, Vue, YouTube, etc.):

```bash
markcrawl --base "https://www.youtube.com/@channel/videos" \
  --no-sitemap --max-pages 1 --render-js
# → outputs one .md file with video titles, view counts, and dates
```

For infinite-scroll pages like YouTube, this captures the first ~28 videos from the initial render.

**Crawl a docs site:**

```bash
markcrawl --base https://docs.example.com --max-pages 500 --concurrency 5 --show-progress
```

**Crawl a subsection without sitemap wandering:**

Large sites (YouTube, GitHub, etc.) have sitemaps with thousands of unrelated pages.
Use `--no-sitemap` to crawl only from your target URL:

```bash
markcrawl --base https://docs.example.com/guides \
  --no-sitemap --max-pages 50 --show-progress
```

**Competitive analysis** (crawl 3 competitors, extract pricing):

```bash
markcrawl --base https://competitor-one.com/pricing --no-sitemap --max-pages 1 --out ./comp1
markcrawl --base https://competitor-two.com/pricing --no-sitemap --max-pages 1 --out ./comp2
markcrawl --base https://competitor-three.com/pricing --no-sitemap --max-pages 1 --out ./comp3
markcrawl-extract \
  --jsonl ./comp1/pages.jsonl ./comp2/pages.jsonl ./comp3/pages.jsonl \
  --fields pricing_tiers features free_trial --show-progress
# → extracted.jsonl with structured pricing data across all three
```

**Docs site → RAG chatbot** (full pipeline: crawl, embed, query):

```bash
markcrawl --base https://docs.example.com --out ./docs --max-pages 500 --concurrency 5 --show-progress
markcrawl-upload --jsonl ./docs/pages.jsonl --show-progress
# → pages are chunked, embedded, and uploaded to Supabase/pgvector
# Wire your chatbot to query the vector table — see docs/SUPABASE.md
```

**API docs → code generation prompt:**

```bash
markcrawl --base https://api.example.com/docs --out ./api-docs --max-pages 200 --show-progress
# Feed the output to an LLM:
# "Using the API documentation in ./api-docs/pages.jsonl, generate a
#  typed Python client with methods for each endpoint."
```

**Back up a blog before it shuts down:**

```bash
markcrawl --base https://engineering.example.com/blog \
  --no-sitemap --max-pages 1000 --concurrency 5 --out ./blog-archive --show-progress
# → every post saved as clean Markdown with citations and access dates
```

**Skip junk pages** (job listings, login walls, SEO spam):

```bash
markcrawl --base https://example.com \
  --exclude-path "/job/*" --exclude-path "/careers/*" --exclude-path "/login" \
  --max-pages 500 --out ./output --show-progress
```

**Preview URLs before committing to a long crawl:**

```bash
markcrawl --base https://example.com --dry-run
# → prints every URL that would be crawled (from sitemap), then exits
# Pipe to wc -l to get a count, or grep to check for junk patterns
markcrawl --base https://example.com --dry-run | wc -l
markcrawl --base https://example.com --dry-run | grep "/job/"
```

**Only crawl specific sections** (blog + pricing, ignore everything else):

```bash
markcrawl --base https://example.com \
  --include-path "/blog/*" --include-path "/pricing" \
  --max-pages 200 --out ./output --show-progress
```

**Safe crawl of a job board** (dry-run + exclude):

```bash
# Step 1: see what you'd get
markcrawl --base https://tealhq.com --dry-run | head -50
# Step 2: exclude the job listings, crawl just the content pages
markcrawl --base https://tealhq.com \
  --exclude-path "/job/*" --exclude-path "/resume-examples/*" \
  --max-pages 200 --out ./tealhq --show-progress
```

**Choose an extraction backend:**

```bash
# Default (BS4 + markdownify) — fastest, good for most sites
markcrawl --base https://docs.example.com --out ./output --show-progress

# Ensemble — runs default + trafilatura, picks best per page
markcrawl --base https://docs.example.com --out ./output --extractor ensemble --show-progress

# ReaderLM-v2 — ML-based extraction (requires: pip install markcrawl[ml])
markcrawl --base https://docs.example.com --out ./output --extractor readerlm --show-progress
```

**Skip pages you've already crawled** (cross-crawl dedup):

```bash
# First crawl
markcrawl --base https://docs.example.com --out ./docs --show-progress
# Later — only fetches new/changed pages
markcrawl --base https://docs.example.com --out ./docs --cross-dedup --show-progress
```

**Crawl high-value pages first** (link prioritization):

```bash
markcrawl --base https://docs.example.com --out ./docs \
  --prioritize-links --max-pages 100 --show-progress
# Prioritizes content-rich pages (guides, docs) over low-value ones (legal, login)
```

**Smart-sample a large site** (e-commerce, job boards, real estate):

```bash
# Preview the pattern clusters first
markcrawl --base https://bigsite.com --dry-run --smart-sample --show-progress
# Crawl with sampling — 5 pages per templated cluster instead of thousands
markcrawl --base https://bigsite.com --out ./bigsite \
  --smart-sample --sample-size 5 --sample-threshold 20 --show-progress
```

**Download images alongside content** (photography blogs, product pages):

```bash
# Crawl a photography blog and save images from the content area
markcrawl --base https://photography-blog.example.com --out ./photos \
  --download-images --max-pages 50 --show-progress
# Output:
#   ./photos/assets/mountain-abc123.jpg
#   ./photos/assets/sunset-def456.png
#   ./photos/post-1__a1b2c3.md  ← Markdown with ![alt](assets/filename.ext) refs
#   ./photos/pages.jsonl         ← index includes "images" array per page

# Adjust minimum image size to skip thumbnails (default: 5000 bytes)
markcrawl --base https://example.com/gallery --out ./gallery \
  --download-images --min-image-size 20000 --show-progress
```

**Resume an interrupted crawl:**

```bash
markcrawl --base https://docs.example.com --out ./docs --resume --show-progress
```

<details>
<summary>How it compares to other crawlers</summary>

Different tools make different tradeoffs. This table summarizes the main differences:

| | MarkCrawl | FireCrawl | Crawl4AI | Scrapy |
|---|---|---|---|---|
| License | MIT | AGPL-3.0 | Apache-2.0 | BSD-3 |
| Install | `pip install markcrawl` | SaaS or self-host | pip + Playwright | pip + framework |
| Output | Markdown + JSONL | Markdown + JSON | Markdown | Custom pipelines |
| JS rendering | Optional (`--render-js`) | Built-in | Built-in | Plugin |
| LLM extraction | Optional add-on | Via API | Built-in | None |
| Best for | Single-site crawl → Markdown | Hosted scraping API | AI-native crawling | Large-scale distributed |

Each tool has strengths: FireCrawl excels as a hosted API, Crawl4AI has deep browser automation, and Scrapy handles massive distributed workloads. MarkCrawl focuses on simple local crawls that produce LLM-ready Markdown.

### Benchmark results (7 tools, April 2026 — v2 methodology)

**Speed:** markcrawl is fastest (12.1 pages/sec), scrapy+md second (9.5). Playwright-based tools (crawlee, playwright, crawl4ai) average 1.5–2.2 pages/sec.

**Content signal:** markcrawl leads at 99% (ratio of answer-bearing tokens to total output) — almost no navigation, footer, or boilerplate makes it into your embeddings.

**RAG quality:** markcrawl scores 4.52/5 on LLM-judged answer quality (tied #2, leader at 4.53 within noise) and 0.698 MRR (3rd, leader crawlee at 0.733) — with 2.1x fewer chunks than crawlee, keeping embedding costs low.

| Tool | Speed (p/s) | Content Signal | MRR | Answer (/5) | Annual cost (100K pages) |
|---|---|---|---|---|---|
| **markcrawl** | **12.1** | **99%** | 0.698 | 4.52 | **$4,505** |
| scrapy+md | 9.5 | 93% | 0.459 | 4.03 | $5,464 |
| colly+md | 4.2 | 67% | 0.677 | **4.53** | $7,213 |
| playwright | 2.2 | 64% | 0.727 | 4.42 | $7,320 |
| crawlee | 1.7 | 63% | **0.733** | 4.52 | $7,467 |
| crawl4ai | 1.5 | 83% | 0.694 | 4.43 | $6,960 |

Full benchmark data: [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | Methodology: [llm-crawler-benchmarks](https://github.com/AIMLPM/llm-crawler-benchmarks)

**RAG-optimized recipe (v0.6.0):** With `--i18n-filter --title-at-top` and the opt-in chunker flags (`auto_extract_title=True`, `prepend_first_paragraph=True`, `strip_markdown_links=True` on `chunk_markdown`), markcrawl reaches **0.8148 MRR** on the same 57-query benchmark — a +0.18 jump over the default config and +0.08 over the next best tool (crawlee at 0.733).
</details>

## Installation

**The core crawler is the only thing you need.** Everything else is optional.

```bash
pip install markcrawl                # Core crawler (free, no API keys)
```

Optional add-ons:

```bash
pip install markcrawl[extract]       # + LLM extraction (OpenAI, Claude, Gemini, Grok)
pip install markcrawl[js]            # + JavaScript rendering (Playwright)
pip install markcrawl[upload]        # + Supabase upload with embeddings
pip install markcrawl[ml]            # + ReaderLM-v2 extraction backend
pip install markcrawl[mcp]           # + MCP server for AI agents
pip install markcrawl[langchain]     # + LangChain tool wrappers
pip install markcrawl[all]           # Everything
```

For Playwright, also run `playwright install chromium` after installing.

<details>
<summary>Install from source (for development)</summary>

```bash
git clone https://github.com/AIMLPM/markcrawl.git
cd markcrawl
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```
</details>

## Crawling

```bash
markcrawl --base https://www.example.com --out ./output --show-progress
```

Add flags as needed:

```bash
markcrawl \
  --base https://www.example.com \
  --out ./output \
  --include-subdomains \        # crawl sub.example.com too
  --render-js \                 # render JavaScript (React, Vue, etc.)
  --concurrency 5 \             # fetch 5 pages in parallel
  --proxy http://proxy:8080 \   # route through a proxy
  --max-pages 200 \             # stop after 200 pages
  --format markdown \           # or "text" for plain text
  --show-progress
```

Resume an interrupted crawl:

```bash
markcrawl --base https://www.example.com --out ./output --resume --show-progress
```

### Output

Each page becomes a `.md` file with a citation header:

```markdown
# Getting Started

> URL: https://docs.example.com/getting-started
> Crawled: April 04, 2026
> Citation: Getting Started. docs.example.com. Available at: https://docs.example.com/getting-started [Accessed April 04, 2026].

Welcome to the platform. This guide walks you through installation...
```

Navigation, footer, cookie banners, and scripts are stripped. Only the main content remains.

<details>
<summary>All crawler CLI arguments</summary>

| Argument | Description |
|---|---|
| `--base` | Base site URL to crawl |
| `--out` | Output directory |
| `--format` | `markdown` or `text` (default: `markdown`) |
| `--show-progress` | Print progress and crawl events |
| `--render-js` | Render JavaScript with Playwright before extracting |
| `--concurrency` | Pages to fetch in parallel (default: `1`) |
| `--proxy` | HTTP/HTTPS proxy URL |
| `--resume` | Resume from saved state |
| `--include-subdomains` | Include subdomains under the base domain |
| `--max-pages` | Max pages to save; `0` = unlimited (default: `500`) |
| `--delay` | Minimum delay between requests in seconds (default: `0`, adaptive throttle adjusts automatically) |
| `--timeout` | Per-request timeout in seconds (default: `15`) |
| `--min-words` | Skip pages with fewer words (default: `20`) |
| `--user-agent` | Override the default user agent |
| `--use-sitemap` / `--no-sitemap` | Enable/disable sitemap discovery. Use `--no-sitemap` when you want to scrape a specific page or subsection — without it, large sites (YouTube, GitHub) may discover thousands of unrelated pages via their sitemap |
| `--exclude-path` | Glob pattern to exclude URL paths (e.g. `'/job/*'`). Can be repeated |
| `--include-path` | Glob pattern to include URL paths (e.g. `'/blog/*'`). Only matching paths are crawled. Can be repeated |
| `--dry-run` | Discover URLs (via sitemap/links) and print them without fetching content |
| `--smart-sample` | Auto-detect templated URL patterns and sample from large clusters instead of crawling every page |
| `--sample-size` | Pages to sample per templated cluster (default: `5`, used with `--smart-sample`) |
| `--sample-threshold` | Clusters larger than this are sampled (default: `20`, used with `--smart-sample`) |
| `--auto-resume` | Automatically resume if saved state exists, otherwise start fresh |
| `--cross-dedup` | Skip pages already seen in previous crawls to the same output directory |
| `--prioritize-links` | Score discovered links by predicted content yield — crawl high-value pages first |
| `--extractor` | Content extraction backend: `default`, `trafilatura`, `ensemble`, or `readerlm` |
| `--download-images` | Download images from the content area to `assets/` and use local paths in Markdown |
| `--min-image-size` | Minimum image file size in bytes to keep (default: `5000`). Smaller images are skipped |
| `--i18n-filter` | Skip URLs under locale path segments (`/fr/`, `/de-DE/`, `/zh-Hans/`, ...) — generic, no per-domain config |
| `--title-at-top` | Prepend `# {title}` to the `text` field of every JSONL row when not already present — top-MRR RAG recipe |
</details>

## Optional: structured extraction

If you need structured data (not just text), the extraction add-on uses an LLM to pull specific fields from each page.

```bash
pip install markcrawl[extract]

markcrawl-extract \
  --jsonl ./output/pages.jsonl \
  --fields company_name pricing features \
  --show-progress
```

Auto-discover fields across multiple crawled sites:

```bash
markcrawl-extract \
  --jsonl ./comp1/pages.jsonl ./comp2/pages.jsonl ./comp3/pages.jsonl \
  --auto-fields \
  --context "competitor pricing analysis" \
  --show-progress
```

Supports OpenAI, Anthropic (Claude), Google Gemini, and xAI (Grok) via `--provider`.

<details>
<summary>Extraction details</summary>

### Provider and model selection

```bash
markcrawl-extract --jsonl ... --fields pricing --provider openai         # default
markcrawl-extract --jsonl ... --fields pricing --provider anthropic      # Claude
markcrawl-extract --jsonl ... --fields pricing --provider gemini         # Gemini
markcrawl-extract --jsonl ... --fields pricing --provider grok           # Grok
markcrawl-extract --jsonl ... --fields pricing --model gpt-4o           # override model
```

| Provider | API key env var | Default model |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| Google Gemini | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| xAI (Grok) | `XAI_API_KEY` | `grok-3-mini-fast` |

### All extraction CLI arguments

| Argument | Description |
|---|---|
| `--jsonl` | Path(s) to `pages.jsonl` — pass multiple for cross-site analysis |
| `--fields` | Field names to extract (space-separated) |
| `--auto-fields` | Auto-discover fields by sampling pages |
| `--context` | Describe your goal for auto-discovery |
| `--sample-size` | Pages to sample for auto-discovery (default: `3`) |
| `--provider` | `openai`, `anthropic`, `gemini`, or `grok` |
| `--model` | Override the default model |
| `--output` | Output path (default: `extracted.jsonl`) |
| `--delay` | Delay between LLM calls in seconds (default: `0.25`) |
| `--show-progress` | Print progress |

### Output format

Extracted rows include LLM attribution:

```json
{
  "url": "https://competitor.com/pricing",
  "citation": "Pricing. competitor.com. Available at: ... [Accessed April 04, 2026].",
  "pricing_tiers": "Starter ($29/mo), Pro ($99/mo), Enterprise (contact sales)",
  "extracted_by": "gpt-4o-mini (openai)",
  "extraction_note": "Field values were extracted by an LLM and may be interpreted, not verbatim."
}
```
</details>

## Optional: Supabase vector search (RAG)

Chunk pages, generate embeddings, and upload to Supabase with pgvector:

```bash
pip install markcrawl[upload]

markcrawl --base https://docs.example.com --out ./output --show-progress
markcrawl-upload --jsonl ./output/pages.jsonl --show-progress
```

Requires `SUPABASE_URL`, `SUPABASE_KEY`, and `OPENAI_API_KEY`. See **[docs/SUPABASE.md](docs/SUPABASE.md)** for table setup, query examples, and recommendations.

## Optional: agent integrations

MarkCrawl includes integrations for AI agents. Each is an optional add-on.

<details>
<summary>MCP Server (Claude Desktop, Cursor, Windsurf)</summary>

```bash
pip install markcrawl[mcp]
```

```json
{
  "mcpServers": {
    "markcrawl": {
      "command": "python",
      "args": ["-m", "markcrawl.mcp_server"]
    }
  }
}
```

Tools: `crawl_site`, `list_pages`, `read_page`, `search_pages`, `extract_data`
</details>

<details>
<summary>LangChain Tool</summary>

```bash
pip install markcrawl[langchain]
```

```python
from markcrawl.langchain import all_tools
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

agent = initialize_agent(tools=all_tools, llm=ChatOpenAI(model="gpt-4o-mini"),
                         agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION)
agent.run("Crawl docs.example.com and summarize their auth guide")
```
</details>

<details>
<summary>OpenClaw Skill (WhatsApp, Telegram, Slack)</summary>

```bash
npx clawhub install markcrawl-skill
```

See [AIMLPM/markcrawl-clawhub-skill](https://github.com/AIMLPM/markcrawl-clawhub-skill).
</details>

<details>
<summary>LLM assistant prompt</summary>

Copy the system prompt from **[docs/LLM_PROMPT.md](docs/LLM_PROMPT.md)** into any LLM to get an assistant that generates correct MarkCrawl commands.
</details>

## When NOT to use MarkCrawl

- **Sites behind login/auth** — no cookie or session support
- **Aggressive bot protection** (Cloudflare, Akamai) — no anti-bot evasion
- **Millions of pages** — designed for hundreds to low thousands; use Scrapy for scale
- **PDF content** — HTML only (PDF support is on the roadmap)
- **JavaScript SPAs** — add `markcrawl[js]` and use `--render-js` for React/Vue/Angular
- **Infinite-scroll pages** — `--render-js` renders the initial page load but does not scroll; you'll get the first screenful of content (e.g., ~28 of 82 YouTube videos). For complete listings, combine with the platform's API or RSS feed (e.g., YouTube's `/feeds/videos.xml?channel_id=...`)

## Architecture

MarkCrawl is a web crawler. The optional layers (extraction, upload, agents) are separate add-ons that work with the crawler's output.

```text
CORE (free, no API keys)              OPTIONAL ADD-ONS
┌──────────────────────────┐
│ 1. Discover URLs         │          markcrawl[extract]  — LLM field extraction
│    (sitemap or links)    │          markcrawl[upload]   — Supabase/pgvector RAG
│ 2. Fetch & clean HTML    │          markcrawl[js]       — Playwright JS rendering
│ 3. Write Markdown + JSONL│          markcrawl[mcp]      — MCP server for agents
│    + auto-citation       │          markcrawl[langchain] — LangChain tools
└──────────────────────────┘
```

For internals, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Extending MarkCrawl

```python
from markcrawl import crawl

result = crawl("https://example.com", out_dir="./output")
print(f"Saved {result.pages_saved} pages")
```

```python
# Process output in your own pipeline
import json
with open(result.index_file) as f:
    for line in f:
        page = json.loads(line)
        your_db.insert(page)  # Pinecone, Weaviate, Elasticsearch, etc.
```

```python
# Use individual components
from markcrawl import chunk_text
from markcrawl.extract import LLMClient, extract_fields
```

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the full module map and extensibility guide.

## Cost

The core crawler is free. Two optional features have API costs:

| Feature | Cost | When |
|---|---|---|
| Structured extraction | ~$0.01-0.03 per page | `markcrawl-extract` |
| Supabase upload | ~$0.0001 per page | `markcrawl-upload` |

## Setting up API keys

Only needed for extraction and upload. The core crawler requires no keys.

```bash
# .env — in your working directory
OPENAI_API_KEY="sk-..."           # extraction (--provider openai) + upload
ANTHROPIC_API_KEY="sk-ant-..."    # extraction (--provider anthropic)
GEMINI_API_KEY="AI..."            # extraction (--provider gemini)
XAI_API_KEY="xai-..."             # extraction (--provider grok)
SUPABASE_URL="https://..."        # upload
SUPABASE_KEY="eyJ..."             # upload (service-role key)
```

```bash
source .env
```

<details>
<summary>Project structure</summary>

```text
.
├── README.md
├── LICENSE
├── PRIVACY.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── Dockerfile
├── Makefile
├── glama.json
├── pyproject.toml
├── requirements.txt
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml
│       └── publish.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── LLM_PROMPT.md
│   ├── MCP_SUBMISSION.md
│   ├── RAG_RETRIEVAL_RESEARCH.md
│   └── SUPABASE.md
├── tests/
│   ├── __init__.py
│   ├── test_chunker.py
│   ├── test_core.py
│   ├── test_extract.py
│   └── test_upload.py
└── markcrawl/
    ├── __init__.py
    ├── cli.py
    ├── core.py               # orchestrator
    ├── fetch.py              # HTTP/Playwright fetching
    ├── robots.py             # robots.txt parsing
    ├── throttle.py           # adaptive rate limiting
    ├── state.py              # crawl state & resume
    ├── urls.py               # URL normalization & filtering
    ├── extract_content.py    # HTML → Markdown conversion
    ├── dedup.py              # cross-crawl deduplication
    ├── link_scorer.py        # link prioritization
    ├── chunker.py
    ├── exceptions.py
    ├── utils.py
    ├── extract.py            # LLM field extraction
    ├── extract_cli.py
    ├── upload.py
    ├── upload_cli.py
    ├── langchain.py
    └── mcp_server.py
```
</details>

## Roadmap

- [ ] Canonical URL support
- [ ] PDF support
- [ ] Authenticated crawling
- [ ] Multi-provider embeddings

<details>
<summary>Shipped features</summary>

- `pip install markcrawl` on PyPI
- 200 automated tests + GitHub Actions CI (Python 3.10-3.13) + ruff linting
- Markdown and plain text output with auto-citation
- Sitemap-first crawling with robots.txt compliance
- Text chunking with configurable overlap + semantic chunking
- Supabase/pgvector upload for RAG
- JavaScript rendering via Playwright
- Concurrent fetching and proxy support
- Resume interrupted crawls + auto-resume
- LLM extraction (OpenAI, Claude, Gemini, Grok) with auto-field discovery
- MCP server, LangChain tools, OpenClaw skill
- Image alt text preservation
- Python API (`result.pages`)
- Page-type extraction and content-region heuristics
- Multiple extraction backends (default, trafilatura, ensemble, ReaderLM-v2)
- Cross-crawl deduplication (`--cross-dedup`)
- Link prioritization by predicted content yield (`--prioritize-links`)
- Smart sampling of templated URL clusters (`--smart-sample`)
- URL path filtering (`--include-path`, `--exclude-path`) and dry-run preview
</details>

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). If you used an LLM to generate code, include the prompt in your PR.

## Security

See [SECURITY.md](SECURITY.md).

## Privacy

MarkCrawl runs locally. No telemetry, no analytics, no data sent anywhere. See [PRIVACY.md](PRIVACY.md).

## License

MIT. See [LICENSE](LICENSE).
