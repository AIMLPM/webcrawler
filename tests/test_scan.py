"""Tests for markcrawl.scan — unified pre-crawl SiteProfile.

Network-touching tests are skipped by default (no requests in unit tests).
The pure-logic helpers (clustering, properties) get full coverage.
"""
from __future__ import annotations

from collections import Counter

from markcrawl.scan import SiteProfile


class TestSiteProfileProperties:
    def test_empty_profile_defaults(self):
        p = SiteProfile(base_url="https://example.com")
        assert p.url_class == "generic"
        assert p.is_spa is None
        assert p.sitemap_url_count == -1
        assert not p.sitemap_clustered
        assert not p.sitemap_huge
        assert not p.seed_outlinks_clustered
        assert not p.empty_seed  # word count -1, not 0

    def test_sitemap_clustered_true_when_dominant(self):
        p = SiteProfile(base_url="https://x.com",
                        sitemap_url_count=100,
                        sitemap_first_seg_distribution=Counter({"docs": 80, "blog": 10, "about": 10}))
        assert p.sitemap_clustered  # 80% > 70% threshold

    def test_sitemap_clustered_false_when_diffuse(self):
        p = SiteProfile(base_url="https://x.com",
                        sitemap_url_count=100,
                        sitemap_first_seg_distribution=Counter({"docs": 40, "blog": 30, "api": 30}))
        assert not p.sitemap_clustered

    def test_sitemap_huge_threshold(self):
        p = SiteProfile(base_url="https://x.com", sitemap_url_count=999)
        assert not p.sitemap_huge
        p2 = SiteProfile(base_url="https://x.com", sitemap_url_count=1001)
        assert p2.sitemap_huge

    def test_seed_outlinks_clustered_true(self):
        p = SiteProfile(base_url="https://x.com",
                        seed_outlink_count=50,
                        seed_outlink_first_seg_distribution=Counter({"book": 35, "appendix": 10, "about": 5}))
        assert p.seed_outlinks_clustered  # 70% > 60% threshold

    def test_seed_outlinks_clustered_false(self):
        p = SiteProfile(base_url="https://x.com",
                        seed_outlink_count=50,
                        seed_outlink_first_seg_distribution=Counter({"a": 20, "b": 15, "c": 15}))
        assert not p.seed_outlinks_clustered  # max 40%

    def test_empty_seed_only_when_explicitly_zero(self):
        # -1 means not probed → empty_seed False
        p = SiteProfile(base_url="https://x.com", seed_word_count=-1)
        assert not p.empty_seed
        # 0 means probed and got nothing → empty_seed True (anti-bot, JS shell, 404)
        p2 = SiteProfile(base_url="https://x.com", seed_word_count=0)
        assert p2.empty_seed
        p3 = SiteProfile(base_url="https://x.com", seed_word_count=42)
        assert not p3.empty_seed


class TestSummary:
    def test_summary_renders(self):
        p = SiteProfile(base_url="https://x.com", url_class="docs",
                        is_spa=True, sitemap_url_count=200,
                        seed_outlink_count=30, fetch_count=4)
        s = p.summary()
        assert "docs" in s
        assert "sitemap=200" in s
        assert "is_spa=True" in s
        assert "fetches=4" in s
