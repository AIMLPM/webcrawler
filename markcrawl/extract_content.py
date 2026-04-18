"""Content extraction — HTML to Markdown/text conversion and DOM cleaning."""
from __future__ import annotations

import re
import urllib.parse as up
from typing import Callable, Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup

from .urls import norm_url
from .utils import HTML_PARSER as _PARSER

# ---------------------------------------------------------------------------
# Page-type classification
# ---------------------------------------------------------------------------

# Lightweight heuristic classifier — no ML, uses DOM structure and URL signals.
PAGE_TYPES = ("docs", "article", "product", "forum", "generic")


def classify_page(soup: BeautifulSoup, url: str = "") -> str:
    """Classify a page into a type using DOM heuristics and URL patterns.

    Returns one of: ``"docs"``, ``"article"``, ``"product"``, ``"forum"``,
    ``"generic"``.
    """
    path = up.urlsplit(url).path.lower() if url else ""
    body_text = (soup.body.get_text(strip=True) if soup.body else "")[:5000]

    # URL-based signals
    docs_url = bool(re.search(r"/(docs?|api|reference|guide|tutorial|manual|sdk|specification)", path))
    article_url = bool(re.search(r"/(blog|post|article|news|story|journal)", path))
    product_url = bool(re.search(r"/(product|item|shop|store|buy|pricing|catalog)", path))
    forum_url = bool(re.search(r"/(forum|thread|discussion|community|topic|question|answer|ask)", path))

    # DOM signals
    has_code = bool(soup.find("pre") or soup.find("code"))
    has_article_tag = bool(soup.find("article"))
    has_time_tag = bool(soup.find("time"))
    has_author = bool(
        soup.find(attrs={"rel": "author"})
        or soup.find(class_=re.compile(r"author|byline", re.I))
    )

    # Docs: code + docs URL, or heavy code usage
    code_blocks = len(soup.find_all("pre"))
    if docs_url and has_code:
        return "docs"
    if code_blocks >= 3:
        return "docs"

    # Article: has article tag + time/author, or article URL
    if has_article_tag and (has_time_tag or has_author):
        return "article"
    if article_url and (has_time_tag or has_author):
        return "article"

    # Product: product URL + price-like content
    has_price = bool(re.search(r"\$\d+|\d+\.\d{2}", body_text[:2000]))
    if product_url and has_price:
        return "product"

    # Forum: forum URL + reply/comment patterns
    has_replies = bool(soup.find(class_=re.compile(r"reply|comment|answer|post", re.I)))
    if forum_url and has_replies:
        return "forum"

    # Fallback by strongest signals
    if docs_url:
        return "docs"
    if article_url:
        return "article"

    return "generic"


# Per-type extraction hints used by clean_dom_for_content_typed
_TYPE_KEEP_ASIDE: Dict[str, bool] = {
    "docs": True,       # Docs sidebars often have params, type info
    "article": False,   # Article sidebars are usually ads/related posts
    "product": True,    # Product specs may be in asides
    "forum": False,     # Forum sidebars are user profiles, badges
    "generic": False,
}

_TYPE_KEEP_NAV: Dict[str, bool] = {
    "docs": True,       # Docs nav may have section links with content
    "article": False,
    "product": False,
    "forum": False,
    "generic": False,
}

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


