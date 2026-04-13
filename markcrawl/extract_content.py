"""Content extraction — HTML to Markdown/text conversion and DOM cleaning."""
from __future__ import annotations

import re
import urllib.parse as up
from typing import Callable, List, Optional, Set, Tuple

from bs4 import BeautifulSoup

from .urls import norm_url
from .utils import HTML_PARSER as _PARSER

try:
    from markdownify import MarkdownConverter
    _HAS_MARKDOWNIFY = True
except Exception:
    _HAS_MARKDOWNIFY = False

EXCLUDE_TAGS = {"script", "style", "noscript", "template", "svg", "canvas"}
STRUCTURE_TAGS = {"nav", "header", "footer", "aside"}

# Hints for identifying content regions when no <main> exists
_CONTENT_ID_HINTS = frozenset({
    "content", "main", "main-content", "page-content", "body-content",
    "article", "post", "entry", "yui-main", "mw-content-text",
})
_CONTENT_CLASS_HINTS = frozenset({
    "content", "main", "main-content", "page-content", "body-content",
    "article", "post", "entry", "post-content", "entry-content",
    "yui-b", "markdown-body", "prose", "article-body", "rich-text",
})

# CTA patterns — links matching these are stripped from content
_CTA_PATH_RE = re.compile(
    r"/(sign-?up|sign-?in|log-?in|register|pricing|demo|trial|get-?started|download|subscribe|contact-sales)\b",
    re.IGNORECASE,
)

_KNOWN_LANGS = frozenset({
    "python", "javascript", "typescript", "java", "go", "rust", "ruby", "c",
    "cpp", "csharp", "bash", "sh", "shell", "json", "yaml", "toml", "sql",
    "html", "css", "xml", "jsx", "tsx", "swift", "kotlin", "scala", "php",
    "r", "perl", "lua", "zig", "elixir", "haskell", "ocaml", "markdown",
})


def _infer_code_language(el) -> str:
    """Infer programming language from class attributes on pre/code elements."""
    candidates = [el]
    if el.name == "pre":
        code = el.find("code")
        if code:
            candidates.append(code)
    for tag in candidates:
        classes = tag.get("class") or []
        for cls in classes:
            m = re.match(r"(?:language|lang|hljs|highlight)[_-](\w+)", cls)
            if m:
                return m.group(1)
            if cls in _KNOWN_LANGS:
                return cls
    return ""


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract page title with fallback chain."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return og["content"].strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    meta = soup.find("meta", attrs={"name": "title"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""


def _extract_meta_description(soup: BeautifulSoup) -> str:
    """Extract meta description with og:description fallback."""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content", "").strip():
        return meta["content"].strip()
    og = soup.find("meta", property="og:description")
    if og and og.get("content", "").strip():
        return og["content"].strip()
    return ""


def _extract_structured_data(soup: BeautifulSoup) -> List[dict]:
    """Extract JSON-LD structured data before DOM cleaning destroys script tags."""
    import json as _json
    results = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = _json.loads(script.string or "")
            if isinstance(data, dict):
                results.append(data)
            elif isinstance(data, list):
                results.extend(d for d in data if isinstance(d, dict))
        except (ValueError, TypeError):
            pass
    return results


def _structured_data_to_text(items: List[dict]) -> str:
    """Convert structured data items to text suitable for chunk context."""
    parts: List[str] = []
    for item in items:
        sd_type = item.get("@type", "")
        name = item.get("name", "")
        desc = item.get("description", "")
        if name and desc:
            parts.append(f"{name}: {desc}")
        elif desc:
            parts.append(desc)
        # FAQ pages have Q&A pairs — gold for RAG
        if sd_type == "FAQPage":
            for entity in item.get("mainEntity", []):
                q = entity.get("name", "")
                a_obj = entity.get("acceptedAnswer", {})
                a = a_obj.get("text", "") if isinstance(a_obj, dict) else ""
                if q and a:
                    parts.append(f"Q: {q}\nA: {a}")
    return "\n\n".join(parts)


