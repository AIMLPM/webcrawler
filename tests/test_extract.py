"""Tests for markcrawl.extract — LLM extraction pipeline with mocked API clients."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from markcrawl.exceptions import MarkcrawlConfigError, MarkcrawlDependencyError
from markcrawl.extract import (
    LLMClient,
    _parse_json_response,
    discover_fields,
    extract_fields,
    extract_from_jsonl,
    load_pages,
    load_pages_multi,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_jsonl(path: str, pages: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for page in pages:
            f.write(json.dumps(page, ensure_ascii=False) + "\n")


SAMPLE_PAGES = [
    {
        "url": "https://example.com/",
        "title": "Example Home",
        "text": "Welcome to Example Inc. We provide cloud infrastructure. Contact us at hello@example.com. Pricing starts at $29/month.",
        "crawled_at": "2026-04-04T12:00:00Z",
        "citation": "Example Home. example.com. Available at: https://example.com/ [Accessed April 04, 2026].",
    },
    {
        "url": "https://example.com/pricing",
        "title": "Pricing",
        "text": "Pricing Plans. Starter $29/month. Pro $99/month. Enterprise contact us for custom pricing. All plans include API access.",
        "crawled_at": "2026-04-04T12:00:00Z",
        "citation": "Pricing. example.com. Available at: https://example.com/pricing [Accessed April 04, 2026].",
    },
]


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    def test_parses_plain_json(self):
        result = _parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parses_json_in_markdown_fence(self):
        result = _parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parses_json_in_plain_fence(self):
        result = _parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_returns_none_for_invalid_json(self):
        result = _parse_json_response("not json at all")
        assert result is None

    def test_strips_whitespace(self):
        result = _parse_json_response('  \n  {"key": "value"}  \n  ')
        assert result == {"key": "value"}


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class TestLLMClient:
    def test_raises_error_for_missing_api_key_or_package(self):
        """Raises ConfigError (missing key) or DependencyError (missing package)."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises((MarkcrawlConfigError, MarkcrawlDependencyError)):
                LLMClient(provider="openai")

    def test_raises_config_error_for_unknown_provider(self):
        with pytest.raises(MarkcrawlConfigError, match="Unknown provider"):
            LLMClient(provider="nonexistent")

    def test_raises_dependency_error_for_missing_package(self):
        # Temporarily hide the openai module
        import sys as _sys
        original = _sys.modules.get("openai")
        _sys.modules["openai"] = None
        try:
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
                with pytest.raises((MarkcrawlDependencyError, ImportError)):
                    LLMClient(provider="openai")
        finally:
            if original is not None:
                _sys.modules["openai"] = original
            else:
                _sys.modules.pop("openai", None)

    def test_default_model(self):
        client = MagicMock(spec=LLMClient)
        client.provider = "openai"
        client.default_model = "gpt-4o-mini"
        assert client.default_model == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# extract_fields
# ---------------------------------------------------------------------------

