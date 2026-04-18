"""Tests for markcrawl.images — image downloading and Markdown rewriting."""

from __future__ import annotations

import os
import textwrap
from unittest.mock import MagicMock

from markcrawl.extract_content import html_to_markdown
from markcrawl.images import (
    download_image,
    download_images,
    extract_image_urls,
    rewrite_image_paths,
    safe_image_filename,
)

# ---------------------------------------------------------------------------
# safe_image_filename
# ---------------------------------------------------------------------------

class TestSafeImageFilename:
    def test_preserves_extension(self):
        name = safe_image_filename("https://example.com/photo.jpg")
        assert name.endswith(".jpg")

    def test_png_extension(self):
        name = safe_image_filename("https://example.com/img/hero.png")
        assert name.endswith(".png")

    def test_fallback_extension(self):
        name = safe_image_filename("https://example.com/image-no-ext")
        assert name.endswith(".img")

    def test_deterministic(self):
        a = safe_image_filename("https://example.com/photo.jpg")
        b = safe_image_filename("https://example.com/photo.jpg")
        assert a == b

    def test_different_urls_different_names(self):
        a = safe_image_filename("https://example.com/a.jpg")
        b = safe_image_filename("https://example.com/b.jpg")
        assert a != b

    def test_long_url_truncated(self):
        long = "https://example.com/" + "a" * 200 + ".png"
        name = safe_image_filename(long)
        assert len(name) < 120


# ---------------------------------------------------------------------------
# extract_image_urls
# ---------------------------------------------------------------------------

class TestExtractImageUrls:
    def test_extracts_markdown_images(self):
        md = "Some text ![Logo](https://example.com/logo.png) more text"
        pairs = extract_image_urls(md)
        assert len(pairs) == 1
        assert pairs[0] == ("Logo", "https://example.com/logo.png")

    def test_multiple_images(self):
        md = "![A](https://a.com/1.jpg) text ![B](https://b.com/2.png)"
        pairs = extract_image_urls(md)
        assert len(pairs) == 2

    def test_no_images(self):
        md = "Just regular text with a [link](https://example.com)"
        pairs = extract_image_urls(md)
        assert len(pairs) == 0

    def test_empty_alt(self):
        md = "![](https://example.com/img.png)"
        pairs = extract_image_urls(md)
        assert len(pairs) == 1
        assert pairs[0] == ("", "https://example.com/img.png")


# ---------------------------------------------------------------------------
# rewrite_image_paths
# ---------------------------------------------------------------------------

class TestRewriteImagePaths:
    def test_rewrites_known_urls(self):
        md = "![Photo](https://example.com/photo.jpg)"
        url_map = {"https://example.com/photo.jpg": "photo-abc123.jpg"}
        result = rewrite_image_paths(md, url_map)
        assert result == "![Photo](assets/photo-abc123.jpg)"

    def test_leaves_unknown_urls(self):
        md = "![Logo](https://example.com/logo.png)"
        url_map = {}
        result = rewrite_image_paths(md, url_map)
        assert result == "![Logo](https://example.com/logo.png)"

    def test_mixed_known_and_unknown(self):
        md = "![A](https://a.com/1.jpg) text ![B](https://b.com/2.jpg)"
        url_map = {"https://a.com/1.jpg": "1-hash.jpg"}
        result = rewrite_image_paths(md, url_map)
        assert "assets/1-hash.jpg" in result
        assert "https://b.com/2.jpg" in result

    def test_preserves_alt_text(self):
        md = "![Architecture diagram](https://example.com/arch.png)"
        url_map = {"https://example.com/arch.png": "arch-abc.png"}
        result = rewrite_image_paths(md, url_map)
        assert "![Architecture diagram](assets/arch-abc.png)" in result


# ---------------------------------------------------------------------------
# download_image
# ---------------------------------------------------------------------------

