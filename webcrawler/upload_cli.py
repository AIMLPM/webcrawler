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
    parser.add_argument(
        "--supabase-url",
        default=os.environ.get("SUPABASE_URL"),
        help="Supabase project URL (or set SUPABASE_URL env var)",
    )
    parser.add_argument(
        "--supabase-key",
        default=os.environ.get("SUPABASE_KEY"),
        help="Supabase service-role key (or set SUPABASE_KEY env var)",
    )
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

    if not args.supabase_url:
        sys.exit("Error: --supabase-url or SUPABASE_URL env var is required")
    if not args.supabase_key:
        sys.exit("Error: --supabase-key or SUPABASE_KEY env var is required")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Error: OPENAI_API_KEY env var is required for embedding generation")

    inserted = upload(
        jsonl_path=args.jsonl,
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
        table=args.table,
        max_words=args.max_words,
        overlap_words=args.overlap_words,
        embedding_model=args.embedding_model,
        show_progress=args.show_progress,
    )

    print(f"Done. Inserted {inserted} row(s) into '{args.table}'.")


if __name__ == "__main__":
    main()
