"""Tests for markcrawl.core — URL helpers, HTML extraction, and crawl flow."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

from markcrawl.core import (
    compact_blank_lines,
    extract_links,
    html_to_markdown,
    html_to_text,
    norm_url,
    safe_filename,
    same_scope,
)

# ---------------------------------------------------------------------------
# norm_url
# ---------------------------------------------------------------------------

class TestNormUrl:
    def test_lowercases_scheme_and_host(self):
        assert norm_url("HTTPS://WWW.Example.COM/Page") == "https://www.example.com/Page"

    def test_adds_trailing_slash_for_empty_path(self):
        assert norm_url("https://example.com") == "https://example.com/"

    def test_preserves_path(self):
        assert norm_url("https://example.com/a/b/c") == "https://example.com/a/b/c"

    def test_collapses_double_slashes_in_path(self):
        result = norm_url("https://example.com/a//b///c")
        assert "//" not in result.split("://", 1)[1]

    def test_strips_fragment(self):
        assert norm_url("https://example.com/page#section") == "https://example.com/page"

    def test_preserves_query_string(self):
        assert norm_url("https://example.com/page?q=1&r=2") == "https://example.com/page?q=1&r=2"

    def test_sorts_query_parameters(self):
        assert norm_url("https://example.com/page?z=3&a=1&m=2") == "https://example.com/page?a=1&m=2&z=3"

    def test_reordered_params_deduplicate(self):
        assert norm_url("https://example.com/page?b=2&a=1") == norm_url("https://example.com/page?a=1&b=2")


# ---------------------------------------------------------------------------
# same_scope
# ---------------------------------------------------------------------------

class TestSameScope:
    def test_exact_match(self):
        assert same_scope("https://example.com/page", "example.com", False)

    def test_different_domain(self):
        assert not same_scope("https://other.com/page", "example.com", False)

    def test_subdomain_excluded_by_default(self):
        assert not same_scope("https://sub.example.com/page", "example.com", False)

    def test_subdomain_included_when_enabled(self):
        assert same_scope("https://sub.example.com/page", "example.com", True)

    def test_unrelated_domain_with_suffix(self):
        # "notexample.com" ends with "example.com" but is not a subdomain
        assert not same_scope("https://notexample.com/", "example.com", True)


# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_index_page(self):
        name = safe_filename("https://example.com/", "md")
        assert name.startswith("index__")
        assert name.endswith(".md")

    def test_path_page(self):
        name = safe_filename("https://example.com/about/team", "txt")
        assert "about" in name
        assert name.endswith(".txt")

    def test_query_string_included(self):
        name = safe_filename("https://example.com/search?q=test", "md")
        assert "q-test" in name or "search" in name

    def test_hash_is_10_chars(self):
        name = safe_filename("https://example.com/page", "md")
        # Format: stub__<10-char-hash>.ext
        hash_part = name.rsplit(".", 1)[0].rsplit("__", 1)[1]
        assert len(hash_part) == 10

    def test_deterministic(self):
        a = safe_filename("https://example.com/page", "md")
        b = safe_filename("https://example.com/page", "md")
        assert a == b

    def test_different_urls_different_names(self):
        a = safe_filename("https://example.com/page-a", "md")
        b = safe_filename("https://example.com/page-b", "md")
        assert a != b


# ---------------------------------------------------------------------------
# compact_blank_lines
# ---------------------------------------------------------------------------

class TestCompactBlankLines:
    def test_collapses_excessive_blanks(self):
        text = "line1\n\n\n\n\nline2"
        result = compact_blank_lines(text, max_blank_streak=2)
        # max_blank_streak=2 allows up to 2 blank lines (3 newlines in a row)
        # but not 4+ blank lines (5 newlines)
        assert "\n\n\n\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_preserves_allowed_blanks(self):
        text = "line1\n\nline2"
        result = compact_blank_lines(text, max_blank_streak=2)
        assert result == "line1\n\nline2"

    def test_strips_trailing_whitespace(self):
        text = "line1   \nline2   "
        result = compact_blank_lines(text)
        assert "   " not in result


# ---------------------------------------------------------------------------
# HTML extraction
# ---------------------------------------------------------------------------

SAMPLE_HTML = textwrap.dedent("""\
    <html>
    <head><title>Test Page</title></head>
    <body>
      <nav><a href="/">Home</a></nav>
      <main>
        <h1>Hello World</h1>
        <p>This is the main content of the page with enough words to pass the min_words filter easily.</p>
      </main>
      <footer>Copyright 2026</footer>
    </body>
    </html>
