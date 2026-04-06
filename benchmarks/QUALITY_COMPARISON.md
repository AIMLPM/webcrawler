# Extraction Quality Comparison

## Methodology

Four automated quality metrics — no LLM or human review needed:

1. **Junk phrases** — known boilerplate strings (nav, footer, breadcrumbs) found in output
2. **Preamble [1]** — average words per page appearing *before* the first heading.
   Nav chrome (version selectors, language pickers, prev/next links) lives here.
   A tool with a high preamble count is injecting site chrome into every chunk.
3. **Cross-page repeat rate** — fraction of sentences that appear on >50% of pages.
   Real content appears on at most a few pages; nav text repeats everywhere.
   High repeat rate = nav boilerplate polluting every chunk in the RAG index.
4. **Cross-tool consensus** — precision (how much output is agreed real content?)
   and recall (how much agreed content did this tool capture?).

> **Why preamble + repeat rate matter for RAG:** A tool that embeds 200 words of
> nav chrome before each article degrades retrieval in two ways: (1) chunks contain
> irrelevant tokens that dilute semantic similarity, and (2) the same nav sentences
> match queries on every page, flooding results with false positives.

## Summary: RAG readiness at a glance

For RAG pipelines, **clean output matters more than comprehensive output.**
A tool that includes 1,000 words of nav chrome per page pollutes every
chunk in the vector index, degrading retrieval for every query.

| Tool | Content signal | Preamble [1] | Repeat rate | Junk/page | Precision | Recall |
|---|---|---|---|---|---|---|
| markcrawl | 100% | 4 | 0% | 0.4 | 99% | 84% |
| crawl4ai | 79% | 411 ⚠ | 2% | 1.1 | 99% | 85% |
| crawl4ai-raw | 79% | 409 ⚠ | 2% | 1.1 | 99% | 84% |
| scrapy+md | 87% | 225 ⚠ | 1% | 1.2 | 100% | 90% |
| crawlee | 84% | 284 ⚠ | 2% | 1.8 | 100% | 98% |
| colly+md | 85% | 275 ⚠ | 2% | 1.8 | 100% | 98% |
| playwright | 85% | 280 ⚠ | 2% | 1.8 | 100% | 98% |
| firecrawl | — | — | — | — | — | — |

**[1]** Avg words per page before the first heading (nav chrome).


**Key takeaway:** markcrawl achieves 100% content signal with only 4 words of preamble per page — compared to 411 for crawl4ai. Its recall is lower (84% vs 98%) because it strips nav, footer, and sponsor content that other tools include. For RAG use cases, this trade-off favors markcrawl: every chunk in the vector index is pure content, with no boilerplate to dilute embeddings or pollute retrieval results.

> **Content signal** = percentage of output that is content (not preamble nav chrome).
> Higher is better. A tool with 100% content signal has zero nav/header pollution.
> **Repeat rate** = fraction of phrases appearing on >50% of pages (boilerplate).
> **Junk/page** = known boilerplate phrases detected per page.

## quotes-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 228 | 0 | 1% | 2 | 2.6 | 0.0 | 100% | 96% |
| crawl4ai | 237 | 0 | 3% | 2 | 2.6 | 0.0 | 100% | 96% |
| crawl4ai-raw | 237 | 0 | 3% | 2 | 2.6 | 0.0 | 100% | 96% |
| scrapy+md | 237 | 0 | 3% | 2 | 2.6 | 0.0 | 100% | 96% |
| crawlee | 261 | 3 | 2% | 3 | 2.6 | 0.0 | 100% | 100% |
| colly+md | 261 | 3 | 2% | 3 | 2.6 | 0.0 | 100% | 100% |
| playwright | 261 | 3 | 2% | 3 | 2.6 | 0.0 | 100% | 100% |
| firecrawl | — | — | — | — | — | — | — | — |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

<details>
<summary>Sample output — first 40 lines of <code>quotes.toscrape.com/author/Jane-Austen</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# [Quotes to Scrape](/)

[Login](/login)

### Jane Austen

**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom

**Description:**

Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture.
```

**crawl4ai**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
### Jane Austen
**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom
**Description:**
Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture. 
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**crawl4ai-raw**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
### Jane Austen
**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom
**Description:**
Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture. 
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**scrapy+md**
```
# [Quotes to Scrape](/)

[Login](/login)

### Jane Austen

**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom

**Description:**

Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture.

Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)

Made with ❤ by [Zyte](https://www.zyte.com)
```

**crawlee**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Jane Austen

**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom

**Description:**

Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture.

Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)

Made with ❤ by [Zyte](https://www.zyte.com)
```

**colly+md**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Jane Austen

**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom

**Description:**

Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture.

Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)

