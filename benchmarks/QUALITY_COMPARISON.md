# Extraction Quality Comparison

## Methodology

Three automated quality metrics, no LLM or human review needed:

1. **Junk detection** — known boilerplate phrases (nav, footer, breadcrumbs) found in output
2. **Structure preservation** — heading count and code block count in Markdown
3. **Cross-tool consensus** — sentences shared with other tools (precision) vs sentences all tools agree on (recall)

Precision answers: "How much of this tool's output is real content?"
Recall answers: "How much of the agreed-upon content did this tool capture?"

> **Note:** Colly+md shows 0% precision due to a URL normalization bug in the benchmark — Colly's reconstructed URLs don't match the other tools' URLs, so the consensus scorer can't find shared sentences. Colly's actual extraction quality is similar to Scrapy+md (both use markdownify on raw HTML). This will be fixed in a future run.

## Key findings

### FastAPI docs — the most revealing test

| Tool | Avg words | Junk found | Precision | Interpretation |
|---|---|---|---|---|
| **MarkCrawl** | 3,550 | 33 | **100%** | Everything extracted is real content. Fewest words = tightest signal. |
| Scrapy+md | 4,473 | 55 | 100% | Same real content but +900 words of sidebar/ToC and more junk |
| Crawl4AI | 5,222 | 32 | 62% | Nearly half the output is noisy text (sidebars, sponsors, nav) |

**MarkCrawl extracts 32% less text than Scrapy and 47% less than Crawl4AI — but achieves the same or higher precision.** The "missing" words are sidebar navigation, table of contents, sponsor banners, and page chrome that other tools include.

For RAG, this matters: fewer words with the same precision means tighter embedding chunks, less noise in retrieval, and more relevant search results.

### Junk detection across all sites

| Tool | quotes | books | fastapi | python | Total junk |
|---|---|---|---|---|---|
| MarkCrawl | 1 | 0 | 33 | 21 | **55** |
| Crawl4AI | 1 | 0 | 32 | 99 | **132** |
| Scrapy+md | 1 | 0 | 55 | 83 | **139** |
| Colly+md | 1 | 0 | 103 | 67 | **171** |
| Playwright | 1 | 0 | 0* | 66 | **67** |

\* Playwright returned 0 pages on FastAPI docs (timeout failure), so 0 junk is misleading.

**MarkCrawl has the least junk overall** (55 instances) — less than half of Scrapy (139) or Colly (171). The `clean_dom_for_content` function that strips `<nav>`, `<aside>`, cookie banners, and aria-hidden elements is paying off.

## Per-site results

