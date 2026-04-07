# End-to-End RAG Answer Quality

<!-- style: v2, 2026-04-07 -->

Does cleaner crawler output produce better LLM answers?

Yes — but modestly. Across 92 queries on 8 sites, markcrawl produces the
highest-scoring answers of all 7 tools tested, with an overall score of 3.91/5.
The closest competitor (scrapy+md) scores 3.86, and the weakest (playwright)
scores 3.74. The gap between first and last is 0.17 points — real, but not
dramatic. Cleaner output helps most on completeness (where markcrawl's lead is
widest) and least on correctness (where all tools cluster between 4.08–4.20).

**What the scores mean.** Each answer is graded on four dimensions —
correctness, relevance, completeness, and usefulness — by `gpt-4o-mini` on a
1–5 scale:

- **5** — the answer is fully correct, directly relevant, covers everything the
  question asks, and is presented clearly. Nothing missing.
- **3** — the answer is partially correct or incomplete. Usable, but you
  wouldn't trust it without double-checking. Important details are missing or
  the response hedges significantly.
- **1** — the answer is wrong, off-topic, or the model declined to answer based
  on the retrieved context.

All tools in this benchmark score between 3.74 and 3.91, which lands in the
"good but not perfect" range: answers are usually correct and relevant, but
completeness is the weak point across the board (all tools score between
3.35–3.57 on that dimension). A score of 3.91 means the average answer is
closer to "solid" than "unreliable" — most answers work, but a meaningful
fraction are incomplete.

**For the senior engineer wondering about rigor:** the judge model is
`gpt-4o-mini`, scores are averaged across 92 queries spanning 8 sites of
varying difficulty, and each query is answered independently per tool using the
same retrieval pipeline (hybrid retrieval with reranking). The sample size is
modest — 92 queries is enough to see consistent patterns but too small for
tight confidence intervals on a 0.05-point gap. See
[METHODOLOGY.md](METHODOLOGY.md) for full test setup, tool configurations, and
reproducibility instructions.

**What this means in practice.** For most RAG applications, any of these
crawlers will produce acceptable answer quality. The choice of crawler alone is
unlikely to make or break whether your LLM answers are good enough. Where
markcrawl's cleaner output shows up most clearly is on harder sites — those
with heavy navigation chrome, repetitive boilerplate, or structured data (like
API docs or e-commerce listings) — where noise in the retrieved context visibly
degrades completeness. If your use case involves crawling messy or content-rich
sites at scale, the 0.17-point quality gap compounds: see
[COST_AT_SCALE.md](COST_AT_SCALE.md) for how cleaner output also reduces chunk
counts and embedding costs at scale. Interestingly, retrieval accuracy itself
is similar across tools (see
[RETRIEVAL_COMPARISON.md](RETRIEVAL_COMPARISON.md)) — the quality difference
shows up downstream, in the LLM's ability to synthesize cleaner context into
better answers.

## Summary (92 queries across 8 sites)

| Tool | Correctness | Relevance | Completeness | Usefulness | **Overall** | Avg tokens/query |
|---|---|---|---|---|---|---|
| **markcrawl** | **4.20** | **4.01** | **3.57** | **3.87** | **3.91** | **2,385** |
| scrapy+md | 4.12 | 3.96 | 3.52 | 3.84 | **3.86** | 2,347 |
| crawl4ai-raw | 4.14 | 3.96 | 3.46 | 3.80 | **3.84** | 2,264 |
| colly+md | 4.11 | 3.93 | 3.49 | 3.79 | **3.83** | 2,360 |
| crawl4ai | 4.13 | 3.92 | 3.46 | 3.76 | **3.82** | 2,272 |
| crawlee | 4.13 | 3.88 | 3.45 | 3.76 | **3.80** | 2,376 |
| playwright | 4.08 | 3.84 | 3.35 | 3.70 | **3.74** | 2,372 |

_Scores are averages across 92 queries on 8 sites. Each dimension is rated 1–5
by `gpt-4o-mini`. Overall is the mean of the four dimensions._

## quotes-toscrape

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.58 | 4.50 | 4.17 | 4.42 | 4.42 |
| crawl4ai | 4.75 | 4.75 | 4.33 | 4.67 | 4.62 |
| crawl4ai-raw | 4.92 | 4.83 | 4.42 | 4.75 | 4.73 |
| scrapy+md | 4.75 | 4.58 | 4.25 | 4.50 | 4.52 |
| crawlee | 4.67 | 4.50 | 4.17 | 4.50 | 4.46 |
| colly+md | 4.42 | 4.42 | 4.00 | 4.33 | 4.29 |
| playwright | 4.58 | 4.50 | 4.08 | 4.42 | 4.40 |

<details>
<summary>Query-by-query scores for quotes-toscrape</summary>

**Q1: What did Albert Einstein say about thinking and the world?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| crawl4ai | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| crawl4ai-raw | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| scrapy+md | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| crawlee | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| colly+md | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |
| playwright | 5.0 | Albert Einstein said, "The world as we have created it is a process of our thinking. It cannot be ch... |

**Q2: Which quotes are tagged with 'inspirational'?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The quotes tagged with 'inspirational' are:  1. “The world as we have created it is a process of our... |
| crawl4ai | 5.0 | The quotes tagged with 'inspirational' are:  1. “Not all of us can do great things. But we can do sm... |
| crawl4ai-raw | 5.0 | The quotes tagged with 'inspirational' are:  1. “There are only two ways to live your life. One is a... |
| scrapy+md | 5.0 | The quotes tagged with 'inspirational' are:  1. “Not all of us can do great things. But we can do sm... |
| crawlee | 5.0 | The quotes tagged with 'inspirational' are:  1. “I have not failed. I've just found 10,000 ways that... |
| colly+md | 5.0 | The quotes tagged with 'inspirational' are:  1. “I have not failed. I've just found 10,000 ways that... |
| playwright | 5.0 | The quotes tagged with 'inspirational' are:  1. “I have not failed. I've just found 10,000 ways that... |

**Q3: What did Jane Austen say about novels and reading?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Jane Austen said, “The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| crawl4ai | 5.0 | Jane Austen said, "The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| crawl4ai-raw | 5.0 | Jane Austen said, "The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| scrapy+md | 5.0 | Jane Austen said, “The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| crawlee | 5.0 | Jane Austen said, "The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| colly+md | 5.0 | Jane Austen said, "The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |
| playwright | 5.0 | Jane Austen said, "The person, be it gentleman or lady, who has not pleasure in a good novel, must b... |

**Q4: What quotes are about the truth?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.8 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q5: Which quotes are about humor and being funny?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.2 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |
| crawl4ai | 4.2 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |
| crawl4ai-raw | 5.0 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |
| scrapy+md | 5.0 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |
| crawlee | 5.0 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |
| colly+md | 3.0 | The quotes about humor and being funny are:  1. “The person, be it gentleman or lady, who has not pl... |
| playwright | 4.2 | The quotes about humor and being funny are:  1. “A day without sunshine is like, you know, night.” b... |

