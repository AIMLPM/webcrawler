"""Tests for _auto_path_scope_from_seed — derives include_paths from seed URL.

Heuristic: take the seed URL's path, drop trailing /index* if present,
return [path + '/*'] when there are >= 2 path segments. Returns None
for root or single-segment seeds (preserves whole-site crawl behavior).
"""

from __future__ import annotations

from markcrawl.core import _auto_path_scope_from_seed as derive


class TestAutoPathScope:
    def test_docs_subsection(self):
        # HF transformers: derives /docs/transformers/* (drops /index)
        assert derive("https://huggingface.co/docs/transformers/index") == ["/docs/transformers/*"]

    def test_deep_docs_path(self):
        # MDN: keeps the full /en-US/docs/Web/CSS path
        assert derive("https://developer.mozilla.org/en-US/docs/Web/CSS") == ["/en-US/docs/Web/CSS/*"]

    def test_trailing_slash_stripped(self):
        # k8s: trailing slash doesn't change the result
        assert derive("https://kubernetes.io/docs/concepts/") == ["/docs/concepts/*"]

    def test_ecommerce_deep_seed(self):
        # ikea: deep category seed → exact subtree scope
        assert derive("https://www.ikea.com/us/en/cat/furniture-fu001/") == ["/us/en/cat/furniture-fu001/*"]

    def test_root_url_returns_none(self):
        assert derive("https://example.com/") is None
        assert derive("https://example.com") is None

    def test_single_segment_returns_none(self):
        # /blog → too shallow to scope; let the crawler do whole-site
        assert derive("https://example.com/blog") is None
        assert derive("https://example.com/blog/") is None

    def test_two_segments_minimum(self):
        # Exactly two segments — qualifies for scoping
        assert derive("https://example.com/a/b") == ["/a/b/*"]

    def test_index_html_dropped(self):
        # /docs/foo/index.html → /docs/foo/*
        assert derive("https://example.com/docs/foo/index.html") == ["/docs/foo/*"]
        assert derive("https://example.com/docs/foo/index.htm") == ["/docs/foo/*"]
        assert derive("https://example.com/docs/foo/index.php") == ["/docs/foo/*"]
        assert derive("https://example.com/docs/foo/index") == ["/docs/foo/*"]

    def test_not_index_suffix_preserved(self):
        # /docs/foo/intro (no /index, no extension) → /docs/foo/intro/*
        assert derive("https://example.com/docs/foo/intro") == ["/docs/foo/intro/*"]

    def test_content_filename_drops_to_parent(self):
        # /stable/user_guide.html (a content page, not /index) → /stable/*
        # Sibling pages like /stable/modules/* should be in scope.
        # Falls back to None when this leaves only 1 segment.
        assert derive("https://scikit-learn.org/stable/user_guide.html") is None
        # Deeper path: /a/b/page.html → /a/b/*
        assert derive("https://example.com/a/b/page.html") == ["/a/b/*"]
        # Other content extensions
        assert derive("https://example.com/a/b/page.php") == ["/a/b/*"]
        assert derive("https://example.com/a/b/page.aspx") == ["/a/b/*"]
        assert derive("https://example.com/a/b/page.htm") == ["/a/b/*"]

    def test_query_string_ignored(self):
        # Querystring + fragment must not affect path-derivation
        assert derive("https://example.com/docs/foo/?ref=hn#section") == ["/docs/foo/*"]