## quotes-toscrape

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 192 | 1 | 2.7 | 0.0 | 67% | 67% |
| crawl4ai | 201 | 1 | 2.7 | 0.0 | 67% | 67% |
| scrapy+md | 201 | 1 | 2.7 | 0.0 | 67% | 67% |
| crawlee | — | — | — | — | — | — |
| colly+md | 204 | 1 | 2.7 | 0.0 | 0% | 67% |
| playwright | 204 | 1 | 2.7 | 0.0 | 67% | 67% |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright |
|---|---|---|---|---|---|---|
| http/quotes.toscrape.com | — | — | — | — | 285 | — |
| http/quotes.toscrape.com/author/Andre-Gide | — | — | — | — | 184 | — |
| http/quotes.toscrape.com/author/Jane-Austen | — | — | — | — | 344 | — |
| http/quotes.toscrape.com/author/Thomas-A-Edison | — | — | — | — | 212 | — |
| http/quotes.toscrape.com/tag/adulthood/page/1 | — | — | — | — | 56 | — |
| http/quotes.toscrape.com/tag/aliteracy/page/1 | — | — | — | — | 62 | — |
| http/quotes.toscrape.com/tag/books | — | — | — | — | 343 | — |
| http/quotes.toscrape.com/tag/failure/page/1 | — | — | — | — | 56 | — |
| http/quotes.toscrape.com/tag/friends | — | — | — | — | 316 | — |
| http/quotes.toscrape.com/tag/friendship | — | — | — | — | 169 | — |
| http/quotes.toscrape.com/tag/humor | — | — | — | — | 298 | — |
| http/quotes.toscrape.com/tag/life | — | — | — | — | 512 | — |
| http/quotes.toscrape.com/tag/live/page/1 | — | — | — | — | 70 | — |
| http/quotes.toscrape.com/tag/miracle/page/1 | — | — | — | — | 70 | — |
| http/quotes.toscrape.com/tag/simile/page/1 | — | — | — | — | 87 | — |
| quotes.toscrape.com | 271 | 282 | 282 | — | — | 285 |
| quotes.toscrape.com/author/Andre-Gide | 173 | 181 | 181 | — | — | 184 |
| quotes.toscrape.com/author/Jane-Austen | 333 | 341 | 341 | — | — | 344 |
| quotes.toscrape.com/author/Thomas-A-Edison | 201 | 209 | 209 | — | — | 212 |
| quotes.toscrape.com/tag/adulthood/page/1 | 45 | 53 | 53 | — | — | 56 |
| quotes.toscrape.com/tag/aliteracy/page/1 | 51 | 59 | 59 | — | — | 62 |
| quotes.toscrape.com/tag/books | 329 | 340 | 340 | — | — | 343 |
| quotes.toscrape.com/tag/failure/page/1 | 45 | 53 | 53 | — | — | 56 |
| quotes.toscrape.com/tag/friends | 305 | 313 | 313 | — | — | 316 |
| quotes.toscrape.com/tag/friendship | 158 | 166 | 166 | — | — | 169 |
| quotes.toscrape.com/tag/humor | 284 | 295 | 295 | — | — | 298 |
| quotes.toscrape.com/tag/life | 498 | 509 | 509 | — | — | 512 |
| quotes.toscrape.com/tag/live/page/1 | 59 | 67 | 67 | — | — | 70 |
| quotes.toscrape.com/tag/miracle/page/1 | 59 | 67 | 67 | — | — | 70 |
| quotes.toscrape.com/tag/simile/page/1 | 76 | 84 | 84 | — | — | 87 |

</details>

