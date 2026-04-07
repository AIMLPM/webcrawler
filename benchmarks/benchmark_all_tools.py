#!/usr/bin/env python3
"""Head-to-head benchmark: MarkCrawl vs Crawl4AI vs Scrapy+markdownify.

Runs all available tools against the same sites with equivalent settings,
measuring performance, extraction quality, and output characteristics.

FireCrawl runs if FIRECRAWL_API_KEY or FIRECRAWL_API_URL is set. The script
auto-loads .env from the project root, so no manual `source .env` is needed.

Usage:
    python benchmarks/benchmark_all_tools.py
    python benchmarks/benchmark_all_tools.py --parallel                    # cross-site parallelism
    python benchmarks/benchmark_all_tools.py --parallel --site-parallelism 2  # 2 tools per site
    python benchmarks/benchmark_all_tools.py --sites quotes-toscrape,fastapi-docs
    python benchmarks/benchmark_all_tools.py --iterations 1 --skip-warmup  # quick test

See benchmarks/METHODOLOGY.md for the methodology.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Auto-relaunch inside .venv if we're running from the system Python.
# This ensures all pip-installed benchmark tools are importable regardless
# of whether the user remembered to `source .venv/bin/activate`.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _REPO_ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python3")

if sys.prefix == sys.base_prefix and _VENV_PYTHON.exists():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

import argparse
import json
import random
import shutil
import statistics
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

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
        "max_pages": 500,
        "description": "API documentation (code blocks, headings, tutorials)",
        "skip_patterns": [r"/[a-z]{2}/"],  # skip translated pages (/tr/, /zh/, etc.)
    },
    "python-docs": {
        "url": "https://docs.python.org/3/library/",
        "max_pages": 500,
        "description": "Python standard library docs",
    },
    # --- New diverse sites ---
    "react-dev": {
        "url": "https://react.dev/learn",
        "max_pages": 500,
        "description": "React docs (SPA, JS-rendered, interactive examples)",
        "render_js": True,
    },
    "wikipedia-python": {
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "max_pages": 50,
        "description": "Wikipedia (tables, infoboxes, citations, deep linking)",
    },
    "stripe-docs": {
        "url": "https://docs.stripe.com/payments",
        "max_pages": 500,
        "description": "Stripe API docs (tabbed content, code samples, sidebars)",
    },
    "blog-engineering": {
        "url": "https://github.blog/engineering/",
        "max_pages": 200,
        "description": "GitHub Engineering Blog (articles, images, technical content)",
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
    """Check if FireCrawl is available and the API key is valid.

    FireCrawl requires either:
    - FIRECRAWL_API_KEY env var (uses their SaaS API — free tier available)
    - FIRECRAWL_API_URL env var (self-hosted via docker-compose)

    For SaaS keys, validates the key against the API and checks remaining
    credits.  Sets ``check_firecrawl.status`` with a human-readable detail
    string (e.g. ``"42 credits remaining"``).

    Note: FireCrawl self-hosting requires docker-compose with multiple services
    (API, worker, Redis). It cannot be run as a single Docker container.
    """
    check_firecrawl.status = ""

    try:
        import firecrawl  # noqa: F401
    except ImportError:
        check_firecrawl.status = "firecrawl-py not installed"
        return False

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    api_url = os.environ.get("FIRECRAWL_API_URL")

    if not (api_key or api_url):
        check_firecrawl.status = "FIRECRAWL_API_KEY not set"
        return False

    # Self-hosted — we can't verify credits, just trust it
    if api_url and not api_key:
        check_firecrawl.status = f"self-hosted ({api_url})"
        return True

    # SaaS — validate key and check credits via SDK
    fc_kwargs = {}
    if api_key:
        fc_kwargs["api_key"] = api_key
    if api_url:
        fc_kwargs["api_url"] = api_url

    try:
        app = firecrawl.FirecrawlApp(**fc_kwargs)
        usage = app.get_credit_usage()
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "Unauthorized" in msg:
            check_firecrawl.status = "invalid API key"
        else:
            check_firecrawl.status = f"API error: {msg[:100]}"
        return False

    try:
        # SDK returns a CreditUsage object with attributes
        remaining = getattr(usage, "remaining_credits", None)
        total = getattr(usage, "plan_credits", None)

        # Fallback: try dict-style access
        if remaining is None and isinstance(usage, dict):
            remaining = usage.get("remaining_credits", usage.get("remaining"))
            total = usage.get("plan_credits", usage.get("total"))

        if remaining is not None:
            check_firecrawl.status = f"{remaining:,}/{total or '?'} credits remaining"
            if remaining <= 0:
                check_firecrawl.status += " — NO CREDITS LEFT"
                return False
        else:
            check_firecrawl.status = "key valid (could not determine credits)"
    except (TypeError, KeyError, AttributeError):
        check_firecrawl.status = "key valid (could not parse credit info)"

    return True


# ---------------------------------------------------------------------------
# URL discovery — cached with validation
#
# Edge cases handled:
#
# 1. max_pages increase: If the user requests more pages than the cache
#    contains (and more than were originally discovered), the cache is
#    invalidated and a full rediscovery runs.
#
# 2. skip_patterns change: The cache stores which skip_patterns were used.
#    If they differ on the next run, the cache is invalidated. This prevents
#    stale non-English URLs from leaking in (or English URLs being missing).
#
# 3. Network outage during validation: If >50% of cached URLs fail HEAD
#    checks, we assume a temporary network issue and keep all cached URLs
#    rather than wiping the cache. This prevents a flaky connection from
#    destroying a valid cache that took minutes to build.
#
# 4. URL ordering: Thread-pool validation returns results in arbitrary
#    order. We preserve the original discovery order so benchmarks are
#    reproducible across runs (same pages in same order → comparable
#    timing results).
#
# 5. Cache expiry: Entries older than _URL_CACHE_MAX_AGE_DAYS trigger a
#    full rediscovery to catch structural site changes (new pages, removed
#    sections, URL scheme changes).
#
# 6. Atomic writes: Cache is written to a .tmp file then os.replace()'d
#    to avoid corruption if the process is killed mid-write.
#
# 7. Docker volume mount: .url_cache.json lives in benchmarks/, which is
#    volume-mounted in Docker. A host-side cache speeds up Docker runs
#    too. Fresh Docker builds (no volume) always do full discovery.
# ---------------------------------------------------------------------------

_URL_CACHE_PATH = os.path.join(os.path.dirname(__file__), ".url_cache.json")
_URL_CACHE_MAX_AGE_DAYS = 7


def _load_url_cache() -> dict:
    """Load the URL cache from disk."""
    if not os.path.isfile(_URL_CACHE_PATH):
        return {}
    try:
        with open(_URL_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_url_cache(cache: dict) -> None:
    """Atomically write the URL cache."""
    tmp = _URL_CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, _URL_CACHE_PATH)


def _validate_urls(urls: List[str], concurrency: int = 20) -> tuple[List[str], List[str]]:
    """Check which URLs are still live using HEAD requests.

    Returns (live_urls, dead_urls) preserving the original order of `urls`.
    If >50% of URLs fail, assumes a network issue and returns all as live
    to avoid wiping the cache during a temporary outage.
    """
    import urllib.request

    # Map url → is_live, preserving order
    status_map: Dict[str, bool] = {}
    lock = threading.Lock()

    def _check(url: str) -> None:
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "markcrawl-benchmark/1.0")
            resp = urllib.request.urlopen(req, timeout=10)
            code = resp.getcode()
        except Exception:
            # HEAD rejected — try GET
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "markcrawl-benchmark/1.0")
                resp = urllib.request.urlopen(req, timeout=10)
                code = resp.getcode()
            except Exception:
                code = 0

        with lock:
            status_map[url] = (200 <= code < 400)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pool.map(_check, urls)

    dead_count = sum(1 for ok in status_map.values() if not ok)
    if len(urls) > 5 and dead_count > len(urls) * 0.5:
        # Likely a network issue, not actual page removal — keep all
        print(f"WARNING: {dead_count}/{len(urls)} URLs unreachable, likely network issue — keeping all cached URLs")
        return list(urls), []

    # Preserve original ordering
    live = [u for u in urls if status_map.get(u, True)]
    dead = [u for u in urls if not status_map.get(u, True)]
    return live, dead


def _discover_fresh(url: str, max_pages: int, skip_patterns: Optional[List[str]] = None) -> List[str]:
    """Full crawl-based URL discovery (original method)."""
    import re
    from markcrawl.core import crawl

    crawl_pages = max_pages * 2 if skip_patterns else max_pages

    tmp_dir = tempfile.mkdtemp(prefix="mc_discover_")
    crawl(
        base_url=url,
        out_dir=tmp_dir,
        fmt="markdown",
        max_pages=crawl_pages,
        delay=0,
        timeout=15,
        show_progress=False,
        min_words=5,
    )

    compiled = [re.compile(p) for p in (skip_patterns or [])]
    urls = []
    jsonl_path = os.path.join(tmp_dir, "pages.jsonl")
    if os.path.isfile(jsonl_path):
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    page = json.loads(line)
                    page_url = page.get("url", "")
                    if page_url and not any(p.search(page_url) for p in compiled):
                        urls.append(page_url)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return urls[:max_pages]


def discover_urls(
    site_name: str,
    url: str,
    max_pages: int,
    skip_patterns: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> List[str]:
    """Discover URLs with caching, validation, and staleness detection.

    1. If a fresh cache exists (< 7 days old) with matching settings,
       validate cached URLs with HEAD requests, remove dead ones, and return.
    2. If cache is stale, settings changed, or missing, do a full crawl
       discovery and cache results.
    3. --refresh-urls forces a full rediscovery.
    """
    from datetime import datetime, timezone

    cache = _load_url_cache()
    entry = cache.get(site_name)
    now = datetime.now(timezone.utc)
    current_patterns = skip_patterns or []

    # Check if cache is usable
    if entry and not force_refresh:
        cached_at = datetime.fromisoformat(entry["discovered_at"])
        age_days = (now - cached_at).total_seconds() / 86400

        # Invalidate if settings changed
        cached_patterns = entry.get("skip_patterns", [])
        cached_max = entry.get("max_pages", 0)
        settings_changed = (cached_patterns != current_patterns)
        needs_more = (max_pages > len(entry.get("urls", [])) and max_pages > cached_max)

        if settings_changed:
            print(f"skip_patterns changed, rediscovering...", end=" ", flush=True)
        elif needs_more:
            print(f"max_pages increased ({cached_max}→{max_pages}), rediscovering...", end=" ", flush=True)
        elif age_days >= _URL_CACHE_MAX_AGE_DAYS:
            print(f"cache expired ({age_days:.0f} days old), rediscovering...", end=" ", flush=True)
        else:
            # Cache is usable — validate
            cached_urls = entry["urls"]
            print(f"validating {len(cached_urls)} cached URLs...", end=" ", flush=True)
            live, dead = _validate_urls(cached_urls)
            if dead:
                print(f"{len(dead)} removed, {len(live)} live")
            else:
                print(f"all live")

            # Update cache with only live URLs
            if dead:
                entry["urls"] = live
                entry["validated_at"] = now.isoformat()
                _save_url_cache(cache)

            return live[:max_pages]

    # Full discovery
    urls = _discover_fresh(url, max_pages, skip_patterns)

    # Cache the results with settings for future invalidation checks
    cache[site_name] = {
        "urls": urls,
        "base_url": url,
        "max_pages": max_pages,
        "skip_patterns": current_patterns,
        "discovered_at": now.isoformat(),
    }
    _save_url_cache(cache)

    return urls


# ---------------------------------------------------------------------------
# Tool runners — fixed URL list mode (identical pages for all tools)
# ---------------------------------------------------------------------------

def run_markcrawl(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, concurrency: int = 1) -> int:
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
            timeout=15, concurrency=concurrency, include_subdomains=False,
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


def run_crawl4ai(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Run Crawl4AI and return pages saved."""
    import asyncio

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    os.makedirs(out_dir, exist_ok=True)
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    urls_to_fetch = url_list if url_list else None

    async def _crawl():
        nonlocal pages_saved
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            if urls_to_fetch:
                # Batch mode — crawl4ai handles concurrency internally
                results = await crawler.arun_many(
                    urls=urls_to_fetch[:max_pages],
                    config=run_config,
                )
                for result in results:
                    try:
                        if not result.success or not result.markdown:
                            continue
                        _write_output(out_dir, jsonl_path, result.url, result)
                        pages_saved += 1
                    except Exception:
                        continue
            else:
                # Discovery mode — follow links (sequential, can't batch)
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


