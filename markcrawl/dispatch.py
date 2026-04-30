"""Production cascade for render_js promotion decisions.

The cascade fires from cheap-and-precise to expensive-and-permissive,
short-circuiting on the first match. Each rule has a single
interpretable signal name so dispatch decisions are auditable.

This module is the production import point for `markcrawl.core`. The
benchmark harness in `bench/local_replica/methods.py` re-exports the
same primitives for autoresearch evaluation, so a rule that scores well
in the sweep behaves identically in production.

Cascade order (cheap → expensive):
  R0  user-set render_js          (authority signal, no scan needed)
  R1  is_spa=True                 (current heuristic, high precision)
  R2  class-gated thin seed       (apiref/docs/spa < threshold words)
  R3  HTML/text size ratio        (>50× ratio = JS shell; needs html bytes)

R4 (in-loop trip-wire after N static pages) was specified but
deliberately NOT shipped. The DS-6 autoresearch sweep on the v0.9.9
campaign labeled dataset (47 definite sites, 6 needs_render_js
positives) scored M3-trip-wire at 0% precision / 0% recall / 10.5%
FP-rate — strictly worse than chance. Adding R4 would degrade the
cascade (M6 with M3 vs M6 without). If reintroduced later, gate it
behind fresh sweep evidence; do not infer from intuition alone.

Each rule returns a `DispatchDecision` so the engine can log the rule
and signal that fired. Keep rule names stable — they're emitted in user
logs and parsed by external tooling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


# Class-gated thresholds for R2. Wiki/blog/ecom seeds are commonly thin
# (category index pages) so a thin seed there is NOT a JS-shell signal.
SEED_WORD_THRESHOLDS: dict[str, int] = {
    "apiref":  100,
    "docs":    150,
    "spa":     100,
    "generic":  50,
}


@dataclass
class DispatchDecision:
    """One cascade outcome. ``promote`` may be None for deferred rules
    (e.g. trip-wire that needs page data not yet available)."""
    promote: Optional[bool]
    rule: str
    signal: str

    def log_line(self) -> str:
        verb = "promote" if self.promote else ("hold" if self.promote is False else "defer")
        return f"[info] dispatch: {self.rule} fired ({verb}) because {self.signal}"


def decide_render_js(
    profile: Any,
    user_render_js: Optional[bool] = None,
    html_bytes: int = 0,
    visible_text_bytes: int = 0,
) -> DispatchDecision:
    """Run the pre-crawl portion of the cascade (R0..R3).

    The trip-wire rule (R4) needs first-N pages and is invoked separately
    from the crawl loop via :func:`should_promote_after_pages`.

    *profile* should have attributes ``url_class``, ``is_spa``,
    ``seed_word_count`` (a SiteProfile or duck-type-compatible).
    """
    # R0: user authority overrides everything
    if user_render_js is True:
        return DispatchDecision(True, "R0/user", f"user_render_js=True")
    if user_render_js is False:
        return DispatchDecision(False, "R0/user", f"user_render_js=False")

    # R1: is_spa
    is_spa = getattr(profile, "is_spa", None)
    if is_spa is True:
        return DispatchDecision(True, "R1/is_spa", "is_spa=True")

    # R2: class-gated thin seed
    cls = getattr(profile, "url_class", "generic")
    swc = getattr(profile, "seed_word_count", -1)
    threshold = SEED_WORD_THRESHOLDS.get(cls)
    if threshold is not None and swc >= 0 and swc < threshold:
        return DispatchDecision(
            True, "R2/seed_word_count",
            f"class={cls} seed_word_count={swc}<{threshold}",
        )

    # R3: HTML/text size ratio (when scan captured these)
    if html_bytes > 0 and visible_text_bytes > 0:
        ratio = html_bytes / max(visible_text_bytes, 1)
        if ratio > 50:
            return DispatchDecision(
                True, "R3/html_text_ratio",
                f"html/text ratio={ratio:.1f}>50",
            )

    # R4 trip-wire is the runtime fallback; until first pages crawled,
    # default to NOT promoting.
    return DispatchDecision(
        False, "R4/default",
        f"no pre-crawl rule fired (class={cls}, is_spa={is_spa})",
    )


def should_promote_after_pages(
    pages: List[dict],
    n_required_thin: int = 4,
    n_total: int = 5,
    word_threshold: int = 50,
) -> DispatchDecision:
    """R4: post-N-pages trip-wire.

    Call after the first N pages have been saved. If at least
    ``n_required_thin`` of them have fewer than ``word_threshold`` visible
    words, the seed lied about being JS-rendered (the static crawler
    isn't extracting content). Promote and re-crawl.

    Pages should be the JSONL-style dicts with a ``text`` field.
    """
    if len(pages) < n_total:
        return DispatchDecision(
            None, "R4/insufficient_pages",
            f"only {len(pages)} pages crawled (need {n_total})",
        )
    sample = pages[:n_total]
    thin = sum(1 for p in sample
               if len((p.get("text") or "").split()) < word_threshold)
    if thin >= n_required_thin:
        return DispatchDecision(
            True, "R4/trip_wire",
            f"{thin}/{n_total} pages thin (<{word_threshold} words)",
        )
    return DispatchDecision(
        False, "R4/trip_wire_skipped",
        f"{thin}/{n_total} pages thin (<{word_threshold} words)",
    )


def should_give_up_after_render(
    rendered_pages: List[dict],
    n_check: int = 5,
    word_threshold: int = 20,
) -> DispatchDecision:
    """Terminal check: even after Playwright, are pages empty?

    Catches mui.com-style cases where ``render_js=True`` still extracts
    0-byte markdown. Returns ``promote=False`` (i.e. give up cycling).
    """
    sample = rendered_pages[:n_check]
    if not sample:
        return DispatchDecision(False, "R-terminal/empty",
                                "no pages after render")
    thin = sum(1 for p in sample
               if len((p.get("text") or "").split()) < word_threshold)
    if thin >= n_check:
        return DispatchDecision(
            False, "R-terminal/all_thin",
            f"all {n_check} rendered pages thin -- give up",
        )
    return DispatchDecision(
        True, "R-terminal/keep",
        f"{n_check - thin}/{n_check} rendered pages have content",
    )
