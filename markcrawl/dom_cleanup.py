"""DOM overlay stripping — remove cookie banners, modals, newsletter popups,
and sticky CTAs before content extraction.

Needed for the Playwright rendering path.  Plain HTTP responses rarely
contain overlay HTML (the banner is usually injected by JS after load).
Playwright's post-load DOM captures them, which then bleeds into
extracted markdown and hurts retrieval.

Design principles:

- **Conservative** — it is far worse to strip legitimate content than to
  leave a banner in.  We look for compound signals (class name pattern
  PLUS container role PLUS visibility hint) rather than any one marker.
- **No per-domain rules** — keeps the tool source-agnostic.
- **BeautifulSoup-based** — we already depend on it for extraction.

Use :func:`strip_overlays` from :mod:`markcrawl.fetch_with_playwright`
before passing HTML to the markdown extractor.
"""
from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


# Case-insensitive substrings that appear in class or id values of overlay
# elements.  Each triggers a *candidate* for removal, which is only
# followed through after additional checks (see `_overlay_candidate`).
_OVERLAY_NAME_PATTERNS = re.compile(
    r"(?i)"
    r"(?:^|[-_ ])"
    r"(cookie|consent|gdpr|privacy[-_]?(?:notice|banner|popup)|"
    r"newsletter|subscribe[-_]?popup|signup[-_]?modal|"
    r"announce(?:ment)?[-_]?bar|promo[-_]?bar|top[-_]?bar|sticky[-_]?cta|"
    r"cta[-_]?sticky|floating[-_]?cta|"
    r"intercom|hubspot|beacon|drift|tawk|"
    r"chat[-_]?widget|chat[-_]?bubble|"
    r"modal|dialog|popup|overlay|lightbox)"
    r"(?:$|[-_ ])"
)

# ARIA / role attributes that mark overlays or dialogs.
_OVERLAY_ROLES = {"dialog", "alertdialog", "banner"}

# Tags that are almost always overlays when they contain overlay-ish
# class/id values or role="dialog".  Strip without further checks.
_OVERLAY_TAGS = {"dialog", "aside"}


def _element_text(el) -> str:
    """Visible text in an element (for length heuristic)."""
    return (el.get_text(" ", strip=True) or "")


def _overlay_candidate(el) -> bool:
    """Does this element look like an overlay?  Compound-signal check.

    Must match at least two of:
    - class/id name matches a known overlay pattern
    - role attribute is an overlay role OR element tag is an overlay tag
    - element is ``position: fixed`` or ``position: sticky`` (inline style)

    Or: explicit ``role="dialog"``/``role="alertdialog"`` — enough on its own.
    """
    # Single strong signal: explicit dialog role
    role = (el.get("role") or "").strip().lower()
    if role in {"dialog", "alertdialog"}:
        return True

    # Weak signals that combine
    signals = 0

    classes = " ".join(el.get("class") or [])
    el_id = el.get("id") or ""
    name_str = f"{classes} {el_id}"
    if name_str.strip() and _OVERLAY_NAME_PATTERNS.search(name_str):
        signals += 1

    if role in _OVERLAY_ROLES or el.name in _OVERLAY_TAGS:
        signals += 1

    style = (el.get("style") or "").lower()
    if "position:fixed" in style or "position: fixed" in style \
            or "position:sticky" in style or "position: sticky" in style:
        signals += 1

    # Data attribute commonly used by consent/modal libs
    for attr in el.attrs or {}:
        if attr.startswith("data-") and attr.lower() in {
            "data-gdpr", "data-cookieconsent", "data-modal", "data-overlay",
            "data-cookiebar", "data-consent",
        }:
            signals += 1
            break

    return signals >= 2


def strip_overlays(html: str) -> str:
    """Return *html* with obvious overlays removed.

    Safe to call on any HTML — if nothing matches, returns the input
    string unchanged.  Uses ``lxml`` parser via BeautifulSoup.
    """
    if not html or "<" not in html:
        return html

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("bs4 not available; skipping overlay strip")
        return html

    soup = BeautifulSoup(html, "lxml")
    removed = 0

    # Walk once — iterate a static list to avoid mutation during traversal
    candidates: List = []
    for el in soup.find_all(True):
        if _overlay_candidate(el):
            candidates.append(el)

    for el in candidates:
        # Skip anything huge — overlays are usually <10KB of text.  If a
        # candidate contains a ton of visible text, it's probably real
        # content using unfortunate class naming.
        text = _element_text(el)
        if len(text) > 4000:
            continue
        el.decompose()
        removed += 1

    if removed:
        logger.debug("Stripped %d overlay element(s) from HTML", removed)

    return str(soup)