class TestDownloadImage:
    def test_successful_download(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\x89PNG" + b"\x00" * 10000
        resp.headers = {"content-type": "image/png"}
        session.get.return_value = resp

        result = download_image(session, "https://example.com/photo.png", str(tmp_path), timeout=10)
        assert result is not None
        assert os.path.exists(os.path.join(str(tmp_path), result))

    def test_skips_small_images(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\x00" * 100  # Only 100 bytes
        resp.headers = {"content-type": "image/gif"}
        session.get.return_value = resp

        result = download_image(session, "https://example.com/icon.gif", str(tmp_path), timeout=10)
        assert result is None

    def test_skips_non_image_content(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"<html>not an image</html>" * 1000
        resp.headers = {"content-type": "text/html"}
        session.get.return_value = resp

        result = download_image(session, "https://example.com/page", str(tmp_path), timeout=10)
        assert result is None

    def test_handles_404(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 404
        session.get.return_value = resp

        result = download_image(session, "https://example.com/missing.png", str(tmp_path), timeout=10)
        assert result is None

    def test_handles_network_error(self, tmp_path):
        session = MagicMock()
        session.get.side_effect = ConnectionError("connection refused")

        result = download_image(session, "https://example.com/photo.png", str(tmp_path), timeout=10)
        assert result is None


# ---------------------------------------------------------------------------
# download_images (batch)
# ---------------------------------------------------------------------------

class TestDownloadImages:
    def test_downloads_multiple(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\x89PNG" + b"\x00" * 10000
        resp.headers = {"content-type": "image/png"}
        session.get.return_value = resp

        pairs = [
            ("Photo A", "https://example.com/a.png"),
            ("Photo B", "https://example.com/b.png"),
        ]
        result = download_images(session, pairs, str(tmp_path), timeout=10)
        assert len(result) == 2
        assert "https://example.com/a.png" in result
        assert "https://example.com/b.png" in result

    def test_deduplicates_urls(self, tmp_path):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\x89PNG" + b"\x00" * 10000
        resp.headers = {"content-type": "image/png"}
        session.get.return_value = resp

        pairs = [
            ("First", "https://example.com/same.png"),
            ("Second", "https://example.com/same.png"),
        ]
        result = download_images(session, pairs, str(tmp_path), timeout=10)
        assert len(result) == 1
        assert session.get.call_count == 1

    def test_creates_assets_dir(self, tmp_path):
        session = MagicMock()
        session.get.return_value = MagicMock(status_code=404)

        assets_dir = str(tmp_path / "assets")
        download_images(session, [("Alt", "https://example.com/x.png")], assets_dir, timeout=10)
        assert os.path.isdir(assets_dir)


# ---------------------------------------------------------------------------
# keep_images mode in html_to_markdown
# ---------------------------------------------------------------------------

class TestKeepImagesExtraction:
    def test_keep_images_produces_markdown_image_syntax(self):
        html = '<html><body><main><p>Before</p><img src="https://example.com/photo.jpg" alt="Sunset"><p>After</p></main></body></html>'
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=True)
        assert "![Sunset]" in content
        assert "photo.jpg" in content

    def test_keep_images_false_produces_placeholder(self):
        html = '<html><body><main><p>Before</p><img src="https://example.com/photo.jpg" alt="Sunset"><p>After</p></main></body></html>'
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=False)
        assert "[Image: Sunset]" in content

    def test_keep_images_figcaption_becomes_alt(self):
        html = '<html><body><main><figure><img src="https://example.com/x.png" alt="Old alt"><figcaption>Better caption</figcaption></figure></main></body></html>'
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=True)
        assert "Better caption" in content
        assert "x.png" in content

    def test_keep_images_removes_img_without_src(self):
        html = '<html><body><main><p>Content here with enough words to pass the filter easily.</p><img alt="No source"></main></body></html>'
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=True)
        assert "No source" not in content

    def test_keep_images_figure_without_img_removed(self):
        html = '<html><body><main><p>Content with enough words to pass.</p><figure><figcaption>Caption only</figcaption></figure></main></body></html>'
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=True)
        assert "Caption only" not in content


# ---------------------------------------------------------------------------
# End-to-end: extraction + rewrite
# ---------------------------------------------------------------------------

class TestEndToEndImagePipeline:
    def test_extract_then_rewrite(self):
        html = textwrap.dedent("""\
            <html><body><main>
            <h1>Gallery</h1>
            <p>Check out these photos with enough words to pass the min word filter.</p>
            <img src="https://cdn.example.com/photo1.jpg" alt="Mountain view">
            <img src="https://cdn.example.com/photo2.png" alt="Ocean sunset">
            </main></body></html>
        """)
        _, content, _ = html_to_markdown(html, base_url="https://example.com/", keep_images=True)

        pairs = extract_image_urls(content)
        assert len(pairs) == 2

        url_map = {
            "https://cdn.example.com/photo1.jpg": "photo1-abc.jpg",
            "https://cdn.example.com/photo2.png": "photo2-def.png",
        }
        rewritten = rewrite_image_paths(content, url_map)
        assert "assets/photo1-abc.jpg" in rewritten
        assert "assets/photo2-def.png" in rewritten
        assert "Mountain view" in rewritten
        assert "Ocean sunset" in rewritten
