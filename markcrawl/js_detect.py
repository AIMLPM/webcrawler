"""JS-heavy (SPA) site detection.

Used to decide whether a crawl should auto-promote to Playwright rendering.
Keeps the decision at the site level — sniff the first page and commit.

Detection heuristic (all-true to flag):

1. **Known SPA framework marker** in the HTML head/body.  We look for
   string tokens that only appear in client-rendered framework output:
   - ``id="__next"``       → Next.js
   - ``id="root"`` with an empty or whitespace-only body → React (CRA, Vite)
   - ``id="app"`` with an empty or whitespace-only body → Vue / Angular
   - ``data-reactroot``    → React
   - ``ng-version=``       → Angular
   - ``__NUXT__``          → Nuxt.js

2. **Low visible text ratio**: after stripping scripts/styles/HTML tags,
   the visible text is less than ``min_text_chars`` characters (default
   400) AND less than 5% of total HTML size.  A meaningful SPA shell is
   by construction mostly JS and bootstrap markup, with very little
   visible text.

Both conditions must be true.  Markers alone are not enough (many SSR
sites use ``id="root"`` as a convention), and low text alone is not
enough (some sites genuinely have short content).

The heuristic is intentionally conservative.  False negatives (saying a
site isn't an SPA when it is) are preferable to false positives (forcing
Playwright on an SSR site that doesn't need it — which regressed MRR by
0.18 in the W23 campaign).
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# Tokens that strongly indicate client-side framework rendering.
# These appear in the *initial HTML*, not after JS execution.
_FRAMEWORK_MARKERS: tuple = (
    'id="__next"',     # Next.js
    'data-reactroot',  # React (older versions)
    'ng-version=',     # Angular
    '__NUXT__',        # Nuxt.js
    'id="___gatsby"',  # Gatsby
    'data-qwik',       # Qwik
)

# Tokens that are *weaker* signals — common as conventions on SSR sites too.
# Require combination with low-visible-text to flag.
_WEAK_FRAMEWORK_MARKERS: tuple = (
    'id="root"',       # React (CRA, Vite) — also used on some SSR sites
    'id="app"',        # Vue, Angular — also common SSR convention
)


_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _visible_text(html: str) -> str:
    """Strip scripts, styles, and HTML tags to get visible text.

    Not a full HTML parser — good enough for a ratio estimate.
    """
    no_scripts = _SCRIPT_RE.sub(" ", html)
    no_styles = _STYLE_RE.sub(" ", no_scripts)
    text_only = _TAG_RE.sub(" ", no_styles)
    return _WS_RE.sub(" ", text_only).strip()


def is_spa_site(
    html: str,
    min_text_chars: int = 400,
    max_text_ratio: float = 0.05,
) -> bool:
    """Heuristically decide whether *html* is from a JS-heavy SPA shell.

    Returns True only when both a framework marker is present AND the
    visible text is short enough that client-side rendering is the
    plausible explanation.  Parameters are exposed for testing — the
    defaults were chosen to be conservative (prefer false negatives).
    """
    if not html:
        return False

    # Strong marker: enough on its own only if text is ALSO minimal
    # (some SSR sites use Next.js with plenty of pre-rendered content —
    # we don't want to force Playwright on those either).
    visible = _visible_text(html)
    visible_len = len(visible)
    html_len = len(html)

    ratio = visible_len / html_len if html_len else 0.0
    low_visible = visible_len < min_text_chars and ratio < max_text_ratio

    has_strong = any(m in html for m in _FRAMEWORK_MARKERS)
    has_weak = any(m in html for m in _WEAK_FRAMEWORK_MARKERS)
    has_marker = has_strong or has_weak

    detected = has_marker and low_visible

    if detected:
        logger.info(
            "SPA detected: marker=%s, visible_chars=%d, ratio=%.3f",
            "strong" if has_strong else "weak",
            visible_len,
            ratio,
        )

    return detected


def probe_url_for_spa(
    url: str,
    user_agent: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """Fetch *url* once (plain HTTP) and run :func:`is_spa_site` on the result.

    Convenience wrapper for the crawl entry point.  Never raises — any
    network/HTTP error returns False (assume not an SPA, fall back to
    HTTP-only crawling).
    """
    try:
        import requests
        headers = {"User-Agent": user_agent} if user_agent else None
        resp = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        if resp.status_code >= 400:
            return False
        # Only examine the first ~50KB to avoid parsing huge pages.
        html = resp.text[:50000] if resp.text else ""
        return is_spa_site(html)
    except Exception as exc:
        logger.debug("SPA probe failed for %s: %s", url, exc)
        return False
