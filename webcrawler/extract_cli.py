"""CLI entry point for LLM-powered structured extraction."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .extract import extract_from_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract structured fields from crawled pages using an LLM."
    )
    parser.add_argument(
        "--jsonl",
        required=True,
        help="Path to pages.jsonl produced by the crawler",
    )

    # Fields: either specify manually or auto-discover
    fields_group = parser.add_mutually_exclusive_group(required=True)
    fields_group.add_argument(
        "--fields",
        nargs="+",
        help="Field names to extract (e.g. company_name pricing api_endpoints)",
    )
    fields_group.add_argument(
        "--auto-fields",
        action="store_true",
        help="Automatically discover field names by analyzing a sample of crawled pages",
    )

    parser.add_argument(
        "--context",
        default=None,
        help="Describe your analysis goal to improve auto-field discovery (e.g. 'competitor pricing analysis', 'API documentation review')",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=3,
        help="Number of pages to sample for --auto-fields discovery (default: 3)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSONL path (default: <jsonl_dir>/extracted.jsonl)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model for extraction (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Print progress during extraction",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Error: OPENAI_API_KEY environment variable is required")

    results = extract_from_jsonl(
        jsonl_path=args.jsonl,
        fields=args.fields,
        output_path=args.output,
        model=args.model,
        show_progress=args.show_progress,
        auto_fields=args.auto_fields,
        auto_fields_context=args.context,
        sample_size=args.sample_size,
    )

    print(f"Extracted {len(results)} page(s).")


if __name__ == "__main__":
    main()
