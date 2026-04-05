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
| markcrawl | 228 | 2 | 2.6 | 0.0 | 87% | 87% |
| crawl4ai | 237 | 2 | 2.6 | 0.0 | 87% | 87% |
| scrapy+md | 237 | 2 | 2.6 | 0.0 | 87% | 87% |
| crawlee | 261 | 3 | 2.6 | 0.0 | 87% | 87% |
| colly+md | 261 | 3 | 2.6 | 0.0 | 87% | 87% |
| playwright | 261 | 3 | 2.6 | 0.0 | 87% | 87% |
| firecrawl | — | — | — | — | — | — |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright | firecrawl |
|---|---|---|---|---|---|---|---|
| quotes.toscrape.com | 271 | 282 | 282 | 285 | 285 | 285 | — |
| quotes.toscrape.com/author/Andre-Gide | 173 | 181 | 181 | 184 | 184 | 184 | — |
| quotes.toscrape.com/author/Jane-Austen | 333 | 341 | 341 | 344 | 344 | 344 | — |
| quotes.toscrape.com/author/Steve-Martin | 139 | 147 | 147 | 150 | 150 | 150 | — |
| quotes.toscrape.com/author/Thomas-A-Edison | 201 | 209 | 209 | 212 | 212 | 212 | — |
| quotes.toscrape.com/page/2 | 600 | 614 | 614 | 725 | 725 | 725 | — |
| quotes.toscrape.com/tag/be-yourself/page/1 | 46 | 54 | 54 | 57 | 57 | 57 | — |
| quotes.toscrape.com/tag/friendship | 158 | 166 | 166 | 169 | 169 | 169 | — |
| quotes.toscrape.com/tag/inspirational/page/1 | 484 | 495 | 495 | 606 | 606 | 606 | — |
| quotes.toscrape.com/tag/life/page/1 | 498 | 509 | 509 | 620 | 620 | 620 | — |
| quotes.toscrape.com/tag/live/page/1 | 59 | 67 | 67 | 70 | 70 | 70 | — |
| quotes.toscrape.com/tag/paraphrased/page/1 | 69 | 77 | 77 | 80 | 80 | 80 | — |
| quotes.toscrape.com/tag/reading | 247 | 255 | 255 | 258 | 258 | 258 | — |
| quotes.toscrape.com/tag/thinking/page/1 | 85 | 93 | 93 | 96 | 96 | 96 | — |
| quotes.toscrape.com/tag/world/page/1 | 53 | 61 | 61 | 64 | 64 | 64 | — |

</details>

