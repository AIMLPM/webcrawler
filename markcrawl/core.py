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

import asyncio
import fnmatch
import hashlib
import json
import logging
import os
import random
import signal
import threading
import time
import urllib.parse as up
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple

from .dedup import DEDUP_FILENAME, PersistentDedup

# Submodule imports — all public names are re-exported for backward compatibility
from .extract_content import (
    EXCLUDE_TAGS,  # noqa: F401 — public re-export
    STRUCTURE_TAGS,  # noqa: F401 — public re-export
    clean_dom_for_content,  # noqa: F401 — public re-export
    compact_blank_lines,  # noqa: F401 — public re-export
    default_progress,
    html_to_markdown,
    html_to_markdown_ensemble,  # noqa: F401 — public re-export
    html_to_markdown_readerlm,  # noqa: F401 — public re-export
    html_to_markdown_trafilatura,  # noqa: F401 — public re-export
    html_to_text,
)
from .fetch import (
    DEFAULT_UA,
    PlaywrightResponse,  # noqa: F401 — public re-export
    _get_playwright_browser,
    build_async_session,
    build_session,
    fetch,
    fetch_async,
    fetch_with_playwright,
)
from .images import (
    ASSETS_DIR,
    extract_image_urls,
    rewrite_image_paths,
)
from .images import (
    download_images as _download_images,
)
from .link_scorer import LinkScorer
from .robots import (
    discover_sitemaps,
    parse_robots_txt,
    parse_robots_txt_async,
    parse_sitemap_xml,
    parse_sitemap_xml_async,
)
from .state import STATE_FILENAME, load_state, save_state
from .throttle import AdaptiveThrottle
from .urls import extract_links, norm_url, safe_filename, same_scope  # noqa: F401 — extract_links is a public re-export

logger = logging.getLogger(__name__)

# Backward-compat aliases for internal state functions
_save_state = save_state
_load_state = load_state


@dataclass
class PatternCluster:
    """A group of URLs sharing a common path pattern."""
    pattern: str
    urls: List[str]
    sampled: List[str]
    is_templated: bool


def smart_sample_urls(
    urls: List[str],
    threshold: int = 20,
    sample_size: int = 5,
    progress: Optional[Callable] = None,
) -> Tuple[List[str], List[PatternCluster]]:
    """Cluster URLs by path pattern and sample from large clusters.

    Returns ``(selected_urls, clusters)`` where *selected_urls* is the
    filtered list and *clusters* records what was discovered.
    """
    # Group by first path segment (the "section")
    buckets: Dict[str, List[str]] = defaultdict(list)
    for url in urls:
        path = up.urlsplit(url).path.strip("/")
        segments = path.split("/") if path else [""]
        key = "/" + segments[0] + "/*" if len(segments) > 1 else "/" + (segments[0] or "")
        buckets[key].append(url)

    selected: List[str] = []
    clusters: List[PatternCluster] = []

    for pattern, cluster_urls in sorted(buckets.items(), key=lambda x: -len(x[1])):
        if len(cluster_urls) > threshold:
            sampled = random.sample(cluster_urls, min(sample_size, len(cluster_urls)))
            selected.extend(sampled)
            clusters.append(PatternCluster(pattern, cluster_urls, sampled, is_templated=True))
        else:
            selected.extend(cluster_urls)
            clusters.append(PatternCluster(pattern, cluster_urls, cluster_urls, is_templated=False))

    if progress:
        progress("[info] Pattern Discovery:")
        for c in clusters:
            if c.is_templated:
                progress(f"  {c.pattern:40s} → {len(c.urls):>10,} URLs (sampled {len(c.sampled)})")
            else:
                progress(f"  {c.pattern:40s} → {len(c.urls):>10,} URLs (crawl all)")
        progress(f"  Total: {len(selected)} pages to fetch (from {len(urls)} discovered)")

    return selected, clusters


@dataclass
class PageData:
    """A single crawled page — available via ``CrawlResult.pages``."""
    url: str
    title: str
    content: str
    filename: str