class TestExtractFields:
    def test_extracts_fields_from_text(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"company_name": "Acme", "pricing": "$29/mo"}'

        result = extract_fields(
            text="Acme Inc offers plans starting at $29/mo",
            fields=["company_name", "pricing"],
            client=mock_client,
            url="https://example.com",
        )

        assert result["company_name"] == "Acme"
        assert result["pricing"] == "$29/mo"
        mock_client.complete.assert_called_once()

    def test_handles_markdown_fenced_response(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '```json\n{"name": "Test"}\n```'

        result = extract_fields(
            text="Test content",
            fields=["name"],
            client=mock_client,
        )
        assert result["name"] == "Test"

    def test_returns_nulls_on_parse_failure(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = "This is not JSON"

        result = extract_fields(
            text="Some text",
            fields=["field1", "field2"],
            client=mock_client,
        )
        assert result == {"field1": None, "field2": None}

    def test_passes_model_to_client(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"f": "v"}'

        extract_fields(
            text="text",
            fields=["f"],
            client=mock_client,
            model="gpt-4o",
        )
        _, kwargs = mock_client.complete.call_args
        assert kwargs.get("model") == "gpt-4o"


# ---------------------------------------------------------------------------
# discover_fields
# ---------------------------------------------------------------------------

class TestDiscoverFields:
    def test_discovers_fields_from_pages(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"fields": ["company_name", "pricing", "features"]}'

        fields = discover_fields(
            pages=SAMPLE_PAGES,
            client=mock_client,
            sample_size=2,
        )
        assert fields == ["company_name", "pricing", "features"]

    def test_spreads_sample_across_sources(self):
        pages = [
            {"url": "https://a.com/", "text": "Site A content", "_source": "a.jsonl"},
            {"url": "https://a.com/about", "text": "About A", "_source": "a.jsonl"},
            {"url": "https://b.com/", "text": "Site B content", "_source": "b.jsonl"},
            {"url": "https://b.com/about", "text": "About B", "_source": "b.jsonl"},
        ]
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"fields": ["name"]}'

        discover_fields(pages=pages, client=mock_client, sample_size=2)

        # Check that the prompt includes pages from both sources
        prompt = mock_client.complete.call_args[0][0]
        assert "a.com" in prompt
        assert "b.com" in prompt

    def test_includes_multi_site_note(self):
        pages = [
            {"url": "https://a.com/", "text": "A", "_source": "a.jsonl"},
            {"url": "https://b.com/", "text": "B", "_source": "b.jsonl"},
        ]
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"fields": ["name"]}'

        discover_fields(pages=pages, client=mock_client, sample_size=2)

        prompt = mock_client.complete.call_args[0][0]
        assert "multiple different websites" in prompt

    def test_includes_context_in_prompt(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = '{"fields": ["name"]}'

        discover_fields(
            pages=SAMPLE_PAGES,
            client=mock_client,
            context="competitor pricing analysis",
        )

        prompt = mock_client.complete.call_args[0][0]
        assert "competitor pricing analysis" in prompt

    def test_returns_empty_on_parse_failure(self):
        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete.return_value = "not json"

        fields = discover_fields(pages=SAMPLE_PAGES, client=mock_client)
        assert fields == []


# ---------------------------------------------------------------------------
# load_pages / load_pages_multi
# ---------------------------------------------------------------------------

class TestLoadPages:
    def test_loads_pages_from_jsonl(self, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)

        pages = load_pages(path)
        assert len(pages) == 2
        assert pages[0]["url"] == "https://example.com/"

    def test_tags_source_when_requested(self, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)

        pages = load_pages(path, tag_source=True)
        assert all(p["_source"] == path for p in pages)

    def test_loads_multi(self, tmp_path):
        path1 = str(tmp_path / "a" / "pages.jsonl")
        path2 = str(tmp_path / "b" / "pages.jsonl")
        _write_jsonl(path1, [SAMPLE_PAGES[0]])
        _write_jsonl(path2, [SAMPLE_PAGES[1]])

        pages = load_pages_multi([path1, path2])
        assert len(pages) == 2
        sources = {p["_source"] for p in pages}
        assert path1 in sources
        assert path2 in sources


# ---------------------------------------------------------------------------
# extract_from_jsonl (integration with mocked LLMClient)
# ---------------------------------------------------------------------------

class TestExtractFromJsonl:
    @patch("markcrawl.extract.LLMClient")
    def test_extracts_fields_from_all_pages(self, MockClient, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)
        output_path = str(tmp_path / "extracted.jsonl")

        mock_instance = MockClient.return_value
        mock_instance.default_model = "gpt-4o-mini"
        mock_instance.complete.return_value = '{"company_name": "Example", "pricing": "$29/mo"}'

        results = extract_from_jsonl(
            jsonl_paths=[path],
            fields=["company_name", "pricing"],
            output_path=output_path,
            extract_delay=0,
        )

        assert len(results) == 2
        assert results[0]["company_name"] == "Example"
        assert results[0]["url"] == "https://example.com/"
        assert results[0]["extracted_by"] == "gpt-4o-mini (openai)"
        assert "extraction_note" in results[0]

        # Verify output file
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

    @patch("markcrawl.extract.LLMClient")
    def test_carries_forward_citation_and_crawled_at(self, MockClient, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)
        output_path = str(tmp_path / "extracted.jsonl")

        mock_instance = MockClient.return_value
        mock_instance.default_model = "gpt-4o-mini"
        mock_instance.complete.return_value = '{"name": "test"}'

        results = extract_from_jsonl(
            jsonl_paths=[path],
            fields=["name"],
            output_path=output_path,
            extract_delay=0,
        )

        assert results[0]["crawled_at"] == "2026-04-04T12:00:00Z"
        assert "citation" in results[0]

    @patch("markcrawl.extract.LLMClient")
    def test_auto_fields_calls_discover(self, MockClient, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, SAMPLE_PAGES)

        mock_instance = MockClient.return_value
        mock_instance.default_model = "gpt-4o-mini"
        # First call: discover_fields, second+: extract_fields
        mock_instance.complete.side_effect = [
            '{"fields": ["company_name"]}',  # discover
            '{"company_name": "Example"}',   # extract page 1
            '{"company_name": "Example"}',   # extract page 2
        ]

        results = extract_from_jsonl(
            jsonl_paths=[path],
            auto_fields=True,
            auto_fields_context="test",
            extract_delay=0,
        )

        assert len(results) == 2
        assert mock_instance.complete.call_count == 3

    @patch("markcrawl.extract.LLMClient")
    def test_returns_empty_for_empty_jsonl(self, MockClient, tmp_path):
        path = str(tmp_path / "pages.jsonl")
        _write_jsonl(path, [])

        results = extract_from_jsonl(jsonl_paths=[path], fields=["name"], extract_delay=0)
        assert results == []

    @patch("markcrawl.extract.LLMClient")
    def test_includes_source_file_for_multi_input(self, MockClient, tmp_path):
        path1 = str(tmp_path / "a" / "pages.jsonl")
        path2 = str(tmp_path / "b" / "pages.jsonl")
        _write_jsonl(path1, [SAMPLE_PAGES[0]])
        _write_jsonl(path2, [SAMPLE_PAGES[1]])

        mock_instance = MockClient.return_value
        mock_instance.default_model = "gpt-4o-mini"
        mock_instance.complete.return_value = '{"name": "test"}'

        results = extract_from_jsonl(
            jsonl_paths=[path1, path2],
            fields=["name"],
            output_path=str(tmp_path / "out.jsonl"),
            extract_delay=0,
        )

        assert len(results) == 2
        assert "source_file" in results[0]
