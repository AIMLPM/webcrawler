# Retrieval Quality Comparison

Does each tool's output produce embeddings that answer real questions?
This benchmark chunks each tool's crawl output, embeds it with
`text-embedding-3-small`, and runs the same retrieval queries against each.

**What matters:** Hit rate — does the correct source page appear in the
top 3 results? Higher is better.

## Summary

| Tool | Queries | Hits | Hit rate | Chunks | Avg chunk words |
|---|---|---|---|---|---|
| markcrawl | 16 | 11 | 69% | 1030 | 130 |
| crawl4ai | 16 | 12 | 75% | 1857 | 105 |
| crawl4ai-raw | 16 | 12 | 75% | 1857 | 105 |
| scrapy+md | 16 | 12 | 75% | 1230 | 133 |
| crawlee | 16 | 11 | 69% | 1279 | 137 |
| colly+md | 16 | 12 | 75% | 1269 | 137 |
| playwright | 16 | 11 | 69% | 1279 | 137 |
| firecrawl | 16 | 5 | 31% | 1623 | 144 |


## quotes-toscrape

| Tool | Hit rate | Hits/3 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|
| markcrawl | 100% | 3/3 | 21 | 15 | 0.6s |
| crawl4ai | 100% | 3/3 | 20 | 15 | 0.5s |
| crawl4ai-raw | 100% | 3/3 | 20 | 15 | 0.4s |
| scrapy+md | 100% | 3/3 | 22 | 15 | 0.4s |
| crawlee | 67% | 2/3 | 24 | 15 | 0.5s |
| colly+md | 100% | 3/3 | 24 | 15 | 0.3s |
| playwright | 67% | 2/3 | 24 | 15 | 0.6s |
| firecrawl | 33% | 1/3 | 18 | 15 | 0.3s |

<details>
<summary>Query-by-query results for quotes-toscrape</summary>

