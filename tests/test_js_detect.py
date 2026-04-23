"""Tests for markcrawl.js_detect — SPA detection heuristic."""

from __future__ import annotations

from markcrawl.js_detect import _visible_text, is_spa_site


class TestVisibleText:
    def test_strips_scripts(self):
        html = "<html><body>hello <script>var x = 1;</script>world</body></html>"
        assert "var x" not in _visible_text(html)
        assert "hello" in _visible_text(html)
        assert "world" in _visible_text(html)

    def test_strips_styles(self):
        html = "<html><head><style>.foo { color: red; }</style></head><body>visible</body></html>"
        text = _visible_text(html)
        assert "color" not in text
        assert "visible" in text

    def test_handles_empty(self):
        assert _visible_text("") == ""


class TestIsSpaSite:
    def test_nextjs_shell(self):
        # Typical Next.js initial HTML: __next marker + mostly scripts
        html = (
            "<!doctype html><html><head>"
            "<script src='/next.js'></script>"
            "<script src='/bundle.js'></script>"
            "</head><body>"
            '<div id="__next"></div>'
            "<script src='/runtime.js'></script>"
            "</body></html>"
        )
        assert is_spa_site(html) is True

    def test_ssr_with_nextjs_marker_has_content(self):
        # SSR Next.js page WITH substantial rendered content — should NOT flag
        body_text = " ".join(["word"] * 500)  # ~2500 chars visible
        html = (
            "<!doctype html><html><body>"
            f'<div id="__next">{body_text}</div>'
            "</body></html>"
        )
        assert is_spa_site(html) is False

    def test_react_empty_root(self):
        # CRA-style empty root + mostly scripts
        html = (
            "<!doctype html><html><head>"
            + "<script src='/a.js'></script>" * 20
            + "</head><body>"
            + '<div id="root"></div>'
            + "<script src='/b.js'></script>" * 20
            + "</body></html>"
        )
        assert is_spa_site(html) is True

    def test_plain_static_site(self):
        # Static blog-style page — plenty of content, no framework markers
        body = " ".join(["<p>This is a real sentence.</p>"] * 30)
        html = f"<html><body><article>{body}</article></body></html>"
        assert is_spa_site(html) is False

    def test_reactroot_marker(self):
        html = (
            "<html><body>"
            + '<div data-reactroot></div>'
            + "<script src='/a.js'></script>" * 15
            + "</body></html>"
        )
        assert is_spa_site(html) is True

    def test_angular_marker(self):
        html = (
            "<html><body>"
            + '<my-app ng-version="17.0"></my-app>'
            + "<script src='/a.js'></script>" * 15
            + "</body></html>"
        )
        assert is_spa_site(html) is True

    def test_weak_marker_with_content_not_flagged(self):
        # id="app" is a weak marker; with content it shouldn't flag
        body = " ".join(["real content"] * 100)
        html = f'<html><body><div id="app">{body}</div></body></html>'
        assert is_spa_site(html) is False

    def test_weak_marker_with_empty_shell_flagged(self):
        # id="app" + mostly scripts → flag
        html = (
            "<!doctype html><html><body>"
            + '<div id="app"></div>'
            + "<script src='/a.js'></script>" * 40
            + "</body></html>"
        )
        assert is_spa_site(html) is True

    def test_empty_html(self):
        assert is_spa_site("") is False

    def test_threshold_override_permits_detection(self):
        html = (
            "<html><body>"
            + '<div id="__next">short bit of rendered text</div>'
            + "<script>a</script>" * 20
            + "</body></html>"
        )
        # Default thresholds: would not flag because visible text is <400 but
        # ratio too high (dep on content). Loosen threshold explicitly.
        assert is_spa_site(html, min_text_chars=1000, max_text_ratio=0.5) is True
