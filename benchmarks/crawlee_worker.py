#!/usr/bin/env python3
"""Crawlee worker — runs in a subprocess so each invocation gets a fresh event loop.

Usage: python crawlee_worker.py <url> <out_dir> <max_pages> [url1 url2 ...]

Each call avoids the asyncio.Lock/event-loop mismatch that occurs when crawlee
is invoked multiple times in the same process (Python 3.13 regression in
crawlee's storage client).
"""
import asyncio
import json
import os
import sys
from pathlib import Path

url = sys.argv[1]
out_dir = sys.argv[2]
max_pages = int(sys.argv[3])
url_list = sys.argv[4:] if len(sys.argv) > 4 else [url]

os.makedirs(out_dir, exist_ok=True)
pages_saved = 0
jsonl_path = os.path.join(out_dir, "pages.jsonl")


async def _run():
    global pages_saved
    from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
    from markdownify import markdownify as md

    crawler = PlaywrightCrawler(max_requests_per_crawl=max_pages, headless=True)

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        global pages_saved
        if pages_saved >= max_pages:
            return
        page_url = context.request.url
        title = await context.page.title()
        content = await context.page.content()
        markdown = md(
            content,
            heading_style="ATX",
            strip=["img", "script", "style", "nav", "footer"],
        )
        if len(markdown.split()) < 5:
            return
        safe_name = page_url.replace("://", "_").replace("/", "_")[:80]
        with open(
            os.path.join(out_dir, f"{safe_name}.md"), "w", encoding="utf-8"
        ) as f:
            f.write(markdown)
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"url": page_url, "title": title, "text": markdown},
                    ensure_ascii=False,
                )
                + "\n"
            )
        pages_saved += 1
        if len(url_list) == 1 and url_list[0] == url:
            await context.enqueue_links()

    await crawler.run(url_list[:max_pages])


asyncio.run(_run())
print(pages_saved)