def _extract_metadata(
    soup: BeautifulSoup, base_url: Optional[str],
) -> Tuple[str, str, List[dict], Set[str]]:
    """Extract title, meta description, structured data, and links in one pass.

    Combines the work of ``_extract_title``, ``_extract_meta_description``,
    ``_extract_structured_data``, and ``_extract_links_from_soup`` to reduce
    the number of tree traversals from ~4 to 1 + targeted finds.

    Returns ``(title, meta_desc, structured_data, links)``.
    """
    import json as _json

    # -- Title: fast targeted finds (not full tree scans) --
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    og_title = ""
    meta_title = ""
    meta_desc = ""
    og_desc = ""
    structured: List[dict] = []
    links: Set[str] = set()

    # Single pass through <head> for meta/og/structured data
    head = soup.find("head")
    if head:
        for el in head.children:
            if not hasattr(el, "name") or el.name is None:
                continue
            if el.name == "meta":
                prop = el.get("property", "")
                name = el.get("name", "")
                content = el.get("content", "").strip()
                if not content:
                    continue
                if prop == "og:title" and not og_title:
                    og_title = content
                elif prop == "og:description" and not og_desc:
                    og_desc = content
                elif name == "description" and not meta_desc:
                    meta_desc = content
                elif name == "title" and not meta_title:
                    meta_title = content
            elif el.name == "script" and el.get("type") == "application/ld+json":
                try:
                    data = _json.loads(el.string or "")
                    if isinstance(data, dict):
                        structured.append(data)
                    elif isinstance(data, list):
                        structured.extend(d for d in data if isinstance(d, dict))
                except (ValueError, TypeError):
                    pass

    # Also check for JSON-LD in body (some sites put it there)
    body = soup.find("body")
    if body:
        for script in body.find_all("script", type="application/ld+json"):
            try:
                data = _json.loads(script.string or "")
                if isinstance(data, dict):
                    structured.append(data)
                elif isinstance(data, list):
                    structured.extend(d for d in data if isinstance(d, dict))
            except (ValueError, TypeError):
                pass

    # Title fallback chain
    if not title:
        title = og_title
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
    if not title:
        title = meta_title

    # Description fallback
    if not meta_desc:
        meta_desc = og_desc

    # Links (single pass through all anchors)
    if base_url is not None:
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            absolute_url = up.urljoin(base_url, href)
            links.add(norm_url(absolute_url))

    return title, meta_desc, structured, links


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


def _has_substantial_content(el) -> bool:
    """Check if an element has enough content to be considered non-boilerplate.

    Returns True when the element contains code blocks, long text (>100 words),
    or other signals of real content rather than navigation.

    Large nav sidebars can have hundreds of words of link text and still be
    pure navigation (see fastapi-docs), so a high link density vetoes the
    "long text" and "data table" signals.
    """
    word_count = len(el.get_text(strip=True).split())
    # A sea of links is navigation even when it's long, has code labels, or
    # has tables inside.  Docs sites wrap nav labels like `openapi.json` in
    # <code>, and multi-level sidebars can render as nested lists; neither
    # is content.
    link_heavy = word_count > 0 and _link_density(el) > 0.75
    if link_heavy:
        return False
    # Real fenced code blocks (<pre>) are almost never navigation.  Inline
    # <code> alone is not a strong signal — see above.
    if el.find("pre"):
        return True
    if el.find("code") and word_count > 10:
        return True
    if word_count > 100:
        return True
    # Tables with multiple rows are usually content, not nav.
    rows = el.find_all("tr")
    if len(rows) > 2:
        return True
    return False


