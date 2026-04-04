"""LLM-powered structured extraction from crawled page content.

Supports OpenAI, Anthropic (Claude), and Google Gemini as extraction providers.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Provider constants
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GEMINI = "gemini"

DEFAULT_MODELS = {
    PROVIDER_OPENAI: "gpt-4o-mini",
    PROVIDER_ANTHROPIC: "claude-sonnet-4-20250514",
    PROVIDER_GEMINI: "gemini-2.0-flash",
}


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified interface for calling different LLM providers."""

    def __init__(self, provider: str = PROVIDER_OPENAI):
        self.provider = provider
        self._client = self._init_client()

    def _init_client(self) -> Any:
        if self.provider == PROVIDER_OPENAI:
            try:
                import openai
            except ImportError:
                sys.exit("Install openai:  pip install openai")
            if not os.environ.get("OPENAI_API_KEY"):
                sys.exit("Error: OPENAI_API_KEY environment variable is required")
            return openai.OpenAI()

        elif self.provider == PROVIDER_ANTHROPIC:
            try:
                import anthropic
            except ImportError:
                sys.exit("Install anthropic:  pip install anthropic")
            if not os.environ.get("ANTHROPIC_API_KEY"):
                sys.exit("Error: ANTHROPIC_API_KEY environment variable is required")
            return anthropic.Anthropic()

        elif self.provider == PROVIDER_GEMINI:
            try:
                from google import genai
            except ImportError:
                sys.exit("Install google-genai:  pip install google-genai")
            if not os.environ.get("GEMINI_API_KEY"):
                sys.exit("Error: GEMINI_API_KEY environment variable is required")
            return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        else:
            sys.exit(f"Unknown provider: {self.provider}. Use: openai, anthropic, or gemini")

    @property
    def default_model(self) -> str:
        return DEFAULT_MODELS[self.provider]

    def complete(self, prompt: str, model: Optional[str] = None) -> str:
        """Send a prompt and return the response text."""
        model = model or self.default_model

        if self.provider == PROVIDER_OPENAI:
            response = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        elif self.provider == PROVIDER_ANTHROPIC:
            response = self._client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif self.provider == PROVIDER_GEMINI:
            from google.genai import types
            response = self._client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
            return response.text


