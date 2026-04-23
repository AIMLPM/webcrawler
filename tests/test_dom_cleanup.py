"""Tests for markcrawl.dom_cleanup — overlay stripping."""

from __future__ import annotations

from markcrawl.dom_cleanup import strip_overlays


def _contains(html: str, needle: str) -> bool:
    return needle in html


class TestStripOverlays:
    def test_removes_cookie_banner(self):
        html = """
            <html><body>
              <main><article>Real page content goes here.</article></main>
              <div class="cookie-consent-banner" style="position: fixed">
                <p>We use cookies. Accept?</p>
                <button>Accept</button>
              </div>
            </body></html>
        """
        out = strip_overlays(html)
        assert "We use cookies" not in out
        assert "Real page content" in out

    def test_removes_role_dialog(self):
        html = """
            <html><body>
              <article>Article body</article>
              <div role="dialog" class="modal-signup">
                <h2>Subscribe!</h2>
                <input type="email"/>
              </div>
            </body></html>
        """
        out = strip_overlays(html)
        assert "Subscribe" not in out
        assert "Article body" in out

    def test_removes_newsletter_modal(self):
        html = """
            <html><body>
              <main>Main content</main>
              <aside class="newsletter-popup" style="position:sticky;">
                Sign up for our newsletter!
              </aside>
            </body></html>
        """
        out = strip_overlays(html)
        assert "newsletter" not in out.lower()
        assert "Main content" in out

    def test_leaves_real_content(self):
        # An article that happens to use the word "modal" is not a modal
        html = """
            <html><body>
              <article>
                <h1>Understanding modal verbs</h1>
                <p>Modal verbs like can, will, and must are...</p>
              </article>
            </body></html>
        """
        out = strip_overlays(html)
        assert "modal verbs" in out.lower()

    def test_leaves_ssr_content_unchanged(self):
        # SSR output with no overlays
        html = """
            <html><body>
              <nav>Home About</nav>
              <main>
                <h1>Docs</h1>
                <p>Plenty of real content.</p>
              </main>
              <footer>Copyright</footer>
            </body></html>
        """
        out = strip_overlays(html)
        assert "Plenty of real content" in out
        assert "Home About" in out
        assert "Copyright" in out

    def test_conservative_single_signal_not_enough(self):
        # class="chat-widget" alone (weak signal) but NO second signal
        # → should NOT remove (conservative heuristic needs 2+ signals).
        html = """
            <html><body>
              <main>Hello world</main>
              <div class="chat-widget">
                Just some text about chat widgets in general.
              </div>
            </body></html>
        """
        out = strip_overlays(html)
        # Content element with only pattern match (no position:fixed, no role):
        # strip_overlays SHOULD keep it. Our heuristic requires >=2 signals
        # unless role=dialog/alertdialog.
        assert "Just some text" in out

    def test_alertdialog_role_alone_is_enough(self):
        html = """
            <html><body>
              <article>real</article>
              <div role="alertdialog">Warning!</div>
            </body></html>
        """
        out = strip_overlays(html)
        assert "Warning" not in out
        assert "real" in out

    def test_huge_overlay_candidate_preserved(self):
        # If a "modal" has a ton of content (>4000 chars), it's probably
        # legitimate content using the class name poorly
        big = "real content " * 500  # ~6500 chars
        html = f"""
            <html><body>
              <div class="modal" style="position:fixed">{big}</div>
            </body></html>
        """
        out = strip_overlays(html)
        assert "real content" in out

    def test_handles_empty_string(self):
        assert strip_overlays("") == ""

    def test_handles_non_html(self):
        assert strip_overlays("not actually html") == "not actually html"