def clean_dom_for_content(soup: BeautifulSoup, page_type: str = "generic", keep_images: bool = False) -> None:
    keep_nav = _TYPE_KEEP_NAV.get(page_type, False)
    keep_aside = _TYPE_KEEP_ASIDE.get(page_type, False)

    for tag in soup.find_all(EXCLUDE_TAGS):
        tag.decompose()
    # Strip nav and footer — but keep them if they contain substantial
    # content (code blocks, >100 words, data tables).  Some docs sites
    # put real content inside <nav> for sidebar sections.
    # For docs pages, be more lenient with nav (may hold section content).
    for tag in soup.find_all({"nav", "footer"}):
        if keep_nav and tag.name == "nav" and _has_substantial_content(tag):
            continue
        if _has_substantial_content(tag):
            continue
        tag.decompose()
    # Context-aware: keep header/aside if inside a content area OR if
    # they have substantial content.  Docs/product pages keep asides
    # more aggressively (parameter lists, specs).
    for tag in soup.find_all({"header", "aside"}):
        if tag.find_parent(["main", "article"]):
            continue
        if keep_aside and tag.name == "aside":
            continue
        if _has_substantial_content(tag):
            continue
        tag.decompose()
    for el in soup.select(
        '[role="navigation"], [aria-hidden="true"], .sr-only, .visually-hidden, .cookie, .Cookie, .cookie-banner, .consent'
    ):
        try:
            # Don't remove role=navigation if it has substantial content
            if el.get("role") == "navigation" and _has_substantial_content(el):
                continue
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
    # Expand <details> elements: replace with their visible content so
    # collapsible sections (tabbed docs, expandable examples) are captured.
    for details in soup.find_all("details"):
        summary = details.find("summary")
        summary_text = summary.get_text(strip=True) if summary else ""
        if summary:
            summary.decompose()
        if summary_text:
            heading = soup.new_tag("p")
            heading.string = summary_text
            details.insert(0, heading)
        details.unwrap()
    # CTA link stripping: remove links whose href matches action patterns
    # (signup, login, demo, pricing) — these pollute chunks without adding
    # retrievable content.  Only strip short-text links (<6 words).
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link_text = a.get_text(strip=True)
        if len(link_text.split()) <= 5 and _CTA_PATH_RE.search(href):
            a.decompose()
    # Image handling — two modes:
    # keep_images=True (--download-images): resolve src to absolute URLs,
    #   flatten figures into plain <img> tags, and let markdownify produce
    #   ![alt](url) syntax.  The caller downloads images and rewrites paths.
    # keep_images=False (default): replace images with [Image: alt] text
    #   placeholders and discard images without alt text.
    if keep_images:
        for fig in soup.find_all("figure"):
            caption = fig.find("figcaption")
            caption_text = caption.get_text(strip=True) if caption else ""
            img = fig.find("img")
            if img:
                if caption_text:
                    img["alt"] = caption_text
                if caption:
                    caption.decompose()
                fig.unwrap()
            else:
                fig.decompose()
        for img in soup.find_all("img"):
            src = img.get("src", "").strip()
            if not src:
                img.decompose()
    else:
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


# Regex for HTML attribute fragments that leak through markdownify
_ATTR_LEAK_RE = re.compile(
    r'\s*(?:data-[\w-]+|aria-[\w-]+|style|class|id|onclick|onmouseover|onload)'
    r'="[^"]*"',
)


def _clean_markdown(text: str) -> str:
    """Post-process Markdown to remove attribute leaks and normalise whitespace."""
    # Strip any leaked HTML attributes
    text = _ATTR_LEAK_RE.sub("", text)
    # Collapse runs of 3+ blank lines to 2
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Remove trailing whitespace on each line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text


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


def html_to_markdown(
    html: str,
    base_url: Optional[str] = None,
    keep_images: bool = False,
) -> Tuple[str, str, Set[str]]:
    """Convert raw HTML to cleaned Markdown text.

    Returns ``(title, markdown, links)`` where *links* is the set of
    normalised ``<a href>`` URLs found in the document.  Extracting links
    during the same parse avoids a second BeautifulSoup pass.

    When *keep_images* is True, ``<img>`` tags are preserved so that
    markdownify produces ``![alt](src)`` references.  The caller is
    responsible for downloading images and rewriting paths.

    Extraction enrichment:
    - Meta description is prepended as a summary line when available.
    - JSON-LD structured data (FAQ Q&A, descriptions) is appended.
    - Content region is detected via readability-style scoring when no
      ``<main>`` tag exists.
    """
    soup = BeautifulSoup(html, _PARSER)
    title, meta_desc, structured, links = _extract_metadata(soup, base_url)
    page_type = classify_page(soup, url=base_url or "")
    clean_dom_for_content(soup, page_type=page_type, keep_images=keep_images)
    main = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
        or _find_content_region(soup)
        or soup.body
        or soup
    )

    if _HAS_MARKDOWNIFY:
        # escape_underscores=False: keep identifiers like my_function intact.
        # With escaping on, prose `my_function` becomes `my\_function`, which
        # tokenises differently and breaks retrieval on snake_case symbol
        # queries. Inline <code> already wraps symbols in backticks, so any
        # genuinely ambiguous cases are still safe.
        # escape_asterisks=False: same rationale — keep `*args`, `**kwargs`
        # and glob patterns readable. Emphasis collisions are rare in docs.
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

    # Post-process: strip data-* / aria-* attributes that leak through
    markdown = _clean_markdown(markdown)

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
    title, meta_desc, structured, links = _extract_metadata(soup, base_url)
    page_type = classify_page(soup, url=base_url or "")
    clean_dom_for_content(soup, page_type=page_type)

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
    title, _, _, links = _extract_metadata(soup, base_url)

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


