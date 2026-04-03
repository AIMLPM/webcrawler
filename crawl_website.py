#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse as up
import xml.etree.ElementTree as ET
from collections import deque
from typing import List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from urllib import robotparser

try:
    # markdownify is small, robust, and ideal for preserving emphasis/headings/links/lists/tables
    from markdownify import markdownify as md_convert
except ImportError:
    md_convert = None  # we'll fall back to plain text if unavailable

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; SiteTextCrawler/1.1; +https://example.com/bot-info) "
    "Python-requests"
)

EXCLUDE_TAGS = {"script", "style", "noscript", "template", "svg", "canvas"}
STRUCTURE_TAGS = {"nav", "header", "footer", "aside"}

def norm_url(url: str) -> str:
    p = up.urlsplit(url)
    normalized = up.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))
    normalized = re.sub(r"(?<!:)/{2,}", "/", normalized)
    return normalized

def same_scope(url: str, base_netloc: str, include_subdomains: bool) -> bool:
    target = up.urlsplit(url).netloc.lower()
    base = base_netloc.lower()
    if target == base:
        return True
    return include_subdomains and target.endswith("." + base)

def safe_filename(url: str, ext: str) -> str:
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

def fetch(session: requests.Session, url: str, timeout: int) -> Optional[requests.Response]:
    try:
        return session.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return None

def parse_robots_txt(session: requests.Session, robots_url: str) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    try:
        r = session.get(robots_url, timeout=10)
        content = r.text if r and r.ok else ""
    except requests.RequestException:
        content = ""
    rp.parse(content.splitlines())
    return rp

def discover_sitemaps(session: requests.Session, base: str) -> List[str]:
    robots_url = up.urljoin(base, "/robots.txt")
    try:
        r = session.get(robots_url, timeout=10)
        if not (r and r.ok):
            return []
        sitemaps = []
        for line in r.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sm = line.split(":", 1)[1].strip()
                if sm:
                    sitemaps.append(sm)
        return sitemaps
    except requests.RequestException:
        return []

def parse_sitemap_xml(session: requests.Session, url: str, timeout: int) -> List[str]:
    try:
        r = session.get(url, timeout=timeout)
        if not (r and r.ok):
            return []
        if not (r.headers.get("Content-Type", "").lower().startswith("application/xml")
                or r.text.strip().startswith("<")):
            return []
        root = ET.fromstring(r.content)
    except Exception:
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for loc in root.findall(".//sm:sitemap/sm:loc", ns):
        if loc.text:
            urls.extend(parse_sitemap_xml(session, loc.text.strip(), timeout))
    for loc in root.findall(".//sm:url/sm:loc", ns):
        if loc.text:
            urls.append(loc.text.strip())
    if not urls:
        for loc in root.findall(".//loc"):
            if loc.text:
                urls.append(loc.text.strip())
    # dedupe preserving order
    return list(dict.fromkeys(urls))

