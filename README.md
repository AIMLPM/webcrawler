# Website Crawler for AI / RAG Ingestion

A lightweight Python website crawler that extracts clean Markdown or plain text from websites for AI ingestion, RAG pipelines, search indexing, and documentation archiving.

This project starts with a sitemap when available, respects `robots.txt`, keeps crawling in-scope, and writes both page files and a `pages.jsonl` index for downstream processing.

## Why this exists

A lot of crawlers are either too heavyweight for small ingestion jobs or too focused on broad web scraping. This project is intentionally simple:

- crawl a single site or subdomain set
- extract readable content instead of raw HTML
- produce output that is easy to load into embeddings, vector stores, or search pipelines
- stay understandable and hackable for contributors

## Features

- Sitemap-first crawling
- `robots.txt` checks
- Optional subdomain support
- Markdown or plain text output
- Progress logging with a single CLI flag
- Retry and backoff support for transient errors
- Safe filenames with URL hashing
- JSONL index for ingestion workflows
- Basic content cleanup for nav / footer / utility elements
- Built-in text chunking for embeddings
- Supabase / pgvector upload with OpenAI embeddings
- Optional JavaScript rendering via Playwright
- Concurrent page fetching
- Proxy support
- Resume interrupted crawls
- LLM-powered structured extraction

## Project structure

```text
.
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── tests/
│   ├── test_core.py
│   └── test_chunker.py
└── webcrawler/
    ├── __init__.py
    ├── cli.py
    ├── core.py
    ├── chunker.py
    ├── upload.py
    ├── upload_cli.py
    ├── extract.py
    └── extract_cli.py
```

## Installation

### Option 1: Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Install as a local package

```bash
pip install -e .
```

### Option 3: Install with JavaScript rendering support

```bash
pip install -e ".[js]"
playwright install chromium
```

This adds Playwright for rendering JavaScript-heavy sites with `--render-js`.

### Option 4: Install with structured extraction support

```bash
pip install -e ".[extract]"
```

This adds the `openai` package needed for LLM-powered field extraction via `python -m webcrawler.extract_cli`.

### Option 5: Install with Supabase upload support

```bash
pip install -e ".[upload]"
```

This adds the `openai` and `supabase` packages needed for the upload command. After installing this way, you can also run `website-crawler-upload` directly instead of `python -m webcrawler.upload_cli`.

### Option 6: Install everything

```bash
pip install -e ".[all]"
playwright install chromium
```

## Cost

The crawler itself is **completely free** — crawling, text extraction, chunking, resume, JS rendering, and proxy support use no paid APIs.

Only two optional features require an OpenAI API key (and therefore have token costs):

| Feature | When it costs money | Typical cost |
|---|---|---|
| `extract_cli` (structured extraction) | When you use `--fields` to extract structured data via LLM | ~$0.01-0.03 per page with `gpt-4o-mini` |
| `upload_cli` (Supabase upload) | When generating embeddings for vector search | ~$0.0001 per page with `text-embedding-3-small` |

You can use the full crawl pipeline (crawl → chunk → save files) without any API keys or costs.

## Quick start — full pipeline

```bash
# 1. Crawl a site
python -m webcrawler.cli \
  --base https://docs.example.com/ \
  --out ./output \
  --format markdown \
  --show-progress

# 2. Extract structured fields (requires OPENAI_API_KEY env var)
python -m webcrawler.extract_cli \
  --jsonl ./output/pages.jsonl \
  --fields company_name pricing features \
  --show-progress

# 3. Upload to Supabase (requires SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY env vars)
python -m webcrawler.upload_cli \
  --jsonl ./output/pages.jsonl \
  --show-progress
```

## Usage

### Basic crawl

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --format markdown
```

### Show progress output

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --format markdown \
  --show-progress
```

### Include subdomains

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --include-subdomains
```

### Plain text output

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --format text
```

### Crawl a JavaScript-heavy site

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --render-js
```

This launches a headless Chromium browser to fully render each page before extracting content. Use this for React, Angular, Vue, or other SPA-based sites.

### Faster crawling with concurrency

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --concurrency 5 \
  --show-progress
```

Fetches up to 5 pages in parallel. The delay is applied between batches rather than between individual requests.

### Crawl through a proxy

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --proxy http://user:pass@proxy-host:8080
```

Works with both `--render-js` (Playwright) and standard requests.

### Resume an interrupted crawl

```bash
python -m webcrawler.cli \
  --base https://www.WEBSITE-TO-CRAWL.com/ \
  --out ./output \
  --resume \
  --show-progress
