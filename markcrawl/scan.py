"""Pre-crawl site scan — combines URL convention, JS detection, sitemap
shape, and seed-page outlinks into a unified ``SiteProfile``.

The profile drives smarter crawl-strategy dispatch in ``core.py``:

* **Sitemap shape** (size + first-segment clustering) tells us whether
  sitemap-first will help or dilute. Wikipedia's 10K+ alphabetical
  sitemap dominates BFS-from-seed signal; rust-book's small sitemap
  doesn't have enough leverage so BFS-from-seed wins.
* **Seed outlinks** measure whether the seed page is a "hub" (most
  outlinks under one path prefix) or a "leaf" (outlinks scattered).
  Hub seeds benefit from BFS-from-seed; leaf seeds need sitemap-broad.
* **JS / SPA flag** triggers Playwright auto-promotion.
* **URL classifier** provides the content-class hint
  (apiref/wiki/docs/blog/ecom/spa/generic).

Adds ~3-5 HTTP fetches at the start of a crawl. ~5 seconds wallclock
for the typical case, ~1% overhead on a 200-page crawl.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional, Set
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


@dataclass
class SiteProfile:
    """Observed structural features of a site, gathered from up to ~5 fetches.

    Each field has an "unknown" sentinel (None / -1 / empty set) so the
    dispatch layer can fall back to current default behavior when scan
    failed or was skipped.
    """
    base_url: str
    url_class: str = "generic"             # from site_class.classify_site
    is_spa: Optional[bool] = None          # from js_detect (None = not probed)
    sitemap_url_count: int = -1            # -1 = not probed, 0 = empty/missing, >0 = count
    sitemap_first_seg_distribution: Counter = field(default_factory=Counter)
    seed_outlink_count: int = -1
    seed_outlink_first_seg_distribution: Counter = field(default_factory=Counter)
    seed_word_count: int = -1
    fetch_count: int = 0                   # how many HTTP fetches scan spent

    @property
    def sitemap_clustered(self) -> bool:
        """True when one first-segment dominates the sitemap (>70%).
        Indicates a single-project host (sitemap-broad reasonable). False
        means multi-project host (rust-lang.org, mediawiki) where
        sitemap-broad dilutes seed-relevant content.
        """
        if self.sitemap_url_count <= 0:
            return False
        top = self.sitemap_first_seg_distribution.most_common(1)
        if not top:
            return False
        return top[0][1] / self.sitemap_url_count > 0.70

    @property
    def sitemap_huge(self) -> bool:
        """True when sitemap dwarfs typical max_pages budget. At 1K+ URLs
        on a 200-page budget, BFS-from-seed contributes proportionally
        less of the saved pages → seed-graph signal is diluted."""
        return self.sitemap_url_count > 1000

    @property
    def seed_outlinks_clustered(self) -> bool:
        """True when most seed outlinks share one first-segment (>60%).
        Indicates seed is a hub for that subtree → BFS-from-seed will
        reach topical neighbors. False means seed is a leaf or scattered
        index → sitemap-broad needed for coverage."""
        if self.seed_outlink_count <= 0:
            return False
        top = self.seed_outlink_first_seg_distribution.most_common(1)
        if not top:
            return False
        return top[0][1] / self.seed_outlink_count > 0.60

    @property
    def empty_seed(self) -> bool:
        """True when seed page returned little or no visible content
        (404, anti-bot wall, JS-only shell)."""
        return self.seed_word_count == 0

    def summary(self) -> str:
        return (f"SiteProfile({self.url_class}, sitemap={self.sitemap_url_count}, "
                f"clustered={self.sitemap_clustered}, "
                f"seed_outlinks={self.seed_outlink_count}/clustered={self.seed_outlinks_clustered}, "
                f"is_spa={self.is_spa}, fetches={self.fetch_count})")


def _first_seg(url: str) -> str:
    parts = urlsplit(url).path.strip("/").split("/")
    return parts[0].lower() if parts and parts[0] else ""


_HREF_RE = re.compile(rb'href=["\']([^"\']+)["\']', re.IGNORECASE)


def _extract_hrefs(html_bytes: bytes) -> list[str]:
    return [m.decode(errors="replace") for m in _HREF_RE.findall(html_bytes)]


def scan_site(base_url: str, session=None, timeout: int = 10,
              user_agent: Optional[str] = None,
              max_sitemap_urls: int = 5000) -> SiteProfile:
    """Build a SiteProfile via up to ~5 lightweight fetches.

    Failures are non-fatal: we set the "unknown" sentinel for any
    component that couldn't be probed, and the dispatch layer falls back
    to current default behavior. Total budget: ~5-10 seconds.
    """
    from .site_class import classify_site
    from urllib.parse import urljoin

    profile = SiteProfile(base_url=base_url)
    profile.url_class = classify_site(base_url).site_class

    # 1. Seed page fetch (1 request) — extract outlinks + visible text + SPA marker.
    if session is None:
        try:
            import requests
            session = requests.Session()
            session.headers.update({"User-Agent": user_agent or "markcrawl/scan"})
        except ImportError:
            return profile

    base_netloc = urlsplit(base_url).netloc
    try:
        resp = session.get(base_url, timeout=timeout, allow_redirects=True)
        profile.fetch_count += 1
        html = resp.content
    except Exception as exc:
        logger.debug("scan: seed fetch failed for %s: %s", base_url, exc)
        return profile

    # Visible text count + SPA detection (use existing js_detect helpers)
    try:
        from .js_detect import is_spa_site, _visible_text
        text = _visible_text(html.decode(errors="replace"))
        profile.seed_word_count = len(text.split())
        profile.is_spa = is_spa_site(html.decode(errors="replace"))
    except Exception as exc:
        logger.debug("scan: text/spa probe failed: %s", exc)

    # Outlinks: same-host only, count first-segment distribution
    hrefs = _extract_hrefs(html)
    seg_counter: Counter = Counter()
    out_count = 0
    for href in hrefs:
        try:
            full = urljoin(base_url, href)
            sp = urlsplit(full)
            if sp.netloc != base_netloc:
                continue
            if not sp.path or sp.path == "/":
                continue
            seg = _first_seg(full)
            if not seg:
                continue
            seg_counter[seg] += 1
            out_count += 1
        except Exception:
            continue
    profile.seed_outlink_count = out_count
    profile.seed_outlink_first_seg_distribution = seg_counter

    # 2. Sitemap discovery + URL count (up to ~3 fetches)
    try:
        from .robots import discover_sitemaps, parse_sitemap_xml
        sitemap_urls: list[str] = []
        for sm_url in discover_sitemaps(session, base_url):
            profile.fetch_count += 1
            try:
                urls = parse_sitemap_xml(session, sm_url, timeout)
                sitemap_urls.extend(urls)
                if len(sitemap_urls) >= max_sitemap_urls:
                    break
            except Exception:
                continue
        # Filter to same-host
        sitemap_urls = [u for u in sitemap_urls if urlsplit(u).netloc == base_netloc]
        profile.sitemap_url_count = len(sitemap_urls)
        sm_seg: Counter = Counter()
        for u in sitemap_urls:
            seg = _first_seg(u)
            if seg:
                sm_seg[seg] += 1
        profile.sitemap_first_seg_distribution = sm_seg
    except Exception as exc:
        logger.debug("scan: sitemap probe failed: %s", exc)

    return profile