def _find_content_region(soup: BeautifulSoup):
    """Readability-style content detection for pages without ``<main>``.

    Strategy:
    1. Match common ``id`` / ``class`` patterns (``content``, ``main-content``, etc.)
    2. Score all block-level candidates by word count, paragraph count,
       heading count, and link density — the highest-scoring element wins.

    Returns ``None`` if no suitable region is found (caller falls back to
    ``soup.body``).
    """
    # Step 1: id/class hint matching — fast and handles most sites
    for el in soup.find_all(["div", "section", "article"]):
        el_id = (el.get("id") or "").lower().replace("_", "-")
        el_classes = {c.lower().replace("_", "-") for c in (el.get("class") or [])}
        if el_id in _CONTENT_ID_HINTS or (el_classes & _CONTENT_CLASS_HINTS):
            if len(el.get_text(strip=True).split()) > 20:
                return el

    # Step 2: content density scoring
    best = None
    best_score = 0.0
    for el in soup.find_all(["div", "section", "article", "td"]):
        text = el.get_text(strip=True)
        word_count = len(text.split())
        if word_count < 25:
            continue
        p_count = len(el.find_all("p"))
        ld = _link_density(el)
        h_count = len(el.find_all(re.compile(r"^h[1-6]$")))
        score = word_count * (1.0 - ld) + p_count * 10 + h_count * 5
        if score > best_score:
            best_score = score
            best = el

    return best


def _link_density(el) -> float:
    """Fraction of an element's text that lives inside ``<a>`` tags."""
    text = el.get_text(strip=True)
    text_len = len(text)
    if text_len == 0:
        return 1.0
    link_text = sum(len(a.get_text(strip=True)) for a in el.find_all("a"))
    return link_text / text_len


def clean_dom_for_content(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(EXCLUDE_TAGS):
        tag.decompose()
    # Always strip nav and footer — almost always boilerplate
    for tag in soup.find_all({"nav", "footer"}):
        tag.decompose()
    # Context-aware: keep header/aside if inside a content area
    for tag in soup.find_all({"header", "aside"}):
        if tag.find_parent(["main", "article"]):
            continue
        tag.decompose()
    for el in soup.select(
        '[role="navigation"], [aria-hidden="true"], .sr-only, .visually-hidden, .cookie, .Cookie, .cookie-banner, .consent'
    ):
        try:
            el.decompose()
        except Exception:
            pass
    # Density-based pass: remove div/section elements outside main/article
    # that are link-heavy and text-light (untagged navigation, sidebars)
    for el in soup.find_all({"div", "section"}):
        if el.find_parent(["main", "article"]):
            continue
        text = el.get_text(strip=True)
        word_count = len(text.split())
        if word_count > 80:
            continue
        if _link_density(el) > 0.5:
            el.decompose()
    # CTA link stripping: remove links whose href matches action patterns
    # (signup, login, demo, pricing) — these pollute chunks without adding
    # retrievable content.  Only strip short-text links (<6 words).
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link_text = a.get_text(strip=True)
        if len(link_text.split()) <= 5 and _CTA_PATH_RE.search(href):
            a.decompose()
    # Preserve image alt text and figcaptions before markdownify strips imgs.
    for fig in soup.find_all("figure"):
        caption = fig.find("figcaption")
        caption_text = caption.get_text(strip=True) if caption else ""
        img = fig.find("img")
        alt = img.get("alt", "").strip() if img else ""
        text = caption_text or alt
        if text:
            fig.replace_with(soup.new_string(f"[Image: {text}]"))
        else:
            fig.decompose()
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        if alt:
            img.replace_with(soup.new_string(f"[Image: {alt}]"))
        else:
            img.decompose()


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


def _extract_links_from_soup(soup: BeautifulSoup, base_url: Optional[str]) -> Set[str]:
    """Extract normalised links from an already-parsed soup (no re-parse needed)."""
    if base_url is None:
        return set()
    links: Set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        absolute_url = up.urljoin(base_url, href)
        links.add(norm_url(absolute_url))
    return links


def html_to_markdown(html: str, base_url: Optional[str] = None) -> Tuple[str, str, Set[str]]:
    """Convert raw HTML to cleaned Markdown text.

    Returns ``(title, markdown, links)`` where *links* is the set of
    normalised ``<a href>`` URLs found in the document.  Extracting links
    during the same parse avoids a second BeautifulSoup pass.

    Extraction enrichment:
    - Meta description is prepended as a summary line when available.
    - JSON-LD structured data (FAQ Q&A, descriptions) is appended.
    - Content region is detected via readability-style scoring when no
      ``<main>`` tag exists.
    """
    soup = BeautifulSoup(html, _PARSER)
    links = _extract_links_from_soup(soup, base_url)
    title = _extract_title(soup)
    meta_desc = _extract_meta_description(soup)
    structured = _extract_structured_data(soup)
    clean_dom_for_content(soup)
    main = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
        or _find_content_region(soup)
        or soup.body
        or soup
    )

    if _HAS_MARKDOWNIFY:
        converter = MarkdownConverter(
            heading_style="ATX",
            strip=[],
            wrap=False,
            bullets="*",
            escape_asterisks=False,
            escape_underscores=False,
            code_language="",
            code_language_callback=_infer_code_language,
        )
        markdown = converter.convert_soup(main)
    else:
        markdown = main.get_text("\n")

    # Prepend meta description as summary context
    parts: List[str] = []
    if meta_desc:
        parts.append(f"*{meta_desc}*")
    parts.append(markdown)
    # Append structured data context
    sd_text = _structured_data_to_text(structured)
    if sd_text:
        parts.append(sd_text)
    markdown = "\n\n".join(parts)

    return title, compact_blank_lines(markdown), links


