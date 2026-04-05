# Extraction Quality Comparison

## Methodology

Three automated quality metrics, no LLM or human review needed:

1. **Junk detection** — known boilerplate phrases (nav, footer, breadcrumbs) found in output
2. **Structure preservation** — heading count and code block count in Markdown
3. **Cross-tool consensus** — sentences shared with other tools (precision) vs sentences all tools agree on (recall)

Precision answers: "How much of this tool's output is real content?"
Recall answers: "How much of the agreed-upon content did this tool capture?"

## quotes-toscrape

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 254 | 0 | 2.5 | 0.0 | 80% | 80% |
| crawl4ai | 262 | 0 | 2.5 | 0.0 | 80% | 80% |
| scrapy+md | 262 | 0 | 2.5 | 0.0 | 33% | 80% |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md |
|---|---|---|---|
| quotes.toscrape.com/ | 271 | 282 | 282 |
| quotes.toscrape.com/author/Albert-Einstein | 621 | 629 | — |
| quotes.toscrape.com/author/Albert-Einstein/ | — | — | 629 |
| quotes.toscrape.com/author/Andre-Gide | 173 | 181 | — |
| quotes.toscrape.com/author/Andre-Gide/ | — | — | 181 |
| quotes.toscrape.com/author/Eleanor-Roosevelt | 242 | 250 | — |
| quotes.toscrape.com/author/Eleanor-Roosevelt/ | — | — | 250 |
| quotes.toscrape.com/author/Jane-Austen | 333 | 341 | — |
| quotes.toscrape.com/author/Jane-Austen/ | — | — | 341 |
| quotes.toscrape.com/author/Marilyn-Monroe | 382 | 390 | — |
| quotes.toscrape.com/author/Marilyn-Monroe/ | — | — | 390 |
| quotes.toscrape.com/author/Steve-Martin | 139 | 147 | — |
| quotes.toscrape.com/author/Steve-Martin/ | — | — | 147 |
| quotes.toscrape.com/author/Thomas-A-Edison | 201 | 209 | — |
| quotes.toscrape.com/author/Thomas-A-Edison/ | — | — | 209 |
| quotes.toscrape.com/tag/adulthood/page/1/ | 45 | 53 | 53 |
| quotes.toscrape.com/tag/change/page/1/ | 53 | 61 | 61 |
| quotes.toscrape.com/tag/inspirational/ | 484 | 495 | 495 |
| quotes.toscrape.com/tag/live/page/1/ | 59 | 67 | 67 |
| quotes.toscrape.com/tag/love/ | 673 | 684 | 684 |
| quotes.toscrape.com/tag/simile/page/1/ | 76 | 84 | 84 |
| quotes.toscrape.com/tag/world/page/1/ | 53 | 61 | 61 |

</details>

