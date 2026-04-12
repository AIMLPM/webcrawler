"""Robots.txt parsing and sitemap discovery."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, List, Optional, Tuple
from urllib import robotparser


def parse_robots_txt(session: Any, robots_url: str) -> Tuple[robotparser.RobotFileParser, str]:
    """Fetch and parse robots.txt, returning both the parser and raw text."""
    rp = robotparser.RobotFileParser()
    try:
        response = session.get(robots_url, timeout=10)
        content = response.text if response.ok else ""
    except Exception:
        content = ""
    rp.parse(content.splitlines())
    return rp, content


def discover_sitemaps(session: Any, base: str, robots_text: Optional[str] = None) -> List[str]:
    """Find sitemap URLs declared in the site's ``robots.txt``."""
    import urllib.parse as up

    if robots_text is None:
        robots_url = up.urljoin(base, "/robots.txt")
        try:
            response = session.get(robots_url, timeout=10)
            if not response.ok:
                return []
            robots_text = response.text
        except Exception:
            return []

    sitemaps: List[str] = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            sitemap_url = line.split(":", 1)[1].strip()
            if sitemap_url:
                sitemaps.append(sitemap_url)
    return sitemaps


def parse_sitemap_xml(
    session: Any,
    url: str,
    timeout: int,
    *,
    _depth: int = 0,
    _visited: Optional[set] = None,
    max_depth: int = 5,
) -> List[str]:
    """Recursively parse a sitemap XML and return all page URLs.

    Guards against infinite recursion via *max_depth* and a *_visited* set
    that tracks already-fetched sitemap URLs (prevents cycles).
    """
    if _depth > max_depth:
        return []
    if _visited is None:
        _visited = set()
    if url in _visited:
        return []
    _visited.add(url)

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
            urls.extend(parse_sitemap_xml(
                session, child_url, timeout,
                _depth=_depth + 1, _visited=_visited, max_depth=max_depth,
            ))

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