## books-toscrape

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 291 | 0 | 1.9 | 0.0 | 95% | 100% |
| crawl4ai | 491 | 0 | 10.5 | 0.0 | 81% | 100% |
| scrapy+md | 389 | 0 | 1.9 | 0.0 | 100% | 100% |
| crawlee | 418 | 11 | 1.9 | 0.0 | 100% | 100% |
| colly+md | 418 | 11 | 1.9 | 0.0 | 3% | 100% |
| playwright | 418 | 11 | 1.9 | 0.0 | 100% | 100% |
| firecrawl | — | — | — | — | — | — |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright | firecrawl |
|---|---|---|---|---|---|---|---|
| books.toscrape.com | 397 | 702 | 531 | 539 | 539 | 539 | — |
| books.toscrape.com/catalogue/a-light-in-the-attic/1000/index | — | — | — | — | 295 | — | — |
| books.toscrape.com/catalogue/a-light-in-the-attic_1000/index | 269 | 276 | 284 | 295 | — | 295 | — |
| books.toscrape.com/catalogue/category/books/1/index.html | — | — | — | — | 644 | — | — |
| books.toscrape.com/catalogue/category/books/academic/40/inde | — | — | — | — | 192 | — | — |
| books.toscrape.com/catalogue/category/books/academic_40/inde | 51 | 282 | 185 | 192 | — | 192 | — |
| books.toscrape.com/catalogue/category/books/add-a-comment/18 | — | — | — | — | 567 | — | — |
| books.toscrape.com/catalogue/category/books/add-a-comment_18 | 424 | 745 | 558 | 567 | — | 567 | — |
| books.toscrape.com/catalogue/category/books/adult-fiction/29 | — | — | — | — | 195 | — | — |
| books.toscrape.com/catalogue/category/books/adult-fiction_29 | 53 | 284 | 187 | 195 | — | 195 | — |
| books.toscrape.com/catalogue/category/books/art/25/index.htm | — | — | — | — | 310 | — | — |
| books.toscrape.com/catalogue/category/books/art_25/index.htm | 169 | 422 | 303 | 310 | — | 310 | — |
| books.toscrape.com/catalogue/category/books/autobiography/27 | — | — | — | — | 310 | — | — |
| books.toscrape.com/catalogue/category/books/autobiography_27 | 169 | 412 | 303 | 310 | — | 310 | — |
| books.toscrape.com/catalogue/category/books/biography/36/ind | — | — | — | — | 286 | — | — |
| books.toscrape.com/catalogue/category/books/biography_36/ind | 145 | 410 | 279 | 286 | — | 286 | — |
| books.toscrape.com/catalogue/category/books/business/35/inde | — | — | — | — | 437 | — | — |
| books.toscrape.com/catalogue/category/books/business_35/inde | 296 | 612 | 430 | 437 | — | 437 | — |
| books.toscrape.com/catalogue/category/books/christian-fictio | — | — | — | — | 390 | — | — |
| books.toscrape.com/catalogue/category/books/christian-fictio | 140 | 388 | 274 | 390 | — | 390 | — |
| books.toscrape.com/catalogue/category/books/christian/43/ind | — | — | — | — | 345 | — | — |
| books.toscrape.com/catalogue/category/books/christian_43/ind | 96 | 342 | 230 | 345 | — | 345 | — |
| books.toscrape.com/catalogue/category/books/contemporary/38/ | — | — | — | — | 333 | — | — |
| books.toscrape.com/catalogue/category/books/contemporary_38/ | 84 | 320 | 218 | 333 | — | 333 | — |
| books.toscrape.com/catalogue/category/books/crime/51/index.h | — | — | — | — | 307 | — | — |
| books.toscrape.com/catalogue/category/books/crime_51/index.h | 58 | 296 | 192 | 307 | — | 307 | — |
| books.toscrape.com/catalogue/category/books/cultural/49/inde | — | — | — | — | 187 | — | — |
| books.toscrape.com/catalogue/category/books/cultural_49/inde | 46 | 274 | 180 | 187 | — | 187 | — |
| books.toscrape.com/catalogue/category/books/erotica/50/index | — | — | — | — | 185 | — | — |
| books.toscrape.com/catalogue/category/books/erotica_50/index | 44 | 271 | 178 | 185 | — | 185 | — |
| books.toscrape.com/catalogue/category/books/fiction/10/index | — | — | — | — | 614 | — | — |
| books.toscrape.com/catalogue/category/books/fiction_10/index | 365 | — | 499 | 614 | — | 614 | — |
| books.toscrape.com/catalogue/category/books/food-and-drink/3 | — | — | — | — | 691 | — | — |
| books.toscrape.com/catalogue/category/books/food-and-drink_3 | 548 | 978 | 682 | 691 | — | 691 | — |
| books.toscrape.com/catalogue/category/books/historical-ficti | — | — | — | — | 533 | — | — |
| books.toscrape.com/catalogue/category/books/historical-ficti | 391 | 681 | 525 | 533 | — | 533 | — |
| books.toscrape.com/catalogue/category/books/historical/42/in | — | — | — | — | 216 | — | — |
| books.toscrape.com/catalogue/category/books/historical_42/in | 75 | 315 | 209 | 216 | — | 216 | — |
| books.toscrape.com/catalogue/category/books/history/32/index | — | — | — | — | 696 | — | — |
| books.toscrape.com/catalogue/category/books/history_32/index | 447 | 822 | 581 | 696 | — | 696 | — |
| books.toscrape.com/catalogue/category/books/horror/31/index. | — | — | — | — | 416 | — | — |
| books.toscrape.com/catalogue/category/books/horror_31/index. | 275 | 524 | 409 | 416 | — | 416 | — |
| books.toscrape.com/catalogue/category/books/humor/30/index.h | — | — | — | — | 488 | — | — |
| books.toscrape.com/catalogue/category/books/humor_30/index.h | 239 | 529 | 373 | 488 | — | 488 | — |
| books.toscrape.com/catalogue/category/books/music/14/index.h | — | — | — | — | 445 | — | — |
| books.toscrape.com/catalogue/category/books/music_14/index.h | 304 | 616 | 438 | 445 | — | 445 | — |
| books.toscrape.com/catalogue/category/books/mystery/3/index. | — | — | — | — | 548 | — | — |
| books.toscrape.com/catalogue/category/books/mystery_3/index. | 407 | 710 | 541 | 548 | — | 548 | — |
| books.toscrape.com/catalogue/category/books/paranormal/24/in | — | — | — | — | 193 | — | — |
| books.toscrape.com/catalogue/category/books/paranormal_24/in | 52 | 284 | 186 | 193 | — | 193 | — |
| books.toscrape.com/catalogue/category/books/parenting/28/ind | — | — | — | — | 194 | — | — |
| books.toscrape.com/catalogue/category/books/parenting_28/ind | 53 | 286 | 187 | 194 | — | 194 | — |
| books.toscrape.com/catalogue/category/books/poetry/23/index. | — | — | — | — | 496 | — | — |
| books.toscrape.com/catalogue/category/books/poetry_23/index. | 355 | 642 | 489 | 496 | — | 496 | — |
| books.toscrape.com/catalogue/category/books/politics/48/inde | — | — | — | — | 235 | — | — |
| books.toscrape.com/catalogue/category/books/politics_48/inde | 94 | 340 | 228 | 235 | — | 235 | — |
| books.toscrape.com/catalogue/category/books/psychology/26/in | — | — | — | — | 325 | — | — |
| books.toscrape.com/catalogue/category/books/psychology_26/in | 184 | 460 | 318 | 325 | — | 325 | — |
| books.toscrape.com/catalogue/category/books/religion/12/inde | — | — | — | — | 321 | — | — |
| books.toscrape.com/catalogue/category/books/religion_12/inde | 180 | 453 | 314 | 321 | — | 321 | — |
| books.toscrape.com/catalogue/category/books/romance/8/index. | — | — | — | — | 553 | — | — |
| books.toscrape.com/catalogue/category/books/romance_8/index. | 412 | 716 | 546 | 553 | — | 553 | — |
| books.toscrape.com/catalogue/category/books/science-fiction/ | — | — | — | — | 464 | — | — |
| books.toscrape.com/catalogue/category/books/science-fiction_ | 322 | 615 | 456 | 464 | — | 464 | — |
| books.toscrape.com/catalogue/category/books/science/22/index | — | — | — | — | 491 | — | — |
| books.toscrape.com/catalogue/category/books/science_22/index | 350 | 690 | 484 | 491 | — | 491 | — |
| books.toscrape.com/catalogue/category/books/self-help/41/ind | — | — | — | — | 294 | — | — |
| books.toscrape.com/catalogue/category/books/self-help_41/ind | 152 | 422 | 286 | 294 | — | 294 | — |
| books.toscrape.com/catalogue/category/books/sequential-art/5 | — | — | — | — | 583 | — | — |
| books.toscrape.com/catalogue/category/books/sequential-art_5 | 441 | 774 | 575 | 583 | — | 583 | — |
| books.toscrape.com/catalogue/category/books/short-stories/45 | — | — | — | — | 188 | — | — |
| books.toscrape.com/catalogue/category/books/short-stories_45 | 46 | 273 | 180 | 188 | — | 188 | — |
| books.toscrape.com/catalogue/category/books/spirituality/39/ | — | — | — | — | 312 | — | — |
| books.toscrape.com/catalogue/category/books/spirituality_39/ | 171 | 447 | 305 | 312 | — | 312 | — |
| books.toscrape.com/catalogue/category/books/sports-and-games | — | — | — | — | 280 | — | — |
| books.toscrape.com/catalogue/category/books/sports-and-games | 137 | 391 | 271 | 280 | — | 280 | — |
| books.toscrape.com/catalogue/category/books/thriller/37/inde | — | — | — | — | 352 | — | — |
| books.toscrape.com/catalogue/category/books/thriller_37/inde | 211 | 465 | 345 | 352 | — | 352 | — |
| books.toscrape.com/catalogue/category/books/travel/2/index.h | — | — | — | — | 399 | — | — |
| books.toscrape.com/catalogue/category/books/travel_2/index.h | 258 | 550 | 392 | 399 | — | 399 | — |
| books.toscrape.com/catalogue/category/books/womens-fiction/9 | — | — | — | — | 472 | — | — |
| books.toscrape.com/catalogue/category/books/womens-fiction_9 | 330 | 614 | 464 | 472 | — | 472 | — |
| books.toscrape.com/catalogue/category/books_1/index.html | 395 | 700 | 529 | 644 | — | 644 | — |
| books.toscrape.com/catalogue/its-only-the-himalayas/981/inde | — | — | — | — | 473 | — | — |
| books.toscrape.com/catalogue/its-only-the-himalayas_981/inde | 448 | 480 | 463 | 473 | — | 473 | — |
| books.toscrape.com/catalogue/libertarianism-for-beginners/98 | — | — | — | — | 435 | — | — |
| books.toscrape.com/catalogue/libertarianism-for-beginners_98 | 411 | 442 | 426 | 435 | — | 435 | — |
| books.toscrape.com/catalogue/mesaerion-the-best-science-fict | — | — | — | — | 528 | — | — |
| books.toscrape.com/catalogue/mesaerion-the-best-science-fict | 500 | 530 | 515 | 528 | — | 528 | — |
| books.toscrape.com/catalogue/olio/984/index.html | — | — | — | — | 484 | — | — |
| books.toscrape.com/catalogue/olio_984/index.html | 462 | 491 | 477 | 484 | — | 484 | — |
| books.toscrape.com/catalogue/our-band-could-be-your-life-sce | — | — | — | — | 422 | — | — |
| books.toscrape.com/catalogue/our-band-could-be-your-life-sce | 388 | 419 | 403 | 422 | — | 422 | — |
| books.toscrape.com/catalogue/page-2.html | 413 | 726 | 547 | 555 | 555 | 555 | — |
| books.toscrape.com/catalogue/rip-it-up-and-start-again/986/i | — | — | — | — | 398 | — | — |
| books.toscrape.com/catalogue/rip-it-up-and-start-again_986/i | 371 | 407 | 386 | 398 | — | 398 | — |
| books.toscrape.com/catalogue/sapiens-a-brief-history-of-huma | — | — | — | — | 605 | — | — |
| books.toscrape.com/catalogue/sapiens-a-brief-history-of-huma | 470 | 481 | 485 | 605 | — | 605 | — |
| books.toscrape.com/catalogue/scott-pilgrims-precious-little- | — | — | — | — | 412 | — | — |
| books.toscrape.com/catalogue/scott-pilgrims-precious-little- | 383 | 428 | 398 | 412 | — | 412 | — |
| books.toscrape.com/catalogue/set-me-free/988/index.html | — | — | — | — | 389 | — | — |
| books.toscrape.com/catalogue/set-me-free_988/index.html | 365 | 411 | 380 | 389 | — | 389 | — |
| books.toscrape.com/catalogue/shakespeares-sonnets/989/index. | — | — | — | — | 398 | — | — |
| books.toscrape.com/catalogue/shakespeares-sonnets_989/index. | 375 | 421 | 390 | 398 | — | 398 | — |
| books.toscrape.com/catalogue/soumission/998/index.html | — | — | — | — | 319 | — | — |
| books.toscrape.com/catalogue/soumission_998/index.html | 297 | 304 | 312 | 319 | — | 319 | — |
| books.toscrape.com/catalogue/starving-hearts-triangular-trad | — | — | — | — | 463 | — | — |
| books.toscrape.com/catalogue/starving-hearts-triangular-trad | 436 | 486 | 451 | 463 | — | 463 | — |
| books.toscrape.com/catalogue/the-boys-in-the-boat-nine-ameri | — | — | — | — | 615 | — | — |
| books.toscrape.com/catalogue/the-boys-in-the-boat-nine-ameri | 576 | 620 | 591 | 615 | — | 615 | — |
| books.toscrape.com/catalogue/the-coming-woman-a-novel-based- | — | — | — | — | 825 | — | — |
| books.toscrape.com/catalogue/the-coming-woman-a-novel-based- | 789 | 818 | 804 | 825 | — | 825 | — |
| books.toscrape.com/catalogue/the-dirty-little-secrets-of-get | — | — | — | — | 627 | — | — |
| books.toscrape.com/catalogue/the-dirty-little-secrets-of-get | 489 | 508 | 504 | 627 | — | 627 | — |
| books.toscrape.com/catalogue/the-requiem-red/995/index.html | — | — | — | — | 374 | — | — |
| books.toscrape.com/catalogue/the-requiem-red_995/index.html | 350 | 362 | 365 | 374 | — | 374 | — |
| books.toscrape.com/catalogue/tipping-the-velvet/999/index.ht | — | — | — | — | 422 | — | — |
| books.toscrape.com/catalogue/tipping-the-velvet_999/index.ht | 290 | 298 | 305 | 422 | — | 422 | — |

