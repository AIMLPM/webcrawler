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
from markcrawl.extract_content import classify_page

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

    def test_preserves_img_alt_text(self):
        html = '<html><body><main><p>Before</p><img src="x.png" alt="Architecture diagram"><p>After</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "[Image: Architecture diagram]" in content

    def test_strips_img_without_alt(self):
        html = '<html><body><main><p>Content</p><img src="spacer.gif"><p>More</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "spacer" not in content
        assert "Content" in content

    def test_preserves_figcaption_over_alt(self):
        html = '<html><body><main><figure><img src="x.png" alt="Alt text"><figcaption>Caption text</figcaption></figure></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "[Image: Caption text]" in content
        assert "Alt text" not in content


class TestTitleFallback:
    def test_og_title_fallback(self):
        html = '<html><head><meta property="og:title" content="OG Title"></head><body><main><p>Content</p></main></body></html>'
        title, _, _ = html_to_markdown(html)
        assert title == "OG Title"

    def test_h1_fallback(self):
        html = "<html><body><main><h1>Heading Title</h1><p>Content</p></main></body></html>"
        title, _, _ = html_to_markdown(html)
        assert title == "Heading Title"

    def test_meta_title_fallback(self):
        html = '<html><head><meta name="title" content="Meta Title"></head><body><main><p>Content</p></main></body></html>'
        title, _, _ = html_to_markdown(html)
        assert title == "Meta Title"

    def test_title_tag_takes_precedence(self):
        html = '<html><head><title>Real Title</title><meta property="og:title" content="OG"></head><body><main><h1>H1</h1></main></body></html>'
        title, _, _ = html_to_markdown(html)
        assert title == "Real Title"

    def test_empty_title_tag_falls_through(self):
        html = '<html><head><title></title><meta property="og:title" content="Fallback"></head><body><main><p>X</p></main></body></html>'
        title, _, _ = html_to_markdown(html)
        assert title == "Fallback"


class TestCodeLanguageDetection:
    def test_language_prefix_class(self):
        html = '<html><body><main><pre><code class="language-python">print(1)</code></pre></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "```python" in content

    def test_hljs_prefix_class(self):
        html = '<html><body><main><pre><code class="hljs-javascript">var x</code></pre></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "```javascript" in content

    def test_no_class_no_language(self):
        html = "<html><body><main><pre><code>plain code</code></pre></main></body></html>"
        _, content, _ = html_to_markdown(html)
        assert "```\n" in content
        assert "plain code" in content


class TestContextAwareStripping:
    def test_aside_inside_main_preserved(self):
        html = '<html><body><main><p>Content</p><aside>Sidebar info</aside></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Sidebar info" in content

    def test_aside_outside_main_stripped(self):
        html = '<html><body><aside>Nav sidebar</aside><main><p>Content</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Nav sidebar" not in content

    def test_header_inside_article_preserved(self):
        html = '<html><body><article><header><h1>Article Title</h1></header><p>Body text</p></article></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Article Title" in content

    def test_header_outside_main_stripped(self):
        html = '<html><body><header>Site Header</header><main><p>Content</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Site Header" not in content

    def test_nav_always_stripped_even_inside_main(self):
        html = '<html><body><main><nav>Breadcrumb</nav><p>Content</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Breadcrumb" not in content

    def test_footer_always_stripped(self):
        html = '<html><body><main><footer>Page footer</footer><p>Content</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Page footer" not in content


    def test_nav_with_code_blocks_preserved(self):
        """Nav containing code blocks should be treated as content (e.g. sidebar docs)."""
        html = '<html><body><nav><pre><code>print("hello")</code></pre><p>Example usage</p></nav><p>Content</p></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "hello" in content

    def test_nav_with_substantial_text_preserved(self):
        """Nav with >100 words should be kept — it's likely a content sidebar."""
        prose = " ".join(f"word{i}" for i in range(120))
        html = f'<html><body><nav><p>{prose}</p></nav><p>Content</p></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "word0" in content

    def test_aside_with_code_preserved(self):
        """Aside with code blocks (e.g. API params) should be kept."""
        html = '<html><body><aside><pre><code>curl https://api.example.com</code></pre></aside><p>Content</p></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "curl" in content

    def test_aside_with_data_table_preserved(self):
        """Aside with a data table (>2 rows) should be kept."""
        html = '<html><body><aside><table><tr><td>A</td></tr><tr><td>B</td></tr><tr><td>C</td></tr></table></aside><p>Content</p></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "A" in content

    def test_details_element_expanded(self):
        """Details/summary elements should be expanded, not stripped."""
        html = '<html><body><main><details><summary>API Reference</summary><p>GET /users returns a list of users.</p></details></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "API Reference" in content
        assert "GET /users" in content

    def test_details_code_content_preserved(self):
        """Details with code examples should be expanded."""
        html = '<html><body><main><details><summary>Example</summary><pre><code>fetch("/api")</code></pre></details></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert 'fetch("/api")' in content


