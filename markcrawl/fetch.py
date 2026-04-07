"""HTTP fetching — session construction, requests-based fetch, and Playwright rendering."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import MarkcrawlDependencyError

try:
    import certifi
    CERT_PATH: str | bool = certifi.where()
except Exception:
    CERT_PATH = True

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; MarkCrawl/0.1; +https://github.com/AIMLPM/markcrawl) "
    "Python-requests"
)

logger = logging.getLogger(__name__)


def build_session(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
    pool_size: int = 10,
) -> requests.Session:
    """Create a ``requests.Session`` pre-configured for crawling."""
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
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _fix_encoding(response: requests.Response) -> None:
    """Fix the well-known requests ISO-8859-1 default encoding issue.

    When a server returns ``Content-Type: text/html`` with no charset,
    ``requests`` defaults to ISO-8859-1 per HTTP/1.1 spec.  But almost all
    modern HTML is UTF-8, so ``response.text`` produces mojibake (e.g.
    smart quotes ``\u2019`` become ``Ã¢â\u0082¬â\u0084¢``).

    Fix: if the detected encoding is the HTTP default and the content
    looks like UTF-8, override it before anyone reads ``response.text``.
    """
    if (
        response.encoding
        and response.encoding.lower().replace("-", "") == "iso88591"
        and response.apparent_encoding
        and response.apparent_encoding.lower().startswith("utf")
    ):
        response.encoding = response.apparent_encoding


def fetch(session: requests.Session, url: str, timeout: int) -> Optional[requests.Response]:
    """Perform an HTTP GET request, returning the response or ``None`` on failure."""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        _fix_encoding(resp)
        return resp
    except requests.RequestException as exc:
        logger.warning("Fetch error for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Playwright (optional) — JS rendering
# ---------------------------------------------------------------------------

def _get_playwright_browser(proxy: Optional[str] = None) -> tuple:
    """Launch a Playwright Chromium browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise MarkcrawlDependencyError(
            "Playwright is required for --render-js.\n"
            "Install it with:  pip install playwright && playwright install chromium"
        )
    pw = sync_playwright().start()
    launch_args: Dict = {
        "args": [
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-dev-shm-usage",
            "--no-first-run",
        ],
    }
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


def fetch_with_playwright(context, url: str, timeout: int) -> Optional[PlaywrightResponse]:
    """Fetch a URL using Playwright, returning rendered HTML.

    Accepts a reusable browser *context* rather than creating one per call,
    avoiding the overhead of context creation/destruction on every page.
    """
    page = None
    try:
        page = context.new_page()
        response = page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
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
        if page:
            try:
                page.close()
            except Exception:
                pass