</details>

## fastapi-docs

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 3835 | 29 | 33.1 | 28.7 | 100% | 100% |
| crawl4ai | 5424 | 29 | 32.8 | 28.7 | 81% | 100% |
| scrapy+md | 4676 | 50 | 33.1 | 28.7 | 100% | 100% |
| crawlee | 4965 | 99 | 32.8 | 28.4 | 100% | 100% |
| colly+md | 5000 | 99 | 33.1 | 28.7 | 100% | 100% |
| playwright | 4975 | 99 | 32.8 | 28.7 | 100% | 100% |
| firecrawl | — | — | — | — | — | — |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright | firecrawl |
|---|---|---|---|---|---|---|---|
| fastapi.tiangolo.com | 2230 | 3979 | 3092 | 3374 | 3404 | 3357 | — |
| fastapi.tiangolo.com/advanced/advanced-dependencies | 2200 | 3660 | 3012 | 3330 | 3335 | 3311 | — |
| fastapi.tiangolo.com/advanced/custom-response | 1987 | 3457 | 2782 | 3095 | 3116 | 3078 | — |
| fastapi.tiangolo.com/advanced/stream-data | 2723 | 4109 | 3465 | 3785 | 3788 | 3768 | — |
| fastapi.tiangolo.com/advanced/testing-events | 263 | 1562 | 929 | 1276 | 1261 | 1259 | — |
| fastapi.tiangolo.com/advanced/testing-websockets | 117 | 1414 | 783 | 1123 | 1108 | 1106 | — |
| fastapi.tiangolo.com/async | 3651 | 5198 | 4478 | 4780 | 4805 | 4763 | — |
| fastapi.tiangolo.com/deployment/docker | 4157 | 5537 | 5156 | 5068 | 5488 | 5405 | — |
| fastapi.tiangolo.com/fastapi-people | 1434 | 3347 | 2230 | 2536 | 2551 | 2517 | — |
| fastapi.tiangolo.com/help-fastapi | 1955 | 3519 | 2842 | 3139 | 3172 | 3122 | — |
| fastapi.tiangolo.com/how-to | 97 | 1400 | 764 | 1110 | 1095 | 1093 | — |
| fastapi.tiangolo.com/ja | 1164 | 2734 | 1818 | 2073 | 2103 | 2056 | — |
| fastapi.tiangolo.com/reference/apirouter | 24889 | 26603 | 25651 | 25971 | 25976 | 25952 | — |
| fastapi.tiangolo.com/reference/openapi/models | 3708 | 7394 | 5672 | 6009 | 5992 | 5990 | — |
| fastapi.tiangolo.com/reference/parameters | 12456 | 13849 | 13154 | 13491 | 13474 | 13472 | — |
| fastapi.tiangolo.com/reference/request | 680 | 2122 | 1446 | 1782 | 1767 | 1765 | — |
| fastapi.tiangolo.com/tutorial/cookie-params | 365 | 1686 | 1058 | 1388 | 1379 | 1371 | — |
| fastapi.tiangolo.com/tutorial/dependencies/dependencies-with | 2580 | 4064 | 3414 | 3479 | 3735 | 3707 | — |
| fastapi.tiangolo.com/tutorial/query-params-str-validations | 4071 | 5682 | 4987 | 5285 | 5316 | 5266 | — |
| fastapi.tiangolo.com/tutorial/request-forms-and-files | 388 | 1721 | 1091 | 1424 | 1415 | 1407 | — |
| fastapi.tiangolo.com/tutorial/response-model | 3150 | 4716 | 4040 | 4342 | 4367 | 4327 | — |
| fastapi.tiangolo.com/tutorial/security/oauth2-jwt | 4418 | 5893 | 5212 | 5550 | 5549 | 5533 | — |
| fastapi.tiangolo.com/tutorial/security/simple-oauth2 | 3596 | 5078 | 4405 | 4726 | 4741 | 4707 | — |
| fastapi.tiangolo.com/tutorial/sql-databases | 10591 | 12262 | 11545 | 11842 | 11872 | 11825 | — |
| fastapi.tiangolo.com/virtual-environments | 3009 | 4623 | 3869 | 4149 | 4191 | 4220 | — |