def run_crawl4ai_raw(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Run Crawl4AI with minimal/out-of-box settings — sequential arun(), default config.

    This is the 'raw' baseline: no arun_many() batching, no custom concurrency,
    just the simplest possible crawl4ai usage.  Compare against run_crawl4ai
    (which uses arun_many for batch parallelism).
    """
    import asyncio

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    os.makedirs(out_dir, exist_ok=True)
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    urls_to_fetch = url_list[:max_pages] if url_list else [url]

    async def _crawl():
        nonlocal pages_saved
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            for page_url in urls_to_fetch:
                try:
                    result = await crawler.arun(url=page_url, config=run_config)
                    if not result.success or not result.markdown:
                        continue
                    # Write output in same format as all other tools
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
                    pages_saved += 1
                except Exception:
                    continue

    asyncio.run(_crawl())
    return pages_saved


def run_scrapy_markdownify(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, concurrency: int = 1, **kwargs) -> int:
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
        "CONCURRENT_REQUESTS": {concurrency},
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
        "CONCURRENT_REQUESTS": {concurrency},
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


def run_firecrawl(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Run FireCrawl and return pages saved.

    Uses SaaS API (FIRECRAWL_API_KEY) or self-hosted (FIRECRAWL_API_URL).
    Note: SaaS API includes network latency to their servers.

    Requires firecrawl-py >= 4.x (v2 API): crawl() replaces crawl_url(),
    response is a CrawlJob object with .data list of Document objects.

    Free tier has a 3 req/min rate limit, so we retry with backoff when
    rate-limited rather than failing the entire site.  The wait time is
    tracked via ``_firecrawl_rate_limit_wait`` so ``run_single`` can
    subtract it from the elapsed time — we measure crawl speed, not how
    long we sat waiting for the rate-limit window to reset.
    """
    import re as _re

    from firecrawl import FirecrawlApp
    from firecrawl.v2.types import ScrapeOptions

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    api_url = os.environ.get("FIRECRAWL_API_URL")

    fc_kwargs = {}
    if api_key:
        fc_kwargs["api_key"] = api_key
    if api_url:
        fc_kwargs["api_url"] = api_url
    app = FirecrawlApp(**fc_kwargs)

    os.makedirs(out_dir, exist_ok=True)
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    # Retry with backoff on rate-limit errors (free tier: 3 req/min).
    # Track total wait so run_single can subtract it from elapsed time.
    max_retries = 5
    result = None
    rate_limit_wait = 0.0
    for attempt in range(max_retries):
        try:
            result = app.crawl(
                url,
                limit=max_pages,
                scrape_options=ScrapeOptions(formats=["markdown"]),
            )
            break
        except Exception as exc:
            msg = str(exc)
            if "Rate Limit" not in msg:
                raise
            match = _re.search(r"retry after (\d+)s", msg)
            wait = int(match.group(1)) + 2 if match else 15
            if attempt < max_retries - 1:
                print(f"    [firecrawl] rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                rate_limit_wait += wait
                time.sleep(wait)
            else:
                raise

    # Stash wait time where run_single can find it
    run_firecrawl._rate_limit_wait = rate_limit_wait

    if result is None:
        return 0

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


_CRAWLEE_WORKER = Path(__file__).parent / "crawlee_worker.py"


def run_crawlee(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Run Crawlee (Python) with Playwright in a subprocess.

    Each call gets a fresh event loop, avoiding the asyncio.Lock/event-loop
    mismatch that occurs when crawlee is invoked multiple times in the same
    process (Python 3.13 regression in crawlee's storage client).
    """
    os.makedirs(out_dir, exist_ok=True)
    cmd = [sys.executable, str(_CRAWLEE_WORKER), url, out_dir, str(max_pages)]
    if url_list:
        cmd.extend(url_list[:max_pages])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
        last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "0"
        return int(last_line)
    except (subprocess.TimeoutExpired, ValueError):
        return 0


def run_colly_markdownify(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Run Colly (Go) for fetching + Python markdownify for conversion."""
    os.makedirs(out_dir, exist_ok=True)

    colly_bin = os.path.join(os.path.dirname(__file__), "colly_crawler", "colly_crawler")
    html_dir = os.path.join(out_dir, "_html")
    os.makedirs(html_dir, exist_ok=True)

    cmd = [colly_bin, "-url", url, "-out", html_dir, "-max", str(max_pages)]

    # Build a safe_name → original_url map BEFORE calling colly so we can
    # recover exact URLs later. Reconstructing from filenames is lossy because
    # underscores in the original URL (e.g. "item_1000") are indistinguishable
    # from path separators after the replace("_", "/") round-trip.
    effective_urls = url_list[:max_pages] if url_list else [url]
    url_map: Dict[str, str] = {}
    for u in effective_urls:
        safe = u.replace("://", "_").replace("/", "_")[:80]
        url_map[safe] = u

    url_map_path = os.path.join(out_dir, "_url_map.json")
    with open(url_map_path, "w", encoding="utf-8") as f:
        json.dump(url_map, f)

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

        # Resolve URL: prefer the pre-built map (exact), fall back to lossy
        # filename reconstruction only for URLs not in the map.
        stem = html_file.stem
        if stem in url_map:
            page_url = url_map[stem]
        elif stem.startswith("https_"):
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


def run_playwright_raw(url: str, out_dir: str, max_pages: int, url_list: Optional[List[str]] = None, **kwargs) -> int:
    """Raw Playwright baseline — browser fetch + markdownify, no framework overhead."""
    from playwright.sync_api import sync_playwright

    os.makedirs(out_dir, exist_ok=True)
    urls_to_fetch = url_list if url_list else [url]
    pages_saved = 0
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    from markdownify import markdownify as md

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-dev-shm-usage",
                "--no-first-run",
            ],
        )

        context = browser.new_context()
        # Block images, CSS, fonts — we only need HTML text
        context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
        context.route("**/*.{css,less,scss}", lambda route: route.abort())
        context.route("**/*.{woff,woff2,ttf,otf,eot}", lambda route: route.abort())
        page = context.new_page()
        for page_url in urls_to_fetch[:max_pages]:
            try:
                page.goto(page_url, timeout=15000, wait_until="domcontentloaded")
                html = page.content()
                title = page.title()
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

        context.close()
        browser.close()

    return pages_saved


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

TOOLS = {
    "markcrawl": {"check": check_markcrawl, "run": run_markcrawl},
    "crawl4ai": {"check": check_crawl4ai, "run": run_crawl4ai},
    "crawl4ai-raw": {"check": check_crawl4ai, "run": run_crawl4ai_raw},
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
    concurrency: int = 1,
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
        pages = run_fn(url, out_dir, max_pages, url_list=url_list, concurrency=concurrency)
        error = None
    except Exception as exc:
        pages = 0
        error = str(exc)

    elapsed = time.time() - start

    # Subtract any rate-limit wait time (firecrawl free tier)
    rate_limit_wait = getattr(run_fn, "_rate_limit_wait", 0.0)
    if rate_limit_wait > 0:
        elapsed = max(0.1, elapsed - rate_limit_wait)
        run_fn._rate_limit_wait = 0.0  # reset for next call

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
    concurrency: int = 1,
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
        f"- **Concurrency:** {concurrency}",
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

    all_tools = ["markcrawl", "crawl4ai", "crawl4ai-raw", "scrapy+md", "crawlee", "colly+md", "playwright", "firecrawl"]
    for tool in all_tools:
        available = tool in available_tools
        notes = {
            "markcrawl": "requests + BeautifulSoup + markdownify — [AIMLPM/markcrawl](https://github.com/AIMLPM/markcrawl)",
            "crawl4ai": "Playwright + arun_many() batch concurrency — [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)",
            "crawl4ai-raw": "Playwright + sequential arun(), default config (out-of-box baseline)",
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
    lines.extend(["## Overall summary", "", "| Tool | Total pages | Total time (s) | Avg pages/sec | Notes |", "|---|---|---|---|---|"])

    total_sites = len(COMPARISON_SITES)
    for tool in available_tools:
        tool_results = results.get(tool, {})
        successful = {k: v for k, v in tool_results.items() if not v.error}
        total_pages = sum(r.pages_median for r in successful.values())
        total_time = sum(r.time_median for r in successful.values())
        avg_pps = total_pages / total_time if total_time > 0 else 0
        note = ""
        if len(successful) < total_sites and len(successful) > 0:
            note = f" *({len(successful)}/{total_sites} sites)*"
        elif len(successful) == 0:
            lines.append(f"| {tool} | — | — | — | *all sites errored* |")
            continue
        lines.append(f"| {tool} | {total_pages:.0f} | {total_time:.1f} | {avg_pps:.1f} |{note}")

    lines.extend([
        "",
        "> **Note on variance:** These benchmarks fetch pages from live public websites.",
        "> Network conditions, server load, and CDN caching can cause significant",
        "> run-to-run variance (std dev shown per site). For the most reliable comparison,",
        "> run multiple iterations and compare medians.",
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
    parser.add_argument("--iterations", type=int, default=2, help="Iterations per tool per site (default: 2)")
    parser.add_argument("--skip-warmup", action="store_true", help="Skip warm-up run")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrency level for tools that support it (default: 5)")
    parser.add_argument("--parallel", action="store_true", default=True,
                        help="Run tools on different sites in parallel (default: on)")
    parser.add_argument("--sequential", action="store_true",
                        help="Run tools sequentially instead of in parallel")
    parser.add_argument("--site-parallelism", type=int, default=2,
                        help="Max tools hitting the same site simultaneously (default: 2)")
    parser.add_argument("--firecrawl-tier", choices=["free", "paid"], default=None,
                        help="FireCrawl account tier. 'free' skips warmup to save credits, "
                             "'paid' enables warmup. Auto-detected from FIRECRAWL_TIER env var, "
                             "defaults to 'free'.")
    parser.add_argument("--no-resume", action="store_true",
                        help="Ignore any saved checkpoint and start fresh")
    parser.add_argument("--refresh-urls", action="store_true",
                        help="Force full URL rediscovery (ignore URL cache)")
    parser.add_argument("--output", default="benchmarks/SPEED_COMPARISON.md", help="Output report path")
    args = parser.parse_args()

    # --sequential overrides --parallel
    if args.sequential:
        args.parallel = False

    # Determine firecrawl tier: CLI flag > env var > default "free"
    firecrawl_tier = args.firecrawl_tier or os.environ.get("FIRECRAWL_TIER", "free").lower()

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
        check_fn = tool["check"]
        ok = check_fn()
        extra = ""
        if name == "firecrawl":
            detail = getattr(check_fn, "status", "")
            if ok:
                extra = f" [{firecrawl_tier} tier — {detail}]" if detail else f" [{firecrawl_tier} tier]"
            elif detail:
                extra = f" ({detail})"
        status = "available" if ok else "NOT AVAILABLE"
        print(f"  {name}: {status}{extra}")
        if ok:
            available.append(name)
        else:
            reason = getattr(check_fn, "status", "") if name == "firecrawl" else "not installed"
            skipped[name] = reason or "not installed"

    if not available:
        print("\nNo tools available. Install at least: pip install markcrawl")
        sys.exit(1)

    # --- Pre-flight: run the full preflight check before starting ---
    print("\n--- Pre-flight check ---")
    try:
        from preflight import run_checks, print_ready_status
        tool_results, _ = run_checks()
        print_ready_status(tool_results)
        if not tool_results.get("markcrawl"):
            print("\nPre-flight FAILED: markcrawl is required (used for URL discovery).")
            print("  Fix: pip install -e .  (from repo root)")
            sys.exit(1)
        ready = [t for t, ok in tool_results.items() if ok]
        not_ready = [t for t, ok in tool_results.items() if not ok]
        if not_ready:
            print(f"\nPre-flight FAILED: {len(not_ready)} tool(s) not ready: {', '.join(not_ready)}")
            print("  Fix: python benchmarks/preflight.py --install")
            sys.exit(1)
        print("Pre-flight passed — all tools ready.\n")
    except ImportError:
        print("  Warning: preflight.py not found, skipping pre-flight checks.\n")

    mode = "parallel" if args.parallel else "sequential"
    print(f"\nRunning comparison: {len(available)} tool(s) × {len(sites)} site(s) × {args.iterations} iteration(s) [{mode}]")
    if not args.skip_warmup:
        print("(+ 1 warm-up run per site)")
    if args.parallel:
        print(f"(max {args.site_parallelism} tool(s) per site simultaneously)")
    print("=" * 60)

    # --- Checkpoint: attempt to resume a previous interrupted run ---
    checkpoint_path = _DEFAULT_CHECKPOINT
    args_dict = {
        "iterations": args.iterations,
        "skip_warmup": args.skip_warmup,
        "concurrency": args.concurrency,
        "sites": sorted(sites.keys()),
        "tools": sorted(available),
    }

    cp = None if args.no_resume else _load_checkpoint(checkpoint_path, args_dict)
    resumed_results: Dict[str, Dict[str, ToolSiteResult]] = {}
    resumed_urls: Dict[str, List[str]] = {}
    resumed_base_dir: Optional[str] = None
    if cp:
        resumed_results = _restore_results(cp)
        resumed_urls = cp.get("site_urls", {})
        resumed_base_dir = cp.get("base_dir")
        completed = sum(len(s) for s in resumed_results.values())
        total = len(available) * len(sites)
        print(f"\n  Resuming from checkpoint: {completed}/{total} tool-site pairs already done.")
    elif not args.no_resume:
        # No valid checkpoint — clean start
        pass

    # Phase 1: Discover URLs for each site (all tools get identical pages)
    phase1_start = time.time()
    print("\n--- Phase 1: URL Discovery ---")
    site_urls: dict[str, List[str]] = {}
    for site_name, site_config in sites.items():
        if site_name in resumed_urls and resumed_urls[site_name]:
            site_urls[site_name] = resumed_urls[site_name]
            print(f"  {site_name}: {len(site_urls[site_name])} URLs (from checkpoint)")
        else:
            print(f"  {site_name}: ", end="", flush=True)
            urls = discover_urls(
                site_name=site_name,
                url=site_config["url"],
                max_pages=site_config["max_pages"],
                skip_patterns=site_config.get("skip_patterns"),
                force_refresh=args.refresh_urls,
            )
            site_urls[site_name] = urls
            print(f"{len(urls)} URLs")
    phase1_end = time.time()

    # Phase 2: Benchmark all tools on identical URL lists
    phase2_start = time.time()
    if resumed_base_dir and os.path.isdir(resumed_base_dir):
        base_dir = resumed_base_dir
    else:
        base_dir = tempfile.mkdtemp(prefix="markcrawl_comparison_")
    results: dict[str, dict[str, ToolSiteResult]] = {}
    tool_site_timing: dict[str, dict[str, dict]] = {}

    for tool_name in available:
        results[tool_name] = resumed_results.get(tool_name, {})
        tool_site_timing[tool_name] = {}

    # Lock for thread-safe checkpoint writes in parallel mode
    _checkpoint_lock = threading.Lock()

    def _bench_tool_site(tool_name: str, site_name: str) -> None:
        """Run warmup + iterations for one tool on one site."""
        # Skip if already completed in a resumed checkpoint
        if site_name in results.get(tool_name, {}):
            r = results[tool_name][site_name]
            status = f"error: {r.error[:40]}" if r.error else f"{r.pages_median:.0f} pages, {r.time_median:.1f}s"
            print(f"\n  {tool_name} → {site_name}: skipped (checkpoint: {status})")
            return

        run_fn = TOOLS[tool_name]["run"]
        site_config = sites[site_name]
        urls = site_urls[site_name]
        tool_site_start = time.time()

        print(f"\n  {tool_name} → {site_name} ({len(urls)} URLs):")

        # Warm-up — skip for firecrawl on free tier (wastes API credits)
        skip_warmup = args.skip_warmup or (tool_name == "firecrawl" and firecrawl_tier == "free")
        if not skip_warmup:
            print(f"    [{tool_name}/{site_name}] warm-up...", flush=True)
            try:
                run_single(tool_name, run_fn, site_name, site_config, base_dir,
                           url_list=urls, concurrency=args.concurrency)
            except Exception as exc:
                print(f"    [{tool_name}/{site_name}] warm-up failed: {exc}")

        # Iterations
        runs = []
        for i in range(args.iterations):
            result = run_single(tool_name, run_fn, site_name, site_config, base_dir,
                                url_list=urls, concurrency=args.concurrency)
            if result.error:
                print(f"    [{tool_name}/{site_name}] run {i+1}/{args.iterations}: error: {result.error[:60]}")
            else:
                print(f"    [{tool_name}/{site_name}] run {i+1}/{args.iterations}: "
                      f"{result.pages} pages in {result.time_seconds:.1f}s ({result.pages_per_second:.1f} p/s)")
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

        # Save checkpoint after each tool-site pair completes
        with _checkpoint_lock:
            _save_checkpoint(checkpoint_path, site_urls, results, base_dir, args_dict)

    if args.parallel:
        # Parallel mode: tools on different sites run concurrently.
        # Per-site semaphores limit how many tools hit the same host at once.
        print(f"\n--- Phase 2: Benchmarking (parallel, max {args.site_parallelism} tool(s) per site) ---")
        site_semaphores: dict[str, threading.Semaphore] = {
            site: threading.Semaphore(args.site_parallelism) for site in sites
        }

        # Build work items: (tool, site) pairs — randomized to reduce ordering bias
        work_items = [(tool, site) for tool in available for site in sites]
        random.shuffle(work_items)

        def _guarded_bench(tool_name: str, site_name: str) -> None:
            with site_semaphores[site_name]:
                _bench_tool_site(tool_name, site_name)

        # Max workers = number of sites (each site can run site_parallelism tools,
        # but we also want cross-site parallelism).  Cap at total work items.
        max_workers = min(len(work_items), len(sites) * args.site_parallelism)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_guarded_bench, tool, site) for tool, site in work_items]
            for future in as_completed(futures):
                exc = future.exception()
                if exc:
                    print(f"  Warning: benchmark task failed: {exc}")
    else:
        # Sequential mode — randomize tool order per site to eliminate
        # cache/CDN bias from fixed ordering.
        print("\n--- Phase 2: Benchmarking (identical URLs per site, randomized tool order) ---")
        for site_name in sites:
            tool_order = list(available)
            random.shuffle(tool_order)
            print(f"  {site_name} tool order: {', '.join(tool_order)}")
            for tool_name in tool_order:
                _bench_tool_site(tool_name, site_name)

    phase2_end = time.time()
    run_end = time.time()

    print("\n" + "=" * 60)
    generate_comparison_report(results, available, args.output, concurrency=args.concurrency)
    print(f"Report saved to: {args.output}")

    # All done — remove checkpoint file
    _remove_checkpoint(checkpoint_path)
    print("Checkpoint cleared (run completed successfully).")
    print(f"\nRun data saved to: {base_dir}")
    print(f"\nTo score extraction quality (preamble, repeat rate, precision/recall):")
    print(f"  python benchmarks/benchmark_quality.py")

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
            "parallel_mode": args.parallel,
            "site_parallelism": args.site_parallelism,
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


# ---------------------------------------------------------------------------
# Checkpoint support — resume after interruption
# ---------------------------------------------------------------------------

_DEFAULT_CHECKPOINT = os.path.join(os.path.dirname(__file__), ".benchmark_checkpoint.json")


def _save_checkpoint(
    path: str,
    site_urls: Dict[str, List[str]],
    results: Dict[str, Dict[str, ToolSiteResult]],
    base_dir: str,
    args_dict: dict,
) -> None:
    """Persist progress so the benchmark can resume after interruption."""
    serialized_results: Dict[str, Dict[str, dict]] = {}
    for tool, sites in results.items():
        serialized_results[tool] = {}
        for site, tsr in sites.items():
            serialized_results[tool][site] = {
                "tool": tsr.tool,
                "site": tsr.site,
                "description": tsr.description,
                "pages_median": tsr.pages_median,
                "time_median": tsr.time_median,
                "time_stddev": tsr.time_stddev,
                "pps_median": tsr.pps_median,
                "output_kb": tsr.output_kb,
                "peak_memory_mb": tsr.peak_memory_mb,
                "avg_words": tsr.avg_words,
                "error": tsr.error,
            }

    checkpoint = {
        "version": 1,
        "base_dir": base_dir,
        "args": args_dict,
        "site_urls": site_urls,
        "results": serialized_results,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    os.replace(tmp, path)


def _load_checkpoint(path: str, args_dict: dict) -> Optional[dict]:
    """Load a checkpoint if it exists and settings match the current run."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            cp = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if cp.get("version") != 1:
        return None

    # Settings must match — different iterations/concurrency/sites means start fresh
    if cp.get("args") != args_dict:
        print("  Checkpoint found but settings differ — starting fresh.")
        return None

    return cp


def _restore_results(cp: dict) -> Dict[str, Dict[str, ToolSiteResult]]:
    """Rebuild ToolSiteResult objects from checkpoint data."""
    results: Dict[str, Dict[str, ToolSiteResult]] = {}
    for tool, sites in cp.get("results", {}).items():
        results[tool] = {}
        for site, data in sites.items():
            results[tool][site] = ToolSiteResult(
                tool=data["tool"],
                site=data["site"],
                description=data["description"],
                pages_median=data["pages_median"],
                time_median=data["time_median"],
                time_stddev=data["time_stddev"],
                pps_median=data["pps_median"],
                output_kb=data["output_kb"],
                peak_memory_mb=data["peak_memory_mb"],
                avg_words=data["avg_words"],
                error=data.get("error"),
            )
    return results


def _remove_checkpoint(path: str) -> None:
    """Remove checkpoint file after successful completion."""
    try:
        os.remove(path)
    except OSError:
        pass


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
