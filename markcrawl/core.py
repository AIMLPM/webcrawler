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
import re
import signal
import time
import urllib.parse as up
import xml.etree.ElementTree as ET
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple
from urllib import robotparser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import MarkcrawlDependencyError

try:
    import certifi
    CERT_PATH: str | bool = certifi.where()
except Exception:
    CERT_PATH = True

try:
    from markdownify import markdownify as md_convert
except Exception:
    md_convert = None

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; MarkCrawl/0.1; +https://github.com/AIMLPM/markcrawl) "
    "Python-requests"
)

EXCLUDE_TAGS = {"script", "style", "noscript", "template", "svg", "canvas"}
STRUCTURE_TAGS = {"nav", "header", "footer", "aside"}

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    pages_saved: int
    output_dir: str
    index_file: str


# ---------------------------------------------------------------------------
# Session / fetch helpers
# ---------------------------------------------------------------------------

def build_session(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
) -> requests.Session:
    """Create a ``requests.Session`` pre-configured for crawling.

    Args:
        user_agent: User-Agent header string sent with every request.
        proxy: Optional HTTP/HTTPS proxy URL (e.g. ``"http://proxy:8080"``).

    Returns:
        A configured ``requests.Session`` ready for use with :func:`fetch`.
    """
    session = requests.Session()
    session.verify = CERT_PATH
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        }
    )
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch(session: requests.Session, url: str, timeout: int) -> Optional[requests.Response]:
    """Perform an HTTP GET request, returning the response or ``None`` on failure.

    Args:
        session: A ``requests.Session`` (typically from :func:`build_session`).
        url: The fully-qualified URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        A ``requests.Response`` on success, or ``None`` if the request raised
        an exception.
    """
    try:
        return session.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        logger.warning("Fetch error for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Playwright (optional) — JS rendering
# ---------------------------------------------------------------------------

def _get_playwright_browser(proxy: Optional[str] = None):
    """Launch a Playwright Chromium browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise MarkcrawlDependencyError(
            "Playwright is required for --render-js.\n"
            "Install it with:  pip install playwright && playwright install chromium"
        )
    pw = sync_playwright().start()
    launch_args: Dict = {}
    if proxy:
        launch_args["proxy"] = {"server": proxy}
    browser = pw.chromium.launch(headless=True, **launch_args)
    return pw, browser


@dataclass
class PlaywrightResponse:
    """Minimal response object matching what the crawl loop needs."""
    ok: bool
    status_code: int
    text: str
    headers: Dict[str, str]


def fetch_with_playwright(browser, url: str, timeout: int, user_agent: str) -> Optional[PlaywrightResponse]:
    """Fetch a URL using Playwright, returning rendered HTML."""
    context = None
    try:
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        response = page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
        if response is None:
            return None
        html = page.content()
        headers = {k.lower(): v for k, v in response.headers.items()}
        return PlaywrightResponse(
            ok=response.ok,
            status_code=response.status,
            text=html,
            headers=headers,
        )
    except Exception as exc:
        logger.warning("Playwright fetch error for %s: %s", url, exc)
        return None
    finally:
        if context:
            context.close()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def norm_url(url: str) -> str:
    """Normalise a URL for deduplication.

    Lowercases the scheme and netloc, ensures the path is at least ``"/"``,
    strips the fragment, and collapses consecutive slashes.
    """
    p = up.urlsplit(url)
    # Negative lookbehind preserves :// in scheme
    normalized = up.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))
    normalized = re.sub(r"(?<!:)/{2,}", "/", normalized)
    return normalized


def same_scope(url: str, base_netloc: str, include_subdomains: bool) -> bool:
    """Check whether *url* falls within the allowed crawl scope."""
    target = up.urlsplit(url).netloc.lower()
    base = base_netloc.lower()
    if target == base:
        return True
    return include_subdomains and target.endswith("." + base)


def safe_filename(url: str, ext: str) -> str:
    """Derive a filesystem-safe filename from a URL with a hash suffix for collision avoidance."""
    p = up.urlsplit(url)
    path = p.path.strip("/")
    if not path:
        stub = "index"
    else:
        stub = re.sub(r"[^a-zA-Z0-9._-]+", "-", path)[:120].strip("-") or "page"
    if p.query:
        qpart = re.sub(r"[^a-zA-Z0-9._-]+", "-", p.query)[:40].strip("-")
        if qpart:
            stub += f"__{qpart}"
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{stub}__{h}.{ext}"


# ---------------------------------------------------------------------------
# Robots / sitemap
# ---------------------------------------------------------------------------

def parse_robots_txt(session: requests.Session, robots_url: str) -> Tuple[robotparser.RobotFileParser, str]:
    """Fetch and parse robots.txt, returning both the parser and raw text."""
    rp = robotparser.RobotFileParser()
    try:
        response = session.get(robots_url, timeout=10)
        content = response.text if response.ok else ""
    except requests.RequestException:
        content = ""
    rp.parse(content.splitlines())
    return rp, content


def discover_sitemaps(session: requests.Session, base: str, robots_text: Optional[str] = None) -> List[str]:
    """Find sitemap URLs declared in the site's ``robots.txt``.

    If *robots_text* is provided, it is parsed directly instead of
    re-fetching ``/robots.txt`` (avoids a duplicate HTTP request when
    ``parse_robots_txt`` has already fetched it).
    """
    if robots_text is None:
        robots_url = up.urljoin(base, "/robots.txt")
        try:
            response = session.get(robots_url, timeout=10)
            if not response.ok:
                return []
            robots_text = response.text
        except requests.RequestException:
            return []

    sitemaps: List[str] = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            sitemap_url = line.split(":", 1)[1].strip()
            if sitemap_url:
                sitemaps.append(sitemap_url)
    return sitemaps


def parse_sitemap_xml(session: requests.Session, url: str, timeout: int) -> List[str]:
    """Recursively parse a sitemap XML and return all page URLs."""
    try:
        response = session.get(url, timeout=timeout)
        if not response.ok:
            return []
        content_type = response.headers.get("content-type", "").lower()
        if not (content_type.startswith("application/xml") or response.text.strip().startswith("<")):
            return []
        root = ET.fromstring(response.content)
    except Exception:
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: List[str] = []

    for loc in root.findall(".//sm:sitemap/sm:loc", ns):
        child_url = (loc.text or "").strip()
        if child_url:
            urls.extend(parse_sitemap_xml(session, child_url, timeout))

    for loc in root.findall(".//sm:url/sm:loc", ns):
        page_url = (loc.text or "").strip()
        if page_url:
            urls.append(page_url)

    if not urls:
        for loc in root.findall(".//loc"):
            page_url = (loc.text or "").strip()
            if page_url:
                urls.append(page_url)

    return list(dict.fromkeys(urls))


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------

def extract_links(html: str, base_url: str) -> Set[str]:
    """Extract and normalise all ``<a href>`` links from an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    links: Set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        absolute_url = up.urljoin(base_url, href)
        links.add(norm_url(absolute_url))
    return links


def clean_dom_for_content(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(EXCLUDE_TAGS):
        tag.decompose()
    for tag in soup.find_all(STRUCTURE_TAGS):
        tag.decompose()
    for el in soup.select(
        '[role="navigation"], [aria-hidden="true"], .sr-only, .visually-hidden, .cookie, .Cookie, .cookie-banner, .consent'
    ):
        try:
            el.decompose()
        except Exception:
            pass


def compact_blank_lines(text: str, max_blank_streak: int = 2) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    output: List[str] = []
    blank_streak = 0
    for line in lines:
        if line.strip():
            blank_streak = 0
            output.append(line)
        else:
            blank_streak += 1
            if blank_streak <= max_blank_streak:
                output.append("")
    return "\n".join(output).strip()


def html_to_markdown(html: str) -> Tuple[str, str]:
    """Convert raw HTML to cleaned Markdown text."""
    soup = BeautifulSoup(html, "html.parser")
    clean_dom_for_content(soup)
    title = (soup.title.string or "").strip() if soup.title else ""
    main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    html_fragment = str(main)

    if md_convert:
        markdown = md_convert(
            html_fragment,
            heading_style="ATX",
            strip=["img"],
            wrap=False,
            bullets="*",
            escape_asterisks=False,
            escape_underscores=False,
            code_language=False,
        )
    else:
        markdown = BeautifulSoup(html_fragment, "html.parser").get_text("\n")

    return title, compact_blank_lines(markdown)


def html_to_text(html: str) -> Tuple[str, str]:
    """Convert raw HTML to cleaned plain text."""
    soup = BeautifulSoup(html, "html.parser")
    clean_dom_for_content(soup)
    title = (soup.title.string or "").strip() if soup.title else ""
    text = soup.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    deduped: List[str] = []
    previous: Optional[str] = None
    for line in lines:
        if line != previous:
            deduped.append(line)
        previous = line
    return title, "\n".join(deduped).strip()


def default_progress(enabled: bool) -> Callable[[str], None]:
    def emit(message: str) -> None:
        if enabled:
            print(message)
    return emit


# ---------------------------------------------------------------------------
# Crawl state persistence (resume support)
# ---------------------------------------------------------------------------

STATE_FILENAME = ".crawl_state.json"


def _save_state(
    state_path: str,
    seen_urls: Set[str],
    seen_content: Set[str],
    to_visit: Deque[str],
    saved_count: int,
    seeds: List[str],
) -> None:
    state = {
        "seen_urls": list(seen_urls),
        "seen_content": list(seen_content),
        "to_visit": list(to_visit),
        "saved_count": saved_count,
        "seeds": seeds,
    }
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, state_path)


def _load_state(state_path: str) -> Optional[Dict]:
    if not os.path.isfile(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


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
        self.session = build_session(user_agent=self.effective_ua, proxy=proxy)
        self.progress = default_progress(show_progress)

        # Playwright (optional)
        self.pw_instance = None
        self.pw_browser = None
        if render_js:
            self.pw_instance, self.pw_browser = _get_playwright_browser(proxy=proxy)
            self.progress("[info] Playwright browser launched for JS rendering")

        # Timestamps
        now = datetime.now(timezone.utc)
        self.crawl_timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.crawl_date_display = now.strftime("%B %d, %Y")

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

    # -- Lifecycle ----------------------------------------------------------

    def close(self) -> None:
        """Release Playwright resources."""
        if self.pw_browser:
            self.pw_browser.close()
        if self.pw_instance:
            self.pw_instance.stop()

    # -- Robots / scope -----------------------------------------------------

    def setup_robots(self, base_url: str) -> None:
        self._rp, self._robots_text = parse_robots_txt(self.session, up.urljoin(base_url, "/robots.txt"))

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
        if self.pw_browser:
            return fetch_with_playwright(self.pw_browser, url, self.timeout, self.effective_ua)
        return fetch(self.session, url, self.timeout)

    # -- Processing (main thread only) --------------------------------------

    def process_response(self, url: str, response) -> Optional[Dict]:
        """Validate response and extract content. Returns page_data or None.

        IMPORTANT: This method mutates ``seen_content`` and must only be called
        from the main thread.
        """
        if not (response and response.ok):
            return None

        # requests normalizes headers to case-insensitive access
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            self.progress(f"[skip] non-HTML content: {url}")
            return None

        if self.content_extractor:
            title, content = self.content_extractor(response.text)
        elif self.fmt == "markdown":
            title, content = html_to_markdown(response.text)
        else:
            title, content = html_to_text(response.text)

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

        return {"url": url, "title": title, "content": content, "html": response.text}

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
        jsonl_file.flush()
        self.saved_count += 1

        if self.total_planned:
            self.progress(f"[prog] saved {self.saved_count}/{self.total_planned} | queued={len(self.to_visit)}")
        else:
            self.progress(f"[prog] saved {self.saved_count} | queued={len(self.to_visit)}")

    def discover_links(self, url: str, html: str, base_netloc: str) -> None:
        """Follow links from a page if not using sitemap seeds."""
        if not self.seeds and url not in self.visited_for_links:
            self.visited_for_links.add(url)
            for link in extract_links(html, url):
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
                results[url] = self.fetch_page(url)
                time.sleep(self.delay)
        else:
            for url in batch:
                self.progress(f"[get ] {url}")
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                futures = {pool.submit(self.fetch_page, url): url for url in batch}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        results[url] = future.result()
                    except Exception as exc:
                        logger.warning("Fetch error for %s: %s", url, exc)
                        results[url] = None
            time.sleep(self.delay)

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

            # Process responses sequentially (main thread only — safe for seen_content mutation)
            for url in batch:
                page_data = self.process_response(url, responses.get(url))
                if page_data is None:
                    continue
                self.save_page(page_data, jsonl_file)
                self.discover_links(url, page_data["html"], base_netloc)

            if self.saved_count % state_save_interval == 0:
                _save_state(self.state_path, self.seen_urls, self.seen_content,
                            self.to_visit, self.saved_count, self.seeds)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crawl(
    base_url: str,
    out_dir: str,
    use_sitemap: bool = True,
    delay: float = 1.0,
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
        saved_state = _load_state(engine.state_path)
        if saved_state:
            engine.seen_urls = set(saved_state["seen_urls"])
            engine.seen_content = set(saved_state["seen_content"])
            engine.to_visit = deque(saved_state["to_visit"])
            engine.saved_count = saved_state["saved_count"]
            engine.seeds = saved_state.get("seeds", [])
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
        _save_state(engine.state_path, engine.seen_urls, engine.seen_content,
                     engine.to_visit, engine.saved_count, engine.seeds)
        engine.progress(f"[info] state saved to {engine.state_path} — use --resume to continue")
    else:
        if os.path.isfile(engine.state_path):
            os.remove(engine.state_path)

    logger.info("Saved %s HTML page(s) to %s", engine.saved_count, out_dir)
    return CrawlResult(pages_saved=engine.saved_count, output_dir=out_dir, index_file=engine.jsonl_path)