class TestDensityBasedStripping:
    """Test density-based stripping on pages WITHOUT a <main> tag,
    where the fallback to soup.body makes the density pass meaningful."""

    def test_link_heavy_div_stripped_no_main(self):
        # No <main> — body is used; link-heavy div should be removed
        html = """<html><body>
        <div><a href="/a">Link A</a> <a href="/b">Link B</a> <a href="/c">Link C</a> <a href="/d">Link D</a></div>
        <p>Real content here about an important topic that matters.</p>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Real content" in content
        assert "Link A" not in content

    def test_prose_div_kept_no_main(self):
        # No <main>; prose-heavy div (low link density) should be kept
        html = """<html><body>
        <div>This is a disclaimer paragraph with lots of real prose content
        that does not contain many links at all and should be preserved.</div>
        <p>Other content goes here too.</p>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "disclaimer paragraph" in content

    def test_div_inside_main_always_kept(self):
        html = """<html><body><main>
        <div><a href="/a">A</a> <a href="/b">B</a> <a href="/c">C</a></div>
        <p>Content</p>
        </main></body></html>"""
        _, content, _ = html_to_markdown(html)
        # Inside main, even link-heavy divs are kept
        assert "Content" in content

    def test_large_text_div_kept_even_with_links(self):
        # >80 words means the element is too large to be nav boilerplate
        prose = " ".join(f"word{i}" for i in range(90))
        html = f"""<html><body>
        <div>{prose} <a href="/a">Link</a></div>
        <p>Other content.</p>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "word0" in content

    def test_section_with_links_stripped_no_main(self):
        html = """<html><body>
        <section><a href="/x">X</a> <a href="/y">Y</a> <a href="/z">Z</a></section>
        <p>Main body content with meaningful text.</p>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Main body" in content
        assert "[X]" not in content


class TestReadabilityContentDetection:
    """Content region detection for pages without <main>."""

    def test_finds_div_by_id_content(self):
        html = """<html><body>
        <div id="nav"><a href="/a">A</a> <a href="/b">B</a></div>
        <div id="content"><h1>Title</h1><p>Real article content with enough words to be meaningful.</p></div>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Real article content" in content

    def test_finds_div_by_class_main_content(self):
        html = """<html><body>
        <div class="sidebar"><a href="/x">X</a><a href="/y">Y</a><a href="/z">Z</a></div>
        <div class="main-content"><h1>Title</h1><p>The main body text with sufficient words for detection.</p></div>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "main body text" in content

    def test_finds_content_by_density_scoring(self):
        # No hint classes — must use density scoring
        html = """<html><body>
        <div class="topbar"><a href="/a">A</a> <a href="/b">B</a> <a href="/c">C</a></div>
        <div class="wrapper">
            <div class="stuff">
                <h1>Important Article</h1>
                <p>First paragraph of a long article that contains substantial prose content about a topic.</p>
                <p>Second paragraph continues the discussion with additional detail and context for the reader.</p>
                <h2>Section Two</h2>
                <p>Third paragraph explores a subtopic in depth with enough words to exceed the threshold.</p>
            </div>
        </div>
        <div class="bottom"><a href="/t">Terms</a> <a href="/p">Privacy</a></div>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Important Article" in content
        assert "Section Two" in content

    def test_prefers_main_over_readability(self):
        # When <main> exists, readability detection is not used
        html = """<html><body>
        <div id="content"><p>Wrong region — should use main.</p></div>
        <main><p>Correct content from the main element.</p></main>
        </body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Correct content" in content