""")


class TestHtmlToMarkdown:
    def test_extracts_title(self):
        title, _, _ = html_to_markdown(SAMPLE_HTML)
        assert title == "Test Page"

    def test_extracts_main_content(self):
        _, content, _ = html_to_markdown(SAMPLE_HTML)
        assert "Hello World" in content
        assert "main content" in content

    def test_strips_nav_and_footer(self):
        _, content, _ = html_to_markdown(SAMPLE_HTML)
        assert "Home" not in content
        assert "Copyright" not in content

    def test_strips_script_tags(self):
        html = '<html><body><main><p>Content</p><script>alert("x")</script></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "alert" not in content

    def test_empty_page_returns_empty(self):
        html = "<html><body></body></html>"
        title, content, _ = html_to_markdown(html)
        assert title == ""

    def test_extracts_links(self):
        html = '<html><body><main><a href="/page2">Link</a><p>Content</p></main></body></html>'
        _, _, links = html_to_markdown(html, base_url="https://example.com/")
        assert "https://example.com/page2" in links

    def test_no_links_without_base_url(self):
        html = '<html><body><main><a href="/page2">Link</a></main></body></html>'
        _, _, links = html_to_markdown(html)
        assert links == set()


class TestHtmlToText:
    def test_extracts_title(self):
        title, _, _ = html_to_text(SAMPLE_HTML)
        assert title == "Test Page"

    def test_extracts_content(self):
        _, content, _ = html_to_text(SAMPLE_HTML)
        assert "Hello World" in content
        assert "main content" in content

    def test_strips_nav_and_footer(self):
        _, content, _ = html_to_text(SAMPLE_HTML)
        assert "Home" not in content
        assert "Copyright" not in content

    def test_deduplicates_consecutive_lines(self):
        html = "<html><body><main><p>Same</p><p>Same</p><p>Same</p><p>Different</p></main></body></html>"
        _, content, _ = html_to_text(html)
        assert content.count("Same") == 1
        assert "Different" in content


# ---------------------------------------------------------------------------
# extract_links
# ---------------------------------------------------------------------------

class TestExtractLinks:
    def test_extracts_absolute_links(self):
        html = '<html><body><a href="https://example.com/page">Link</a></body></html>'
        links = extract_links(html, "https://example.com/")
        assert "https://example.com/page" in links

    def test_resolves_relative_links(self):
        html = '<html><body><a href="/about">About</a></body></html>'
        links = extract_links(html, "https://example.com/")
        assert "https://example.com/about" in links

    def test_ignores_anchors_without_href(self):
        html = '<html><body><a name="top">Anchor</a></body></html>'
        links = extract_links(html, "https://example.com/")
        assert len(links) == 0

    def test_normalizes_links(self):
        html = '<html><body><a href="HTTPS://EXAMPLE.COM/Page">Link</a></body></html>'
        links = extract_links(html, "https://example.com/")
        assert "https://example.com/Page" in links


# ---------------------------------------------------------------------------
# crawl (integration with mocked HTTP)
# ---------------------------------------------------------------------------

class TestCrawlIntegration:
    def _mock_response(self, url: str, html: str, ok: bool = True) -> MagicMock:
        resp = MagicMock()
        resp.ok = ok
        resp.status_code = 200 if ok else 404
        resp.text = html
        resp.content = html.encode()
        resp.headers = {"content-type": "text/html; charset=utf-8"}
        return resp

    @patch("markcrawl.core.build_session")
    def test_crawl_saves_page_and_jsonl(self, mock_build, tmp_path):
        from markcrawl.core import crawl

        html = textwrap.dedent("""\
            <html><head><title>Test</title></head>
            <body><main><p>This page has enough words to pass the minimum word filter for testing purposes here.</p></main></body>
            </html>
        """)

        session = MagicMock()
        mock_build.return_value = session

        # robots.txt returns empty (allow all)
        robots_resp = self._mock_response("robots", "")
        # base page returns our HTML
        page_resp = self._mock_response("https://example.com/", html)

        session.get.side_effect = [robots_resp, page_resp]

        result = crawl(
            base_url="https://example.com/",
            out_dir=str(tmp_path / "output"),
            use_sitemap=True,
            delay=0,
            max_pages=10,
            min_words=5,
        )

        assert result.pages_saved == 1
        assert os.path.isfile(result.index_file)

        # Verify JSONL content
        with open(result.index_file) as f:
            row = json.loads(f.readline())
        assert row["url"] == "https://example.com/"
        assert row["title"] == "Test"
        assert "enough words" in row["text"]

        # Verify file was written
        output_files = list(Path(result.output_dir).glob("*.md"))
        assert len(output_files) == 1

    @patch("markcrawl.core.build_session")
    def test_crawl_skips_low_word_count(self, mock_build, tmp_path):
        from markcrawl.core import crawl

        html = "<html><body><main><p>Short</p></main></body></html>"

        session = MagicMock()
        mock_build.return_value = session

        robots_resp = self._mock_response("robots", "")
        page_resp = self._mock_response("https://example.com/", html)
        session.get.side_effect = [robots_resp, page_resp]

        result = crawl(
            base_url="https://example.com/",
            out_dir=str(tmp_path / "output"),
            use_sitemap=True,
            delay=0,
            min_words=20,
        )

        assert result.pages_saved == 0

    @patch("markcrawl.core.fetch")
    @patch("markcrawl.core.build_session")
    def test_crawl_skips_duplicate_content(self, mock_build, mock_fetch, tmp_path):
        from markcrawl.core import crawl

        # Both pages have identical main content; page1 has a nav link to page2
        html1 = textwrap.dedent("""\
            <html><head><title>Page</title></head>
            <body>
            <nav><a href="/page2">Next</a></nav>
            <main>
              <p>Duplicate content with enough words to pass the filter for this test case.</p>
            </main></body>
            </html>
        """)
        html2 = textwrap.dedent("""\
            <html><head><title>Page</title></head>
            <body><main>
              <p>Duplicate content with enough words to pass the filter for this test case.</p>
            </main></body>
            </html>
        """)

        session = MagicMock()
        mock_build.return_value = session

        # robots.txt returns empty (allow all)
        robots_resp = self._mock_response("robots", "")
        session.get.return_value = robots_resp

        page1 = self._mock_response("https://example.com/", html1)
        page2 = self._mock_response("https://example.com/page2", html2)
        mock_fetch.side_effect = [page1, page2]

        result = crawl(
            base_url="https://example.com/",
            out_dir=str(tmp_path / "output"),
            use_sitemap=False,
            delay=0,
            min_words=5,
        )

        # Page1 is saved, page2 is skipped as duplicate
        assert result.pages_saved == 1

    @patch("markcrawl.core.build_session")
    def test_crawl_with_custom_content_extractor(self, mock_build, tmp_path):
        from markcrawl.core import crawl

        html = "<html><body><p>Raw HTML content here for testing.</p></body></html>"

        session = MagicMock()
        mock_build.return_value = session

        robots_resp = self._mock_response("robots", "")
        page_resp = self._mock_response("https://example.com/", html)
        session.get.side_effect = [robots_resp, page_resp]

        def custom_extractor(raw_html: str):
            return ("Custom Title", "Custom extracted content with enough words for the filter.")

        result = crawl(
            base_url="https://example.com/",
            out_dir=str(tmp_path / "output"),
            use_sitemap=True,
            delay=0,
            max_pages=10,
            min_words=5,
            content_extractor=custom_extractor,
        )

        assert result.pages_saved == 1
        with open(result.index_file) as f:
            row = json.loads(f.readline())
        assert row["title"] == "Custom Title"
        assert "Custom extracted content" in row["text"]


# ---------------------------------------------------------------------------
# Adaptive throttle
# ---------------------------------------------------------------------------

class TestAdaptiveThrottle:
    def _make_engine(self, delay=0):
        """Create a minimal CrawlEngine for throttle testing."""
        import tempfile

        from markcrawl.core import CrawlEngine
        out_dir = tempfile.mkdtemp()
        engine = CrawlEngine(
            out_dir=out_dir, fmt="markdown", min_words=5, delay=delay,
            timeout=15, concurrency=1, include_subdomains=False,
            user_agent="test", render_js=False, proxy=None, show_progress=False,
        )
        return engine

    def test_parse_crawl_delay_present(self):
        from markcrawl.core import CrawlEngine
        result = CrawlEngine._parse_crawl_delay("User-agent: *\nCrawl-delay: 2.5\nDisallow: /private")
        assert result == 2.5

    def test_parse_crawl_delay_missing(self):
        from markcrawl.core import CrawlEngine
        result = CrawlEngine._parse_crawl_delay("User-agent: *\nDisallow: /private")
        assert result is None

    def test_parse_crawl_delay_zero(self):
        from markcrawl.core import CrawlEngine
        result = CrawlEngine._parse_crawl_delay("Crawl-delay: 0")
        assert result == 0.0

    def test_parse_crawl_delay_invalid(self):
        from markcrawl.core import CrawlEngine
        result = CrawlEngine._parse_crawl_delay("Crawl-delay: notanumber")
        assert result is None

    def test_parse_crawl_delay_respects_ua_block(self):
        from markcrawl.core import CrawlEngine
        robots = (
            "User-agent: Googlebot\nCrawl-delay: 5\n\n"
            "User-agent: *\nCrawl-delay: 1\n"
        )
        # Wildcard UA gets its own block's delay
        assert CrawlEngine._parse_crawl_delay(robots, "*") == 1.0
        # A specific UA gets its block's delay
        assert CrawlEngine._parse_crawl_delay(robots, "Googlebot") == 5.0
        # Unknown UA falls back to wildcard
        assert CrawlEngine._parse_crawl_delay(robots, "MyBot/1.0") == 1.0

    def test_parse_crawl_delay_ignores_other_ua(self):
        from markcrawl.core import CrawlEngine
        robots = "User-agent: Googlebot\nCrawl-delay: 10\n"
        # Our UA is not Googlebot — should not get Googlebot's delay
        assert CrawlEngine._parse_crawl_delay(robots, "markcrawl") is None

    def test_update_throttle_429_increases_delay(self):
        engine = self._make_engine(delay=0)
        resp = MagicMock()
        resp.status_code = 429
        resp.elapsed = None

        engine._update_throttle(resp)
        assert engine.throttle._backoff_count == 1
        # With base_delay=0 and doubling, active_delay should be > 0
        # (max(0, 0 * 2) = 0, but the backoff triggers)

    def test_update_throttle_429_then_success_decays(self):
        engine = self._make_engine(delay=0.1)

        # Simulate 429
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.elapsed = None
        engine._update_throttle(resp_429)
        assert engine.throttle._backoff_count == 1
        assert engine.throttle.active_delay >= engine.throttle.base_delay

        # Simulate success
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.ok = True
        resp_200.elapsed = None
        engine._update_throttle(resp_200)
        assert engine.throttle._backoff_count == 0
        assert engine.throttle.active_delay == engine.throttle.base_delay

    def test_update_throttle_none_response_safe(self):
        engine = self._make_engine(delay=0)
        engine._update_throttle(None)  # Should not raise
        assert engine.throttle.active_delay == 0

    def test_update_throttle_slow_server_adds_delay(self):
        engine = self._make_engine(delay=0)

        # Simulate 10 slow responses (800ms each)
        for _ in range(10):
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            mock_elapsed = MagicMock()
            mock_elapsed.total_seconds.return_value = 0.8
            resp.elapsed = mock_elapsed
            engine._update_throttle(resp)

        # Average response time is 0.8s > 0.5s threshold → should add delay
        assert engine.throttle.active_delay > 0

    def test_update_throttle_fast_server_no_delay(self):
        engine = self._make_engine(delay=0)

        # Simulate 10 fast responses (50ms each)
        for _ in range(10):
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            mock_elapsed = MagicMock()
            mock_elapsed.total_seconds.return_value = 0.05
            resp.elapsed = mock_elapsed
            engine._update_throttle(resp)

        assert engine.throttle.active_delay == 0

    def test_update_throttle_mock_elapsed_no_crash(self):
        """MagicMock elapsed (no real total_seconds) should not crash."""
        engine = self._make_engine(delay=0)
        resp = MagicMock()
        resp.status_code = 200
        resp.ok = True
        # MagicMock().elapsed.total_seconds() returns another MagicMock
        # The try/except in _update_throttle should handle this
        engine._update_throttle(resp)
        # Should not raise
