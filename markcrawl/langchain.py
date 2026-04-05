"""LangChain tool wrappers for MarkCrawl.

Provides ready-to-use LangChain ``StructuredTool`` instances that can be
plugged directly into agents, chains, or RAG pipelines.

Usage::

    from markcrawl.langchain import crawl_tool, search_tool, read_tool

    # Use in a LangChain agent
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = initialize_agent(
        tools=[crawl_tool, search_tool, read_tool],
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    )
    agent.run("Crawl docs.example.com and find their authentication guide")
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class CrawlInput(BaseModel):
    url: str = Field(description="The base URL to crawl (e.g. 'https://docs.example.com')")
    max_pages: int = Field(default=100, description="Maximum number of pages to crawl")
    output_dir: Optional[str] = Field(default=None, description="Output directory (auto-generated if not provided)")
    include_subdomains: bool = Field(default=False, description="Include subdomains in crawl scope")
    render_js: bool = Field(default=False, description="Render JavaScript before extracting (for React/Vue sites)")


class SearchInput(BaseModel):
    query: str = Field(description="Search query (keywords to find in crawled pages)")
    output_dir: str = Field(description="Path to the crawl output directory")
    max_results: int = Field(default=10, description="Maximum number of results to return")


class ReadPageInput(BaseModel):
    url: str = Field(description="URL of the page to read (must have been previously crawled)")
    output_dir: str = Field(description="Path to the crawl output directory")


class ListPagesInput(BaseModel):
    output_dir: str = Field(description="Path to the crawl output directory")


class ExtractInput(BaseModel):
    output_dir: str = Field(description="Path to the crawl output directory")
    fields: str = Field(description="Comma-separated field names to extract (e.g. 'company_name,pricing,features'). Leave empty to auto-discover.")
    context: Optional[str] = Field(default=None, description="Analysis goal for auto-field discovery (e.g. 'competitor pricing analysis')")
    provider: str = Field(default="openai", description="LLM provider: openai, anthropic, gemini, or grok")


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def _crawl(
    url: str,
    max_pages: int = 100,
    output_dir: Optional[str] = None,
    include_subdomains: bool = False,
    render_js: bool = False,
) -> str:
    """Crawl a website and extract clean Markdown."""
    from .core import crawl

    if not output_dir:
        slug = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
        output_dir = os.path.join(tempfile.gettempdir(), f"markcrawl_{slug}")

    result = crawl(
        base_url=url,
        out_dir=output_dir,
        fmt="markdown",
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
        f"Use this output_dir for search_pages, read_page, and extract_data tools."
    )


def _search(query: str, output_dir: str, max_results: int = 10) -> str:
    """Search through crawled pages by keyword."""
    jsonl_path = os.path.join(output_dir, "pages.jsonl")
    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {output_dir}. Run crawl_site first."

    query_lower = query.lower()
    query_words = query_lower.split()
    results = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            searchable = (page.get("title", "") + " " + page.get("text", "")).lower()
            score = sum(1 for w in query_words if w in searchable)
            if score > 0:
                text = page.get("text", "")
                # Snippet around first match
                text_lower = text.lower()
                pos = len(text)
                for w in query_words:
                    p = text_lower.find(w)
                    if p != -1 and p < pos:
                        pos = p
                start = max(0, pos - 100)
                end = min(len(text), pos + 200)
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet += "..."

                results.append((score, page.get("url", ""), page.get("title", ""), snippet))

    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:max_results]

    if not results:
        return f"No results found for '{query}'"

    lines = [f"Found {len(results)} result(s) for '{query}':\n"]
    for score, url, title, snippet in results:
        lines.append(f"**{title}** ({url})\n{snippet}\n")
    return "\n".join(lines)


def _read_page(url: str, output_dir: str) -> str:
    """Read the full content of a crawled page."""
    jsonl_path = os.path.join(output_dir, "pages.jsonl")
    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {output_dir}. Run crawl_site first."

    url_lower = url.lower().rstrip("/")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            if page.get("url", "").lower().rstrip("/") == url_lower:
                title = page.get("title", "Untitled")
                text = page.get("text", "")
                return f"# {title}\n\nURL: {page.get('url', '')}\n\n{text}"

    return f"Page not found: {url}"


def _list_pages(output_dir: str) -> str:
    """List all crawled pages."""
    jsonl_path = os.path.join(output_dir, "pages.jsonl")
    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {output_dir}. Run crawl_site first."

    pages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            word_count = len(page.get("text", "").split())
            pages.append(f"- {page.get('title', 'Untitled')} ({word_count} words)\n  {page.get('url', '')}")

    if not pages:
        return "No pages found."

    return f"**{len(pages)} crawled page(s):**\n\n" + "\n".join(pages)


def _extract(
    output_dir: str,
    fields: str = "",
    context: Optional[str] = None,
    provider: str = "openai",
) -> str:
    """Extract structured fields from crawled pages using an LLM."""
    jsonl_path = os.path.join(output_dir, "pages.jsonl")
    if not os.path.isfile(jsonl_path):
        return f"No crawl data found at {output_dir}. Run crawl_site first."

    from .extract import extract_from_jsonl

    field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else None
    auto_fields = not field_list

    results = extract_from_jsonl(
        jsonl_paths=[jsonl_path],
        fields=field_list,
        show_progress=False,
        auto_fields=auto_fields,
        auto_fields_context=context,
        provider=provider,
    )

    if not results:
        return "No data extracted."

    lines = [f"Extracted {len(results)} page(s):\n"]
    for row in results[:20]:
        url = row.get("url", "")
        lines.append(f"**{url}**")
        for key, value in row.items():
            if key not in ("url", "title", "source_file") and value is not None:
                lines.append(f"  {key}: {value}")
        lines.append("")

    if len(results) > 20:
        lines.append(f"... and {len(results) - 20} more page(s)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Exported tools
# ---------------------------------------------------------------------------

crawl_tool = StructuredTool.from_function(
    func=_crawl,
    name="crawl_site",
    description=(
        "Crawl a website and extract clean Markdown content. "
        "Returns the output directory path needed for search, read, and extract tools. "
        "Use this when asked to research, analyze, or read a website."
    ),
    args_schema=CrawlInput,
)

search_tool = StructuredTool.from_function(
    func=_search,
    name="search_pages",
    description=(
        "Search through previously crawled pages by keyword. "
        "Returns matching pages with text snippets. "
        "Requires output_dir from a previous crawl_site call."
    ),
    args_schema=SearchInput,
)

read_tool = StructuredTool.from_function(
    func=_read_page,
    name="read_page",
    description=(
        "Read the full Markdown content of a specific crawled page by URL. "
        "Use after search_pages to get the complete text of a relevant page. "
        "Requires output_dir from a previous crawl_site call."
    ),
    args_schema=ReadPageInput,
)

list_tool = StructuredTool.from_function(
    func=_list_pages,
    name="list_pages",
    description=(
        "List all pages from a previous crawl with titles and word counts. "
        "Use to see what content is available before searching. "
        "Requires output_dir from a previous crawl_site call."
    ),
    args_schema=ListPagesInput,
)

extract_tool = StructuredTool.from_function(
    func=_extract,
    name="extract_data",
    description=(
        "Extract structured fields from crawled pages using an LLM. "
        "Specify fields as comma-separated names (e.g. 'company_name,pricing') "
        "or leave empty to auto-discover. Requires OPENAI_API_KEY (or matching provider key). "
        "Requires output_dir from a previous crawl_site call."
    ),
    args_schema=ExtractInput,
)

# Convenience list of all tools
all_tools = [crawl_tool, search_tool, read_tool, list_tool, extract_tool]
