"""HTTP fetching — session construction, fetch, and Playwright rendering.

When ``httpx`` is installed (``pip install markcrawl[http2]``), the module
uses :class:`httpx.Client` with HTTP/2 support for better performance.
Otherwise it falls back to :mod:`requests` transparently.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter

from .exceptions import MarkcrawlDependencyError
from .retry import with_retry, with_retry_async

try:
    import httpx as _httpx
    _HAS_HTTPX = True
except ImportError:
    _httpx = None  # type: ignore[assignment]
    _HAS_HTTPX = False

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


# ---------------------------------------------------------------------------
# httpx client (preferred when installed)
# ---------------------------------------------------------------------------

def _build_httpx_client(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
    pool_size: int = 10,
) -> Any:
    """Create an ``httpx.Client`` with HTTP/2 and connection pooling."""
    import ssl as _ssl

    # Check if h2 is available for HTTP/2
    try:
        import h2  # noqa: F401
        http2 = True
    except ImportError:
        http2 = False

    limits = _httpx.Limits(
        max_connections=pool_size,
        max_keepalive_connections=pool_size,
    )

    # Build SSL context (avoids deprecated verify=<str>)
    if isinstance(CERT_PATH, str):
        ssl_ctx = _ssl.create_default_context(cafile=CERT_PATH)
        verify: Any = ssl_ctx
    else:
        verify = CERT_PATH

    client = _httpx.Client(
        http2=http2,
        limits=limits,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
        verify=verify,
        proxy=proxy,
        follow_redirects=True,
    )
    return client


def _fetch_httpx(client: Any, url: str, timeout: int) -> Optional[Any]:
    """Fetch with httpx, applying markcrawl's standard retry policy.

    Retry policy lives in ``markcrawl.retry``: 5 attempts, full-jitter
    exponential 2s->30s, ``Retry-After`` honored on 429, structured INFO log
    per retry. Replaced the prior hand-rolled doubling loop in v0.10.0.
    """
    fetch = with_retry(
        lambda: client.get(url, timeout=timeout),
        transient_errors=(_httpx.HTTPError,),
    )
    return fetch()


# ---------------------------------------------------------------------------
# requests session (fallback)
# ---------------------------------------------------------------------------

def _build_requests_session(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
    pool_size: int = 10,
) -> requests.Session:
    """Create a ``requests.Session`` pre-configured for crawling.

    No transport-level ``urllib3.Retry`` adapter is mounted: request-level
    retry is now centralised in :mod:`markcrawl.retry` (applied in
    ``_fetch_requests``) so the two layers do not double-retry.
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

    adapter = HTTPAdapter(
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


def _fetch_requests(session: requests.Session, url: str, timeout: int) -> Optional[requests.Response]:
    """Fetch with requests, applying markcrawl's standard retry policy.

    The retry decorator from :mod:`markcrawl.retry` handles 429/5xx and
    transient ``RequestException`` cases uniformly with the httpx path.
    Encoding is fixed on the final response that bubbles back.
    """
    fetch = with_retry(
        lambda: session.get(url, timeout=timeout, allow_redirects=True),
        transient_errors=(requests.RequestException,),
    )
    resp = fetch()
    if resp is not None:
        _fix_encoding(resp)
    return resp


# ---------------------------------------------------------------------------
# Public API — auto-selects httpx or requests
# ---------------------------------------------------------------------------

def build_session(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
    pool_size: int = 10,
) -> Any:
    """Create an HTTP client pre-configured for crawling.

    Prefers :mod:`httpx` with HTTP/2 when installed (``pip install
    markcrawl[http2]``), otherwise falls back to :mod:`requests`.
    """
    if _HAS_HTTPX:
        logger.debug("Using httpx client (HTTP/2 %s)", "enabled" if _httpx else "disabled")
        return _build_httpx_client(user_agent=user_agent, proxy=proxy, pool_size=pool_size)
    return _build_requests_session(user_agent=user_agent, proxy=proxy, pool_size=pool_size)


def fetch(session: Any, url: str, timeout: int) -> Optional[Any]:
    """Perform an HTTP GET request, returning the response or ``None`` on failure."""
    if _HAS_HTTPX and isinstance(session, _httpx.Client):
        return _fetch_httpx(session, url, timeout)
    return _fetch_requests(session, url, timeout)


# ---------------------------------------------------------------------------
# Async API — native asyncio with httpx.AsyncClient
# ---------------------------------------------------------------------------

def build_async_session(
    user_agent: str = DEFAULT_UA,
    proxy: Optional[str] = None,
    pool_size: int = 10,
) -> Any:
    """Create an ``httpx.AsyncClient`` for async crawling.

    Raises :class:`MarkcrawlDependencyError` if httpx is not installed.
    """
    if not _HAS_HTTPX:
        raise MarkcrawlDependencyError(
            "httpx is required for async crawling.\n"
            "Install it with:  pip install markcrawl[http2]"
        )
    import ssl as _ssl

    try:
        import h2  # noqa: F401
        http2 = True
    except ImportError:
        http2 = False

    limits = _httpx.Limits(
        max_connections=pool_size,
        max_keepalive_connections=pool_size,
    )

    if isinstance(CERT_PATH, str):
        ssl_ctx = _ssl.create_default_context(cafile=CERT_PATH)
        verify: Any = ssl_ctx
    else:
        verify = CERT_PATH

    return _httpx.AsyncClient(
        http2=http2,
        limits=limits,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
        verify=verify,
        proxy=proxy,
        follow_redirects=True,
    )


async def fetch_async(client: Any, url: str, timeout: int) -> Optional[Any]:
    """Async HTTP GET, applying markcrawl's standard retry policy.

    Mirrors :func:`_fetch_httpx` using :func:`markcrawl.retry.with_retry_async`
    so sync and async callers see identical 429/5xx handling and
    ``Retry-After`` honoring.
    """

    async def _do_get():
        # async wrapper (not a sync lambda) so tenacity's AsyncRetrying
        # detects this as a coroutine callable and awaits it on each attempt.
        return await client.get(url, timeout=timeout)

    fetch = with_retry_async(
        _do_get,
        transient_errors=(_httpx.HTTPError,),
    )
    return await fetch()


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
    browser_args = [
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-dev-shm-usage",
        "--no-first-run",
    ]
    # In Docker (running as root), Chromium needs --no-sandbox
    if os.getuid() == 0:
        browser_args.extend(["--no-sandbox", "--disable-setuid-sandbox"])
    launch_args: Dict = {"args": browser_args}
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
    screenshot_path: Optional[str] = None  # relative to out_dir, set only when --screenshot is on
    screenshot_error: Optional[str] = None  # populated when a screenshot was requested but failed


def fetch_with_playwright(
    context,
    url: str,
    timeout: int,
    screenshot_config: Optional[Any] = None,
    screenshots_dir: Optional[str] = None,
) -> Optional[PlaywrightResponse]:
    """Fetch a URL using Playwright, returning rendered HTML.

    Accepts a reusable browser *context* rather than creating one per call,
    avoiding the overhead of context creation/destruction on every page.

    When *screenshot_config* is enabled, the page is loaded with
    ``wait_until="load"`` (fires on ``window.load`` — all resources fetched)
    plus an explicit ``screenshot_config.wait_ms`` pause before the
    screenshot is captured.  We deliberately avoid ``networkidle`` because
    many real sites (tracker.gg, dotabuff, analytics-heavy pages) never
    idle within a reasonable timeout due to long-polling, keep-alives, and
    beacon pings.  Screenshot failures are recorded on the response rather
    than aborting the fetch.
    """
    shoot = bool(screenshot_config and getattr(screenshot_config, "enabled", False))
    # Always use "load" — "domcontentloaded" fires before client-side framework
    # components hydrate, giving us an empty SPA shell.  "load" waits for all
    # resources, which is enough for React/Next/Vue to render their initial
    # tree.  "networkidle" is too strict (modern sites never idle).
    wait_until = "load"
    page = None
    try:
        page = context.new_page()
        if shoot:
            page.set_viewport_size({
                "width": screenshot_config.viewport_width,
                "height": screenshot_config.viewport_height,
            })
        response = page.goto(url, timeout=timeout * 1000, wait_until=wait_until)
        if response is None:
            return None

        # Let framework hydration settle.  Without this, Playwright often
        # captures pre-hydration DOM even on "load" waits.
        try:
            page.wait_for_timeout(500)
        except Exception:
            pass

        screenshot_path: Optional[str] = None
        screenshot_error: Optional[str] = None
        if shoot and response.ok and screenshots_dir:
            if screenshot_config.wait_ms > 0:
                page.wait_for_timeout(screenshot_config.wait_ms)
            # Import here so screenshots.py is only loaded when actually used.
            from .screenshots import SCREENSHOTS_DIR, capture_screenshot
            fname, err = capture_screenshot(
                page, url, screenshot_config, screenshots_dir,
                timeout_ms=timeout * 1000,
            )
            if fname:
                screenshot_path = f"{SCREENSHOTS_DIR}/{fname}"
            if err:
                screenshot_error = err

        html = page.content()
        # Strip post-load overlays (cookie banners, modals, newsletter popups,
        # sticky CTAs) before returning HTML for extraction.  Screenshots are
        # already captured above, so this doesn't affect visual output.
        try:
            from .dom_cleanup import strip_overlays
            html = strip_overlays(html)
        except Exception as exc:
            logger.debug("overlay strip failed for %s: %s", url, exc)

        headers = {k.lower(): v for k, v in response.headers.items()}
        return PlaywrightResponse(
            ok=response.ok,
            status_code=response.status,
            text=html,
            headers=headers,
            screenshot_path=screenshot_path,
            screenshot_error=screenshot_error,
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