@dataclass
class CrawlResult:
    pages_saved: int
    output_dir: str
    index_file: str
    pages: List[PageData]


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
        extractor: str = "default",
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        download_images: bool = False,
        min_image_size: int = 5000,
        i18n_filter: bool = False,
        title_at_top: bool = False,
    ):
        self.out_dir = out_dir
        self.fmt = fmt
        self.ext = "md" if fmt == "markdown" else "txt"
        self.min_words = min_words
        self.content_extractor = content_extractor
        self.extractor = extractor
        self.delay = delay
        self.timeout = timeout
        self.concurrency = concurrency
        self.include_subdomains = include_subdomains
        self.proxy = proxy
        self.i18n_filter = i18n_filter
        self.title_at_top = title_at_top
        self.show_progress = show_progress
        self.exclude_paths = exclude_paths or []
        self.include_paths = include_paths or []
        self.download_images = download_images
        self.min_image_size = min_image_size

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
            if self.concurrency > 1:
                logger.warning(
                    "--render-js forces concurrency=1 (Playwright is single-threaded, requested %d)",
                    self.concurrency,
                )
                self.progress(
                    f"[warn] --render-js forces concurrency=1 "
                    f"(Playwright is single-threaded, requested {self.concurrency})"
                )
                self.concurrency = 1
            self.pw_instance, self.pw_browser = _get_playwright_browser(proxy=proxy)
            self._pw_context = self.pw_browser.new_context(user_agent=self.effective_ua)
            if not download_images:
                # Block image resources — we only need HTML for markdown
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
        self._seed_urls: Set[str] = set()
        self.saved_count: int = 0
        self.total_planned: Optional[int] = None
        self.interrupted: bool = False
        self._cluster_map: Dict[str, Tuple[str, int, bool]] = {}
        self.collected_pages: List[PageData] = []

        # Cross-crawl dedup (loaded later if enabled)
        self._dedup: Optional[PersistentDedup] = None
        # Link prioritization scorer
        self._scorer: Optional[LinkScorer] = None

        # Paths
        self.jsonl_path = os.path.join(out_dir, "pages.jsonl")
        self.state_path = os.path.join(out_dir, STATE_FILENAME)
        self.dedup_path = os.path.join(out_dir, DEDUP_FILENAME)

    def enable_cross_dedup(self) -> None:
        """Load or create the persistent dedup index."""
        self._dedup = PersistentDedup(self.dedup_path)
        self.progress(f"[info] cross-crawl dedup: {self._dedup.size} known hashes loaded")

    def enable_link_scoring(self) -> None:
        """Enable link prioritization via content-yield scoring."""
        self._scorer = LinkScorer()
        self.progress("[info] link prioritization enabled")

    @property
    def throttle(self) -> "AdaptiveThrottle":
        """Public access to the throttle instance."""
        return self._throttle

    # -- Lifecycle ----------------------------------------------------------

    def close(self) -> None:
        """Release Playwright resources and save dedup state."""
        if self._dedup:
            self._dedup.save()
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

    def path_excluded(self, url: str) -> bool:
        """Check whether *url*'s path is excluded by path filters.

        A URL is excluded when it matches any ``exclude_paths`` pattern,
        or when ``include_paths`` is set and it matches none of them.
        Seed URLs (base URL fallback) bypass include filtering so we can
        still discover links from the entry point.
        """
        if self.i18n_filter:
            from .analyzer import i18n_path_excluded
            if i18n_path_excluded(url):
                return True
        path = up.urlsplit(url).path
        if self.exclude_paths and any(fnmatch.fnmatch(path, pat) for pat in self.exclude_paths):
            return True
        if self.include_paths and not any(fnmatch.fnmatch(path, pat) for pat in self.include_paths):
            return url not in self._seed_urls
        return False

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
        keep_imgs = self.download_images and self.fmt == "markdown"
        if self.content_extractor:
            title, content = self.content_extractor(response.text)
        elif self.fmt == "markdown":
            if self.extractor == "trafilatura":
                title, content, links = html_to_markdown_trafilatura(response.text, base_url=url)
            elif self.extractor == "ensemble":
                title, content, links = html_to_markdown_ensemble(response.text, base_url=url)
            elif self.extractor == "readerlm":
                title, content, links = html_to_markdown_readerlm(response.text, base_url=url)
            else:
                title, content, links = html_to_markdown(response.text, base_url=url, keep_images=keep_imgs)
        else:
            title, content, links = html_to_text(response.text, base_url=url)

        if not content:
            return None
        if len(content.split()) < self.min_words:
            self.progress(f"[skip] too little content: {url}")
            return None

        # Download images and rewrite markdown paths
        images: List[str] = []
        if keep_imgs:
            image_pairs = extract_image_urls(content)
            if image_pairs:
                assets_dir = os.path.join(self.out_dir, ASSETS_DIR)
                url_map = _download_images(
                    self.session, image_pairs, assets_dir,
                    self.timeout, self.min_image_size,
                )
                if url_map:
                    content = rewrite_image_paths(content, url_map)
                    images = [f"{ASSETS_DIR}/{fn}" for fn in url_map.values()]
                    self.progress(f"[img ] downloaded {len(url_map)} image(s) for {url}")

        content_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
        if content_hash in self.seen_content:
            self.progress(f"[skip] duplicate content: {url}")
            return None
        # Cross-crawl dedup check
        if self._dedup and self._dedup.check_and_add(content):
            self.progress(f"[skip] cross-crawl duplicate: {url}")
            return None
        self.seen_content.add(content_hash)

        return {"url": url, "title": title, "content": content, "links": links, "images": images}

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

    def build_jsonl_row(self, url: str, title: str, filename: str, content: str, images: Optional[List[str]] = None) -> str:
        text = content
        if self.title_at_top and title and not text.lstrip().startswith("# "):
            text = f"# {title}\n\n{text}"
        row = {
            "url": url,
            "title": title,
            "path": filename,
            "crawled_at": self.crawl_timestamp,
            "citation": self.build_citation(title or "Untitled", url),
            "tool": "markcrawl",
            "text": text,
        }
        if images:
            row["images"] = images
        if url in self._cluster_map:
            pattern, cluster_size, is_templated = self._cluster_map[url]
            row["pattern"] = pattern
            row["pattern_cluster_size"] = cluster_size
            row["is_sample"] = is_templated
        return json.dumps(row, ensure_ascii=False) + "\n"

    def save_page(self, page_data: Dict, jsonl_file) -> None:
        """Write page file, append JSONL row, increment counter."""
        url = page_data["url"]
        filename = self.write_page(page_data)
        images = page_data.get("images")
        jsonl_file.write(self.build_jsonl_row(url, page_data["title"], filename, page_data["content"], images=images))
        self.collected_pages.append(PageData(
            url=url, title=page_data["title"],
            content=page_data["content"], filename=filename,
        ))
        self._record_yield(url, page_data["content"])
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
            new_links = [
                link for link in links
                if (link not in self.seen_urls
                    and self.in_scope(link, base_netloc)
                    and self.allowed(link)
                    and not self.path_excluded(link))
            ]
            if self._scorer and new_links:
                # Insert prioritized links at the front of the queue
                new_links = self._scorer.prioritize(new_links)
                for link in reversed(new_links):
                    self.to_visit.appendleft(link)
            else:
                for link in new_links:
                    self.to_visit.append(link)

    def _record_yield(self, url: str, content: str) -> None:
        """Record content yield for link prioritization."""
        if self._scorer:
            self._scorer.record(url, len(content.split()))

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
            if self.path_excluded(url):
                self.progress(f"[skip] excluded path: {url}")
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
# AsyncCrawlEngine — native asyncio for zero-thread-overhead I/O
# ---------------------------------------------------------------------------