```

If a crawl is interrupted (Ctrl+C, crash, or `--max-pages` limit), the crawler saves its state to `.crawl_state.json` in the output directory. Use `--resume` to pick up where it left off without re-fetching pages already saved.

## CLI arguments

| Argument | Description |
|---|---|
| `--base` | Base site URL to crawl |
| `--out` | Output directory |
| `--use-sitemap` | Use sitemap(s) when available |
| `--delay` | Delay between requests in seconds |
| `--timeout` | Per-request timeout in seconds |
| `--max-pages` | Maximum number of pages to save; `0` means unlimited |
| `--include-subdomains` | Include subdomains under the base domain |
| `--format` | `markdown` or `text` |
| `--show-progress` | Print progress and crawl events |
| `--min-words` | Skip pages with very little content |
| `--user-agent` | Override the default user agent |
| `--render-js` | Render JavaScript with Playwright before extracting (requires `.[js]`) |
| `--concurrency` | Number of pages to fetch in parallel (default: `1`) |
| `--proxy` | HTTP/HTTPS proxy URL |
| `--resume` | Resume a previously interrupted crawl from saved state |

## Output

For each page, the crawler writes:

1. a `.md` or `.txt` file with extracted content
2. a `pages.jsonl` index row for downstream ingestion

Example JSONL row:

```json
{
  "url": "https://www.WEBSITE-TO-CRAWL.com/page",
  "title": "Page Title",
  "path": "page__abc123def0.md",
  "text": "Extracted content..."
}
```

Example output tree:

```text
output/
├── index__6dcd4ce23d.md
├── about__9c1185a5c5.md
├── docs-getting-started__0cc175b9c0.md
└── pages.jsonl
```

## Uploading to Supabase for RAG

After crawling, you can chunk the output, generate embeddings, and upload directly to a Supabase table with pgvector for vector search.

### 1. Set up Supabase

In your Supabase project, go to the **SQL Editor** and run:

```sql
-- Enable the pgvector extension (one time per project)
create extension if not exists vector;