def html_to_text(html: str, base_url: Optional[str] = None) -> Tuple[str, str, Set[str]]:
    """Convert raw HTML to cleaned plain text.

    Returns ``(title, text, links)``.
    """
    soup = BeautifulSoup(html, _PARSER)
    links = _extract_links_from_soup(soup, base_url)
    title = _extract_title(soup)
    meta_desc = _extract_meta_description(soup)
    structured = _extract_structured_data(soup)
    clean_dom_for_content(soup)

    body = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
        or _find_content_region(soup)
        or soup.body
        or soup
    )
    text = body.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    deduped: List[str] = []
    previous: Optional[str] = None
    for line in lines:
        if line != previous:
            deduped.append(line)
        previous = line

    parts: List[str] = []
    if meta_desc:
        parts.append(meta_desc)
    parts.append("\n".join(deduped).strip())
    sd_text = _structured_data_to_text(structured)
    if sd_text:
        parts.append(sd_text)
    return title, "\n\n".join(parts).strip(), links


def html_to_markdown_trafilatura(html: str, base_url: Optional[str] = None) -> Tuple[str, str, Set[str]]:
    """Extract content using trafilatura (higher recall), with BS4 link extraction.

    Requires ``pip install trafilatura``.  Falls back to the default
    BS4 + markdownify pipeline if trafilatura is not installed or returns
    no content.

    Returns ``(title, markdown, links)``.
    """
    try:
        import trafilatura
    except ImportError:
        return html_to_markdown(html, base_url)

    soup = BeautifulSoup(html, _PARSER)
    links = _extract_links_from_soup(soup, base_url)
    title = _extract_title(soup)

    markdown = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=False,
        include_tables=True,
        include_comments=False,
        favor_recall=True,
    )

    if not markdown:
        # trafilatura couldn't extract content — fall back
        _, fallback_md, _ = html_to_markdown(html, base_url)
        return title, fallback_md, links

    return title, compact_blank_lines(markdown), links


def _score_extraction(text: str) -> float:
    """Score an extraction result for the ensemble selector.

    Higher score = better extraction.  Rewards: more words, fewer links,
    longer sentences (real prose, not menu items), structural markers.
    """
    words = text.split()
    word_count = len(words)
    if word_count == 0:
        return 0.0

    # Link density: markdown links [text](url) indicate nav leftovers
    link_count = len(re.findall(r"\[.*?\]\(.*?\)", text))
    link_density = link_count / max(word_count, 1)

    # Average sentence length — short sentences suggest menus/nav
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    # Structural markers — headings and paragraphs indicate good structure
    has_headings = 1.0 if re.search(r"^#{1,6}\s+", text, re.MULTILINE) else 0.0
    has_paragraphs = 1.0 if "\n\n" in text else 0.0

    return (
        word_count * 0.3
        + (1 - link_density) * 0.3
        + min(avg_sentence_len / 20, 1.0) * 0.2
        + (has_headings + has_paragraphs) * 0.1
    )


def html_to_markdown_ensemble(html: str, base_url: Optional[str] = None) -> Tuple[str, str, Set[str]]:
    """Run both default and trafilatura extractors, return the best result.

    Uses a content scoring function to pick the extraction with more real
    prose content and better structure.  Falls back to default-only when
    trafilatura is not installed.

    Returns ``(title, markdown, links)``.
    """
    default_result = html_to_markdown(html, base_url)

    try:
        import trafilatura  # noqa: F401
    except ImportError:
        return default_result

    traf_result = html_to_markdown_trafilatura(html, base_url)

    default_score = _score_extraction(default_result[1])
    traf_score = _score_extraction(traf_result[1])

    return traf_result if traf_score > default_score else default_result


def default_progress(enabled: bool) -> Callable[[str], None]:
    def emit(message: str) -> None:
        if enabled:
            print(message)
    return emit