</details>

## python-docs

| Tool | Avg words | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 2817 | 14 | 9.1 | 4.6 | 93% | 50% |
| crawl4ai | 3268 | 98 | 16.6 | 4.6 | 31% | 50% |
| scrapy+md | 3418 | 91 | 17.7 | 5.1 | 100% | 50% |
| crawlee | 3214 | 98 | 16.6 | 4.6 | 100% | 50% |
| colly+md | 3125 | 98 | 16.6 | 4.6 | 100% | 50% |
| playwright | 3214 | 98 | 16.6 | 4.6 | 100% | 50% |
| firecrawl | — | — | — | — | — | — |

<details>
<summary>Per-page word counts</summary>

| URL | markcrawl | crawl4ai | scrapy+md | crawlee | colly+md | playwright | firecrawl |
|---|---|---|---|---|---|---|---|
| docs.python.org/3.10 | 190 | 711 | 521 | 629 | 533 | 629 | — |
| docs.python.org/3.10/about.html | 180 | 604 | 407 | 520 | 424 | 520 | — |
| docs.python.org/3.10/bugs.html | 666 | 1104 | 913 | 1026 | 930 | 1026 | — |
| docs.python.org/3.10/contents.html | 19401 | 19782 | 19584 | 19697 | 19601 | 19697 | — |
| docs.python.org/3.10/distributing/index.html | 984 | 1481 | 1285 | 1402 | 1306 | 1402 | — |
| docs.python.org/3.10/download.html | 277 | 599 | 404 | 515 | 419 | 515 | — |
| docs.python.org/3.10/glossary.html | 7963 | 8264 | 8186 | 8302 | 8201 | 8302 | — |
| docs.python.org/3.10/library/index.html | 2282 | 2684 | 2487 | 2601 | 2505 | 2601 | — |
| docs.python.org/3.10/reference/index.html | 438 | 844 | 647 | 761 | 665 | 761 | — |
| docs.python.org/3.10/tutorial/index.html | 982 | 1382 | 1185 | 1298 | 1202 | 1298 | — |
| docs.python.org/3.10/whatsnew/3.10.html | 12688 | 13749 | 13627 | 13773 | 13646 | 13773 | — |
| docs.python.org/3.11 | 188 | 711 | 522 | 629 | 534 | 629 | — |
| docs.python.org/3.12 | 191 | 712 | 525 | 632 | 537 | 632 | — |
| docs.python.org/3.13 | 191 | 712 | 525 | 632 | 537 | 632 | — |
| docs.python.org/3.14 | 191 | 712 | 525 | 632 | 537 | 632 | — |
| docs.python.org/3.15 | 191 | 709 | 525 | 629 | 537 | 629 | — |
| docs.python.org/3.4 | 339 | 336 | — | 361 | 360 | 361 | — |
| docs.python.org/3.5 | 186 | 371 | — | 353 | 324 | 353 | — |
| docs.python.org/3/bugs.html | — | — | 980 | — | 997 | — | — |
| docs.python.org/3/license.html | — | — | 8679 | — | 8696 | — | — |
| docs.python.org/bugs.html | 650 | 1096 | — | 1092 | — | 1092 | — |
| docs.python.org/license.html | 8155 | 8801 | — | 8791 | — | 8791 | — |

</details>

