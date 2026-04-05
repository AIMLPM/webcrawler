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

Example prompts:
    1. "Crawl the Stripe API docs and summarize their authentication methods."
    2. "Research competitor1.com and competitor2.com — compare their pricing and features."
    3. "Crawl our company wiki and find all pages mentioning the onboarding process."
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .core import crawl as run_crawl

mcp = FastMCP("markcrawl")

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
    """Crawl a website and save extracted content as clean Markdown or plain text.

    This tool fetches pages from the given URL, strips navigation, footers,
    scripts, and boilerplate, then saves each page as a Markdown file with a
    JSONL index (pages.jsonl). It respects robots.txt and uses sitemap-first
    discovery when available.

    Use this tool when asked to research, read, analyze, or archive a website.
    The output_dir from this tool is required by search_pages, read_page,
    list_pages, and extract_data.

    Typical workflow: crawl_site → list_pages or search_pages → read_page.

    Args:
        url: The base URL to crawl (e.g. "https://docs.example.com/"). Only
            public, non-authenticated pages will be fetched.
        output_dir: Directory to save output files. Each crawl creates .md files
            and a pages.jsonl index here. Default: ./crawl_output
        format: Output format — "markdown" (preserves headings, code blocks,
            lists) or "text" (plain text). Default: "markdown".
        max_pages: Maximum number of pages to save. Set to 0 for unlimited.
            Default: 100. Use lower values (10-20) for quick previews.
        include_subdomains: If True, also crawl subdomains (e.g. docs.example.com
            when crawling example.com). Default: False.
        render_js: If True, use a headless Chromium browser to render JavaScript
            before extracting content. Required for React/Vue/Angular sites.
            Slower but necessary for SPAs. Default: False.
    """
    result = run_crawl(
        base_url=url,
        out_dir=output_dir,
        fmt=format,
        max_pages=max_pages,
        include_subdomains=include_subdomains,
        render_js=render_js,
        delay=0,
        timeout=15,
        show_progress=False,
        min_words=20,
    )

    return (
        f"Crawled {result.pages_saved} page(s) from {url}\n"
        f"Output directory: {result.output_dir}\n"
        f"Index file: {result.index_file}\n"
        f"Use output_dir='{result.output_dir}' with search_pages, read_page, "
        f"list_pages, or extract_data to work with this content."
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
    """Search through previously crawled pages by keyword.

    Performs case-insensitive keyword search across page titles and text content.
    Results are ranked by the number of matching query words found. Each result
    includes the page URL, title, and a text snippet showing context around the
    first match.

    This is a read-only operation on local files — no network requests are made.
    Requires a prior crawl_site call to have populated the pages.jsonl file.

    Args:
        query: Search query — one or more keywords separated by spaces. All words
            are searched independently (OR logic). Example: "authentication API key".
        jsonl_path: Full path to the pages.jsonl file from a previous crawl. If
            empty, defaults to <WEBCRAWLER_OUTPUT_DIR>/pages.jsonl.
        max_results: Maximum number of results to return. Default: 10. Use lower
            values for focused searches, higher for comprehensive surveys.
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
    """Read the full extracted content of a specific crawled page by its URL.

    Returns the complete Markdown or text content of a single page, including
    its title and source URL. Use this after search_pages to read the full
    content of a relevant result.

    This is a read-only operation on local files — no network requests are made.
    URL matching is case-insensitive and tolerates trailing slashes.

    Args:
        url: The exact URL of the page to read. Must match a URL from a previous
            crawl. Case-insensitive. Example: "https://docs.example.com/auth".
        jsonl_path: Full path to the pages.jsonl file. If empty, defaults to
            <WEBCRAWLER_OUTPUT_DIR>/pages.jsonl.
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
    """List all pages from a previous crawl with their URLs, titles, and word counts.

    Returns a summary of every page in the crawl index. Use this to get an
    overview of available content before searching or reading specific pages.
    Word counts help identify content-rich pages vs. thin landing pages.

    This is a read-only operation on local files — no network requests are made.

    Args:
        jsonl_path: Full path to the pages.jsonl file. If empty, defaults to
            <WEBCRAWLER_OUTPUT_DIR>/pages.jsonl.
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

    Analyzes each crawled page and pulls out specific data fields you define
    (e.g. company_name, pricing, features, api_endpoints). If no fields are
    specified, the LLM automatically discovers relevant fields by sampling
    pages from the crawl.

    This tool makes external API calls to OpenAI (requires OPENAI_API_KEY
    environment variable). Results are saved to extracted.jsonl and include
    LLM attribution metadata.

    Use this for competitive research, API documentation analysis, or building
    structured datasets from unstructured web content.

    Args:
        jsonl_path: Full path to the pages.jsonl file. If empty, defaults to
            <WEBCRAWLER_OUTPUT_DIR>/pages.jsonl.
        fields: Comma-separated field names to extract. Example:
            "company_name,pricing,features,api_endpoints". Leave empty to
            let the LLM auto-discover the most relevant fields.
        context: Description of your analysis goal. Improves auto-field
            discovery quality. Example: "competitor pricing analysis" or
            "API documentation review". Ignored when fields are specified.
        sample_size: Number of pages to sample for auto-field discovery.
            Default: 3. Higher values give better field suggestions but
            cost more tokens.
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
        extract_delay=0.25,
    )

    if not results:
        return "No data extracted."

    output_parts = [f"Extracted {len(results)} page(s):\n"]
    for row in results[:20]:
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
