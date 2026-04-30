"""Site classifier — detect a site's content shape from URL conventions.

The classifier returns one of seven SiteClass values based on generic URL
conventions used by ≥3 unrelated platforms each (per the
``analyzer.py`` rule: no per-domain hardcoding). The class informs
crawl-strategy dispatch in ``core.py::crawl`` — different content shapes
have different optimal scope/priority defaults.

Classes (in detection priority order):

* ``apiref``  — ``api.*`` hostname, or first segment in
  ``{api, reference, endpoints, methods, rest}``. Queries usually span
  the whole reference; sitemap-broad discovery wins.
* ``wiki``    — first segment in ``_ARTICLE_CONTAINERS`` (``wiki``,
  ``wikipedia``, ``title``). Articles are siblings under a single
  container path; queries usually about seed-near concepts; BFS-from-seed
  priority typically wins (unsolved tradeoff for now — see
  ``bfs_priority_failed_2026-04-27.md``).
* ``docs``    — first segment in ``{docs, documentation, tutorial, guide,
  book, handbook, manual}`` and seed has only 1 path segment ("hub"
  shape). Single-segment scoping wins (Tier 0 fix gated by class).
* ``blog``    — ``blog.*``/``news.*`` hostname, first segment in
  ``{blog, news, posts, articles}``, or ``/YYYY/MM/`` path pattern.
  Sitemap-broad wins (queries match specific posts site-wide).
* ``ecom``    — any path segment matches ``_ECOMMERCE_CATEGORY_MARKERS``.
  Sitemap-broad wins (queries match specific products).
* ``spa``     — orthogonal flag from ``js_detect.py``; not a content
  class but a rendering hint.
* ``generic`` — fallback when no convention matches; current default
  behavior preserved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit


# Hostname prefix → class hints. Conservative: only signals where the
# convention is unambiguous across ≥3 platforms. (`developer.*` was tried
# and removed: MDN is `developer.mozilla.org` but is docs not apiref;
# Salesforce's `developer.salesforce.com` is apiref. Too inconsistent.)
_HOSTNAME_PREFIXES: dict[str, str] = {
    "api.":   "apiref",
    "wiki.":  "wiki",
    "blog.":  "blog",
    "news.":  "blog",
    "docs.":  "docs",
    "doc.":   "docs",
}

# First-path-segment → class hints (lowercased)
_FIRST_SEG_CONTENT: dict[str, str] = {
    # apiref-class
    "api":         "apiref",
    "reference":   "apiref",
    "endpoints":   "apiref",
    "methods":     "apiref",
    "rest":        "apiref",
    # wiki-class (kept consistent with core.py::_ARTICLE_CONTAINERS)
    "wiki":        "wiki",
    "wikipedia":   "wiki",
    "title":       "wiki",
    # docs-class (single-segment hub/section)
    "docs":        "docs",
    "documentation": "docs",
    "tutorial":    "docs",
    "tutorials":   "docs",
    "guide":       "docs",
    "guides":      "docs",
    "book":        "docs",
    "handbook":    "docs",
    "manual":      "docs",
    "learn":       "docs",     # graphql.org/learn, codecademy-style
    "get-started": "docs",     # /en/get-started GitHub support
    # blog-class
    "blog":        "blog",
    "news":        "blog",
    "posts":       "blog",
    "articles":    "blog",
    "sections":    "blog",     # npr.org/sections/news, washington-post style
}

# Generic ecom-marker set (must match ``core.py::_ECOMMERCE_CATEGORY_MARKERS``)
_ECOM_MARKERS: frozenset[str] = frozenset({
    "cat", "category", "categories",
    "products", "shop", "collections", "catalog",
})

# Year-month path pattern: /YYYY/MM/ — common blog convention
_YEAR_MONTH_RE = re.compile(r"/(?:19|20)\d{2}/(?:0\d|1[0-2])/")


@dataclass
class SiteClassification:
    site_class: str
    detection_reason: str

    def __str__(self) -> str:
        return f"{self.site_class} ({self.detection_reason})"


def classify_site(seed_url: str) -> SiteClassification:
    """Classify a seed URL by its content shape.

    URL-only — no fetches. Generic conventions only (≥3 platforms each).
    Detection priority is encoded in the function order: more-specific
    hostname signals win over first-segment, which wins over deeper
    path-anywhere markers. Leading locale segments (e.g. ``/de/``,
    ``/en-US/``) are stripped before first-segment matching, so MDN
    `/de/docs/Web/CSS` still classifies as docs.

    Returns ``SiteClassification`` with the class label and a short
    reason string for logging/debugging.
    """
    parts = urlsplit(seed_url)
    host = (parts.hostname or "").lower()
    path = parts.path or "/"
    segs = [s for s in path.split("/") if s]

    # Strip leading locale segment (e.g. /en-US/docs/...) so the actual
    # content-class signal in the next segment can be detected.
    try:
        from .analyzer import locale_segment
        loc = locale_segment(seed_url)
        if loc and segs and segs[0].lower() == loc.lower():
            segs = segs[1:]
    except Exception:
        pass

    first = segs[0].lower() if segs else ""

    # 1. Hostname-prefix signals (most specific source of truth)
    for prefix, klass in _HOSTNAME_PREFIXES.items():
        if host.startswith(prefix):
            # Special case: docs.* hostname BUT path starts with /api → apiref wins.
            # Reason: docs.stripe.com/api is API ref, not generic docs.
            if klass == "docs" and first in {"api", "reference", "endpoints"}:
                return SiteClassification("apiref", f"hostname={prefix}* + path=/{first}")
            return SiteClassification(klass, f"hostname={prefix}*")

    # 2. First-path-segment signals
    if first in _FIRST_SEG_CONTENT:
        klass = _FIRST_SEG_CONTENT[first]
        # Refinement: docs class only fires when seed is exactly a single-segment
        # "hub" path (e.g. /docs, /book/, /tutorial). For 2+-segment seeds like
        # /docs/concepts/, the existing _auto_path_scope_from_seed already
        # produces the right scope (`/docs/concepts/*`). Docs class is the
        # signal that we should apply the SINGLE-SEGMENT scope override
        # (Tier 0 fix) — only meaningful for single-segment seeds.
        if klass == "docs" and len(segs) > 1:
            return SiteClassification("generic", f"deep docs path /{'/'.join(segs[:3])}/...")
        return SiteClassification(klass, f"first_seg=/{first}")

    # 3. Year-month path (blog signal even when first segment isn't /blog/)
    if _YEAR_MONTH_RE.search(path):
        return SiteClassification("blog", f"year-month path pattern in {path}")

    # 4. Ecom markers anywhere in path
    seg_set = {s.lower() for s in segs}
    if seg_set & _ECOM_MARKERS:
        return SiteClassification("ecom", f"ecom marker in path ({seg_set & _ECOM_MARKERS})")

    return SiteClassification("generic", "no conventions matched")