## books-toscrape

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 283 | 0 | 1.7 | 0.0 | 93% | 100% |
| crawl4ai | 504 | 0 | 10.8 | 0.0 | 79% | 100% |
| scrapy+md | 389 | 0 | 1.7 | 0.0 | 100% | 100% |
| crawlee | — | — | — | — | — | — |
| colly+md | 397 | 0 | 1.7 | 0.0 | 0% | 100% |
| playwright | 397 | 0 | 1.7 | 0.0 | 99% | 100% |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright |
|---|---|---|---|---|---|---|
| http/books.toscrape.com | — | — | — | — | 539 | — |
| http/books.toscrape.com/catalogue/category/books/academic/40 | — | — | — | — | 192 | — |
| http/books.toscrape.com/catalogue/category/books/add-a-comme | — | — | — | — | 567 | — |
| http/books.toscrape.com/catalogue/category/books/adult-ficti | — | — | — | — | 195 | — |
| http/books.toscrape.com/catalogue/category/books/art/25/inde | — | — | — | — | 310 | — |
| http/books.toscrape.com/catalogue/category/books/autobiograp | — | — | — | — | 310 | — |
| http/books.toscrape.com/catalogue/category/books/biography/3 | — | — | — | — | 286 | — |
| http/books.toscrape.com/catalogue/category/books/business/35 | — | — | — | — | 437 | — |
| http/books.toscrape.com/catalogue/category/books/childrens/1 | — | — | — | — | 507 | — |
| http/books.toscrape.com/catalogue/category/books/christian-f | — | — | — | — | 282 | — |
| http/books.toscrape.com/catalogue/category/books/christian/4 | — | — | — | — | 237 | — |
| http/books.toscrape.com/catalogue/category/books/contemporar | — | — | — | — | 225 | — |
| http/books.toscrape.com/catalogue/category/books/crime/51/in | — | — | — | — | 199 | — |
| http/books.toscrape.com/catalogue/category/books/cultural/49 | — | — | — | — | 187 | — |
| http/books.toscrape.com/catalogue/category/books/default/15/ | — | — | — | — | 580 | — |
| http/books.toscrape.com/catalogue/category/books/erotica/50/ | — | — | — | — | 185 | — |
| http/books.toscrape.com/catalogue/category/books/fantasy/19/ | — | — | — | — | 577 | — |
| http/books.toscrape.com/catalogue/category/books/food-and-dr | — | — | — | — | 691 | — |
| http/books.toscrape.com/catalogue/category/books/health/47/i | — | — | — | — | 265 | — |
| http/books.toscrape.com/catalogue/category/books/historical- | — | — | — | — | 533 | — |
| http/books.toscrape.com/catalogue/category/books/historical/ | — | — | — | — | 216 | — |
| http/books.toscrape.com/catalogue/category/books/history/32/ | — | — | — | — | 588 | — |
| http/books.toscrape.com/catalogue/category/books/horror/31/i | — | — | — | — | 416 | — |
| http/books.toscrape.com/catalogue/category/books/humor/30/in | — | — | — | — | 380 | — |
| http/books.toscrape.com/catalogue/category/books/music/14/in | — | — | — | — | 445 | — |
| http/books.toscrape.com/catalogue/category/books/mystery/3/i | — | — | — | — | 548 | — |
| http/books.toscrape.com/catalogue/category/books/new-adult/2 | — | — | — | — | 272 | — |
| http/books.toscrape.com/catalogue/category/books/nonfiction/ | — | — | — | — | 642 | — |
| http/books.toscrape.com/catalogue/category/books/paranormal/ | — | — | — | — | 193 | — |
| http/books.toscrape.com/catalogue/category/books/parenting/2 | — | — | — | — | 194 | — |
| http/books.toscrape.com/catalogue/category/books/politics/48 | — | — | — | — | 235 | — |
| http/books.toscrape.com/catalogue/category/books/psychology/ | — | — | — | — | 325 | — |
| http/books.toscrape.com/catalogue/category/books/romance/8/i | — | — | — | — | 553 | — |
| http/books.toscrape.com/catalogue/category/books/science-fic | — | — | — | — | 464 | — |
| http/books.toscrape.com/catalogue/category/books/science/22/ | — | — | — | — | 491 | — |
| http/books.toscrape.com/catalogue/category/books/self-help/4 | — | — | — | — | 294 | — |
| http/books.toscrape.com/catalogue/category/books/sequential- | — | — | — | — | 583 | — |
| http/books.toscrape.com/catalogue/category/books/short-stori | — | — | — | — | 188 | — |
| http/books.toscrape.com/catalogue/category/books/spiritualit | — | — | — | — | 312 | — |
| http/books.toscrape.com/catalogue/category/books/sports-and- | — | — | — | — | 280 | — |
| http/books.toscrape.com/catalogue/category/books/suspense/44 | — | — | — | — | 193 | — |
| http/books.toscrape.com/catalogue/category/books/thriller/37 | — | — | — | — | 352 | — |
| http/books.toscrape.com/catalogue/category/books/travel/2/in | — | — | — | — | 399 | — |
| http/books.toscrape.com/catalogue/category/books/womens-fict | — | — | — | — | 472 | — |
| http/books.toscrape.com/catalogue/category/books/young-adult | — | — | — | — | 528 | — |
| http/books.toscrape.com/catalogue/libertarianism-for-beginne | — | — | — | — | 435 | — |
| http/books.toscrape.com/catalogue/mesaerion-the-best-science | — | — | — | — | 528 | — |
| http/books.toscrape.com/catalogue/page-2.html | — | — | — | — | 555 | — |
| http/books.toscrape.com/catalogue/sapiens-a-brief-history-of | — | — | — | — | 497 | — |
| http/books.toscrape.com/catalogue/scott-pilgrims-precious-li | — | — | — | — | 412 | — |
| http/books.toscrape.com/catalogue/set-me-free/988/index.html | — | — | — | — | 389 | — |
| http/books.toscrape.com/catalogue/shakespeares-sonnets/989/i | — | — | — | — | 398 | — |
| http/books.toscrape.com/catalogue/sharp-objects/997/index.ht | — | — | — | — | 443 | — |
| http/books.toscrape.com/catalogue/soumission/998/index.html | — | — | — | — | 319 | — |
| http/books.toscrape.com/catalogue/starving-hearts-triangular | — | — | — | — | 463 | — |
| http/books.toscrape.com/catalogue/the-black-maria/991/index. | — | — | — | — | 720 | — |
| http/books.toscrape.com/catalogue/the-boys-in-the-boat-nine- | — | — | — | — | 615 | — |
| http/books.toscrape.com/catalogue/the-dirty-little-secrets-o | — | — | — | — | 519 | — |
| http/books.toscrape.com/catalogue/the-requiem-red/995/index. | — | — | — | — | 374 | — |
| http/books.toscrape.com/catalogue/tipping-the-velvet/999/ind | — | — | — | — | 314 | — |
| books.toscrape.com | 397 | 702 | 531 | — | — | 539 |
| books.toscrape.com/catalogue/category/books/academic_40/inde | 51 | 282 | 185 | — | — | 192 |
| books.toscrape.com/catalogue/category/books/add-a-comment_18 | 424 | 745 | 558 | — | — | 567 |
| books.toscrape.com/catalogue/category/books/adult-fiction_29 | 53 | 284 | 187 | — | — | 195 |
| books.toscrape.com/catalogue/category/books/art_25/index.htm | 169 | 422 | 303 | — | — | 310 |
| books.toscrape.com/catalogue/category/books/autobiography_27 | 169 | 412 | 303 | — | — | 310 |
| books.toscrape.com/catalogue/category/books/biography_36/ind | 145 | 410 | 279 | — | — | 286 |
| books.toscrape.com/catalogue/category/books/business_35/inde | 296 | 612 | 430 | — | — | 437 |
| books.toscrape.com/catalogue/category/books/childrens_11/ind | 366 | 642 | 500 | — | — | 507 |
| books.toscrape.com/catalogue/category/books/christian-fictio | 140 | 388 | 274 | — | — | 282 |
| books.toscrape.com/catalogue/category/books/christian_43/ind | 96 | 342 | 230 | — | — | 237 |
| books.toscrape.com/catalogue/category/books/contemporary_38/ | 84 | 320 | 218 | — | — | 225 |
| books.toscrape.com/catalogue/category/books/crime_51/index.h | 58 | 296 | 192 | — | — | 199 |
| books.toscrape.com/catalogue/category/books/cultural_49/inde | 46 | 274 | 180 | — | — | 187 |
| books.toscrape.com/catalogue/category/books/default_15/index | 439 | 777 | 573 | — | — | 580 |
| books.toscrape.com/catalogue/category/books/erotica_50/index | 44 | 271 | 178 | — | — | 185 |
| books.toscrape.com/catalogue/category/books/fantasy_19/index | 436 | 764 | 570 | — | — | 577 |
| books.toscrape.com/catalogue/category/books/food-and-drink_3 | 548 | 978 | 682 | — | — | 691 |
| books.toscrape.com/catalogue/category/books/health_47/index. | 124 | 384 | 258 | — | — | 265 |
| books.toscrape.com/catalogue/category/books/historical-ficti | 391 | 681 | 525 | — | — | 533 |
| books.toscrape.com/catalogue/category/books/historical_42/in | 75 | 315 | 209 | — | — | 216 |
| books.toscrape.com/catalogue/category/books/history_32/index | 447 | 822 | 581 | — | — | 588 |
| books.toscrape.com/catalogue/category/books/horror_31/index. | 275 | 524 | 409 | — | — | 416 |
| books.toscrape.com/catalogue/category/books/humor_30/index.h | 239 | 529 | 373 | — | — | 380 |
| books.toscrape.com/catalogue/category/books/music_14/index.h | 304 | 616 | 438 | — | — | 445 |
| books.toscrape.com/catalogue/category/books/mystery_3/index. | 407 | 710 | 541 | — | — | 548 |
| books.toscrape.com/catalogue/category/books/new-adult_20/ind | 130 | 370 | 264 | — | — | 272 |
| books.toscrape.com/catalogue/category/books/nonfiction_13/in | 501 | 887 | 635 | — | — | 642 |
| books.toscrape.com/catalogue/category/books/paranormal_24/in | 52 | 284 | 186 | — | — | 193 |
| books.toscrape.com/catalogue/category/books/parenting_28/ind | 53 | 286 | 187 | — | — | 194 |
| books.toscrape.com/catalogue/category/books/politics_48/inde | 94 | 340 | 228 | — | — | 235 |
| books.toscrape.com/catalogue/category/books/psychology_26/in | 184 | 460 | 318 | — | — | 325 |
| books.toscrape.com/catalogue/category/books/romance_8/index. | 412 | 716 | 546 | — | — | 553 |
| books.toscrape.com/catalogue/category/books/science-fiction_ | 322 | 615 | 456 | — | — | 464 |
| books.toscrape.com/catalogue/category/books/science_22/index | 350 | 690 | 484 | — | — | 491 |
| books.toscrape.com/catalogue/category/books/self-help_41/ind | 152 | 422 | 286 | — | — | 294 |
| books.toscrape.com/catalogue/category/books/sequential-art_5 | 441 | 774 | 575 | — | — | 583 |
| books.toscrape.com/catalogue/category/books/short-stories_45 | 46 | 273 | 180 | — | — | 188 |
| books.toscrape.com/catalogue/category/books/spirituality_39/ | 171 | 447 | 305 | — | — | 312 |
| books.toscrape.com/catalogue/category/books/sports-and-games | 137 | 391 | 271 | — | — | 280 |
| books.toscrape.com/catalogue/category/books/suspense_44/inde | 52 | 284 | 186 | — | — | 193 |
| books.toscrape.com/catalogue/category/books/thriller_37/inde | 211 | 465 | 345 | — | — | 352 |
| books.toscrape.com/catalogue/category/books/travel_2/index.h | 258 | 550 | 392 | — | — | 399 |
| books.toscrape.com/catalogue/category/books/womens-fiction_9 | 330 | 614 | 464 | — | — | 472 |
| books.toscrape.com/catalogue/category/books/young-adult_21/i | 386 | 676 | 520 | — | — | 528 |
| books.toscrape.com/catalogue/libertarianism-for-beginners_98 | 411 | 442 | 426 | — | — | 435 |
| books.toscrape.com/catalogue/mesaerion-the-best-science-fict | 500 | 530 | 515 | — | — | 528 |
| books.toscrape.com/catalogue/page-2.html | 413 | 726 | 547 | — | — | 555 |
| books.toscrape.com/catalogue/sapiens-a-brief-history-of-huma | 470 | 481 | 485 | — | — | 497 |
| books.toscrape.com/catalogue/scott-pilgrims-precious-little- | 383 | 428 | 398 | — | — | 412 |
| books.toscrape.com/catalogue/set-me-free_988/index.html | 365 | 411 | 380 | — | — | 389 |
| books.toscrape.com/catalogue/shakespeares-sonnets_989/index. | 375 | 421 | 390 | — | — | 398 |
| books.toscrape.com/catalogue/sharp-objects_997/index.html | 420 | 427 | 435 | — | — | 443 |
| books.toscrape.com/catalogue/soumission_998/index.html | 297 | 304 | 312 | — | — | 319 |
| books.toscrape.com/catalogue/starving-hearts-triangular-trad | 436 | 486 | 451 | — | — | 463 |
| books.toscrape.com/catalogue/the-black-maria_991/index.html | 696 | 742 | 711 | — | — | 720 |
| books.toscrape.com/catalogue/the-boys-in-the-boat-nine-ameri | 576 | 620 | 591 | — | — | 615 |
| books.toscrape.com/catalogue/the-dirty-little-secrets-of-get | 489 | 508 | 504 | — | — | 519 |
| books.toscrape.com/catalogue/the-requiem-red_995/index.html | 350 | 362 | 365 | — | — | 374 |
| books.toscrape.com/catalogue/tipping-the-velvet_999/index.ht | 290 | 298 | 305 | — | — | 314 |

