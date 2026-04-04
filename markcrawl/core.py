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
from typing import Callable, Deque, Dict, Iterable, List, Optional, Set, Tuple
from urllib import robotparser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    The session is set up with automatic retries (3 attempts with exponential
    back-off) for transient HTTP errors, a custom User-Agent header, and
    optional proxy support.

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

    All ``requests.RequestException`` errors are caught and logged at WARNING
    level so the caller can treat ``None`` as "skip this URL".

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
    """Launch a Playwright Chromium browser (reuse across calls via caller)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
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
    try:
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        response = page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
        if response is None:
            context.close()
            return None
        html = page.content()
        headers = {k.lower(): v for k, v in response.headers.items()}
        result = PlaywrightResponse(
            ok=response.ok,
            status_code=response.status,
            text=html,
            headers=headers,
        )
        context.close()
        return result
    except Exception as exc:
        logger.warning("Playwright fetch error for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def norm_url(url: str) -> str:
    """Normalise a URL for deduplication.

    Lowercases the scheme and netloc, ensures the path is at least ``"/"``,
    strips the fragment, and collapses consecutive slashes.

    Args:
        url: Any absolute URL string.

    Returns:
        The canonicalised URL string (fragment removed, scheme/host lowered).
    """
    p = up.urlsplit(url)
    normalized = up.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))
    normalized = re.sub(r"(?<!:)/{2,}", "/", normalized)
    return normalized


def same_scope(url: str, base_netloc: str, include_subdomains: bool) -> bool:
    """Check whether *url* falls within the allowed crawl scope.

    Args:
        url: The candidate URL to test.
        base_netloc: The netloc (host[:port]) of the seed/base URL.
        include_subdomains: When ``True``, subdomains of *base_netloc* are
            also considered in-scope (e.g. ``docs.example.com`` matches
            ``example.com``).

    Returns:
        ``True`` if *url* shares the same host (or is a subdomain when
        allowed), ``False`` otherwise.
    """
    target = up.urlsplit(url).netloc.lower()
    base = base_netloc.lower()
    if target == base:
        return True
    return include_subdomains and target.endswith("." + base)


def safe_filename(url: str, ext: str) -> str:
    """Derive a filesystem-safe filename from a URL.

    The filename is built from the URL path (non-alphanumeric characters
    replaced with dashes, truncated to 120 chars) plus a short SHA-1 hash
    suffix to avoid collisions.

    Args:
        url: The page URL.
        ext: File extension without the leading dot (e.g. ``"md"``, ``"txt"``).

    Returns:
        A filename string like ``"docs-api__a1b2c3d4e5.md"``.
    """
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

def parse_robots_txt(session: requests.Session, robots_url: str) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    try:
        response = session.get(robots_url, timeout=10)
        content = response.text if response.ok else ""
    except requests.RequestException:
        content = ""
    rp.parse(content.splitlines())
    return rp


def discover_sitemaps(session: requests.Session, base: str) -> List[str]:
    """Find sitemap URLs declared in the site's ``robots.txt``.

    Fetches ``/robots.txt`` relative to *base* and extracts every
    ``Sitemap:`` directive.

    Args:
        session: An active ``requests.Session``.
        base: The base URL of the target site (e.g. ``"https://example.com"``).

    Returns:
        A list of sitemap URLs (may be empty if ``robots.txt`` is missing,
        inaccessible, or contains no ``Sitemap`` directives).
    """
    robots_url = up.urljoin(base, "/robots.txt")
    try:
        response = session.get(robots_url, timeout=10)
        if not response.ok:
            return []
        sitemaps: List[str] = []
        for line in response.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                if sitemap_url:
                    sitemaps.append(sitemap_url)
        return sitemaps
    except requests.RequestException:
        return []


def parse_sitemap_xml(session: requests.Session, url: str, timeout: int) -> List[str]:
    """Recursively parse a sitemap XML and return all page URLs.

    Handles both sitemap index files (which reference child sitemaps) and
    regular sitemaps containing ``<url><loc>`` entries.  Child sitemaps are
    fetched and parsed recursively.

    Args:
        session: An active ``requests.Session``.
        url: URL of the sitemap XML to parse.
        timeout: Request timeout in seconds.

    Returns:
        A deduplicated list of page URLs found in the sitemap tree, in
        discovery order.  Returns an empty list on fetch/parse errors.
    """
    try:
        response = session.get(url, timeout=timeout)
        if not response.ok:
            return []
        content_type = response.headers.get("Content-Type", "").lower()
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
    """Extract and normalise all ``<a href>`` links from an HTML document.

    Relative URLs are resolved against *base_url* and every result is passed
    through :func:`norm_url` for deduplication.

    Args:
        html: Raw HTML string.
        base_url: The URL of the page (used to resolve relative hrefs).

    Returns:
        A set of normalised absolute URL strings.
    """
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
    """Convert raw HTML to cleaned Markdown text.

    Strips scripts, styles, navigation, footers, and other boilerplate (via
    :func:`clean_dom_for_content`), then converts the ``<main>`` content
    region to Markdown using *markdownify* (falls back to plain text extraction
    if *markdownify* is not installed).

    Args:
        html: The full HTML source of a page.

    Returns:
        A ``(title, markdown)`` tuple.  *title* is the ``<title>`` text
        (empty string if absent); *markdown* is the cleaned content with
        excessive blank lines collapsed.
    """
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
    """Convert raw HTML to cleaned plain text.

    Performs the same DOM cleaning as :func:`html_to_markdown` but extracts
    text via ``BeautifulSoup.get_text()``.  Whitespace is normalised per line
    and consecutive duplicate lines are collapsed.

    Args:
        html: The full HTML source of a page.

    Returns:
        A ``(title, text)`` tuple.  *title* is the ``<title>`` text (empty
        string if absent); *text* is the cleaned plain-text content.
    """
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
# Main crawl
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
) -> CrawlResult:
    """Crawl a website and save cleaned content to disk.

    Orchestrates the full three-stage pipeline: URL discovery (sitemap-first,
    falling back to BFS link following), fetching and cleaning HTML, and
    writing Markdown/text files plus a JSONL index.

    Respects ``robots.txt``, deduplicates pages by content hash, and supports
    resumable crawls (state is checkpointed periodically and on ``SIGINT``).

    Args:
        base_url: Seed URL and scope root (e.g. ``"https://example.com"``).
        out_dir: Directory where output files and ``pages.jsonl`` are written.
        use_sitemap: If ``True``, attempt sitemap-based discovery before
            falling back to link following.
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
        resume: If ``True``, resume a previously interrupted crawl from the
            saved state file in *out_dir*.

    Returns:
        A :class:`CrawlResult` with the count of saved pages, output
        directory path, and path to the JSONL index file.
    """
    os.makedirs(out_dir, exist_ok=True)
    jsonl_path = os.path.join(out_dir, "pages.jsonl")
    state_path = os.path.join(out_dir, STATE_FILENAME)

    effective_user_agent = user_agent or DEFAULT_UA
    session = build_session(user_agent=effective_user_agent, proxy=proxy)
    progress = default_progress(show_progress)

    # Playwright browser (only when JS rendering is requested)
    pw_instance = None
    pw_browser = None
    if render_js:
        pw_instance, pw_browser = _get_playwright_browser(proxy=proxy)
        progress("[info] Playwright browser launched for JS rendering")

    base_url = norm_url(base_url)
    base_netloc = up.urlsplit(base_url).netloc

    rp = parse_robots_txt(session, up.urljoin(base_url, "/robots.txt"))

    def allowed(url: str) -> bool:
        try:
            return rp.can_fetch(effective_user_agent, url)
        except Exception:
            return True

    def fetch_page(url: str):
        """Fetch a single page using either requests or Playwright."""
        if render_js:
            return fetch_with_playwright(pw_browser, url, timeout, effective_user_agent)
        return fetch(session, url, timeout)

    to_visit: Deque[str] = deque()
    seen_urls: Set[str] = set()
    seen_content: Set[str] = set()
    visited_for_links: Set[str] = set()
    seeds: List[str] = []

    # --- Resume from saved state ---
    resumed = False
    if resume:
        saved_state = _load_state(state_path)
        if saved_state:
            seen_urls = set(saved_state["seen_urls"])
            seen_content = set(saved_state["seen_content"])
            to_visit = deque(saved_state["to_visit"])
            saved_count_start = saved_state["saved_count"]
            seeds = saved_state.get("seeds", [])
            resumed = True
            progress(f"[info] resuming crawl: {saved_count_start} page(s) already saved, {len(to_visit)} queued")
        else:
            progress("[info] no saved state found, starting fresh")

    total_planned: Optional[int] = None
    if not resumed:
        if use_sitemap:
            for sitemap_url in discover_sitemaps(session, base_url):
                seeds.extend(parse_sitemap_xml(session, sitemap_url, timeout))
            seeds = [norm_url(url) for url in seeds if url]
            seeds = [url for url in seeds if same_scope(url, base_netloc, include_subdomains)]
            seeds = [url for url in seeds if allowed(url)]
            for url in seeds:
                to_visit.append(url)
            if seeds:
                total_planned = len(seeds)
                progress(f"[info] sitemap discovered {total_planned} in-scope page(s)")

        if not to_visit:
            to_visit.append(base_url)
            progress("[info] no sitemap seeds available; using base URL as crawl seed")

    saved_count = saved_count_start if resumed else 0
    ext = "md" if fmt == "markdown" else "txt"

    # Interrupt handler — save state on Ctrl+C
    interrupted = False
    original_sigint = signal.getsignal(signal.SIGINT)

    def _handle_interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
        progress("\n[info] interrupt received — saving state and stopping...")

    signal.signal(signal.SIGINT, _handle_interrupt)

    def process_page(url: str, html: str) -> Optional[Dict]:
        """Extract content from HTML and return a dict to write, or None to skip."""
        if fmt == "markdown":
            title, content = html_to_markdown(html)
        else:
            title, content = html_to_text(html)

        if not content:
            return None
        if len(content.split()) < min_words:
            progress(f"[skip] too little content: {url}")
            return None

        content_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
        if content_hash in seen_content:
            progress(f"[skip] duplicate content: {url}")
            return None
        seen_content.add(content_hash)

        return {"url": url, "title": title, "content": content, "html": html}

    def write_page(page_data: Dict) -> str:
        """Write a page to disk and return the filename."""
        url = page_data["url"]
        title = page_data["title"]
        content = page_data["content"]

        filename = safe_filename(url, ext)
        output_path = os.path.join(out_dir, filename)
        with open(output_path, "w", encoding="utf-8") as output_file:
            if fmt == "markdown":
                header = f"# {title}\n\n" if title else ""
                meta = f"> URL: {url}\n\n"
            else:
                header = f"Title: {title}\n\n" if title else ""
                meta = f"URL: {url}\n\n"
            output_file.write(header + meta + content + "\n")
        return filename

    # Save state every N pages
    state_save_interval = 10

    jsonl_mode = "a" if resumed else "w"

    try:
        with open(jsonl_path, jsonl_mode, encoding="utf-8") as jsonl_file:

            if concurrency <= 1:
                # --- Sequential mode (original behavior) ---
                while to_visit and (max_pages <= 0 or saved_count < max_pages) and not interrupted:
                    url = to_visit.popleft()
                    if url in seen_urls:
                        continue
                    if not same_scope(url, base_netloc, include_subdomains):
                        continue
                    if not allowed(url):
                        progress(f"[skip] robots.txt disallowed: {url}")
                        continue

                    seen_urls.add(url)
                    progress(f"[get ] {url}")
                    response = fetch_page(url)
                    time.sleep(delay)

                    if not (response and response.ok):
                        continue
                    content_type = response.headers.get("content-type", response.headers.get("Content-Type", "")).lower()
                    if "text/html" not in content_type:
                        progress(f"[skip] non-HTML content: {url}")
                        continue

                    page_data = process_page(url, response.text)
                    if page_data is None:
                        continue

                    filename = write_page(page_data)
                    jsonl_file.write(
                        json.dumps(
                            {"url": url, "title": page_data["title"], "path": filename, "text": page_data["content"]},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    jsonl_file.flush()
                    saved_count += 1

                    if total_planned:
                        progress(f"[prog] saved {saved_count}/{total_planned} | queued={len(to_visit)}")
                    else:
                        progress(f"[prog] saved {saved_count} | queued={len(to_visit)}")

                    if not seeds and url not in visited_for_links:
                        visited_for_links.add(url)
                        for link in extract_links(response.text, url):
                            if link not in seen_urls and same_scope(link, base_netloc, include_subdomains) and allowed(link):
                                to_visit.append(link)

                    if saved_count % state_save_interval == 0:
                        _save_state(state_path, seen_urls, seen_content, to_visit, saved_count, seeds)

            else:
                # --- Concurrent mode ---
                progress(f"[info] concurrent mode: {concurrency} workers")

                while to_visit and (max_pages <= 0 or saved_count < max_pages) and not interrupted:
                    # Collect a batch of URLs to fetch in parallel
                    batch: List[str] = []
                    while to_visit and len(batch) < concurrency and (max_pages <= 0 or saved_count + len(batch) < max_pages):
                        url = to_visit.popleft()
                        if url in seen_urls:
                            continue
                        if not same_scope(url, base_netloc, include_subdomains):
                            continue
                        if not allowed(url):
                            progress(f"[skip] robots.txt disallowed: {url}")
                            continue
                        seen_urls.add(url)
                        batch.append(url)

                    if not batch:
                        break

                    for url in batch:
                        progress(f"[get ] {url}")

                    # Fetch all URLs in the batch concurrently
                    results: Dict[str, Optional] = {}
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        futures = {pool.submit(fetch_page, url): url for url in batch}
                        for future in as_completed(futures):
                            url = futures[future]
                            try:
                                results[url] = future.result()
                            except Exception as exc:
                                logger.warning("Fetch error for %s: %s", url, exc)
                                results[url] = None

                    # Process results in original batch order
                    for url in batch:
                        response = results.get(url)
                        if not (response and response.ok):
                            continue
                        content_type = response.headers.get("content-type", response.headers.get("Content-Type", "")).lower()
                        if "text/html" not in content_type:
                            progress(f"[skip] non-HTML content: {url}")
                            continue

                        page_data = process_page(url, response.text)
                        if page_data is None:
                            continue

                        filename = write_page(page_data)
                        jsonl_file.write(
                            json.dumps(
                                {"url": url, "title": page_data["title"], "path": filename, "text": page_data["content"]},
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                        jsonl_file.flush()
                        saved_count += 1

                        if total_planned:
                            progress(f"[prog] saved {saved_count}/{total_planned} | queued={len(to_visit)}")
                        else:
                            progress(f"[prog] saved {saved_count} | queued={len(to_visit)}")

                        if not seeds and url not in visited_for_links:
                            visited_for_links.add(url)
                            for link in extract_links(response.text, url):
                                if link not in seen_urls and same_scope(link, base_netloc, include_subdomains) and allowed(link):
                                    to_visit.append(link)

                    # Respect delay between batches
                    time.sleep(delay)

                    if saved_count % state_save_interval == 0:
                        _save_state(state_path, seen_urls, seen_content, to_visit, saved_count, seeds)

    finally:
        signal.signal(signal.SIGINT, original_sigint)
        if pw_browser:
            pw_browser.close()
        if pw_instance:
            pw_instance.stop()

    # If interrupted or queue not empty (hit max_pages), save state for resume
    if interrupted or (to_visit and max_pages > 0 and saved_count >= max_pages):
        _save_state(state_path, seen_urls, seen_content, to_visit, saved_count, seeds)
        progress(f"[info] state saved to {state_path} — use --resume to continue")
    else:
        # Crawl completed — clean up state file
        if os.path.isfile(state_path):
            os.remove(state_path)

    logger.info("Saved %s HTML page(s) to %s", saved_count, out_dir)
    return CrawlResult(pages_saved=saved_count, output_dir=out_dir, index_file=jsonl_path)
