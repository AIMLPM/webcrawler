"""CLI entry point for LLM-powered structured extraction."""

from __future__ import annotations

import argparse
import logging

from .extract import PROVIDER_ANTHROPIC, PROVIDER_GEMINI, PROVIDER_OPENAI, extract_from_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract structured fields from crawled pages using an LLM."
    )
    parser.add_argument(
        "--jsonl",
        required=True,
        nargs="+",
        help="Path(s) to pages.jsonl file(s) from the crawler. Pass multiple files to analyze across sites.",
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
        "--provider",
        default=PROVIDER_OPENAI,
        choices=[PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GEMINI],
        help="LLM provider (default: openai). Set the matching API key env var.",
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
        help="Number of pages to sample for --auto-fields discovery (default: 3). When using multiple JSONL files, samples are spread across all sites.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSONL path (default: extracted.jsonl in the first input file's directory)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model name. Defaults to provider's recommended model.",
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

    results = extract_from_jsonl(
        jsonl_paths=args.jsonl,
        fields=args.fields,
        output_path=args.output,
        model=args.model,
        show_progress=args.show_progress,
        auto_fields=args.auto_fields,
        auto_fields_context=args.context,
        sample_size=args.sample_size,
        provider=args.provider,
    )

    print(f"Extracted {len(results)} page(s).")


if __name__ == "__main__":
    main()
