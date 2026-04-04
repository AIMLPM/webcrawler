"""MCP server exposing MarkCrawl tools for AI agents.

Run with:
    python -m markcrawl.mcp_server

Or configure in your MCP client (Claude Desktop, Cursor, etc.):
    {
        "mcpServers": {
            "markcrawl": {
                "command": "python",
                "args": ["-m", "markcrawl.mcp_server"]
            }
        }
    }
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import crawl as run_crawl

mcp = FastMCP(
    "markcrawl",
    description="Website crawler for AI ingestion — crawl sites, search pages, and extract structured data.",
)

DEFAULT_OUTPUT_DIR = os.environ.get("WEBCRAWLER_OUTPUT_DIR", "./crawl_output")


# ---------------------------------------------------------------------------
# Tool: crawl_site
# ---------------------------------------------------------------------------

@mcp.tool()
def crawl_site(
    url: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    format: str = "markdown",
    max_pages: int = 100,
    include_subdomains: bool = False,
    render_js: bool = False,
) -> str:
    """Crawl a website and save extracted content as Markdown or plain text files.

    Returns a summary of what was crawled. The output directory will contain
    individual page files and a pages.jsonl index.

    Args:
        url: The base URL to crawl (e.g. "https://docs.example.com/")
        output_dir: Directory to save output files (default: ./crawl_output)
        format: Output format — "markdown" or "text"
        max_pages: Maximum number of pages to save (default: 100, 0 for unlimited)
        include_subdomains: Whether to include subdomains in the crawl scope
        render_js: Use Playwright to render JavaScript-heavy sites (requires playwright)
    """
    result = run_crawl(
        base_url=url,
        out_dir=output_dir,
        fmt=format,
        max_pages=max_pages,
        include_subdomains=include_subdomains,
        render_js=render_js,
        delay=1.0,
        timeout=15,
        show_progress=False,
        min_words=20,
    )

    return (
        f"Crawled {result.pages_saved} page(s) from {url}\n"
        f"Output directory: {result.output_dir}\n"
        f"Index file: {result.index_file}"
    )


# ---------------------------------------------------------------------------
# Tool: search_pages
# ---------------------------------------------------------------------------

@mcp.tool()
def search_pages(
    query: str,
    jsonl_path: str = "",
    max_results: int = 10,
) -> str:
    """Search through crawled pages by keyword.

    Searches the title and text of all pages in a pages.jsonl file
    and returns matching results ranked by relevance.

    Args:
        query: Search query (case-insensitive keyword search)
        jsonl_path: Path to pages.jsonl (default: <output_dir>/pages.jsonl)
        max_results: Maximum number of results to return (default: 10)
    """
    if not jsonl_path:
        jsonl_path = os.path.join(DEFAULT_OUTPUT_DIR, "pages.jsonl")

    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {jsonl_path}. Run crawl_site first."

    query_lower = query.lower()
    query_words = query_lower.split()
    results = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            text = page.get("text", "").lower()
            title = page.get("title", "").lower()
            searchable = title + " " + text

            # Score by number of query words found
            score = sum(1 for w in query_words if w in searchable)
            if score > 0:
                results.append((score, page))

    if not results:
        return f"No results found for '{query}' in {jsonl_path}"

    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:max_results]

    output_parts = [f"Found {len(results)} result(s) for '{query}':\n"]
    for score, page in results:
        url = page.get("url", "")
        title = page.get("title", "Untitled")
        text = page.get("text", "")
        # Show a snippet around the first match
        snippet = _find_snippet(text, query_words, context_chars=200)
        output_parts.append(f"**{title}**\n{url}\n{snippet}\n")

    return "\n".join(output_parts)


def _find_snippet(text: str, query_words: list, context_chars: int = 200) -> str:
    """Find a text snippet around the first occurrence of any query word."""
    text_lower = text.lower()
    best_pos = len(text)
    for word in query_words:
        pos = text_lower.find(word)
        if pos != -1 and pos < best_pos:
            best_pos = pos

    if best_pos == len(text):
        return text[:context_chars] + "..." if len(text) > context_chars else text

    start = max(0, best_pos - context_chars // 2)
    end = min(len(text), best_pos + context_chars // 2)
    snippet = text[start:end].strip()

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


# ---------------------------------------------------------------------------
# Tool: read_page
# ---------------------------------------------------------------------------

@mcp.tool()
def read_page(
    url: str,
    jsonl_path: str = "",
) -> str:
    """Read the full extracted content of a specific crawled page by URL.

    Args:
        url: The URL of the page to read (must have been previously crawled)
        jsonl_path: Path to pages.jsonl (default: <output_dir>/pages.jsonl)
    """
    if not jsonl_path:
        jsonl_path = os.path.join(DEFAULT_OUTPUT_DIR, "pages.jsonl")

    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {jsonl_path}. Run crawl_site first."

    url_lower = url.lower().rstrip("/")

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            page_url = page.get("url", "").lower().rstrip("/")
            if page_url == url_lower:
                title = page.get("title", "Untitled")
                text = page.get("text", "")
                return f"# {title}\n\nURL: {page.get('url', '')}\n\n{text}"

    return f"Page not found: {url}"


# ---------------------------------------------------------------------------
# Tool: list_pages
# ---------------------------------------------------------------------------

@mcp.tool()
def list_pages(
    jsonl_path: str = "",
) -> str:
    """List all crawled pages with their URLs and titles.

    Args:
        jsonl_path: Path to pages.jsonl (default: <output_dir>/pages.jsonl)
    """
    if not jsonl_path:
        jsonl_path = os.path.join(DEFAULT_OUTPUT_DIR, "pages.jsonl")

    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {jsonl_path}. Run crawl_site first."

    pages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            pages.append(page)

    if not pages:
        return "No pages found."

    lines = [f"**{len(pages)} crawled page(s):**\n"]
    for page in pages:
        title = page.get("title", "Untitled")
        url = page.get("url", "")
        word_count = len(page.get("text", "").split())
        lines.append(f"- {title} ({word_count} words)\n  {url}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: extract_data
# ---------------------------------------------------------------------------

@mcp.tool()
def extract_data(
    jsonl_path: str = "",
    fields: str = "",
    context: str = "",
    sample_size: int = 3,
) -> str:
    """Extract structured fields from crawled pages using an LLM.

    Either specify field names or let the LLM auto-discover them.
    Requires OPENAI_API_KEY environment variable.

    Args:
        jsonl_path: Path to pages.jsonl (default: <output_dir>/pages.jsonl)
        fields: Comma-separated field names to extract (e.g. "company_name,pricing,features"). Leave empty to auto-discover.
        context: Describe your analysis goal to improve field discovery (e.g. "competitor pricing analysis")
        sample_size: Number of pages to sample for auto-field discovery (default: 3)
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return "Error: OPENAI_API_KEY environment variable is required for extraction."

    if not jsonl_path:
        jsonl_path = os.path.join(DEFAULT_OUTPUT_DIR, "pages.jsonl")

    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {jsonl_path}. Run crawl_site first."

    from .extract import extract_from_jsonl

    field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else None
    auto_fields = not field_list

    results = extract_from_jsonl(
        jsonl_paths=[jsonl_path],
        fields=field_list,
        model="gpt-4o-mini",
        show_progress=False,
        auto_fields=auto_fields,
        auto_fields_context=context or None,
        sample_size=sample_size,
    )

    if not results:
        return "No data extracted."

    # Format as readable output
    output_parts = [f"Extracted {len(results)} page(s):\n"]
    for row in results[:20]:  # Limit output to first 20 to avoid overwhelming the agent
        url = row.get("url", "")
        output_parts.append(f"**{url}**")
        for key, value in row.items():
            if key not in ("url", "title", "source_file") and value is not None:
                output_parts.append(f"  {key}: {value}")
        output_parts.append("")

    if len(results) > 20:
        output_parts.append(f"... and {len(results) - 20} more page(s)")

    output_path = str(Path(jsonl_path).parent / "extracted.jsonl")
    output_parts.append(f"\nFull results saved to: {output_path}")

    return "\n".join(output_parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run()


if __name__ == "__main__":
    main()