**Q1: What did Albert Einstein say about thinking and the world?**
*(expects URL containing: `quotes.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.421 | quotes.toscrape.com/tag/change/page/1/ | 0.379 | quotes.toscrape.com/ | 0.379 |
| crawl4ai | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.481 | quotes.toscrape.com/tag/change/page/1/ | 0.433 | quotes.toscrape.com/tag/live/page/1/ | 0.362 |
| crawl4ai-raw | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.481 | quotes.toscrape.com/tag/change/page/1/ | 0.435 | quotes.toscrape.com/tag/live/page/1/ | 0.361 |
| scrapy+md | #1 | quotes.toscrape.com/tag/thinking/page/1/ | 0.405 | quotes.toscrape.com/ | 0.367 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 |
| crawlee | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| colly+md | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| playwright | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.351 | quotes.toscrape.com/ | 0.342 | quotes.toscrape.com/tag/thinking/page/1/ | 0.336 |
| firecrawl | #1 | quotes.toscrape.com/author/Albert-Einstein/ | 0.544 | quotes.toscrape.com/author/Albert-Einstein/ | 0.535 | quotes.toscrape.com/author/Albert-Einstein/ | 0.465 |


**Q2: Which quotes are tagged with 'inspirational'?**
*(expects URL containing: `tag/inspirational`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.586 | quotes.toscrape.com/ | 0.578 | quotes.toscrape.com/tag/be-yourself/page/1/ | 0.557 |
| crawl4ai | #2 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.581 | quotes.toscrape.com/tag/live/page/1/ | 0.575 |
| crawl4ai-raw | #2 | quotes.toscrape.com/ | 0.582 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.580 | quotes.toscrape.com/tag/live/page/1/ | 0.575 |
| scrapy+md | #1 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.584 | quotes.toscrape.com/ | 0.567 | quotes.toscrape.com/tag/miracles/page/1/ | 0.566 |
| crawlee | miss | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/tag/live/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| colly+md | #2 | quotes.toscrape.com/tag/miracles/page/1/ | 0.586 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| playwright | miss | quotes.toscrape.com/tag/miracles/page/1/ | 0.588 | quotes.toscrape.com/tag/live/page/1/ | 0.586 | quotes.toscrape.com/ | 0.586 |
| firecrawl | miss | quotes.toscrape.com | 0.576 | quotes.toscrape.com/page/299/ | 0.535 | quotes.toscrape.com/page/539/ | 0.535 |


**Q3: What did Jane Austen say about novels and reading?**
*(expects URL containing: `author/Jane-Austen`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | quotes.toscrape.com/author/Jane-Austen | 0.554 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.379 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| crawl4ai | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/page/1/ | 0.322 |
| crawl4ai-raw | #1 | quotes.toscrape.com/author/Jane-Austen | 0.547 | quotes.toscrape.com/author/J-K-Rowling | 0.365 | quotes.toscrape.com/tag/humor/page/1/ | 0.322 |
| scrapy+md | #1 | quotes.toscrape.com/author/Jane-Austen/ | 0.532 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/tag/humor/page/1/ | 0.334 |
| crawlee | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| colly+md | #1 | quotes.toscrape.com/author/Jane-Austen/ | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling/ | 0.333 |
| playwright | #1 | quotes.toscrape.com/author/Jane-Austen | 0.473 | quotes.toscrape.com/tag/inspirational/page/1/ | 0.372 | quotes.toscrape.com/author/J-K-Rowling | 0.333 |
| firecrawl | miss | quotes.toscrape.com | 0.293 | quotes.toscrape.com/tableful/tag/fairy-tales/page/ | 0.280 | quotes.toscrape.com/tableful/tag/good/page/1/ | 0.249 |


</details>

## books-toscrape

| Tool | Hit rate | Hits/3 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|
| markcrawl | 100% | 3/3 | 114 | 60 | 0.6s |
| crawl4ai | 100% | 3/3 | 675 | 60 | 4.3s |
| crawl4ai-raw | 100% | 3/3 | 675 | 60 | 5.9s |
| scrapy+md | 100% | 3/3 | 127 | 60 | 1.1s |
| crawlee | 100% | 3/3 | 131 | 60 | 1.4s |
| colly+md | 100% | 3/3 | 131 | 60 | 1.0s |
| playwright | 100% | 3/3 | 131 | 60 | 1.4s |
| firecrawl | 67% | 2/3 | 538 | 60 | 3.3s |

<details>
<summary>Query-by-query results for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/catalogue/category/books_1/inde | 0.488 | books.toscrape.com/catalogue/category/books/food-a | 0.485 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/novels | 0.491 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/childr | 0.497 | books.toscrape.com/catalogue/category/books/contem | 0.492 | books.toscrape.com/catalogue/category/books/novels | 0.491 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/defaul | 0.512 | books.toscrape.com/ | 0.491 | books.toscrape.com/catalogue/category/books_1/inde | 0.489 |
| firecrawl | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.496 | books.toscrape.com | 0.495 | books.toscrape.com/catalogue/category/books_1/inde | 0.480 |


**Q2: What mystery and thriller books are in the catalog?**
*(expects URL containing: `mystery`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/sharp-objects_997/ind | 0.468 |
| crawl4ai | #2 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.503 |
| crawl4ai-raw | #2 | books.toscrape.com/catalogue/category/books/thrill | 0.520 | books.toscrape.com/catalogue/category/books/myster | 0.513 | books.toscrape.com/catalogue/category/books/horror | 0.504 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/ | 0.479 | books.toscrape.com/catalogue/category/books/sequen | 0.460 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| playwright | #1 | books.toscrape.com/catalogue/category/books/myster | 0.514 | books.toscrape.com/catalogue/category/books/myster | 0.495 | books.toscrape.com/catalogue/category/books/thrill | 0.483 |
| firecrawl | miss | books.toscrape.com/catalogue/in-her-wake_980/index | 0.524 | books.toscrape.com/catalogue/far-from-true-promise | 0.489 | books.toscrape.com/catalogue/the-murder-of-roger-a | 0.464 |


**Q3: What is the rating of the most expensive book?**
*(expects URL containing: `books.toscrape.com`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | books.toscrape.com/catalogue/category/books/young- | 0.424 | books.toscrape.com/catalogue/category/books/defaul | 0.417 | books.toscrape.com/catalogue/category/books/scienc | 0.414 |
| crawl4ai | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/horror | 0.423 | books.toscrape.com/catalogue/category/books_1/inde | 0.410 |
| crawl4ai-raw | #1 | books.toscrape.com/catalogue/category/books/myster | 0.434 | books.toscrape.com/catalogue/category/books/horror | 0.423 | books.toscrape.com/catalogue/category/books_1/inde | 0.410 |
| scrapy+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| crawlee | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| colly+md | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| playwright | #1 | books.toscrape.com/catalogue/category/books_1/inde | 0.427 | books.toscrape.com/catalogue/category/books/scienc | 0.421 | books.toscrape.com/catalogue/category/books/young- | 0.418 |
| firecrawl | #1 | books.toscrape.com/catalogue/the-giver-the-giver-q | 0.425 | books.toscrape.com/catalogue/ways-of-seeing_94/ind | 0.414 | books.toscrape.com/catalogue/the-bhagavad-gita_60/ | 0.412 |


</details>

## fastapi-docs

| Tool | Hit rate | Hits/5 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|
| markcrawl | 60% | 3/5 | 736 | 25 | 7.6s |
| crawl4ai | 60% | 3/5 | 863 | 25 | 7.7s |
| crawl4ai-raw | 60% | 3/5 | 863 | 25 | 5.1s |
| scrapy+md | 60% | 3/5 | 801 | 25 | 14.1s |
| crawlee | 60% | 3/5 | 821 | 25 | 7.3s |
| colly+md | 60% | 3/5 | 821 | 25 | 41.3s |
| playwright | 60% | 3/5 | 821 | 25 | 6.5s |
| firecrawl | 20% | 1/5 | 348 | 25 | 2.8s |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/ | 0.565 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.598 | fastapi.tiangolo.com/tutorial/security/ | 0.593 | fastapi.tiangolo.com/tutorial/security/ | 0.570 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 | fastapi.tiangolo.com/tutorial/security/ | 0.570 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| firecrawl | miss | fastapi.tiangolo.com/alternatives/ | 0.533 | fastapi.tiangolo.com/features/ | 0.514 | fastapi.tiangolo.com/features/ | 0.511 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| playwright | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.532 | fastapi.tiangolo.com/advanced/stream-data/ | 0.527 |
| firecrawl | #1 | fastapi.tiangolo.com/es/tutorial/path-operation-co | 0.558 | fastapi.tiangolo.com/alternatives/ | 0.548 | fastapi.tiangolo.com/features/ | 0.497 |


**Q3: How do I define query parameters in FastAPI?**
*(expects URL containing: `query-parameter`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| crawl4ai | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| scrapy+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/reference/fastapi/ | 0.529 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| crawlee | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| colly+md | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/reference/fastapi/ | 0.529 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| playwright | miss | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/reference/fastapi/ | 0.533 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.524 |
| firecrawl | miss | fastapi.tiangolo.com/de/reference/parameters/ | 0.647 | fastapi.tiangolo.com/alternatives/ | 0.561 | fastapi.tiangolo.com/de/reference/parameters/ | 0.555 |


**Q4: How do I handle file uploads in FastAPI?**
*(expects URL containing: `request-files`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/ | 0.484 |
| crawl4ai | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.523 |
| crawl4ai-raw | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.523 |
| scrapy+md | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/additional-responses | 0.482 |
| crawlee | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.497 |
| colly+md | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.499 |
| playwright | miss | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.545 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.497 |
| firecrawl | miss | fastapi.tiangolo.com/de/reference/parameters/ | 0.563 | fastapi.tiangolo.com/alternatives/ | 0.560 | fastapi.tiangolo.com/features/ | 0.515 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/reference/openapi/models/ | 0.539 | fastapi.tiangolo.com/reference/openapi/models/ | 0.529 |
| crawl4ai | #3 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/ | 0.548 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.548 |
| crawl4ai-raw | #3 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/ | 0.548 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.548 |
| scrapy+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.555 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.534 |
| crawlee | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.545 | fastapi.tiangolo.com/ | 0.532 |
| colly+md | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.555 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.554 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.541 |
| playwright | #2 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.545 | fastapi.tiangolo.com/ | 0.532 |
| firecrawl | miss | fastapi.tiangolo.com/de/reference/parameters/ | 0.603 | fastapi.tiangolo.com/features/ | 0.558 | fastapi.tiangolo.com/alternatives/ | 0.555 |


</details>

## python-docs

| Tool | Hit rate | Hits/5 | Chunks | Pages | Embed time |
|---|---|---|---|---|---|
| markcrawl | 40% | 2/5 | 159 | 20 | 1.4s |
| crawl4ai | 60% | 3/5 | 299 | 20 | 5.1s |
| crawl4ai-raw | 60% | 3/5 | 299 | 20 | 2.4s |
| scrapy+md | 60% | 3/5 | 280 | 16 | 1.7s |
| crawlee | 60% | 3/5 | 303 | 20 | 2.4s |
| colly+md | 60% | 3/5 | 293 | 20 | 2.9s |
| playwright | 60% | 3/5 | 303 | 20 | 10.4s |
| firecrawl | 20% | 1/5 | 719 | 20 | 6.7s |

<details>
<summary>Query-by-query results for python-docs</summary>

**Q1: What new features were added in Python 3.10?**
*(expects URL containing: `whatsnew/3.10`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/contents.html | 0.636 | docs.python.org/3.10/ | 0.596 | docs.python.org/3.10/contents.html | 0.588 |
| crawl4ai | #1 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/contents.html | 0.649 |
| crawl4ai-raw | #1 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/whatsnew/index.html | 0.704 | docs.python.org/3.10/contents.html | 0.649 |
| scrapy+md | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| crawlee | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| colly+md | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| playwright | #1 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/whatsnew/index.html | 0.678 | docs.python.org/3.10/contents.html | 0.638 |
| firecrawl | miss | docs.python.org/3/library/ | 0.481 | docs.python.org/3/library/stdtypes.html | 0.451 | docs.python.org/3/library/ | 0.448 |


**Q2: What does the term 'decorator' mean in Python?**
*(expects URL containing: `glossary`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/3.10/glossary.html | 0.585 | docs.python.org/3.10/glossary.html | 0.367 | docs.python.org/3.10/glossary.html | 0.364 |
| crawl4ai | #1 | docs.python.org/3.10/glossary.html | 0.541 | docs.python.org/3.10/glossary.html | 0.397 | docs.python.org/3.10/glossary.html | 0.371 |
| crawl4ai-raw | #1 | docs.python.org/3.10/glossary.html | 0.541 | docs.python.org/3.10/glossary.html | 0.397 | docs.python.org/3.10/glossary.html | 0.371 |
| scrapy+md | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.376 | docs.python.org/3.10/glossary.html | 0.367 |
| crawlee | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.378 | docs.python.org/3.10/glossary.html | 0.367 |
| colly+md | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.376 | docs.python.org/3.10/glossary.html | 0.367 |
| playwright | #1 | docs.python.org/3.10/glossary.html | 0.587 | docs.python.org/3.10/glossary.html | 0.378 | docs.python.org/3.10/glossary.html | 0.367 |
| firecrawl | miss | docs.python.org/3/library/stdtypes.html | 0.434 | docs.python.org/3/library/functions.html | 0.351 | docs.python.org/3/library/multiprocessing.html | 0.330 |


**Q3: What modules are in the Python standard library?**
*(expects URL containing: `library/index`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/tutorial/index.html | 0.544 | docs.python.org/3.10/py-modindex.html | 0.534 | docs.python.org/3.10/py-modindex.html | 0.520 |
| crawl4ai | miss | docs.python.org/license.html | 0.555 | docs.python.org/license.html | 0.555 | docs.python.org/3.10/contents.html | 0.554 |
| crawl4ai-raw | miss | docs.python.org/license.html | 0.555 | docs.python.org/license.html | 0.555 | docs.python.org/3.10/contents.html | 0.554 |
| scrapy+md | miss | docs.python.org/3/license.html | 0.545 | docs.python.org/3/license.html | 0.545 | docs.python.org/3.10/tutorial/index.html | 0.544 |
| crawlee | miss | docs.python.org/license.html | 0.545 | docs.python.org/license.html | 0.545 | docs.python.org/3.10/tutorial/index.html | 0.544 |
| colly+md | miss | docs.python.org/3/license.html | 0.545 | docs.python.org/3/license.html | 0.545 | docs.python.org/3.10/tutorial/index.html | 0.544 |
| playwright | miss | docs.python.org/license.html | 0.545 | docs.python.org/license.html | 0.545 | docs.python.org/3.10/tutorial/index.html | 0.544 |
| firecrawl | #1 | docs.python.org/3/library/ | 0.690 | docs.python.org/3/library/intro.html | 0.618 | docs.python.org/3/library/ | 0.598 |


**Q4: How do I report a bug in Python?**
*(expects URL containing: `bugs`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | docs.python.org/bugs.html | 0.609 | docs.python.org/bugs.html | 0.585 | docs.python.org/bugs.html | 0.561 |
| crawl4ai | #1 | docs.python.org/bugs.html | 0.668 | docs.python.org/bugs.html | 0.659 | docs.python.org/bugs.html | 0.652 |
| crawl4ai-raw | #1 | docs.python.org/bugs.html | 0.668 | docs.python.org/bugs.html | 0.659 | docs.python.org/bugs.html | 0.652 |
| scrapy+md | #1 | docs.python.org/3/bugs.html | 0.609 | docs.python.org/3.10/using/index.html | 0.588 | docs.python.org/3.10/using/index.html | 0.588 |
| crawlee | #1 | docs.python.org/bugs.html | 0.641 | docs.python.org/bugs.html | 0.640 | docs.python.org/bugs.html | 0.609 |
| colly+md | #1 | docs.python.org/3/bugs.html | 0.609 | docs.python.org/3.10/using/index.html | 0.588 | docs.python.org/3.10/using/index.html | 0.588 |
| playwright | #1 | docs.python.org/bugs.html | 0.641 | docs.python.org/bugs.html | 0.640 | docs.python.org/bugs.html | 0.609 |
| firecrawl | miss | docs.python.org/3/library/intro.html | 0.573 | docs.python.org/3/library/ | 0.565 | docs.python.org/3/library/exceptions.html | 0.544 |


**Q5: What is structural pattern matching in Python?**
*(expects URL containing: `whatsnew/3.10`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | miss | docs.python.org/3.10/py-modindex.html | 0.360 | docs.python.org/3.10/contents.html | 0.339 | docs.python.org/3.10/glossary.html | 0.330 |
| crawl4ai | miss | docs.python.org/3.10/glossary.html | 0.383 | docs.python.org/3.10/glossary.html | 0.363 | docs.python.org/3.10/contents.html | 0.350 |
| crawl4ai-raw | miss | docs.python.org/3.10/glossary.html | 0.383 | docs.python.org/3.10/glossary.html | 0.363 | docs.python.org/3.10/contents.html | 0.350 |
| scrapy+md | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| crawlee | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| colly+md | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| playwright | miss | docs.python.org/3.10/py-modindex.html | 0.353 | docs.python.org/3.10/glossary.html | 0.328 | docs.python.org/3.10/contents.html | 0.326 |
| firecrawl | miss | docs.python.org/3/library/struct.html | 0.390 | docs.python.org/3/library/struct.html | 0.339 | docs.python.org/3/library/ctypes.html | 0.325 |


</details>

## Methodology

- **Embedding model:** `text-embedding-3-small` (1536 dimensions)
- **Chunking:** Markdown-aware, 400 word max, 50 word overlap
- **Retrieval:** Cosine similarity, top-3 results checked for expected URL
- **Same chunking and embedding** for all tools — only extraction quality varies
- **No fine-tuning or tool-specific optimization** — identical pipeline for all

