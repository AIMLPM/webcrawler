"""Image downloading and Markdown rewriting for --download-images."""
from __future__ import annotations

import hashlib
import logging
import os
import re
import urllib.parse as up
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Regex matching markdown image syntax: ![alt](url)
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

ASSETS_DIR = "assets"


def safe_image_filename(url: str) -> str:
    """Derive a filesystem-safe filename for an image URL.

    Uses the original file extension when present, falls back to ``.img``.
    A 12-char hash suffix ensures uniqueness.
    """
    parsed = up.urlsplit(url)
    path = parsed.path.rstrip("/")
    _, ext = os.path.splitext(path)
    if not ext or len(ext) > 6:
        ext = ".img"
    # Short readable stub from the path
    basename = os.path.basename(path).rsplit(".", 1)[0] if path else "image"
    stub = re.sub(r"[^a-zA-Z0-9._-]+", "-", basename)[:80].strip("-") or "image"
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{stub}-{h}{ext}"


def extract_image_urls(markdown: str) -> List[Tuple[str, str]]:
    """Extract ``(alt, url)`` pairs from Markdown ``![alt](url)`` references."""
    return _MD_IMAGE_RE.findall(markdown)


def download_image(
    session: Any,
    url: str,
    assets_dir: str,
    timeout: int,
    min_bytes: int = 5000,
) -> Optional[str]:
    """Download one image and save to *assets_dir*.

    Returns the local filename on success, or ``None`` if the download fails
    or the file is smaller than *min_bytes*.
    """
    try:
        resp = session.get(url, timeout=timeout)
    except Exception as exc:
        logger.debug("Image download failed for %s: %s", url, exc)
        return None

    status = getattr(resp, "status_code", None)
    if status is None:
        status = getattr(resp, "status", None)
    if status is None or status >= 400:
        return None

    content = getattr(resp, "content", b"")
    if len(content) < min_bytes:
        logger.debug("Image too small (%d bytes), skipping: %s", len(content), url)
        return None

    content_type = ""
    headers = getattr(resp, "headers", {})
    if headers:
        content_type = headers.get("content-type", "")
    if content_type and not content_type.startswith("image/"):
        logger.debug("Non-image content-type %s, skipping: %s", content_type, url)
        return None

    filename = safe_image_filename(url)
    filepath = os.path.join(assets_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    return filename


def download_images(
    session: Any,
    image_pairs: List[Tuple[str, str]],
    assets_dir: str,
    timeout: int,
    min_bytes: int = 5000,
) -> Dict[str, str]:
    """Download images and return a mapping of ``{url: local_filename}``.

    *image_pairs* is a list of ``(alt, url)`` tuples as returned by
    :func:`extract_image_urls`.  Only successfully downloaded images
    appear in the returned dict.
    """
    os.makedirs(assets_dir, exist_ok=True)
    url_map: Dict[str, str] = {}
    seen: set = set()
    for _alt, url in image_pairs:
        if url in seen:
            continue
        seen.add(url)
        filename = download_image(session, url, assets_dir, timeout, min_bytes)
        if filename:
            url_map[url] = filename
    return url_map


def rewrite_image_paths(markdown: str, url_map: Dict[str, str]) -> str:
    """Replace absolute image URLs with local ``assets/`` paths in Markdown."""
    def _replace(match: re.Match) -> str:
        alt = match.group(1)
        url = match.group(2)
        if url in url_map:
            return f"![{alt}]({ASSETS_DIR}/{url_map[url]})"
        return match.group(0)

    return _MD_IMAGE_RE.sub(_replace, markdown)