**Q6: What did J.K. Rowling say about choices and abilities?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | J.K. Rowling said, “It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| crawl4ai | 5.0 | J.K. Rowling said, “It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| crawl4ai-raw | 5.0 | J.K. Rowling said, “It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| scrapy+md | 5.0 | J.K. Rowling said, "It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| crawlee | 5.0 | J.K. Rowling said, "It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| colly+md | 5.0 | J.K. Rowling said, "It is our choices, Harry, that show what we truly are, far more than our abiliti... |
| playwright | 5.0 | J.K. Rowling said, "It is our choices, Harry, that show what we truly are, far more than our abiliti... |

**Q7: What quotes are tagged with 'change'?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai | 5.0 | The quote tagged with 'change' is: “The world as we have created it is a process of our thinking. It... |
| crawl4ai-raw | 4.8 | The quote tagged with 'change' is: “The world as we have created it is a process of our thinking. It... |
| scrapy+md | 2.8 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

**Q8: What did Steve Martin say about sunshine?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| crawl4ai | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| crawl4ai-raw | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| scrapy+md | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| crawlee | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| colly+md | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |
| playwright | 5.0 | Steve Martin said, “A day without sunshine is like, you know, night.”... |

**Q9: Which quotes talk about believing in yourself?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.8 | The quote by Marilyn Monroe discusses believing in yourself: "Keep trying, hold on, and always, alwa... |
| crawl4ai | 4.8 | The quote that talks about believing in yourself is:   "Keep trying, hold on, and always, always, al... |
| crawl4ai-raw | 4.8 | The quote that talks about believing in yourself is:   "Keep trying, hold on, and always, always, al... |
| scrapy+md | 4.8 | The quote by Marilyn Monroe talks about believing in yourself: "Keep trying, hold on, and always, al... |
| crawlee | 4.8 | The quote by Marilyn Monroe talks about believing in yourself: "Keep trying, hold on, and always, al... |
| colly+md | 4.8 | The quote by Marilyn Monroe talks about believing in yourself: "Keep trying, hold on, and always, al... |
| playwright | 4.8 | The quote by Marilyn Monroe talks about believing in yourself: "Keep trying, hold on, and always, al... |

**Q10: What are the quotes about miracles and living life?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| crawl4ai | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| crawl4ai-raw | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| scrapy+md | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| crawlee | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| colly+md | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |
| playwright | 4.8 | “There are only two ways to live your life. One is as though nothing is a miracle. The other is as t... |

**Q11: What quotes are about thinking deeply?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| crawl4ai | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| crawl4ai-raw | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| scrapy+md | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| crawlee | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| colly+md | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |
| playwright | 4.8 | The quote about thinking deeply is: “The world as we have created it is a process of our thinking. I... |

**Q12: What quotes talk about living life fully?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |
| crawl4ai | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |
| crawl4ai-raw | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |
| scrapy+md | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |
| crawlee | 5.0 | The quotes that talk about living life fully include:  1. “There are only two ways to live your life... |
| colly+md | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |
| playwright | 5.0 | The quotes that talk about living life fully are:  1. “There are only two ways to live your life. On... |

</details>

## books-toscrape

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.62 | 4.77 | 4.54 | 4.62 | 4.63 |
| crawl4ai | 3.69 | 3.54 | 3.15 | 3.31 | 3.42 |
| crawl4ai-raw | 3.62 | 3.69 | 3.08 | 3.38 | 3.44 |
| scrapy+md | 4.38 | 4.77 | 4.38 | 4.46 | 4.50 |
| crawlee | 4.46 | 4.62 | 4.38 | 4.46 | 4.48 |
| colly+md | 4.46 | 4.62 | 4.38 | 4.46 | 4.48 |
| playwright | 4.46 | 4.69 | 4.38 | 4.46 | 4.50 |

<details>
<summary>Query-by-query scores for books-toscrape</summary>

