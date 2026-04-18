"""Site analysis utilities.

Content-agnostic heuristics for adapting crawl and chunk behaviour to a
site's structure. No per-domain logic: everything is driven by URL-pattern
evidence or (optionally) sampled page content. If you find yourself
tempted to match a specific hostname here, add a general heuristic
instead.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional, Set
from urllib.parse import urlparse

# Matches path segments that look like language or locale codes:
#   "de", "es", "en-us", "zh-hant", "pt_BR"
# Two ASCII letters, optionally followed by a hyphen/underscore and 2-4
# letters for the region/script subtag.
_LOCALE_SEGMENT_RE = re.compile(r"^[a-z]{2}(?:[-_][a-zA-Z]{2,4})?$")

# ISO 639-1 codes that commonly appear as URL i18n prefixes. Limited to
# language codes only; full locale tags are handled via the extended form
# above. This list disambiguates locale segments from unrelated two-letter
# path segments (e.g. "id" used for resource IDs).
_KNOWN_LANG_CODES: frozenset[str] = frozenset(
    "ar bg bn ca cs da de el en es et fa fi fr he hi hr hu id it ja ko lt "
    "lv ms nb nl no pl pt ro ru sk sl sr sv th tr uk vi zh".split()
)

# Locales treated as primary English unless the caller overrides.
DEFAULT_PRIMARY_LOCALES: Set[str] = {
    "en", "en-us", "en-gb", "en-ca", "en-au", "en_us", "en_gb",
}


def _path_segments(url: str) -> list[str]:
    return [s for s in urlparse(url).path.split("/") if s]


def _lang_base(locale: str) -> str:
    return locale.lower().split("-")[0].split("_")[0]


def locale_segment(url: str) -> Optional[str]:
    """Return the locale prefix of *url* if its path starts with one.

    A path segment counts as a locale only when:

      * it is among the first two segments (locales are conventionally at
        the path root; we allow one extra for sites that prefix a constant
        like `/docs/de/`),
      * it matches the locale-segment shape,
      * its base two-letter code is a known ISO 639-1 language, and
      * it is followed by at least one more non-numeric segment, so that
        resource-id style paths (`/id/1234`) don't masquerade as locales.

    The returned string is lowercased. `None` means no locale was detected.
    """
    segs = _path_segments(url)
    if not segs:
        return None
    for i, seg in enumerate(segs[:2]):
        low = seg.lower()
        if not _LOCALE_SEGMENT_RE.match(low):
            continue
        if _lang_base(low) not in _KNOWN_LANG_CODES:
            continue
        # If there's a following segment, require it to be non-numeric so
        # that resource-id style paths (`/id/1234`) don't masquerade as
        # locales. A locale prefix with nothing after it (e.g. `/es/`) is
        # still a legitimate locale root.
        tail = segs[i + 1:]
        if tail and tail[0].isdigit():
            continue
        return low
    return None


def detect_locale_segments(urls: Iterable[str]) -> Counter:
    """Count occurrences of each locale segment across *urls*."""
    c: Counter = Counter()
    for u in urls:
        loc = locale_segment(u)
        if loc is not None:
            c[loc] += 1
    return c


def infer_i18n_variants(
    urls: Iterable[str],
    min_variants: int = 2,
    min_urls_per_variant: int = 3,
) -> Set[str]:
    """Infer which locale segments represent confirmed i18n variants.

    A locale is confirmed only if it appears on at least
    ``min_urls_per_variant`` URLs, AND the corpus contains at least
    ``min_variants`` distinct such locales. This guards against
    false positives on sites where a lone two-letter segment is a
    coincidence (e.g. an e-commerce category).
    """
    counts = detect_locale_segments(urls)
    confirmed = {loc for loc, n in counts.items() if n >= min_urls_per_variant}
    if len(confirmed) < min_variants:
        return set()
    return confirmed


def i18n_path_excluded(
    url: str,
    primary_locales: Set[str] = DEFAULT_PRIMARY_LOCALES,
) -> bool:
    """Should *url* be skipped as a non-primary-language i18n variant?

    Stateless check. Returns True when the URL carries a recognised
    locale segment whose base language is not in ``primary_locales``.
    """
    loc = locale_segment(url)
    if loc is None:
        return False
    if loc in primary_locales:
        return False
    if _lang_base(loc) in {_lang_base(p) for p in primary_locales}:
        return False
    return True


# ---------------------------------------------------------------------------
# Site fingerprint (scaffolding for self-optimizing crawl policy)
# ---------------------------------------------------------------------------


@dataclass
class SiteProfile:
    """Observed structural features of a site, with no domain labels.

    A profile is a summary of evidence gathered from a sample of URLs
    (and optionally their content). Downstream policy turns this into
    concrete crawl/chunk settings via generic rules.
    """

    sample_size: int = 0
    locale_counts: Counter = field(default_factory=Counter)
    confirmed_locales: Set[str] = field(default_factory=set)
    primary_language: str = "en"

    @property
    def has_i18n_variants(self) -> bool:
        non_primary = {
            loc for loc in self.confirmed_locales
            if _lang_base(loc) != _lang_base(self.primary_language)
        }
        return bool(non_primary)

    @property
    def i18n_non_primary(self) -> Set[str]:
        return {
            loc for loc in self.confirmed_locales
            if _lang_base(loc) != _lang_base(self.primary_language)
        }

    def to_dict(self) -> dict:
        return {
            "sample_size": self.sample_size,
            "locale_counts": dict(self.locale_counts),
            "confirmed_locales": sorted(self.confirmed_locales),
            "primary_language": self.primary_language,
            "has_i18n_variants": self.has_i18n_variants,
            "i18n_non_primary": sorted(self.i18n_non_primary),
        }


def profile_from_urls(
    urls: Iterable[str],
    primary_language: str = "en",
) -> SiteProfile:
    """Build a SiteProfile from URL evidence alone (no page fetches)."""
    url_list = list(urls)
    counts = detect_locale_segments(url_list)
    confirmed = infer_i18n_variants(url_list)
    return SiteProfile(
        sample_size=len(url_list),
        locale_counts=counts,
        confirmed_locales=confirmed,
        primary_language=primary_language,
    )
