# Retrieval Quality Comparison

<!-- style: v2, 2026-04-07 -->

Does each tool's output produce embeddings that answer real questions?
This benchmark chunks each tool's crawl output, embeds it with
`text-embedding-3-small`, and measures retrieval across four modes:

- **Embedding**: Cosine similarity on OpenAI embeddings
- **BM25**: Keyword search (Okapi BM25)
- **Hybrid**: Embedding + BM25 fused via Reciprocal Rank Fusion
- **Reranked**: Hybrid candidates reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2`

**15 queries** across 1 sites.
Hit rate = correct source page in top-K results. Higher is better.

## Summary: retrieval modes compared

| Tool | Mode | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR |
|---|---|---|---|---|---|---|---|
| markcrawl | embedding | 80% (12/15) ±19% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.843 |
| markcrawl | bm25 | 47% (7/15) ±23% | 80% (12/15) ±19% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.666 |
| markcrawl | hybrid | 80% (12/15) ±19% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.863 |
| markcrawl | reranked | 73% (11/15) ±21% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.819 |
| crawl4ai | embedding | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.947 |
| crawl4ai | bm25 | 33% (5/15) ±22% | 53% (8/15) ±23% | 73% (11/15) ±21% | 80% (12/15) ±19% | 93% (14/15) ±14% | 0.488 |
| crawl4ai | hybrid | 87% (13/15) ±17% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.907 |
| crawl4ai | reranked | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.861 |
| crawl4ai-raw | embedding | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.947 |
| crawl4ai-raw | bm25 | 27% (4/15) ±21% | 53% (8/15) ±23% | 73% (11/15) ±21% | 80% (12/15) ±19% | 93% (14/15) ±14% | 0.443 |
| crawl4ai-raw | hybrid | 87% (13/15) ±17% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.907 |
| crawl4ai-raw | reranked | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.861 |
| scrapy+md | embedding | 80% (12/15) ±19% | 87% (13/15) ±17% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.849 |
| scrapy+md | bm25 | 40% (6/15) ±22% | 73% (11/15) ±21% | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 0.589 |
| scrapy+md | hybrid | 80% (12/15) ±19% | 87% (13/15) ±17% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 0.856 |
| scrapy+md | reranked | 73% (11/15) ±21% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.811 |
| crawlee | embedding | 53% (8/15) ±23% | 60% (9/15) ±22% | 73% (11/15) ±21% | 73% (11/15) ±21% | 80% (12/15) ±19% | 0.587 |
| crawlee | bm25 | 27% (4/15) ±21% | 53% (8/15) ±23% | 60% (9/15) ±22% | 73% (11/15) ±21% | 80% (12/15) ±19% | 0.428 |
| crawlee | hybrid | 60% (9/15) ±22% | 73% (11/15) ±21% | 73% (11/15) ±21% | 80% (12/15) ±19% | 80% (12/15) ±19% | 0.662 |
| crawlee | reranked | 53% (8/15) ±23% | 67% (10/15) ±22% | 73% (11/15) ±21% | 80% (12/15) ±19% | 80% (12/15) ±19% | 0.617 |
| colly+md | embedding | 80% (12/15) ±19% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.844 |
| colly+md | bm25 | 40% (6/15) ±22% | 73% (11/15) ±21% | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 0.589 |
| colly+md | hybrid | 80% (12/15) ±19% | 93% (14/15) ±14% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 0.862 |
| colly+md | reranked | 73% (11/15) ±21% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.799 |
| playwright | embedding | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.917 |
| playwright | bm25 | 40% (6/15) ±22% | 73% (11/15) ±21% | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 0.579 |
| playwright | hybrid | 80% (12/15) ±19% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.880 |
| playwright | reranked | 73% (11/15) ±21% | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.808 |


## Summary: embedding-only (hit rate at multiple K values)

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Avg words |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 80% (12/15) ±19% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.843 | 4254 | 101 |
| crawl4ai | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.947 | 5355 | 139 |
| crawl4ai-raw | 93% (14/15) ±14% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.947 | 5356 | 138 |
| scrapy+md | 80% (12/15) ±19% | 87% (13/15) ±17% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.849 | 4837 | 121 |
| crawlee | 53% (8/15) ±23% | 60% (9/15) ±22% | 73% (11/15) ±21% | 73% (11/15) ±21% | 80% (12/15) ±19% | 0.587 | 1323 | 120 |
| colly+md | 80% (12/15) ±19% | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.844 | 4990 | 130 |
| playwright | 87% (13/15) ±17% | 93% (14/15) ±14% | 100% (15/15) ±10% | 100% (15/15) ±10% | 100% (15/15) ±10% | 0.917 | 4979 | 130 |


## fastapi-docs

| Tool | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Chunks | Pages |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 80% (12/15) | 87% (13/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 0.843 | 4254 | 200 |
| crawl4ai | 93% (14/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.947 | 5355 | 200 |
| crawl4ai-raw | 93% (14/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.947 | 5356 | 200 |
| scrapy+md | 80% (12/15) | 87% (13/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.849 | 4837 | 200 |
| crawlee | 53% (8/15) | 60% (9/15) | 73% (11/15) | 73% (11/15) | 80% (12/15) | 0.587 | 1323 | 65 |
| colly+md | 80% (12/15) | 87% (13/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 0.844 | 4990 | 200 |
| playwright | 87% (13/15) | 93% (14/15) | 100% (15/15) | 100% (15/15) | 100% (15/15) | 0.917 | 4979 | 200 |

<details>
<summary>Query-by-query results for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**
*(expects URL containing: `security`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/tutorial/security/ | 0.565 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.631 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.598 | fastapi.tiangolo.com/tutorial/security/ | 0.593 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.631 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.599 | fastapi.tiangolo.com/tutorial/security/ | 0.593 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/tr/advanced/json-base64-bytes | 0.550 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.604 | fastapi.tiangolo.com/tutorial/security/ | 0.568 | fastapi.tiangolo.com/reference/security/ | 0.555 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.600 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.594 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.550 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.604 | fastapi.tiangolo.com/tutorial/security/simple-oaut | 0.591 | fastapi.tiangolo.com/tutorial/security/ | 0.568 |


**Q2: What is the default response status code in FastAPI?**
*(expects URL containing: `fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.610 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.692 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/advanced/response-change-stat | 0.629 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.692 | fastapi.tiangolo.com/reference/status/ | 0.663 | fastapi.tiangolo.com/advanced/response-change-stat | 0.629 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.613 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.679 | fastapi.tiangolo.com/advanced/custom-response/ | 0.573 | fastapi.tiangolo.com/alternatives/ | 0.547 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.696 | fastapi.tiangolo.com/reference/status/ | 0.614 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.613 |
| playwright | #1 | fastapi.tiangolo.com/advanced/additional-status-co | 0.679 | fastapi.tiangolo.com/reference/status/ | 0.651 | fastapi.tiangolo.com/tutorial/path-operation-confi | 0.602 |