try:
    from .fetch import _HAS_HTTPX
except ImportError:
    _HAS_HTTPX = False


def _extract_content_worker(
    html_text: str, url: str, fmt: str, extractor: str,
    keep_images: bool = False,
) -> Optional[Tuple[str, str, Set[str]]]:
    """Extract content from HTML — runs in a :class:`ProcessPoolExecutor`.

    This is a module-level function (required for pickling across processes).
    """
    try:
        if fmt == "markdown":
            if extractor == "trafilatura":
                return html_to_markdown_trafilatura(html_text, base_url=url)
            elif extractor == "ensemble":
                return html_to_markdown_ensemble(html_text, base_url=url)
            elif extractor == "readerlm":
                return html_to_markdown_readerlm(html_text, base_url=url)
            else:
                return html_to_markdown(html_text, base_url=url, keep_images=keep_images)
        else:
            return html_to_text(html_text, base_url=url)
    except Exception:
        logger.warning("Extraction failed for %s", url, exc_info=True)
        return None


class AsyncCrawlEngine:
    """Async counterpart of :class:`CrawlEngine`.

    Uses ``httpx.AsyncClient`` with ``asyncio.gather`` and a semaphore for
    concurrency control.  Eliminates thread overhead and GIL contention,
    matching the I/O model that gives Scrapy (Twisted) its speed advantage.

    HTML-to-Markdown extraction — the main CPU bottleneck — runs in a
    :class:`ProcessPoolExecutor` to bypass the GIL and utilise multiple
    cores while the event loop continues managing I/O.
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
        proxy: Optional[str],
        show_progress: bool,
        content_extractor: Optional[Callable[[str], Tuple[str, str]]] = None,
        extractor: str = "default",
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        download_images: bool = False,
        min_image_size: int = 5000,
        i18n_filter: bool = False,
        title_at_top: bool = False,
    ):
        self.out_dir = out_dir
        self.fmt = fmt
        self.ext = "md" if fmt == "markdown" else "txt"
        self.min_words = min_words
        self.content_extractor = content_extractor
        self.extractor = extractor
        self.download_images = download_images
        self.min_image_size = min_image_size
        self.delay = delay
        self.timeout = timeout
        self.concurrency = concurrency
        self.include_subdomains = include_subdomains
        self.proxy = proxy
        self.show_progress = show_progress
        self.exclude_paths = exclude_paths or []
        self.include_paths = include_paths or []
        self.i18n_filter = i18n_filter
        self.title_at_top = title_at_top

        self.effective_ua = user_agent or DEFAULT_UA
        self.session = build_async_session(
            user_agent=self.effective_ua, proxy=proxy,
            pool_size=max(10, concurrency),
        )
        self.progress = default_progress(show_progress)

        # Semaphore limits in-flight requests
        self._sem = asyncio.Semaphore(concurrency)

        # Timestamps
        now = datetime.now(timezone.utc)
        self.crawl_timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.crawl_date_display = now.strftime("%B %d, %Y")

        # Adaptive throttle
        self._throttle = AdaptiveThrottle(delay, self.progress)

        # Process pool for CPU-bound HTML extraction (bypasses GIL)
        if content_extractor is None and concurrency >= 2:
            workers = min(os.cpu_count() or 2, concurrency)
            self._executor: Optional[ProcessPoolExecutor] = ProcessPoolExecutor(max_workers=workers)
        else:
            self._executor = None

        # Crawl state
        self.to_visit: Deque[str] = deque()
        self.seen_urls: Set[str] = set()
        self.seen_content: Set[str] = set()
        self.visited_for_links: Set[str] = set()
        self.seeds: List[str] = []
        self._seed_urls: Set[str] = set()
        self.saved_count: int = 0
        self.total_planned: Optional[int] = None
        self.interrupted: bool = False
        self._cluster_map: Dict[str, Tuple[str, int, bool]] = {}
        self.collected_pages: List[PageData] = []

        # Cross-crawl dedup (loaded later if enabled)
        self._dedup: Optional[PersistentDedup] = None
        # Link prioritization scorer
        self._scorer: Optional[LinkScorer] = None

        # Sync session for image downloads (async httpx can't be used in sync context)
        self._img_session = build_session(
            user_agent=self.effective_ua, proxy=proxy,
        ) if download_images else None

        # Paths
        self.jsonl_path = os.path.join(out_dir, "pages.jsonl")
        self.state_path = os.path.join(out_dir, STATE_FILENAME)
        self.dedup_path = os.path.join(out_dir, DEDUP_FILENAME)

    def enable_cross_dedup(self) -> None:
        """Load or create the persistent dedup index."""
        self._dedup = PersistentDedup(self.dedup_path)
        self.progress(f"[info] cross-crawl dedup: {self._dedup.size} known hashes loaded")

    def enable_link_scoring(self) -> None:
        """Enable link prioritization via content-yield scoring."""
        self._scorer = LinkScorer()
        self.progress("[info] link prioritization enabled")

    @property
    def throttle(self) -> "AdaptiveThrottle":
        return self._throttle

    async def close(self) -> None:
        if self._dedup:
            self._dedup.save()
        await self.session.aclose()
        if self._executor:
            self._executor.shutdown(wait=False)

    # -- Robots / scope -----------------------------------------------------

    async def setup_robots(self, base_url: str) -> None:
        self._rp, self._robots_text = await parse_robots_txt_async(
            self.session, up.urljoin(base_url, "/robots.txt"),
        )
        crawl_delay = AdaptiveThrottle.parse_crawl_delay(self._robots_text, self.effective_ua)
        if crawl_delay is not None and crawl_delay > self._throttle.base_delay:
            self._throttle.base_delay = crawl_delay
            self.progress(f"[info] robots.txt Crawl-delay: {crawl_delay}s")

    def allowed(self, url: str) -> bool:
        try:
            return self._rp.can_fetch(self.effective_ua, url)
        except Exception:
            return True

    def in_scope(self, url: str, base_netloc: str) -> bool:
        return same_scope(url, base_netloc, self.include_subdomains)

    def path_excluded(self, url: str) -> bool:
        """Check whether *url*'s path is excluded by path filters.

        A URL is excluded when it matches any ``exclude_paths`` pattern,
        or when ``include_paths`` is set and it matches none of them.
        Seed URLs (base URL fallback) bypass include filtering so we can
        still discover links from the entry point.
        """
        if self.i18n_filter:
            from .analyzer import i18n_path_excluded
            if i18n_path_excluded(url):
                return True
        path = up.urlsplit(url).path
        if self.exclude_paths and any(fnmatch.fnmatch(path, pat) for pat in self.exclude_paths):
            return True
        if self.include_paths and not any(fnmatch.fnmatch(path, pat) for pat in self.include_paths):
            return url not in self._seed_urls
        return False

    # -- Fetching -----------------------------------------------------------

    async def fetch_page(self, url: str):
        """Fetch a single page through the semaphore."""
        async with self._sem:
            return await fetch_async(self.session, url, self.timeout)

    # -- Processing ---------------------------------------------------------

    def process_response(self, url: str, response) -> Optional[Dict]:
        """Sync extraction — used by the benchmark runner and fallback paths."""
        if not (response and getattr(response, "is_success", getattr(response, "ok", False))):
            return None

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            self.progress(f"[skip] non-HTML content: {url}")
            return None

        keep_imgs = self.download_images and self.fmt == "markdown"
        links: Set[str] = set()
        if self.content_extractor:
            title, content = self.content_extractor(response.text)
        elif self.fmt == "markdown":
            if self.extractor == "trafilatura":
                title, content, links = html_to_markdown_trafilatura(response.text, base_url=url)
            elif self.extractor == "ensemble":
                title, content, links = html_to_markdown_ensemble(response.text, base_url=url)
            elif self.extractor == "readerlm":
                title, content, links = html_to_markdown_readerlm(response.text, base_url=url)
            else:
                title, content, links = html_to_markdown(response.text, base_url=url, keep_images=keep_imgs)
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
        if self._dedup and self._dedup.check_and_add(content):
            self.progress(f"[skip] cross-crawl duplicate: {url}")
            return None
        self.seen_content.add(content_hash)

        return {"url": url, "title": title, "content": content, "links": links}

    async def _extract_response(
        self, url: str, response,
    ) -> Optional[Tuple[str, str, Set[str]]]:
        """Extract content from a response, using the process pool when available.

        Returns ``(title, content, links)`` or *None*.  Dedup is **not**
        performed here — the caller must check ``seen_content``.
        """
        if not (response and getattr(response, "is_success", getattr(response, "ok", False))):
            return None

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            self.progress(f"[skip] non-HTML content: {url}")
            return None

        html_text = response.text

        if self.content_extractor:
            title, content = self.content_extractor(html_text)
            return title, content, set()

        keep_imgs = self.download_images and self.fmt == "markdown"
        if self._executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self._executor,
                _extract_content_worker, html_text, url, self.fmt, self.extractor,
                keep_imgs,
            )
            return result

        return _extract_content_worker(html_text, url, self.fmt, self.extractor, keep_images=keep_imgs)

    def build_citation(self, title: str, url: str) -> str:
        site_name = up.urlsplit(url).netloc
        return f"{title}. {site_name}. Available at: {url} [Accessed {self.crawl_date_display}]."

    def write_page(self, page_data: Dict) -> str:
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

    def build_jsonl_row(self, url: str, title: str, filename: str, content: str, images: Optional[List[str]] = None) -> str:
        text = content
        if self.title_at_top and title and not text.lstrip().startswith("# "):
            text = f"# {title}\n\n{text}"
        row = {
            "url": url,
            "title": title,
            "path": filename,
            "crawled_at": self.crawl_timestamp,
            "citation": self.build_citation(title or "Untitled", url),
            "tool": "markcrawl",
            "text": text,
        }
        if images:
            row["images"] = images
        if url in self._cluster_map:
            pattern, cluster_size, is_templated = self._cluster_map[url]
            row["pattern"] = pattern
            row["pattern_cluster_size"] = cluster_size
            row["is_sample"] = is_templated
        return json.dumps(row, ensure_ascii=False) + "\n"

    def save_page(self, page_data: Dict, jsonl_file) -> None:
        url = page_data["url"]
        filename = self.write_page(page_data)
        images = page_data.get("images")
        jsonl_file.write(self.build_jsonl_row(url, page_data["title"], filename, page_data["content"], images=images))
        self.collected_pages.append(PageData(
            url=url, title=page_data["title"],
            content=page_data["content"], filename=filename,
        ))
        self._record_yield(url, page_data["content"])
        self.saved_count += 1
        if self.saved_count % 10 == 0:
            jsonl_file.flush()
        if self.total_planned:
            self.progress(f"[prog] saved {self.saved_count}/{self.total_planned} | queued={len(self.to_visit)}")
        else:
            self.progress(f"[prog] saved {self.saved_count} | queued={len(self.to_visit)}")

    def discover_links(self, url: str, links: Set[str], base_netloc: str) -> None:
        if url not in self.visited_for_links:
            self.visited_for_links.add(url)
            new_links = [
                link for link in links
                if (link not in self.seen_urls
                    and self.in_scope(link, base_netloc)
                    and self.allowed(link)
                    and not self.path_excluded(link))
            ]
            if self._scorer and new_links:
                new_links = self._scorer.prioritize(new_links)
                for link in reversed(new_links):
                    self.to_visit.appendleft(link)
            else:
                for link in new_links:
                    self.to_visit.append(link)

    def _record_yield(self, url: str, content: str) -> None:
        """Record content yield for link prioritization."""
        if self._scorer:
            self._scorer.record(url, len(content.split()))

    # -- Batch processing (async) -------------------------------------------

    def _should_continue(self, max_pages: int) -> bool:
        return bool(self.to_visit) and (max_pages <= 0 or self.saved_count < max_pages) and not self.interrupted

    def _collect_batch(self, base_netloc: str, max_pages: int) -> List[str]:
        batch_size = max(1, self.concurrency * 2)
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
            if self.path_excluded(url):
                self.progress(f"[skip] excluded path: {url}")
                continue
            self.seen_urls.add(url)
            batch.append(url)
        return batch

    async def _fetch_batch(self, batch: List[str]) -> Dict[str, Optional]:
        """Fetch all URLs in the batch concurrently via asyncio.gather."""
        for url in batch:
            self.progress(f"[get ] {url}")

        tasks = [self.fetch_page(url) for url in batch]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results: Dict[str, Optional] = {}
        for url, result in zip(batch, results_list):
            if isinstance(result, Exception):
                logger.warning("Fetch error for %s: %s", url, result)
                results[url] = None
            else:
                results[url] = result
                self._throttle.update(result)

        if self._throttle.active_delay > 0:
            await asyncio.sleep(self._throttle.active_delay)

        return results

    async def run(self, base_netloc: str, max_pages: int, jsonl_file) -> None:
        """Main async crawl loop.

        Fetches a batch of URLs concurrently, then extracts content in
        parallel via the process pool.  Dedup, save, and link discovery
        remain sequential (fast, and must be single-threaded).
        """
        state_save_interval = 10

        if self.concurrency > 1:
            pool_info = f", {self._executor._max_workers} extraction workers" if self._executor else ""
            self.progress(f"[info] async mode: {self.concurrency} concurrent requests{pool_info}")

        while self._should_continue(max_pages):
            batch = self._collect_batch(base_netloc, max_pages)
            if not batch:
                break

            # Phase 1: fetch concurrently (I/O-bound, event loop)
            responses = await self._fetch_batch(batch)

            # Phase 2: extract concurrently (CPU-bound, process pool)
            extract_tasks = [
                self._extract_response(url, responses.get(url))
                for url in batch
            ]
            extracted = await asyncio.gather(*extract_tasks, return_exceptions=True)

            # Phase 3: dedup + save + discover (sequential, fast)
            keep_imgs = self.download_images and self.fmt == "markdown"
            for url, result in zip(batch, extracted):
                if isinstance(result, (Exception, type(None))):
                    if isinstance(result, Exception):
                        logger.warning("Extraction error for %s: %s", url, result)
                    continue

                title, content, links = result
                if not content or len(content.split()) < self.min_words:
                    self.progress(f"[skip] too little content: {url}")
                    continue

                # Download images and rewrite markdown paths
                images: List[str] = []
                if keep_imgs and self._img_session:
                    image_pairs = extract_image_urls(content)
                    if image_pairs:
                        assets_dir = os.path.join(self.out_dir, ASSETS_DIR)
                        url_map = _download_images(
                            self._img_session, image_pairs, assets_dir,
                            self.timeout, self.min_image_size,
                        )
                        if url_map:
                            content = rewrite_image_paths(content, url_map)
                            images = [f"{ASSETS_DIR}/{fn}" for fn in url_map.values()]
                            self.progress(f"[img ] downloaded {len(url_map)} image(s) for {url}")

                content_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
                if content_hash in self.seen_content:
                    self.progress(f"[skip] duplicate content: {url}")
                    continue
                if self._dedup and self._dedup.check_and_add(content):
                    self.progress(f"[skip] cross-crawl duplicate: {url}")
                    continue
                self.seen_content.add(content_hash)

                page_data = {"url": url, "title": title, "content": content, "links": links, "images": images}
                self.save_page(page_data, jsonl_file)
                self.discover_links(url, links, base_netloc)

            if self.saved_count % state_save_interval == 0:
                save_state(self.state_path, self.seen_urls, self.seen_content,
                           self.to_visit, self.saved_count, self.seeds,
                           self.visited_for_links)

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
    extractor: str = "default",
    exclude_paths: Optional[List[str]] = None,
    include_paths: Optional[List[str]] = None,
    dry_run: bool = False,
    smart_sample: bool = False,
    sample_size: int = 5,
    sample_threshold: int = 20,
    cross_dedup: bool = False,
    prioritize_links: bool = False,
    download_images: bool = False,
    min_image_size: int = 5000,
    i18n_filter: bool = False,
    title_at_top: bool = False,
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
        extractor: Built-in extraction backend -- ``"default"`` (BS4 + markdownify),
            ``"trafilatura"`` (higher recall), or ``"ensemble"`` (runs both,
            picks best per page). Trafilatura options require
            ``pip install trafilatura``.
        exclude_paths: List of glob patterns to exclude by URL path
            (e.g. ``["/job/*", "/careers/*"]``).
        include_paths: List of glob patterns to *include* by URL path.
            When set, only URLs matching at least one pattern are crawled
            (e.g. ``["/blog/*", "/pricing"]``).  Exclude takes priority.
        dry_run: Only run URL discovery (sitemap + initial page links),
            print the URL list, and exit without fetching content.
        smart_sample: Auto-detect templated URL patterns and sample from
            large clusters instead of crawling every instance.
        sample_size: Number of pages to sample from each templated cluster
            (default: 5).  Only used when ``smart_sample=True``.
        sample_threshold: Clusters with more URLs than this are considered
            templated and sampled (default: 20).
        download_images: Download images from the content area and save
            to an ``assets/`` subdirectory.  Markdown output uses local
            paths instead of ``[Image: alt]`` placeholders.
        min_image_size: Minimum image file size in bytes (default: 5000).
            Smaller images (icons, spacers) are skipped.

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

    # Use async engine when httpx is available and JS rendering is off.
    # Async eliminates thread overhead and GIL contention — matching the
    # event-loop model that gives Scrapy/Twisted its speed advantage.
    use_async = _HAS_HTTPX and not render_js

    if use_async:
        return _crawl_async(
            base_url=base_url, out_dir=out_dir, use_sitemap=use_sitemap,
            delay=delay, timeout=timeout, max_pages=max_pages,
            include_subdomains=include_subdomains, fmt=fmt,
            show_progress=show_progress, min_words=min_words,
            user_agent=user_agent, concurrency=concurrency,
            proxy=proxy, resume=resume, content_extractor=content_extractor,
            extractor=extractor, exclude_paths=exclude_paths,
            include_paths=include_paths, dry_run=dry_run,
            smart_sample=smart_sample, sample_size=sample_size,
            sample_threshold=sample_threshold,
            cross_dedup=cross_dedup,
            prioritize_links=prioritize_links,
            download_images=download_images,
            min_image_size=min_image_size,
            i18n_filter=i18n_filter,
            title_at_top=title_at_top,
        )

    return _crawl_sync(
        base_url=base_url, out_dir=out_dir, use_sitemap=use_sitemap,
        delay=delay, timeout=timeout, max_pages=max_pages,
        include_subdomains=include_subdomains, fmt=fmt,
        show_progress=show_progress, min_words=min_words,
        user_agent=user_agent, render_js=render_js,
        concurrency=concurrency, proxy=proxy, resume=resume,
        content_extractor=content_extractor, extractor=extractor,
        exclude_paths=exclude_paths, include_paths=include_paths,
        dry_run=dry_run, smart_sample=smart_sample,
        sample_size=sample_size, sample_threshold=sample_threshold,
        cross_dedup=cross_dedup, prioritize_links=prioritize_links,
        download_images=download_images, min_image_size=min_image_size,
        i18n_filter=i18n_filter, title_at_top=title_at_top,
    )


def _crawl_sync(
    base_url: str,
    out_dir: str,
    use_sitemap: bool,
    delay: float,
    timeout: int,
    max_pages: int,
    include_subdomains: bool,
    fmt: str,
    show_progress: bool,
    min_words: int,
    user_agent: Optional[str],
    render_js: bool,
    concurrency: int,
    proxy: Optional[str],
    resume: bool,
    content_extractor: Optional[Callable[[str], Tuple[str, str]]],
    extractor: str,
    exclude_paths: Optional[List[str]] = None,
    include_paths: Optional[List[str]] = None,
    dry_run: bool = False,
    smart_sample: bool = False,
    sample_size: int = 5,
    sample_threshold: int = 20,
    cross_dedup: bool = False,
    prioritize_links: bool = False,
    download_images: bool = False,
    min_image_size: int = 5000,
    i18n_filter: bool = False,
    title_at_top: bool = False,
) -> CrawlResult:
    """Synchronous crawl path using ThreadPoolExecutor."""
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
        extractor=extractor,
        exclude_paths=exclude_paths,
        include_paths=include_paths,
        download_images=download_images,
        min_image_size=min_image_size,
        i18n_filter=i18n_filter,
        title_at_top=title_at_top,
    )

    base_url = norm_url(base_url)
    base_netloc = up.urlsplit(base_url).netloc

    if cross_dedup:
        engine.enable_cross_dedup()
    if prioritize_links:
        engine.enable_link_scoring()

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
            engine.seeds = [u for u in engine.seeds if not engine.path_excluded(u)]
            for u in engine.seeds:
                engine.to_visit.append(u)
            if engine.seeds:
                engine.total_planned = len(engine.seeds)
                engine.progress(f"[info] sitemap discovered {engine.total_planned} in-scope page(s)")

        if not engine.to_visit:
            engine.to_visit.append(base_url)
            engine._seed_urls.add(base_url)
            engine.progress("[info] no sitemap seeds available; using base URL as crawl seed")

    # --- Smart sampling: cluster and sample from templated patterns ---
    if smart_sample and len(engine.to_visit) > 0:
        sampled, engine._clusters = smart_sample_urls(
            list(engine.to_visit), threshold=sample_threshold,
            sample_size=sample_size, progress=engine.progress,
        )
        engine.to_visit = deque(sampled)
        engine.total_planned = len(sampled)
        # Build lookup for JSONL metadata
        engine._sample_urls = set(sampled)
        engine._cluster_map = {}
        for c in engine._clusters:
            for u in c.sampled:
                engine._cluster_map[u] = (c.pattern, len(c.urls), c.is_templated)

    # --- Dry run: print discovered URLs and exit ---
    if dry_run:
        urls = list(engine.to_visit)
        engine.close()
        for u in urls:
            print(u)
        engine.progress(f"[dry-run] {len(urls)} URL(s) discovered — exiting without fetching")
        return CrawlResult(pages_saved=0, output_dir=out_dir, index_file=engine.jsonl_path, pages=[])

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
    return CrawlResult(pages_saved=engine.saved_count, output_dir=out_dir, index_file=engine.jsonl_path, pages=engine.collected_pages)


def _crawl_async(
    base_url: str,
    out_dir: str,
    use_sitemap: bool,
    delay: float,
    timeout: int,
    max_pages: int,
    include_subdomains: bool,
    fmt: str,
    show_progress: bool,
    min_words: int,
    user_agent: Optional[str],
    concurrency: int,
    proxy: Optional[str],
    resume: bool,
    content_extractor: Optional[Callable[[str], Tuple[str, str]]],
    extractor: str,
    exclude_paths: Optional[List[str]] = None,
    include_paths: Optional[List[str]] = None,
    dry_run: bool = False,
    smart_sample: bool = False,
    sample_size: int = 5,
    sample_threshold: int = 20,
    cross_dedup: bool = False,
    prioritize_links: bool = False,
    download_images: bool = False,
    min_image_size: int = 5000,
    i18n_filter: bool = False,
    title_at_top: bool = False,
) -> CrawlResult:
    """Async crawl path using native asyncio event loop."""

    async def _run() -> CrawlResult:
        engine = AsyncCrawlEngine(
            out_dir=out_dir,
            fmt=fmt,
            min_words=min_words,
            delay=delay,
            timeout=timeout,
            concurrency=concurrency,
            include_subdomains=include_subdomains,
            user_agent=user_agent,
            proxy=proxy,
            show_progress=show_progress,
            content_extractor=content_extractor,
            extractor=extractor,
            exclude_paths=exclude_paths,
            include_paths=include_paths,
            download_images=download_images,
            min_image_size=min_image_size,
            i18n_filter=i18n_filter,
            title_at_top=title_at_top,
        )

        nonlocal base_url
        base_url = norm_url(base_url)
        base_netloc = up.urlsplit(base_url).netloc

        if cross_dedup:
            engine.enable_cross_dedup()

        await engine.setup_robots(base_url)

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
                robots_text = engine._robots_text
                sitemaps: List[str] = []
                for line in robots_text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        if sitemap_url:
                            sitemaps.append(sitemap_url)

                for sitemap_url in sitemaps:
                    engine.seeds.extend(await parse_sitemap_xml_async(
                        engine.session, sitemap_url, timeout,
                    ))
                engine.seeds = [norm_url(u) for u in engine.seeds if u]
                engine.seeds = [u for u in engine.seeds if engine.in_scope(u, base_netloc)]
                engine.seeds = [u for u in engine.seeds if engine.allowed(u)]
                engine.seeds = [u for u in engine.seeds if not engine.path_excluded(u)]
                for u in engine.seeds:
                    engine.to_visit.append(u)
                if engine.seeds:
                    engine.total_planned = len(engine.seeds)
                    engine.progress(f"[info] sitemap discovered {engine.total_planned} in-scope page(s)")

            if not engine.to_visit:
                engine.to_visit.append(base_url)
                engine._seed_urls.add(base_url)
                engine.progress("[info] no sitemap seeds available; using base URL as crawl seed")

        # --- Smart sampling: cluster and sample from templated patterns ---
        if smart_sample and len(engine.to_visit) > 0:
            sampled, engine._clusters = smart_sample_urls(
                list(engine.to_visit), threshold=sample_threshold,
                sample_size=sample_size, progress=engine.progress,
            )
            engine.to_visit = deque(sampled)
            engine.total_planned = len(sampled)
            # Build lookup for JSONL metadata
            engine._sample_urls = set(sampled)
            engine._cluster_map = {}
            for c in engine._clusters:
                for u in c.sampled:
                    engine._cluster_map[u] = (c.pattern, len(c.urls), c.is_templated)

        # --- Dry run: print discovered URLs and exit ---
        if dry_run:
            urls = list(engine.to_visit)
            await engine.close()
            for u in urls:
                print(u)
            engine.progress(f"[dry-run] {len(urls)} URL(s) discovered — exiting without fetching")
            return CrawlResult(pages_saved=0, output_dir=out_dir, index_file=engine.jsonl_path, pages=[])

        # Interrupt handler
        original_sigint = signal.getsignal(signal.SIGINT)

        def _handle_interrupt(signum, frame):
            engine.interrupted = True
            engine.progress("\n[info] interrupt received — saving state and stopping...")

        signal.signal(signal.SIGINT, _handle_interrupt)

        jsonl_mode = "a" if resumed else "w"

        try:
            with open(engine.jsonl_path, jsonl_mode, encoding="utf-8") as jsonl_file:
                await engine.run(base_netloc, max_pages, jsonl_file)
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            await engine.close()

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
        return CrawlResult(pages_saved=engine.saved_count, output_dir=out_dir, index_file=engine.jsonl_path, pages=engine.collected_pages)

    return asyncio.run(_run())