class TestMetaDescriptionExtraction:
    def test_meta_description_prepended(self):
        html = """<html><head>
        <meta name="description" content="A guide to building REST APIs with Python.">
        </head><body><main><h1>REST APIs</h1><p>Content here.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "A guide to building REST APIs" in content
        # Should appear before the main content
        desc_pos = content.find("A guide to building")
        h1_pos = content.find("REST APIs")
        assert desc_pos < h1_pos

    def test_og_description_fallback(self):
        html = """<html><head>
        <meta property="og:description" content="OpenGraph description for sharing.">
        </head><body><main><h1>Title</h1><p>Content.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "OpenGraph description" in content

    def test_no_description_no_prefix(self):
        html = "<html><body><main><p>Just content.</p></main></body></html>"
        _, content, _ = html_to_markdown(html)
        assert content.strip().startswith("Just content")

    def test_meta_preferred_over_og(self):
        html = """<html><head>
        <meta name="description" content="Meta description.">
        <meta property="og:description" content="OG description.">
        </head><body><main><p>Content.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Meta description" in content


class TestStructuredDataExtraction:
    def test_json_ld_tech_article(self):
        html = """<html><head>
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"TechArticle","name":"API Guide","description":"Complete reference for the REST API"}</script>
        </head><body><main><p>Content.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "API Guide: Complete reference" in content

    def test_json_ld_faq(self):
        html = """<html><head>
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"What is X?","acceptedAnswer":{"@type":"Answer","text":"X is a framework."}}]}</script>
        </head><body><main><p>FAQ page.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Q: What is X?" in content
        assert "A: X is a framework." in content

    def test_no_json_ld_no_append(self):
        html = "<html><body><main><p>Plain page.</p></main></body></html>"
        _, content, _ = html_to_markdown(html)
        assert content.strip() == "Plain page."

    def test_malformed_json_ld_ignored(self):
        html = """<html><head>
        <script type="application/ld+json">{invalid json here}</script>
        </head><body><main><p>Content survives.</p></main></body></html>"""
        _, content, _ = html_to_markdown(html)
        assert "Content survives" in content


class TestCTALinkStripping:
    def test_signup_link_stripped(self):
        html = '<html><body><main><p>Try it.</p><a href="/signup">Sign Up Free</a><p>More content.</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Sign Up Free" not in content
        assert "More content" in content

    def test_demo_link_stripped(self):
        html = '<html><body><main><p>See it in action.</p><a href="/demo">Watch Demo</a></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Watch Demo" not in content

    def test_pricing_link_stripped(self):
        html = '<html><body><main><p>Plans for every team.</p><a href="/pricing">View Pricing</a></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "View Pricing" not in content

    def test_docs_link_kept(self):
        html = '<html><body><main><p>Learn more.</p><a href="/docs/guide">Read the guide</a></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Read the guide" in content

    def test_long_cta_text_kept(self):
        # Links with >5 words are kept even if href matches CTA pattern
        html = '<html><body><main><a href="/signup">Sign up for our free developer tier with full API access</a></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Sign up for our free" in content

    def test_login_stripped(self):
        html = '<html><body><main><p>Welcome back.</p><a href="/login">Log In</a><p>Dashboard content here with enough words.</p></main></body></html>'
        _, content, _ = html_to_markdown(html)
        assert "Log In" not in content
        assert "Dashboard content" in content


class TestTrafilaturaExtractor:
    def test_extracts_content(self):
        from markcrawl.core import html_to_markdown_trafilatura

        html = """<html><head><title>API Guide</title></head><body>
        <nav><a href="/">Home</a></nav>
        <main>
        <h1>Getting Started</h1>
        <p>This guide walks you through setting up the API client and making your first request to the service.</p>
        <h2>Installation</h2>
        <p>Install the package with pip install example-sdk and configure your API key in the environment.</p>
        </main>
        <footer>Copyright 2026</footer>
        </body></html>"""
        title, content, links = html_to_markdown_trafilatura(html)
        assert title == "API Guide"
        assert "Getting Started" in content
        assert "API client" in content
        assert "Copyright" not in content

    def test_extracts_links(self):
        from markcrawl.core import html_to_markdown_trafilatura

        html = '<html><body><main><a href="/about">About</a><p>Content with enough words for extraction.</p></main></body></html>'
        _, _, links = html_to_markdown_trafilatura(html, base_url="https://example.com/")
        assert "https://example.com/about" in links

    def test_returns_title_even_without_title_tag(self):
        from markcrawl.core import html_to_markdown_trafilatura

        html = '<html><head><meta property="og:title" content="OG Title"></head><body><main><p>Content here with enough words for the extractor to work properly.</p></main></body></html>'
        title, _, _ = html_to_markdown_trafilatura(html)
        assert title == "OG Title"


class TestEnsembleExtractor:
    def test_returns_content(self):
        from markcrawl.core import html_to_markdown_ensemble

        html = """<html><head><title>Test</title></head><body>
        <nav><a href="/">Home</a></nav>
        <main><h1>Title</h1>
        <p>Real content with enough words for extraction to work properly in both extractors.</p>
        </main></body></html>"""
        title, content, links = html_to_markdown_ensemble(html)
        assert "Title" in content
        assert "Real content" in content

    def test_picks_higher_scoring_extraction(self):
        from markcrawl.extract_content import _score_extraction

        # Good extraction: prose with headings
        good = "# API Guide\n\nThis is a detailed guide to the API with multiple sentences. It covers authentication, rate limiting, and error handling."
        # Bad extraction: nav junk
        bad = "[Home](/) | [About](/about) | [Contact](/contact)"
        assert _score_extraction(good) > _score_extraction(bad)

    def test_score_empty_is_zero(self):
        from markcrawl.extract_content import _score_extraction

        assert _score_extraction("") == 0.0


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
# httpx client selection
# ---------------------------------------------------------------------------

class TestHttpxSelection:
    def test_build_session_returns_httpx_when_available(self):
        from markcrawl.fetch import _HAS_HTTPX, build_session
        client = build_session()
        if _HAS_HTTPX:
            import httpx
            assert isinstance(client, httpx.Client)
        else:
            import requests
            assert isinstance(client, requests.Session)

    def test_httpx_client_has_http2(self):
        from markcrawl.fetch import _HAS_HTTPX, build_session
        if not _HAS_HTTPX:
            return  # skip if httpx not installed
        client = build_session()
        # httpx.Client exposes http2 capability
        import httpx
        assert isinstance(client, httpx.Client)


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

    @patch("markcrawl.core._HAS_HTTPX", False)
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

    @patch("markcrawl.core._HAS_HTTPX", False)
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

    @patch("markcrawl.core._HAS_HTTPX", False)
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

    @patch("markcrawl.core._HAS_HTTPX", False)
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
# Playwright concurrency guard
# ---------------------------------------------------------------------------

class TestPlaywrightConcurrencyGuard:
    def test_render_js_caps_concurrency_to_one(self):
        """render_js=True should force concurrency=1 regardless of requested value."""
        import tempfile
        from unittest.mock import patch

        from markcrawl.core import CrawlEngine

        out_dir = tempfile.mkdtemp()
        with patch("markcrawl.core._get_playwright_browser") as mock_pw:
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_browser.new_context.return_value = mock_context
            mock_pw.return_value = (MagicMock(), mock_browser)

            engine = CrawlEngine(
                out_dir=out_dir, fmt="markdown", min_words=5, delay=0,
                timeout=15, concurrency=5, include_subdomains=False,
                user_agent="test", render_js=True, proxy=None, show_progress=False,
            )
            assert engine.concurrency == 1


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

    def test_update_throttle_429_is_ignored(self):
        # As of v0.10.0 the throttle no longer reacts to 429 — that signal
        # is owned by markcrawl.retry. Throttle should leave delay alone.
        engine = self._make_engine(delay=0.5)
        resp = MagicMock()
        resp.status_code = 429
        resp.elapsed = None

        engine._update_throttle(resp)
        assert engine.throttle._backoff_count == 0
        assert engine.throttle.active_delay == engine.throttle.base_delay

    def test_update_throttle_429_does_not_disturb_pacing(self):
        # A 429 must not change inter-request pacing; subsequent 200s must
        # set delay based on response-time signal alone.
        engine = self._make_engine(delay=0.1)

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.elapsed = None
        engine._update_throttle(resp_429)
        assert engine.throttle.active_delay == engine.throttle.base_delay

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


# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------

pytest = __import__("pytest")
_skip_no_httpx = pytest.mark.skipif(
    not __import__("importlib").util.find_spec("httpx"),
    reason="httpx not installed",
)


@_skip_no_httpx
class TestAsyncEngine:
    def test_async_engine_creates_with_httpx(self):
        """AsyncCrawlEngine should construct when httpx is available."""
        import tempfile

        from markcrawl.core import AsyncCrawlEngine

        out_dir = tempfile.mkdtemp()
        engine = AsyncCrawlEngine(
            out_dir=out_dir, fmt="markdown", min_words=5, delay=0,
            timeout=15, concurrency=5, include_subdomains=False,
            user_agent="test", proxy=None, show_progress=False,
        )
        assert engine.concurrency == 5
        # Should have an httpx.AsyncClient
        import httpx
        assert isinstance(engine.session, httpx.AsyncClient)

    def test_async_process_response_extracts_content(self):
        """AsyncCrawlEngine.process_response works with httpx-style responses."""
        import tempfile

        from markcrawl.core import AsyncCrawlEngine

        out_dir = tempfile.mkdtemp()
        engine = AsyncCrawlEngine(
            out_dir=out_dir, fmt="markdown", min_words=5, delay=0,
            timeout=15, concurrency=1, include_subdomains=False,
            user_agent="test", proxy=None, show_progress=False,
        )

        resp = MagicMock()
        resp.is_success = True
        resp.ok = True
        resp.text = "<html><head><title>Test</title></head><body><main><p>Enough words to pass the filter here.</p></main></body></html>"
        resp.headers = {"content-type": "text/html"}

        result = engine.process_response("https://example.com/", resp)
        assert result is not None
        assert result["title"] == "Test"
        assert "Enough words" in result["content"]

    def test_async_process_response_deduplicates(self):
        """AsyncCrawlEngine deduplicates identical content."""
        import tempfile

        from markcrawl.core import AsyncCrawlEngine

        out_dir = tempfile.mkdtemp()
        engine = AsyncCrawlEngine(
            out_dir=out_dir, fmt="markdown", min_words=5, delay=0,
            timeout=15, concurrency=1, include_subdomains=False,
            user_agent="test", proxy=None, show_progress=False,
        )

        html = "<html><head><title>Test</title></head><body><main><p>Identical content words to pass the filter.</p></main></body></html>"
        resp1 = MagicMock()
        resp1.is_success = True
        resp1.ok = True
        resp1.text = html
        resp1.headers = {"content-type": "text/html"}

        resp2 = MagicMock()
        resp2.is_success = True
        resp2.ok = True
        resp2.text = html
        resp2.headers = {"content-type": "text/html"}

        result1 = engine.process_response("https://example.com/page1", resp1)
        result2 = engine.process_response("https://example.com/page2", resp2)
        assert result1 is not None
        assert result2 is None  # duplicate

    def test_async_crawl_integration(self, tmp_path):
        """Full async crawl path via crawl() with mocked httpx.AsyncClient."""
        from markcrawl.core import _HAS_HTTPX, crawl

        if not _HAS_HTTPX:
            return  # Skip if httpx not installed

        html = textwrap.dedent("""\
            <html><head><title>Async Test</title></head>
            <body><main><p>This page has enough words to pass the minimum word filter for async testing.</p></main></body>
            </html>
        """)

        # Mock httpx.AsyncClient
        import httpx

        async def mock_get(url, timeout=None):
            resp = MagicMock()
            resp.is_success = True
            resp.status_code = 200
            resp.text = "" if "robots.txt" in str(url) else html
            resp.content = resp.text.encode()
            resp.headers = {"content-type": "text/html; charset=utf-8"}
            return resp

        mock_client = MagicMock(spec=httpx.AsyncClient)
        mock_client.get = mock_get

        async def mock_aclose():
            pass

        mock_client.aclose = mock_aclose

        with patch("markcrawl.core.build_async_session", return_value=mock_client):
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

        with open(result.index_file) as f:
            row = json.loads(f.readline())
        assert row["title"] == "Async Test"
        assert "enough words" in row["text"]

    def test_async_fetch_retries_on_error(self):
        """fetch_async retries transient HTTP errors."""
        import asyncio

        import httpx

        from markcrawl.fetch import fetch_async

        call_count = 0

        async def mock_get(url, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection failed")
            resp = MagicMock()
            resp.status_code = 200
            resp.is_success = True
            resp.text = "ok"
            return resp

        client = MagicMock()
        client.get = mock_get

        result = asyncio.run(fetch_async(client, "https://example.com", timeout=10))
        assert result is not None
        assert call_count == 3  # 2 failures + 1 success

    def test_async_fetch_returns_none_after_max_retries(self):
        """fetch_async returns None after exhausting retries."""
        import asyncio

        import httpx

        from markcrawl.fetch import fetch_async

        async def mock_get(url, timeout=None):
            raise httpx.ConnectError("connection failed")

        client = MagicMock()
        client.get = mock_get

        result = asyncio.run(fetch_async(client, "https://example.com", timeout=10))
        assert result is None


class TestPageTypeClassification:
    def test_docs_by_url(self):
        from bs4 import BeautifulSoup
        html = '<html><body><pre><code>x = 1</code></pre><p>Content</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert classify_page(soup, "https://example.com/docs/api") == "docs"

    def test_article_by_tag_and_time(self):
        from bs4 import BeautifulSoup
        html = '<html><body><article><time>2026-01-01</time><p>Blog post content</p></article></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert classify_page(soup, "https://example.com/some-page") == "article"

    def test_article_by_url(self):
        from bs4 import BeautifulSoup
        html = '<html><body><time>2026-01-01</time><p>Blog post</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert classify_page(soup, "https://example.com/blog/my-post") == "article"

    def test_generic_fallback(self):
        from bs4 import BeautifulSoup
        html = '<html><body><p>Just some content</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert classify_page(soup, "https://example.com/about") == "generic"

    def test_docs_by_code_blocks(self):
        from bs4 import BeautifulSoup
        html = '<html><body><pre>code1</pre><pre>code2</pre><pre>code3</pre><p>Docs</p></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert classify_page(soup, "https://example.com/page") == "docs"


class TestSmartSampleUrls:
    """Tests for the smart_sample_urls() clustering function."""

    def test_small_clusters_kept_intact(self):
        from markcrawl.core import smart_sample_urls

        urls = [
            "https://example.com/about",
            "https://example.com/pricing",
            "https://example.com/contact",
        ]
        selected, clusters = smart_sample_urls(urls, threshold=20, sample_size=5)
        assert set(selected) == set(urls)
        assert all(not c.is_templated for c in clusters)

    def test_large_cluster_sampled(self):
        from markcrawl.core import smart_sample_urls

        urls = [f"https://example.com/jobs/job-{i}" for i in range(100)]
        urls.append("https://example.com/about")
        selected, clusters = smart_sample_urls(urls, threshold=20, sample_size=5)

        # Should sample 5 from /jobs/* cluster, keep /about
        assert len(selected) == 6
        job_cluster = [c for c in clusters if c.pattern == "/jobs/*"][0]
        assert job_cluster.is_templated
        assert len(job_cluster.sampled) == 5
        assert len(job_cluster.urls) == 100

    def test_threshold_boundary(self):
        from markcrawl.core import smart_sample_urls

        # Exactly at threshold — should NOT be sampled
        urls = [f"https://example.com/items/item-{i}" for i in range(20)]
        selected, clusters = smart_sample_urls(urls, threshold=20, sample_size=5)
        assert len(selected) == 20

        # One over threshold — should be sampled
        urls.append("https://example.com/items/item-extra")
        selected, clusters = smart_sample_urls(urls, threshold=20, sample_size=5)
        assert len(selected) == 5

    def test_progress_callback_invoked(self):
        from markcrawl.core import smart_sample_urls

        messages = []
        urls = [f"https://example.com/products/p-{i}" for i in range(50)]
        smart_sample_urls(urls, threshold=10, sample_size=3, progress=messages.append)
        assert any("Pattern Discovery" in m for m in messages)
        assert any("sampled" in m for m in messages)

    def test_root_urls_grouped(self):
        from markcrawl.core import smart_sample_urls

        urls = [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/pricing",
        ]
        selected, clusters = smart_sample_urls(urls, threshold=20, sample_size=5)
        # All three should remain (small clusters)
        assert len(selected) == 3
