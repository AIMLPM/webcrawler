# MarkCrawl by iD8 🕷️📝
### Turn any website into clean Markdown for LLM pipelines — in one command.

[![CI](https://github.com/AIMLPM/markcrawl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AIMLPM/markcrawl/actions/workflows/ci.yml)
![PyPI Version](https://img.shields.io/pypi/v/markcrawl)
![License](https://img.shields.io/github/license/AIMLPM/markcrawl)
[![MCP Server](https://img.shields.io/badge/MCP-AA-green?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiA3bDEwIDUgMTAtNS0xMC01ek0yIDE3bDEwIDUgMTAtNS0xMC01LTEwIDV6TTIgMTJsMTAgNSAxMC01LTEwLTUtMTAgNXoiIGZpbGw9IndoaXRlIi8+PC9zdmc+)](https://glama.ai/mcp/servers/AIMLPM/markcrawl)

```bash
pip install markcrawl
markcrawl --base https://docs.example.com --out ./output --show-progress
```

MarkCrawl is a crawl-and-structure engine. It crawls a website, strips navigation/scripts/boilerplate, and writes clean Markdown files with a structured JSONL index. Every page includes a citation with the access date. No API keys needed.

Everything else — LLM extraction, Supabase upload, MCP server, LangChain tools — is optional and installed separately.

## Quickstart (2 minutes)

```bash
pip install markcrawl
markcrawl --base https://httpbin.org --out ./demo --show-progress
```

Your `./demo` folder now contains:

```text
demo/
├── index__a4f3b2c1d0.md    ← clean Markdown of the page
└── pages.jsonl              ← structured index (one JSON line per page)
```

Each line in `pages.jsonl`:

```json
{
  "url": "https://httpbin.org/",
  "title": "httpbin.org",
  "crawled_at": "2026-04-04T12:30:00Z",
  "citation": "httpbin.org. httpbin.org. Available at: https://httpbin.org/ [Accessed April 04, 2026].",
  "tool": "markcrawl",
  "text": "# httpbin.org\n\nA simple HTTP Request & Response Service..."
}
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

### Benchmark results (7 tools, 8 sites, 92 queries)

**Speed:** colly+md is fastest (5.8 pages/sec), scrapy+md second (5.2), markcrawl third (3.0) — but markcrawl is the only tool that fetched all 210 pages without missing any. Playwright-based tools are 2-7x slower. See [speed comparison](benchmarks/SPEED_COMPARISON.md).

**Output cleanliness:** markcrawl has the lowest nav pollution (4 words of preamble per page vs 275-398 for others), at the cost of 84% recall vs 97% for crawlee. See [quality comparison](benchmarks/QUALITY_COMPARISON.md).

**RAG answer quality:** markcrawl produces the highest LLM answer scores (3.91/5) with the fewest chunks per page (14.2). The gap is small but consistent across all 92 queries:

| Tool | Chunks/page | Answer Quality (/5) | Annual cost (100K pages, 1K queries/day) |
|---|---|---|---|
| **markcrawl** | **14.2** | **3.91** | **$4,995** |
| scrapy+md | 17.2 | 3.86 | $6,011 |
| crawl4ai | 23.6 | 3.82 | $7,102 |
| colly+md | 25.9 | 3.83 | $7,418 |
| playwright | 27.8 | 3.74 | $8,291 |
| crawlee | 29.5 | 3.80 | $7,826 |

Fewer chunks = lower storage and embedding costs. Cleaner chunks = better answers with less context. For the complete cost analysis across all scales (100 to 1M pages) with full methodology, see [benchmarks/COST_AT_SCALE.md](benchmarks/COST_AT_SCALE.md).

See also: [Retrieval quality](benchmarks/RETRIEVAL_COMPARISON.md) | [Answer quality](benchmarks/ANSWER_QUALITY.md)
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
| `--use-sitemap` / `--no-sitemap` | Enable/disable sitemap discovery |
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
- **JavaScript SPAs without `--render-js`** — add `markcrawl[js]` for React/Vue/Angular

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
├── benchmarks/
│   ├── Dockerfile
│   ├── run_benchmarks.sh
│   ├── preflight.py
│   ├── benchmark_all_tools.py
│   ├── benchmark_markcrawl.py
│   ├── benchmark_quality.py
│   ├── benchmark_retrieval.py
│   ├── benchmark_answer_quality.py
│   ├── quality_scorer.py
│   ├── crawlee_worker.py
│   ├── lint_reports.py
│   ├── METHODOLOGY.md
│   ├── SPEED_COMPARISON.md
│   ├── QUALITY_COMPARISON.md
│   ├── RETRIEVAL_COMPARISON.md
│   ├── ANSWER_QUALITY.md
│   ├── COST_AT_SCALE.md
│   └── MARKCRAWL_RESULTS.md
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
- [ ] Fuzzy duplicate-content detection
- [ ] PDF support
- [ ] Authenticated crawling
- [ ] Multi-provider embeddings

<details>
<summary>Shipped features</summary>

- `pip install markcrawl` on PyPI
- 102 automated tests + GitHub Actions CI (Python 3.10-3.13) + ruff linting
- Markdown and plain text output with auto-citation
- Sitemap-first crawling with robots.txt compliance
- Text chunking with configurable overlap
- Supabase/pgvector upload for RAG
- JavaScript rendering via Playwright
- Concurrent fetching and proxy support
- Resume interrupted crawls
- LLM extraction (OpenAI, Claude, Gemini, Grok) with auto-field discovery
- MCP server, LangChain tools, OpenClaw skill
</details>

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). If you used an LLM to generate code, include the prompt in your PR.

## Security

See [SECURITY.md](SECURITY.md).

## Privacy

MarkCrawl runs locally. No telemetry, no analytics, no data sent anywhere. See [PRIVACY.md](PRIVACY.md).

## License

MIT. See [LICENSE](LICENSE).