def html_to_markdown_readerlm(html: str, base_url: Optional[str] = None) -> Tuple[str, str, Set[str]]:
    """Extract content using a ReaderLM-style small language model.

    Uses a local transformer model (jinaai/ReaderLM-v2 or similar) to convert
    HTML directly to Markdown.  Falls back to the default heuristic pipeline
    if the model is not available.

    Requires ``pip install markcrawl[ml]`` (transformers + torch).

    Returns ``(title, markdown, links)``.
    """
    try:
        import transformers  # noqa: F401
    except ImportError:
        return html_to_markdown(html, base_url)

    # Extract links and title from soup first (model only does content)
    soup = BeautifulSoup(html, _PARSER)
    title, _, _, links = _extract_metadata(soup, base_url)

    model_name = "jinaai/ReaderLM-v2"

    try:
        tokenizer = _get_readerlm_tokenizer(model_name)
        model = _get_readerlm_model(model_name)
    except Exception:
        return html_to_markdown(html, base_url)

    # Truncate HTML to fit model context (keep first ~32K chars)
    max_html_chars = 32_000
    truncated_html = html[:max_html_chars]

    messages = [{"role": "user", "content": f"Convert the following HTML to clean Markdown:\n\n{truncated_html}"}]

    try:
        input_ids = tokenizer.apply_chat_template(
            messages, return_tensors="pt", add_generation_prompt=True,
        )
        input_ids = input_ids.to(model.device)
        outputs = model.generate(
            input_ids, max_new_tokens=4096,
            do_sample=False, temperature=None, top_p=None,
        )
        # Decode only the new tokens
        new_tokens = outputs[0][input_ids.shape[1]:]
        markdown = tokenizer.decode(new_tokens, skip_special_tokens=True)
    except Exception:
        return html_to_markdown(html, base_url)

    if not markdown or len(markdown.split()) < 10:
        return html_to_markdown(html, base_url)

    return title, compact_blank_lines(markdown), links


# Lazy-loaded model cache to avoid reloading on every page
_readerlm_cache: dict = {}


def _get_readerlm_tokenizer(model_name: str):
    """Get or load the ReaderLM tokenizer (cached)."""
    key = f"tokenizer:{model_name}"
    if key not in _readerlm_cache:
        from transformers import AutoTokenizer
        _readerlm_cache[key] = AutoTokenizer.from_pretrained(model_name)
    return _readerlm_cache[key]


def _get_readerlm_model(model_name: str):
    """Get or load the ReaderLM model (cached)."""
    key = f"model:{model_name}"
    if key not in _readerlm_cache:
        import torch
        from transformers import AutoModelForCausalLM
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _readerlm_cache[key] = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        ).to(device)
    return _readerlm_cache[key]


def default_progress(enabled: bool) -> Callable[[str], None]:
    def emit(message: str) -> None:
        if enabled:
            print(message)
    return emit
