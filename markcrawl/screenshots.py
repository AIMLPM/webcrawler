"""Screenshot capture for --screenshot.

Captures a full-page (or selector-cropped) PNG/JPEG of each rendered page
through the existing Playwright context.  Files land in
``{out_dir}/screenshots/`` with deterministic hash-suffixed names, and the
per-page JSONL record gets a ``screenshot`` (or ``screenshot_error``) field.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import urllib.parse as up
from dataclasses import dataclass
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = "screenshots"


@dataclass
class ScreenshotConfig:
    """User-facing configuration for the screenshot feature."""
    enabled: bool = False
    viewport_width: int = 1920
    viewport_height: int = 1080
    full_page: bool = True
    selector: Optional[str] = None
    fmt: str = "png"  # "png" or "jpeg"
    wait_ms: int = 1500  # extra wait after networkidle for late-rendering JS


def safe_screenshot_filename(url: str, ext: str) -> str:
    """Derive a filesystem-safe filename for a page screenshot.

    Mirrors :func:`markcrawl.images.safe_image_filename` in spirit: a short
    readable stub from the URL path plus a 12-char hash for uniqueness.
    """
    parsed = up.urlsplit(url)
    path = parsed.path.rstrip("/")
    basename = os.path.basename(path) or parsed.netloc or "page"
    stub = re.sub(r"[^a-zA-Z0-9._-]+", "-", basename)[:80].strip("-") or "page"
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    if not ext.startswith("."):
        ext = "." + ext
    return f"{stub}-{h}{ext}"


def capture_screenshot(
    page: Any,
    url: str,
    config: ScreenshotConfig,
    screenshots_dir: str,
    timeout_ms: Optional[int] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Capture a screenshot of a Playwright *page*.

    The caller is responsible for navigation and wait strategy — this function
    only issues the screenshot call against an already-loaded page.

    ``timeout_ms`` bounds how long Playwright waits (primarily for selector
    resolution when ``config.selector`` is set).  If *None*, Playwright's
    30-second default applies, which can compound badly across many pages
    when a selector doesn't match — callers should pass the user's
    ``--timeout`` value.

    Returns ``(filename, error_message)``.  On success, ``filename`` is the
    basename (relative to *screenshots_dir*) and *error_message* is *None*.
    On failure, ``filename`` is *None* and *error_message* is a short string
    describing the cause (recorded in the JSONL row).
    """
    if not config.enabled:
        return None, None

    ext = "jpg" if config.fmt == "jpeg" else "png"
    filename = safe_screenshot_filename(url, ext)
    filepath = os.path.join(screenshots_dir, filename)

    shot_kwargs: dict = {
        "path": filepath,
        "type": "jpeg" if config.fmt == "jpeg" else "png",
        "full_page": config.full_page,
    }
    if config.fmt == "jpeg":
        shot_kwargs["quality"] = 85
    if timeout_ms is not None:
        shot_kwargs["timeout"] = timeout_ms

    try:
        os.makedirs(screenshots_dir, exist_ok=True)
        if config.selector:
            locator = page.locator(config.selector).first
            # Explicit wait_for bounds the locator-resolution phase.  The
            # `timeout` kwarg on .screenshot() only bounds the capture
            # itself, leaving Playwright's 30s default implicit-wait in
            # place — which compounds painfully for non-matching selectors
            # across many pages.
            if timeout_ms is not None:
                locator.wait_for(state="visible", timeout=timeout_ms)
            # Scoped screenshots don't support full_page — Playwright raises if passed.
            scoped_kwargs: dict = {
                "path": filepath,
                "type": shot_kwargs["type"],
            }
            if config.fmt == "jpeg":
                scoped_kwargs["quality"] = 85
            if timeout_ms is not None:
                scoped_kwargs["timeout"] = timeout_ms
            locator.screenshot(**scoped_kwargs)
        else:
            page.screenshot(**shot_kwargs)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        logger.warning("Screenshot failed for %s: %s", url, err)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return None, err

    return filename, None
