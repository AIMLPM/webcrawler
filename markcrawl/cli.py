from __future__ import annotations

import argparse
import logging

from .core import crawl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crawl a site and extract Markdown or plain text for AI ingestion."
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base site URL, e.g., https://www.WEBSITE-TO-CRAWL.com/",
    )
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument(
        "--use-sitemap",
        action="store_true",
        default=True,
        help="Use sitemap(s) when available (default: enabled)",
    )
    parser.add_argument(
        "--no-sitemap",
        dest="use_sitemap",
        action="store_false",
        help="Disable sitemap discovery and use link-based crawling from the base page",
    )
    parser.add_argument("--delay", type=float, default=0, help="Minimum delay between requests in seconds (default: 0, adaptive throttling adjusts automatically)")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP request timeout in seconds")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=500,
        help="Maximum pages to save; 0 means unlimited",
    )
    parser.add_argument(
        "--include-subdomains",
        action="store_true",
        help="Include subdomains in the crawl scope",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="markdown",
        choices=["markdown", "text"],
        help="Output format",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Print crawl progress as pages are processed",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=20,
        help="Skip pages with fewer than this many extracted words",
    )
    parser.add_argument(
        "--user-agent",
        default=None,
        help="Optional custom user agent string",
    )
    parser.add_argument(
        "--render-js",
        action="store_true",
        help="Use Playwright to render JavaScript before extracting content (requires: pip install playwright && playwright install chromium)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of pages to fetch in parallel (default: 1)",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="HTTP/HTTPS proxy URL, e.g. http://user:pass@host:port",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previously interrupted crawl from saved state",
    )
    parser.add_argument(
        "--auto-resume",
        action="store_true",
        help="Automatically resume if a saved state exists, otherwise start fresh",
    )
    parser.add_argument(
        "--cross-dedup",
        action="store_true",
        help="Enable cross-crawl deduplication — skip pages seen in previous crawls to the same output directory",
    )
    parser.add_argument(
        "--prioritize-links",
        action="store_true",
        help="Score and prioritize discovered links by predicted content yield — crawl high-value pages first",
    )
    parser.add_argument(
        "--extractor",
        choices=["default", "trafilatura", "ensemble", "readerlm"],
        default="default",
        help="Content extraction backend (default: BS4+markdownify, trafilatura: higher recall, ensemble: best-of-both per page, readerlm: ML-based via ReaderLM-v2)",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Glob pattern to exclude URL paths (e.g. '/job/*'). Can be repeated.",
    )
    parser.add_argument(
        "--include-path",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Glob pattern to include URL paths (e.g. '/blog/*'). Only matching paths are crawled. Can be repeated.",
    )
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="Download images from within the extracted content area and save to an assets/ subdirectory. "
        "Markdown output uses local paths (assets/filename.ext) instead of [Image: alt] placeholders.",
    )
    parser.add_argument(
        "--min-image-size",
        type=int,
        default=5000,
        help="Minimum image file size in bytes to keep (default: 5000). Smaller images (icons, spacers) are skipped.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover URLs (via sitemap/links) and print them without fetching content",
    )
    parser.add_argument(
        "--smart-sample",
        action="store_true",
        help="Auto-detect templated URL patterns and sample from large clusters instead of crawling every page",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Pages to sample from each templated cluster (default: 5, used with --smart-sample)",
    )
    parser.add_argument(
        "--sample-threshold",
        type=int,
        default=20,
        help="Clusters larger than this are considered templated and sampled (default: 20, used with --smart-sample)",
    )
    parser.add_argument(
        "--i18n-filter",
        action="store_true",
        help="Skip URLs under locale path segments (e.g. /fr/, /de-DE/, /zh-Hans/) — generic, no per-domain config. "
        "Improves RAG retrieval MRR when the primary-language content is what you want to index.",
    )
    parser.add_argument(
        "--title-at-top",
        action="store_true",
        help="Prepend '# {title}' to the text field of every JSONL row when not already present. "
        "Part of the top-MRR RAG recipe in llm-crawler-benchmarks.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()

    # --auto-resume: resume if state file exists, else start fresh
    resume = args.resume
    if args.auto_resume and not resume:
        import os

        from .state import STATE_FILENAME
        state_path = os.path.join(args.out, STATE_FILENAME)
        if os.path.isfile(state_path):
            resume = True
            print(f"[auto-resume] Found saved state at {state_path}, resuming...")

    result = crawl(
        base_url=args.base,
        out_dir=args.out,
        use_sitemap=args.use_sitemap,
        delay=args.delay,
        timeout=args.timeout,
        max_pages=args.max_pages,
        include_subdomains=args.include_subdomains,
        fmt=args.fmt,
        show_progress=args.show_progress,
        min_words=args.min_words,
        user_agent=args.user_agent or None,
        render_js=args.render_js,
        concurrency=args.concurrency,
        proxy=args.proxy,
        resume=resume,
        extractor=args.extractor,
        exclude_paths=args.exclude_path or None,
        include_paths=args.include_path or None,
        dry_run=args.dry_run,
        smart_sample=args.smart_sample,
        sample_size=args.sample_size,
        sample_threshold=args.sample_threshold,
        cross_dedup=args.cross_dedup,
        prioritize_links=args.prioritize_links,
        download_images=args.download_images,
        min_image_size=args.min_image_size,
        i18n_filter=args.i18n_filter,
        title_at_top=args.title_at_top,
    )

    if not args.dry_run:
        print(f"Saved {result.pages_saved} page(s) to: {result.output_dir}")
        print(f"Index written: {result.index_file}")


if __name__ == "__main__":
    main()
