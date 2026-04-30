"""Tests for markcrawl.dispatch — the production cascade for render_js."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from markcrawl.dispatch import (
    DispatchDecision,
    SEED_WORD_THRESHOLDS,
    decide_render_js,
    should_promote_after_pages,
    should_give_up_after_render,
)


@dataclass
class FakeProfile:
    """Duck-type compatible with markcrawl.scan.SiteProfile for tests."""
    url_class: str = "generic"
    is_spa: object = None        # tri-state
    seed_word_count: int = -1


# ---- R0: user authority -----------------------------------------------

def test_r0_user_render_js_true_overrides_all_signals():
    p = FakeProfile(url_class="apiref", is_spa=True, seed_word_count=0)
    d = decide_render_js(p, user_render_js=True)
    assert d.promote is True
    assert d.rule == "R0/user"


def test_r0_user_render_js_false_overrides_all_signals():
    p = FakeProfile(url_class="apiref", is_spa=True, seed_word_count=0)
    d = decide_render_js(p, user_render_js=False)
    assert d.promote is False
    assert d.rule == "R0/user"


# ---- R1: is_spa --------------------------------------------------------

def test_r1_promotes_when_is_spa_true():
    p = FakeProfile(is_spa=True)
    d = decide_render_js(p)
    assert d.promote is True
    assert d.rule == "R1/is_spa"


def test_r1_skips_when_is_spa_false():
    p = FakeProfile(is_spa=False, url_class="wiki", seed_word_count=500)
    d = decide_render_js(p)
    assert d.promote is False


# ---- R2: class-gated thin seed ----------------------------------------

def test_r2_promotes_apiref_thin_seed():
    p = FakeProfile(url_class="apiref", seed_word_count=50, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is True
    assert d.rule == "R2/seed_word_count"


def test_r2_promotes_docs_thin_seed():
    p = FakeProfile(url_class="docs", seed_word_count=100, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is True


def test_r2_skips_apiref_rich_seed():
    p = FakeProfile(url_class="apiref", seed_word_count=500, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is False
    assert d.rule == "R4/default"


def test_r2_skips_wiki_thin_seed():
    """Wiki seeds are commonly thin (category indexes); not a JS signal."""
    p = FakeProfile(url_class="wiki", seed_word_count=20, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is False


def test_r2_skips_blog_thin_seed():
    p = FakeProfile(url_class="blog", seed_word_count=30, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is False


def test_r2_handles_unknown_seed_word_count():
    p = FakeProfile(url_class="apiref", seed_word_count=-1, is_spa=False)
    d = decide_render_js(p)
    assert d.promote is False  # falls through


# ---- R3: HTML/text ratio -----------------------------------------------

def test_r3_promotes_high_ratio():
    p = FakeProfile(url_class="wiki", seed_word_count=500, is_spa=False)
    d = decide_render_js(p, html_bytes=100_000, visible_text_bytes=500)
    assert d.promote is True
    assert d.rule == "R3/html_text_ratio"


def test_r3_skips_low_ratio():
    p = FakeProfile(url_class="wiki", seed_word_count=500, is_spa=False)
    d = decide_render_js(p, html_bytes=10_000, visible_text_bytes=2_000)
    assert d.promote is False


def test_r3_skipped_when_bytes_zero():
    """No html/text byte counts available => fall through to R4 default."""
    p = FakeProfile(url_class="wiki", seed_word_count=500, is_spa=False)
    d = decide_render_js(p, html_bytes=0, visible_text_bytes=0)
    assert d.rule == "R4/default"


# ---- R4: trip-wire after first pages ----------------------------------

def test_r4_returns_none_when_too_few_pages():
    d = should_promote_after_pages([{"text": "x"}, {"text": "y"}])
    assert d.promote is None


def test_r4_promotes_when_4_of_5_thin():
    pages = [{"text": ""}] * 4 + [{"text": " ".join(["w"] * 100)}]
    d = should_promote_after_pages(pages)
    assert d.promote is True
    assert d.rule == "R4/trip_wire"


def test_r4_keeps_when_only_2_of_5_thin():
    pages = [{"text": ""}] * 2 + [{"text": " ".join(["w"] * 100)}] * 3
    d = should_promote_after_pages(pages)
    assert d.promote is False


# ---- Terminal: post-Playwright check ----------------------------------

def test_terminal_keeps_when_rendered_pages_have_content():
    pages = [{"text": " ".join(["w"] * 100)}] * 5
    d = should_give_up_after_render(pages)
    assert d.promote is True


def test_terminal_gives_up_when_all_rendered_pages_thin():
    pages = [{"text": ""}] * 5
    d = should_give_up_after_render(pages)
    assert d.promote is False
    assert d.rule == "R-terminal/all_thin"


def test_terminal_gives_up_on_empty_list():
    d = should_give_up_after_render([])
    assert d.promote is False


# ---- Cascade ordering / short-circuit ----------------------------------

def test_cascade_short_circuits_on_first_match():
    """If R1 fires, R2/R3 should not be evaluated -- attribution stays at R1."""
    p = FakeProfile(url_class="apiref", is_spa=True, seed_word_count=50)
    d = decide_render_js(p)
    assert d.rule == "R1/is_spa"  # not R2 even though R2 would also fire


def test_cascade_falls_through_to_r2():
    p = FakeProfile(url_class="apiref", is_spa=False, seed_word_count=50)
    d = decide_render_js(p)
    assert d.rule == "R2/seed_word_count"


def test_cascade_falls_through_to_r3():
    p = FakeProfile(url_class="wiki", is_spa=False, seed_word_count=500)
    d = decide_render_js(p, html_bytes=200_000, visible_text_bytes=1000)
    assert d.rule == "R3/html_text_ratio"


def test_cascade_default_when_nothing_fires():
    p = FakeProfile(url_class="wiki", is_spa=False, seed_word_count=500)
    d = decide_render_js(p)
    assert d.rule == "R4/default"
    assert d.promote is False


# ---- Log line format (used in user-facing output) ---------------------

def test_log_line_contains_rule_and_signal():
    p = FakeProfile(is_spa=True)
    d = decide_render_js(p)
    log = d.log_line()
    assert "R1/is_spa" in log
    assert "is_spa=True" in log
    assert "promote" in log
    assert "fired" in log
    assert "because" in log


def test_log_line_describes_hold_when_no_promote():
    p = FakeProfile(url_class="wiki", is_spa=False, seed_word_count=500)
    d = decide_render_js(p)
    log = d.log_line()
    assert "hold" in log
    assert "fired" in log


def test_log_line_matches_sc5_format():
    """SC-5 spec: '[info] dispatch: <rule> fired because <signal>=<value>'."""
    p = FakeProfile(is_spa=True)
    d = decide_render_js(p)
    log = d.log_line()
    assert log.startswith("[info] dispatch: ")
    assert " fired " in log
    assert " because " in log


# ---- Threshold sanity checks ------------------------------------------

def test_thresholds_only_cover_jsy_classes():
    """Wiki/blog/ecom MUST NOT be in the gate set -- their thin seeds are normal."""
    assert "wiki" not in SEED_WORD_THRESHOLDS
    assert "blog" not in SEED_WORD_THRESHOLDS
    assert "ecom" not in SEED_WORD_THRESHOLDS


def test_thresholds_cover_jsy_classes():
    for cls in ("apiref", "docs", "spa"):
        assert cls in SEED_WORD_THRESHOLDS
