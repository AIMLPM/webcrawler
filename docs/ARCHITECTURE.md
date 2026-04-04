# Architecture

MarkCrawl is designed as a **core engine + optional layers**. You can use just the crawler, or add extraction, storage, and MCP on top.

## Core vs optional layers

```text
┌─────────────────────────────────────────────────────────┐
│                     markcrawl CLI                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  CORE (no API keys, no optional deps)                   │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Discover  │→ │ Fetch &      │→ │ Transform to     │ │
│  │ URLs      │  │ Clean HTML   │  │ Markdown / Text  │ │
│  └───────────┘  └──────────────┘  └──────────────────┘ │
│       │                │                    │           │
│   sitemap.xml     strip nav/footer     .md files +     │
│   or link-follow  strip scripts        pages.jsonl     │
│                   extract <main>                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  OPTIONAL LAYERS (install separately)                   │
│                                                         │
│  ┌──────────────┐  pip install markcrawl[extract]       │
│  │ LLM Extract  │  OpenAI / Claude / Gemini             │
│  │ (extract.py) │  → extracted.jsonl                    │
│  └──────────────┘                                       │
│                                                         │
│  ┌──────────────┐  pip install markcrawl[upload]        │
│  │ RAG Upload   │  Chunk → Embed → Supabase/pgvector   │
│  │ (upload.py)  │  → vector search                     │
│  └──────────────┘                                       │
│                                                         │
│  ┌──────────────┐  pip install markcrawl[js]            │
│  │ JS Rendering │  Playwright / headless Chromium       │
│  │ (core.py)    │  → render SPAs before extraction      │
│  └──────────────┘                                       │
│                                                         │
│  ┌──────────────┐  pip install markcrawl[mcp]           │
│  │ MCP Server   │  Expose tools to AI agents            │
│  │ (mcp_server) │  Claude Desktop, Cursor, etc.         │
│  └──────────────┘                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## How the core crawl works

The `crawl()` function in `core.py` runs a 3-stage pipeline:

### Stage 1: Discover URLs

```
robots.txt → parse sitemap URLs → filter by scope → queue
                                         ↓ (if no sitemap)
                              use base URL as seed → follow <a> links
```

- Checks `robots.txt` first (respects disallow rules)
- Tries to find sitemap URLs from `robots.txt` (`Sitemap:` directive)
- Parses sitemap XML (handles nested sitemap indexes)
- Filters URLs by scope (`same_scope()` — same domain, optional subdomains)
- Falls back to link-following from the base URL if no sitemap is found

### Stage 2: Fetch & clean HTML

For each URL in the queue:

1. **Fetch** — via `requests` (default) or Playwright (`--render-js`)
2. **Validate** — check HTTP status, confirm `Content-Type: text/html`
3. **Clean DOM** — remove `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, cookie banners, sr-only elements
4. **Find main content** — look for `<main>`, `role="main"`, or fall back to `<body>`
5. **Deduplicate** — hash content, skip pages with identical extracted text

### Stage 3: Transform & write

- **Markdown mode** — uses `markdownify` to convert cleaned HTML to Markdown with ATX headings
- **Text mode** — uses BeautifulSoup `get_text()` with line deduplication
- **Output** — writes `.md`/`.txt` file per page + appends to `pages.jsonl`

## Key data structures

### `pages.jsonl` (one line per page)

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "path": "page__a1b2c3d4e5.md",
  "text": "Extracted content as markdown or plain text..."
}
```

### `extracted.jsonl` (one line per page, after LLM extraction)

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "field_name": "extracted value",
  "another_field": "another value",
  "source_file": "./comp1/pages.jsonl"
}
```

### `.crawl_state.json` (resume support)

```json
{
  "seen_urls": ["https://example.com/", "https://example.com/about"],
  "seen_content": ["a1b2c3...", "d4e5f6..."],
  "to_visit": ["https://example.com/pricing", "https://example.com/docs"],
  "saved_count": 42,
  "seeds": []
}
```

## Module map

| Module | Role | Dependencies |
|---|---|---|
| `core.py` | Core crawl engine — URL discovery, fetch, HTML cleaning, transform | `requests`, `beautifulsoup4`, `markdownify` |
| `cli.py` | CLI entry point for `markcrawl` command | `core.py` |
| `chunker.py` | Text chunking with word-based overlap | None (stdlib only) |
| `extract.py` | LLM-powered field extraction (multi-provider) | `openai` / `anthropic` / `google-genai` |
| `extract_cli.py` | CLI entry point for `markcrawl-extract` | `extract.py` |
| `upload.py` | Chunk + embed + Supabase upload | `openai`, `supabase` |
| `upload_cli.py` | CLI entry point for `markcrawl-upload` | `upload.py` |
| `mcp_server.py` | MCP server exposing tools for AI agents | `mcp`, `core.py`, `extract.py` |

## Extending MarkCrawl

### Use as a Python library

You don't have to use the CLI. Import and call directly:

```python
from markcrawl.core import crawl

result = crawl(
    base_url="https://example.com",
    out_dir="./output",
    fmt="markdown",
    max_pages=50,
    show_progress=True,
)
print(f"Saved {result.pages_saved} pages")
```

### Process crawl output with your own code

```python
import json

with open("./output/pages.jsonl") as f:
    for line in f:
        page = json.loads(line)
        # page["url"], page["title"], page["text"]
        # Feed to your own embedding pipeline, database, etc.
```

### Use the chunker independently

```python
from markcrawl.chunker import chunk_text

chunks = chunk_text(
    "Your long text here...",
    max_words=400,
    overlap_words=50,
)
for chunk in chunks:
    print(f"Chunk {chunk.index}/{chunk.total}: {chunk.text[:80]}...")
```

### Use extraction with your own LLM client

```python
from markcrawl.extract import LLMClient, extract_fields

client = LLMClient(provider="anthropic")
result = extract_fields(
    text="Page content here...",
    fields=["company_name", "pricing"],
    client=client,
)
print(result)  # {"company_name": "Acme", "pricing": "$29/mo"}
```

### Swap output formats

The core crawler writes Markdown or plain text. If you need a different format (HTML, JSON, custom), process the `pages.jsonl` output — each row contains the full extracted text that you can transform however you need.

### Plug in your own storage

The `pages.jsonl` output is a standard newline-delimited JSON file. You can write a simple script to load it into any database, vector store, or search engine:

```python
import json

with open("./output/pages.jsonl") as f:
    for line in f:
        page = json.loads(line)
        # Insert into Pinecone, Weaviate, Elasticsearch, PostgreSQL, etc.
        your_db.insert(page)
```

The built-in Supabase upload (`upload.py`) is one example of this pattern. Use it as a reference for writing your own storage adapter.