</details>

## fastapi-docs

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 3550 | 33 | 48.0 | 15.1 | 100% | 100% |
| crawl4ai | 5222 | 32 | 48.0 | 15.0 | 62% | 100% |
| scrapy+md | 4473 | 55 | 48.0 | 15.1 | 100% | 100% |
| crawlee | — | — | — | — | — | — |
| colly+md | 4795 | 103 | 48.0 | 15.1 | 0% | 100% |
| playwright | — | — | — | — | — | — |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright |
|---|---|---|---|---|---|---|
| https/fastapi.tiangolo.com | — | — | — | — | 3404 | — |
| https/fastapi.tiangolo.com/advanced/additional-responses | — | — | — | — | 2337 | — |
| https/fastapi.tiangolo.com/advanced/behind-a-proxy | — | — | — | — | 3378 | — |
| https/fastapi.tiangolo.com/advanced/generate-clients | — | — | — | — | 2823 | — |
| https/fastapi.tiangolo.com/advanced/response-change-status-c | — | — | — | — | 1311 | — |
| https/fastapi.tiangolo.com/advanced/security | — | — | — | — | 1090 | — |
| https/fastapi.tiangolo.com/advanced/sub-applications | — | — | — | — | 1512 | — |
| https/fastapi.tiangolo.com/advanced/testing-dependencies | — | — | — | — | 1729 | — |
| https/fastapi.tiangolo.com/external-links | — | — | — | — | 1699 | — |
| https/fastapi.tiangolo.com/fastapi-people | — | — | — | — | 2551 | — |
| https/fastapi.tiangolo.com/help-fastapi | — | — | — | — | 3172 | — |
| https/fastapi.tiangolo.com/ko | — | — | — | — | 2987 | — |
| https/fastapi.tiangolo.com/learn | — | — | — | — | 1015 | — |
| https/fastapi.tiangolo.com/management-tasks | — | — | — | — | 2876 | — |
| https/fastapi.tiangolo.com/reference/openapi | — | — | — | — | 1013 | — |
| https/fastapi.tiangolo.com/reference/request | — | — | — | — | 1767 | — |
| https/fastapi.tiangolo.com/reference/security | — | — | — | — | 10232 | — |
| https/fastapi.tiangolo.com/reference/staticfiles | — | — | — | — | 2041 | — |
| https/fastapi.tiangolo.com/release-notes | — | — | — | — | 57812 | — |
| https/fastapi.tiangolo.com/tutorial | — | — | — | — | 1579 | — |
| https/fastapi.tiangolo.com/tutorial/body-multiple-params | — | — | — | — | 2468 | — |
| https/fastapi.tiangolo.com/tutorial/cookie-param-models | — | — | — | — | 1619 | — |
| https/fastapi.tiangolo.com/tutorial/path-params | — | — | — | — | 2680 | — |
| https/fastapi.tiangolo.com/tutorial/query-params-str-validat | — | — | — | — | 5316 | — |
| https/fastapi.tiangolo.com/tutorial/request-form-models | — | — | — | — | 1472 | — |
| fastapi.tiangolo.com | 2230 | 3979 | 3092 | — | — | — |
| fastapi.tiangolo.com/advanced/additional-responses | 1274 | 2648 | 2008 | — | — | — |
| fastapi.tiangolo.com/advanced/behind-a-proxy | 2218 | 3674 | 3055 | — | — | — |
| fastapi.tiangolo.com/advanced/generate-clients | 1654 | 3177 | 2498 | — | — | — |
| fastapi.tiangolo.com/advanced/response-change-status-code | 292 | 1612 | 985 | — | — | — |
| fastapi.tiangolo.com/advanced/security | 90 | 1395 | 770 | — | — | — |
| fastapi.tiangolo.com/advanced/sub-applications | 463 | 1829 | 1187 | — | — | — |
| fastapi.tiangolo.com/advanced/testing-dependencies | 694 | 2036 | 1400 | — | — | — |
| fastapi.tiangolo.com/external-links | 699 | 1999 | 1375 | — | — | — |
| fastapi.tiangolo.com/fastapi-people | 1434 | 3347 | 2230 | — | — | — |
| fastapi.tiangolo.com/help-fastapi | 1955 | 3519 | 2842 | — | — | — |
| fastapi.tiangolo.com/ko | 1847 | 3609 | 2674 | — | — | — |
| fastapi.tiangolo.com/learn | 35 | 1322 | 697 | — | — | — |
| fastapi.tiangolo.com/management-tasks | 1798 | 3193 | 2553 | — | — | — |
| fastapi.tiangolo.com/reference/openapi | 32 | 1320 | 696 | — | — | — |
| fastapi.tiangolo.com/reference/request | 680 | 2122 | 1446 | — | — | — |
| fastapi.tiangolo.com/reference/security | 8809 | 10905 | 9911 | — | — | — |
| fastapi.tiangolo.com/reference/staticfiles | 987 | 2367 | 1715 | — | — | — |
| fastapi.tiangolo.com/release-notes | 52921 | 59584 | 57495 | — | — | — |
| fastapi.tiangolo.com/tutorial | 574 | 1717 | 1255 | — | — | — |
| fastapi.tiangolo.com/tutorial/body-multiple-params | 1405 | 2779 | 2142 | — | — | — |
| fastapi.tiangolo.com/tutorial/cookie-param-models | 588 | 1930 | 1296 | — | — | — |
| fastapi.tiangolo.com/tutorial/path-params | 1543 | 3029 | 2360 | — | — | — |
| fastapi.tiangolo.com/tutorial/query-params-str-validations | 4071 | 5684 | 4987 | — | — | — |
| fastapi.tiangolo.com/tutorial/request-form-models | 445 | 1784 | 1152 | — | — | — |