-- Create the documents table
create table documents (
  id bigserial primary key,
  url text not null,
  title text,
  chunk_text text not null,
  chunk_index integer not null,
  chunk_total integer not null,
  embedding vector(1536) not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Create an index for fast similarity search
create index on documents using hnsw (embedding vector_cosine_ops);
```

> **Note on dimensions:** The default embedding model (`text-embedding-3-small`) produces 1536-dimensional vectors. If you use a different model, update `vector(1536)` to match.

### 2. Set environment variables

Create a `.env` file in the project root (it is already in `.gitignore` so it won't be committed):

```bash
# .env
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-service-role-key"
OPENAI_API_KEY="your-openai-api-key"
```

Then load it before running the upload:

```bash
source .env
```

Use your **service-role key** (not the anon key) since it bypasses Row Level Security for inserts.

> **Security note:** All credentials are read from environment variables only — they are never accepted as command-line arguments to avoid leaking secrets in shell history or process listings. Never commit your `.env` file to git.

#### Credential management options

| Approach | Security | Complexity | Best for |
|---|---|---|---|
| `.env` file + `.gitignore` | Basic | Low | Local dev, personal projects |
| OS keychain (macOS Keychain, etc.) | Good | Medium | Single-user local tools |
| Secret manager (AWS SSM, GCP Secret Manager, Vault) | High | Higher | Production, teams, CI/CD |

This project uses the `.env` approach. If you deploy this as a service or share it with a team, consider upgrading to a secret manager.

### 3. Run the upload

```bash
python -m webcrawler.upload_cli \
  --jsonl ./output/pages.jsonl \
  --show-progress
```

### Upload CLI arguments

| Argument | Description |
|---|---|
| `--jsonl` | Path to `pages.jsonl` from the crawler |
| `--table` | Target table name (default: `documents`) |
| `--max-words` | Max words per chunk (default: `400`) |
| `--overlap-words` | Overlap words between chunks (default: `50`) |
| `--embedding-model` | OpenAI embedding model (default: `text-embedding-3-small`) |
| `--show-progress` | Print progress during upload |

| Environment variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL (required) |
| `SUPABASE_KEY` | Supabase service-role key (required) |
| `OPENAI_API_KEY` | OpenAI API key for embeddings (required) |

### 4. Query with vector search

Once uploaded, you can find relevant chunks using cosine similarity:

```sql
-- Replace the array with your query's embedding vector
select
  url,
  title,
  chunk_text,
  1 - (embedding <=> '[0.012, -0.003, ...]') as similarity
from documents
order by embedding <=> '[0.012, -0.003, ...]'
limit 5;
```

In practice, you would generate the query embedding in your application code:

```python
import os
import openai
from supabase import create_client

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
client = openai.OpenAI()  # uses OPENAI_API_KEY env var

# Embed the user's question
query = "How do I set up authentication?"
response = client.embeddings.create(input=[query], model="text-embedding-3-small")
query_embedding = response.data[0].embedding

# Search for the most relevant chunks
result = supabase.rpc(
    "match_documents",
    {"query_embedding": query_embedding, "match_count": 5},
).execute()

for row in result.data:
    print(f"{row['similarity']:.3f}  {row['url']}")
    print(f"  {row['chunk_text'][:120]}...\n")
```

To use the `match_documents` RPC, create this function in Supabase:

```sql
create or replace function match_documents(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id bigint,
  url text,
  title text,
  chunk_text text,
  similarity float
)
language sql stable
as $$
  select
    id,
    url,
    title,
    chunk_text,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  order by embedding <=> query_embedding
  limit match_count;
$$;
```

### Supabase recommendations

- **HNSW index**: The `create index ... using hnsw` statement above creates an approximate nearest-neighbor index. This is much faster than exact search for tables with more than a few thousand rows. ([Supabase HNSW docs](https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes))
- **Service-role key**: Use the service-role key for bulk inserts. For user-facing queries, use the anon key with Row Level Security enabled.
- **Embedding model**: `text-embedding-3-small` is a good balance of cost and quality. For higher accuracy, use `text-embedding-3-large` (3072 dimensions — update the `vector()` size accordingly). ([OpenAI embeddings guide](https://platform.openai.com/docs/guides/embeddings))
- **Chunk size**: The default 400 words with 50-word overlap works well for most documentation. Decrease for short-form content, increase for long technical documents.
- **pgvector reference**: The `<=>` operator is cosine distance (lower = more similar). See the [pgvector documentation](https://github.com/pgvector/pgvector) for all available distance operators.

> These recommendations were verified against official documentation as of April 2026.

## Structured extraction with LLM

After crawling, you can use an LLM to extract specific fields from each page — useful for competitive research, API documentation analysis, or building structured datasets.

### Example: Extract company info from competitor sites

```bash
python -m webcrawler.extract_cli \
  --jsonl ./output/pages.jsonl \
  --fields company_name pricing features target_audience \
  --show-progress
```

### Example: Extract API details from documentation

```bash
python -m webcrawler.extract_cli \
  --jsonl ./output/pages.jsonl \
  --fields api_endpoint http_method parameters response_format authentication \
  --model gpt-4o-mini \
  --show-progress
```

This produces an `extracted.jsonl` file with structured data:

```json
{
  "url": "https://docs.example.com/api/users",
  "title": "Users API",
  "api_endpoint": "/api/v1/users",
  "http_method": "GET, POST",
  "parameters": "id, name, email, role",
  "response_format": "JSON",
  "authentication": "Bearer token in Authorization header"
}
```

### Extraction CLI arguments

| Argument | Description |
|---|---|
| `--jsonl` | Path to `pages.jsonl` from the crawler |
| `--fields` | Field names to extract (space-separated) |
| `--output` | Output JSONL path (default: `extracted.jsonl` in same directory) |
| `--model` | OpenAI model for extraction (default: `gpt-4o-mini`) |
| `--show-progress` | Print progress during extraction |

| Environment variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (required) |

### Tips

- Use descriptive field names — the LLM uses them to understand what to look for
- `gpt-4o-mini` is fast and cheap for most extraction tasks; use `gpt-4o` for complex pages
- Each page sends up to 8,000 characters to the LLM to stay within reasonable token limits

## Good fit for

- RAG ingestion
- knowledge base extraction
- internal site archiving
- documentation indexing
- competitor or market research on public pages

## Not currently designed for

- authenticated crawling
- PDF extraction
- anti-bot evasion

## Open-source roadmap

- [ ] Package publishing
- [x] Automated tests
- [x] GitHub Actions CI
- [ ] Canonical URL support
- [ ] Duplicate-content detection
- [x] Optional chunking for embeddings
- [x] Supabase / pgvector upload
- [x] Browser-rendered page mode (Playwright)
- [x] Concurrent fetching
- [x] Proxy support
- [x] Resume interrupted crawls
- [x] LLM-powered structured extraction
- [ ] PDF support

## Legal and ethical use

Use this tool responsibly.

- Respect `robots.txt`, site terms, and rate limits.
- Only crawl content you are authorized to access.
- Do not use this project to evade access controls or scrape private content.
- You are responsible for complying with the target site's policies and applicable laws.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Security

If you discover a security issue, please follow the instructions in [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