**Q3: How do I define query parameters in the FastAPI reference?**
*(expects URL containing: `reference/fastapi`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #9 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.657 | fastapi.tiangolo.com/tutorial/query-params/ | 0.645 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.631 |
| crawl4ai | #1 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.680 | fastapi.tiangolo.com/reference/parameters/ | 0.671 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.680 | fastapi.tiangolo.com/reference/parameters/ | 0.671 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 |
| scrapy+md | #5 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.636 | fastapi.tiangolo.com/tutorial/query-params/ | 0.617 |
| crawlee | #5 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.634 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.626 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.608 |
| colly+md | #8 | fastapi.tiangolo.com/tutorial/query-params/ | 0.662 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.636 | fastapi.tiangolo.com/tutorial/query-params/ | 0.635 |
| playwright | #2 | fastapi.tiangolo.com/tutorial/query-params/ | 0.649 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.647 | fastapi.tiangolo.com/reference/parameters/ | 0.642 |


**Q4: How does FastAPI handle JSON encoding and base64 bytes?**
*(expects URL containing: `json-base64-bytes`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.599 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/custom-response/ | 0.572 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.654 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.645 | fastapi.tiangolo.com/reference/encoders/ | 0.635 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.654 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.645 | fastapi.tiangolo.com/reference/encoders/ | 0.634 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.572 |
| crawlee | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.560 | fastapi.tiangolo.com/alternatives/ | 0.543 | fastapi.tiangolo.com/tutorial/request-forms/ | 0.527 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.609 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.582 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.572 |
| playwright | #1 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.647 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.606 | fastapi.tiangolo.com/advanced/json-base64-bytes/ | 0.579 |


**Q5: What Python types does FastAPI support for request bodies?**
*(expects URL containing: `body`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.620 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.685 | fastapi.tiangolo.com/tutorial/body/ | 0.622 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.608 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.685 | fastapi.tiangolo.com/tutorial/body/ | 0.622 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.608 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.667 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/reference/openapi/models/ | 0.593 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/advanced/strict-content-type/ | 0.586 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/body/ | 0.667 | fastapi.tiangolo.com/tutorial/body/ | 0.623 | fastapi.tiangolo.com/tr/reference/parameters/ | 0.594 |


**Q6: How do I use OAuth2 with password flow in FastAPI?**
*(expects URL containing: `simple-oauth2`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #5 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/tr/reference/security/ | 0.671 |
| crawl4ai | #5 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.719 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tr/reference/security/ | 0.709 |
| crawl4ai-raw | #5 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.720 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tr/reference/security/ | 0.709 |
| scrapy+md | #5 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/tr/reference/security/ | 0.673 | fastapi.tiangolo.com/reference/security/ | 0.673 |
| crawlee | #3 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.682 | fastapi.tiangolo.com/advanced/security/oauth2-scop | 0.674 |
| colly+md | #5 | fastapi.tiangolo.com/reference/openapi/models/ | 0.679 | fastapi.tiangolo.com/reference/security/ | 0.671 | fastapi.tiangolo.com/tr/reference/security/ | 0.671 |
| playwright | #4 | fastapi.tiangolo.com/reference/security/ | 0.712 | fastapi.tiangolo.com/tr/reference/security/ | 0.709 | fastapi.tiangolo.com/tutorial/security/first-steps | 0.682 |


**Q7: How do I use WebSockets in FastAPI?**
*(expects URL containing: `websockets`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.652 | fastapi.tiangolo.com/reference/websockets/ | 0.622 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.818 | fastapi.tiangolo.com/advanced/websockets/ | 0.678 | fastapi.tiangolo.com/advanced/websockets/ | 0.672 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/reference/websockets/ | 0.625 |
| crawlee | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.810 | fastapi.tiangolo.com/advanced/websockets/ | 0.662 | fastapi.tiangolo.com/tr/reference/websockets/ | 0.625 |
| playwright | #1 | fastapi.tiangolo.com/advanced/websockets/ | 0.811 | fastapi.tiangolo.com/advanced/websockets/ | 0.657 | fastapi.tiangolo.com/advanced/websockets/ | 0.645 |


**Q8: How do I stream data responses in FastAPI?**
*(expects URL containing: `stream-data`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.610 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 | fastapi.tiangolo.com/advanced/stream-data/ | 0.625 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.642 | fastapi.tiangolo.com/advanced/stream-data/ | 0.625 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.610 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/stream-json-lines/ | 0.580 | fastapi.tiangolo.com/advanced/custom-response/ | 0.571 | fastapi.tiangolo.com/alternatives/ | 0.563 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.612 | fastapi.tiangolo.com/advanced/stream-data/ | 0.610 |
| playwright | #1 | fastapi.tiangolo.com/advanced/stream-data/ | 0.654 | fastapi.tiangolo.com/advanced/stream-data/ | 0.616 | fastapi.tiangolo.com/reference/responses/ | 0.615 |


**Q9: How do I return additional response types in FastAPI?**
*(expects URL containing: `additional-responses`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/reference/responses/ | 0.604 | fastapi.tiangolo.com/advanced/additional-responses | 0.600 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.681 | fastapi.tiangolo.com/advanced/additional-responses | 0.646 | fastapi.tiangolo.com/advanced/custom-response/ | 0.639 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/custom-response/ | 0.615 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 |
| crawlee | miss | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.592 | fastapi.tiangolo.com/advanced/additional-status-co | 0.591 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.640 | fastapi.tiangolo.com/advanced/additional-responses | 0.605 | fastapi.tiangolo.com/reference/responses/ | 0.604 |
| playwright | #1 | fastapi.tiangolo.com/advanced/additional-responses | 0.656 | fastapi.tiangolo.com/advanced/additional-responses | 0.612 | fastapi.tiangolo.com/advanced/custom-response/ | 0.612 |


**Q10: How do I write async tests for FastAPI applications?**
*(expects URL containing: `async-tests`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/tutorial/testing/ | 0.657 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.747 | fastapi.tiangolo.com/tutorial/testing/ | 0.657 | fastapi.tiangolo.com/advanced/async-tests/ | 0.632 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| crawlee | miss | fastapi.tiangolo.com/tutorial/testing/ | 0.644 | fastapi.tiangolo.com/tutorial/testing/ | 0.577 | fastapi.tiangolo.com/deployment/versions/ | 0.564 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.750 | fastapi.tiangolo.com/tutorial/testing/ | 0.623 | fastapi.tiangolo.com/advanced/async-tests/ | 0.604 |
| playwright | #1 | fastapi.tiangolo.com/advanced/async-tests/ | 0.727 | fastapi.tiangolo.com/tutorial/testing/ | 0.644 | fastapi.tiangolo.com/advanced/async-tests/ | 0.617 |


**Q11: How do I define nested Pydantic models for request bodies?**
*(expects URL containing: `body-nested-models`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/body/ | 0.626 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body/ | 0.592 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.735 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.706 | fastapi.tiangolo.com/tutorial/body/ | 0.592 |
| scrapy+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.570 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.564 |
| colly+md | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.711 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.658 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.570 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.721 | fastapi.tiangolo.com/tutorial/body-nested-models/ | 0.686 | fastapi.tiangolo.com/tutorial/query-param-models/ | 0.564 |


**Q12: How do I handle startup and shutdown events in FastAPI?**
*(expects URL containing: `events`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/advanced/events/ | 0.660 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/tutorial/sql-databases/ | 0.625 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/advanced/events/ | 0.633 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/events/ | 0.685 | fastapi.tiangolo.com/advanced/events/ | 0.679 | fastapi.tiangolo.com/advanced/events/ | 0.633 |
| scrapy+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/tutorial/sql-databases/ | 0.625 |
| crawlee | #5 | fastapi.tiangolo.com/deployment/concepts/ | 0.566 | fastapi.tiangolo.com/deployment/concepts/ | 0.552 | fastapi.tiangolo.com/deployment/concepts/ | 0.492 |
| colly+md | #1 | fastapi.tiangolo.com/advanced/events/ | 0.670 | fastapi.tiangolo.com/advanced/events/ | 0.659 | fastapi.tiangolo.com/tutorial/sql-databases/ | 0.625 |
| playwright | #1 | fastapi.tiangolo.com/advanced/events/ | 0.682 | fastapi.tiangolo.com/advanced/events/ | 0.655 | fastapi.tiangolo.com/tutorial/sql-databases/ | 0.625 |


**Q13: How do I use middleware in FastAPI?**
*(expects URL containing: `middleware`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 | fastapi.tiangolo.com/reference/fastapi/ | 0.677 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.677 |
| crawl4ai | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.730 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.716 | fastapi.tiangolo.com/reference/fastapi/ | 0.716 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.730 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.717 | fastapi.tiangolo.com/reference/fastapi/ | 0.716 |
| scrapy+md | #3 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 |
| crawlee | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.719 | fastapi.tiangolo.com/tutorial/middleware/ | 0.627 | fastapi.tiangolo.com/tutorial/middleware/ | 0.600 |
| colly+md | #3 | fastapi.tiangolo.com/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.723 | fastapi.tiangolo.com/tutorial/middleware/ | 0.711 |
| playwright | #1 | fastapi.tiangolo.com/tutorial/middleware/ | 0.719 | fastapi.tiangolo.com/reference/fastapi/ | 0.718 | fastapi.tiangolo.com/tr/reference/fastapi/ | 0.716 |


**Q14: How do I use Jinja2 templates in FastAPI?**
*(expects URL containing: `templating`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #1 | fastapi.tiangolo.com/reference/templating/ | 0.755 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/advanced/templates/ | 0.669 |
| crawl4ai | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.765 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.765 | fastapi.tiangolo.com/reference/templating/ | 0.761 | fastapi.tiangolo.com/reference/templating/ | 0.702 |
| scrapy+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/reference/templating/ | 0.685 |
| crawlee | #1 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 | fastapi.tiangolo.com/alternatives/ | 0.579 |
| colly+md | #1 | fastapi.tiangolo.com/reference/templating/ | 0.766 | fastapi.tiangolo.com/advanced/templates/ | 0.741 | fastapi.tiangolo.com/reference/templating/ | 0.685 |
| playwright | #1 | fastapi.tiangolo.com/advanced/templates/ | 0.752 | fastapi.tiangolo.com/reference/templating/ | 0.742 | fastapi.tiangolo.com/reference/templating/ | 0.692 |


**Q15: How do I deploy FastAPI to the cloud?**
*(expects URL containing: `deployment`)*

| Tool | Hit | Top-1 URL | Score | Top-2 URL | Score | Top-3 URL | Score |
|---|---|---|---|---|---|---|---|
| markcrawl | #3 | fastapi.tiangolo.com/tutorial/first-steps/ | 0.754 | fastapi.tiangolo.com/ | 0.754 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.740 |
| crawl4ai | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/cloud/ | 0.786 | fastapi.tiangolo.com/deployment/cloud/ | 0.783 |
| crawl4ai-raw | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.787 | fastapi.tiangolo.com/deployment/cloud/ | 0.786 | fastapi.tiangolo.com/deployment/cloud/ | 0.783 |
| scrapy+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/ | 0.754 |
| crawlee | #14 | fastapi.tiangolo.com/ | 0.748 | fastapi.tiangolo.com/ | 0.718 | fastapi.tiangolo.com/ | 0.708 |
| colly+md | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.760 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.756 | fastapi.tiangolo.com/ | 0.754 |
| playwright | #1 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.768 | fastapi.tiangolo.com/deployment/cloud/ | 0.762 | fastapi.tiangolo.com/deployment/fastapicloud/ | 0.762 |


</details>

## Methodology

- **Queries:** 15 across 1 sites (verified against crawled pages)
- **Embedding model:** `text-embedding-3-small` (1536 dimensions)
- **Chunking:** Markdown-aware, 400 word max, 50 word overlap
- **Retrieval modes:** Embedding (cosine), BM25 (Okapi), Hybrid (RRF k=60), Reranked (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Retrieval:** Hit rate reported at K = 1, 3, 5, 10, 20, plus MRR
- **Reranking:** Top-50 candidates from hybrid search, reranked to top-20
- **Chunk sensitivity:** Tested at ~256tok, ~512tok, ~1024tok
- **Confidence intervals:** Wilson score interval (95%)
- **Same chunking and embedding** for all tools — only extraction quality varies
- **No fine-tuning or tool-specific optimization** — identical pipeline for all