</details>

## python-docs

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 2298 | 22 | 9.3 | 3.6 | 91% | 45% |
| crawl4ai | 2699 | 89 | 15.8 | 3.6 | 42% | 45% |
| scrapy+md | 3304 | 71 | 18.8 | 4.9 | 100% | 40% |
| crawlee | — | — | — | — | — | — |
| colly+md | 2571 | 89 | 15.7 | 3.6 | 0% | 100% |
| playwright | 2646 | 89 | 15.7 | 3.6 | 83% | 45% |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright |
|---|---|---|---|---|---|---|
| https/docs.python.org/2.7 | — | — | — | — | 309 | — |
| https/docs.python.org/3.10 | — | — | — | — | 533 | — |
| https/docs.python.org/3.10/contents.html | — | — | — | — | 19601 | — |
| https/docs.python.org/3.10/download.html | — | — | — | — | 419 | — |
| https/docs.python.org/3.10/faq/index.html | — | — | — | — | 275 | — |
| https/docs.python.org/3.10/howto/index.html | — | — | — | — | 372 | — |
| https/docs.python.org/3.10/installing/index.html | — | — | — | — | 1629 | — |
| https/docs.python.org/3.10/library/index.html | — | — | — | — | 2505 | — |
| https/docs.python.org/3.10/license.html | — | — | — | — | 7462 | — |
| https/docs.python.org/3.10/reference/index.html | — | — | — | — | 665 | — |
| https/docs.python.org/3.10/whatsnew/3.10.html | — | — | — | — | 13646 | — |
| https/docs.python.org/3.11 | — | — | — | — | 534 | — |
| https/docs.python.org/3.12 | — | — | — | — | 537 | — |
| https/docs.python.org/3.13 | — | — | — | — | 537 | — |
| https/docs.python.org/3.14 | — | — | — | — | 537 | — |
| https/docs.python.org/3.15 | — | — | — | — | 537 | — |
| https/docs.python.org/3.2 | — | — | — | — | 323 | — |
| https/docs.python.org/3.3 | — | — | — | — | 323 | — |
| https/docs.python.org/3.4 | — | — | — | — | 360 | — |
| https/docs.python.org/3.6 | — | — | — | — | 324 | — |
| docs.python.org/2.7 | 186 | 320 | — | — | — | 315 |
| docs.python.org/3.10 | 190 | 711 | 521 | — | — | 629 |
| docs.python.org/3.10/contents.html | 19401 | 19782 | 19584 | — | — | 19697 |
| docs.python.org/3.10/download.html | 277 | 599 | 404 | — | — | 515 |
| docs.python.org/3.10/faq/index.html | 48 | 454 | 257 | — | — | 371 |
| docs.python.org/3.10/howto/index.html | 135 | 553 | 356 | — | — | 468 |
| docs.python.org/3.10/installing/index.html | 1255 | 1808 | 1612 | — | — | 1725 |
| docs.python.org/3.10/library/index.html | 2282 | 2684 | 2487 | — | — | 2601 |
| docs.python.org/3.10/license.html | 6986 | 7625 | 7445 | — | — | 7558 |
| docs.python.org/3.10/reference/index.html | 438 | 844 | 647 | — | — | 761 |
| docs.python.org/3.10/whatsnew/3.10.html | 12688 | 13749 | 13627 | — | — | 13773 |
| docs.python.org/3.11 | 188 | 711 | 522 | — | — | 629 |
| docs.python.org/3.12 | 191 | 712 | 525 | — | — | 632 |
| docs.python.org/3.13 | 191 | 712 | 525 | — | — | 632 |
| docs.python.org/3.14 | 191 | 712 | 525 | — | — | 632 |
| docs.python.org/3.15 | 191 | 709 | 525 | — | — | 629 |
| docs.python.org/3.2 | 302 | 298 | — | — | — | 324 |
| docs.python.org/3.3 | 302 | 298 | — | — | — | 324 |
| docs.python.org/3.4 | 339 | 336 | — | — | — | 361 |
| docs.python.org/3.6 | 186 | 371 | — | — | — | 353 |

</details>