Made with ❤ by [Zyte](https://www.zyte.com)
```

**playwright**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Jane Austen

**Born:** December 16, 1775 in Steventon Rectory, Hampshire, The United Kingdom

**Description:**

Jane Austen was an English novelist whose works of romantic fiction, set among the landed gentry, earned her a place as one of the most widely read writers in English literature, her realism and biting social commentary cementing her historical importance among scholars and critics.Austen lived her entire life as part of a close-knit family located on the lower fringes of the English landed gentry. She was educated primarily by her father and older brothers as well as through her own reading. The steadfast support of her family was critical to her development as a professional writer. Her artistic apprenticeship lasted from her teenage years until she was about 35 years old. During this period, she experimented with various literary forms, including the epistolary novel which she tried then abandoned, and wrote and extensively revised three major novels and began a fourth. From 1811 until 1816, with the release of Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814) and Emma (1815), she achieved success as a published writer. She wrote two additional novels, Northanger Abbey and Persuasion, both published posthumously in 1818, and began a third, which was eventually titled Sanditon, but died before completing it.Austen's works critique the novels of sensibility of the second half of the 18th century and are part of the transition to 19th-century realism. Her plots, though fundamentally comic, highlight the dependence of women on marriage to secure social standing and economic security. Her work brought her little personal fame and only a few positive reviews during her lifetime, but the publication in 1869 of her nephew's A Memoir of Jane Austen introduced her to a wider public, and by the 1940s she had become widely accepted in academia as a great English writer. The second half of the 20th century saw a proliferation of Austen scholarship and the emergence of a Janeite fan culture.

Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)

Made with ❤ by [Zyte](https://www.zyte.com)
```

**firecrawl** — no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| quotes.toscrape.com | 271 / 0 | 282 / 0 | 282 / 0 | 282 / 0 | 285 / 3 | 285 / 3 | 285 / 3 | — |
| quotes.toscrape.com/author/Andre-Gide | 173 / 0 | 181 / 0 | 181 / 0 | 181 / 0 | 184 / 3 | 184 / 3 | 184 / 3 | — |
| quotes.toscrape.com/author/Jane-Austen | 333 / 0 | 341 / 0 | 341 / 0 | 341 / 0 | 344 / 3 | 344 / 3 | 344 / 3 | — |
| quotes.toscrape.com/author/Steve-Martin | 139 / 0 | 147 / 0 | 147 / 0 | 147 / 0 | 150 / 3 | 150 / 3 | 150 / 3 | — |
| quotes.toscrape.com/author/Thomas-A-Edison | 201 / 0 | 209 / 0 | 209 / 0 | 209 / 0 | 212 / 3 | 212 / 3 | 212 / 3 | — |
| quotes.toscrape.com/page/2 | 600 / 0 | 614 / 0 | 614 / 0 | 614 / 0 | 725 / 3 | 725 / 3 | 725 / 3 | — |
| quotes.toscrape.com/tag/be-yourself/page/1 | 46 / 0 | 54 / 0 | 54 / 0 | 54 / 0 | 57 / 3 | 57 / 3 | 57 / 3 | — |
| quotes.toscrape.com/tag/friendship | 158 / 0 | 166 / 0 | 166 / 0 | 166 / 0 | 169 / 3 | 169 / 3 | 169 / 3 | — |
| quotes.toscrape.com/tag/inspirational/page/1 | 484 / 0 | 495 / 0 | 495 / 0 | 495 / 0 | 606 / 3 | 606 / 3 | 606 / 3 | — |
| quotes.toscrape.com/tag/life/page/1 | 498 / 0 | 509 / 0 | 509 / 0 | 509 / 0 | 620 / 3 | 620 / 3 | 620 / 3 | — |
| quotes.toscrape.com/tag/live/page/1 | 59 / 0 | 67 / 0 | 67 / 0 | 67 / 0 | 70 / 3 | 70 / 3 | 70 / 3 | — |
| quotes.toscrape.com/tag/paraphrased/page/1 | 69 / 0 | 77 / 0 | 77 / 0 | 77 / 0 | 80 / 3 | 80 / 3 | 80 / 3 | — |
| quotes.toscrape.com/tag/reading | 247 / 0 | 255 / 0 | 255 / 0 | 255 / 0 | 258 / 3 | 258 / 3 | 258 / 3 | — |
| quotes.toscrape.com/tag/thinking/page/1 | 85 / 0 | 93 / 0 | 93 / 0 | 93 / 0 | 96 / 3 | 96 / 3 | 96 / 3 | — |
| quotes.toscrape.com/tag/world/page/1 | 53 / 0 | 61 / 0 | 61 / 0 | 61 / 0 | 64 / 3 | 64 / 3 | 64 / 3 | — |

</details>

## books-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 291 | 8 | 0% | 0 | 1.9 | 0.0 | 98% | 90% |
| crawl4ai | 491 | 170 ⚠ | 2% | 0 | 10.5 | 0.0 | 96% | 92% |
| crawl4ai-raw | 493 | 171 ⚠ | 2% | 0 | 10.6 | 0.0 | 96% | 92% |
| scrapy+md | 389 | 98 ⚠ | 1% | 0 | 1.9 | 0.0 | 100% | 92% |
| crawlee | 418 | 107 ⚠ | 1% | 11 | 1.9 | 0.0 | 100% | 100% |
| colly+md | 418 | 107 ⚠ | 1% | 11 | 1.9 | 0.0 | 100% | 100% |
| playwright | 418 | 107 ⚠ | 1% | 11 | 1.9 | 0.0 | 100% | 100% |
| firecrawl | — | — | — | — | — | — | — | — |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**markcrawl** produces the cleanest output with 8 words of preamble per page, while **crawl4ai-raw** injects 171 words of nav chrome before content begins. The word count gap (291 vs 493 avg words) is largely explained by preamble: 171 words of nav chrome account for ~35% of crawl4ai-raw's output on this site. markcrawl's lower recall (90% vs 100%) reflects stricter content filtering — the "missed" sentences are predominantly navigation, sponsor links, and footer text that other tools include as content. For RAG, this is a net positive: fewer junk tokens per chunk means better embedding quality and retrieval precision.

<details>
<summary>Sample output — first 40 lines of <code>books.toscrape.com/catalogue/category/books/romance_8/index.html</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Romance

# Romance

**35** results - showing **1** to **20**.

**Warning!** This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning.

1. ### [Chase Me (Paris Nights ...](../../../chase-me-paris-nights-2_977/index.html "Chase Me (Paris Nights #2)")

   Â£25.27

   In stock

   Add to basket
2. ### [Black Dust](../../../black-dust_976/index.html "Black Dust")

   Â£34.53

   In stock

   Add to basket
3. ### [Her Backup Boyfriend (The ...](../../../her-backup-boyfriend-the-sorensen-family-1_896/index.html "Her Backup Boyfriend (The Sorensen Family #1)")

   Â£33.97

   In stock

   Add to basket
4. ### [First and First (Five ...](../../../first-and-first-five-boroughs-3_893/index.html "First and First (Five Boroughs #3)")

   Â£15.97

   In stock

   Add to basket
5. ### [Fifty Shades Darker (Fifty ...](../../../fifty-shades-darker-fifty-shades-2_892/index.html "Fifty Shades Darker (Fifty Shades #2)")
```

**crawl4ai**
```
[Books to Scrape](http://books.toscrape.com/index.html) We love being scraped!
  * [Home](http://books.toscrape.com/index.html)
  * [Books](http://books.toscrape.com/catalogue/category/books_1/index.html)
  * Romance


  * [ Books ](http://books.toscrape.com/catalogue/category/books_1/index.html)
    * [ Travel ](http://books.toscrape.com/catalogue/category/books/travel_2/index.html)
    * [ Mystery ](http://books.toscrape.com/catalogue/category/books/mystery_3/index.html)
    * [ Historical Fiction ](http://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html)
    * [ Sequential Art ](http://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html)
    * [ Classics ](http://books.toscrape.com/catalogue/category/books/classics_6/index.html)
    * [ Philosophy ](http://books.toscrape.com/catalogue/category/books/philosophy_7/index.html)
    * [ **Romance** ](http://books.toscrape.com/catalogue/category/books/romance_8/index.html)
    * [ Womens Fiction ](http://books.toscrape.com/catalogue/category/books/womens-fiction_9/index.html)
    * [ Fiction ](http://books.toscrape.com/catalogue/category/books/fiction_10/index.html)
    * [ Childrens ](http://books.toscrape.com/catalogue/category/books/childrens_11/index.html)
    * [ Religion ](http://books.toscrape.com/catalogue/category/books/religion_12/index.html)
    * [ Nonfiction ](http://books.toscrape.com/catalogue/category/books/nonfiction_13/index.html)
    * [ Music ](http://books.toscrape.com/catalogue/category/books/music_14/index.html)
    * [ Default ](http://books.toscrape.com/catalogue/category/books/default_15/index.html)
    * [ Science Fiction ](http://books.toscrape.com/catalogue/category/books/science-fiction_16/index.html)
    * [ Sports and Games ](http://books.toscrape.com/catalogue/category/books/sports-and-games_17/index.html)
    * [ Add a comment ](http://books.toscrape.com/catalogue/category/books/add-a-comment_18/index.html)
    * [ Fantasy ](http://books.toscrape.com/catalogue/category/books/fantasy_19/index.html)
    * [ New Adult ](http://books.toscrape.com/catalogue/category/books/new-adult_20/index.html)
    * [ Young Adult ](http://books.toscrape.com/catalogue/category/books/young-adult_21/index.html)
    * [ Science ](http://books.toscrape.com/catalogue/category/books/science_22/index.html)
    * [ Poetry ](http://books.toscrape.com/catalogue/category/books/poetry_23/index.html)
    * [ Paranormal ](http://books.toscrape.com/catalogue/category/books/paranormal_24/index.html)
    * [ Art ](http://books.toscrape.com/catalogue/category/books/art_25/index.html)
    * [ Psychology ](http://books.toscrape.com/catalogue/category/books/psychology_26/index.html)
    * [ Autobiography ](http://books.toscrape.com/catalogue/category/books/autobiography_27/index.html)
    * [ Parenting ](http://books.toscrape.com/catalogue/category/books/parenting_28/index.html)
    * [ Adult Fiction ](http://books.toscrape.com/catalogue/category/books/adult-fiction_29/index.html)
    * [ Humor ](http://books.toscrape.com/catalogue/category/books/humor_30/index.html)
    * [ Horror ](http://books.toscrape.com/catalogue/category/books/horror_31/index.html)
    * [ History ](http://books.toscrape.com/catalogue/category/books/history_32/index.html)
    * [ Food and Drink ](http://books.toscrape.com/catalogue/category/books/food-and-drink_33/index.html)
    * [ Christian Fiction ](http://books.toscrape.com/catalogue/category/books/christian-fiction_34/index.html)
```

**crawl4ai-raw**
```
[Books to Scrape](https://books.toscrape.com/index.html) We love being scraped!
  * [Home](https://books.toscrape.com/index.html)
  * [Books](https://books.toscrape.com/catalogue/category/books_1/index.html)
  * Romance


  * [ Books ](https://books.toscrape.com/catalogue/category/books_1/index.html)
    * [ Travel ](https://books.toscrape.com/catalogue/category/books/travel_2/index.html)
    * [ Mystery ](https://books.toscrape.com/catalogue/category/books/mystery_3/index.html)
    * [ Historical Fiction ](https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html)
    * [ Sequential Art ](https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html)
    * [ Classics ](https://books.toscrape.com/catalogue/category/books/classics_6/index.html)
    * [ Philosophy ](https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html)
    * [ **Romance** ](https://books.toscrape.com/catalogue/category/books/romance_8/index.html)
    * [ Womens Fiction ](https://books.toscrape.com/catalogue/category/books/womens-fiction_9/index.html)
    * [ Fiction ](https://books.toscrape.com/catalogue/category/books/fiction_10/index.html)
    * [ Childrens ](https://books.toscrape.com/catalogue/category/books/childrens_11/index.html)
    * [ Religion ](https://books.toscrape.com/catalogue/category/books/religion_12/index.html)
    * [ Nonfiction ](https://books.toscrape.com/catalogue/category/books/nonfiction_13/index.html)
    * [ Music ](https://books.toscrape.com/catalogue/category/books/music_14/index.html)
    * [ Default ](https://books.toscrape.com/catalogue/category/books/default_15/index.html)
    * [ Science Fiction ](https://books.toscrape.com/catalogue/category/books/science-fiction_16/index.html)
    * [ Sports and Games ](https://books.toscrape.com/catalogue/category/books/sports-and-games_17/index.html)
    * [ Add a comment ](https://books.toscrape.com/catalogue/category/books/add-a-comment_18/index.html)
    * [ Fantasy ](https://books.toscrape.com/catalogue/category/books/fantasy_19/index.html)
    * [ New Adult ](https://books.toscrape.com/catalogue/category/books/new-adult_20/index.html)
    * [ Young Adult ](https://books.toscrape.com/catalogue/category/books/young-adult_21/index.html)
    * [ Science ](https://books.toscrape.com/catalogue/category/books/science_22/index.html)
    * [ Poetry ](https://books.toscrape.com/catalogue/category/books/poetry_23/index.html)
    * [ Paranormal ](https://books.toscrape.com/catalogue/category/books/paranormal_24/index.html)
    * [ Art ](https://books.toscrape.com/catalogue/category/books/art_25/index.html)
    * [ Psychology ](https://books.toscrape.com/catalogue/category/books/psychology_26/index.html)
    * [ Autobiography ](https://books.toscrape.com/catalogue/category/books/autobiography_27/index.html)
    * [ Parenting ](https://books.toscrape.com/catalogue/category/books/parenting_28/index.html)
    * [ Adult Fiction ](https://books.toscrape.com/catalogue/category/books/adult-fiction_29/index.html)
    * [ Humor ](https://books.toscrape.com/catalogue/category/books/humor_30/index.html)
    * [ Horror ](https://books.toscrape.com/catalogue/category/books/horror_31/index.html)
    * [ History ](https://books.toscrape.com/catalogue/category/books/history_32/index.html)
    * [ Food and Drink ](https://books.toscrape.com/catalogue/category/books/food-and-drink_33/index.html)
    * [ Christian Fiction ](https://books.toscrape.com/catalogue/category/books/christian-fiction_34/index.html)
```

**scrapy+md**
```
[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Romance

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [**Romance**](index.html)
  + [Womens Fiction](../womens-fiction_9/index.html)
  + [Fiction](../fiction_10/index.html)
  + [Childrens](../childrens_11/index.html)
  + [Religion](../religion_12/index.html)
  + [Nonfiction](../nonfiction_13/index.html)
  + [Music](../music_14/index.html)
  + [Default](../default_15/index.html)
  + [Science Fiction](../science-fiction_16/index.html)
  + [Sports and Games](../sports-and-games_17/index.html)
  + [Add a comment](../add-a-comment_18/index.html)
  + [Fantasy](../fantasy_19/index.html)
  + [New Adult](../new-adult_20/index.html)
  + [Young Adult](../young-adult_21/index.html)
  + [Science](../science_22/index.html)
  + [Poetry](../poetry_23/index.html)
  + [Paranormal](../paranormal_24/index.html)
  + [Art](../art_25/index.html)
  + [Psychology](../psychology_26/index.html)
  + [Autobiography](../autobiography_27/index.html)
  + [Parenting](../parenting_28/index.html)
  + [Adult Fiction](../adult-fiction_29/index.html)
  + [Humor](../humor_30/index.html)
  + [Horror](../horror_31/index.html)
  + [History](../history_32/index.html)
  + [Food and Drink](../food-and-drink_33/index.html)
  + [Christian Fiction](../christian-fiction_34/index.html)
```

**crawlee**
```
Romance |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Romance

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [**Romance**](index.html)
  + [Womens Fiction](../womens-fiction_9/index.html)
  + [Fiction](../fiction_10/index.html)
  + [Childrens](../childrens_11/index.html)
  + [Religion](../religion_12/index.html)
  + [Nonfiction](../nonfiction_13/index.html)
  + [Music](../music_14/index.html)
  + [Default](../default_15/index.html)
  + [Science Fiction](../science-fiction_16/index.html)
  + [Sports and Games](../sports-and-games_17/index.html)
  + [Add a comment](../add-a-comment_18/index.html)
  + [Fantasy](../fantasy_19/index.html)
  + [New Adult](../new-adult_20/index.html)
  + [Young Adult](../young-adult_21/index.html)
  + [Science](../science_22/index.html)
  + [Poetry](../poetry_23/index.html)
  + [Paranormal](../paranormal_24/index.html)
  + [Art](../art_25/index.html)
  + [Psychology](../psychology_26/index.html)
  + [Autobiography](../autobiography_27/index.html)
  + [Parenting](../parenting_28/index.html)
```

**colly+md**
```
  


Romance |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Romance

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [**Romance**](index.html)
  + [Womens Fiction](../womens-fiction_9/index.html)
  + [Fiction](../fiction_10/index.html)
  + [Childrens](../childrens_11/index.html)
  + [Religion](../religion_12/index.html)
  + [Nonfiction](../nonfiction_13/index.html)
  + [Music](../music_14/index.html)
  + [Default](../default_15/index.html)
  + [Science Fiction](../science-fiction_16/index.html)
  + [Sports and Games](../sports-and-games_17/index.html)
  + [Add a comment](../add-a-comment_18/index.html)
  + [Fantasy](../fantasy_19/index.html)
  + [New Adult](../new-adult_20/index.html)
  + [Young Adult](../young-adult_21/index.html)
  + [Science](../science_22/index.html)
  + [Poetry](../poetry_23/index.html)
  + [Paranormal](../paranormal_24/index.html)
  + [Art](../art_25/index.html)
```

**playwright**
```
Romance |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Romance

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [**Romance**](index.html)
  + [Womens Fiction](../womens-fiction_9/index.html)
  + [Fiction](../fiction_10/index.html)
  + [Childrens](../childrens_11/index.html)
  + [Religion](../religion_12/index.html)
  + [Nonfiction](../nonfiction_13/index.html)
  + [Music](../music_14/index.html)
  + [Default](../default_15/index.html)
  + [Science Fiction](../science-fiction_16/index.html)
  + [Sports and Games](../sports-and-games_17/index.html)
  + [Add a comment](../add-a-comment_18/index.html)
  + [Fantasy](../fantasy_19/index.html)
  + [New Adult](../new-adult_20/index.html)
  + [Young Adult](../young-adult_21/index.html)
  + [Science](../science_22/index.html)
  + [Poetry](../poetry_23/index.html)
  + [Paranormal](../paranormal_24/index.html)
  + [Art](../art_25/index.html)
  + [Psychology](../psychology_26/index.html)
  + [Autobiography](../autobiography_27/index.html)
  + [Parenting](../parenting_28/index.html)
```

**firecrawl** — no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| books.toscrape.com | 397 / 5 | 702 / 232 | 702 / 232 | 531 / 130 | 539 / 138 | 539 / 138 | 539 / 138 | — |
| books.toscrape.com/catalogue/a-light-in-the-attic_1000/ | 269 / 12 | 276 / 24 | 276 / 24 | 284 / 19 | 295 / 30 | 295 / 30 | 295 / 30 | — |
| books.toscrape.com/catalogue/category/books/academic_40 | 51 / 6 | 282 / 233 | 282 / 233 | 185 / 131 | 192 / 138 | 192 / 138 | 192 / 138 | — |
| books.toscrape.com/catalogue/category/books/add-a-comme | 424 / 8 | 745 / 235 | 745 / 235 | 558 / 133 | 567 / 142 | 567 / 142 | 567 / 142 | — |
| books.toscrape.com/catalogue/category/books/adult-ficti | 53 / 7 | 284 / 234 | 284 / 234 | 187 / 132 | 195 / 140 | 195 / 140 | 195 / 140 | — |
| books.toscrape.com/catalogue/category/books/art_25/inde | 169 / 6 | 422 / 233 | 422 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | — |
| books.toscrape.com/catalogue/category/books/autobiograp | 169 / 6 | 412 / 233 | 412 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | — |
| books.toscrape.com/catalogue/category/books/biography_3 | 145 / 6 | 410 / 233 | 410 / 233 | 279 / 131 | 286 / 138 | 286 / 138 | 286 / 138 | — |
| books.toscrape.com/catalogue/category/books/business_35 | 296 / 6 | 612 / 233 | 612 / 233 | 430 / 131 | 437 / 138 | 437 / 138 | 437 / 138 | — |
| books.toscrape.com/catalogue/category/books/christian-f | 140 / 7 | 388 / 234 | 388 / 234 | 274 / 132 | 390 / 140 | 390 / 140 | 390 / 140 | — |
| books.toscrape.com/catalogue/category/books/christian_4 | 96 / 6 | 342 / 233 | 342 / 233 | 230 / 131 | 345 / 138 | 345 / 138 | 345 / 138 | — |
| books.toscrape.com/catalogue/category/books/contemporar | 84 / 6 | 320 / 233 | 320 / 233 | 218 / 131 | 333 / 138 | 333 / 138 | 333 / 138 | — |
| books.toscrape.com/catalogue/category/books/crime_51/in | 58 / 6 | 296 / 233 | 296 / 233 | 192 / 131 | 307 / 138 | 307 / 138 | 307 / 138 | — |
| books.toscrape.com/catalogue/category/books/cultural_49 | 46 / 6 | 274 / 233 | 274 / 233 | 180 / 131 | 187 / 138 | 187 / 138 | 187 / 138 | — |
| books.toscrape.com/catalogue/category/books/erotica_50/ | 44 / 6 | 271 / 233 | 271 / 233 | 178 / 131 | 185 / 138 | 185 / 138 | 185 / 138 | — |
| books.toscrape.com/catalogue/category/books/fiction_10/ | 365 / 6 | — | 636 / 233 | 499 / 131 | 614 / 138 | 614 / 138 | 614 / 138 | — |
| books.toscrape.com/catalogue/category/books/food-and-dr | 548 / 8 | 978 / 235 | 978 / 235 | 682 / 133 | 691 / 142 | 691 / 142 | 691 / 142 | — |
| books.toscrape.com/catalogue/category/books/historical- | 391 / 7 | 681 / 234 | 681 / 234 | 525 / 132 | 533 / 140 | 533 / 140 | 533 / 140 | — |
| books.toscrape.com/catalogue/category/books/historical_ | 75 / 6 | 315 / 233 | 315 / 233 | 209 / 131 | 216 / 138 | 216 / 138 | 216 / 138 | — |
| books.toscrape.com/catalogue/category/books/history_32/ | 447 / 6 | 822 / 233 | 822 / 233 | 581 / 131 | 696 / 138 | 696 / 138 | 696 / 138 | — |
| books.toscrape.com/catalogue/category/books/horror_31/i | 275 / 6 | 524 / 233 | 524 / 233 | 409 / 131 | 416 / 138 | 416 / 138 | 416 / 138 | — |
| books.toscrape.com/catalogue/category/books/humor_30/in | 239 / 6 | 529 / 233 | 529 / 233 | 373 / 131 | 488 / 138 | 488 / 138 | 488 / 138 | — |
| books.toscrape.com/catalogue/category/books/music_14/in | 304 / 6 | 616 / 233 | 616 / 233 | 438 / 131 | 445 / 138 | 445 / 138 | 445 / 138 | — |
| books.toscrape.com/catalogue/category/books/mystery_3/i | 407 / 6 | 710 / 233 | 710 / 233 | 541 / 131 | 548 / 138 | 548 / 138 | 548 / 138 | — |
| books.toscrape.com/catalogue/category/books/paranormal_ | 52 / 6 | 284 / 233 | 284 / 233 | 186 / 131 | 193 / 138 | 193 / 138 | 193 / 138 | — |
| books.toscrape.com/catalogue/category/books/parenting_2 | 53 / 6 | 286 / 233 | 286 / 233 | 187 / 131 | 194 / 138 | 194 / 138 | 194 / 138 | — |
| books.toscrape.com/catalogue/category/books/poetry_23/i | 355 / 6 | 642 / 233 | 642 / 233 | 489 / 131 | 496 / 138 | 496 / 138 | 496 / 138 | — |
| books.toscrape.com/catalogue/category/books/politics_48 | 94 / 6 | 340 / 233 | 340 / 233 | 228 / 131 | 235 / 138 | 235 / 138 | 235 / 138 | — |
| books.toscrape.com/catalogue/category/books/psychology_ | 184 / 6 | 460 / 233 | 460 / 233 | 318 / 131 | 325 / 138 | 325 / 138 | 325 / 138 | — |
| books.toscrape.com/catalogue/category/books/religion_12 | 180 / 6 | 453 / 233 | 453 / 233 | 314 / 131 | 321 / 138 | 321 / 138 | 321 / 138 | — |
| books.toscrape.com/catalogue/category/books/romance_8/i | 412 / 6 | 716 / 233 | 716 / 233 | 546 / 131 | 553 / 138 | 553 / 138 | 553 / 138 | — |
| books.toscrape.com/catalogue/category/books/science-fic | 322 / 7 | 615 / 234 | 615 / 234 | 456 / 132 | 464 / 140 | 464 / 140 | 464 / 140 | — |
| books.toscrape.com/catalogue/category/books/science_22/ | 350 / 6 | 690 / 233 | 690 / 233 | 484 / 131 | 491 / 138 | 491 / 138 | 491 / 138 | — |
| books.toscrape.com/catalogue/category/books/self-help_4 | 152 / 7 | 422 / 234 | 422 / 234 | 286 / 132 | 294 / 140 | 294 / 140 | 294 / 140 | — |
| books.toscrape.com/catalogue/category/books/sequential- | 441 / 7 | 774 / 234 | 774 / 234 | 575 / 132 | 583 / 140 | 583 / 140 | 583 / 140 | — |
| books.toscrape.com/catalogue/category/books/short-stori | 46 / 7 | 273 / 234 | 273 / 234 | 180 / 132 | 188 / 140 | 188 / 140 | 188 / 140 | — |
| books.toscrape.com/catalogue/category/books/spiritualit | 171 / 6 | 447 / 233 | 447 / 233 | 305 / 131 | 312 / 138 | 312 / 138 | 312 / 138 | — |
| books.toscrape.com/catalogue/category/books/sports-and- | 137 / 8 | 391 / 235 | 391 / 235 | 271 / 133 | 280 / 142 | 280 / 142 | 280 / 142 | — |
| books.toscrape.com/catalogue/category/books/thriller_37 | 211 / 6 | 465 / 233 | 465 / 233 | 345 / 131 | 352 / 138 | 352 / 138 | 352 / 138 | — |
| books.toscrape.com/catalogue/category/books/travel_2/in | 258 / 6 | 550 / 233 | 550 / 233 | 392 / 131 | 399 / 138 | 399 / 138 | 399 / 138 | — |
| books.toscrape.com/catalogue/category/books/womens-fict | 330 / 7 | 614 / 234 | 614 / 234 | 464 / 132 | 472 / 140 | 472 / 140 | 472 / 140 | — |
| books.toscrape.com/catalogue/category/books_1/index.htm | 395 / 4 | 700 / 231 | 700 / 231 | 529 / 129 | 644 / 136 | 644 / 136 | 644 / 136 | — |
| books.toscrape.com/catalogue/its-only-the-himalayas_981 | 448 / 11 | 480 / 22 | 480 / 22 | 463 / 18 | 473 / 28 | 473 / 28 | 473 / 28 | — |
| books.toscrape.com/catalogue/libertarianism-for-beginne | 411 / 10 | 442 / 20 | 442 / 20 | 426 / 17 | 435 / 26 | 435 / 26 | 435 / 26 | — |
| books.toscrape.com/catalogue/mesaerion-the-best-science | 500 / 15 | 530 / 29 | 530 / 29 | 515 / 22 | 528 / 35 | 528 / 35 | 528 / 35 | — |
| books.toscrape.com/catalogue/olio_984/index.html | 462 / 8 | 491 / 16 | 491 / 16 | 477 / 15 | 484 / 22 | 484 / 22 | 484 / 22 | — |
| books.toscrape.com/catalogue/our-band-could-be-your-lif | 388 / 20 | 419 / 40 | 419 / 40 | 403 / 27 | 422 / 46 | 422 / 46 | 422 / 46 | — |
| books.toscrape.com/catalogue/page-2.html | 413 / 5 | 726 / 232 | 726 / 232 | 547 / 130 | 555 / 138 | 555 / 138 | 555 / 138 | — |
| books.toscrape.com/catalogue/rip-it-up-and-start-again_ | 371 / 13 | 407 / 26 | 407 / 26 | 386 / 20 | 398 / 32 | 398 / 32 | 398 / 32 | — |
| books.toscrape.com/catalogue/sapiens-a-brief-history-of | 470 / 13 | 481 / 26 | 481 / 26 | 485 / 20 | 605 / 32 | 605 / 32 | 605 / 32 | — |
| books.toscrape.com/catalogue/scott-pilgrims-precious-li | 383 / 16 | 428 / 31 | 428 / 31 | 398 / 23 | 412 / 37 | 412 / 37 | 412 / 37 | — |
| books.toscrape.com/catalogue/set-me-free_988/index.html | 365 / 11 | 411 / 21 | 411 / 21 | 380 / 18 | 389 / 27 | 389 / 27 | 389 / 27 | — |
| books.toscrape.com/catalogue/shakespeares-sonnets_989/i | 375 / 9 | 421 / 18 | 421 / 18 | 390 / 16 | 398 / 24 | 398 / 24 | 398 / 24 | — |
| books.toscrape.com/catalogue/soumission_998/index.html | 297 / 8 | 304 / 16 | 304 / 16 | 312 / 15 | 319 / 22 | 319 / 22 | 319 / 22 | — |
| books.toscrape.com/catalogue/starving-hearts-triangular | 436 / 13 | 486 / 26 | 486 / 26 | 451 / 20 | 463 / 32 | 463 / 32 | 463 / 32 | — |
| books.toscrape.com/catalogue/the-boys-in-the-boat-nine- | 576 / 25 | 620 / 50 | 620 / 50 | 591 / 32 | 615 / 56 | 615 / 56 | 615 / 56 | — |
| books.toscrape.com/catalogue/the-coming-woman-a-novel-b | 789 / 22 | 818 / 44 | 818 / 44 | 804 / 29 | 825 / 50 | 825 / 50 | 825 / 50 | — |
| books.toscrape.com/catalogue/the-dirty-little-secrets-o | 489 / 16 | 508 / 32 | 508 / 32 | 504 / 23 | 627 / 38 | 627 / 38 | 627 / 38 | — |
| books.toscrape.com/catalogue/the-requiem-red_995/index. | 350 / 11 | 362 / 21 | 362 / 21 | 365 / 18 | 374 / 27 | 374 / 27 | 374 / 27 | — |
| books.toscrape.com/catalogue/tipping-the-velvet_999/ind | 290 / 11 | 298 / 21 | 298 / 21 | 305 / 18 | 422 / 27 | 422 / 27 | 422 / 27 | — |

</details>

## fastapi-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 3835 | 0 | 0% | 29 | 33.1 | 28.7 | 100% | 73% |
| crawl4ai | 5424 | 1502 ⚠ | 4% | 29 | 32.8 | 28.7 | 100% | 92% |
| crawl4ai-raw | 5415 | 1502 ⚠ | 4% | 29 | 32.8 | 28.6 | 100% | 92% |
| scrapy+md | 4676 | 824 ⚠ | 2% | 50 | 33.1 | 28.7 | 100% | 73% |
| crawlee | 4965 | 1064 ⚠ | 3% | 99 | 32.8 | 28.4 | 100% | 96% |
| colly+md | 5000 | 1046 ⚠ | 3% | 99 | 33.1 | 28.7 | 100% | 97% |
| playwright | 4975 | 1046 ⚠ | 3% | 99 | 32.8 | 28.7 | 100% | 97% |
| firecrawl | — | — | — | — | — | — | — | — |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**markcrawl** produces the cleanest output with 0 word of preamble per page, while **crawl4ai-raw** injects 1502 words of nav chrome before content begins. The word count gap (3835 vs 5424 avg words) is largely explained by preamble: 1502 words of nav chrome account for ~28% of crawl4ai's output on this site. markcrawl's lower recall (73% vs 97%) reflects stricter content filtering — the "missed" sentences are predominantly navigation, sponsor links, and footer text that other tools include as content. For RAG, this is a net positive: fewer junk tokens per chunk means better embedding quality and retrieval precision.

<details>
<summary>Sample output — first 40 lines of <code>fastapi.tiangolo.com/tutorial/request-forms-and-files</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# Request Forms and Files[¶](#request-forms-and-files "Permanent link")

You can define files and form fields at the same time using `File` and `Form`.

Info

To receive uploaded files and/or form data, first install [`python-multipart`](https://github.com/Kludex/python-multipart).

Make sure you create a [virtual environment](../../virtual-environments/), activate it, and then install it, for example:

```False
$ pip install python-multipart
```

## Import `File` and `Form`[¶](#import-file-and-form "Permanent link")

Python 3.10+

```False
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()],
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }
```

🤓 Other versions and variants
```

**crawl4ai**
```
[ Skip to content ](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#request-forms-and-files)
[ **FastAPI Cloud** waiting list 🚀 ](https://fastapicloud.com)
[ Follow **@fastapi** on **X (Twitter)** to stay updated ](https://x.com/fastapi)
[ Follow **FastAPI** on **LinkedIn** to stay updated ](https://www.linkedin.com/company/fastapi)
[ **FastAPI and friends** newsletter 🎉 ](https://fastapi.tiangolo.com/newsletter/)
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/blockbee-banner.png) ](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/scalar-banner.svg) ](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/propelauth-banner.png) ](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/zuplo-banner.png) ](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/liblab-banner.png) ](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from FastAPI")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/render-banner.svg) ](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/coderabbit-banner.png) ](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/subtotal-banner.svg) ](https://subtotal.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=open-source "Making Retail Purchases Actionable for Brands and Developers")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/railway-banner.png) ](https://docs.railway.com/guides/fastapi?utm_medium=integration&utm_source=docs&utm_campaign=fastapi "Deploy enterprise applications at startup speed")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/serpapi-banner.png) ](https://serpapi.com/?utm_source=fastapi_website "SerpApi: Web Search API")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/greptile-banner.png) ](https://www.greptile.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=fastapi_sponsor_page "Greptile: The AI Code Reviewer")
[ ![logo](https://fastapi.tiangolo.com/img/icon-white.svg) ](https://fastapi.tiangolo.com/ "FastAPI")
FastAPI 
Request Forms and Files 
  * [ en - English ](https://fastapi.tiangolo.com/)
  * [ de - Deutsch ](https://fastapi.tiangolo.com/de/)
  * [ es - español ](https://fastapi.tiangolo.com/es/)
  * [ fr - français ](https://fastapi.tiangolo.com/fr/)
  * [ ja - 日本語 ](https://fastapi.tiangolo.com/ja/)
  * [ ko - 한국어 ](https://fastapi.tiangolo.com/ko/)
  * [ pt - português ](https://fastapi.tiangolo.com/pt/)
  * [ ru - русский язык ](https://fastapi.tiangolo.com/ru/)
  * [ tr - Türkçe ](https://fastapi.tiangolo.com/tr/)
  * [ uk - українська мова ](https://fastapi.tiangolo.com/uk/)
  * [ zh - 简体中文 ](https://fastapi.tiangolo.com/zh/)
  * [ zh-hant - 繁體中文 ](https://fastapi.tiangolo.com/zh-hant/)


[ ](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/?q= "Share")
Initializing search 
[ fastapi/fastapi 
  * 0.135.3
  * 96.9k
  * 9k
```

**crawl4ai-raw**
```
[ Skip to content ](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#request-forms-and-files)
[ **FastAPI Cloud** waiting list 🚀 ](https://fastapicloud.com)
[ Follow **@fastapi** on **X (Twitter)** to stay updated ](https://x.com/fastapi)
[ Follow **FastAPI** on **LinkedIn** to stay updated ](https://www.linkedin.com/company/fastapi)
[ **FastAPI and friends** newsletter 🎉 ](https://fastapi.tiangolo.com/newsletter/)
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/blockbee-banner.png) ](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/scalar-banner.svg) ](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/propelauth-banner.png) ](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/zuplo-banner.png) ](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/liblab-banner.png) ](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from FastAPI")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/render-banner.svg) ](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/coderabbit-banner.png) ](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/subtotal-banner.svg) ](https://subtotal.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=open-source "Making Retail Purchases Actionable for Brands and Developers")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/railway-banner.png) ](https://docs.railway.com/guides/fastapi?utm_medium=integration&utm_source=docs&utm_campaign=fastapi "Deploy enterprise applications at startup speed")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/serpapi-banner.png) ](https://serpapi.com/?utm_source=fastapi_website "SerpApi: Web Search API")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/greptile-banner.png) ](https://www.greptile.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=fastapi_sponsor_page "Greptile: The AI Code Reviewer")
[ ![logo](https://fastapi.tiangolo.com/img/icon-white.svg) ](https://fastapi.tiangolo.com/ "FastAPI")
FastAPI 
Request Forms and Files 
  * [ en - English ](https://fastapi.tiangolo.com/)
  * [ de - Deutsch ](https://fastapi.tiangolo.com/de/)
  * [ es - español ](https://fastapi.tiangolo.com/es/)
  * [ fr - français ](https://fastapi.tiangolo.com/fr/)
  * [ ja - 日本語 ](https://fastapi.tiangolo.com/ja/)
  * [ ko - 한국어 ](https://fastapi.tiangolo.com/ko/)
  * [ pt - português ](https://fastapi.tiangolo.com/pt/)
  * [ ru - русский язык ](https://fastapi.tiangolo.com/ru/)
  * [ tr - Türkçe ](https://fastapi.tiangolo.com/tr/)
  * [ uk - українська мова ](https://fastapi.tiangolo.com/uk/)
  * [ zh - 简体中文 ](https://fastapi.tiangolo.com/zh/)
  * [ zh-hant - 繁體中文 ](https://fastapi.tiangolo.com/zh-hant/)


[ ](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/?q= "Share")
Initializing search 
[ fastapi/fastapi 
  * 0.135.3
  * 96.9k
  * 9k
```

**scrapy+md**
```
FastAPI

[fastapi/fastapi](https://github.com/fastapi/fastapi "Go to repository")

* [FastAPI](../..)
* [Features](../../features/)
* [Learn](../../learn/)

  Learn
  + [Python Types Intro](../../python-types/)
  + [Concurrency and async / await](../../async/)
  + [Environment Variables](../../environment-variables/)
  + [Virtual Environments](../../virtual-environments/)
  + [Tutorial - User Guide](../)

    Tutorial - User Guide
    - [First Steps](../first-steps/)
    - [Path Parameters](../path-params/)
    - [Query Parameters](../query-params/)
    - [Request Body](../body/)
    - [Query Parameters and String Validations](../query-params-str-validations/)
    - [Path Parameters and Numeric Validations](../path-params-numeric-validations/)
    - [Query Parameter Models](../query-param-models/)
    - [Body - Multiple Parameters](../body-multiple-params/)
    - [Body - Fields](../body-fields/)
    - [Body - Nested Models](../body-nested-models/)
    - [Declare Request Example Data](../schema-extra-example/)
    - [Extra Data Types](../extra-data-types/)
    - [Cookie Parameters](../cookie-params/)
    - [Header Parameters](../header-params/)
    - [Cookie Parameter Models](../cookie-param-models/)
    - [Header Parameter Models](../header-param-models/)
    - [Response Model - Return Type](../response-model/)
    - [Extra Models](../extra-models/)
    - [Response Status Code](../response-status-code/)
    - [Form Data](../request-forms/)
    - [Form Models](../request-form-models/)
    - [Request Files](../request-files/)
    - Request Forms and Files
```

**crawlee**
```
Request Forms and Files - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}













.grecaptcha-badge {
visibility: hidden;
}





[Skip to content](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#request-forms-and-files)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)
```

**colly+md**
```
Request Forms and Files - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}






[Skip to content](#request-forms-and-files)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)

[sponsor](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")

[sponsor](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")

[sponsor](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")

[sponsor](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")

[sponsor](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from FastAPI")

[sponsor](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")

[sponsor](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")
```

**playwright**
```
Request Forms and Files - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}






[Skip to content](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#request-forms-and-files)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)

[sponsor](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")

[sponsor](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")

[sponsor](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")

[sponsor](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")

[sponsor](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from FastAPI")

[sponsor](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")

[sponsor](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")
```

**firecrawl** — no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| fastapi.tiangolo.com | 2230 / 0 | 3979 / 1526 | 3979 / 1526 | 3092 / 839 | 3374 / 1071 | 3404 / 1054 | 3357 / 1054 | — |
| fastapi.tiangolo.com/advanced/advanced-dependencies | 2200 / 0 | 3660 / 1434 | 3658 / 1432 | 3012 / 796 | 3330 / 1034 | 3335 / 1015 | 3311 / 1015 | — |
| fastapi.tiangolo.com/advanced/custom-response | 1987 / 0 | 3457 / 1448 | 3459 / 1450 | 2782 / 779 | 3095 / 1025 | 3116 / 1008 | 3078 / 1008 | — |
| fastapi.tiangolo.com/advanced/stream-data | 2723 / 0 | 4109 / 1354 | 4109 / 1354 | 3465 / 726 | 3785 / 962 | 3788 / 945 | 3768 / 945 | — |
| fastapi.tiangolo.com/advanced/testing-events | 263 / 0 | 1562 / 1253 | 1562 / 1253 | 929 / 650 | 1276 / 896 | 1261 / 879 | 1259 / 879 | — |
| fastapi.tiangolo.com/advanced/testing-websockets | 117 / 0 | 1414 / 1248 | 1414 / 1248 | 783 / 650 | 1123 / 886 | 1108 / 869 | 1106 / 869 | — |
| fastapi.tiangolo.com/async | 3651 / 0 | 5198 / 1484 | 5198 / 1484 | 4478 / 811 | 4780 / 1053 | 4805 / 1036 | 4763 / 1036 | — |
| fastapi.tiangolo.com/deployment/docker | 4157 / 0 | 5537 / 1722 | 5537 / 1722 | 5156 / 983 | 5068 / 1225 | 5488 / 1208 | 5405 / 1208 | — |
| fastapi.tiangolo.com/fastapi-people | 1434 / 0 | 3347 / 1430 | 3347 / 1430 | 2230 / 780 | 2536 / 1018 | 2551 / 999 | 2517 / 999 | — |
| fastapi.tiangolo.com/help-fastapi | 1955 / 0 | 3519 / 1564 | 3519 / 1564 | 2842 / 875 | 3139 / 1117 | 3172 / 1100 | 3122 / 1100 | — |
| fastapi.tiangolo.com/how-to | 97 / 0 | 1400 / 1251 | 1400 / 1251 | 764 / 651 | 1110 / 891 | 1095 / 874 | 1093 / 874 | — |
| fastapi.tiangolo.com/ja | 1164 / 0 | 2734 / 1334 | 2734 / 1334 | 1818 / 631 | 2073 / 858 | 2103 / 841 | 2056 / 841 | — |
| fastapi.tiangolo.com/reference/apirouter | 24889 / 0 | 26603 / 1404 | 26603 / 1404 | 25651 / 746 | 25971 / 984 | 25976 / 965 | 25952 / 965 | — |
| fastapi.tiangolo.com/reference/openapi/models | 3708 / 0 | 7394 / 3186 | 7394 / 3186 | 5672 / 1948 | 6009 / 2186 | 5992 / 2167 | 5990 / 2167 | — |
| fastapi.tiangolo.com/reference/parameters | 12456 / 0 | 13849 / 1286 | 13849 / 1286 | 13154 / 682 | 13491 / 920 | 13474 / 901 | 13472 / 901 | — |
| fastapi.tiangolo.com/reference/request | 680 / 0 | 2122 / 1388 | 2122 / 1388 | 1446 / 750 | 1782 / 986 | 1767 / 969 | 1765 / 969 | — |
| fastapi.tiangolo.com/tutorial/cookie-params | 365 / 0 | 1686 / 1281 | 1686 / 1281 | 1058 / 677 | 1388 / 913 | 1379 / 896 | 1371 / 896 | — |
| fastapi.tiangolo.com/tutorial/dependencies/dependencies | 2580 / 0 | 4064 / 1465 | 3817 / 1465 | 3414 / 818 | 3479 / 1058 | 3735 / 1039 | 3707 / 1039 | — |
| fastapi.tiangolo.com/tutorial/query-params-str-validati | 4071 / 0 | 5682 / 1591 | 5682 / 1591 | 4987 / 900 | 5285 / 1144 | 5316 / 1125 | 5266 / 1125 | — |
| fastapi.tiangolo.com/tutorial/request-forms-and-files | 388 / 0 | 1721 / 1293 | 1721 / 1293 | 1091 / 687 | 1424 / 927 | 1415 / 910 | 1407 / 910 | — |
| fastapi.tiangolo.com/tutorial/response-model | 3150 / 0 | 4716 / 1553 | 4716 / 1553 | 4040 / 874 | 4342 / 1118 | 4367 / 1099 | 4327 / 1103 | — |
| fastapi.tiangolo.com/tutorial/security/oauth2-jwt | 4418 / 0 | 5893 / 1431 | 5895 / 1433 | 5212 / 778 | 5550 / 1028 | 5549 / 1011 | 5533 / 1011 | — |
| fastapi.tiangolo.com/tutorial/security/simple-oauth2 | 3596 / 0 | 5078 / 1455 | 5078 / 1455 | 4405 / 793 | 4726 / 1039 | 4741 / 1020 | 4707 / 1020 | — |
| fastapi.tiangolo.com/tutorial/sql-databases | 10591 / 0 | 12262 / 1635 | 12262 / 1635 | 11545 / 938 | 11842 / 1176 | 11872 / 1159 | 11825 / 1159 | — |
| fastapi.tiangolo.com/virtual-environments | 3009 / 0 | 4623 / 1522 | 4623 / 1522 | 3869 / 844 | 4149 / 1082 | 4191 / 1063 | 4220 / 1063 | — |

</details>

## python-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 2817 | 1 | 0% | 14 | 9.1 | 4.6 | 100% | 76% |
| crawl4ai | 3268 | 64 ⚠ | 0% | 98 | 16.6 | 4.6 | 100% | 58% |
| crawl4ai-raw | 3268 | 64 ⚠ | 0% | 98 | 16.6 | 4.6 | 100% | 58% |
| scrapy+md | 3418 | 4 | 0% | 91 | 17.7 | 5.1 | 100% | 100% |
| crawlee | 3214 | 49 | 0% | 98 | 16.6 | 4.6 | 100% | 94% |
| colly+md | 3125 | 21 | 0% | 98 | 16.6 | 4.6 | 100% | 95% |
| playwright | 3214 | 49 | 0% | 98 | 16.6 | 4.6 | 100% | 94% |
| firecrawl | — | — | — | — | — | — | — | — |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**markcrawl** produces the cleanest output with 1 word of preamble per page, while **crawl4ai** injects 64 words of nav chrome before content begins. markcrawl's lower recall (76% vs 100%) reflects stricter content filtering — the "missed" sentences are predominantly navigation, sponsor links, and footer text that other tools include as content. For RAG, this is a net positive: fewer junk tokens per chunk means better embedding quality and retrieval precision.

<details>
<summary>Sample output — first 40 lines of <code>docs.python.org/3.10/library/index.html</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# The Python Standard Library[Â¶](#the-python-standard-library "Permalink to this headline")

While [The Python Language Reference](../reference/index.html#reference-index) describes the exact syntax and
semantics of the Python language, this library reference manual
describes the standard library that is distributed with Python. It also
describes some of the optional components that are commonly included
in Python distributions.

Pythonâs standard library is very extensive, offering a wide range of
facilities as indicated by the long table of contents listed below. The
library contains built-in modules (written in C) that provide access to
system functionality such as file I/O that would otherwise be
inaccessible to Python programmers, as well as modules written in Python
that provide standardized solutions for many problems that occur in
everyday programming. Some of these modules are explicitly designed to
encourage and enhance the portability of Python programs by abstracting
away platform-specifics into platform-neutral APIs.

The Python installers for the Windows platform usually include
the entire standard library and often also include many additional
components. For Unix-like operating systems Python is normally provided
as a collection of packages, so it may be necessary to use the packaging
tools provided with the operating system to obtain some or all of the
optional components.

In addition to the standard library, there is a growing collection of
several thousand components (from individual programs and modules to
packages and entire application development frameworks), available from
the [Python Package Index](https://pypi.org).

* [Introduction](intro.html)
  * [Notes on availability](intro.html#notes-on-availability)
* [Built-in Functions](functions.html)
* [Built-in Constants](constants.html)
  * [Constants added by the `site` module](constants.html#constants-added-by-the-site-module)
* [Built-in Types](stdtypes.html)
  * [Truth Value Testing](stdtypes.html#truth-value-testing)
  * [Boolean Operations â `and`, `or`, `not`](stdtypes.html#boolean-operations-and-or-not)
  * [Comparisons](stdtypes.html#comparisons)
  * [Numeric Types â `int`, `float`, `complex`](stdtypes.html#numeric-types-int-float-complex)
```

**crawl4ai**
```
[ ![Python logo](https://docs.python.org/3.10/_static/py.svg) ](https://www.python.org/) dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
#### Previous topic
[10. Full Grammar specification](https://docs.python.org/3.10/reference/grammar.html "previous chapter")
#### Next topic
[Introduction](https://docs.python.org/3.10/library/intro.html "next chapter")
### This Page
  * [Report a Bug](https://docs.python.org/3.10/bugs.html)
  * [Show Source ](https://github.com/python/cpython/blob/3.10/Doc/library/index.rst)


### Navigation
  * [index](https://docs.python.org/3.10/genindex.html "General Index")
  * [modules](https://docs.python.org/3.10/py-modindex.html "Python Module Index") |
  * [next](https://docs.python.org/3.10/library/intro.html "Introduction") |
  * [previous](https://docs.python.org/3.10/reference/grammar.html "10. Full Grammar specification") |
  * ![Python logo](https://docs.python.org/3.10/_static/py.svg)
  * [Python](https://www.python.org/) »
  * Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
  * [3.10.20 Documentation](https://docs.python.org/3.10/index.html) » 
  * [The Python Standard Library](https://docs.python.org/3.10/library/index.html)
  * | 
  * Theme  Auto Light Dark |


# The Python Standard Library[¶](https://docs.python.org/3.10/library/index.html#the-python-standard-library "Permalink to this headline")
While [The Python Language Reference](https://docs.python.org/3.10/reference/index.html#reference-index) describes the exact syntax and semantics of the Python language, this library reference manual describes the standard library that is distributed with Python. It also describes some of the optional components that are commonly included in Python distributions.
Python’s standard library is very extensive, offering a wide range of facilities as indicated by the long table of contents listed below. The library contains built-in modules (written in C) that provide access to system functionality such as file I/O that would otherwise be inaccessible to Python programmers, as well as modules written in Python that provide standardized solutions for many problems that occur in everyday programming. Some of these modules are explicitly designed to encourage and enhance the portability of Python programs by abstracting away platform-specifics into platform-neutral APIs.
The Python installers for the Windows platform usually include the entire standard library and often also include many additional components. For Unix-like operating systems Python is normally provided as a collection of packages, so it may be necessary to use the packaging tools provided with the operating system to obtain some or all of the optional components.
In addition to the standard library, there is a growing collection of several thousand components (from individual programs and modules to packages and entire application development frameworks), available from the [Python Package Index](https://pypi.org).
  * [Introduction](https://docs.python.org/3.10/library/intro.html)
    * [Notes on availability](https://docs.python.org/3.10/library/intro.html#notes-on-availability)
  * [Built-in Functions](https://docs.python.org/3.10/library/functions.html)
  * [Built-in Constants](https://docs.python.org/3.10/library/constants.html)
    * [Constants added by the `site` module](https://docs.python.org/3.10/library/constants.html#constants-added-by-the-site-module)
  * [Built-in Types](https://docs.python.org/3.10/library/stdtypes.html)
    * [Truth Value Testing](https://docs.python.org/3.10/library/stdtypes.html#truth-value-testing)
    * [Boolean Operations — `and`, `or`, `not`](https://docs.python.org/3.10/library/stdtypes.html#boolean-operations-and-or-not)
```

**crawl4ai-raw**
```
[ ![Python logo](https://docs.python.org/3.10/_static/py.svg) ](https://www.python.org/) dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
#### Previous topic
[10. Full Grammar specification](https://docs.python.org/3.10/reference/grammar.html "previous chapter")
#### Next topic
[Introduction](https://docs.python.org/3.10/library/intro.html "next chapter")
### This Page
  * [Report a Bug](https://docs.python.org/3.10/bugs.html)
  * [Show Source ](https://github.com/python/cpython/blob/3.10/Doc/library/index.rst)


### Navigation
  * [index](https://docs.python.org/3.10/genindex.html "General Index")
  * [modules](https://docs.python.org/3.10/py-modindex.html "Python Module Index") |
  * [next](https://docs.python.org/3.10/library/intro.html "Introduction") |
  * [previous](https://docs.python.org/3.10/reference/grammar.html "10. Full Grammar specification") |
  * ![Python logo](https://docs.python.org/3.10/_static/py.svg)
  * [Python](https://www.python.org/) »
  * Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
  * [3.10.20 Documentation](https://docs.python.org/3.10/index.html) » 
  * [The Python Standard Library](https://docs.python.org/3.10/library/index.html)
  * | 
  * Theme  Auto Light Dark |


# The Python Standard Library[¶](https://docs.python.org/3.10/library/index.html#the-python-standard-library "Permalink to this headline")
While [The Python Language Reference](https://docs.python.org/3.10/reference/index.html#reference-index) describes the exact syntax and semantics of the Python language, this library reference manual describes the standard library that is distributed with Python. It also describes some of the optional components that are commonly included in Python distributions.
Python’s standard library is very extensive, offering a wide range of facilities as indicated by the long table of contents listed below. The library contains built-in modules (written in C) that provide access to system functionality such as file I/O that would otherwise be inaccessible to Python programmers, as well as modules written in Python that provide standardized solutions for many problems that occur in everyday programming. Some of these modules are explicitly designed to encourage and enhance the portability of Python programs by abstracting away platform-specifics into platform-neutral APIs.
The Python installers for the Windows platform usually include the entire standard library and often also include many additional components. For Unix-like operating systems Python is normally provided as a collection of packages, so it may be necessary to use the packaging tools provided with the operating system to obtain some or all of the optional components.
In addition to the standard library, there is a growing collection of several thousand components (from individual programs and modules to packages and entire application development frameworks), available from the [Python Package Index](https://pypi.org).
  * [Introduction](https://docs.python.org/3.10/library/intro.html)
    * [Notes on availability](https://docs.python.org/3.10/library/intro.html#notes-on-availability)
  * [Built-in Functions](https://docs.python.org/3.10/library/functions.html)
  * [Built-in Constants](https://docs.python.org/3.10/library/constants.html)
    * [Constants added by the `site` module](https://docs.python.org/3.10/library/constants.html#constants-added-by-the-site-module)
  * [Built-in Types](https://docs.python.org/3.10/library/stdtypes.html)
    * [Truth Value Testing](https://docs.python.org/3.10/library/stdtypes.html#truth-value-testing)
    * [Boolean Operations — `and`, `or`, `not`](https://docs.python.org/3.10/library/stdtypes.html#boolean-operations-and-or-not)
```

**scrapy+md**
```
Theme
Auto
Light
Dark

#### Previous topic

[10. Full Grammar specification](../reference/grammar.html "previous chapter")

#### Next topic

[Introduction](intro.html "next chapter")

### This Page

* [Report a Bug](../bugs.html)
* [Show Source](https://github.com/python/cpython/blob/3.10/Doc/library/index.rst)

### Navigation

* [index](../genindex.html "General Index")
* [modules](../py-modindex.html "Python Module Index") |
* [next](intro.html "Introduction") |
* [previous](../reference/grammar.html "10. Full Grammar specification") |
* [Python](https://www.python.org/) »

* [3.10.20 Documentation](../index.html) »
* The Python Standard Library
* |
* Theme
  Auto
  Light
  Dark
   |

# The Python Standard Library[¶](#the-python-standard-library "Permalink to this headline")

While [The Python Language Reference](../reference/index.html#reference-index) describes the exact syntax and
semantics of the Python language, this library reference manual
describes the standard library that is distributed with Python. It also
```

**crawlee**
```
The Python Standard Library — Python 3.10.20 documentation

















@media only screen {
table.full-width-table {
width: 100%;
}
}



dev (3.15)3.143.133.123.113.10.203.93.83.73.63.53.43.33.23.13.02.72.6

Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文

Theme
Auto
Light
Dark

#### Previous topic

[10. Full Grammar specification](../reference/grammar.html "previous chapter")

#### Next topic
```

**colly+md**
```
The Python Standard Library — Python 3.10.20 documentation

















@media only screen {
table.full-width-table {
width: 100%;
}
}



Theme
Auto
Light
Dark

#### Previous topic

[10. Full Grammar specification](../reference/grammar.html "previous chapter")

#### Next topic

[Introduction](intro.html "next chapter")

### This Page
```

**playwright**
```
The Python Standard Library — Python 3.10.20 documentation

















@media only screen {
table.full-width-table {
width: 100%;
}
}



dev (3.15)3.143.133.123.113.10.203.93.83.73.63.53.43.33.23.13.02.72.6

Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文

Theme
Auto
Light
Dark

#### Previous topic

[10. Full Grammar specification](../reference/grammar.html "previous chapter")

#### Next topic
```

**firecrawl** — no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| docs.python.org/3.10 | 190 / 0 | 711 / 68 | 711 / 68 | 521 / 4 | 629 / 47 | 533 / 16 | 629 / 47 | — |
| docs.python.org/3.10/about.html | 180 / 0 | 604 / 68 | 604 / 68 | 407 / 4 | 520 / 52 | 424 / 21 | 520 / 52 | — |
| docs.python.org/3.10/bugs.html | 666 / 0 | 1104 / 68 | 1104 / 68 | 913 / 4 | 1026 / 52 | 930 / 21 | 1026 / 52 | — |
| docs.python.org/3.10/contents.html | 19401 / 0 | 19782 / 68 | 19782 / 68 | 19584 / 4 | 19697 / 52 | 19601 / 21 | 19697 / 52 | — |
| docs.python.org/3.10/distributing/index.html | 984 / 0 | 1481 / 68 | 1481 / 68 | 1285 / 4 | 1402 / 52 | 1306 / 21 | 1402 / 52 | — |
| docs.python.org/3.10/download.html | 277 / 0 | 599 / 68 | 599 / 68 | 404 / 4 | 515 / 50 | 419 / 19 | 515 / 50 | — |
| docs.python.org/3.10/glossary.html | 7963 / 0 | 8264 / 68 | 8264 / 68 | 8186 / 4 | 8302 / 50 | 8201 / 19 | 8302 / 50 | — |
| docs.python.org/3.10/library/index.html | 2282 / 0 | 2684 / 68 | 2684 / 68 | 2487 / 4 | 2601 / 53 | 2505 / 22 | 2601 / 53 | — |
| docs.python.org/3.10/reference/index.html | 438 / 0 | 844 / 68 | 844 / 68 | 647 / 4 | 761 / 53 | 665 / 22 | 761 / 53 | — |
| docs.python.org/3.10/tutorial/index.html | 982 / 0 | 1382 / 68 | 1382 / 68 | 1185 / 4 | 1298 / 52 | 1202 / 21 | 1298 / 52 | — |
| docs.python.org/3.10/whatsnew/3.10.html | 12688 / 0 | 13749 / 68 | 13749 / 68 | 13627 / 4 | 13773 / 54 | 13646 / 23 | 13773 / 54 | — |
| docs.python.org/3.11 | 188 / 0 | 711 / 68 | 711 / 68 | 522 / 4 | 629 / 47 | 534 / 16 | 629 / 47 | — |
| docs.python.org/3.12 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.13 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.14 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.15 | 191 / 0 | 709 / 67 | 709 / 67 | 525 / 4 | 629 / 46 | 537 / 16 | 629 / 46 | — |
| docs.python.org/3.4 | 339 / 27 | 336 / 28 | 336 / 28 | — | 361 / 47 | 360 / 47 | 361 / 47 | — |
| docs.python.org/3.5 | 186 / 0 | 371 / 28 | 371 / 28 | — | 353 / 29 | 324 / 29 | 353 / 29 | — |
| docs.python.org/3/bugs.html | — | — | — | 980 / 4 | — | 997 / 21 | — | — |
| docs.python.org/3/license.html | — | — | — | 8679 / 4 | — | 8696 / 21 | — | — |
| docs.python.org/bugs.html | 650 / 0 | 1096 / 68 | 1096 / 68 | — | 1092 / 52 | — | 1092 / 52 | — |
| docs.python.org/license.html | 8155 / 0 | 8801 / 68 | 8801 / 68 | — | 8791 / 52 | — | 8791 / 52 | — |

</details>