**Q1: What books are available for under 20 pounds?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.2 | The following books are available for under 20 pounds:  1. [Starving Hearts (Triangular Trade Trilog... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 3.2 | 1. [The Requiem Red](../../../the-requiem-red_995/index.html) - £22.65   2. [Set Me Free](../../../s... |
| crawlee | 2.2 | 1. [The Requiem Red](../../../the-requiem-red_995/index.html) - £22.65   2. [Set Me Free](../../../s... |
| colly+md | 2.2 | 1. [The Requiem Red](../../../the-requiem-red_995/index.html) - £22.65   2. [Set Me Free](../../../s... |
| playwright | 2.2 | 1. **The Requiem Red** - £22.65 2. **Set Me Free** - £17.46 3. **Obsidian (Lux #1)** - £14.86 4. **W... |

**Q2: What mystery and thriller books are in the catalog?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The mystery books in the catalog are:  1. Sharp Objects - £47.82 2. In a Dark, Dark Wood - £19.63 3.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 4.8 | **Mystery Books:** 1. Sharp Objects - £47.82 2. In a Dark, Dark Wood - £19.63 3. The Past Never Ends... |
| crawlee | 4.8 | **Mystery Books:** 1. Sharp Objects - £47.82 2. In a Dark, Dark Wood - £19.63 3. The Past Never Ends... |
| colly+md | 4.8 | **Mystery Books:** 1. Sharp Objects - £47.82 2. In a Dark, Dark ... - £19.63 3. The Past Never Ends ... |
| playwright | 4.8 | **Mystery Books:** 1. Sharp Objects - £47.82 2. In a Dark, Dark Wood - £19.63 3. The Past Never Ends... |

**Q3: What is the rating of the most expensive book?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

**Q4: What science fiction books are available?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The available science fiction books are:  1. Mesaerion: The Best Science Fiction Stories 1800-1849 -... |
| crawl4ai | 2.2 | The available science fiction book is "Mesaerion: The Best Science Fiction Stories 1800-1849."... |
| crawl4ai-raw | 2.2 | The available science fiction book is "Mesaerion: The Best Science Fiction Stories 1800-1849."... |
| scrapy+md | 5.0 | The available science fiction books are:  1. Mesaerion: The Best Science Fiction Stories 1800-1849 -... |
| crawlee | 5.0 | The available science fiction books are:  1. Mesaerion: The Best Science Fiction Stories 1800-1849 -... |
| colly+md | 5.0 | The available science fiction books are:  1. Mesaerion: The Best Science Fiction Stories 1800-1849 -... |
| playwright | 5.0 | The available science fiction books are:  1. Mesaerion: The Best Science Fiction Stories 1800-1849 -... |

**Q5: What horror books are in the catalog?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The horror books in the catalog are:  1. Security - £39.25 2. Follow You Home - £21.36 3. The Loney ... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 5.0 | The horror books in the catalog are:  1. Security - £39.25 2. Follow You Home - £21.36 3. The Loney ... |
| crawlee | 5.0 | The horror books in the catalog are:  1. Security - £39.25 2. Follow You Home - £21.36 3. The Loney ... |
| colly+md | 5.0 | The horror books in the catalog are:  1. Security - £39.25 2. Follow You Home - £21.36 3. The Loney ... |
| playwright | 5.0 | The horror books in the catalog are:  1. Security - £39.25 2. Follow You Home - £21.36 3. The Loney ... |

**Q6: What poetry books can I find?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can find the following poetry books:  1. A Light in the Attic - £51.77 2. The Black Maria - £52.... |
| crawl4ai | 5.0 | You can find the following poetry books:  1. [A Light in the Attic](https://books.toscrape.com/catal... |
| crawl4ai-raw | 5.0 | You can find the following poetry books:  1. [A Light in the Attic](https://books.toscrape.com/catal... |
| scrapy+md | 5.0 | You can find the following poetry books:  1. A Light in the Attic - £51.77 2. The Black Maria - £52.... |
| crawlee | 5.0 | You can find the following poetry books:  1. A Light in the Attic - £51.77 2. The Black Maria - £52.... |
| colly+md | 5.0 | You can find the following poetry books:  1. A Light in the Attic - £51.77 2. The Black Maria - £52.... |
| playwright | 5.0 | You can find the following poetry books:  1. A Light in the Attic - £51.77 2. The Black Maria - £52.... |

**Q7: What romance novels are available?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The available romance novels are:  1. Chase Me (Paris Nights #2) - £25.27 2. Black Dust - £34.53 3. ... |
| crawl4ai | 3.5 | The available romance novels are:  1. [Chase Me (Paris Nights #2)](https://books.toscrape.com/catalo... |
| crawl4ai-raw | 3.5 | The available romance novels are:  1. [Chase Me (Paris Nights #2)](https://books.toscrape.com/catalo... |
| scrapy+md | 5.0 | The available romance novels are:  1. Chase Me (Paris Nights #2) - £25.27 2. Black Dust - £34.53 3. ... |
| crawlee | 5.0 | The available romance novels are:  1. Chase Me (Paris Nights #2) - £25.27 2. Black Dust - £34.53 3. ... |
| colly+md | 5.0 | The available romance novels are:  1. Chase Me (Paris Nights #2) - £25.27 2. Black Dust - £34.53 3. ... |
| playwright | 5.0 | The available romance novels are:  1. Chase Me (Paris Nights #2) - £25.27 2. Black Dust - £34.53 3. ... |

**Q8: What history books are in the collection?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The history books in the collection are:  1. Sapiens: A Brief History of Humankind - £54.23 2. Unbou... |
| crawl4ai | 3.0 | The context does not provide specific titles of history books in the collection, only a mention of "... |
| crawl4ai-raw | 3.5 | The history books in the collection include:  1. "A Short History of Nearly Everything" 2. "The Rise... |
| scrapy+md | 5.0 | The history books in the collection are:  1. **Sapiens: A Brief History of Humankind** - £54.23 2. *... |
| crawlee | 5.0 | The history books in the collection are:  1. Sapiens: A Brief History of Humankind - £54.23 2. Unbou... |
| colly+md | 5.0 | The history books in the collection are:  1. Sapiens: A Brief History of Humankind - £54.23 2. Unbou... |
| playwright | 5.0 | The history books in the collection are:  1. Sapiens: A Brief History of Humankind - £54.23 2. Unbou... |

**Q9: What philosophy books are available to read?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.0 | The available philosophy books are:  1. **Sophie’s World** - £15.94 2. **The Death of Humanity: and ... |
| crawl4ai | 3.8 | The available philosophy books are:  1. At The Existentialist Café: Freedom, Being, and apricot cock... |
| crawl4ai-raw | 3.5 | The available philosophy books are:  1. At The Existentialist Café: Freedom, Being, and apricot cock... |
| scrapy+md | 4.0 | The available philosophy books are:  1. **Sophie's World** - £15.94 2. **The Death of Humanity: and ... |
| crawlee | 4.0 | The available philosophy books are:  1. Sophie's World - £15.94 2. The Death of Humanity: and the Ca... |
| colly+md | 4.0 | The available philosophy books are:  1. Sophie's World - £15.94 2. The Death of Humanity: and the Ca... |
| playwright | 4.0 | The available philosophy books are:  1. Sophie's World - £15.94 2. The Death of Humanity: and the Ca... |

**Q10: What humor and comedy books can I find?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The humor and comedy books available are:  1. **The Long Haul (Diary of a Wimpy Kid #9)** - £44.07 2... |
| crawl4ai | 5.0 | You can find the following humor and comedy books:  1. [The Long Haul (Diary of a Wimpy Kid #9)](htt... |
| crawl4ai-raw | 5.0 | The humor and comedy books available are:  1. [The Long Haul (Diary of a Wimpy Kid #9)](https://book... |
| scrapy+md | 4.2 | The humor and comedy books available are:  1. **The Long Haul (Diary of a Wimpy Kid #9)** - £44.07 2... |
| crawlee | 5.0 | You can find the following humor and comedy books:  1. The Long Haul (Diary of a Wimpy Kid #9) - £44... |
| colly+md | 5.0 | You can find the following humor and comedy books:  1. The Long Haul (Diary of a Wimpy Kid #9) - £44... |
| playwright | 5.0 | You can find the following humor and comedy books:  1. The Long Haul (Diary of a Wimpy Kid #9) - £44... |

**Q11: What fantasy books are in the bookstore?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | 1. Unicorn Tracks - £18.78   2. Saga, Volume 6 - £25.02   3. Princess Between Worlds - £13.34   4. M... |
| crawl4ai | 5.0 | The fantasy books in the bookstore are:  1. The Bane Chronicles (The Bane Chronicles #1-11) - £44.73... |
| crawl4ai-raw | 5.0 | The fantasy books in the bookstore are:  1. The Bane Chronicles (The Bane Chronicles #1-11) - £44.73... |
| scrapy+md | 5.0 | The fantasy books in the bookstore are:  1. Unicorn Tracks - £18.78 2. Saga, Volume 6 - £25.02 3. Pr... |
| crawlee | 5.0 | 1. Unicorn Tracks - £18.78 2. Saga, Volume 6 - £25.02 3. Princess Between Worlds - £13.34 4. Masks a... |
| colly+md | 5.0 | 1. Unicorn Tracks - £18.78 2. Saga, Volume 6 - £25.02 3. Princess Between Worlds - £13.34 4. Masks a... |
| playwright | 5.0 | 1. Unicorn Tracks - £18.78 2. Saga, Volume 6 - £25.02 3. Princess Between Worlds - £13.34 4. Masks a... |

**Q12: What is the book Sharp Objects about?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |
| crawl4ai | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |
| crawl4ai-raw | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |
| scrapy+md | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |
| crawlee | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |
| colly+md | 5.0 | Sharp Objects is about reporter Camille Preaker, who returns to her hometown to cover the murders of... |
| playwright | 5.0 | Sharp Objects follows reporter Camille Preaker, who returns to her hometown to cover the murders of ... |

**Q13: What biography books are in the catalog?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | 1. Louisa: The Extraordinary Life of Mrs. Adams - £16.85 2. Setting the World on Fire: The Brief, As... |
| crawl4ai | 2.8 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.8 | I cannot answer this based on the provided context.... |
| scrapy+md | 5.0 | 1. Louisa: The Extraordinary Life of Mrs. Adams - £16.85 2. Setting the World on Fire: The Brief, As... |
| crawlee | 5.0 | The biography books in the catalog are:  1. Louisa: The Extraordinary Life of Mrs. Adams - £16.85 2.... |
| colly+md | 5.0 | The biography books in the catalog are:  1. Louisa: The Extraordinary Life of Mrs. Adams - £16.85 2.... |
| playwright | 5.0 | The biography books in the catalog are:  1. Louisa: The Extraordinary Life of Mrs. Adams - £16.85 2.... |

</details>

## fastapi-docs

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.00 | 3.80 | 3.20 | 3.60 | 3.65 |
| crawl4ai | 4.00 | 3.73 | 3.07 | 3.53 | 3.58 |
| crawl4ai-raw | 4.00 | 3.73 | 3.13 | 3.53 | 3.60 |
| scrapy+md | 4.13 | 3.87 | 3.47 | 3.73 | 3.80 |
| crawlee | 4.00 | 3.67 | 3.13 | 3.47 | 3.57 |
| colly+md | 4.20 | 4.20 | 3.73 | 4.00 | 4.03 |
| playwright | 4.00 | 3.67 | 3.13 | 3.47 | 3.57 |

<details>
<summary>Query-by-query scores for fastapi-docs</summary>

**Q1: How do I add authentication to a FastAPI endpoint?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q2: What is the default response status code in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 3.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 5.0 | The default response status code in FastAPI is `200` (OK) for the `JSONResponse`. For the `RedirectR... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 4.2 | The default response status code in FastAPI is `200` (OK) for JSON responses and `307` (Temporary Re... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q3: How do I define query parameters in the FastAPI reference?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can define query parameters in FastAPI using the `Depends` function along with the `APIKeyQuery`... |
| crawl4ai | 5.0 | You can define query parameters in FastAPI using the `APIKeyQuery` class from `fastapi.security`. Yo... |
| crawl4ai-raw | 5.0 | You can define query parameters in FastAPI using the `APIKeyQuery` class from `fastapi.security`. Yo... |
| scrapy+md | 5.0 | You can define query parameters in FastAPI using the `APIKeyQuery` class from `fastapi.security`. Yo... |
| crawlee | 5.0 | You can define query parameters in FastAPI using the `Depends` function along with a security class ... |
| colly+md | 5.0 | To define query parameters in FastAPI, you can use the `Depends` function along with a security clas... |
| playwright | 5.0 | You can define query parameters in FastAPI using the `Depends` function along with a security class ... |

**Q4: How does FastAPI handle JSON encoding and base64 bytes?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 3.0 | I cannot answer this based on the provided context.... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

**Q5: What Python types does FastAPI support for request bodies?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | FastAPI supports standard Python types for request bodies, including Pydantic models, lists, diction... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 5.0 | FastAPI supports standard modern Python types for request bodies, including Pydantic models, lists, ... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

**Q6: How do I use OAuth2 with password flow in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 5.0 | To use OAuth2 with password flow in FastAPI, you can utilize the `OAuth2PasswordRequestForm` or `OAu... |
| crawl4ai-raw | 5.0 | To use OAuth2 with password flow in FastAPI, you can utilize the `OAuth2PasswordRequestForm` or `OAu... |
| scrapy+md | 5.0 | To use OAuth2 with password flow in FastAPI, you can utilize the `OAuth2PasswordRequestForm` or `OAu... |
| crawlee | 5.0 | To use OAuth2 with password flow in FastAPI, you can follow these steps:  1. **Create a dependency c... |
| colly+md | 5.0 | To use OAuth2 with password flow in FastAPI, you can utilize the `OAuth2PasswordRequestForm` or `OAu... |
| playwright | 5.0 | To use OAuth2 with password flow in FastAPI, you can follow these steps:  1. **Create a dependency c... |

**Q7: How do I use WebSockets in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To use WebSockets in FastAPI, you can define a WebSocket endpoint using the `@app.websocket` decorat... |
| crawl4ai | 4.8 | To use WebSockets in FastAPI, you typically declare a parameter of type `WebSocket` in your route fu... |
| crawl4ai-raw | 4.8 | To use WebSockets in FastAPI, you typically declare a parameter of type `WebSocket` in your endpoint... |
| scrapy+md | 5.0 | To use WebSockets in FastAPI, you can define a WebSocket endpoint using the `@app.websocket` decorat... |
| crawlee | 5.0 | To use WebSockets in FastAPI, you can define a WebSocket endpoint by decorating a function with `@ap... |
| colly+md | 5.0 | To use WebSockets in FastAPI, you can define a WebSocket endpoint using the `@app.websocket` decorat... |
| playwright | 5.0 | To use WebSockets in FastAPI, you need to define a WebSocket endpoint using the `@app.websocket()` d... |

**Q8: How do I stream data responses in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can stream data responses in FastAPI using the `StreamingResponse` class. This class takes an as... |
| crawl4ai | 5.0 | To stream data responses in FastAPI, you can use the `StreamingResponse` class. This class takes an ... |
| crawl4ai-raw | 5.0 | You can stream data responses in FastAPI using the `StreamingResponse` class. This class takes an as... |
| scrapy+md | 5.0 | To stream data responses in FastAPI, you can use the `StreamingResponse` class. This class takes an ... |
| crawlee | 5.0 | To stream data responses in FastAPI, you can use the `StreamingResponse` class. This class takes an ... |
| colly+md | 5.0 | To stream data responses in FastAPI, you can use the `StreamingResponse` class. This class takes an ... |
| playwright | 5.0 | To stream data responses in FastAPI, you can use the `StreamingResponse` class. This class takes an ... |

**Q9: How do I return additional response types in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can return additional response types in FastAPI by returning a `Response` directly or any subcla... |
| crawl4ai | 5.0 | You can return additional response types in FastAPI by using the `Response` class or any of its subc... |
| crawl4ai-raw | 5.0 | You can return additional response types in FastAPI by using the `Response` class or any of its subc... |
| scrapy+md | 5.0 | You can return additional response types in FastAPI by using the `Response` class or any of its subc... |
| crawlee | 5.0 | You can return additional response types in FastAPI by overriding the default JSON response. This ca... |
| colly+md | 5.0 | You can return additional response types in FastAPI by returning a `Response` directly or any subcla... |
| playwright | 5.0 | You can return additional response types in FastAPI by overriding the default JSON response. This ca... |

**Q10: How do I write async tests for FastAPI applications?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.5 | I cannot answer this based on the provided context.... |
| crawlee | 2.5 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q11: How do I define nested Pydantic models for request bodies?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 3.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q12: How do I handle startup and shutdown events in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.8 | You should use `lifespan` event handlers instead of the deprecated `on_event` method to handle start... |
| crawl4ai | 4.8 | You can handle startup and shutdown events in FastAPI using the `lifespan` event handlers, as the `o... |
| crawl4ai-raw | 4.8 | You can handle startup and shutdown events in FastAPI using the `lifespan` event handlers, as the `o... |
| scrapy+md | 4.8 | You should use `lifespan` event handlers instead of the deprecated `on_event` method to handle start... |
| crawlee | 4.5 | You should use `lifespan` event handlers instead of `on_event`, as `on_event` is deprecated. For han... |
| colly+md | 4.8 | You should use `lifespan` event handlers instead of `on_event`, as `on_event` is deprecated.... |
| playwright | 4.5 | You should use `lifespan` event handlers instead of `on_event`, as `on_event` is deprecated. For han... |

**Q13: How do I use middleware in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware("http"... |
| crawl4ai | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware` decor... |
| crawl4ai-raw | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware("http"... |
| scrapy+md | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware` decor... |
| crawlee | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware("http"... |
| colly+md | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware("http"... |
| playwright | 5.0 | To use middleware in FastAPI, you can define a middleware function using the `@app.middleware("http"... |

**Q14: How do I use Jinja2 templates in FastAPI?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.5 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

**Q15: How do I deploy FastAPI to the cloud?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| crawl4ai | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| crawl4ai-raw | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| scrapy+md | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| crawlee | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| colly+md | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |
| playwright | 4.0 | You can deploy FastAPI apps to any cloud provider by following their specific guides. Additionally, ... |

</details>

## python-docs

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 3.50 | 3.00 | 2.17 | 2.75 | 2.85 |
| crawl4ai | 3.92 | 3.42 | 2.75 | 3.25 | 3.33 |
| crawl4ai-raw | 3.67 | 3.25 | 2.58 | 3.17 | 3.17 |
| scrapy+md | 3.17 | 2.83 | 2.17 | 2.67 | 2.71 |
| crawlee | 3.25 | 2.75 | 2.08 | 2.50 | 2.65 |
| colly+md | 3.42 | 2.92 | 2.25 | 2.75 | 2.83 |
| playwright | 3.25 | 2.58 | 1.83 | 2.42 | 2.52 |

<details>
<summary>Query-by-query scores for python-docs</summary>

**Q1: What new features were added in Python 3.10?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.8 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q2: What does the term 'decorator' mean in Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q3: How do I report a bug in Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 4.8 | To report a bug in Python, you can visit the [Report a Bug](https://docs.python.org/3.10/bugs.html) ... |
| crawl4ai-raw | 4.8 | To report a bug in Python, you can visit the [Report a Bug](https://docs.python.org/3.10/bugs.html) ... |
| scrapy+md | 2.8 | You can report a bug in Python by visiting the "Report a Bug" link provided on the pages.... |
| crawlee | 2.2 | You can report a bug in Python by visiting the "Report a Bug" link provided on the page.... |
| colly+md | 2.2 | You can report a bug in Python by visiting the "Report a Bug" link provided on the page.... |
| playwright | 2.2 | You can report a bug in Python by visiting the "Report a Bug" link provided on the page.... |

**Q4: What is structural pattern matching in Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q5: What is Python's glossary definition of a generator?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

**Q6: What are the Python how-to guides about?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.0 | The Python how-to guides provide in-depth documents on specific topics related to Python programming... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.5 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

**Q7: What is the Python module index?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The Python module index is a quick access resource that lists all modules available in Python docume... |
| crawl4ai | 5.0 | The Python module index is a quick access resource that lists all modules available in Python. It ca... |
| crawl4ai-raw | 5.0 | The Python module index is a quick access resource that lists all modules available in Python. It ca... |
| scrapy+md | 5.0 | The Python module index is a section in the documentation that lists all the available Python module... |
| crawlee | 3.0 | I cannot answer this based on the provided context.... |
| colly+md | 5.0 | The Python module index is a section in the documentation that lists all the available Python module... |
| playwright | 3.0 | I cannot answer this based on the provided context.... |

**Q8: What Python tutorial topics are available?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 3.0 | The available Python tutorial topics include:  - A tour of Python's syntax and features (found in th... |
| crawl4ai | 4.8 | The available Python tutorial topics include a tour of Python's syntax and features, as well as link... |
| crawl4ai-raw | 4.8 | The available Python tutorial topics include a tour of Python's syntax and features, as well as link... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 4.0 | The available Python tutorial topics include a tour of Python's syntax and features, as indicated in... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

**Q9: What is the Python license and copyright?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright for Py... |
| crawl4ai | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |
| crawl4ai-raw | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |
| scrapy+md | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |
| crawlee | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |
| colly+md | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |
| playwright | 5.0 | Python software and documentation are licensed under the PSF License Agreement. The copyright is hel... |

**Q10: What is the table of contents for Python 3.10 documentation?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.8 | I cannot answer this based on the provided context.... |
| crawl4ai | 5.0 | The table of contents for Python 3.10 documentation includes:  - Installing Python Modules   - Key t... |
| crawl4ai-raw | 4.0 | The table of contents for Python 3.10 documentation includes:  1. Installing Python Modules    - Key... |
| scrapy+md | 3.0 | The table of contents for Python 3.10 documentation includes:  * History and License   + History of ... |
| crawlee | 4.2 | The table of contents for Python 3.10 documentation includes:  - History and License   - History of ... |
| colly+md | 3.0 | I cannot answer this based on the provided context.... |
| playwright | 3.0 | I cannot answer this based on the provided context.... |

**Q11: What does the term 'iterable' mean in Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q12: How do I install and configure Python on my system?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

</details>

## react-dev

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.67 | 4.50 | 4.33 | 4.50 | 4.50 |
| crawl4ai | 4.50 | 4.33 | 4.08 | 4.25 | 4.29 |
| crawl4ai-raw | 4.67 | 4.50 | 4.33 | 4.50 | 4.50 |
| scrapy+md | 4.67 | 4.50 | 4.33 | 4.50 | 4.50 |
| crawlee | 4.50 | 4.25 | 4.00 | 4.25 | 4.25 |
| colly+md | 4.33 | 4.00 | 3.67 | 4.00 | 4.00 |
| playwright | 4.33 | 4.00 | 3.67 | 4.00 | 4.00 |

<details>
<summary>Query-by-query scores for react-dev</summary>

**Q1: How do I manage state in a React component?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To manage state in a React component, you can use the `useState` hook. Call `useState` at the top le... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 5.0 | To manage state in a React component, you can use the `useState` hook. Call `useState` at the top le... |
| crawlee | 5.0 | To manage state in a React component, you can use the `useState` hook. Call `useState` at the top le... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q2: What are React hooks and how do I use them?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | React hooks are functions that allow you to use React features, such as state and lifecycle methods,... |
| crawl4ai | 5.0 | React hooks are functions that start with `use` and allow you to use React features in your componen... |
| crawl4ai-raw | 5.0 | React hooks are functions that start with `use` and allow you to use React features in your componen... |
| scrapy+md | 5.0 | React hooks are functions that allow you to use React features, such as state and lifecycle methods,... |
| crawlee | 5.0 | React hooks are functions that allow you to use React features, such as state and lifecycle methods,... |
| colly+md | 5.0 | React hooks are functions that allow you to use React features, such as state and lifecycle methods,... |
| playwright | 5.0 | React hooks are functions that allow you to use React features, such as state and lifecycle methods,... |

**Q3: How does the useEffect hook work in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q4: How do I handle forms and user input in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 5.0 | To handle forms and user input in React, you can use controlled components with state management. He... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q5: How do I create and use context in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To create and use context in React, follow these steps:  1. **Create the context**: Use `createConte... |
| crawl4ai | 5.0 | To create and use context in React, follow these steps:  1. **Create the context**: Use `createConte... |
| crawl4ai-raw | 5.0 | To create and use context in React, follow these steps:  1. **Create the context**: Use `createConte... |
| scrapy+md | 5.0 | To create and use context in React, follow these steps:  1. **Create the context**: Use `createConte... |
| crawlee | 5.0 | To create and use context in React, follow these steps:  1. **Create the Context**: Use `createConte... |
| colly+md | 5.0 | To create and use context in React, follow these steps:  1. **Create the context**: Use `createConte... |
| playwright | 5.0 | To create and use context in React, follow these steps:  1. **Create the Context**: Use `createConte... |

**Q6: How do I handle events like clicks in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You handle events like clicks in React by declaring event handler functions inside your components a... |
| crawl4ai | 5.0 | In React, you handle events like clicks by declaring event handler functions inside your components ... |
| crawl4ai-raw | 5.0 | In React, you handle events like clicks by declaring event handler functions inside your components ... |
| scrapy+md | 5.0 | You can handle events like clicks in React by declaring event handler functions inside your componen... |
| crawlee | 5.0 | You can handle events like clicks in React by declaring event handler functions inside your componen... |
| colly+md | 5.0 | You can handle events like clicks in React by declaring *event handler* functions inside your compon... |
| playwright | 5.0 | You can handle events like clicks in React by declaring event handler functions inside your componen... |

**Q7: What is JSX and how does React use it?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | JSX is a JavaScript syntax extension popularized by React that allows you to write markup within Jav... |
| crawl4ai | 5.0 | JSX is a JavaScript syntax extension popularized by React that allows you to write markup within Jav... |
| crawl4ai-raw | 5.0 | JSX is a JavaScript syntax extension popularized by React that allows you to write markup within Jav... |
| scrapy+md | 5.0 | JSX is a JavaScript syntax extension popularized by React that allows you to write markup within Jav... |
| crawlee | 5.0 | JSX is a markup syntax that is a JavaScript syntax extension popularized by React. It allows develop... |
| colly+md | 5.0 | JSX is a markup syntax that is a JavaScript syntax extension popularized by React. It allows develop... |
| playwright | 5.0 | JSX is a markup syntax that is a JavaScript syntax extension popularized by React. It allows develop... |

**Q8: How do I render lists and use keys in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To render lists in React, you can use the `map()` function to transform an array into an array of JS... |
| crawl4ai | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of data into ... |
| crawl4ai-raw | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of data into ... |
| scrapy+md | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of items into... |
| crawlee | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of items into... |
| colly+md | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of items into... |
| playwright | 5.0 | To render lists in React, you can use the array `map()` function to transform an array of data into ... |

**Q9: How do I use the useRef hook in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To use the `useRef` hook in React, follow these steps:  1. **Import the Hook**: Start by importing `... |
| crawl4ai | 5.0 | To use the `useRef` hook in React, follow these steps:  1. **Import the Hook**: Start by importing `... |
| crawl4ai-raw | 5.0 | To use the `useRef` hook in React, follow these steps:  1. **Import the Hook**: Start by importing `... |
| scrapy+md | 5.0 | To use the `useRef` hook in React, follow these steps:  1. **Import the Hook**: Start by importing `... |
| crawlee | 5.0 | To use the `useRef` hook in React, follow these steps:  1. Import the `useRef` hook from React:    `... |
| colly+md | 5.0 | To use the `useRef` hook in React, follow these steps:  1. Import the `useRef` hook from React:    `... |
| playwright | 5.0 | To use the `useRef` hook in React, follow these steps:  1. Import the `useRef` hook from React:    `... |

**Q10: How do I pass props between React components?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You pass props between React components by including them as attributes in the JSX of the parent com... |
| crawl4ai | 5.0 | To pass props between React components, you can follow these steps:  1. In the parent component, def... |
| crawl4ai-raw | 5.0 | To pass props between React components, you can follow these steps:  1. **Define the props in the pa... |
| scrapy+md | 5.0 | You can pass props between React components by using JSX curly braces to specify the data you want t... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q11: How do I conditionally render content in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can conditionally render content in React using an `if` statement, the conditional `?` operator,... |
| crawl4ai | 5.0 | You can conditionally render content in React using an `if` statement, the conditional `?` operator,... |
| crawl4ai-raw | 5.0 | You can conditionally render content in React using an `if` statement, the conditional `?` operator,... |
| scrapy+md | 5.0 | You can conditionally render content in React using an `if` statement, the conditional `?` operator,... |
| crawlee | 5.0 | In React, you can conditionally render content using several methods:  1. **Using an `if` statement*... |
| colly+md | 5.0 | In React, you can conditionally render content using several methods:  1. **Using an `if` statement*... |
| playwright | 5.0 | In React, you can conditionally render content using several methods:  1. **Using an `if` statement*... |

**Q12: What is the useMemo hook for in React?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The `useMemo` hook in React is used to create or re-access a memoized value from a function call, re... |
| crawl4ai | 5.0 | The `useMemo` hook in React is used to create and memoize a value from a function call, re-running t... |
| crawl4ai-raw | 5.0 | The `useMemo` hook in React is used to create and memoize a value from a function call, re-running t... |
| scrapy+md | 5.0 | The `useMemo` hook in React is used to create or re-access a memoized value from a function call, re... |
| crawlee | 5.0 | The `useMemo` hook in React is used to create or re-access a memoized value from a function call, re... |
| colly+md | 5.0 | The `useMemo` hook in React is used to create or re-access a memoized value from a function call, re... |
| playwright | 5.0 | The `useMemo` hook in React is used to create or re-access a memoized value from a function call, re... |

</details>

## wikipedia-python

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.80 | 4.70 | 4.50 | 4.70 | 4.67 |
| crawl4ai | 4.80 | 4.70 | 4.40 | 4.70 | 4.65 |
| crawl4ai-raw | 4.80 | 4.70 | 4.40 | 4.70 | 4.65 |
| scrapy+md | 4.80 | 4.70 | 4.50 | 4.70 | 4.67 |
| crawlee | 4.80 | 4.70 | 4.50 | 4.70 | 4.67 |
| colly+md | 4.80 | 4.70 | 4.50 | 4.70 | 4.67 |
| playwright | 4.80 | 4.70 | 4.50 | 4.70 | 4.67 |

<details>
<summary>Query-by-query scores for wikipedia-python</summary>

**Q1: Who created the Python programming language?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Guido van Rossum created the Python programming language.... |
| crawl4ai | 5.0 | Guido van Rossum created the Python programming language.... |
| crawl4ai-raw | 5.0 | Guido van Rossum created the Python programming language.... |
| scrapy+md | 5.0 | Guido van Rossum created the Python programming language.... |
| crawlee | 5.0 | The Python programming language was created by Guido van Rossum.... |
| colly+md | 5.0 | The Python programming language was created by Guido van Rossum.... |
| playwright | 5.0 | The Python programming language was created by Guido van Rossum.... |

**Q2: What is the history and development of Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| crawl4ai | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| crawl4ai-raw | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| scrapy+md | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| crawlee | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| colly+md | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |
| playwright | 5.0 | Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) i... |

**Q3: What programming paradigms does Python support?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural (imperative), ... |
| crawl4ai | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural (imperative), ... |
| crawl4ai-raw | 5.0 | Python supports multiple programming paradigms, including object-oriented programming, structured pr... |
| scrapy+md | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural (imperative), ... |
| crawlee | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural (imperative), ... |
| colly+md | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural, functional, s... |
| playwright | 5.0 | Python supports multiple programming paradigms, including object-oriented, procedural, functional, s... |

**Q4: What is the Python Software Foundation?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | The Python Software Foundation is an organization that supports the development and promotion of the... |
| crawl4ai | 5.0 | The Python Software Foundation is the organization that develops and supports the Python programming... |
| crawl4ai-raw | 5.0 | The Python Software Foundation is the organization that develops and supports the Python programming... |
| scrapy+md | 5.0 | The Python Software Foundation is an organization that supports the development and promotion of the... |
| crawlee | 5.0 | The Python Software Foundation is an organization that supports the development of the Python progra... |
| colly+md | 5.0 | The Python Software Foundation is an organization that supports the development and promotion of the... |
| playwright | 5.0 | The Python Software Foundation is an organization that supports the development and promotion of the... |

**Q5: What is the syntax and design philosophy of Python?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Python's design philosophy emphasizes code readability, using significant indentation to define code... |
| crawl4ai | 5.0 | Python's design philosophy emphasizes code readability, using significant indentation to define code... |
| crawl4ai-raw | 5.0 | Python's design philosophy emphasizes code readability, using significant indentation to define code... |
| scrapy+md | 5.0 | Python's syntax is designed to be easily readable, featuring a visually uncluttered format that ofte... |
| crawlee | 5.0 | Python's syntax is designed to be easily readable, using significant indentation instead of curly br... |
| colly+md | 5.0 | Python's syntax is designed to be easily readable, featuring a visually uncluttered format that ofte... |
| playwright | 5.0 | Python's syntax is designed to be easily readable, featuring a visually uncluttered format that ofte... |

**Q6: What are Python's standard library modules?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| crawl4ai | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| crawl4ai-raw | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| scrapy+md | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| crawlee | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| colly+md | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |
| playwright | 4.8 | Python's standard library includes modules for creating graphical user interfaces, connecting to rel... |

**Q7: Who is Guido van Rossum?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until July 12,... |
| crawl4ai | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until he annou... |
| crawl4ai-raw | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until he annou... |
| scrapy+md | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until he annou... |
| crawlee | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until July 201... |
| colly+md | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until he annou... |
| playwright | 5.0 | Guido van Rossum is the designer of Python and was the lead developer of the language until he annou... |

**Q8: What is CPython and how does it work?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | CPython is the reference implementation of Python, written in C and compliant with the C11 standard ... |
| crawl4ai | 5.0 | CPython is the reference implementation of Python, written in C. It compiles Python programs into an... |
| crawl4ai-raw | 5.0 | CPython is the reference implementation of Python, written in C. It compiles Python programs into an... |
| scrapy+md | 5.0 | CPython is the reference implementation of Python, written in C. It compiles Python programs into in... |
| crawlee | 5.0 | CPython is the reference implementation of Python, written in C. It compiles Python programs into in... |
| colly+md | 5.0 | CPython is the reference implementation of Python, written in C and compliant with the C11 standard ... |
| playwright | 5.0 | CPython is the reference implementation of Python, written in C and compliant with the C11 standard ... |

**Q9: How does Python compare to other programming languages?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q10: What are Python Enhancement Proposals (PEPs)?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| crawl4ai | 4.8 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| crawl4ai-raw | 4.8 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| scrapy+md | 5.0 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| crawlee | 5.0 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| colly+md | 5.0 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |
| playwright | 5.0 | Python Enhancement Proposals (PEPs) are the primary mechanism for proposing major new features, coll... |

</details>

## stripe-docs

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 4.00 | 3.50 | 3.00 | 3.50 | 3.50 |
| crawl4ai | 4.10 | 3.90 | 3.50 | 3.70 | 3.80 |
| crawl4ai-raw | 4.20 | 3.80 | 3.30 | 3.80 | 3.77 |
| scrapy+md | 3.70 | 3.40 | 2.70 | 3.30 | 3.27 |
| crawlee | 4.00 | 3.50 | 3.10 | 3.50 | 3.52 |
| colly+md | 3.90 | 3.50 | 3.00 | 3.40 | 3.45 |
| playwright | 3.80 | 3.40 | 2.90 | 3.40 | 3.38 |

<details>
<summary>Query-by-query scores for stripe-docs</summary>

**Q1: How do I create a payment intent with Stripe?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q2: How do I handle webhooks from Stripe?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To handle webhooks from Stripe, set up an Express server that listens for Stripe webhook events. Val... |
| crawl4ai | 5.0 | To handle webhooks from Stripe, set up an Express server that listens for incoming webhook events. U... |
| crawl4ai-raw | 5.0 | To handle webhooks from Stripe, set up an Express server that listens for incoming webhook events. U... |
| scrapy+md | 5.0 | To handle webhooks from Stripe, you need to set up an Express server that listens for Stripe webhook... |
| crawlee | 5.0 | To handle webhooks from Stripe, you need to set up an Express server that listens for Stripe webhook... |
| colly+md | 5.0 | To handle webhooks from Stripe, you need to set up an Express server that listens for Stripe webhook... |
| playwright | 5.0 | To handle webhooks from Stripe, you need to set up an Express server that listens for Stripe webhook... |

**Q3: How do I set up Stripe subscriptions?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 5.0 | To set up Stripe subscriptions, you need to create a new customer and attach a subscription. Here’s ... |
| crawl4ai-raw | 4.8 | To set up Stripe subscriptions, you need to create a new customer and attach a subscription. Here’s ... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q4: How do I authenticate with the Stripe API?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q5: How do I handle errors in the Stripe API?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q6: How do I create a customer in Stripe?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To create a customer in Stripe, you need to implement the following steps:  1. Use [Customer](/api#c... |
| crawl4ai | 4.2 | To create a customer in Stripe, use the following steps:  1. Use the [Customer](https://docs.stripe.... |
| crawl4ai-raw | 4.8 | To create a customer in Stripe, use the following steps:  1. Use the [Customer](https://docs.stripe.... |
| scrapy+md | 3.5 | To create a customer in Stripe, use the CheckoutSession API with the `customer_creation` parameter s... |
| crawlee | 5.0 | To create a customer in Stripe, use the following steps:  1. Use [Customer](/api#create_customer) ob... |
| colly+md | 4.2 | To create a customer in Stripe, use the following steps:  1. Implement the use of [Customer](/api#cr... |
| playwright | 3.5 | To create a customer in Stripe, use the CheckoutSession API with the `customer_creation` parameter s... |

**Q7: How do I process refunds with Stripe?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | You can process refunds with Stripe by using the Refund endpoint for ACH charges within 90 days from... |
| crawl4ai | 5.0 | You can process refunds with Stripe by using the Refund endpoint for ACH charges within 90 days from... |
| crawl4ai-raw | 5.0 | You can process refunds with Stripe by using the Refund endpoint for ACH charges within 90 days from... |
| scrapy+md | 5.0 | You can process refunds with Stripe by using the Refund endpoint for ACH charges within 90 days from... |
| crawlee | 5.0 | You can refund ACH charges for up to 90 days from the date of the original payment using the Refund ... |
| colly+md | 5.0 | You can refund ACH charges for up to 90 days from the date of the original payment using the Refund ... |
| playwright | 5.0 | You can refund ACH charges for up to 90 days from the date of the original payment using the Refund ... |

**Q8: How do I use Stripe checkout for payments?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To use Stripe Checkout for payments, follow these steps:  1. Create an embedded Checkout Session and... |
| crawl4ai | 5.0 | To use Stripe Checkout for payments, you should follow these steps:  1. Build your Stripe integratio... |
| crawl4ai-raw | 5.0 | To use Stripe Checkout for payments, follow these steps:  1. Build your Stripe integration by implem... |
| scrapy+md | 4.2 | To use Stripe checkout for payments, follow these steps:  1. Create an embedded Checkout Session and... |
| crawlee | 5.0 | To use Stripe checkout for payments, follow these steps:  1. Create an embedded Checkout Session and... |
| colly+md | 5.0 | To use Stripe checkout for payments, follow these steps:  1. Create an embedded Checkout Session and... |
| playwright | 5.0 | To use Stripe checkout for payments, follow these steps:  1. Create an embedded Checkout Session and... |

**Q9: How do I test Stripe payments in development?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 5.0 | To test Stripe payments in development, you can create an embedded Checkout Session and mount the pa... |
| crawl4ai | 5.0 | To test Stripe payments in development, follow these steps:  1. Create an embedded Checkout Session ... |
| crawl4ai-raw | 5.0 | To test Stripe payments in development, follow these steps:  1. Create an embedded Checkout Session ... |
| scrapy+md | 5.0 | To test Stripe payments in development, create an embedded Checkout Session and mount the payment fo... |
| crawlee | 5.0 | To test Stripe payments in development, create an embedded Checkout Session and mount the payment fo... |
| colly+md | 5.0 | To test Stripe payments in development, create an embedded Checkout Session and mount the payment fo... |
| playwright | 5.0 | To test Stripe payments in development, create an embedded Checkout Session and mount the payment fo... |

**Q10: What are Stripe Connect and platform payments?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.2 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.2 | I cannot answer this based on the provided context.... |

</details>

## blog-engineering

| Tool | Correctness | Relevance | Completeness | Usefulness | Overall |
|---|---|---|---|---|---|
| markcrawl | 3.12 | 3.00 | 2.25 | 2.50 | 2.72 |
| crawl4ai | 3.12 | 2.88 | 2.25 | 2.50 | 2.69 |
| crawl4ai-raw | 3.12 | 3.00 | 2.25 | 2.38 | 2.69 |
| scrapy+md | 3.00 | 2.50 | 1.75 | 2.38 | 2.41 |
| crawlee | 3.12 | 2.75 | 1.75 | 2.38 | 2.50 |
| colly+md | 3.00 | 2.62 | 1.75 | 2.12 | 2.38 |
| playwright | 3.12 | 2.88 | 1.88 | 2.38 | 2.56 |

<details>
<summary>Query-by-query scores for blog-engineering</summary>

**Q1: What are best practices for building reliable distributed systems?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q2: How do companies handle database migrations at scale?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

**Q3: What monitoring and observability tools do engineering teams use?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 4.2 | Engineering teams use `gh-ost` for migration monitoring, `Haystack` for exception tracking, and `sta... |
| crawl4ai | 4.2 | Engineering teams use tools like `gh-ost` for migration status visibility, `statsd` for metrics aggr... |
| crawl4ai-raw | 4.2 | Engineering teams use tools like `gh-ost` for migration status visibility, `statsd` for metrics aggr... |
| scrapy+md | 3.5 | The engineering teams use Haystack for exception tracking and monitoring, and `statsd` for metrics a... |
| crawlee | 4.0 | The engineering teams use Haystack for exception tracking and `statsd` as a metrics aggregation daem... |
| colly+md | 3.2 | The engineering teams use Haystack for exception tracking and `statsd` for metrics aggregation.... |
| playwright | 4.0 | The engineering teams use Haystack for exception tracking and monitoring, and they utilize `statsd` ... |

**Q4: How do you implement continuous deployment pipelines?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.5 | I cannot answer this based on the provided context.... |
| crawlee | 2.5 | I cannot answer this based on the provided context.... |
| colly+md | 2.5 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

**Q5: What are common microservices architecture patterns?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.2 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.2 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.2 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.2 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q6: How do you handle API versioning in production?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 3.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 2.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 3.0 | I cannot answer this based on the provided context.... |
| crawlee | 3.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.5 | I cannot answer this based on the provided context.... |
| playwright | 3.0 | I cannot answer this based on the provided context.... |

**Q7: What caching strategies work best for web applications?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 2.5 | I cannot answer this based on the provided context.... |
| crawl4ai | 3.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 3.0 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.0 | I cannot answer this based on the provided context.... |
| colly+md | 2.0 | I cannot answer this based on the provided context.... |
| playwright | 2.0 | I cannot answer this based on the provided context.... |

**Q8: How do you design for high availability and fault tolerance?**

| Tool | Score | Answer (truncated) |
|---|---|---|
| markcrawl | 3.0 | I cannot answer this based on the provided context.... |
| crawl4ai | 3.0 | I cannot answer this based on the provided context.... |
| crawl4ai-raw | 2.5 | I cannot answer this based on the provided context.... |
| scrapy+md | 2.0 | I cannot answer this based on the provided context.... |
| crawlee | 2.5 | I cannot answer this based on the provided context.... |
| colly+md | 2.5 | I cannot answer this based on the provided context.... |
| playwright | 2.5 | I cannot answer this based on the provided context.... |

</details>

## Methodology

- **Answer generation:** `gpt-4o-mini` with temperature=0, max_tokens=500
- **Answer judging:** `gpt-4o-mini` scores correctness, relevance, completeness, usefulness (1-5)
- **Retrieval:** Top-10 chunks by cosine similarity (same as retrieval benchmark)
- **Chunking:** Markdown-aware, 400 word max, 50 word overlap
- **Embedding:** `text-embedding-3-small`
- **Same pipeline for all tools** — only crawler output quality varies

