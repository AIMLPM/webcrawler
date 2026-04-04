"""LLM-powered structured extraction from crawled page content."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_openai_client() -> Any:
    try:
        import openai
    except ImportError:
        sys.exit(
            "The 'openai' package is required for structured extraction.\n"
            "Install it with:  pip install openai"
        )
    return openai.OpenAI()


def extract_fields(
    text: str,
    fields: List[str],
    client: Any,
    model: str = "gpt-4o-mini",
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
        An OpenAI client instance.
    model:
        The model to use for extraction.
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

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError, AttributeError):
        logger.warning("Failed to parse extraction response for %s", url)
        return {f: None for f in fields}


def discover_fields(
    pages: List[Dict],
    client: Any,
    model: str = "gpt-4o-mini",
    sample_size: int = 3,
    context: Optional[str] = None,
) -> List[str]:
    """Analyze a sample of crawled pages and suggest field names for extraction.

    Parameters
    ----------
    pages:
        List of page dicts from the crawl JSONL (must have "text" and "url" keys).
    client:
        An OpenAI client instance.
    model:
        The model to use for field discovery.
    sample_size:
        Number of pages to sample (default: 3).
    context:
        Optional description of what the user is looking for
        (e.g. "competitor analysis", "API documentation").

    Returns
    -------
    List of suggested field names.
    """
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

    prompt = f"""You are analyzing crawled web pages to determine what structured fields should be extracted.

Review the sample pages below and suggest 5-15 field names that would be most useful to extract from these types of pages. Field names should be lowercase_with_underscores and descriptive.
{context_line}
Return a JSON object with a single key "fields" containing an array of field name strings, ordered from most to least important.

Example response:
{{"fields": ["company_name", "product_description", "pricing", "contact_email", "features"]}}

Return ONLY the JSON object.

{pages_text}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return result.get("fields", [])
    except (json.JSONDecodeError, IndexError, AttributeError):
        logger.warning("Failed to parse field discovery response")
        return []


def load_pages(jsonl_path: str) -> List[Dict]:
    """Load pages from a crawl JSONL file."""
    pages: List[Dict] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))
    return pages


def extract_from_jsonl(
    jsonl_path: str,
    fields: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    model: str = "gpt-4o-mini",
    show_progress: bool = False,
    auto_fields: bool = False,
    auto_fields_context: Optional[str] = None,
    sample_size: int = 3,
) -> List[Dict]:
    """Run structured extraction on all pages in a crawl JSONL file.

    Parameters
    ----------
    jsonl_path:
        Path to pages.jsonl from the crawler.
    fields:
        Field names to extract from each page. If None and auto_fields is True,
        fields are discovered automatically from a sample of pages.
    output_path:
        Where to write the extracted JSONL. Defaults to <jsonl_dir>/extracted.jsonl.
    model:
        OpenAI model to use.
    show_progress:
        Print progress.
    auto_fields:
        If True and fields is empty, automatically discover fields from sample pages.
    auto_fields_context:
        Optional description of what the user is looking for, passed to field discovery.
    sample_size:
        Number of pages to sample for field discovery (default: 3).

    Returns
    -------
    List of dicts, one per page, with url, title, and extracted fields.
    """
    client = _get_openai_client()

    pages = load_pages(jsonl_path)

    if not pages:
        logger.warning("No pages found in %s", jsonl_path)
        return []

    # Auto-discover fields if none provided
    if not fields and auto_fields:
        if show_progress:
            print(f"[discover] analyzing {min(sample_size, len(pages))} sample page(s) to suggest fields...")
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
        output_path = str(Path(jsonl_path).parent / "extracted.jsonl")

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
            results.append(row)

            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    if show_progress:
        print(f"[done] extracted {len(results)} page(s) -> {output_path}")

    return results
