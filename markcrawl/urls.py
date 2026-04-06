"""URL helpers — normalisation, scope checking, and safe filename generation."""
from __future__ import annotations

import hashlib
import re
import urllib.parse as up
from typing import Set

from bs4 import BeautifulSoup


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


def extract_links(html: str, base_url: str) -> Set[str]:
    """Extract and normalise all ``<a href>`` links from an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    links: Set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        absolute_url = up.urljoin(base_url, href)
        links.add(norm_url(absolute_url))
    return links
