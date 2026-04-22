"""Tests for markcrawl.screenshots — screenshot capture + config."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

from markcrawl.screenshots import (
    SCREENSHOTS_DIR,
    ScreenshotConfig,
    capture_screenshot,
    safe_screenshot_filename,
)

# ---------------------------------------------------------------------------
# safe_screenshot_filename
# ---------------------------------------------------------------------------

class TestSafeScreenshotFilename:
    def test_png_extension(self):
        name = safe_screenshot_filename("https://example.com/page", "png")
        assert name.endswith(".png")

    def test_jpg_extension(self):
        name = safe_screenshot_filename("https://example.com/page", "jpg")
        assert name.endswith(".jpg")

    def test_deterministic(self):
        a = safe_screenshot_filename("https://example.com/page", "png")
        b = safe_screenshot_filename("https://example.com/page", "png")
        assert a == b

    def test_different_urls_different_names(self):
        a = safe_screenshot_filename("https://example.com/a", "png")
        b = safe_screenshot_filename("https://example.com/b", "png")
        assert a != b

    def test_accepts_leading_dot_ext(self):
        name = safe_screenshot_filename("https://example.com/page", ".png")
        assert name.endswith(".png")
        assert ".png.png" not in name

    def test_long_url_bounded(self):
        long = "https://example.com/" + "a" * 200
        name = safe_screenshot_filename(long, "png")
        assert len(name) < 120

    def test_root_url_fallback(self):
        name = safe_screenshot_filename("https://example.com/", "png")
        assert name.endswith(".png")
        # Stub should fall back to netloc when path is empty
        assert "example.com" in name


# ---------------------------------------------------------------------------
# ScreenshotConfig
# ---------------------------------------------------------------------------

class TestScreenshotConfig:
    def test_defaults(self):
        cfg = ScreenshotConfig()
        assert cfg.enabled is False
        assert cfg.full_page is True
        assert cfg.fmt == "png"
        assert cfg.viewport_width == 1920
        assert cfg.viewport_height == 1080
        assert cfg.wait_ms == 1500
        assert cfg.selector is None


# ---------------------------------------------------------------------------
# capture_screenshot — mocked Playwright page
# ---------------------------------------------------------------------------

class TestCaptureScreenshot:
    def test_disabled_returns_none(self, tmp_path):
        page = MagicMock()
        cfg = ScreenshotConfig(enabled=False)
        fname, err = capture_screenshot(page, "https://x.com/", cfg, str(tmp_path))
        assert fname is None
        assert err is None
        page.screenshot.assert_not_called()

    def test_success_png(self, tmp_path):
        page = MagicMock()

        def _fake_shot(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"\x89PNG" + b"\x00" * 100)

        page.screenshot.side_effect = _fake_shot

        cfg = ScreenshotConfig(enabled=True, fmt="png", full_page=True)
        fname, err = capture_screenshot(page, "https://x.com/dash", cfg, str(tmp_path))
        assert err is None
        assert fname is not None
        assert fname.endswith(".png")
        assert os.path.exists(os.path.join(str(tmp_path), fname))

        page.screenshot.assert_called_once()
        call_kwargs = page.screenshot.call_args.kwargs
        assert call_kwargs["type"] == "png"
        assert call_kwargs["full_page"] is True
        assert "quality" not in call_kwargs

    def test_success_jpeg_sets_quality(self, tmp_path):
        page = MagicMock()

        def _fake_shot(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"\xff\xd8\xff" + b"\x00" * 100)

        page.screenshot.side_effect = _fake_shot

        cfg = ScreenshotConfig(enabled=True, fmt="jpeg", full_page=True)
        fname, err = capture_screenshot(page, "https://x.com/dash", cfg, str(tmp_path))
        assert err is None
        assert fname is not None
        assert fname.endswith(".jpg")

        call_kwargs = page.screenshot.call_args.kwargs
        assert call_kwargs["type"] == "jpeg"
        assert call_kwargs["quality"] == 85

    def test_selector_uses_locator(self, tmp_path):
        page = MagicMock()
        locator = MagicMock()
        first = MagicMock()

        def _fake_shot(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"\x89PNG" + b"\x00" * 100)

        first.screenshot.side_effect = _fake_shot
        locator.first = first
        page.locator.return_value = locator

        cfg = ScreenshotConfig(
            enabled=True, fmt="png", full_page=True, selector=".dashboard",
        )
        fname, err = capture_screenshot(page, "https://x.com/dash", cfg, str(tmp_path))
        assert err is None
        assert fname is not None

        page.locator.assert_called_once_with(".dashboard")
        # Element-scoped shots must NOT pass full_page (Playwright rejects it).
        first.screenshot.assert_called_once()
        assert "full_page" not in first.screenshot.call_args.kwargs
        page.screenshot.assert_not_called()

    def test_selector_timeout_propagates_to_wait_and_shot(self, tmp_path):
        page = MagicMock()
        locator = MagicMock()
        first = MagicMock()

        def _fake_shot(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"\x89PNG" + b"\x00" * 100)

        first.screenshot.side_effect = _fake_shot
        locator.first = first
        page.locator.return_value = locator

        cfg = ScreenshotConfig(
            enabled=True, fmt="png", full_page=True, selector=".x",
        )
        fname, err = capture_screenshot(
            page, "https://x.com/", cfg, str(tmp_path), timeout_ms=5000,
        )
        assert err is None
        assert fname is not None

        # Both wait_for (for implicit wait) and screenshot must see the timeout.
        first.wait_for.assert_called_once()
        assert first.wait_for.call_args.kwargs.get("timeout") == 5000
        assert first.screenshot.call_args.kwargs.get("timeout") == 5000

    def test_failure_records_error_and_no_file(self, tmp_path):
        page = MagicMock()
        page.screenshot.side_effect = TimeoutError("page timeout after 30000ms")

        cfg = ScreenshotConfig(enabled=True, fmt="png")
        fname, err = capture_screenshot(page, "https://x.com/dash", cfg, str(tmp_path))
        assert fname is None
        assert err is not None
        assert "TimeoutError" in err
        assert "30000ms" in err

        # No stray empty file left behind.
        assert os.listdir(str(tmp_path)) == []

    def test_failure_cleans_up_partial_file(self, tmp_path):
        page = MagicMock()

        def _partial_then_fail(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"partial")
            raise RuntimeError("disk full mid-write")

        page.screenshot.side_effect = _partial_then_fail

        cfg = ScreenshotConfig(enabled=True, fmt="png")
        fname, err = capture_screenshot(page, "https://x.com/dash", cfg, str(tmp_path))
        assert fname is None
        assert err is not None
        assert "RuntimeError" in err
        assert os.listdir(str(tmp_path)) == []

    def test_creates_screenshots_dir(self, tmp_path):
        page = MagicMock()

        def _fake_shot(path: str, **kwargs):
            with open(path, "wb") as f:
                f.write(b"\x89PNG" + b"\x00" * 100)

        page.screenshot.side_effect = _fake_shot

        target = str(tmp_path / "nested" / "screenshots")
        cfg = ScreenshotConfig(enabled=True, fmt="png")
        fname, err = capture_screenshot(page, "https://x.com/", cfg, target)
        assert err is None
        assert fname is not None
        assert os.path.isdir(target)


# ---------------------------------------------------------------------------
# SCREENSHOTS_DIR constant
# ---------------------------------------------------------------------------

def test_screenshots_dir_constant():
    assert SCREENSHOTS_DIR == "screenshots"
