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
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
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
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()

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
        resume=args.resume,
    )

    print(f"Saved {result.pages_saved} page(s) to: {result.output_dir}")
    print(f"Index written: {result.index_file}")


if __name__ == "__main__":
    main()
