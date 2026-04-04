"""CLI entry point for uploading crawl output to Supabase."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .upload import DEFAULT_EMBEDDING_MODEL, upload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload crawled pages to Supabase with embeddings for RAG / vector search."
    )
    parser.add_argument(
        "--jsonl",
        required=True,
        help="Path to pages.jsonl produced by the crawler",
    )
    # Supabase credentials are read from environment variables only
    # to avoid leaking secrets in shell history or process listings.
    # Set SUPABASE_URL, SUPABASE_KEY, and OPENAI_API_KEY before running.
    parser.add_argument(
        "--table",
        default="documents",
        help="Target table name (default: documents)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=400,
        help="Max words per chunk (default: 400)",
    )
    parser.add_argument(
        "--overlap-words",
        type=int,
        default=50,
        help="Overlap words between chunks (default: 50)",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"OpenAI embedding model (default: {DEFAULT_EMBEDDING_MODEL})",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Print progress during upload",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url:
        sys.exit("Error: SUPABASE_URL environment variable is required")
    if not supabase_key:
        sys.exit("Error: SUPABASE_KEY environment variable is required")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Error: OPENAI_API_KEY environment variable is required")

    inserted = upload(
        jsonl_path=args.jsonl,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        table=args.table,
        max_words=args.max_words,
        overlap_words=args.overlap_words,
        embedding_model=args.embedding_model,
        show_progress=args.show_progress,
    )

    print(f"Done. Inserted {inserted} row(s) into '{args.table}'.")


if __name__ == "__main__":
    main()
