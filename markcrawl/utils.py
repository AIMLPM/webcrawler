"""Shared utilities for markcrawl modules."""

from __future__ import annotations

import json
from typing import Dict, List


def load_pages(jsonl_path: str, tag_source: bool = False) -> List[Dict]:
    """Load pages from a crawl JSONL file.

    Args:
        jsonl_path: Path to the JSONL file.
        tag_source: If True, add a ``_source`` key to each page dict
            with the file path (used for multi-file field discovery).
    """
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
