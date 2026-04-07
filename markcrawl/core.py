"""Web crawler core module.

Implements a three-stage crawl pipeline:

1. **Discover URLs** -- sitemap-first discovery (parses robots.txt for Sitemap
   directives, then recursively fetches sitemap XML).  Falls back to BFS link
   following when no sitemap is available.
2. **Fetch & clean content** -- downloads each page (optionally rendering JS
   via Playwright), strips navigation, footer, scripts, and other boilerplate,
   then extracts the main content region.
3. **Transform & persist** -- converts cleaned HTML to Markdown or plain text,
   deduplicates by content hash, writes individual files, and appends each
   page to a JSONL index (``pages.jsonl``).

The public entry point is :func:`crawl`, which orchestrates all three stages
and returns a :class:`CrawlResult`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import signal
import threading
import time
import urllib.parse as up
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple

# Submodule imports — all public names are re-exported for backward compatibility
from .extract_content import (
    EXCLUDE_TAGS,
    STRUCTURE_TAGS,
    clean_dom_for_content,
    compact_blank_lines,
    default_progress,
    html_to_markdown,
    html_to_text,
)
from .fetch import (
    DEFAULT_UA,
    PlaywrightResponse,
    _get_playwright_browser,
    build_session,
    fetch,
    fetch_with_playwright,
)
from .robots import discover_sitemaps, parse_robots_txt, parse_sitemap_xml
from .state import STATE_FILENAME, load_state, save_state
from .throttle import AdaptiveThrottle
from .urls import extract_links, norm_url, safe_filename, same_scope

logger = logging.getLogger(__name__)

# Backward-compat aliases for internal state functions
_save_state = save_state
_load_state = load_state


@dataclass
class CrawlResult:
    pages_saved: int
    output_dir: str
    index_file: str


# ---------------------------------------------------------------------------
# CrawlEngine — unified crawl loop for sequential and concurrent modes
# ---------------------------------------------------------------------------

class CrawlEngine:
    """Encapsulates crawl state and provides a single processing path
    for both sequential and concurrent modes.

    The key invariant: ``_process_page()`` mutates ``seen_content`` and must
    only be called from the main thread (never inside a thread pool worker).
    Only ``_fetch_page()`` runs in parallel.
    """

    def __init__(
        self,
        out_dir: str,
        fmt: str,
        min_words: int,
        delay: float,
        timeout: int,
        concurrency: int,
        include_subdomains: bool,
        user_agent: str,
        render_js: bool,
        proxy: Optional[str],
        show_progress: bool,
        content_extractor: Optional[Callable[[str], Tuple[str, str]]] = None,
    ):
        self.out_dir = out_dir
        self.fmt = fmt
        self.ext = "md" if fmt == "markdown" else "txt"
        self.min_words = min_words
        self.content_extractor = content_extractor
        self.delay = delay
        self.timeout = timeout
        self.concurrency = concurrency
        self.include_subdomains = include_subdomains
        self.proxy = proxy
        self.show_progress = show_progress

        self.effective_ua = user_agent or DEFAULT_UA
        self.session = build_session(
            user_agent=self.effective_ua, proxy=proxy,
            pool_size=max(10, concurrency),
        )
        self.progress = default_progress(show_progress)

        # Playwright (optional)
        self.pw_instance = None
        self.pw_browser = None
        self._pw_context = None
        self._pw_lock = threading.Lock()
        if render_js:
            self.pw_instance, self.pw_browser = _get_playwright_browser(proxy=proxy)
            self._pw_context = self.pw_browser.new_context(user_agent=self.effective_ua)
            # Block non-essential resources — we only need HTML for markdown
            self._pw_context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
            self._pw_context.route("**/*.{css,less,scss}", lambda route: route.abort())
            self._pw_context.route("**/*.{woff,woff2,ttf,otf,eot}", lambda route: route.abort())
            self.progress("[info] Playwright browser launched for JS rendering")

        # Timestamps
        now = datetime.now(timezone.utc)
        self.crawl_timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.crawl_date_display = now.strftime("%B %d, %Y")

        # Adaptive throttle
        self._throttle = AdaptiveThrottle(delay, self.progress)

        # Crawl state
        self.to_visit: Deque[str] = deque()
        self.seen_urls: Set[str] = set()
        self.seen_content: Set[str] = set()
        self.visited_for_links: Set[str] = set()
        self.seeds: List[str] = []
        self.saved_count: int = 0
        self.total_planned: Optional[int] = None
        self.interrupted: bool = False

        # Paths
        self.jsonl_path = os.path.join(out_dir, "pages.jsonl")
        self.state_path = os.path.join(out_dir, STATE_FILENAME)

    # Backward-compat properties for throttle state (used by tests)
    @property
    def _base_delay(self):
        return self._throttle.base_delay

    @_base_delay.setter
    def _base_delay(self, value):
        self._throttle.base_delay = value

    @property
    def _active_delay(self):
        return self._throttle.active_delay

    @_active_delay.setter
    def _active_delay(self, value):
        self._throttle._active_delay = value

    @property
    def _backoff_count(self):
        return self._throttle._backoff_count

    @_backoff_count.setter
    def _backoff_count(self, value):
        self._throttle._backoff_count = value

    @property
    def _response_times(self):
        return self._throttle._response_times

    @_response_times.setter
    def _response_times(self, value):
        self._throttle._response_times = value

    # -- Lifecycle ----------------------------------------------------------

    def close(self) -> None:
        """Release Playwright resources."""
        if self._pw_context:
            self._pw_context.close()
        if self.pw_browser:
            self.pw_browser.close()
        if self.pw_instance:
            self.pw_instance.stop()

    # -- Robots / scope -----------------------------------------------------

    def setup_robots(self, base_url: str) -> None:
        self._rp, self._robots_text = parse_robots_txt(self.session, up.urljoin(base_url, "/robots.txt"))

        crawl_delay = AdaptiveThrottle.parse_crawl_delay(self._robots_text, self.effective_ua)
        if crawl_delay is not None and crawl_delay > self._throttle.base_delay:
            self._throttle.base_delay = crawl_delay
            self.progress(f"[info] robots.txt Crawl-delay: {crawl_delay}s")

    # Keep static method for backward compatibility
    @staticmethod
    def _parse_crawl_delay(robots_text: str, user_agent: str = "*") -> Optional[float]:
        return AdaptiveThrottle.parse_crawl_delay(robots_text, user_agent)

    def _update_throttle(self, response) -> None:
        self._throttle.update(response)

    def allowed(self, url: str) -> bool:
        try:
            return self._rp.can_fetch(self.effective_ua, url)
        except Exception:
            return True

    def in_scope(self, url: str, base_netloc: str) -> bool:
        return same_scope(url, base_netloc, self.include_subdomains)

    # -- Fetching -----------------------------------------------------------

    def fetch_page(self, url: str):
        """Fetch a single page. Safe to call from a thread pool worker."""
        if self._pw_context:
            with self._pw_lock:
                return fetch_with_playwright(self._pw_context, url, self.timeout)
        return fetch(self.session, url, self.timeout)

    # -- Processing (main thread only) --------------------------------------

    def process_response(self, url: str, response) -> Optional[Dict]:
        """Validate response and extract content. Returns page_data or None.

        IMPORTANT: This method mutates ``seen_content`` and must only be called
        from the main thread.
        """
        # Note: this method mutates seen_content and is not thread-safe.
        # Callers must not share a CrawlEngine instance across threads.
        if not (response and response.ok):
            return None

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            self.progress(f"[skip] non-HTML content: {url}")
            return None

        links: Set[str] = set()
        if self.content_extractor:
            title, content = self.content_extractor(response.text)
        elif self.fmt == "markdown":
            title, content, links = html_to_markdown(response.text, base_url=url)
        else:
            title, content, links = html_to_text(response.text, base_url=url)

        if not content:
            return None
        if len(content.split()) < self.min_words:
            self.progress(f"[skip] too little content: {url}")
            return None

        content_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
        if content_hash in self.seen_content:
            self.progress(f"[skip] duplicate content: {url}")
            return None
        self.seen_content.add(content_hash)

        return {"url": url, "title": title, "content": content, "links": links}

    def build_citation(self, title: str, url: str) -> str:
        site_name = up.urlsplit(url).netloc
        return f"{title}. {site_name}. Available at: {url} [Accessed {self.crawl_date_display}]."

    def write_page(self, page_data: Dict) -> str:
        """Write a page to disk and return the filename."""
        url = page_data["url"]
        title = page_data["title"]
        content = page_data["content"]

        filename = safe_filename(url, self.ext)
        output_path = os.path.join(self.out_dir, filename)
        citation = self.build_citation(title or "Untitled", url)
        with open(output_path, "w", encoding="utf-8") as output_file:
            if self.fmt == "markdown":
                header = f"# {title}\n\n" if title else ""
                meta = f"> URL: {url}\n> Crawled: {self.crawl_date_display}\n> Citation: {citation}\n\n"
            else:
                header = f"Title: {title}\n\n" if title else ""
                meta = f"URL: {url}\nCrawled: {self.crawl_date_display}\nCitation: {citation}\n\n"
            output_file.write(header + meta + content + "\n")
        return filename

    def build_jsonl_row(self, url: str, title: str, filename: str, content: str) -> str:
        return json.dumps(
            {
                "url": url,
                "title": title,
                "path": filename,
                "crawled_at": self.crawl_timestamp,
                "citation": self.build_citation(title or "Untitled", url),
                "tool": "markcrawl",
                "text": content,
            },
            ensure_ascii=False,
        ) + "\n"

    def save_page(self, page_data: Dict, jsonl_file) -> None:
        """Write page file, append JSONL row, increment counter."""
        url = page_data["url"]
        filename = self.write_page(page_data)
        jsonl_file.write(self.build_jsonl_row(url, page_data["title"], filename, page_data["content"]))
        self.saved_count += 1
        # Flush every 10 pages to reduce syscalls while still protecting against data loss
        if self.saved_count % 10 == 0:
            jsonl_file.flush()

        if self.total_planned:
            self.progress(f"[prog] saved {self.saved_count}/{self.total_planned} | queued={len(self.to_visit)}")
        else:
            self.progress(f"[prog] saved {self.saved_count} | queued={len(self.to_visit)}")

    def discover_links(self, url: str, links: Set[str], base_netloc: str) -> None:
        """Follow links from a crawled page (hybrid mode: sitemap seeds + link-following)."""
        if url not in self.visited_for_links:
            self.visited_for_links.add(url)
            for link in links:
                if link not in self.seen_urls and self.in_scope(link, base_netloc) and self.allowed(link):
                    self.to_visit.append(link)

    # -- Batch processing (unified for sequential & concurrent) -------------

    def _should_continue(self, max_pages: int) -> bool:
        return bool(self.to_visit) and (max_pages <= 0 or self.saved_count < max_pages) and not self.interrupted

    def _collect_batch(self, base_netloc: str, max_pages: int) -> List[str]:
        """Pop up to ``concurrency`` eligible URLs from the queue."""
        batch_size = max(1, self.concurrency)
        batch: List[str] = []
        while self.to_visit and len(batch) < batch_size:
            if max_pages > 0 and self.saved_count + len(batch) >= max_pages:
                break
            url = self.to_visit.popleft()
            if url in self.seen_urls:
                continue
            if not self.in_scope(url, base_netloc):
                continue
            if not self.allowed(url):
                self.progress(f"[skip] robots.txt disallowed: {url}")
                continue
            self.seen_urls.add(url)
            batch.append(url)
        return batch

    def _fetch_batch(self, batch: List[str]) -> Dict[str, Optional]:
        """Fetch a batch of URLs. Sequential if concurrency=1, parallel otherwise."""
        results: Dict[str, Optional] = {}

        if self.concurrency <= 1:
            for url in batch:
                self.progress(f"[get ] {url}")
                resp = self.fetch_page(url)
                results[url] = resp
                self._update_throttle(resp)
                if self._throttle.active_delay > 0:
                    time.sleep(self._throttle.active_delay)
        else:
            for url in batch:
                self.progress(f"[get ] {url}")
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                futures = {pool.submit(self.fetch_page, url): url for url in batch}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        resp = future.result()
                        results[url] = resp
                        self._update_throttle(resp)
                    except Exception as exc:
                        logger.warning("Fetch error for %s: %s", url, exc)
                        results[url] = None
            if self._throttle.active_delay > 0:
                time.sleep(self._throttle.active_delay)

        return results

    def run(self, base_netloc: str, max_pages: int, jsonl_file) -> None:
        """Main crawl loop. Processes batches until done, interrupted, or max_pages reached."""
        state_save_interval = 10

        if self.concurrency > 1:
            self.progress(f"[info] concurrent mode: {self.concurrency} workers")

        while self._should_continue(max_pages):
            batch = self._collect_batch(base_netloc, max_pages)
            if not batch:
                break

            responses = self._fetch_batch(batch)

            for url in batch:
                page_data = self.process_response(url, responses.get(url))
                if page_data is None:
                    continue
                self.save_page(page_data, jsonl_file)
                self.discover_links(url, page_data.get("links", set()), base_netloc)

            if self.saved_count % state_save_interval == 0:
                save_state(self.state_path, self.seen_urls, self.seen_content,
                           self.to_visit, self.saved_count, self.seeds,
                           self.visited_for_links)

        # Final flush to ensure all buffered writes are persisted
        jsonl_file.flush()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crawl(
    base_url: str,
    out_dir: str,
    use_sitemap: bool = True,
    delay: float = 0,
    timeout: int = 15,
    max_pages: int = 500,
    include_subdomains: bool = False,
    fmt: str = "markdown",
    show_progress: bool = False,
    min_words: int = 20,
    user_agent: Optional[str] = DEFAULT_UA,
    render_js: bool = False,
    concurrency: int = 1,
    proxy: Optional[str] = None,
    resume: bool = False,
    content_extractor: Optional[Callable[[str], Tuple[str, str]]] = None,
) -> CrawlResult:
    """Crawl a website and save cleaned content to disk.

    Orchestrates the full three-stage pipeline: URL discovery (sitemap-first,
    falling back to BFS link following), fetching and cleaning HTML, and
    writing Markdown/text files plus a JSONL index.

    Args:
        base_url: Seed URL and scope root (e.g. ``"https://example.com"``).
        out_dir: Directory where output files and ``pages.jsonl`` are written.
        use_sitemap: Attempt sitemap-based discovery before link following.
        delay: Politeness delay in seconds between requests (or batches).
        timeout: Per-request timeout in seconds.
        max_pages: Stop after saving this many pages (``0`` for unlimited).
        include_subdomains: Allow crawling subdomains of *base_url*'s host.
        fmt: Output format -- ``"markdown"`` or ``"text"``.
        show_progress: Print progress messages to stdout.
        min_words: Skip pages with fewer than this many words.
        user_agent: Custom User-Agent string; ``None`` uses the default.
        render_js: Use Playwright to render JavaScript before extraction.
        concurrency: Number of parallel fetch workers (``1`` for sequential).
        proxy: Optional HTTP/HTTPS proxy URL.
        resume: Resume a previously interrupted crawl from saved state.
        content_extractor: Optional custom function that takes raw HTML and
            returns a ``(title, content)`` tuple. When provided, this replaces
            the built-in extraction (html_to_markdown / html_to_text).

    Returns:
        A :class:`CrawlResult` with the count of saved pages, output
        directory path, and path to the JSONL index file.
    """
    # --- Input validation ---
    if not base_url or not isinstance(base_url, str):
        raise ValueError("base_url must be a non-empty string")
    parsed = up.urlsplit(base_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"base_url must use http or https, got {parsed.scheme!r}")
    if delay < 0:
        raise ValueError("delay must be >= 0")
    if timeout <= 0:
        raise ValueError("timeout must be > 0")
    if max_pages < 0:
        raise ValueError("max_pages must be >= 0")
    if concurrency <= 0:
        raise ValueError("concurrency must be > 0")
    if min_words < 0:
        raise ValueError("min_words must be >= 0")

    os.makedirs(out_dir, exist_ok=True)

    engine = CrawlEngine(
        out_dir=out_dir,
        fmt=fmt,
        min_words=min_words,
        delay=delay,
        timeout=timeout,
        concurrency=concurrency,
        include_subdomains=include_subdomains,
        user_agent=user_agent,
        render_js=render_js,
        proxy=proxy,
        show_progress=show_progress,
        content_extractor=content_extractor,
    )

    base_url = norm_url(base_url)
    base_netloc = up.urlsplit(base_url).netloc

    engine.setup_robots(base_url)

    # --- Resume from saved state ---
    resumed = False
    if resume:
        saved_state = load_state(engine.state_path)
        if saved_state:
            engine.seen_urls = set(saved_state["seen_urls"])
            engine.seen_content = set(saved_state["seen_content"])
            engine.to_visit = deque(saved_state["to_visit"])
            engine.saved_count = saved_state["saved_count"]
            engine.seeds = saved_state.get("seeds", [])
            engine.visited_for_links = set(saved_state.get("visited_for_links", []))
            resumed = True
            engine.progress(f"[info] resuming crawl: {engine.saved_count} page(s) already saved, {len(engine.to_visit)} queued")
        else:
            engine.progress("[info] no saved state found, starting fresh")

    if not resumed:
        if use_sitemap:
            for sitemap_url in discover_sitemaps(engine.session, base_url, robots_text=engine._robots_text):
                engine.seeds.extend(parse_sitemap_xml(engine.session, sitemap_url, timeout))
            engine.seeds = [norm_url(u) for u in engine.seeds if u]
            engine.seeds = [u for u in engine.seeds if engine.in_scope(u, base_netloc)]
            engine.seeds = [u for u in engine.seeds if engine.allowed(u)]
            for u in engine.seeds:
                engine.to_visit.append(u)
            if engine.seeds:
                engine.total_planned = len(engine.seeds)
                engine.progress(f"[info] sitemap discovered {engine.total_planned} in-scope page(s)")

        if not engine.to_visit:
            engine.to_visit.append(base_url)
            engine.progress("[info] no sitemap seeds available; using base URL as crawl seed")

    # Interrupt handler — save state on Ctrl+C
    original_sigint = signal.getsignal(signal.SIGINT)

    def _handle_interrupt(signum, frame):
        engine.interrupted = True
        engine.progress("\n[info] interrupt received — saving state and stopping...")

    signal.signal(signal.SIGINT, _handle_interrupt)

    jsonl_mode = "a" if resumed else "w"

    try:
        with open(engine.jsonl_path, jsonl_mode, encoding="utf-8") as jsonl_file:
            engine.run(base_netloc, max_pages, jsonl_file)
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        engine.close()

    # Save or clean up state
    if engine.interrupted or (engine.to_visit and max_pages > 0 and engine.saved_count >= max_pages):
        save_state(engine.state_path, engine.seen_urls, engine.seen_content,
                   engine.to_visit, engine.saved_count, engine.seeds,
                   engine.visited_for_links)
        engine.progress(f"[info] state saved to {engine.state_path} — use --resume to continue")
    else:
        if os.path.isfile(engine.state_path):
            os.remove(engine.state_path)

    logger.info("Saved %s HTML page(s) to %s", engine.saved_count, out_dir)
    return CrawlResult(pages_saved=engine.saved_count, output_dir=out_dir, index_file=engine.jsonl_path)