def _parse_json_response(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response, handling markdown fences."""
    text = text.strip()
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------

def extract_fields(
    text: str,
    fields: List[str],
    client: LLMClient,
    model: Optional[str] = None,
    url: str = "",
) -> Dict[str, Optional[str]]:
    """Use an LLM to extract structured fields from page text.

    Parameters
    ----------
    text:
        The page content (markdown or plain text).
    fields:
        List of field names to extract (e.g. ["company_name", "pricing", "api_endpoints"]).
    client:
        An LLMClient instance.
    model:
        The model to use for extraction. Defaults to provider's default.
    url:
        The source URL (included in the prompt for context).

    Returns
    -------
    Dict mapping each field name to its extracted value, or null if not found.
    """
    fields_description = "\n".join(f'- "{f}"' for f in fields)
    schema_fields = ", ".join(f'"{f}": "<extracted value or null>"' for f in fields)

    prompt = f"""Extract the following fields from the web page content below.
Return a JSON object with exactly these fields. If a field is not found in the content, set its value to null.
Do not add any fields that were not requested. Return ONLY the JSON object, no other text.

Fields to extract:
{fields_description}

Expected format:
{{{schema_fields}}}

Source URL: {url}

--- PAGE CONTENT ---
{text[:8000]}
"""

    response_text = client.complete(prompt, model=model)

    result = _parse_json_response(response_text)
    if result is not None:
        return result

    logger.warning("Failed to parse extraction response for %s", url)
    return {f: None for f in fields}


def discover_fields(
    pages: List[Dict],
    client: LLMClient,
    model: Optional[str] = None,
    sample_size: int = 3,
    context: Optional[str] = None,
) -> List[str]:
    """Analyze a sample of crawled pages and suggest field names for extraction.

    The sample is spread across different sources when pages come from multiple
    crawls, so the suggested fields work consistently across all sites.

    Parameters
    ----------
    pages:
        List of page dicts from one or more crawl JSONL files
        (must have "text" and "url" keys; "_source" is used to spread
        the sample across files when present).
    client:
        An LLMClient instance.
    model:
        The model to use for field discovery. Defaults to provider's default.
    sample_size:
        Total number of pages to sample (default: 3).
    context:
        Optional description of what the user is looking for
        (e.g. "competitor analysis", "API documentation").

    Returns
    -------
    List of suggested field names.
    """
    # Group pages by source file so we sample across sites
    sources: Dict[str, List[Dict]] = {}
    for page in pages:
        src = page.get("_source", "default")
        sources.setdefault(src, []).append(page)

    # Spread sample evenly across sources
    sample: List[Dict] = []
    if len(sources) > 1:
        per_source = max(1, sample_size // len(sources))
        for src_pages in sources.values():
            sample.extend(src_pages[:per_source])
        remaining = sample_size - len(sample)
        if remaining > 0:
            all_pages = [p for p in pages if p not in sample]
            sample.extend(all_pages[:remaining])
        sample = sample[:sample_size]
    else:
        sample = pages[:sample_size]

    page_summaries = []
    for i, page in enumerate(sample, 1):
        text = page.get("text", "")[:4000]
        url = page.get("url", "")
        page_summaries.append(f"--- PAGE {i}: {url} ---\n{text}")

    pages_text = "\n\n".join(page_summaries)

    context_line = ""
    if context:
        context_line = f"\nThe user's goal: {context}\n"

    multi_site_note = ""
    if len(sources) > 1:
        multi_site_note = (
            "\nIMPORTANT: These pages come from multiple different websites. "
            "Suggest fields that would be useful to compare ACROSS all these sites, "
            "not fields specific to just one site.\n"
        )

    prompt = f"""You are analyzing crawled web pages to determine what structured fields should be extracted.

Review the sample pages below and suggest 5-15 field names that would be most useful to extract from these types of pages. Field names should be lowercase_with_underscores and descriptive.
{context_line}{multi_site_note}
Return a JSON object with a single key "fields" containing an array of field name strings, ordered from most to least important.

Example response:
{{"fields": ["company_name", "product_description", "pricing", "contact_email", "features"]}}

Return ONLY the JSON object.

{pages_text}
"""

    response_text = client.complete(prompt, model=model)

    result = _parse_json_response(response_text)
    if result is not None:
        return result.get("fields", [])

    logger.warning("Failed to parse field discovery response")
    return []


# ---------------------------------------------------------------------------
# Page loading
# ---------------------------------------------------------------------------

def load_pages(jsonl_path: str, tag_source: bool = False) -> List[Dict]:
    """Load pages from a crawl JSONL file."""
    pages: List[Dict] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                page = json.loads(line)
                if tag_source:
                    page["_source"] = jsonl_path
                pages.append(page)
    return pages


def load_pages_multi(jsonl_paths: List[str]) -> List[Dict]:
    """Load and tag pages from multiple JSONL files."""
    all_pages: List[Dict] = []
    for path in jsonl_paths:
        all_pages.extend(load_pages(path, tag_source=True))
    return all_pages


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def extract_from_jsonl(
    jsonl_paths: List[str],
    fields: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    show_progress: bool = False,
    auto_fields: bool = False,
    auto_fields_context: Optional[str] = None,
    sample_size: int = 3,
    provider: str = PROVIDER_OPENAI,
) -> List[Dict]:
    """Run structured extraction on pages from one or more crawl JSONL files.

    Parameters
    ----------
    jsonl_paths:
        List of paths to pages.jsonl files from the crawler.
    fields:
        Field names to extract from each page. If None and auto_fields is True,
        fields are discovered automatically from a sample of pages.
    output_path:
        Where to write the extracted JSONL. Defaults to extracted.jsonl in the
        first JSONL file's directory.
    model:
        LLM model to use. Defaults to provider's default model.
    show_progress:
        Print progress.
    auto_fields:
        If True and fields is empty, automatically discover fields from sample pages.
    auto_fields_context:
        Optional description of what the user is looking for, passed to field discovery.
    sample_size:
        Number of pages to sample for field discovery (default: 3).
    provider:
        LLM provider — "openai", "anthropic", or "gemini".

    Returns
    -------
    List of dicts, one per page, with url, title, and extracted fields.
    """
    client = LLMClient(provider=provider)

    if show_progress:
        effective_model = model or client.default_model
        print(f"[info] using {provider} ({effective_model})")

    # Load pages from all input files
    if len(jsonl_paths) == 1:
        pages = load_pages(jsonl_paths[0], tag_source=False)
    else:
        pages = load_pages_multi(jsonl_paths)
        if show_progress:
            sources = set(p.get("_source", "") for p in pages)
            print(f"[info] loaded {len(pages)} page(s) from {len(sources)} file(s)")

    if not pages:
        logger.warning("No pages found in input file(s)")
        return []

    # Auto-discover fields if none provided
    if not fields and auto_fields:
        actual_sample = min(sample_size, len(pages))
        if show_progress:
            print(f"[discover] analyzing {actual_sample} sample page(s) to suggest fields...")
            if len(jsonl_paths) > 1:
                print(f"[discover] sampling across {len(jsonl_paths)} site(s) for cross-site field consistency")
            if auto_fields_context:
                print(f"[discover] context: {auto_fields_context}")

        fields = discover_fields(
            pages=pages,
            client=client,
            model=model,
            sample_size=sample_size,
            context=auto_fields_context,
        )

        if not fields:
            logger.warning("Field discovery returned no fields")
            return []

        if show_progress:
            print(f"[discover] suggested fields: {', '.join(fields)}")

    if not fields:
        logger.warning("No fields specified and --auto-fields not enabled")
        return []

    if output_path is None:
        output_path = str(Path(jsonl_paths[0]).parent / "extracted.jsonl")

    results: List[Dict] = []

    with open(output_path, "w", encoding="utf-8") as out:
        for i, page in enumerate(pages):
            if show_progress:
                print(f"[extract] {i + 1}/{len(pages)} — {page.get('url', '')}")

            extracted = extract_fields(
                text=page.get("text", ""),
                fields=fields,
                client=client,
                model=model,
                url=page.get("url", ""),
            )

            row = {
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                **extracted,
            }
            if len(jsonl_paths) > 1 and "_source" in page:
                row["source_file"] = page["_source"]
            results.append(row)

            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    if show_progress:
        print(f"[done] extracted {len(results)} page(s) -> {output_path}")

    return results