def extract_links(html: str, base_url: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        abs_url = up.urljoin(base_url, href)
        links.add(norm_url(abs_url))
    return links

def clean_dom_for_content(soup: BeautifulSoup):
    # Remove non-content tags
    for tag in soup.find_all(EXCLUDE_TAGS):
        tag.decompose()
    # Remove typical global chrome
    for tag in soup.find_all(STRUCTURE_TAGS):
        tag.decompose()
    # Common accessibility/utility elements that are not content
    for el in soup.select('[role="navigation"], [aria-hidden="true"], .sr-only, .visually-hidden, .cookie, .Cookie, .cookie-banner, .consent'):
        try:
            el.decompose()
        except Exception:
            pass

def html_to_markdown(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    clean_dom_for_content(soup)
    title = (soup.title.string or "").strip() if soup.title else ""
    # Prefer a main-like region if present
    main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body
    if not main:
        main = soup
    html_fragment = str(main)

    if md_convert:
        # Options tuned to keep emphasis, headings, lists, links, code, and tables
        md = md_convert(
            html_fragment,
            heading_style="ATX",      # # H1
            strip=["img",],           # drop images by default (can change to keep alt)
            wrap=False,               # don't reflow lines
            bullets="*",
            escape_asterisks=False,
            escape_underscores=False,
            code_language=False,      # don't force language fences
        )
    else:
        # Fallback: minimal plain text if markdownify not installed
        md = BeautifulSoup(html_fragment, "html.parser").get_text("\n")

    # Normalize excessive blank lines
    md_lines = [ln.rstrip() for ln in md.splitlines()]
    compact = []
    blank_streak = 0
    for ln in md_lines:
        if ln.strip():
            blank_streak = 0
            compact.append(ln)
        else:
            blank_streak += 1
            if blank_streak <= 2:
                compact.append("")
    final_md = "\n".join(compact).strip()
    return title, final_md

def html_to_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    clean_dom_for_content(soup)
    title = (soup.title.string or "").strip() if soup.title else ""
    text = soup.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    deduped = []
    prev = None
    for ln in lines:
        if ln != prev:
            deduped.append(ln)
        prev = ln
    final_text = "\n".join(deduped).strip()
    return title, final_text

def crawl(
    base_url: str,
    out_dir: str,
    use_sitemap: bool,
    delay: float,
    timeout: int,
    max_pages: int,
    include_subdomains: bool,
    fmt: str,
):
    os.makedirs(out_dir, exist_ok=True)
    jsonl_path = os.path.join(out_dir, "pages.jsonl")

    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA, "Accept": "text/html,application/xhtml+xml"})
    base_url = norm_url(base_url)
    base_netloc = up.urlsplit(base_url).netloc

    rp = parse_robots_txt(session, up.urljoin(base_url, "/robots.txt"))
    def allowed(u: str) -> bool:
        try:
            return rp.can_fetch(DEFAULT_UA, u)
        except Exception:
            return True

    to_visit: deque[str] = deque()
    seen: Set[str] = set()
    seeds: List[str] = []

    if use_sitemap:
        for sm in discover_sitemaps(session, base_url):
            seeds.extend(parse_sitemap_xml(session, sm, timeout))
        seeds = [norm_url(u) for u in seeds if u]
        seeds = [u for u in seeds if same_scope(u, base_netloc, include_subdomains)]
        for u in seeds:
            if allowed(u):
                to_visit.append(u)
    if not to_visit:
        to_visit.append(base_url)

    count = 0
    visited_for_links = set()
    ext = "md" if fmt == "markdown" else "txt"

    with open(jsonl_path, "w", encoding="utf-8") as jf:
        while to_visit and (max_pages <= 0 or count < max_pages):
            url = to_visit.popleft()
            if url in seen or not same_scope(url, base_netloc, include_subdomains) or not allowed(url):
                continue
            seen.add(url)

            resp = fetch(session, url, timeout)
            time.sleep(delay)
            if not (resp and resp.ok):
                continue
            ctype = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in ctype:
                continue

            if fmt == "markdown":
                title, content = html_to_markdown(resp.text)
            else:
                title, content = html_to_text(resp.text)

            fname = safe_filename(url, ext)
            fpath = os.path.join(out_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                header = f"# {title}\n\n" if (fmt == "markdown" and title) else (f"Title: {title}\n\n" if title else "")
                meta = f"> URL: {url}\n\n" if fmt == "markdown" else f"URL: {url}\n\n"
                f.write(header + meta + (content or "") + ("\n" if content else ""))

            jf.write(json.dumps({"url": url, "title": title, "path": fname, "text": content}, ensure_ascii=False) + "\n")
            count += 1

            if not seeds:
                if url not in visited_for_links:
                    visited_for_links.add(url)
                    for link in extract_links(resp.text, url):
                        if link not in seen and same_scope(link, base_netloc, include_subdomains) and allowed(link):
                            to_visit.append(link)

    print(f"Saved {count} HTML pages to: {out_dir}")
    print(f"Index written: {jsonl_path}")

def main():
    parser = argparse.ArgumentParser(description="Crawl a site and extract text or Markdown for ingestion.")
    parser.add_argument("--base", required=True, help="Base site URL, e.g., https://www.WEBSITE-TO-CRAWL.com/")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--use-sitemap", default="true", choices=["true", "false"], help="Use sitemap(s) if present")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP request timeout (seconds)")
    parser.add_argument("--max-pages", type=int, default=500, help="Max pages when BFS fallback is used; 0 = unlimited")
    parser.add_argument("--include-subdomains", default="false", choices=["true", "false"], help="Include subdomains")
    parser.add_argument("--format", dest="fmt", default="markdown", choices=["markdown", "text"], help="Output format")
    args = parser.parse_args()

    crawl(
        base_url=args.base,
        out_dir=args.out,
        use_sitemap=(args.use_sitemap.lower() == "true"),
        delay=args.delay,
        timeout=args.timeout,
        max_pages=args.max_pages,
        include_subdomains=(args.include_subdomains.lower() == "true"),
        fmt=args.fmt,
    )

if __name__ == "__main__":
    main()
