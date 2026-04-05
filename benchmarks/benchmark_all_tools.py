#!/usr/bin/env python3
"""Head-to-head benchmark: MarkCrawl vs Crawl4AI vs Scrapy+markdownify.

Runs all available tools against the same sites with equivalent settings,
measuring performance, extraction quality, and output characteristics.

FireCrawl runs if FIRECRAWL_API_KEY or FIRECRAWL_API_URL is set. The script
auto-loads .env from the project root, so no manual `source .env` is needed.

Usage:
    python benchmarks/benchmark_all_tools.py
    python benchmarks/benchmark_all_tools.py --sites quotes-toscrape,fastapi-docs
    python benchmarks/benchmark_all_tools.py --iterations 1 --skip-warmup  # quick test
    python benchmarks/benchmark_all_tools.py --output benchmarks/SPEED_COMPARISON.md

See benchmarks/METHODOLOGY.md for the methodology.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from project root if present (so FIRECRAWL_API_KEY etc. are available
# without needing to `source .env` manually before running)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPARISON_SITES = {
    "quotes-toscrape": {
        "url": "http://quotes.toscrape.com",
        "max_pages": 15,
        "description": "Paginated quotes (simple HTML, link-following)",
    },
    "books-toscrape": {
        "url": "http://books.toscrape.com",
        "max_pages": 60,
        "description": "E-commerce catalog (60 pages, pagination)",
    },
    "fastapi-docs": {
        "url": "https://fastapi.tiangolo.com",
        "max_pages": 25,
        "description": "API documentation (code blocks, headings, tutorials)",
    },
    "python-docs": {
        "url": "https://docs.python.org/3/library/",
        "max_pages": 20,
        "description": "Python standard library docs",
    },
}


# ---------------------------------------------------------------------------
# Memory tracker (shared)
# ---------------------------------------------------------------------------

def _get_memory_mb() -> float:
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)
        return usage / 1024


class MemoryTracker:
    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.peak_mb: float = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.peak_mb = _get_memory_mb()
        self._running = True
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        return self.peak_mb

    def _sample(self):
        while self._running:
            current = _get_memory_mb()
            if current > self.peak_mb:
                self.peak_mb = current
            time.sleep(self.interval)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    tool: str
    site: str
    pages: int
    time_seconds: float
    pages_per_second: float
    output_kb: float
    peak_memory_mb: float
    avg_words: float
    error: Optional[str] = None


@dataclass
class ToolSiteResult:
    """Aggregated results across iterations for one tool on one site."""
    tool: str
    site: str
    description: str
    pages_median: float
    time_median: float
    time_stddev: float
    pps_median: float
    output_kb: float
    peak_memory_mb: float
    avg_words: float
    runs: List[RunResult] = field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool availability checks
# ---------------------------------------------------------------------------

def check_markcrawl() -> bool:
    try:
        from markcrawl.core import crawl  # noqa: F401
        return True
    except ImportError:
        return False


def check_crawl4ai() -> bool:
    try:
        import crawl4ai  # noqa: F401
        return True
    except ImportError:
        return False


def check_scrapy() -> bool:
    try:
        import markdownify  # noqa: F401
        import scrapy  # noqa: F401
        return True
    except ImportError:
        return False


def check_firecrawl() -> bool:
    """Check if FireCrawl is available.

    FireCrawl requires either:
    - FIRECRAWL_API_KEY env var (uses their SaaS API — free tier available)
    - FIRECRAWL_API_URL env var (self-hosted via docker-compose)

    Note: FireCrawl self-hosting requires docker-compose with multiple services
    (API, worker, Redis). It cannot be run as a single Docker container.
    """
    try:
        import firecrawl  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("FIRECRAWL_API_KEY") or os.environ.get("FIRECRAWL_API_URL"))


# ---------------------------------------------------------------------------
# URL discovery — run once, then feed identical URLs to all tools
# ---------------------------------------------------------------------------

def discover_urls(url: str, max_pages: int) -> List[str]:
    """Use MarkCrawl to discover URLs, then return the list for all tools."""
    from markcrawl.core import crawl

    tmp_dir = tempfile.mkdtemp(prefix="mc_discover_")
    crawl(
        base_url=url,
        out_dir=tmp_dir,
        fmt="markdown",
        max_pages=max_pages,
        delay=0,
        timeout=15,
        show_progress=False,
        min_words=5,
    )

    urls = []
    jsonl_path = os.path.join(tmp_dir, "pages.jsonl")
    if os.path.isfile(jsonl_path):
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    page = json.loads(line)
                    if page.get("url"):
                        urls.append(page["url"])

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return urls


# ---------------------------------------------------------------------------
# Tool runners — fixed URL list mode (identical pages for all tools)
# ---------------------------------------------------------------------------

def run_markcrawl(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run MarkCrawl and return pages saved."""
    from markcrawl.core import crawl

    if url_list:
        # Fetch specific URLs using the crawl engine directly
        from markcrawl.core import (
            CrawlEngine,
        )

        os.makedirs(out_dir, exist_ok=True)
        engine = CrawlEngine(
            out_dir=out_dir, fmt="markdown", min_words=5, delay=0,
            timeout=15, concurrency=1, include_subdomains=False,
            user_agent=None, render_js=False, proxy=None, show_progress=False,
        )
        jsonl_path = os.path.join(out_dir, "pages.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            for page_url in url_list:
                resp = engine.fetch_page(page_url)
                page_data = engine.process_response(page_url, resp)
                if page_data:
                    engine.save_page(page_data, jsonl_file)
        engine.close()
        return engine.saved_count
    else:
        result = crawl(
            base_url=url,
            out_dir=out_dir,
            fmt="markdown",
            max_pages=max_pages,
            delay=0,
            timeout=15,
            show_progress=False,
            min_words=5,
        )
        return result.pages_saved


def run_crawl4ai(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run Crawl4AI and return pages saved."""
    import asyncio

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    os.makedirs(out_dir, exist_ok=True)
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    # If url_list provided, fetch those specific URLs (no discovery)
    urls_to_fetch = url_list if url_list else None

    async def _crawl():
        nonlocal pages_saved
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            if urls_to_fetch:
                # Fixed URL list mode — fetch exact URLs
                for page_url in urls_to_fetch:
                    try:
                        result = await crawler.arun(url=page_url, config=run_config)
                        if not result.success or not result.markdown:
                            continue
                        _write_output(out_dir, jsonl_path, page_url, result)
                        pages_saved += 1
                    except Exception:
                        continue
            else:
                # Discovery mode — follow links
                visited = set()
                to_visit = [url]
                while to_visit and pages_saved < max_pages:
                    current_url = to_visit.pop(0)
                    if current_url in visited:
                        continue
                    visited.add(current_url)
                    try:
                        result = await crawler.arun(url=current_url, config=run_config)
                        if not result.success or not result.markdown:
                            continue
                        _write_output(out_dir, jsonl_path, current_url, result)
                        pages_saved += 1
                        if hasattr(result, "links") and result.links:
                            base_domain = url.split("//")[-1].split("/")[0]
                            for link_info in result.links.get("internal", []):
                                link = link_info.get("href", "") if isinstance(link_info, dict) else str(link_info)
                                if link and link not in visited and base_domain in link:
                                    to_visit.append(link)
                    except Exception:
                        continue

    def _write_output(out_dir, jsonl_path, page_url, result):
        safe_name = page_url.replace("://", "_").replace("/", "_")[:80]
        md_path = os.path.join(out_dir, f"{safe_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.markdown)
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "url": page_url,
                "title": result.metadata.get("title", "") if result.metadata else "",
                "text": result.markdown,
            }, ensure_ascii=False) + "\n")

    asyncio.run(_crawl())
    return pages_saved


def run_scrapy_markdownify(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run Scrapy with markdownify pipeline via subprocess."""
    os.makedirs(out_dir, exist_ok=True)

    if url_list:
        # Fixed URL list mode — no link following
        url_list_json = json.dumps(url_list)
        spider_code = f'''
import json
import os
import scrapy
from markdownify import markdownify as md
from scrapy.crawler import CrawlerProcess

class BenchSpider(scrapy.Spider):
    name = "bench"
    start_urls = {url_list_json}
    custom_settings = {{
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 0,
    }}

    def parse(self, response):
        body = response.css("main").get() or response.css("body").get() or response.text
        markdown = md(body, heading_style="ATX", strip=["img", "script", "style", "nav", "footer"])
        title = response.css("title::text").get() or ""
        if len(markdown.split()) < 5:
            return
        safe_name = response.url.replace("://", "_").replace("/", "_")[:80]
        md_path = os.path.join("{out_dir}", f"{{safe_name}}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        jsonl_path = os.path.join("{out_dir}", "pages.jsonl")
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({{
                "url": response.url,
                "title": title.strip(),
                "text": markdown,
            }}, ensure_ascii=False) + "\\n")

process = CrawlerProcess()
process.crawl(BenchSpider)
process.start()
'''
    else:
        # Discovery mode — follow links
        spider_code = f'''
import json
import os
import scrapy
from markdownify import markdownify as md
from scrapy.crawler import CrawlerProcess
from urllib.parse import urlparse

class BenchSpider(scrapy.Spider):
    name = "bench"
    start_urls = ["{url}"]
    custom_settings = {{
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 0,
        "CLOSESPIDER_PAGECOUNT": {max_pages},
    }}
    pages_saved = 0

    def parse(self, response):
        if self.pages_saved >= {max_pages}:
            return
        body = response.css("main").get() or response.css("body").get() or response.text
        markdown = md(body, heading_style="ATX", strip=["img", "script", "style", "nav", "footer"])
        title = response.css("title::text").get() or ""
        if len(markdown.split()) < 5:
            return
        safe_name = response.url.replace("://", "_").replace("/", "_")[:80]
        md_path = os.path.join("{out_dir}", f"{{safe_name}}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        jsonl_path = os.path.join("{out_dir}", "pages.jsonl")
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({{
                "url": response.url,
                "title": title.strip(),
                "text": markdown,
            }}, ensure_ascii=False) + "\\n")
        self.pages_saved += 1
        base_domain = urlparse("{url}").netloc
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if urlparse(full_url).netloc == base_domain:
                yield scrapy.Request(full_url, callback=self.parse)

process = CrawlerProcess()
process.crawl(BenchSpider)
process.start()
'''

    spider_file = os.path.join(out_dir, "_spider.py")
    with open(spider_file, "w") as f:
        f.write(spider_code)

    subprocess.run(
        [sys.executable, spider_file],
        capture_output=True,
        timeout=300,
        check=False,
    )

    # Count pages
    jsonl_path = os.path.join(out_dir, "pages.jsonl")
    if os.path.isfile(jsonl_path):
        with open(jsonl_path) as f:
            return sum(1 for line in f if line.strip())
    return 0


def run_firecrawl(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run FireCrawl and return pages saved.

    Uses SaaS API (FIRECRAWL_API_KEY) or self-hosted (FIRECRAWL_API_URL).
    Note: SaaS API includes network latency to their servers.

    Requires firecrawl-py >= 4.x (v2 API): crawl() replaces crawl_url(),
    response is a CrawlJob object with .data list of Document objects.
    """
    from firecrawl import FirecrawlApp
    from firecrawl.v2.types import ScrapeOptions

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    api_url = os.environ.get("FIRECRAWL_API_URL")

    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if api_url:
        kwargs["api_url"] = api_url
    app = FirecrawlApp(**kwargs)

    os.makedirs(out_dir, exist_ok=True)
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    result = app.crawl(
        url,
        limit=max_pages,
        scrape_options=ScrapeOptions(formats=["markdown"]),
    )

    pages_saved = 0
    data = getattr(result, "data", []) or []
    for page in data:
        markdown = getattr(page, "markdown", "") or ""
        meta = getattr(page, "metadata", None)
        page_url = getattr(meta, "source_url", "") or getattr(meta, "url", "") or ""
        title = getattr(meta, "title", "") or ""

        if not markdown or len(markdown.split()) < 5:
            continue

        safe_name = page_url.replace("://", "_").replace("/", "_")[:80]
        md_path = os.path.join(out_dir, f"{safe_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "url": page_url,
                "title": title,
                "text": markdown,
            }, ensure_ascii=False) + "\n")
        pages_saved += 1

    return pages_saved


def check_crawlee() -> bool:
    try:
        import crawlee  # noqa: F401
        return True
    except ImportError:
        return False


def check_colly() -> bool:
    colly_bin = os.path.join(os.path.dirname(__file__), "colly_crawler", "colly_crawler")
    return os.path.isfile(colly_bin)


def check_playwright_raw() -> bool:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        return False


def run_crawlee(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run Crawlee (Python) with Playwright and return pages saved."""
    import asyncio

    from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

    os.makedirs(out_dir, exist_ok=True)
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")
    urls_to_visit = url_list if url_list else [url]

    async def _run():
        nonlocal pages_saved
        crawler = PlaywrightCrawler(max_requests_per_crawl=max_pages, headless=True)

        @crawler.router.default_handler
        async def handler(context: PlaywrightCrawlingContext) -> None:
            nonlocal pages_saved
            if pages_saved >= max_pages:
                return

            page_url = context.request.url
            title = await context.page.title()
            content = await context.page.content()

            # Convert to markdown using markdownify
            from markdownify import markdownify as md
            markdown = md(content, heading_style="ATX", strip=["img", "script", "style", "nav", "footer"])

            if len(markdown.split()) < 5:
                return

            safe_name = page_url.replace("://", "_").replace("/", "_")[:80]
            md_path = os.path.join(out_dir, f"{safe_name}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown)

            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "url": page_url,
                    "title": title,
                    "text": markdown,
                }, ensure_ascii=False) + "\n")

            pages_saved += 1

            if not url_list:
                await context.enqueue_links()

        await crawler.run(urls_to_visit)

    asyncio.run(_run())
    return pages_saved


def run_colly_markdownify(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Run Colly (Go) for fetching + Python markdownify for conversion."""
    os.makedirs(out_dir, exist_ok=True)

    colly_bin = os.path.join(os.path.dirname(__file__), "colly_crawler", "colly_crawler")
    html_dir = os.path.join(out_dir, "_html")
    os.makedirs(html_dir, exist_ok=True)

    cmd = [colly_bin, "-url", url, "-out", html_dir, "-max", str(max_pages)]

    if url_list:
        urls_file = os.path.join(out_dir, "_urls.txt")
        with open(urls_file, "w") as f:
            f.write("\n".join(url_list))
        cmd.extend(["-urls", urls_file])

    subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)

    # Convert HTML files to Markdown using markdownify
    from markdownify import markdownify as md

    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    for html_file in sorted(Path(html_dir).glob("*.html")):
        html_content = html_file.read_text(encoding="utf-8", errors="ignore")
        markdown = md(html_content, heading_style="ATX", strip=["img", "script", "style", "nav", "footer"])

        if len(markdown.split()) < 5:
            continue

        md_path = os.path.join(out_dir, html_file.stem + ".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Reconstruct URL from filename (http_example.com_path → http://example.com/path)
        stem = html_file.stem
        if stem.startswith("https_"):
            page_url = "https://" + stem[6:].replace("_", "/")
        elif stem.startswith("http_"):
            page_url = "http://" + stem[5:].replace("_", "/")
        else:
            page_url = stem.replace("_", "/")
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "url": page_url,
                "title": "",
                "text": markdown,
            }, ensure_ascii=False) + "\n")

        pages_saved += 1

    return pages_saved


def run_playwright_raw(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None) -> int:
    """Raw Playwright baseline — browser fetch + markdownify, no framework overhead."""
    from playwright.sync_api import sync_playwright

    os.makedirs(out_dir, exist_ok=True)
    urls_to_fetch = url_list if url_list else [url]
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    from markdownify import markdownify as md

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for page_url in urls_to_fetch[:max_pages]:
            try:
                context = browser.new_context()
                page = context.new_page()
                page.goto(page_url, timeout=15000, wait_until="networkidle")
                html = page.content()
                title = page.title()
                context.close()
            except Exception:
                continue

            markdown = md(html, heading_style="ATX", strip=["img", "script", "style", "nav", "footer"])
            if len(markdown.split()) < 5:
                continue

            safe_name = page_url.replace("://", "_").replace("/", "_")[:80]
            md_path = os.path.join(out_dir, f"{safe_name}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown)

            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "url": page_url,
                    "title": title,
                    "text": markdown,
                }, ensure_ascii=False) + "\n")

            pages_saved += 1

        browser.close()

    return pages_saved


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

TOOLS = {
    "markcrawl": {"check": check_markcrawl, "run": run_markcrawl},
    "crawl4ai": {"check": check_crawl4ai, "run": run_crawl4ai},
    "scrapy+md": {"check": check_scrapy, "run": run_scrapy_markdownify},
    "crawlee": {"check": check_crawlee, "run": run_crawlee},
    "colly+md": {"check": check_colly, "run": run_colly_markdownify},
    "playwright": {"check": check_playwright_raw, "run": run_playwright_raw},
    "firecrawl": {"check": check_firecrawl, "run": run_firecrawl},
}


def analyze_output(out_dir: str) -> dict:
    """Analyze Markdown output quality."""
    total_words = 0
    total_bytes = 0
    page_count = 0

    for f in Path(out_dir).glob("*.md"):
        content = f.read_text(encoding="utf-8", errors="ignore")
        total_words += len(content.split())
        total_bytes += f.stat().st_size
        page_count += 1

    return {
        "avg_words": total_words / page_count if page_count else 0,
        "output_kb": total_bytes / 1024,
    }


def run_single(
    tool_name: str,
    run_fn: Callable,
    site_name: str,
    site_config: dict,
    base_dir: str,
    url_list: Optional[List[str]] = None,
) -> RunResult:
    """Run a single tool on a single site and return results."""
    out_dir = os.path.join(base_dir, tool_name, site_name)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    url = site_config["url"]
    max_pages = site_config["max_pages"]

    mem = MemoryTracker()
    mem.start()
    start = time.time()

    try:
        pages = run_fn(url, out_dir, max_pages, url_list=url_list)
        error = None
    except Exception as exc:
        pages = 0
        error = str(exc)

    elapsed = time.time() - start
    peak_mem = mem.stop()

    analysis = analyze_output(out_dir)

    return RunResult(
        tool=tool_name,
        site=site_name,
        pages=pages,
        time_seconds=elapsed,
        pages_per_second=pages / elapsed if elapsed > 0 else 0,
        output_kb=analysis["output_kb"],
        peak_memory_mb=peak_mem,
        avg_words=analysis["avg_words"],
        error=error,
    )


def aggregate_runs(runs: List[RunResult], site_config: dict) -> ToolSiteResult:
    """Aggregate multiple iterations into median + stddev."""
    if not runs:
        return ToolSiteResult(
            tool="", site="", description="", pages_median=0,
            time_median=0, time_stddev=0, pps_median=0,
            output_kb=0, peak_memory_mb=0, avg_words=0,
        )

    successful = [r for r in runs if r.error is None]
    if not successful:
        return ToolSiteResult(
            tool=runs[0].tool,
            site=runs[0].site,
            description=site_config["description"],
            pages_median=0, time_median=0, time_stddev=0, pps_median=0,
            output_kb=0, peak_memory_mb=0, avg_words=0,
            runs=runs,
            error=runs[0].error,
        )

    times = [r.time_seconds for r in successful]
    return ToolSiteResult(
        tool=runs[0].tool,
        site=runs[0].site,
        description=site_config["description"],
        pages_median=statistics.median([r.pages for r in successful]),
        time_median=statistics.median(times),
        time_stddev=statistics.stdev(times) if len(times) > 1 else 0,
        pps_median=statistics.median([r.pages_per_second for r in successful]),
        output_kb=statistics.median([r.output_kb for r in successful]),
        peak_memory_mb=max(r.peak_memory_mb for r in successful),
        avg_words=statistics.median([r.avg_words for r in successful]),
        runs=runs,
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_comparison_report(
    results: dict[str, dict[str, ToolSiteResult]],
    available_tools: list[str],
    output_path: str,
):
    """Generate SPEED_COMPARISON.md report."""
    lines = [
        "# MarkCrawl Head-to-Head Comparison",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
        "## Methodology",
        "",
        "**Two-phase approach** for a fair comparison:",
        "",
        "1. **URL Discovery** — MarkCrawl crawls each site once to build a URL list",
        "2. **Benchmarking** — All tools fetch the **identical URLs** (no discovery, pure fetch+convert speed)",
        "",
        "Settings:",
        "- **Delay:** 0 (no politeness throttle)",
        "- **Concurrency:** 1 (sequential, single-thread comparison)",
        "- **Iterations:** 3 per tool per site (reporting median + std dev)",
        "- **Warm-up:** 1 throwaway run per site before timing",
        "- **Output:** Markdown files + JSONL index",
        "- **URL list:** Identical for all tools (discovered in Phase 1)",
        "",
        "See [METHODOLOGY.md](METHODOLOGY.md) for full methodology.",
        "",
        "## Tools tested",
        "",
        "| Tool | Available | Notes |",
        "|---|---|---|",
    ]

    all_tools = ["markcrawl", "crawl4ai", "scrapy+md", "crawlee", "colly+md", "playwright", "firecrawl"]
    for tool in all_tools:
        available = tool in available_tools
        notes = {
            "markcrawl": "requests + BeautifulSoup + markdownify — [AIMLPM/markcrawl](https://github.com/AIMLPM/markcrawl)",
            "crawl4ai": "Playwright + built-in extraction — [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)",
            "scrapy+md": "Scrapy async + markdownify — [scrapy/scrapy](https://github.com/scrapy/scrapy)",
            "crawlee": "Playwright + markdownify — [apify/crawlee-python](https://github.com/apify/crawlee-python)",
            "colly+md": "Go fetch (Colly) + Python markdownify — [gocolly/colly](https://github.com/gocolly/colly)",
            "playwright": "Raw Playwright baseline + markdownify (no framework)",
            "firecrawl": "Self-hosted Docker — [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)",
        }
        status = "Yes" if available else "Not installed"
        lines.append(f"| {tool} | {status} | {notes.get(tool, '')} |")

    lines.extend(["", "## Results by site", ""])

    for site_name, site_config in COMPARISON_SITES.items():
        lines.extend([
            f"### {site_name} — {site_config['description']}",
            "",
            f"Max pages: {site_config['max_pages']}",
            "",
            "| Tool | Pages | Time (s) | Std dev | Pages/sec | Avg words | Output KB | Peak MB |",
            "|---|---|---|---|---|---|---|---|",
        ])

        for tool in available_tools:
            r = results.get(tool, {}).get(site_name)
            if r and not r.error:
                lines.append(
                    f"| {tool} | {r.pages_median:.0f} | {r.time_median:.1f} | "
                    f"±{r.time_stddev:.1f} | {r.pps_median:.1f} | "
                    f"{r.avg_words:.0f} | {r.output_kb:.0f} | {r.peak_memory_mb:.0f} |"
                )
            elif r and r.error:
                lines.append(f"| {tool} | — | — | — | — | — | — | error: {r.error[:50]} |")
            else:
                lines.append(f"| {tool} | — | — | — | — | — | — | — |")

        lines.append("")

    # Overall summary
    lines.extend(["## Overall summary", "", "| Tool | Total pages | Total time (s) | Avg pages/sec |", "|---|---|---|---|"])

    for tool in available_tools:
        total_pages = sum(
            r.pages_median for r in results.get(tool, {}).values() if not r.error
        )
        total_time = sum(
            r.time_median for r in results.get(tool, {}).values() if not r.error
        )
        avg_pps = total_pages / total_time if total_time > 0 else 0
        lines.append(f"| {tool} | {total_pages:.0f} | {total_time:.1f} | {avg_pps:.1f} |")

    lines.extend([
        "",
        "## Reproducing these results",
        "",
        "```bash",
        "# Install all tools",
        "pip install markcrawl crawl4ai scrapy markdownify",
        "playwright install chromium  # for crawl4ai",
        "",
        "# Run comparison",
        "python benchmarks/benchmark_all_tools.py",
        "```",
        "",
        "For FireCrawl, also run:",
        "```bash",
        "docker run -p 3002:3002 firecrawl/firecrawl:latest",
        "export FIRECRAWL_API_URL=http://localhost:3002",
        "python benchmarks/benchmark_all_tools.py",
        "```",
    ])

    report = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _get_tool_version(tool_name: str) -> str:
    """Return installed package version for a tool, or 'unknown'."""
    pkg_map = {
        "markcrawl": "markcrawl",
        "crawl4ai": "crawl4ai",
        "scrapy+md": "scrapy",
        "crawlee": "crawlee",
        "playwright": "playwright",
        "firecrawl": "firecrawl-py",
        "colly+md": None,  # Go binary — no Python package
    }
    pkg = pkg_map.get(tool_name)
    if pkg is None:
        return "go binary"
    try:
        import importlib.metadata
        return importlib.metadata.version(pkg)
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Head-to-head crawler comparison")
    parser.add_argument("--sites", default=None, help="Comma-separated sites to test")
    parser.add_argument("--iterations", type=int, default=3, help="Iterations per tool per site (default: 3)")
    parser.add_argument("--skip-warmup", action="store_true", help="Skip warm-up run")
    parser.add_argument("--output", default="benchmarks/SPEED_COMPARISON.md", help="Output report path")
    args = parser.parse_args()

    run_start = time.time()
    run_start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_start))

    # Select sites
    if args.sites:
        site_names = [s.strip() for s in args.sites.split(",")]
        sites = {k: v for k, v in COMPARISON_SITES.items() if k in site_names}
    else:
        sites = COMPARISON_SITES

    # Check available tools
    available = []
    skipped = {}
    print("Checking tools...")
    for name, tool in TOOLS.items():
        ok = tool["check"]()
        status = "available" if ok else "NOT INSTALLED"
        print(f"  {name}: {status}")
        if ok:
            available.append(name)
        else:
            skipped[name] = "not installed"

    if not available:
        print("\nNo tools available. Install at least: pip install markcrawl")
        sys.exit(1)

    print(f"\nRunning comparison: {len(available)} tool(s) × {len(sites)} site(s) × {args.iterations} iteration(s)")
    if not args.skip_warmup:
        print("(+ 1 warm-up run per site)")
    print("=" * 60)

    # Phase 1: Discover URLs for each site (all tools get identical pages)
    phase1_start = time.time()
    print("\n--- Phase 1: URL Discovery ---")
    site_urls: dict[str, List[str]] = {}
    for site_name, site_config in sites.items():
        print(f"  Discovering URLs for {site_name}...", end=" ", flush=True)
        urls = discover_urls(site_config["url"], site_config["max_pages"])
        site_urls[site_name] = urls
        print(f"{len(urls)} URLs found")
    phase1_end = time.time()

    # Phase 2: Benchmark all tools on identical URL lists
    phase2_start = time.time()
    print("\n--- Phase 2: Benchmarking (identical URLs per site) ---")
    base_dir = tempfile.mkdtemp(prefix="markcrawl_comparison_")
    results: dict[str, dict[str, ToolSiteResult]] = {}

    # Per-tool per-site timing for metadata
    tool_site_timing: dict[str, dict[str, dict]] = {}

    for tool_name in available:
        results[tool_name] = {}
        tool_site_timing[tool_name] = {}
        run_fn = TOOLS[tool_name]["run"]

        for site_name, site_config in sites.items():
            urls = site_urls[site_name]
            print(f"\n  {tool_name} → {site_name} ({len(urls)} URLs):")

            tool_site_start = time.time()

            # Warm-up
            if not args.skip_warmup:
                print("    warm-up...", end=" ", flush=True)
                try:
                    run_single(tool_name, run_fn, site_name, site_config, base_dir, url_list=urls)
                    print("done")
                except Exception as exc:
                    print(f"failed: {exc}")

            # Iterations
            runs = []
            for i in range(args.iterations):
                print(f"    run {i + 1}/{args.iterations}...", end=" ", flush=True)
                result = run_single(tool_name, run_fn, site_name, site_config, base_dir, url_list=urls)
                if result.error:
                    print(f"error: {result.error[:60]}")
                else:
                    print(f"{result.pages} pages in {result.time_seconds:.1f}s ({result.pages_per_second:.1f} p/s)")
                runs.append(result)

            agg = aggregate_runs(runs, site_config)
            results[tool_name][site_name] = agg

            tool_site_timing[tool_name][site_name] = {
                "wall_start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(tool_site_start)),
                "wall_end_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "pages_median": agg.pages_median,
                "time_median_s": round(agg.time_median, 3),
                "pps_median": round(agg.pps_median, 3),
                "error": agg.error,
            }

    phase2_end = time.time()

    # Phase 3: Quality scoring (cross-tool consensus on last iteration's output)
    phase3_start = time.time()
    print("\n--- Phase 3: Extraction Quality Scoring ---")
    try:
        from benchmarks.quality_scorer import (
            PageQuality,
            generate_quality_report,
            score_consensus,
            score_density,
            score_signals,
        )

        quality_results: dict[str, dict[str, list]] = {}

        for site_name in sites:
            quality_results[site_name] = {}

            # Load each tool's output from the last iteration
            tool_outputs_by_url: dict[str, dict[str, str]] = {}  # {url: {tool: markdown}}

            for tool_name in available:
                out_dir = os.path.join(base_dir, tool_name, site_name)
                jsonl_path = os.path.join(out_dir, "pages.jsonl")
                if not os.path.isfile(jsonl_path):
                    continue
                with open(jsonl_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        page = json.loads(line)
                        url = page.get("url", "").rstrip("/")  # normalize trailing slash
                        text = page.get("text", "")
                        if url and text:
                            if url not in tool_outputs_by_url:
                                tool_outputs_by_url[url] = {}
                            tool_outputs_by_url[url][tool_name] = text

            # Score each tool
            for tool_name in available:
                pages = []
                for url, outputs in tool_outputs_by_url.items():
                    if tool_name not in outputs:
                        continue
                    markdown = outputs[tool_name]
                    signal = score_signals(markdown)
                    density = score_density(markdown)
                    consensus = score_consensus(markdown, outputs, tool_name)
                    pages.append(PageQuality(
                        url=url, tool=tool_name,
                        signal=signal, density=density, consensus=consensus,
                    ))
                quality_results[site_name][tool_name] = pages

            print(f"  {site_name}: scored {sum(len(p) for p in quality_results[site_name].values())} pages across {len(available)} tools")

        # Generate quality report
        quality_report_path = os.path.join(os.path.dirname(args.output), "QUALITY_COMPARISON.md")
        quality_report = generate_quality_report(quality_results, available)
        with open(quality_report_path, "w", encoding="utf-8") as f:
            f.write(quality_report)
        print(f"Quality report saved to: {quality_report_path}")

    except Exception as exc:
        print(f"  Quality scoring failed: {exc}")

    phase3_end = time.time()
    run_end = time.time()

    print("\n" + "=" * 60)
    generate_comparison_report(results, available, args.output)
    print(f"Report saved to: {args.output}")

    # Write run_metadata.json before saving
    metadata = {
        "run_start_iso": run_start_iso,
        "run_end_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_end)),
        "total_wall_seconds": round(run_end - run_start, 1),
        "settings": {
            "iterations": args.iterations,
            "skip_warmup": args.skip_warmup,
            "sites": list(sites.keys()),
        },
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
        },
        "tools": {
            name: {
                "available": name in available,
                "version": _get_tool_version(name) if name in available else None,
                "skip_reason": skipped.get(name),
            }
            for name in TOOLS
        },
        "phases": {
            "url_discovery": {
                "start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase1_start)),
                "end_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase1_end)),
                "wall_seconds": round(phase1_end - phase1_start, 1),
                "urls_discovered": {site: len(urls) for site, urls in site_urls.items()},
            },
            "benchmarking": {
                "start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase2_start)),
                "end_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase2_end)),
                "wall_seconds": round(phase2_end - phase2_start, 1),
                "results": tool_site_timing,
            },
            "quality_scoring": {
                "start_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase3_start)),
                "end_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(phase3_end)),
                "wall_seconds": round(phase3_end - phase3_start, 1),
            },
        },
        "output_report": args.output,
        "note": "Markdown output files in each tool/site subfolder are usable for a "
                "later embedding pass without re-running the crawl.",
    }
    metadata_path = os.path.join(base_dir, "run_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save run data (keep last 10 runs)
    _save_run_data(base_dir)


def _save_run_data(base_dir: str) -> None:
    """Copy run output to benchmarks/runs/ with timestamp. Keep last 10 runs (~35-40MB each)."""
    runs_dir = os.path.join(os.path.dirname(__file__), "runs")
    os.makedirs(runs_dir, exist_ok=True)

    # Save current run
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    run_dest = os.path.join(runs_dir, f"run_{timestamp}")
    try:
        shutil.copytree(base_dir, run_dest)
        print(f"Run data saved to: {run_dest}")
    except Exception as exc:
        print(f"Warning: could not save run data: {exc}")
        shutil.rmtree(base_dir, ignore_errors=True)
        return

    # Clean up temp dir
    shutil.rmtree(base_dir, ignore_errors=True)

    # Keep only the last 10 runs
    existing_runs = sorted(
        [d for d in os.listdir(runs_dir) if d.startswith("run_") and os.path.isdir(os.path.join(runs_dir, d))],
    )
    while len(existing_runs) > 10:
        oldest = existing_runs.pop(0)
        oldest_path = os.path.join(runs_dir, oldest)
        shutil.rmtree(oldest_path, ignore_errors=True)
        print(f"Removed old run: {oldest}")


if __name__ == "__main__":
    main()
