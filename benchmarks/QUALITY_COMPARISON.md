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
| markcrawl | 100% | 1 | 0% | 0.7 | 100% | 86% |
| crawl4ai | 86% | 473 ⚠ | 1% | 4.0 | 100% | 88% |
| crawl4ai-raw | 86% | 473 ⚠ | 1% | 4.0 | 100% | 88% |
| scrapy+md | 92% | 246 ⚠ | 1% | 4.1 | 100% | 89% |
| crawlee | 90% | 331 ⚠ | 1% | 4.9 | 100% | 98% |
| colly+md | 90% | 309 ⚠ | 1% | 4.9 | 100% | 98% |
| playwright | 90% | 329 ⚠ | 1% | 4.9 | 100% | 98% |
| firecrawl | 92% | 188 ⚠ | 0% | 3.4 | 29% | 33% |

**[1]** Avg words per page before the first heading (nav chrome).


**Key takeaway:** markcrawl achieves 100% content signal with only 1 words of preamble per page — compared to 473 for crawl4ai. Its recall is lower (86% vs 98%) because it strips nav, footer, and sponsor content that other tools include. For RAG use cases, this trade-off favors markcrawl: every chunk in the vector index is pure content, with no boilerplate to dilute embeddings or pollute retrieval results.

> **Content signal** = percentage of output that is content (not preamble nav chrome).
> Higher is better. A tool with 100% content signal has zero nav/header pollution.
> **Repeat rate** = fraction of phrases appearing on >50% of pages (boilerplate).
> **Junk/page** = known boilerplate phrases detected per page.

## quotes-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 280 | 0 | 1% | 2 | 2.7 | 0.0 | 100% | 100% |
| crawl4ai | 289 | 0 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| crawl4ai-raw | 289 | 0 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| scrapy+md | 289 | 0 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| crawlee | 292 | 3 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| colly+md | 292 | 3 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| playwright | 292 | 3 | 2% | 2 | 2.7 | 0.0 | 100% | 100% |
| firecrawl | 203 | 23 | 1% | 1 | 0.9 | 0.0 | 33% | 33% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

<details>
<summary>Sample output — first 40 lines of <code>quotes.toscrape.com/tag/world/page/1</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# [Quotes to Scrape](/)

[Login](/login)

### Viewing tag: [world](/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

## Top Ten tags

[love](/tag/love/)

[inspirational](/tag/inspirational/)

[life](/tag/life/)

[humor](/tag/humor/)

[books](/tag/books/)

[reading](/tag/reading/)

[friendship](/tag/friendship/)

[friends](/tag/friends/)

[truth](/tag/truth/)

[simile](/tag/simile/)
```

**crawl4ai**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
### Viewing tag: [world](https://quotes.toscrape.com/tag/world/page/1/)
“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.” by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [change](https://quotes.toscrape.com/tag/change/page/1/) [deep-thoughts](https://quotes.toscrape.com/tag/deep-thoughts/page/1/) [thinking](https://quotes.toscrape.com/tag/thinking/page/1/) [world](https://quotes.toscrape.com/tag/world/page/1/)
## Top Ten tags
[love](https://quotes.toscrape.com/tag/love/) [inspirational](https://quotes.toscrape.com/tag/inspirational/) [life](https://quotes.toscrape.com/tag/life/) [humor](https://quotes.toscrape.com/tag/humor/) [books](https://quotes.toscrape.com/tag/books/) [reading](https://quotes.toscrape.com/tag/reading/) [friendship](https://quotes.toscrape.com/tag/friendship/) [friends](https://quotes.toscrape.com/tag/friends/) [truth](https://quotes.toscrape.com/tag/truth/) [simile](https://quotes.toscrape.com/tag/simile/)
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**crawl4ai-raw**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
### Viewing tag: [world](https://quotes.toscrape.com/tag/world/page/1/)
“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.” by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [change](https://quotes.toscrape.com/tag/change/page/1/) [deep-thoughts](https://quotes.toscrape.com/tag/deep-thoughts/page/1/) [thinking](https://quotes.toscrape.com/tag/thinking/page/1/) [world](https://quotes.toscrape.com/tag/world/page/1/)
## Top Ten tags
[love](https://quotes.toscrape.com/tag/love/) [inspirational](https://quotes.toscrape.com/tag/inspirational/) [life](https://quotes.toscrape.com/tag/life/) [humor](https://quotes.toscrape.com/tag/humor/) [books](https://quotes.toscrape.com/tag/books/) [reading](https://quotes.toscrape.com/tag/reading/) [friendship](https://quotes.toscrape.com/tag/friendship/) [friends](https://quotes.toscrape.com/tag/friends/) [truth](https://quotes.toscrape.com/tag/truth/) [simile](https://quotes.toscrape.com/tag/simile/)
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**scrapy+md**
```
# [Quotes to Scrape](/)

[Login](/login)

### Viewing tag: [world](/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

## Top Ten tags

[love](/tag/love/)

[inspirational](/tag/inspirational/)

[life](/tag/life/)

[humor](/tag/humor/)

[books](/tag/books/)

[reading](/tag/reading/)

[friendship](/tag/friendship/)

[friends](/tag/friends/)

[truth](/tag/truth/)

[simile](/tag/simile/)

Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
```

**crawlee**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Viewing tag: [world](/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

## Top Ten tags

[love](/tag/love/)

[inspirational](/tag/inspirational/)

[life](/tag/life/)

[humor](/tag/humor/)

[books](/tag/books/)

[reading](/tag/reading/)

[friendship](/tag/friendship/)

[friends](/tag/friends/)

[truth](/tag/truth/)
```

**colly+md**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Viewing tag: [world](/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

## Top Ten tags

[love](/tag/love/)

[inspirational](/tag/inspirational/)

[life](/tag/life/)

[humor](/tag/humor/)

[books](/tag/books/)

[reading](/tag/reading/)

[friendship](/tag/friendship/)

[friends](/tag/friends/)

[truth](/tag/truth/)
```

**playwright**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

### Viewing tag: [world](/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

## Top Ten tags

[love](/tag/love/)

[inspirational](/tag/inspirational/)

[life](/tag/life/)

[humor](/tag/humor/)

[books](/tag/books/)

[reading](/tag/reading/)

[friendship](/tag/friendship/)

[friends](/tag/friends/)

[truth](/tag/truth/)
```

**firecrawl**
```
[Quotes to Scrape](http://quotes.toscrape.com/)

================================================

[Login](http://quotes.toscrape.com/login)

### Viewing tag: [world](http://quotes.toscrape.com/tag/world/page/1/)

“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.” by Albert Einstein [(about)](http://quotes.toscrape.com/author/Albert-Einstein)

Tags: [change](http://quotes.toscrape.com/tag/change/page/1/)
 [deep-thoughts](http://quotes.toscrape.com/tag/deep-thoughts/page/1/)
 [thinking](http://quotes.toscrape.com/tag/thinking/page/1/)
 [world](http://quotes.toscrape.com/tag/world/page/1/)

Top Ten tags
------------

[love](http://quotes.toscrape.com/tag/love/) [inspirational](http://quotes.toscrape.com/tag/inspirational/) [life](http://quotes.toscrape.com/tag/life/) [humor](http://quotes.toscrape.com/tag/humor/) [books](http://quotes.toscrape.com/tag/books/) [reading](http://quotes.toscrape.com/tag/reading/) [friendship](http://quotes.toscrape.com/tag/friendship/) [friends](http://quotes.toscrape.com/tag/friends/) [truth](http://quotes.toscrape.com/tag/truth/) [simile](http://quotes.toscrape.com/tag/simile/)
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| quotes.toscrape.com | 271 / 0 | 282 / 0 | 282 / 0 | 282 / 0 | 285 / 3 | 285 / 3 | 285 / 3 | 271 / 271 |
| quotes.toscrape.com/author/Albert-Einstein | — | — | — | — | — | — | — | 621 / 5 |
| quotes.toscrape.com/author/Eleanor-Roosevelt | 242 / 0 | 250 / 0 | 250 / 0 | 250 / 0 | 253 / 3 | 253 / 3 | 253 / 3 | — |
| quotes.toscrape.com/author/J-K-Rowling | 650 / 0 | 658 / 0 | 658 / 0 | 658 / 0 | 661 / 3 | 661 / 3 | 661 / 3 | 650 / 5 |
| quotes.toscrape.com/author/Jane-Austen | 333 / 0 | 341 / 0 | 341 / 0 | 341 / 0 | 344 / 3 | 344 / 3 | 344 / 3 | — |
| quotes.toscrape.com/login | — | — | — | — | — | — | — | 7 / 7 |
| quotes.toscrape.com/page/2 | 600 / 0 | 614 / 0 | 614 / 0 | 614 / 0 | 617 / 3 | 617 / 3 | 617 / 3 | — |
| quotes.toscrape.com/tag/abilities/page/1 | — | — | — | — | — | — | — | 46 / 5 |
| quotes.toscrape.com/tag/be-yourself/page/1 | 46 / 0 | 54 / 0 | 54 / 0 | 54 / 0 | 57 / 3 | 57 / 3 | 57 / 3 | — |
| quotes.toscrape.com/tag/change/page/1 | 53 / 0 | 61 / 0 | 61 / 0 | 61 / 0 | 64 / 3 | 64 / 3 | 64 / 3 | 53 / 5 |
| quotes.toscrape.com/tag/choices/page/1 | — | — | — | — | — | — | — | 46 / 5 |
| quotes.toscrape.com/tag/deep-thoughts/page/1 | 53 / 0 | 61 / 0 | 61 / 0 | 61 / 0 | 64 / 3 | 64 / 3 | 64 / 3 | 53 / 5 |
| quotes.toscrape.com/tag/friends | 305 / 0 | 313 / 0 | 313 / 0 | 313 / 0 | 316 / 3 | 316 / 3 | 316 / 3 | — |
| quotes.toscrape.com/tag/humor | 284 / 0 | 295 / 0 | 295 / 0 | 295 / 0 | 298 / 3 | 298 / 3 | 298 / 3 | — |
| quotes.toscrape.com/tag/inspirational/page/1 | — | — | — | — | — | — | — | 484 / 5 |
| quotes.toscrape.com/tag/life | 498 / 0 | 509 / 0 | 509 / 0 | 509 / 0 | 512 / 3 | 512 / 3 | 512 / 3 | — |
| quotes.toscrape.com/tag/life/page/1 | — | — | — | — | — | — | — | 498 / 5 |
| quotes.toscrape.com/tag/live/page/1 | — | — | — | — | — | — | — | 59 / 5 |
| quotes.toscrape.com/tag/love | 673 / 0 | 684 / 0 | 684 / 0 | 684 / 0 | 687 / 3 | 687 / 3 | 687 / 3 | — |
| quotes.toscrape.com/tag/miracle/page/1 | — | — | — | — | — | — | — | 59 / 5 |
| quotes.toscrape.com/tag/miracles/page/1 | 59 / 0 | 67 / 0 | 67 / 0 | 67 / 0 | 70 / 3 | 70 / 3 | 70 / 3 | 59 / 5 |
| quotes.toscrape.com/tag/simile/page/1 | 76 / 0 | 84 / 0 | 84 / 0 | 84 / 0 | 87 / 3 | 87 / 3 | 87 / 3 | — |
| quotes.toscrape.com/tag/thinking/page/1 | — | — | — | — | — | — | — | 85 / 5 |
| quotes.toscrape.com/tag/world/page/1 | 53 / 0 | 61 / 0 | 61 / 0 | 61 / 0 | 64 / 3 | 64 / 3 | 64 / 3 | 53 / 5 |

</details>

## books-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 291 | 8 | 0% | 0 | 1.7 | 0.0 | 100% | 98% |
| crawl4ai | 508 | 181 ⚠ | 1% | 0 | 11.1 | 0.0 | 100% | 99% |
| crawl4ai-raw | 508 | 181 ⚠ | 1% | 0 | 11.1 | 0.0 | 100% | 99% |
| scrapy+md | 395 | 103 ⚠ | 1% | 0 | 1.7 | 0.0 | 100% | 98% |
| crawlee | 403 | 111 ⚠ | 1% | 0 | 1.7 | 0.0 | 100% | 98% |
| colly+md | 403 | 111 ⚠ | 1% | 0 | 1.7 | 0.0 | 100% | 98% |
| playwright | 403 | 111 ⚠ | 1% | 0 | 1.7 | 0.0 | 100% | 98% |
| firecrawl | 328 | 328 ⚠ | 0% | 0 | 0.0 | 0.0 | 60% | 84% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**markcrawl** produces the cleanest output with 8 words of preamble per page, while **firecrawl** injects 328 words of nav chrome before content begins. The word count gap (291 vs 508 avg words) is largely explained by preamble: 181 words of nav chrome account for ~36% of crawl4ai's output on this site.

<details>
<summary>Sample output — first 40 lines of <code>books.toscrape.com/catalogue/category/books/self-help_41/index.html</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Self Help

# Self Help

**5** results.

**Warning!** This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning.

1. ### [Online Marketing for Busy ...](../../../online-marketing-for-busy-authors-a-step-by-step-guide_913/index.html "Online Marketing for Busy Authors: A Step-By-Step Guide")

   £46.35

   In stock

   Add to basket
2. ### [How to Be Miserable: ...](../../../how-to-be-miserable-40-strategies-you-already-use_897/index.html "How to Be Miserable: 40 Strategies You Already Use")

   £46.03

   In stock

   Add to basket
3. ### [Overload: How to Unplug, ...](../../../overload-how-to-unplug-unwind-and-unleash-yourself-from-the-pressure-of-stress_725/index.html "Overload: How to Unplug, Unwind, and Unleash Yourself from the Pressure of Stress")

   £52.15

   In stock

   Add to basket
4. ### [You Are a Badass: ...](../../../you-are-a-badass-how-to-stop-doubting-your-greatness-and-start-living-an-awesome-life_508/index.html "You Are a Badass: How to Stop Doubting Your Greatness and Start Living an Awesome Life")

   £12.08

   In stock

   Add to basket
5. ### [How to Stop Worrying ...](../../../how-to-stop-worrying-and-start-living_431/index.html "How to Stop Worrying and Start Living")
```

**crawl4ai**
```
[Books to Scrape](https://books.toscrape.com/index.html) We love being scraped!
  * [Home](https://books.toscrape.com/index.html)
  * [Books](https://books.toscrape.com/catalogue/category/books_1/index.html)
  * Self Help


  * [ Books ](https://books.toscrape.com/catalogue/category/books_1/index.html)
    * [ Travel ](https://books.toscrape.com/catalogue/category/books/travel_2/index.html)
    * [ Mystery ](https://books.toscrape.com/catalogue/category/books/mystery_3/index.html)
    * [ Historical Fiction ](https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html)
    * [ Sequential Art ](https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html)
    * [ Classics ](https://books.toscrape.com/catalogue/category/books/classics_6/index.html)
    * [ Philosophy ](https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html)
    * [ Romance ](https://books.toscrape.com/catalogue/category/books/romance_8/index.html)
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

**crawl4ai-raw**
```
[Books to Scrape](https://books.toscrape.com/index.html) We love being scraped!
  * [Home](https://books.toscrape.com/index.html)
  * [Books](https://books.toscrape.com/catalogue/category/books_1/index.html)
  * Self Help


  * [ Books ](https://books.toscrape.com/catalogue/category/books_1/index.html)
    * [ Travel ](https://books.toscrape.com/catalogue/category/books/travel_2/index.html)
    * [ Mystery ](https://books.toscrape.com/catalogue/category/books/mystery_3/index.html)
    * [ Historical Fiction ](https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html)
    * [ Sequential Art ](https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html)
    * [ Classics ](https://books.toscrape.com/catalogue/category/books/classics_6/index.html)
    * [ Philosophy ](https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html)
    * [ Romance ](https://books.toscrape.com/catalogue/category/books/romance_8/index.html)
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
* Self Help

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [Romance](../romance_8/index.html)
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
Self Help |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Self Help

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [Romance](../romance_8/index.html)
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
  


Self Help |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Self Help

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [Romance](../romance_8/index.html)
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
Self Help |
Books to Scrape - Sandbox




[Books to Scrape](../../../../index.html) We love being scraped!

* [Home](../../../../index.html)
* [Books](../../books_1/index.html)
* Self Help

* [Books](../../books_1/index.html)
  + [Travel](../travel_2/index.html)
  + [Mystery](../mystery_3/index.html)
  + [Historical Fiction](../historical-fiction_4/index.html)
  + [Sequential Art](../sequential-art_5/index.html)
  + [Classics](../classics_6/index.html)
  + [Philosophy](../philosophy_7/index.html)
  + [Romance](../romance_8/index.html)
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

**firecrawl**
```
*   [Home](http://books.toscrape.com/index.html)
    
*   [Books](http://books.toscrape.com/catalogue/category/books_1/index.html)
    
*   Self Help

Self Help
=========

**5** results.

**Warning!** This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning.

1.  [![Online Marketing for Busy Authors: A Step-By-Step Guide](http://books.toscrape.com/media/cache/ea/9b/ea9b2cb8abbb317402e618445bade1e1.jpg)](http://books.toscrape.com/catalogue/online-marketing-for-busy-authors-a-step-by-step-guide_913/index.html)
    
    ### [Online Marketing for Busy ...](http://books.toscrape.com/catalogue/online-marketing-for-busy-authors-a-step-by-step-guide_913/index.html "Online Marketing for Busy Authors: A Step-By-Step Guide")
    
    £46.35
    
    In stock
    
    Add to basket
    
2.  [![How to Be Miserable: 40 Strategies You Already Use](http://books.toscrape.com/media/cache/da/8b/da8bc9b824dd3f446ef63e438ddbfc85.jpg)](http://books.toscrape.com/catalogue/how-to-be-miserable-40-strategies-you-already-use_897/index.html)
    
    ### [How to Be Miserable: ...](http://books.toscrape.com/catalogue/how-to-be-miserable-40-strategies-you-already-use_897/index.html "How to Be Miserable: 40 Strategies You Already Use")
    
    £46.03
    
    In stock
    
    Add to basket
    
3.  [![Overload: How to Unplug, Unwind, and Unleash Yourself from the Pressure of Stress](http://books.toscrape.com/media/cache/9c/da/9cda4893c7fce0c1c8eaa34fb092aa04.jpg)](http://books.toscrape.com/catalogue/overload-how-to-unplug-unwind-and-unleash-yourself-from-the-pressure-of-stress_725/index.html)
    
    ### [Overload: How to Unplug, ...](http://books.toscrape.com/catalogue/overload-how-to-unplug-unwind-and-unleash-yourself-from-the-pressure-of-stress_725/index.html "Overload: How to Unplug, Unwind, and Unleash Yourself from the Pressure of Stress")
    
    £52.15
    
    In stock
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| books.toscrape.com | 397 / 5 | 702 / 232 | 702 / 232 | 531 / 130 | 539 / 138 | 539 / 138 | 539 / 138 | 515 / 515 |
| books.toscrape.com/catalogue/a-light-in-the-attic_1000/ | 269 / 12 | 276 / 24 | 276 / 24 | 284 / 19 | 295 / 30 | 295 / 30 | 295 / 30 | 276 / 276 |
| books.toscrape.com/catalogue/category/books/academic_40 | — | — | — | — | — | — | — | 57 / 57 |
| books.toscrape.com/catalogue/category/books/add-a-comme | 424 / 8 | 745 / 235 | 745 / 235 | 558 / 133 | 567 / 142 | 567 / 142 | 567 / 142 | 558 / 558 |
| books.toscrape.com/catalogue/category/books/adult-ficti | 53 / 7 | 284 / 234 | 284 / 234 | 187 / 132 | 195 / 140 | 195 / 140 | 195 / 140 | 59 / 59 |
| books.toscrape.com/catalogue/category/books/art_25/inde | 169 / 6 | 422 / 233 | 422 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | 211 / 211 |
| books.toscrape.com/catalogue/category/books/autobiograp | 169 / 6 | 412 / 233 | 412 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | 203 / 203 |
| books.toscrape.com/catalogue/category/books/biography_3 | 145 / 6 | 410 / 233 | 410 / 233 | 279 / 131 | 286 / 138 | 286 / 138 | 286 / 138 | 193 / 193 |
| books.toscrape.com/catalogue/category/books/business_35 | — | — | — | — | — | — | — | 409 / 409 |
| books.toscrape.com/catalogue/category/books/childrens_1 | 366 / 6 | 642 / 233 | 642 / 233 | 500 / 131 | 507 / 138 | 507 / 138 | 507 / 138 | 455 / 455 |
| books.toscrape.com/catalogue/category/books/christian-f | 140 / 7 | 388 / 234 | 388 / 234 | 274 / 132 | 282 / 140 | 282 / 140 | 282 / 140 | 173 / 173 |
| books.toscrape.com/catalogue/category/books/christian_4 | 96 / 6 | 342 / 233 | 342 / 233 | 230 / 131 | 237 / 138 | 237 / 138 | 237 / 138 | 121 / 121 |
| books.toscrape.com/catalogue/category/books/classics_6/ | — | — | — | — | — | — | — | 404 / 404 |
| books.toscrape.com/catalogue/category/books/contemporar | 84 / 6 | 320 / 233 | 320 / 233 | 218 / 131 | 225 / 138 | 225 / 138 | 225 / 138 | 99 / 99 |
| books.toscrape.com/catalogue/category/books/crime_51/in | 58 / 6 | 296 / 233 | 296 / 233 | 192 / 131 | 199 / 138 | 199 / 138 | 199 / 138 | 71 / 71 |
| books.toscrape.com/catalogue/category/books/cultural_49 | 46 / 6 | 274 / 233 | 274 / 233 | 180 / 131 | 187 / 138 | 187 / 138 | 187 / 138 | 49 / 49 |
| books.toscrape.com/catalogue/category/books/default_15/ | 439 / 6 | 777 / 233 | 777 / 233 | 573 / 131 | 580 / 138 | 580 / 138 | 580 / 138 | 590 / 590 |
| books.toscrape.com/catalogue/category/books/erotica_50/ | 44 / 6 | 271 / 233 | 271 / 233 | 178 / 131 | 185 / 138 | 185 / 138 | 185 / 138 | 46 / 46 |
| books.toscrape.com/catalogue/category/books/fantasy_19/ | 436 / 6 | 764 / 233 | 764 / 233 | 570 / 131 | 577 / 138 | 577 / 138 | 577 / 138 | 577 / 577 |
| books.toscrape.com/catalogue/category/books/fiction_10/ | 365 / 6 | 636 / 233 | 636 / 233 | 499 / 131 | 506 / 138 | 506 / 138 | 506 / 138 | 449 / 449 |
| books.toscrape.com/catalogue/category/books/food-and-dr | 548 / 8 | 978 / 235 | 978 / 235 | 682 / 133 | 691 / 142 | 691 / 142 | 691 / 142 | 791 / 791 |
| books.toscrape.com/catalogue/category/books/health_47/i | 124 / 6 | 384 / 233 | 384 / 233 | 258 / 131 | 265 / 138 | 265 / 138 | 265 / 138 | 165 / 165 |
| books.toscrape.com/catalogue/category/books/historical- | 391 / 7 | 681 / 234 | 681 / 234 | 525 / 132 | 533 / 140 | 533 / 140 | 533 / 140 | 494 / 494 |
| books.toscrape.com/catalogue/category/books/historical_ | — | — | — | — | — | — | — | 92 / 92 |
| books.toscrape.com/catalogue/category/books/history_32/ | 447 / 6 | 822 / 233 | 822 / 233 | 581 / 131 | 588 / 138 | 588 / 138 | 588 / 138 | 631 / 631 |
| books.toscrape.com/catalogue/category/books/horror_31/i | 275 / 6 | 524 / 233 | 524 / 233 | 409 / 131 | 416 / 138 | 416 / 138 | 416 / 138 | 331 / 331 |
| books.toscrape.com/catalogue/category/books/humor_30/in | 239 / 6 | 529 / 233 | 529 / 233 | 373 / 131 | 380 / 138 | 380 / 138 | 380 / 138 | 322 / 322 |
| books.toscrape.com/catalogue/category/books/music_14/in | 304 / 6 | 616 / 233 | 616 / 233 | 438 / 131 | 445 / 138 | 445 / 138 | 445 / 138 | 415 / 415 |
| books.toscrape.com/catalogue/category/books/mystery_3/i | 407 / 6 | 710 / 233 | 710 / 233 | 541 / 131 | 548 / 138 | 548 / 138 | 548 / 138 | 523 / 523 |
| books.toscrape.com/catalogue/category/books/new-adult_2 | 130 / 7 | 370 / 234 | 370 / 234 | 264 / 132 | 272 / 140 | 272 / 140 | 272 / 140 | 155 / 155 |
| books.toscrape.com/catalogue/category/books/nonfiction_ | 501 / 6 | 887 / 233 | 887 / 233 | 635 / 131 | 642 / 138 | 642 / 138 | 642 / 138 | 700 / 700 |
| books.toscrape.com/catalogue/category/books/novels_46/i | 53 / 6 | 286 / 233 | 286 / 233 | 187 / 131 | 194 / 138 | 194 / 138 | 194 / 138 | 61 / 61 |
| books.toscrape.com/catalogue/category/books/paranormal_ | 52 / 6 | 284 / 233 | 284 / 233 | 186 / 131 | 193 / 138 | 193 / 138 | 193 / 138 | 59 / 59 |
| books.toscrape.com/catalogue/category/books/parenting_2 | 53 / 6 | 286 / 233 | 286 / 233 | 187 / 131 | 194 / 138 | 194 / 138 | 194 / 138 | 61 / 61 |
| books.toscrape.com/catalogue/category/books/philosophy_ | 236 / 6 | 516 / 233 | 516 / 233 | 370 / 131 | 377 / 138 | 377 / 138 | 377 / 138 | 311 / 311 |
| books.toscrape.com/catalogue/category/books/poetry_23/i | 355 / 6 | 642 / 233 | 642 / 233 | 489 / 131 | 496 / 138 | 496 / 138 | 496 / 138 | 453 / 453 |
| books.toscrape.com/catalogue/category/books/politics_48 | 94 / 6 | 340 / 233 | 340 / 233 | 228 / 131 | 235 / 138 | 235 / 138 | 235 / 138 | 119 / 119 |
| books.toscrape.com/catalogue/category/books/psychology_ | 184 / 6 | 460 / 233 | 460 / 233 | 318 / 131 | 325 / 138 | 325 / 138 | 325 / 138 | 247 / 247 |
| books.toscrape.com/catalogue/category/books/religion_12 | 180 / 6 | 453 / 233 | 453 / 233 | 314 / 131 | 321 / 138 | 321 / 138 | 321 / 138 | 240 / 240 |
| books.toscrape.com/catalogue/category/books/romance_8/i | — | — | — | — | — | — | — | 529 / 529 |
| books.toscrape.com/catalogue/category/books/science-fic | 322 / 7 | 615 / 234 | 615 / 234 | 456 / 132 | 464 / 140 | 464 / 140 | 464 / 140 | 420 / 420 |
| books.toscrape.com/catalogue/category/books/science_22/ | 350 / 6 | 690 / 233 | 690 / 233 | 484 / 131 | 491 / 138 | 491 / 138 | 491 / 138 | 491 / 491 |
| books.toscrape.com/catalogue/category/books/self-help_4 | 152 / 7 | 422 / 234 | 422 / 234 | 286 / 132 | 294 / 140 | 294 / 140 | 294 / 140 | 205 / 205 |
| books.toscrape.com/catalogue/category/books/sequential- | — | — | — | — | — | — | — | 587 / 587 |
| books.toscrape.com/catalogue/category/books/short-stori | 46 / 7 | 273 / 234 | 273 / 234 | 180 / 132 | 188 / 140 | 188 / 140 | 188 / 140 | 48 / 48 |
| books.toscrape.com/catalogue/category/books/spiritualit | 171 / 6 | 447 / 233 | 447 / 233 | 305 / 131 | 312 / 138 | 312 / 138 | 312 / 138 | 232 / 232 |
| books.toscrape.com/catalogue/category/books/sports-and- | 137 / 8 | 391 / 235 | 391 / 235 | 271 / 133 | 280 / 142 | 280 / 142 | 280 / 142 | 174 / 174 |
| books.toscrape.com/catalogue/category/books/suspense_44 | — | — | — | — | — | — | — | 59 / 59 |
| books.toscrape.com/catalogue/category/books/thriller_37 | — | — | — | — | — | — | — | 260 / 260 |
| books.toscrape.com/catalogue/category/books/travel_2/in | 258 / 6 | 550 / 233 | 550 / 233 | 392 / 131 | 399 / 138 | 399 / 138 | 399 / 138 | 345 / 345 |
| books.toscrape.com/catalogue/category/books/womens-fict | 330 / 7 | 614 / 234 | 614 / 234 | 464 / 132 | 472 / 140 | 472 / 140 | 472 / 140 | 421 / 421 |
| books.toscrape.com/catalogue/category/books/young-adult | 386 / 7 | 676 / 234 | 676 / 234 | 520 / 132 | 528 / 140 | 528 / 140 | 528 / 140 | 489 / 489 |
| books.toscrape.com/catalogue/category/books_1/index.htm | 395 / 4 | 700 / 231 | 700 / 231 | 529 / 129 | 536 / 136 | 536 / 136 | 536 / 136 | 513 / 513 |
| books.toscrape.com/catalogue/its-only-the-himalayas_981 | 448 / 11 | 480 / 22 | 480 / 22 | 463 / 18 | 473 / 28 | 473 / 28 | 473 / 28 | — |
| books.toscrape.com/catalogue/libertarianism-for-beginne | 411 / 10 | 442 / 20 | 442 / 20 | 426 / 17 | 435 / 26 | 435 / 26 | 435 / 26 | — |
| books.toscrape.com/catalogue/mesaerion-the-best-science | 500 / 15 | 530 / 29 | 530 / 29 | 515 / 22 | 528 / 35 | 528 / 35 | 528 / 35 | — |
| books.toscrape.com/catalogue/olio_984/index.html | 462 / 8 | 491 / 16 | 491 / 16 | 477 / 15 | 484 / 22 | 484 / 22 | 484 / 22 | — |
| books.toscrape.com/catalogue/our-band-could-be-your-lif | 388 / 20 | 419 / 40 | 419 / 40 | 403 / 27 | 422 / 46 | 422 / 46 | 422 / 46 | — |
| books.toscrape.com/catalogue/page-2.html | 413 / 5 | 726 / 232 | 726 / 232 | 547 / 130 | 555 / 138 | 555 / 138 | 555 / 138 | — |
| books.toscrape.com/catalogue/sapiens-a-brief-history-of | — | — | — | — | — | — | — | 489 / 489 |
| books.toscrape.com/catalogue/set-me-free_988/index.html | 365 / 11 | 411 / 21 | 411 / 21 | 380 / 18 | 389 / 27 | 389 / 27 | 389 / 27 | — |
| books.toscrape.com/catalogue/shakespeares-sonnets_989/i | 375 / 9 | 421 / 18 | 421 / 18 | 390 / 16 | 398 / 24 | 398 / 24 | 398 / 24 | — |
| books.toscrape.com/catalogue/sharp-objects_997/index.ht | 420 / 9 | 427 / 18 | 427 / 18 | 435 / 16 | 443 / 24 | 443 / 24 | 443 / 24 | 433 / 433 |
| books.toscrape.com/catalogue/soumission_998/index.html | 297 / 8 | 304 / 16 | 304 / 16 | 312 / 15 | 319 / 22 | 319 / 22 | 319 / 22 | 308 / 308 |
| books.toscrape.com/catalogue/starving-hearts-triangular | 436 / 13 | 486 / 26 | 486 / 26 | 451 / 20 | 463 / 32 | 463 / 32 | 463 / 32 | — |
| books.toscrape.com/catalogue/the-black-maria_991/index. | 696 / 10 | 742 / 20 | 742 / 20 | 711 / 17 | 720 / 26 | 720 / 26 | 720 / 26 | — |
| books.toscrape.com/catalogue/the-coming-woman-a-novel-b | 789 / 22 | 818 / 44 | 818 / 44 | 804 / 29 | 825 / 50 | 825 / 50 | 825 / 50 | 830 / 830 |
| books.toscrape.com/catalogue/the-dirty-little-secrets-o | — | — | — | — | — | — | — | 520 / 520 |
| books.toscrape.com/catalogue/the-requiem-red_995/index. | 350 / 11 | 362 / 21 | 362 / 21 | 365 / 18 | 374 / 27 | 374 / 27 | 374 / 27 | 372 / 372 |
| books.toscrape.com/catalogue/tipping-the-velvet_999/ind | 290 / 11 | 298 / 21 | 298 / 21 | 305 / 18 | 314 / 27 | 314 / 27 | 314 / 27 | 300 / 300 |

</details>

## fastapi-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 1475 | 0 | 0% | 332 | 15.9 | 11.7 | 100% | 58% |
| crawl4ai | 2815 | 1312 ⚠ | 1% | 330 | 15.8 | 11.6 | 100% | 88% |
| crawl4ai-raw | 2814 | 1311 ⚠ | 1% | 327 | 15.8 | 11.6 | 100% | 88% |
| scrapy+md | 2158 | 668 ⚠ | 0% | 588 | 15.9 | 11.7 | 100% | 58% |
| crawlee | 2462 | 905 ⚠ | 1% | 1128 | 15.8 | 11.6 | 100% | 96% |
| colly+md | 2480 | 888 ⚠ | 1% | 1135 | 15.9 | 11.7 | 100% | 98% |
| playwright | 2468 | 900 ⚠ | 1% | 1135 | 15.8 | 11.7 | 100% | 97% |
| firecrawl | 1811 | 455 ⚠ | 0% | 206 | 10.1 | 0.0 | 21% | 16% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**markcrawl** produces the cleanest output with 0 word of preamble per page, while **crawl4ai** injects 1312 words of nav chrome before content begins. The word count gap (1475 vs 2815 avg words) is largely explained by preamble: 1312 words of nav chrome account for ~47% of crawl4ai's output on this site. markcrawl's lower recall (58% vs 98%) reflects stricter content filtering — the "missed" sentences are predominantly navigation, sponsor links, and footer text that other tools include as content. For RAG, this is a net positive: fewer junk tokens per chunk means better embedding quality and retrieval precision.

<details>
<summary>Sample output — first 40 lines of <code>fastapi.tiangolo.com/advanced/json-base64-bytes</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# JSON with Bytes as Base64[¶](#json-with-bytes-as-base64 "Permanent link")

If your app needs to receive and send JSON data, but you need to include binary data in it, you can encode it as base64.

## Base64 vs Files[¶](#base64-vs-files "Permanent link")

Consider first if you can use [Request Files](../../tutorial/request-files/) for uploading binary data and [Custom Response - FileResponse](../custom-response/#fileresponse--fileresponse-) for sending binary data, instead of encoding it in JSON.

JSON can only contain UTF-8 encoded strings, so it can't contain raw bytes.

Base64 can encode binary data in strings, but to do it, it needs to use more characters than the original binary data, so it would normally be less efficient than regular files.

Use base64 only if you definitely need to include binary data in JSON, and you can't use files for that.

## Pydantic `bytes`[¶](#pydantic-bytes "Permanent link")

You can declare a Pydantic model with `bytes` fields, and then use `val_json_bytes` in the model config to tell it to use base64 to *validate* input JSON data, as part of that validation it will decode the base64 string into bytes.

Python 3.10+

```False
from fastapi import FastAPI
from pydantic import BaseModel


class DataInput(BaseModel):
    description: str
    data: bytes

    model_config = {"val_json_bytes": "base64"}

# Code here omitted 👈

app = FastAPI()


@app.post("/data")
def post_data(body: DataInput):
    content = body.data.decode("utf-8")
    return {"description": body.description, "content": content}
```

**crawl4ai**
```
[ Skip to content ](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)
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
JSON with Bytes as Base64 
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


[ ](https://fastapi.tiangolo.com/advanced/json-base64-bytes/?q= "Share")
Initializing search 
[ fastapi/fastapi 
  * 0.135.3
  * 96.9k
  * 9k
```

**crawl4ai-raw**
```
[ Skip to content ](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)
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
JSON with Bytes as Base64 
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


[ ](https://fastapi.tiangolo.com/advanced/json-base64-bytes/?q= "Share")
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
  + [Tutorial - User Guide](../../tutorial/)

    Tutorial - User Guide
    - [First Steps](../../tutorial/first-steps/)
    - [Path Parameters](../../tutorial/path-params/)
    - [Query Parameters](../../tutorial/query-params/)
    - [Request Body](../../tutorial/body/)
    - [Query Parameters and String Validations](../../tutorial/query-params-str-validations/)
    - [Path Parameters and Numeric Validations](../../tutorial/path-params-numeric-validations/)
    - [Query Parameter Models](../../tutorial/query-param-models/)
    - [Body - Multiple Parameters](../../tutorial/body-multiple-params/)
    - [Body - Fields](../../tutorial/body-fields/)
    - [Body - Nested Models](../../tutorial/body-nested-models/)
    - [Declare Request Example Data](../../tutorial/schema-extra-example/)
    - [Extra Data Types](../../tutorial/extra-data-types/)
    - [Cookie Parameters](../../tutorial/cookie-params/)
    - [Header Parameters](../../tutorial/header-params/)
    - [Cookie Parameter Models](../../tutorial/cookie-param-models/)
    - [Header Parameter Models](../../tutorial/header-param-models/)
    - [Response Model - Return Type](../../tutorial/response-model/)
    - [Extra Models](../../tutorial/extra-models/)
    - [Response Status Code](../../tutorial/response-status-code/)
    - [Form Data](../../tutorial/request-forms/)
    - [Form Models](../../tutorial/request-form-models/)
    - [Request Files](../../tutorial/request-files/)
    - [Request Forms and Files](../../tutorial/request-forms-and-files/)
    - [Handling Errors](../../tutorial/handling-errors/)
```

**crawlee**
```
JSON with Bytes as Base64 - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}













.grecaptcha-badge {
visibility: hidden;
}





[Skip to content](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)
```

**colly+md**
```
JSON with Bytes as Base64 - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}






[Skip to content](#json-with-bytes-as-base64)

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
JSON with Bytes as Base64 - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("../..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}






[Skip to content](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)

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

**firecrawl**
```
 

[Skip to content](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)

JSON with Bytes as Base64[¶](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#json-with-bytes-as-base64)

=================================================================================================================

If your app needs to receive and send JSON data, but you need to include binary data in it, you can encode it as base64.

Base64 vs Files[¶](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#base64-vs-files)

---------------------------------------------------------------------------------------------

Consider first if you can use [Request Files](https://fastapi.tiangolo.com/tutorial/request-files/)
 for uploading binary data and [Custom Response - FileResponse](https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse--fileresponse-)
 for sending binary data, instead of encoding it in JSON.

JSON can only contain UTF-8 encoded strings, so it can't contain raw bytes.

Base64 can encode binary data in strings, but to do it, it needs to use more characters than the original binary data, so it would normally be less efficient than regular files.

Use base64 only if you definitely need to include binary data in JSON, and you can't use files for that.

Pydantic `bytes`[¶](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#pydantic-bytes)

---------------------------------------------------------------------------------------------

You can declare a Pydantic model with `bytes` fields, and then use `val_json_bytes` in the model config to tell it to use base64 to _validate_ input JSON data, as part of that validation it will decode the base64 string into bytes.

[Python 3.10+](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#__tabbed_1_1)

`from fastapi import FastAPI from pydantic import BaseModel class DataInput(BaseModel):     description: str    data: bytes     model_config = {"val_json_bytes": "base64"} # Code here omitted 👈 app = FastAPI() @app.post("/data") def post_data(body: DataInput):     content = body.data.decode("utf-8")    return {"description": body.description, "content": content} # Code below omitted 👇`

👀 Full file preview

[Python 3.10+](https://fastapi.tiangolo.com/advanced/json-base64-bytes/#__tabbed_2_1)

`from fastapi import FastAPI from pydantic import BaseModel class DataInput(BaseModel):     description: str    data: bytes     model_config = {"val_json_bytes": "base64"} class DataOutput(BaseModel):     description: str    data: bytes     model_config = {"ser_json_bytes": "base64"} class DataInputOutput(BaseModel):     description: str    data: bytes     model_config = {        "val_json_bytes": "base64",        "ser_json_bytes": "base64",    } app = FastAPI() @app.post("/data") def post_data(body: DataInput):     content = body.data.decode("utf-8")    return {"description": body.description, "content": content} @app.get("/data") def get_data() -> DataOutput:     data = "hello".encode("utf-8")    return DataOutput(description="A plumbus", data=data) @app.post("/data-in-out") def post_data_in_out(body: DataInputOutput) -> DataInputOutput:     return body`
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| fastapi.tiangolo.com | 2230 / 0 | 3991 / 1538 | 3979 / 1526 | 3092 / 839 | 3374 / 1071 | 3404 / 1054 | 3357 / 1054 | 2388 / 196 |
| fastapi.tiangolo.com/?q= | — | — | — | — | — | — | — | 2388 / 196 |
| fastapi.tiangolo.com/_llm-test | — | — | — | — | — | — | — | 1598 / 678 |
| fastapi.tiangolo.com/_llm-test/?q= | — | — | — | — | — | — | — | 1598 / 678 |
| fastapi.tiangolo.com/about | 15 / 0 | 1303 / 1241 | 1303 / 1241 | 677 / 646 | 1013 / 880 | 998 / 863 | 1008 / 875 | 16 / 16 |
| fastapi.tiangolo.com/advanced | 115 / 0 | 1415 / 1261 | 1415 / 1261 | 792 / 661 | 1124 / 899 | 1113 / 882 | 1119 / 894 | 113 / 113 |
| fastapi.tiangolo.com/advanced/additional-responses | 1274 / 0 | 2648 / 1332 | 2648 / 1332 | 2008 / 718 | 2342 / 958 | 2337 / 941 | 2337 / 953 | 1264 / 1264 |
| fastapi.tiangolo.com/advanced/additional-status-codes | 472 / 0 | 1794 / 1278 | 1794 / 1278 | 1165 / 677 | 1502 / 915 | 1491 / 898 | 1497 / 910 | 466 / 466 |
| fastapi.tiangolo.com/advanced/advanced-dependencies | 2200 / 0 | 3658 / 1432 | 3658 / 1432 | 3012 / 796 | 3330 / 1034 | 3335 / 1015 | 3323 / 1027 | 2172 / 882 |
| fastapi.tiangolo.com/advanced/advanced-python-types | 330 / 0 | 1642 / 1266 | 1642 / 1266 | 1015 / 669 | 1353 / 907 | 1340 / 890 | 1348 / 902 | 323 / 323 |
| fastapi.tiangolo.com/advanced/async-sql-databases | — | — | — | — | — | — | — | 8 / 8 |
| fastapi.tiangolo.com/advanced/async-tests | 646 / 0 | 1991 / 1308 | 1991 / 1308 | 1354 / 692 | 1682 / 928 | 1678 / 911 | 1677 / 923 | 639 / 639 |
| fastapi.tiangolo.com/advanced/behind-a-proxy | 2218 / 0 | 3672 / 1478 | 3672 / 1478 | 3055 / 821 | 3318 / 1061 | 3378 / 1042 | 3381 / 1054 | 2188 / 147 |
| fastapi.tiangolo.com/advanced/conditional-openapi | — | — | — | — | — | — | — | 376 / 376 |
| fastapi.tiangolo.com/advanced/custom-request-and-route | — | — | — | — | — | — | — | 1483 / 137 |
| fastapi.tiangolo.com/advanced/custom-response | 1987 / 0 | 3457 / 1448 | 3457 / 1448 | 2782 / 779 | 3095 / 1025 | 3116 / 1008 | 3090 / 1020 | 1965 / 293 |
| fastapi.tiangolo.com/advanced/dataclasses | 778 / 0 | 2115 / 1296 | 2115 / 1296 | 1482 / 688 | 1813 / 926 | 1804 / 907 | 1806 / 919 | 779 / 779 |
| fastapi.tiangolo.com/advanced/events | 1500 / 0 | 2886 / 1356 | 2886 / 1356 | 2240 / 724 | 2554 / 960 | 2559 / 943 | 2549 / 955 | 1468 / 543 |
| fastapi.tiangolo.com/advanced/extending-openapi | — | — | — | — | — | — | — | 736 / 263 |
| fastapi.tiangolo.com/advanced/generate-clients | 1654 / 0 | 3179 / 1482 | 3177 / 1480 | 2498 / 828 | 2810 / 1066 | 2823 / 1047 | 2803 / 1059 | 1620 / 350 |
| fastapi.tiangolo.com/advanced/graphql | — | — | — | — | — | — | — | 361 / 361 |
| fastapi.tiangolo.com/advanced/json-base64-bytes | 743 / 0 | 2096 / 1314 | 2096 / 1314 | 1462 / 703 | 1799 / 947 | 1790 / 928 | 1792 / 940 | 721 / 721 |
| fastapi.tiangolo.com/advanced/middleware | 597 / 0 | 1942 / 1306 | 1942 / 1306 | 1303 / 690 | 1628 / 926 | 1625 / 909 | 1623 / 921 | 578 / 578 |
| fastapi.tiangolo.com/advanced/openapi-callbacks | 1746 / 0 | 3155 / 1376 | 3155 / 1376 | 2510 / 748 | 2831 / 986 | 2832 / 967 | 2824 / 979 | 1710 / 814 |
| fastapi.tiangolo.com/advanced/openapi-webhooks | 519 / 0 | 1868 / 1304 | 1868 / 1304 | 1231 / 696 | 1564 / 934 | 1555 / 915 | 1557 / 927 | 512 / 478 |
| fastapi.tiangolo.com/advanced/path-operation-advanced-c | 1323 / 0 | 2727 / 1374 | 2727 / 1374 | 2083 / 744 | 2405 / 984 | 2408 / 967 | 2400 / 979 | 1293 / 72 |
| fastapi.tiangolo.com/advanced/response-change-status-co | 292 / 0 | 1612 / 1280 | 1612 / 1280 | 985 / 677 | 1324 / 921 | 1311 / 902 | 1317 / 914 | 288 / 288 |
| fastapi.tiangolo.com/advanced/response-cookies | 376 / 0 | 1704 / 1288 | 1704 / 1288 | 1076 / 684 | 1407 / 920 | 1398 / 903 | 1402 / 915 | 369 / 290 |
| fastapi.tiangolo.com/advanced/response-directly | 737 / 0 | 2099 / 1322 | 2099 / 1322 | 1461 / 708 | 1796 / 948 | 1791 / 931 | 1791 / 943 | 723 / 723 |
| fastapi.tiangolo.com/advanced/response-headers | 351 / 0 | 1682 / 1290 | 1680 / 1288 | 1051 / 684 | 1383 / 920 | 1374 / 903 | 1378 / 915 | 345 / 345 |
| fastapi.tiangolo.com/advanced/security | 90 / 0 | 1397 / 1267 | 1395 / 1265 | 770 / 664 | 1101 / 900 | 1090 / 883 | 1096 / 895 | — |
| fastapi.tiangolo.com/advanced/security/http-basic-auth | 1169 / 0 | 2553 / 1351 | 2553 / 1351 | 1913 / 728 | 2240 / 968 | 2237 / 949 | 2233 / 961 | — |
| fastapi.tiangolo.com/advanced/security/oauth2-scopes | 8989 / 0 | 10452 / 1443 | 10452 / 1443 | 9798 / 793 | 10106 / 1029 | 10119 / 1012 | 10101 / 1024 | — |
| fastapi.tiangolo.com/advanced/settings | 2182 / 0 | 3542 / 1470 | 3544 / 1472 | 3006 / 808 | 3193 / 1050 | 3330 / 1031 | 3317 / 1043 | 1994 / 173 |
| fastapi.tiangolo.com/advanced/sql-databases-peewee | — | — | — | — | — | — | — | 8 / 8 |
| fastapi.tiangolo.com/advanced/stream-data | 2723 / 0 | 4109 / 1354 | 4109 / 1354 | 3465 / 726 | 3785 / 962 | 3788 / 945 | 3780 / 957 | 2672 / 544 |
| fastapi.tiangolo.com/advanced/strict-content-type | 522 / 0 | 1858 / 1296 | 1858 / 1296 | 1225 / 687 | 1557 / 925 | 1550 / 908 | 1552 / 920 | 505 / 505 |
| fastapi.tiangolo.com/advanced/sub-applications | 463 / 0 | 1831 / 1328 | 1829 / 1326 | 1187 / 708 | 1519 / 950 | 1512 / 931 | 1512 / 943 | 452 / 73 |
| fastapi.tiangolo.com/advanced/sub-applications-proxy | — | — | — | — | — | — | — | 8 / 8 |
| fastapi.tiangolo.com/advanced/templates | 558 / 0 | 1919 / 1328 | 1913 / 1326 | 1281 / 707 | 1599 / 941 | 1599 / 924 | 1598 / 936 | 528 / 310 |
| fastapi.tiangolo.com/advanced/testing-database | — | — | — | — | — | — | — | 46 / 46 |
| fastapi.tiangolo.com/advanced/testing-dependencies | 694 / 0 | 2036 / 1298 | 2034 / 1296 | 1400 / 690 | 1738 / 930 | 1729 / 913 | 1733 / 925 | — |
| fastapi.tiangolo.com/advanced/testing-events | 263 / 0 | 1562 / 1253 | 1562 / 1253 | 929 / 650 | 1276 / 896 | 1261 / 879 | 1259 / 879 | — |
| fastapi.tiangolo.com/advanced/testing-websockets | 117 / 0 | 1414 / 1248 | 1414 / 1248 | 783 / 650 | 1123 / 886 | 1108 / 869 | 1118 / 881 | — |
| fastapi.tiangolo.com/advanced/using-request-directly | 357 / 0 | 1692 / 1296 | 1692 / 1296 | 1063 / 690 | 1397 / 930 | 1388 / 913 | 1392 / 925 | — |
| fastapi.tiangolo.com/advanced/vibe | 389 / 0 | 1717 / 1280 | 1717 / 1280 | 1081 / 676 | 1411 / 912 | 1402 / 895 | 1406 / 907 | — |
| fastapi.tiangolo.com/advanced/websockets | 1638 / 0 | 3050 / 1374 | 3046 / 1374 | 2397 / 743 | 2714 / 979 | 2714 / 960 | 2711 / 972 | — |
| fastapi.tiangolo.com/advanced/wsgi | 247 / 0 | 1567 / 1280 | 1565 / 1278 | 937 / 674 | 1276 / 918 | 1265 / 901 | 1271 / 913 | — |
| fastapi.tiangolo.com/alternatives | 3293 / 0 | 4759 / 1460 | 4757 / 1458 | 4087 / 778 | 4381 / 1018 | 4412 / 1001 | 4376 / 1013 | 3264 / 126 |
| fastapi.tiangolo.com/alternatives/?q= | — | — | — | — | — | — | — | 3264 / 126 |
| fastapi.tiangolo.com/async | 3651 / 0 | 5200 / 1486 | 5198 / 1484 | 4478 / 811 | 4780 / 1053 | 4805 / 1036 | 4775 / 1048 | 3641 / 694 |
| fastapi.tiangolo.com/async/?q= | — | — | — | — | — | — | — | 3641 / 694 |
| fastapi.tiangolo.com/benchmarks | 525 / 0 | 1831 / 1256 | 1829 / 1254 | 1202 / 661 | 1535 / 895 | 1522 / 878 | 1530 / 890 | 525 / 525 |
| fastapi.tiangolo.com/benchmarks/?q= | — | — | — | — | — | — | — | 525 / 525 |
| fastapi.tiangolo.com/contributing | 1599 / 0 | 3123 / 1496 | 3116 / 1494 | 2438 / 823 | 2753 / 1061 | 2765 / 1044 | 2753 / 1056 | 1575 / 50 |
| fastapi.tiangolo.com/contributing/?q= | — | — | — | — | — | — | — | 1576 / 50 |
| fastapi.tiangolo.com/de | — | — | — | — | — | — | — | 2331 / 251 |
| fastapi.tiangolo.com/de/?q= | — | — | — | — | — | — | — | 2331 / 251 |
| fastapi.tiangolo.com/de/about | — | — | — | — | — | — | — | 62 / 62 |
| fastapi.tiangolo.com/de/advanced | — | — | — | — | — | — | — | 150 / 150 |
| fastapi.tiangolo.com/de/advanced/additional-responses | — | — | — | — | — | — | — | 1242 / 1242 |
| fastapi.tiangolo.com/de/advanced/additional-status-code | — | — | — | — | — | — | — | 488 / 488 |
| fastapi.tiangolo.com/de/advanced/advanced-dependencies | — | — | — | — | — | — | — | 2108 / 897 |
| fastapi.tiangolo.com/de/advanced/async-tests | — | — | — | — | — | — | — | 672 / 672 |
| fastapi.tiangolo.com/de/advanced/behind-a-proxy | — | — | — | — | — | — | — | 2062 / 178 |
| fastapi.tiangolo.com/de/advanced/custom-response | — | — | — | — | — | — | — | 1907 / 300 |
| fastapi.tiangolo.com/de/advanced/dataclasses | — | — | — | — | — | — | — | 773 / 773 |
| fastapi.tiangolo.com/de/advanced/events | — | — | — | — | — | — | — | 1441 / 580 |
| fastapi.tiangolo.com/de/advanced/middleware | — | — | — | — | — | — | — | 599 / 599 |
| fastapi.tiangolo.com/de/advanced/openapi-callbacks | — | — | — | — | — | — | — | 1692 / 823 |
| fastapi.tiangolo.com/de/advanced/openapi-webhooks | — | — | — | — | — | — | — | 527 / 494 |
| fastapi.tiangolo.com/de/advanced/path-operation-advance | — | — | — | — | — | — | — | 1247 / 113 |
| fastapi.tiangolo.com/de/advanced/response-change-status | — | — | — | — | — | — | — | 314 / 314 |
| fastapi.tiangolo.com/de/advanced/response-cookies | — | — | — | — | — | — | — | 397 / 318 |
| fastapi.tiangolo.com/de/advanced/response-directly | — | — | — | — | — | — | — | 735 / 735 |
| fastapi.tiangolo.com/de/advanced/response-headers | — | — | — | — | — | — | — | 377 / 377 |
| fastapi.tiangolo.com/de/advanced/security | — | — | — | — | — | — | — | 129 / 129 |
| fastapi.tiangolo.com/de/advanced/security/http-basic-au | — | — | — | — | — | — | — | 1193 / 599 |
| fastapi.tiangolo.com/de/advanced/security/oauth2-scopes | — | — | — | — | — | — | — | 8872 / 8872 |
| fastapi.tiangolo.com/de/advanced/settings | — | — | — | — | — | — | — | 1942 / 204 |
| fastapi.tiangolo.com/de/advanced/stream-data | — | — | — | — | — | — | — | 2629 / 568 |
| fastapi.tiangolo.com/de/advanced/sub-applications | — | — | — | — | — | — | — | 470 / 115 |
| fastapi.tiangolo.com/de/advanced/templates | — | — | — | — | — | — | — | 557 / 356 |
| fastapi.tiangolo.com/de/advanced/testing-dependencies | — | — | — | — | — | — | — | 714 / 125 |
| fastapi.tiangolo.com/de/advanced/testing-events | — | — | — | — | — | — | — | 300 / 300 |
| fastapi.tiangolo.com/de/advanced/testing-websockets | — | — | — | — | — | — | — | 163 / 163 |
| fastapi.tiangolo.com/de/advanced/using-request-directly | — | — | — | — | — | — | — | 369 / 369 |
| fastapi.tiangolo.com/de/advanced/websockets | — | — | — | — | — | — | — | 1653 / 90 |
| fastapi.tiangolo.com/de/async | — | — | — | — | — | — | — | 3599 / 729 |
| fastapi.tiangolo.com/de/environment-variables | — | — | — | — | — | — | — | 1062 / 776 |
| fastapi.tiangolo.com/de/fastapi-people | — | — | — | — | — | — | — | 2188 / 285 |
| fastapi.tiangolo.com/de/features | — | — | — | — | — | — | — | 1129 / 57 |
| fastapi.tiangolo.com/de/learn | — | — | — | — | — | — | — | 82 / 82 |
| fastapi.tiangolo.com/de/python-types | — | — | — | — | — | — | — | 1840 / 260 |
| fastapi.tiangolo.com/de/reference | — | — | — | — | — | — | — | 45 / 45 |
| fastapi.tiangolo.com/de/release-notes | — | — | — | — | — | — | — | 56324 / 12 |
| fastapi.tiangolo.com/de/resources | — | — | — | — | — | — | — | 60 / 60 |
| fastapi.tiangolo.com/de/tutorial | — | — | — | — | — | — | — | 537 / 537 |
| fastapi.tiangolo.com/de/tutorial/background-tasks | — | — | — | — | — | — | — | 951 / 951 |
| fastapi.tiangolo.com/de/tutorial/bigger-applications | — | — | — | — | — | — | — | 3273 / 506 |
| fastapi.tiangolo.com/de/tutorial/body | — | — | — | — | — | — | — | 1150 / 1150 |
| fastapi.tiangolo.com/de/tutorial/body-fields | — | — | — | — | — | — | — | 659 / 659 |
| fastapi.tiangolo.com/de/tutorial/body-multiple-params | — | — | — | — | — | — | — | 1353 / 1353 |
| fastapi.tiangolo.com/de/tutorial/body-nested-models | — | — | — | — | — | — | — | 1384 / 170 |
| fastapi.tiangolo.com/de/tutorial/body-updates | — | — | — | — | — | — | — | 1022 / 215 |
| fastapi.tiangolo.com/de/tutorial/cookie-param-models | — | — | — | — | — | — | — | 592 / 592 |
| fastapi.tiangolo.com/de/tutorial/cookie-params | — | — | — | — | — | — | — | 379 / 379 |
| fastapi.tiangolo.com/de/tutorial/cors | — | — | — | — | — | — | — | 746 / 631 |
| fastapi.tiangolo.com/de/tutorial/debugging | — | — | — | — | — | — | — | 416 / 116 |
| fastapi.tiangolo.com/de/tutorial/dependencies | — | — | — | — | — | — | — | 1712 / 229 |
| fastapi.tiangolo.com/de/tutorial/dependencies/classes-a | — | — | — | — | — | — | — | 1940 / 1940 |
| fastapi.tiangolo.com/de/tutorial/dependencies/dependenc | — | — | — | — | — | — | — | 895 / 378 |
| fastapi.tiangolo.com/de/tutorial/dependencies/dependenc | — | — | — | — | — | — | — | 2488 / 1257 |
| fastapi.tiangolo.com/de/tutorial/dependencies/global-de | — | — | — | — | — | — | — | 303 / 303 |
| fastapi.tiangolo.com/de/tutorial/dependencies/sub-depen | — | — | — | — | — | — | — | 871 / 871 |
| fastapi.tiangolo.com/de/tutorial/encoder | — | — | — | — | — | — | — | 308 / 308 |
| fastapi.tiangolo.com/de/tutorial/extra-data-types | — | — | — | — | — | — | — | 711 / 711 |
| fastapi.tiangolo.com/de/tutorial/extra-models | — | — | — | — | — | — | — | 1158 / 243 |
| fastapi.tiangolo.com/de/tutorial/first-steps | — | — | — | — | — | — | — | 1659 / 232 |
| fastapi.tiangolo.com/de/tutorial/handling-errors | — | — | — | — | — | — | — | 1622 / 206 |
| fastapi.tiangolo.com/de/tutorial/header-param-models | — | — | — | — | — | — | — | 689 / 689 |
| fastapi.tiangolo.com/de/tutorial/header-params | — | — | — | — | — | — | — | 693 / 693 |
| fastapi.tiangolo.com/de/tutorial/metadata | — | — | — | — | — | — | — | 1085 / 628 |
| fastapi.tiangolo.com/de/tutorial/middleware | — | — | — | — | — | — | — | 618 / 376 |
| fastapi.tiangolo.com/de/tutorial/path-operation-configu | — | — | — | — | — | — | — | 884 / 306 |
| fastapi.tiangolo.com/de/tutorial/path-params | — | — | — | — | — | — | — | 1421 / 654 |
| fastapi.tiangolo.com/de/tutorial/path-params-numeric-va | — | — | — | — | — | — | — | 1699 / 937 |
| fastapi.tiangolo.com/de/tutorial/query-param-models | — | — | — | — | — | — | — | 533 / 533 |
| fastapi.tiangolo.com/de/tutorial/query-params | — | — | — | — | — | — | — | 815 / 815 |
| fastapi.tiangolo.com/de/tutorial/query-params-str-valid | — | — | — | — | — | — | — | 3890 / 194 |
| fastapi.tiangolo.com/de/tutorial/request-files | — | — | — | — | — | — | — | 1741 / 599 |
| fastapi.tiangolo.com/de/tutorial/request-form-models | — | — | — | — | — | — | — | 461 / 461 |
| fastapi.tiangolo.com/de/tutorial/request-forms | — | — | — | — | — | — | — | 491 / 491 |
| fastapi.tiangolo.com/de/tutorial/request-forms-and-file | — | — | — | — | — | — | — | 406 / 406 |
| fastapi.tiangolo.com/de/tutorial/response-model | — | — | — | — | — | — | — | 2918 / 611 |
| fastapi.tiangolo.com/de/tutorial/response-status-code | — | — | — | — | — | — | — | 638 / 638 |
| fastapi.tiangolo.com/de/tutorial/schema-extra-example | — | — | — | — | — | — | — | 1940 / 420 |
| fastapi.tiangolo.com/de/tutorial/security | — | — | — | — | — | — | — | 701 / 219 |
| fastapi.tiangolo.com/de/tutorial/security/first-steps | — | — | — | — | — | — | — | 1514 / 1214 |
| fastapi.tiangolo.com/de/tutorial/security/get-current-u | — | — | — | — | — | — | — | 1525 / 1525 |
| fastapi.tiangolo.com/de/tutorial/security/oauth2-jwt | — | — | — | — | — | — | — | 4388 / 391 |
| fastapi.tiangolo.com/de/tutorial/security/simple-oauth2 | — | — | — | — | — | — | — | 3511 / 196 |
| fastapi.tiangolo.com/de/tutorial/server-sent-events | — | — | — | — | — | — | — | 1441 / 623 |
| fastapi.tiangolo.com/de/tutorial/sql-databases | — | — | — | — | — | — | — | 10410 / 323 |
| fastapi.tiangolo.com/de/tutorial/static-files | — | — | — | — | — | — | — | 284 / 125 |
| fastapi.tiangolo.com/de/tutorial/stream-json-lines | — | — | — | — | — | — | — | 1226 / 863 |
| fastapi.tiangolo.com/de/tutorial/testing | — | — | — | — | — | — | — | 1480 / 338 |
| fastapi.tiangolo.com/de/virtual-environments | — | — | — | — | — | — | — | 2916 / 1039 |
| fastapi.tiangolo.com/deployment | 240 / 0 | 1542 / 1259 | 1540 / 1257 | 915 / 659 | 1245 / 893 | 1234 / 876 | 1240 / 888 | — |
| fastapi.tiangolo.com/deployment/cloud | 142 / 0 | 1468 / 1280 | 1466 / 1278 | 833 / 675 | 1174 / 917 | 1163 / 900 | 1169 / 912 | — |
| fastapi.tiangolo.com/deployment/concepts | 3066 / 0 | 4701 / 1608 | 4699 / 1606 | 3988 / 906 | 4274 / 1142 | 4313 / 1125 | 4269 / 1137 | — |
| fastapi.tiangolo.com/deployment/docker | 4157 / 0 | 5539 / 1724 | 5537 / 1722 | 5156 / 983 | 5068 / 1225 | 5488 / 1208 | 5417 / 1220 | — |
| fastapi.tiangolo.com/deployment/fastapicloud | 295 / 0 | 1650 / 1308 | 1637 / 1306 | 1005 / 694 | 1310 / 932 | 1326 / 913 | 1334 / 925 | — |
| fastapi.tiangolo.com/deployment/https | 2093 / 0 | 3541 / 1396 | 3541 / 1396 | 2857 / 748 | 3166 / 984 | 3179 / 967 | 3161 / 979 | — |
| fastapi.tiangolo.com/deployment/manually | 798 / 0 | 2132 / 1332 | 2052 / 1332 | 1528 / 714 | 1734 / 954 | 1852 / 937 | 1809 / 949 | — |
| fastapi.tiangolo.com/deployment/server-workers | 864 / 0 | 2029 / 1296 | 2026 / 1296 | 1564 / 684 | 1725 / 928 | 1898 / 911 | 1798 / 923 | — |
| fastapi.tiangolo.com/deployment/versions | 537 / 0 | 1888 / 1320 | 1886 / 1318 | 1254 / 701 | 1578 / 939 | 1575 / 922 | 1573 / 934 | — |
| fastapi.tiangolo.com/editor-support | 310 / 0 | 1621 / 1274 | 1621 / 1274 | 998 / 672 | 1326 / 908 | 1317 / 891 | 1321 / 903 | 309 / 98 |
| fastapi.tiangolo.com/editor-support/?q= | — | — | — | — | — | — | — | 317 / 102 |
| fastapi.tiangolo.com/environment-variables | 1134 / 0 | 2464 / 1326 | 2449 / 1326 | 1862 / 712 | 2110 / 948 | 2185 / 931 | 2217 / 943 | 1116 / 807 |
| fastapi.tiangolo.com/es | — | — | — | — | — | — | — | 2504 / 263 |
| fastapi.tiangolo.com/es/advanced | — | — | — | — | — | — | — | 156 / 156 |
| fastapi.tiangolo.com/es/async | — | — | — | — | — | — | — | 3629 / 751 |
| fastapi.tiangolo.com/es/features | — | — | — | — | — | — | — | 1294 / 60 |
| fastapi.tiangolo.com/es/python-types | — | — | — | — | — | — | — | 1843 / 259 |
| fastapi.tiangolo.com/es/tutorial | — | — | — | — | — | — | — | 550 / 550 |
| fastapi.tiangolo.com/external-links | 699 / 0 | 1999 / 1254 | 1999 / 1254 | 1375 / 660 | 1714 / 898 | 1699 / 879 | 1707 / 891 | 798 / 798 |
| fastapi.tiangolo.com/external-links/?q= | — | — | — | — | — | — | — | 802 / 802 |
| fastapi.tiangolo.com/fastapi-cli | 658 / 0 | 1930 / 1296 | 1825 / 1296 | 1364 / 690 | 1521 / 926 | 1684 / 909 | 1621 / 921 | 574 / 312 |
| fastapi.tiangolo.com/fastapi-cli/?q= | — | — | — | — | — | — | — | 650 / 382 |
| fastapi.tiangolo.com/fastapi-people | 1434 / 0 | 3347 / 1430 | 3347 / 1430 | 2230 / 780 | 2536 / 1018 | 2551 / 999 | 2529 / 1011 | 2189 / 286 |
| fastapi.tiangolo.com/fastapi-people/?q= | — | — | — | — | — | — | — | 2223 / 294 |
| fastapi.tiangolo.com/features | 1154 / 0 | 2569 / 1366 | 2569 / 1366 | 1899 / 729 | 2204 / 963 | 2215 / 946 | 2199 / 958 | 1171 / 17 |
| fastapi.tiangolo.com/fr | — | — | — | — | — | — | — | 2697 / 301 |
| fastapi.tiangolo.com/help-fastapi | 1955 / 0 | 3521 / 1566 | 3519 / 1564 | 2842 / 875 | 3139 / 1117 | 3172 / 1100 | 3134 / 1112 | 1928 / 578 |
| fastapi.tiangolo.com/help-fastapi/?q= | — | — | — | — | — | — | — | 1928 / 578 |
| fastapi.tiangolo.com/history-design-future | 619 / 0 | 1946 / 1296 | 1946 / 1296 | 1315 / 680 | 1645 / 922 | 1640 / 903 | 1638 / 915 | 612 / 612 |
| fastapi.tiangolo.com/history-design-future/?q= | — | — | — | — | — | — | — | 612 / 612 |
| fastapi.tiangolo.com/how-to | 97 / 0 | 1400 / 1251 | 1400 / 1251 | 764 / 651 | 1112 / 893 | 1095 / 874 | 1105 / 886 | — |
| fastapi.tiangolo.com/how-to/authentication-error-status | 194 / 0 | 1494 / 1256 | 1492 / 1254 | 861 / 651 | 1206 / 897 | 1191 / 880 | 1201 / 892 | — |
| fastapi.tiangolo.com/how-to/conditional-openapi | 380 / 0 | 1715 / 1289 | 1713 / 1287 | 1083 / 687 | 1422 / 925 | 1406 / 906 | 1415 / 918 | — |
| fastapi.tiangolo.com/how-to/configure-swagger-ui | 1564 / 0 | 2925 / 1319 | 2923 / 1317 | 2284 / 704 | 2616 / 942 | 2611 / 925 | 2611 / 937 | — |
| fastapi.tiangolo.com/how-to/custom-docs-ui-assets | 1532 / 0 | 3044 / 1481 | 3044 / 1481 | 2377 / 829 | 2702 / 1075 | 2713 / 1056 | 2695 / 1068 | — |
| fastapi.tiangolo.com/how-to/custom-request-and-route | 1510 / 0 | 2896 / 1355 | 2896 / 1355 | 2262 / 736 | 2590 / 978 | 2587 / 961 | 2585 / 973 | — |
| fastapi.tiangolo.com/how-to/extending-openapi | 759 / 0 | 2147 / 1351 | 2145 / 1349 | 1500 / 725 | 1828 / 963 | 1827 / 944 | 1821 / 956 | — |
| fastapi.tiangolo.com/how-to/general | 353 / 0 | 1806 / 1419 | 1806 / 1419 | 1152 / 783 | 1482 / 1027 | 1487 / 1010 | 1477 / 1022 | — |
| fastapi.tiangolo.com/how-to/graphql | 364 / 0 | 1705 / 1295 | 1705 / 1295 | 1068 / 688 | 1401 / 922 | 1394 / 905 | 1396 / 917 | — |
| fastapi.tiangolo.com/how-to/migrate-from-pydantic-v1-to | 944 / 0 | 2267 / 1369 | 2267 / 1369 | 1698 / 738 | 1955 / 986 | 2031 / 967 | 2025 / 979 | — |
| fastapi.tiangolo.com/how-to/separate-openapi-schemas | 887 / 0 | 2345 / 1411 | 2345 / 1411 | 1679 / 776 | 2016 / 1028 | 2017 / 1009 | 2009 / 1021 | — |
| fastapi.tiangolo.com/how-to/testing-database | 42 / 0 | 1342 / 1250 | 1342 / 1250 | 709 / 651 | 1052 / 889 | 1037 / 872 | 1047 / 884 | — |
| fastapi.tiangolo.com/ja | — | — | — | — | — | — | — | 1308 / 95 |
| fastapi.tiangolo.com/ko | — | — | — | — | — | — | — | 2003 / 202 |
| fastapi.tiangolo.com/learn | 35 / 0 | 1324 / 1243 | 1322 / 1241 | 697 / 646 | 1030 / 880 | 1015 / 863 | 1025 / 875 | — |
| fastapi.tiangolo.com/management | 215 / 0 | 1535 / 1280 | 1535 / 1280 | 905 / 674 | 1231 / 910 | 1224 / 893 | 1226 / 905 | 214 / 214 |
| fastapi.tiangolo.com/management-tasks | 1798 / 0 | 3193 / 1370 | 3193 / 1370 | 2553 / 739 | 2871 / 977 | 2876 / 960 | 2866 / 972 | 1787 / 142 |
| fastapi.tiangolo.com/management-tasks/?q= | — | — | — | — | — | — | — | 1787 / 142 |
| fastapi.tiangolo.com/management/?q= | — | — | — | — | — | — | — | 214 / 214 |
| fastapi.tiangolo.com/newsletter | 10 / 0 | 1301 / 1246 | 1299 / 1244 | 672 / 646 | 1014 / 888 | 997 / 869 | 1007 / 881 | 11 / 11 |
| fastapi.tiangolo.com/newsletter/?q= | — | — | — | — | — | — | — | 11 / 11 |
| fastapi.tiangolo.com/project-generation | 253 / 0 | 1568 / 1272 | 1568 / 1272 | 945 / 676 | 1283 / 916 | 1270 / 899 | 1278 / 911 | 254 / 254 |
| fastapi.tiangolo.com/project-generation/?q= | — | — | — | — | — | — | — | 254 / 254 |
| fastapi.tiangolo.com/pt | — | — | — | — | — | — | — | 2504 / 260 |
| fastapi.tiangolo.com/pt/alternatives | — | — | — | — | — | — | — | 3483 / 173 |
| fastapi.tiangolo.com/pt/benchmarks | — | — | — | — | — | — | — | 591 / 591 |
| fastapi.tiangolo.com/pt/features | — | — | — | — | — | — | — | 1329 / 67 |
| fastapi.tiangolo.com/pt/history-design-future | — | — | — | — | — | — | — | 667 / 667 |
| fastapi.tiangolo.com/pt/tutorial | — | — | — | — | — | — | — | 568 / 568 |
| fastapi.tiangolo.com/python-types | 1892 / 0 | 3339 / 1424 | 3337 / 1422 | 2671 / 763 | 2976 / 1001 | 2995 / 984 | 2971 / 996 | 1829 / 209 |
| fastapi.tiangolo.com/python-types/?q= | — | — | — | — | — | — | — | 1829 / 209 |
| fastapi.tiangolo.com/reference | 44 / 0 | 1336 / 1243 | 1334 / 1241 | 706 / 646 | 1044 / 880 | 1029 / 863 | 1039 / 875 | — |
| fastapi.tiangolo.com/reference/apirouter | 24889 / 0 | 26605 / 1406 | 26603 / 1404 | 25651 / 746 | 25969 / 982 | 25976 / 965 | 25964 / 977 | — |
| fastapi.tiangolo.com/reference/background | 375 / 0 | 1717 / 1300 | 1715 / 1298 | 1079 / 688 | 1416 / 928 | 1403 / 911 | 1411 / 923 | — |
| fastapi.tiangolo.com/reference/dependencies | 1517 / 0 | 2839 / 1280 | 2837 / 1278 | 2206 / 673 | 2548 / 917 | 2535 / 898 | 2541 / 910 | — |
| fastapi.tiangolo.com/reference/encoders | 1117 / 0 | 2415 / 1252 | 2415 / 1252 | 1792 / 659 | 2133 / 899 | 2116 / 880 | 2126 / 892 | — |
| fastapi.tiangolo.com/reference/exceptions | 746 / 0 | 2099 / 1310 | 2097 / 1308 | 1455 / 693 | 1795 / 935 | 1784 / 918 | 1790 / 930 | — |
| fastapi.tiangolo.com/reference/fastapi | 29527 / 0 | 31324 / 1456 | 31322 / 1454 | 30321 / 778 | 30631 / 1014 | 30640 / 997 | 30626 / 1009 | — |
| fastapi.tiangolo.com/reference/httpconnection | 292 / 0 | 1671 / 1336 | 1669 / 1334 | 1022 / 714 | 1356 / 950 | 1341 / 933 | 1351 / 945 | — |
| fastapi.tiangolo.com/reference/middleware | 1030 / 0 | 2490 / 1410 | 2490 / 1410 | 1811 / 765 | 2152 / 1001 | 2135 / 982 | 2145 / 994 | — |
| fastapi.tiangolo.com/reference/openapi | 32 / 0 | 1322 / 1247 | 1320 / 1245 | 696 / 648 | 1028 / 882 | 1013 / 865 | 1023 / 877 | — |
| fastapi.tiangolo.com/reference/openapi/docs | 1757 / 0 | 3076 / 1276 | 3074 / 1274 | 2445 / 672 | 2781 / 910 | 2764 / 891 | 2774 / 903 | 1717 / 1717 |
| fastapi.tiangolo.com/reference/openapi/models | 3708 / 0 | 7396 / 3188 | 7394 / 3186 | 5672 / 1948 | 6007 / 2184 | 5992 / 2167 | 6002 / 2179 | — |
| fastapi.tiangolo.com/reference/parameters | 12456 / 0 | 13851 / 1288 | 13849 / 1286 | 13154 / 682 | 13489 / 918 | 13474 / 901 | 13484 / 913 | — |
| fastapi.tiangolo.com/reference/request | 680 / 0 | 2124 / 1390 | 2122 / 1388 | 1446 / 750 | 1782 / 986 | 1767 / 969 | 1777 / 981 | — |
| fastapi.tiangolo.com/reference/response | 651 / 0 | 2014 / 1312 | 2012 / 1310 | 1365 / 698 | 1709 / 936 | 1692 / 917 | 1702 / 929 | — |
| fastapi.tiangolo.com/reference/responses | 5508 / 0 | 7509 / 1886 | 7507 / 1884 | 6601 / 1077 | 6945 / 1327 | 6934 / 1310 | 6940 / 1322 | — |
| fastapi.tiangolo.com/reference/security | 8809 / 0 | 10907 / 1922 | 10905 / 1920 | 9911 / 1086 | 10205 / 1322 | 10232 / 1305 | 10200 / 1317 | — |
| fastapi.tiangolo.com/reference/staticfiles | 987 / 0 | 2367 / 1334 | 2365 / 1332 | 1715 / 712 | 2056 / 952 | 2041 / 935 | 2051 / 947 | — |
| fastapi.tiangolo.com/reference/status | 996 / 0 | 2770 / 1732 | 2768 / 1730 | 1986 / 974 | 2327 / 1218 | 2306 / 1193 | 2314 / 1205 | — |
| fastapi.tiangolo.com/reference/templating | 623 / 0 | 1976 / 1278 | 1974 / 1276 | 1314 / 675 | 1655 / 913 | 1640 / 896 | 1650 / 908 | — |
| fastapi.tiangolo.com/reference/testclient | 2168 / 0 | 3662 / 1448 | 3660 / 1446 | 2972 / 788 | 3312 / 1028 | 3297 / 1011 | 3307 / 1023 | — |
| fastapi.tiangolo.com/reference/uploadfile | 713 / 0 | 2072 / 1314 | 2070 / 1312 | 1427 / 698 | 1763 / 934 | 1750 / 917 | 1758 / 929 | — |
| fastapi.tiangolo.com/reference/websockets | 1267 / 0 | 2828 / 1468 | 2826 / 1466 | 2086 / 803 | 2419 / 1039 | 2404 / 1020 | 2412 / 1032 | — |
| fastapi.tiangolo.com/release-notes | 52941 / 0 | 59610 / 8426 | 59793 / 8424 | 57519 / 4562 | 56028 / 4798 | 57836 / 4781 | 56208 / 4793 | 56325 / 13 |
| fastapi.tiangolo.com/resources | 14 / 0 | 1304 / 1243 | 1302 / 1241 | 676 / 646 | 1012 / 880 | 997 / 863 | 1007 / 875 | — |
| fastapi.tiangolo.com/ru | — | — | — | — | — | — | — | 2235 / 238 |
| fastapi.tiangolo.com/tr | — | — | — | — | — | — | — | 2143 / 238 |
| fastapi.tiangolo.com/translation-banner | — | — | — | — | — | — | — | 52 / 52 |
| fastapi.tiangolo.com/translation-banner/?q= | — | — | — | — | — | — | — | 52 / 52 |
| fastapi.tiangolo.com/translation-banner/ENGLISH_VERSION | — | — | — | — | — | — | — | 8 / 8 |
| fastapi.tiangolo.com/tutorial | 574 / 0 | 1824 / 1270 | 1717 / 1268 | 1255 / 665 | 1421 / 905 | 1579 / 888 | 1521 / 900 | — |
| fastapi.tiangolo.com/tutorial/application-configuration | — | — | — | — | — | — | — | 8 / 8 |
| fastapi.tiangolo.com/tutorial/background-tasks | 974 / 0 | 2336 / 1327 | 2334 / 1325 | 1695 / 705 | 2019 / 941 | 2018 / 924 | 2014 / 936 | — |
| fastapi.tiangolo.com/tutorial/bigger-applications | 3327 / 0 | 4914 / 1567 | 4912 / 1565 | 4229 / 886 | 4532 / 1128 | 4557 / 1111 | 4527 / 1123 | — |
| fastapi.tiangolo.com/tutorial/body | 1231 / 0 | 2652 / 1381 | 2650 / 1379 | 1994 / 747 | 2314 / 985 | 2317 / 966 | 2307 / 978 | — |
| fastapi.tiangolo.com/tutorial/body-fields | 652 / 0 | 1987 / 1295 | 1987 / 1295 | 1354 / 686 | 1687 / 924 | 1680 / 907 | 1682 / 919 | — |
| fastapi.tiangolo.com/tutorial/body-multiple-params | 1405 / 0 | 2779 / 1339 | 2779 / 1339 | 2142 / 721 | 2471 / 961 | 2468 / 944 | 2466 / 956 | — |
| fastapi.tiangolo.com/tutorial/body-nested-models | 1463 / 0 | 2929 / 1443 | 2927 / 1441 | 2270 / 791 | 2584 / 1031 | 2597 / 1014 | 2579 / 1026 | — |
| fastapi.tiangolo.com/tutorial/body-updates | 1011 / 0 | 2379 / 1335 | 2377 / 1333 | 1743 / 716 | 2068 / 954 | 2065 / 937 | 2063 / 949 | — |
| fastapi.tiangolo.com/tutorial/cookie-param-models | 588 / 0 | 1930 / 1301 | 1930 / 1301 | 1296 / 692 | 1626 / 930 | 1619 / 913 | 1621 / 925 | — |
| fastapi.tiangolo.com/tutorial/cookie-params | 365 / 0 | 1686 / 1281 | 1686 / 1281 | 1058 / 677 | 1388 / 913 | 1379 / 896 | 1383 / 908 | — |
| fastapi.tiangolo.com/tutorial/cors | 752 / 0 | 2107 / 1321 | 2107 / 1321 | 1467 / 699 | 1794 / 941 | 1791 / 922 | 1787 / 934 | — |
| fastapi.tiangolo.com/tutorial/debugging | 380 / 0 | 1733 / 1301 | 1733 / 1301 | 1090 / 694 | 1420 / 928 | 1408 / 911 | 1418 / 923 | — |
| fastapi.tiangolo.com/tutorial/dependencies | 1793 / 0 | 3111 / 1336 | 3111 / 1336 | 2521 / 712 | 2786 / 948 | 2841 / 929 | 2825 / 941 | — |
| fastapi.tiangolo.com/tutorial/dependencies/classes-as-d | 1943 / 0 | 3312 / 1333 | 3312 / 1333 | 2673 / 714 | 2996 / 952 | 2993 / 935 | 2991 / 947 | — |
| fastapi.tiangolo.com/tutorial/dependencies/dependencies | 900 / 0 | 2288 / 1359 | 2286 / 1357 | 1648 / 732 | 1974 / 974 | 1973 / 957 | 1969 / 969 | — |
| fastapi.tiangolo.com/tutorial/dependencies/dependencies | 2580 / 0 | 3817 / 1465 | 3819 / 1467 | 3414 / 818 | 3479 / 1058 | 3735 / 1039 | 3719 / 1051 | — |
| fastapi.tiangolo.com/tutorial/dependencies/global-depen | 282 / 0 | 1601 / 1273 | 1601 / 1273 | 973 / 675 | 1312 / 913 | 1297 / 894 | 1305 / 906 | — |
| fastapi.tiangolo.com/tutorial/dependencies/sub-dependen | 864 / 0 | 2211 / 1319 | 2211 / 1319 | 1586 / 706 | 1903 / 942 | 1908 / 923 | 1908 / 935 | — |
| fastapi.tiangolo.com/tutorial/encoder | 281 / 0 | 1590 / 1265 | 1590 / 1265 | 965 / 668 | 1302 / 906 | 1289 / 889 | 1297 / 901 | — |
| fastapi.tiangolo.com/tutorial/extra-data-types | 713 / 0 | 2030 / 1275 | 2028 / 1273 | 1401 / 672 | 1736 / 910 | 1725 / 893 | 1731 / 905 | — |
| fastapi.tiangolo.com/tutorial/extra-models | 1219 / 0 | 2647 / 1403 | 2647 / 1403 | 1998 / 763 | 2313 / 999 | 2322 / 982 | 2308 / 994 | — |
| fastapi.tiangolo.com/tutorial/first-steps | 1784 / 0 | 3329 / 1591 | 3327 / 1589 | 2693 / 893 | 2816 / 1129 | 3015 / 1112 | 2916 / 1124 | — |
| fastapi.tiangolo.com/tutorial/handling-errors | 1710 / 0 | 3161 / 1421 | 3159 / 1419 | 2503 / 777 | 2817 / 1013 | 2826 / 996 | 2812 / 1008 | — |
| fastapi.tiangolo.com/tutorial/header-param-models | 702 / 0 | 2059 / 1315 | 2059 / 1315 | 1420 / 702 | 1751 / 940 | 1746 / 923 | 1746 / 935 | — |
| fastapi.tiangolo.com/tutorial/header-params | 697 / 0 | 2033 / 1301 | 2033 / 1301 | 1402 / 689 | 1728 / 925 | 1723 / 908 | 1723 / 920 | — |
| fastapi.tiangolo.com/tutorial/metadata | 1172 / 0 | 2563 / 1361 | 2561 / 1359 | 1917 / 729 | 2240 / 971 | 2241 / 952 | 2233 / 964 | — |
| fastapi.tiangolo.com/tutorial/middleware | 598 / 0 | 1953 / 1303 | 1951 / 1301 | 1308 / 694 | 1644 / 930 | 1635 / 911 | 1637 / 923 | — |
| fastapi.tiangolo.com/tutorial/path-operation-configurat | 900 / 0 | 2280 / 1343 | 2278 / 1341 | 1632 / 716 | 1954 / 954 | 1955 / 937 | 1949 / 949 | — |
| fastapi.tiangolo.com/tutorial/path-params | 1543 / 0 | 3031 / 1471 | 3029 / 1469 | 2360 / 801 | 2657 / 1037 | 2680 / 1020 | 2657 / 1037 | — |
| fastapi.tiangolo.com/tutorial/path-params-numeric-valid | 1734 / 0 | 3181 / 1401 | 3179 / 1399 | 2518 / 768 | 2845 / 1010 | 2848 / 993 | 2840 / 1005 | — |
| fastapi.tiangolo.com/tutorial/query-param-models | 538 / 0 | 1889 / 1307 | 1887 / 1305 | 1250 / 696 | 1584 / 934 | 1577 / 917 | 1579 / 929 | — |
| fastapi.tiangolo.com/tutorial/query-params | 863 / 0 | 2208 / 1311 | 2208 / 1311 | 1578 / 699 | 1903 / 935 | 1898 / 918 | 1898 / 930 | — |
| fastapi.tiangolo.com/tutorial/query-params-str-validati | 4071 / 0 | 5682 / 1591 | 5682 / 1591 | 4987 / 900 | 5283 / 1142 | 5316 / 1125 | 5278 / 1137 | — |
| fastapi.tiangolo.com/tutorial/request-files | 1791 / 0 | 3199 / 1373 | 3199 / 1373 | 2548 / 741 | 2865 / 977 | 2870 / 960 | 2860 / 972 | — |
| fastapi.tiangolo.com/tutorial/request-form-models | 445 / 0 | 1784 / 1301 | 1782 / 1299 | 1152 / 691 | 1481 / 929 | 1472 / 910 | 1474 / 922 | — |
| fastapi.tiangolo.com/tutorial/request-forms | 488 / 0 | 1826 / 1295 | 1824 / 1293 | 1189 / 685 | 1517 / 921 | 1510 / 904 | 1512 / 916 | — |
| fastapi.tiangolo.com/tutorial/request-forms-and-files | 388 / 0 | 1721 / 1293 | 1721 / 1293 | 1091 / 687 | 1424 / 927 | 1415 / 910 | 1419 / 922 | — |
| fastapi.tiangolo.com/tutorial/response-model | 3150 / 0 | 4716 / 1553 | 4716 / 1553 | 4040 / 874 | 4346 / 1122 | 4367 / 1099 | 4335 / 1111 | — |
| fastapi.tiangolo.com/tutorial/response-status-code | 626 / 0 | 1964 / 1295 | 1964 / 1295 | 1332 / 690 | 1663 / 928 | 1654 / 911 | 1658 / 923 | — |
| fastapi.tiangolo.com/tutorial/schema-extra-example | 2006 / 0 | 3483 / 1453 | 3481 / 1451 | 2823 / 801 | 3137 / 1041 | 3150 / 1024 | 3132 / 1036 | — |
| fastapi.tiangolo.com/tutorial/security | 687 / 0 | 2012 / 1290 | 2010 / 1288 | 1381 / 678 | 1703 / 912 | 1702 / 895 | 1698 / 907 | — |
| fastapi.tiangolo.com/tutorial/security/first-steps | 1526 / 0 | 2917 / 1357 | 2915 / 1355 | 2263 / 721 | 2586 / 961 | 2587 / 944 | 2581 / 956 | — |
| fastapi.tiangolo.com/tutorial/security/get-current-user | 1537 / 0 | 2915 / 1341 | 2913 / 1339 | 2269 / 716 | 2598 / 954 | 2597 / 937 | 2593 / 949 | — |
| fastapi.tiangolo.com/tutorial/security/oauth2-jwt | 4418 / 0 | 5895 / 1433 | 5893 / 1431 | 5212 / 778 | 5550 / 1028 | 5549 / 1011 | 5545 / 1023 | — |
| fastapi.tiangolo.com/tutorial/security/simple-oauth2 | 3596 / 0 | 5078 / 1455 | 5078 / 1455 | 4405 / 793 | 4724 / 1037 | 4741 / 1020 | 4719 / 1032 | — |
| fastapi.tiangolo.com/tutorial/server-sent-events | 1449 / 0 | 2839 / 1361 | 2837 / 1359 | 2195 / 730 | 2517 / 970 | 2518 / 951 | 2510 / 963 | — |
| fastapi.tiangolo.com/tutorial/sql-databases | 10591 / 0 | 12264 / 1637 | 12262 / 1635 | 11545 / 938 | 11842 / 1176 | 11872 / 1159 | 11837 / 1171 | — |
| fastapi.tiangolo.com/tutorial/static-files | 245 / 0 | 1575 / 1293 | 1573 / 1291 | 944 / 683 | 1274 / 921 | 1265 / 902 | 1267 / 914 | — |
| fastapi.tiangolo.com/tutorial/stream-json-lines | 1214 / 0 | 2544 / 1343 | 2544 / 1343 | 1950 / 720 | 2226 / 960 | 2276 / 941 | 2272 / 953 | — |
| fastapi.tiangolo.com/tutorial/testing | 1485 / 0 | 2853 / 1341 | 2851 / 1339 | 2217 / 716 | 2533 / 952 | 2534 / 933 | 2526 / 945 | — |
| fastapi.tiangolo.com/uk | — | — | — | — | — | — | — | 2274 / 233 |
| fastapi.tiangolo.com/virtual-environments | 3009 / 0 | 4558 / 1524 | 4528 / 1524 | 3869 / 844 | 4142 / 1082 | 4191 / 1063 | 4264 / 1075 | 2934 / 988 |
| fastapi.tiangolo.com/zh | — | — | — | — | — | — | — | 1318 / 93 |
| fastapi.tiangolo.com/zh-hant | 1126 / 0 | 2714 / 1341 | 2714 / 1341 | 1786 / 637 | 2068 / 869 | 2098 / 852 | 2051 / 852 | 1285 / 90 |
| fastapi.tiangolo.com/zh-hant/about | 21 / 0 | 1157 / 1092 | 1155 / 1090 | 527 / 490 | 860 / 724 | 845 / 707 | 855 / 719 | — |
| fastapi.tiangolo.com/zh-hant/advanced | 43 / 0 | 1186 / 1104 | 1184 / 1102 | 558 / 499 | 885 / 733 | 874 / 716 | 880 / 728 | — |
| fastapi.tiangolo.com/zh-hant/advanced/additional-respon | 739 / 0 | 1921 / 1147 | 1919 / 1145 | 1283 / 528 | 1607 / 764 | 1602 / 747 | 1602 / 759 | — |
| fastapi.tiangolo.com/zh-hant/advanced/additional-status | 255 / 0 | 1413 / 1119 | 1411 / 1117 | 784 / 513 | 1112 / 747 | 1101 / 730 | 1107 / 742 | — |
| fastapi.tiangolo.com/zh-hant/advanced/advanced-dependen | 1169 / 0 | 2408 / 1217 | 2406 / 1215 | 1760 / 575 | 2071 / 809 | 2078 / 792 | 2066 / 804 | — |
| fastapi.tiangolo.com/zh-hant/advanced/advanced-python-t | 134 / 0 | 1293 / 1115 | 1291 / 1113 | 661 / 511 | 998 / 749 | 985 / 732 | 993 / 744 | — |
| fastapi.tiangolo.com/zh-hant/advanced/async-tests | 305 / 0 | 1481 / 1145 | 1479 / 1143 | 844 / 523 | 1164 / 757 | 1160 / 740 | 1159 / 752 | — |
| fastapi.tiangolo.com/zh-hant/advanced/behind-a-proxy | 955 / 0 | 2179 / 1253 | 2181 / 1255 | 1564 / 593 | 1820 / 827 | 1882 / 810 | 1885 / 822 | — |
| fastapi.tiangolo.com/zh-hant/advanced/custom-response | 993 / 0 | 2263 / 1257 | 2263 / 1257 | 1598 / 589 | 1895 / 823 | 1916 / 806 | 1890 / 818 | — |
| fastapi.tiangolo.com/zh-hant/advanced/dataclasses | 456 / 0 | 1630 / 1137 | 1630 / 1137 | 996 / 524 | 1322 / 760 | 1315 / 743 | 1317 / 755 | — |
| fastapi.tiangolo.com/zh-hant/advanced/events | 588 / 0 | 1828 / 1191 | 1828 / 1191 | 1159 / 555 | 1471 / 789 | 1476 / 772 | 1466 / 784 | — |
| fastapi.tiangolo.com/zh-hant/advanced/generate-clients | 712 / 0 | 2068 / 1279 | 2068 / 1279 | 1350 / 622 | 1657 / 858 | 1672 / 841 | 1652 / 853 | — |
| fastapi.tiangolo.com/zh-hant/advanced/json-base64-bytes | 547 / 0 | 1731 / 1145 | 1731 / 1145 | 1093 / 530 | 1426 / 770 | 1419 / 753 | 1421 / 765 | — |
| fastapi.tiangolo.com/zh-hant/advanced/middleware | 277 / 0 | 1464 / 1147 | 1464 / 1147 | 820 / 527 | 1142 / 761 | 1139 / 744 | 1137 / 756 | — |
| fastapi.tiangolo.com/zh-hant/advanced/openapi-callbacks | 958 / 0 | 2161 / 1177 | 2161 / 1177 | 1518 / 544 | 1834 / 780 | 1837 / 763 | 1829 / 775 | — |
| fastapi.tiangolo.com/zh-hant/advanced/openapi-webhooks | 197 / 0 | 1380 / 1145 | 1380 / 1145 | 745 / 532 | 1073 / 768 | 1066 / 751 | 1068 / 763 | — |
| fastapi.tiangolo.com/zh-hant/advanced/path-operation-ad | 742 / 0 | 1994 / 1195 | 1994 / 1195 | 1321 / 563 | 1634 / 797 | 1637 / 780 | 1629 / 792 | — |
| fastapi.tiangolo.com/zh-hant/advanced/response-change-s | 114 / 0 | 1275 / 1119 | 1275 / 1119 | 643 / 513 | 974 / 751 | 963 / 734 | 969 / 746 | — |
| fastapi.tiangolo.com/zh-hant/advanced/response-cookies | 173 / 0 | 1337 / 1127 | 1337 / 1127 | 707 / 518 | 1037 / 756 | 1026 / 737 | 1030 / 749 | — |
| fastapi.tiangolo.com/zh-hant/advanced/response-directly | 320 / 0 | 1499 / 1147 | 1499 / 1147 | 866 / 530 | 1189 / 766 | 1184 / 749 | 1184 / 761 | — |
| fastapi.tiangolo.com/zh-hant/advanced/response-headers | 158 / 0 | 1325 / 1125 | 1325 / 1125 | 691 / 517 | 1019 / 751 | 1010 / 734 | 1014 / 746 | — |
| fastapi.tiangolo.com/zh-hant/advanced/security | 36 / 0 | 1182 / 1106 | 1182 / 1106 | 553 / 501 | 881 / 735 | 870 / 718 | 876 / 730 | — |
| fastapi.tiangolo.com/zh-hant/advanced/security/http-bas | 676 / 0 | 1874 / 1165 | 1874 / 1165 | 1230 / 538 | 1551 / 774 | 1550 / 757 | 1546 / 769 | — |
| fastapi.tiangolo.com/zh-hant/advanced/security/oauth2-s | 7671 / 0 | 8941 / 1253 | 8941 / 1253 | 8285 / 598 | 8591 / 834 | 8604 / 817 | 8586 / 829 | — |
| fastapi.tiangolo.com/zh-hant/advanced/settings | 1198 / 0 | 2347 / 1259 | 2349 / 1261 | 1809 / 595 | 1989 / 831 | 2126 / 812 | 2113 / 824 | — |
| fastapi.tiangolo.com/zh-hant/advanced/stream-data | 2120 / 0 | 3329 / 1185 | 3327 / 1183 | 2687 / 551 | 3000 / 785 | 3003 / 768 | 2995 / 780 | — |
| fastapi.tiangolo.com/zh-hant/advanced/strict-content-ty | 172 / 0 | 1347 / 1137 | 1347 / 1137 | 711 / 523 | 1042 / 761 | 1035 / 744 | 1037 / 756 | — |
| fastapi.tiangolo.com/zh-hant/advanced/sub-applications | 223 / 0 | 1422 / 1155 | 1422 / 1155 | 772 / 533 | 1097 / 771 | 1092 / 754 | 1092 / 766 | — |
| fastapi.tiangolo.com/zh-hant/advanced/templates | 308 / 0 | 1503 / 1161 | 1502 / 1161 | 861 / 537 | 1177 / 771 | 1177 / 754 | 1176 / 766 | — |
| fastapi.tiangolo.com/zh-hant/advanced/testing-dependenc | 402 / 0 | 1569 / 1123 | 1569 / 1123 | 933 / 515 | 1262 / 749 | 1253 / 732 | 1257 / 744 | — |
| fastapi.tiangolo.com/zh-hant/advanced/testing-events | 238 / 0 | 1379 / 1098 | 1379 / 1098 | 746 / 492 | 1086 / 734 | 1071 / 717 | 1081 / 729 | — |
| fastapi.tiangolo.com/zh-hant/advanced/testing-websocket | 109 / 0 | 1250 / 1095 | 1250 / 1095 | 617 / 492 | 954 / 728 | 939 / 711 | 949 / 723 | — |
| fastapi.tiangolo.com/zh-hant/advanced/using-request-dir | 143 / 0 | 1312 / 1131 | 1312 / 1131 | 681 / 522 | 1010 / 758 | 1001 / 741 | 1005 / 753 | — |
| fastapi.tiangolo.com/zh-hant/advanced/vibe | 425 / 0 | 1600 / 1127 | 1600 / 1127 | 959 / 518 | 1289 / 754 | 1280 / 737 | 1284 / 749 | — |
| fastapi.tiangolo.com/zh-hant/advanced/websockets | 1230 / 0 | 2450 / 1187 | 2449 / 1187 | 1797 / 551 | 2111 / 785 | 2113 / 768 | 2110 / 780 | — |
| fastapi.tiangolo.com/zh-hant/advanced/wsgi | 152 / 0 | 1309 / 1117 | 1309 / 1117 | 679 / 511 | 1012 / 749 | 1001 / 732 | 1007 / 744 | — |
| fastapi.tiangolo.com/zh-hant/alternatives | 908 / 0 | 2205 / 1293 | 2205 / 1293 | 1535 / 611 | 1822 / 847 | 1851 / 828 | 1815 / 840 | — |
| fastapi.tiangolo.com/zh-hant/async | 753 / 0 | 2113 / 1271 | 2113 / 1271 | 1363 / 594 | 1661 / 834 | 1686 / 817 | 1656 / 829 | — |
| fastapi.tiangolo.com/zh-hant/benchmarks | 133 / 0 | 1280 / 1099 | 1280 / 1099 | 650 / 501 | 980 / 735 | 967 / 718 | 975 / 730 | — |
| fastapi.tiangolo.com/zh-hant/contributing | 1635 / 0 | 3004 / 1343 | 3004 / 1343 | 2318 / 667 | 2636 / 905 | 2643 / 888 | 2631 / 900 | — |
| fastapi.tiangolo.com/zh-hant/deployment | 51 / 0 | 1202 / 1102 | 1202 / 1102 | 566 / 499 | 895 / 733 | 884 / 716 | 890 / 728 | — |
| fastapi.tiangolo.com/zh-hant/deployment/cloud | 67 / 0 | 1232 / 1119 | 1232 / 1119 | 597 / 514 | 930 / 750 | 919 / 733 | 925 / 745 | — |
| fastapi.tiangolo.com/zh-hant/deployment/concepts | 558 / 0 | 1882 / 1329 | 1882 / 1329 | 1199 / 625 | 1477 / 859 | 1516 / 842 | 1472 / 854 | — |
| fastapi.tiangolo.com/zh-hant/deployment/docker | 1075 / 0 | 2436 / 1461 | 2436 / 1461 | 1809 / 718 | 1990 / 958 | 2137 / 941 | 2066 / 953 | — |
| fastapi.tiangolo.com/zh-hant/deployment/fastapicloud | 126 / 0 | 1299 / 1141 | 1299 / 1141 | 666 / 524 | 989 / 760 | 987 / 743 | 995 / 755 | — |
| fastapi.tiangolo.com/zh-hant/deployment/https | 502 / 0 | 1865 / 1227 | 1865 / 1227 | 1092 / 574 | 1398 / 810 | 1411 / 793 | 1393 / 805 | — |
| fastapi.tiangolo.com/zh-hant/deployment/manually | 377 / 0 | 1447 / 1151 | 1445 / 1151 | 924 / 531 | 1125 / 767 | 1241 / 748 | 1198 / 760 | — |
| fastapi.tiangolo.com/zh-hant/deployment/server-workers | 486 / 0 | 1496 / 1137 | 1496 / 1137 | 1023 / 521 | 1178 / 763 | 1351 / 746 | 1251 / 758 | — |
| fastapi.tiangolo.com/zh-hant/deployment/versions | 156 / 0 | 1346 / 1159 | 1346 / 1159 | 709 / 537 | 1033 / 775 | 1030 / 758 | 1028 / 770 | — |
| fastapi.tiangolo.com/zh-hant/editor-support | 140 / 0 | 1292 / 1115 | 1292 / 1115 | 665 / 509 | 991 / 743 | 982 / 726 | 986 / 738 | — |
| fastapi.tiangolo.com/zh-hant/environment-variables | 397 / 0 | 1600 / 1151 | 1599 / 1151 | 946 / 533 | 1255 / 769 | 1265 / 750 | 1297 / 762 | — |
| fastapi.tiangolo.com/zh-hant/fastapi-cli | 366 / 0 | 1378 / 1139 | 1377 / 1139 | 910 / 528 | 1066 / 764 | 1229 / 747 | 1166 / 759 | — |
| fastapi.tiangolo.com/zh-hant/features | 441 / 0 | 1703 / 1197 | 1703 / 1197 | 1012 / 555 | 1317 / 789 | 1328 / 772 | 1312 / 784 | — |
| fastapi.tiangolo.com/zh-hant/help-fastapi | 480 / 0 | 1843 / 1331 | 1843 / 1331 | 1130 / 638 | 1425 / 878 | 1458 / 861 | 1420 / 873 | — |
| fastapi.tiangolo.com/zh-hant/history-design-future | 125 / 0 | 1293 / 1139 | 1293 / 1139 | 662 / 521 | 981 / 755 | 978 / 738 | 976 / 750 | — |
| fastapi.tiangolo.com/zh-hant/how-to | 28 / 0 | 1179 / 1098 | 1179 / 1098 | 538 / 494 | 880 / 732 | 865 / 715 | 875 / 727 | — |
| fastapi.tiangolo.com/zh-hant/how-to/authentication-erro | 111 / 0 | 1251 / 1098 | 1251 / 1098 | 621 / 494 | 958 / 734 | 941 / 715 | 956 / 732 | — |
| fastapi.tiangolo.com/zh-hant/how-to/conditional-openapi | 154 / 0 | 1320 / 1119 | 1320 / 1119 | 684 / 514 | 1021 / 750 | 1007 / 733 | 1016 / 745 | — |
| fastapi.tiangolo.com/zh-hant/how-to/configure-swagger-u | 1396 / 0 | 2591 / 1157 | 2591 / 1157 | 1951 / 539 | 2278 / 777 | 2273 / 760 | 2273 / 772 | — |
| fastapi.tiangolo.com/zh-hant/how-to/custom-docs-ui-asse | 867 / 0 | 2122 / 1231 | 2122 / 1231 | 1460 / 577 | 1771 / 815 | 1784 / 798 | 1766 / 810 | — |
| fastapi.tiangolo.com/zh-hant/how-to/custom-request-and- | 1103 / 0 | 2300 / 1165 | 2300 / 1165 | 1660 / 541 | 1988 / 783 | 1985 / 766 | 1983 / 778 | — |
| fastapi.tiangolo.com/zh-hant/how-to/extending-openapi | 490 / 0 | 1697 / 1177 | 1697 / 1177 | 1054 / 548 | 1374 / 784 | 1375 / 767 | 1369 / 779 | — |
| fastapi.tiangolo.com/zh-hant/how-to/general | 156 / 0 | 1428 / 1235 | 1428 / 1235 | 763 / 591 | 1089 / 833 | 1094 / 816 | 1084 / 828 | — |
| fastapi.tiangolo.com/zh-hant/how-to/graphql | 188 / 0 | 1374 / 1143 | 1374 / 1143 | 735 / 531 | 1067 / 765 | 1060 / 748 | 1062 / 760 | — |
| fastapi.tiangolo.com/zh-hant/how-to/migrate-from-pydant | 494 / 0 | 1648 / 1201 | 1648 / 1201 | 1078 / 568 | 1330 / 812 | 1408 / 795 | 1402 / 807 | — |
| fastapi.tiangolo.com/zh-hant/how-to/separate-openapi-sc | 428 / 0 | 1637 / 1177 | 1637 / 1177 | 987 / 543 | 1307 / 781 | 1310 / 764 | 1302 / 776 | — |
| fastapi.tiangolo.com/zh-hant/how-to/testing-database | 37 / 0 | 1179 / 1096 | 1179 / 1096 | 547 / 494 | 882 / 728 | 867 / 711 | 877 / 723 | — |
| fastapi.tiangolo.com/zh-hant/learn | 25 / 0 | 1161 / 1090 | 1161 / 1090 | 531 / 490 | 863 / 724 | 848 / 707 | 858 / 719 | — |
| fastapi.tiangolo.com/zh-hant/project-generation | 132 / 0 | 1288 / 1113 | 1286 / 1111 | 659 / 511 | 995 / 749 | 982 / 732 | 990 / 744 | — |
| fastapi.tiangolo.com/zh-hant/python-types | 751 / 0 | 2014 / 1245 | 2014 / 1245 | 1349 / 582 | 1651 / 818 | 1670 / 801 | 1646 / 813 | — |
| fastapi.tiangolo.com/zh-hant/resources | 20 / 0 | 1156 / 1090 | 1156 / 1090 | 526 / 490 | 863 / 726 | 846 / 707 | 856 / 719 | — |
| fastapi.tiangolo.com/zh-hant/tutorial | 283 / 0 | 1377 / 1111 | 1377 / 1111 | 803 / 504 | 1070 / 742 | 1123 / 725 | 1065 / 737 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/background-tasks | 441 / 0 | 1626 / 1155 | 1626 / 1155 | 988 / 531 | 1307 / 765 | 1306 / 748 | 1302 / 760 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/bigger-applicatio | 1649 / 0 | 2997 / 1335 | 2997 / 1335 | 2318 / 653 | 2615 / 891 | 2640 / 874 | 2610 / 886 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/body | 554 / 0 | 1802 / 1197 | 1802 / 1197 | 1131 / 561 | 1442 / 795 | 1447 / 778 | 1437 / 790 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/body-fields | 449 / 0 | 1622 / 1135 | 1622 / 1135 | 986 / 521 | 1317 / 759 | 1310 / 742 | 1312 / 754 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/body-multiple-par | 995 / 0 | 2200 / 1173 | 2200 / 1173 | 1562 / 551 | 1887 / 789 | 1884 / 772 | 1882 / 784 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/body-nested-model | 871 / 0 | 2111 / 1219 | 2111 / 1219 | 1452 / 565 | 1761 / 803 | 1774 / 786 | 1756 / 798 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/body-updates | 622 / 0 | 1828 / 1173 | 1828 / 1173 | 1189 / 551 | 1515 / 791 | 1510 / 772 | 1508 / 784 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/cookie-param-mode | 355 / 0 | 1547 / 1139 | 1547 / 1139 | 897 / 526 | 1223 / 762 | 1216 / 745 | 1218 / 757 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/cookie-params | 229 / 0 | 1395 / 1129 | 1395 / 1129 | 765 / 520 | 1093 / 756 | 1084 / 739 | 1088 / 751 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/cors | 272 / 0 | 1463 / 1157 | 1463 / 1157 | 821 / 533 | 1138 / 767 | 1137 / 750 | 1133 / 762 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/debugging | 202 / 0 | 1389 / 1137 | 1389 / 1137 | 743 / 525 | 1074 / 759 | 1059 / 742 | 1069 / 754 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies | 804 / 0 | 1942 / 1162 | 1942 / 1162 | 1355 / 535 | 1618 / 771 | 1673 / 752 | 1657 / 764 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies/clas | 1384 / 0 | 2574 / 1153 | 2574 / 1153 | 1931 / 531 | 2250 / 765 | 2247 / 748 | 2245 / 760 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies/depe | 616 / 0 | 1803 / 1159 | 1803 / 1159 | 1165 / 533 | 1482 / 767 | 1481 / 750 | 1482 / 767 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies/depe | 1529 / 0 | 2571 / 1269 | 2571 / 1269 | 2160 / 615 | 2224 / 855 | 2480 / 836 | 2464 / 848 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies/glob | 189 / 0 | 1340 / 1109 | 1340 / 1109 | 712 / 507 | 1043 / 741 | 1030 / 724 | 1038 / 736 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/dependencies/sub- | 517 / 0 | 1686 / 1149 | 1686 / 1149 | 1064 / 531 | 1373 / 765 | 1380 / 748 | 1380 / 760 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/encoder | 140 / 0 | 1291 / 1109 | 1291 / 1109 | 664 / 508 | 997 / 744 | 984 / 727 | 992 / 739 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/extra-data-types | 511 / 0 | 1663 / 1113 | 1663 / 1113 | 1036 / 509 | 1364 / 743 | 1353 / 726 | 1359 / 738 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/extra-models | 639 / 0 | 1882 / 1223 | 1882 / 1223 | 1234 / 579 | 1543 / 813 | 1552 / 796 | 1538 / 808 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/first-steps | 952 / 0 | 2250 / 1343 | 2250 / 1343 | 1611 / 643 | 1730 / 877 | 1929 / 860 | 1830 / 872 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/handling-errors | 923 / 0 | 2170 / 1229 | 2170 / 1229 | 1524 / 585 | 1831 / 819 | 1840 / 802 | 1826 / 814 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/header-param-mode | 468 / 0 | 1645 / 1141 | 1645 / 1141 | 1009 / 525 | 1333 / 759 | 1328 / 742 | 1328 / 754 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/header-params | 429 / 0 | 1609 / 1145 | 1609 / 1145 | 973 / 528 | 1298 / 764 | 1293 / 747 | 1293 / 759 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/metadata | 711 / 0 | 1920 / 1177 | 1920 / 1177 | 1271 / 544 | 1586 / 780 | 1589 / 763 | 1581 / 775 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/middleware | 216 / 0 | 1416 / 1133 | 1416 / 1133 | 753 / 521 | 1081 / 755 | 1074 / 738 | 1076 / 750 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/path-operation-co | 589 / 0 | 1790 / 1169 | 1790 / 1169 | 1146 / 541 | 1462 / 775 | 1463 / 758 | 1457 / 770 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/path-params | 775 / 0 | 2046 / 1259 | 2046 / 1259 | 1378 / 587 | 1671 / 821 | 1694 / 804 | 1666 / 816 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/path-params-numer | 1133 / 0 | 2355 / 1175 | 2355 / 1175 | 1692 / 543 | 2005 / 777 | 2008 / 760 | 2000 / 772 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/query-param-model | 359 / 0 | 1545 / 1133 | 1545 / 1133 | 896 / 521 | 1221 / 755 | 1214 / 738 | 1216 / 750 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/query-params | 467 / 0 | 1636 / 1137 | 1636 / 1137 | 1004 / 521 | 1325 / 755 | 1320 / 738 | 1320 / 750 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/query-params-str- | 2572 / 0 | 3921 / 1337 | 3921 / 1337 | 3233 / 645 | 3518 / 881 | 3549 / 862 | 3511 / 874 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/request-files | 1168 / 0 | 2386 / 1189 | 2386 / 1189 | 1737 / 553 | 2048 / 787 | 2053 / 770 | 2043 / 782 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/request-form-mode | 308 / 0 | 1478 / 1133 | 1478 / 1133 | 845 / 521 | 1170 / 757 | 1161 / 738 | 1163 / 750 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/request-forms | 270 / 0 | 1448 / 1137 | 1446 / 1135 | 809 / 523 | 1132 / 757 | 1125 / 740 | 1127 / 752 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/request-forms-and | 282 / 0 | 1453 / 1135 | 1453 / 1135 | 825 / 527 | 1150 / 761 | 1141 / 744 | 1145 / 756 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/response-model | 1435 / 0 | 2736 / 1297 | 2736 / 1297 | 2066 / 615 | 2362 / 856 | 2386 / 836 | 2354 / 848 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/response-status-c | 222 / 0 | 1389 / 1125 | 1389 / 1125 | 755 / 517 | 1080 / 751 | 1071 / 734 | 1075 / 746 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/schema-extra-exam | 1292 / 0 | 2597 / 1283 | 2597 / 1283 | 1939 / 631 | 2244 / 865 | 2257 / 848 | 2239 / 860 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/security | 208 / 0 | 1372 / 1132 | 1372 / 1132 | 741 / 517 | 1062 / 751 | 1061 / 734 | 1057 / 746 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/security/first-st | 591 / 0 | 1805 / 1185 | 1805 / 1185 | 1156 / 549 | 1475 / 787 | 1476 / 770 | 1470 / 782 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/security/get-curr | 1070 / 0 | 2283 / 1161 | 2283 / 1161 | 1621 / 535 | 1943 / 769 | 1942 / 752 | 1938 / 764 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/security/oauth2-j | 3168 / 0 | 4447 / 1233 | 4447 / 1233 | 3762 / 578 | 4092 / 822 | 4091 / 805 | 4087 / 817 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/security/simple-o | 2619 / 0 | 3897 / 1253 | 3897 / 1253 | 3223 / 588 | 3533 / 828 | 3550 / 811 | 3528 / 823 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/server-sent-event | 1108 / 0 | 2337 / 1195 | 2337 / 1195 | 1686 / 562 | 2003 / 798 | 2006 / 781 | 1998 / 793 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/sql-databases | 9089 / 0 | 10471 / 1373 | 10471 / 1373 | 9778 / 673 | 10066 / 907 | 10096 / 890 | 10061 / 902 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/static-files | 98 / 0 | 1264 / 1131 | 1264 / 1131 | 633 / 519 | 957 / 753 | 950 / 736 | 952 / 748 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/stream-json-lines | 810 / 0 | 1975 / 1173 | 1975 / 1173 | 1371 / 545 | 1644 / 785 | 1694 / 766 | 1690 / 778 | — |
| fastapi.tiangolo.com/zh-hant/tutorial/testing | 1039 / 0 | 2233 / 1169 | 2233 / 1169 | 1596 / 541 | 1909 / 775 | 1912 / 758 | 1904 / 770 | — |
| fastapi.tiangolo.com/zh-hant/virtual-environments | 967 / 0 | 2284 / 1275 | 2286 / 1277 | 1576 / 593 | 1847 / 829 | 1894 / 810 | 1967 / 822 | — |
| fastapi.tiangolo.com/zh/contributing | — | — | — | — | — | — | — | 1610 / 84 |
| fastapi.tiangolo.com/zh/deployment | — | — | — | — | — | — | — | 46 / 46 |
| fastapi.tiangolo.com/zh/features | — | — | — | — | — | — | — | 410 / 21 |
| fastapi.tiangolo.com/zh/help-fastapi | — | — | — | — | — | — | — | 463 / 209 |
| fastapi.tiangolo.com/zh/python-types | — | — | — | — | — | — | — | 684 / 86 |
| fastapi.tiangolo.com/zh/tutorial | — | — | — | — | — | — | — | 278 / 278 |
| fastapi.tiangolo.com/zh/tutorial/body | — | — | — | — | — | — | — | 524 / 524 |
| fastapi.tiangolo.com/zh/tutorial/body-fields | — | — | — | — | — | — | — | 427 / 427 |
| fastapi.tiangolo.com/zh/tutorial/body-multiple-params | — | — | — | — | — | — | — | 909 / 909 |
| fastapi.tiangolo.com/zh/tutorial/first-steps | — | — | — | — | — | — | — | 820 / 162 |
| fastapi.tiangolo.com/zh/tutorial/path-params | — | — | — | — | — | — | — | 712 / 263 |
| fastapi.tiangolo.com/zh/tutorial/path-params-numeric-va | — | — | — | — | — | — | — | 1086 / 588 |
| fastapi.tiangolo.com/zh/tutorial/query-params | — | — | — | — | — | — | — | 420 / 420 |
| fastapi.tiangolo.com/zh/tutorial/query-params-str-valid | — | — | — | — | — | — | — | 2477 / 86 |

</details>

## python-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 3736 | 0 | 0% | 248 | 11.4 | 7.5 | 100% | 87% |
| crawl4ai | 4190 | 61 ⚠ | 0% | 3039 | 19.4 | 7.5 | 100% | 66% |
| crawl4ai-raw | 4190 | 61 ⚠ | 0% | 3039 | 19.4 | 7.5 | 100% | 66% |
| scrapy+md | 4262 | 4 | 0% | 2634 | 20.1 | 8.2 | 100% | 100% |
| crawlee | 4132 | 51 ⚠ | 0% | 3039 | 19.1 | 7.5 | 100% | 96% |
| colly+md | 4044 | 24 | 0% | 3039 | 19.1 | 7.5 | 100% | 96% |
| playwright | 4132 | 51 ⚠ | 0% | 3039 | 19.1 | 7.5 | 100% | 96% |
| firecrawl | 3077 | 0 | 0% | 1815 | 8.2 | 0.0 | 0% | 0% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

**Reading the numbers:**
**firecrawl** produces the cleanest output with 0 word of preamble per page, while **crawl4ai** injects 61 words of nav chrome before content begins. firecrawl's lower recall (0% vs 100%) reflects stricter content filtering — the "missed" sentences are predominantly navigation, sponsor links, and footer text that other tools include as content. For RAG, this is a net positive: fewer junk tokens per chunk means better embedding quality and retrieval precision.

<details>
<summary>Sample output — first 40 lines of <code>docs.python.org/3.10/genindex-Y.html</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# Index – Y

|  |  |
| --- | --- |
| * [ycor() (in module turtle)](library/turtle.html#turtle.ycor) * [year (datetime.date attribute)](library/datetime.html#datetime.date.year)   * [(datetime.datetime attribute)](library/datetime.html#datetime.datetime.year) * [Year 2038](library/time.html#index-2) * [yeardatescalendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardatescalendar) * [yeardays2calendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardays2calendar) * [yeardayscalendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardayscalendar) * [YESEXPR (in module locale)](library/locale.html#locale.YESEXPR) | * yield   * [examples](reference/expressions.html#index-34)   * [expression](reference/expressions.html#index-23)   * [keyword](reference/expressions.html#index-23)   * [statement](reference/simple_stmts.html#index-26)   * [yield from (in What's New)](whatsnew/3.3.html#index-11) * [Yield (class in ast)](library/ast.html#ast.Yield) * [YIELD_FROM (opcode)](library/dis.html#opcode-YIELD_FROM) * [YIELD_VALUE (opcode)](library/dis.html#opcode-YIELD_VALUE) * [YieldFrom (class in ast)](library/ast.html#ast.YieldFrom) * [yiq_to_rgb() (in module colorsys)](library/colorsys.html#colorsys.yiq_to_rgb) * [yview() (tkinter.ttk.Treeview method)](library/tkinter.ttk.html#tkinter.ttk.Treeview.yview) |
```

**crawl4ai**
```
[ ![Python logo](https://docs.python.org/3.10/_static/py.svg) ](https://www.python.org/) dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
### Navigation
  * [index](https://docs.python.org/3.10/genindex.html "General Index")
  * [modules](https://docs.python.org/3.10/py-modindex.html "Python Module Index") |
  * ![Python logo](https://docs.python.org/3.10/_static/py.svg)
  * [Python](https://www.python.org/) »
  * Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
  * [3.10.20 Documentation](https://docs.python.org/3.10/index.html) » 
  * [Index](https://docs.python.org/3.10/genindex-Y.html)
  * | 
  * Theme  Auto Light Dark |


# Index – Y  
| 
  * [ycor() (in module turtle)](https://docs.python.org/3.10/library/turtle.html#turtle.ycor)
  * [year (datetime.date attribute)](https://docs.python.org/3.10/library/datetime.html#datetime.date.year)
    * [(datetime.datetime attribute)](https://docs.python.org/3.10/library/datetime.html#datetime.datetime.year)
  * [Year 2038](https://docs.python.org/3.10/library/time.html#index-2)
  * [yeardatescalendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardatescalendar)
  * [yeardays2calendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardays2calendar)
  * [yeardayscalendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardayscalendar)
  * [YESEXPR (in module locale)](https://docs.python.org/3.10/library/locale.html#locale.YESEXPR)

 | 
  * yield 
    * [examples](https://docs.python.org/3.10/reference/expressions.html#index-34)
    * [expression](https://docs.python.org/3.10/reference/expressions.html#index-23)
    * [keyword](https://docs.python.org/3.10/reference/expressions.html#index-23)
    * [statement](https://docs.python.org/3.10/reference/simple_stmts.html#index-26)
    * [yield from (in What's New)](https://docs.python.org/3.10/whatsnew/3.3.html#index-11)
  * [Yield (class in ast)](https://docs.python.org/3.10/library/ast.html#ast.Yield)
  * [YIELD_FROM (opcode)](https://docs.python.org/3.10/library/dis.html#opcode-YIELD_FROM)
  * [YIELD_VALUE (opcode)](https://docs.python.org/3.10/library/dis.html#opcode-YIELD_VALUE)
  * [YieldFrom (class in ast)](https://docs.python.org/3.10/library/ast.html#ast.YieldFrom)
  * [yiq_to_rgb() (in module colorsys)](https://docs.python.org/3.10/library/colorsys.html#colorsys.yiq_to_rgb)
  * [yview() (tkinter.ttk.Treeview method)](https://docs.python.org/3.10/library/tkinter.ttk.html#tkinter.ttk.Treeview.yview)
```

**crawl4ai-raw**
```
[ ![Python logo](https://docs.python.org/3.10/_static/py.svg) ](https://www.python.org/) dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
### Navigation
  * [index](https://docs.python.org/3.10/genindex.html "General Index")
  * [modules](https://docs.python.org/3.10/py-modindex.html "Python Module Index") |
  * ![Python logo](https://docs.python.org/3.10/_static/py.svg)
  * [Python](https://www.python.org/) »
  * Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
dev (3.15) 3.14 3.13 3.12 3.11 3.10.20 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
  * [3.10.20 Documentation](https://docs.python.org/3.10/index.html) » 
  * [Index](https://docs.python.org/3.10/genindex-Y.html)
  * | 
  * Theme  Auto Light Dark |


# Index – Y  
| 
  * [ycor() (in module turtle)](https://docs.python.org/3.10/library/turtle.html#turtle.ycor)
  * [year (datetime.date attribute)](https://docs.python.org/3.10/library/datetime.html#datetime.date.year)
    * [(datetime.datetime attribute)](https://docs.python.org/3.10/library/datetime.html#datetime.datetime.year)
  * [Year 2038](https://docs.python.org/3.10/library/time.html#index-2)
  * [yeardatescalendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardatescalendar)
  * [yeardays2calendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardays2calendar)
  * [yeardayscalendar() (calendar.Calendar method)](https://docs.python.org/3.10/library/calendar.html#calendar.Calendar.yeardayscalendar)
  * [YESEXPR (in module locale)](https://docs.python.org/3.10/library/locale.html#locale.YESEXPR)

 | 
  * yield 
    * [examples](https://docs.python.org/3.10/reference/expressions.html#index-34)
    * [expression](https://docs.python.org/3.10/reference/expressions.html#index-23)
    * [keyword](https://docs.python.org/3.10/reference/expressions.html#index-23)
    * [statement](https://docs.python.org/3.10/reference/simple_stmts.html#index-26)
    * [yield from (in What's New)](https://docs.python.org/3.10/whatsnew/3.3.html#index-11)
  * [Yield (class in ast)](https://docs.python.org/3.10/library/ast.html#ast.Yield)
  * [YIELD_FROM (opcode)](https://docs.python.org/3.10/library/dis.html#opcode-YIELD_FROM)
  * [YIELD_VALUE (opcode)](https://docs.python.org/3.10/library/dis.html#opcode-YIELD_VALUE)
  * [YieldFrom (class in ast)](https://docs.python.org/3.10/library/ast.html#ast.YieldFrom)
  * [yiq_to_rgb() (in module colorsys)](https://docs.python.org/3.10/library/colorsys.html#colorsys.yiq_to_rgb)
  * [yview() (tkinter.ttk.Treeview method)](https://docs.python.org/3.10/library/tkinter.ttk.html#tkinter.ttk.Treeview.yview)
```

**scrapy+md**
```
Theme
Auto
Light
Dark

### Navigation

* [index](genindex.html "General Index")
* [modules](py-modindex.html "Python Module Index") |
* [Python](https://www.python.org/) »

* [3.10.20 Documentation](index.html) »
* Index
* |
* Theme
  Auto
  Light
  Dark
   |

# Index – Y

|  |  |
| --- | --- |
| * [ycor() (in module turtle)](library/turtle.html#turtle.ycor) * [year (datetime.date attribute)](library/datetime.html#datetime.date.year)   + [(datetime.datetime attribute)](library/datetime.html#datetime.datetime.year) * [Year 2038](library/time.html#index-2) * [yeardatescalendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardatescalendar) * [yeardays2calendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardays2calendar) * [yeardayscalendar() (calendar.Calendar method)](library/calendar.html#calendar.Calendar.yeardayscalendar) * [YESEXPR (in module locale)](library/locale.html#locale.YESEXPR) | * yield   + [examples](reference/expressions.html#index-34)   + [expression](reference/expressions.html#index-23)   + [keyword](reference/expressions.html#index-23)   + [statement](reference/simple_stmts.html#index-26)   + [yield from (in What's New)](whatsnew/3.3.html#index-11) * [Yield (class in ast)](library/ast.html#ast.Yield) * [YIELD\_FROM (opcode)](library/dis.html#opcode-YIELD_FROM) * [YIELD\_VALUE (opcode)](library/dis.html#opcode-YIELD_VALUE) * [YieldFrom (class in ast)](library/ast.html#ast.YieldFrom) * [yiq\_to\_rgb() (in module colorsys)](library/colorsys.html#colorsys.yiq_to_rgb) * [yview() (tkinter.ttk.Treeview method)](library/tkinter.ttk.html#tkinter.ttk.Treeview.yview) |

### Navigation

* [index](genindex.html "General Index")
* [modules](py-modindex.html "Python Module Index") |
* [Python](https://www.python.org/) »

* [3.10.20 Documentation](index.html) »
* Index
* |
* Theme
  Auto
  Light
  Dark
   |
```

**crawlee**
```
Index — Python 3.10.20 documentation















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

### Navigation

* [index](genindex.html "General Index")
* [modules](py-modindex.html "Python Module Index") |
* [Python](https://www.python.org/) »
* Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文
```

**colly+md**
```
Index — Python 3.10.20 documentation















@media only screen {
table.full-width-table {
width: 100%;
}
}



Theme
Auto
Light
Dark

### Navigation

* [index](genindex.html "General Index")
* [modules](py-modindex.html "Python Module Index") |
* [Python](https://www.python.org/) »

* [3.10.20 Documentation](index.html) »
* Index
* |
* Theme
  Auto
```

**playwright**
```
Index — Python 3.10.20 documentation















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

### Navigation

* [index](genindex.html "General Index")
* [modules](py-modindex.html "Python Module Index") |
* [Python](https://www.python.org/) »
* Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文
```

**firecrawl** — no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| docs.python.org/2.6 | 328 / 0 | 323 / 0 | 323 / 0 | — | 349 / 20 | 349 / 20 | 349 / 20 | — |
| docs.python.org/2.7 | 186 / 0 | 320 / 28 | 320 / 28 | — | 315 / 30 | 309 / 30 | 315 / 30 | — |
| docs.python.org/3.0 | 286 / 0 | 281 / 0 | 281 / 0 | — | 307 / 20 | 307 / 20 | 307 / 20 | — |
| docs.python.org/3.1 | 320 / 0 | 315 / 0 | 315 / 0 | — | 341 / 20 | 341 / 20 | 341 / 20 | — |
| docs.python.org/3.10 | 190 / 0 | 711 / 68 | 711 / 68 | 521 / 4 | 629 / 47 | 533 / 16 | 629 / 47 | — |
| docs.python.org/3.10/about.html | 180 / 0 | 604 / 68 | 604 / 68 | 407 / 4 | 520 / 52 | 424 / 21 | 520 / 52 | — |
| docs.python.org/3.10/bugs.html | 666 / 0 | 1104 / 68 | 1104 / 68 | 913 / 4 | 1026 / 52 | 930 / 21 | 1026 / 52 | — |
| docs.python.org/3.10/c-api/arg.html | 4786 / 0 | 5210 / 68 | 5210 / 68 | 5075 / 4 | 5190 / 54 | 5094 / 23 | 5190 / 54 | — |
| docs.python.org/3.10/c-api/codec.html | 899 / 0 | 1338 / 68 | 1338 / 68 | 1164 / 4 | 1279 / 54 | 1183 / 23 | 1279 / 54 | — |
| docs.python.org/3.10/c-api/conversion.html | 817 / 0 | 1252 / 68 | 1252 / 68 | 1044 / 4 | 1158 / 53 | 1062 / 22 | 1158 / 53 | — |
| docs.python.org/3.10/c-api/exceptions.html | 6000 / 0 | 6509 / 68 | 6509 / 68 | 6295 / 4 | 6407 / 51 | 6311 / 20 | 6407 / 51 | — |
| docs.python.org/3.10/c-api/gcsupport.html | 1284 / 0 | 1728 / 68 | 1728 / 68 | 1545 / 4 | 1659 / 53 | 1563 / 22 | 1659 / 53 | — |
| docs.python.org/3.10/c-api/index.html | 427 / 0 | 837 / 68 | 837 / 68 | 640 / 4 | 754 / 53 | 658 / 22 | 754 / 53 | — |
| docs.python.org/3.10/c-api/marshal.html | 580 / 0 | 1007 / 68 | 1007 / 68 | 809 / 4 | 922 / 52 | 826 / 21 | 922 / 52 | — |
| docs.python.org/3.10/c-api/memory.html | 4092 / 0 | 4582 / 68 | 4582 / 68 | 4415 / 4 | 4527 / 51 | 4431 / 20 | 4527 / 51 | — |
| docs.python.org/3.10/c-api/objimpl.html | 118 / 0 | 538 / 68 | 538 / 68 | 341 / 4 | 454 / 52 | 358 / 21 | 454 / 52 | — |
| docs.python.org/3.10/c-api/reflection.html | 357 / 0 | 775 / 68 | 775 / 68 | 590 / 4 | 701 / 50 | 605 / 19 | 701 / 50 | — |
| docs.python.org/3.10/c-api/stable.html | 3414 / 0 | 3894 / 68 | 3894 / 68 | 3695 / 4 | 3808 / 52 | 3712 / 21 | 3808 / 52 | — |
| docs.python.org/3.10/contents.html | 19401 / 0 | 19782 / 68 | 19782 / 68 | 19584 / 4 | 19697 / 52 | 19601 / 21 | 19697 / 52 | — |
| docs.python.org/3.10/copyright.html | 58 / 0 | 460 / 68 | 460 / 68 | 261 / 4 | 372 / 50 | 276 / 19 | 372 / 50 | — |
| docs.python.org/3.10/distributing/index.html | 984 / 0 | 1481 / 68 | 1481 / 68 | 1285 / 4 | 1402 / 52 | 1306 / 21 | 1402 / 52 | — |
| docs.python.org/3.10/distutils/apiref.html | 10839 / 0 | 12072 / 68 | 12072 / 68 | 11828 / 4 | 11941 / 52 | 11845 / 21 | 11941 / 52 | — |
| docs.python.org/3.10/download.html | 277 / 0 | 599 / 68 | 599 / 68 | 404 / 4 | 515 / 50 | 419 / 19 | 515 / 50 | — |
| docs.python.org/3.10/extending/index.html | 623 / 0 | 1108 / 68 | 1108 / 68 | 912 / 4 | 1028 / 55 | 932 / 24 | 1028 / 55 | — |
| docs.python.org/3.10/faq/index.html | 48 / 0 | 454 / 68 | 454 / 68 | 257 / 4 | 371 / 53 | 275 / 22 | 371 / 53 | — |
| docs.python.org/3.10/genindex-A.html | 2360 / 0 | 2679 / 68 | 2679 / 68 | 2487 / 4 | 2598 / 50 | 2502 / 19 | 2598 / 50 | — |
| docs.python.org/3.10/genindex-B.html | 1562 / 0 | 1881 / 68 | 1881 / 68 | 1689 / 4 | 1800 / 50 | 1704 / 19 | 1800 / 50 | — |
| docs.python.org/3.10/genindex-C.html | 3998 / 0 | 4317 / 68 | 4317 / 68 | 4125 / 4 | 4236 / 50 | 4140 / 19 | 4236 / 50 | — |
| docs.python.org/3.10/genindex-D.html | 2091 / 0 | 2410 / 68 | 2410 / 68 | 2218 / 4 | 2329 / 50 | 2233 / 19 | 2329 / 50 | — |
| docs.python.org/3.10/genindex-E.html | 3069 / 0 | 3388 / 68 | 3388 / 68 | 3196 / 4 | 3307 / 50 | 3211 / 19 | 3307 / 50 | — |
| docs.python.org/3.10/genindex-F.html | 2192 / 0 | 2511 / 68 | 2511 / 68 | 2319 / 4 | 2430 / 50 | 2334 / 19 | 2430 / 50 | — |
| docs.python.org/3.10/genindex-G.html | 2852 / 0 | 3171 / 68 | 3171 / 68 | 2979 / 4 | 3090 / 50 | 2994 / 19 | 3090 / 50 | — |
| docs.python.org/3.10/genindex-H.html | 1165 / 0 | 1484 / 68 | 1484 / 68 | 1292 / 4 | 1403 / 50 | 1307 / 19 | 1403 / 50 | — |
| docs.python.org/3.10/genindex-I.html | 2845 / 0 | 3164 / 68 | 3164 / 68 | 2972 / 4 | 3083 / 50 | 2987 / 19 | 3083 / 50 | — |
| docs.python.org/3.10/genindex-J.html | 171 / 0 | 490 / 68 | 490 / 68 | 298 / 4 | 409 / 50 | 313 / 19 | 409 / 50 | — |
| docs.python.org/3.10/genindex-K.html | 284 / 0 | 603 / 68 | 603 / 68 | 411 / 4 | 522 / 50 | 426 / 19 | 522 / 50 | — |
| docs.python.org/3.10/genindex-L.html | 1496 / 0 | 1815 / 68 | 1815 / 68 | 1623 / 4 | 1734 / 50 | 1638 / 19 | 1734 / 50 | — |
| docs.python.org/3.10/genindex-M.html | 2833 / 0 | 3152 / 68 | 3152 / 68 | 2960 / 4 | 3071 / 50 | 2975 / 19 | 3071 / 50 | — |
| docs.python.org/3.10/genindex-N.html | 1131 / 0 | 1450 / 68 | 1450 / 68 | 1258 / 4 | 1369 / 50 | 1273 / 19 | 1369 / 50 | — |
| docs.python.org/3.10/genindex-O.html | 1345 / 0 | 1664 / 68 | 1664 / 68 | 1472 / 4 | 1583 / 50 | 1487 / 19 | 1583 / 50 | — |
| docs.python.org/3.10/genindex-P.html | 10396 / 0 | 10715 / 68 | 10715 / 68 | 10523 / 4 | 10634 / 50 | 10538 / 19 | 10634 / 50 | — |
| docs.python.org/3.10/genindex-Q.html | 210 / 0 | 529 / 68 | 529 / 68 | 337 / 4 | 448 / 50 | 352 / 19 | 448 / 50 | — |
| docs.python.org/3.10/genindex-R.html | 3455 / 0 | 3774 / 68 | 3774 / 68 | 3582 / 4 | 3693 / 50 | 3597 / 19 | 3693 / 50 | — |
| docs.python.org/3.10/genindex-S.html | 5362 / 0 | 5681 / 68 | 5681 / 68 | 5489 / 4 | 5600 / 50 | 5504 / 19 | 5600 / 50 | — |
| docs.python.org/3.10/genindex-Symbols.html | 2582 / 0 | 2902 / 68 | 2902 / 68 | 2709 / 4 | 2820 / 50 | 2724 / 19 | 2820 / 50 | — |
| docs.python.org/3.10/genindex-T.html | 2059 / 0 | 2378 / 68 | 2378 / 68 | 2186 / 4 | 2297 / 50 | 2201 / 19 | 2297 / 50 | — |
| docs.python.org/3.10/genindex-U.html | 1215 / 0 | 1534 / 68 | 1534 / 68 | 1342 / 4 | 1453 / 50 | 1357 / 19 | 1453 / 50 | — |
| docs.python.org/3.10/genindex-V.html | 380 / 0 | 699 / 68 | 699 / 68 | 507 / 4 | 618 / 50 | 522 / 19 | 618 / 50 | — |
| docs.python.org/3.10/genindex-W.html | 912 / 0 | 1231 / 68 | 1231 / 68 | 1039 / 4 | 1150 / 50 | 1054 / 19 | 1150 / 50 | — |
| docs.python.org/3.10/genindex-X.html | 410 / 0 | 729 / 68 | 729 / 68 | 537 / 4 | 648 / 50 | 552 / 19 | 648 / 50 | — |
| docs.python.org/3.10/genindex-Y.html | 88 / 0 | 407 / 68 | 407 / 68 | 215 / 4 | 326 / 50 | 230 / 19 | 326 / 50 | — |
| docs.python.org/3.10/genindex-Z.html | 192 / 0 | 511 / 68 | 511 / 68 | 319 / 4 | 430 / 50 | 334 / 19 | 430 / 50 | — |
| docs.python.org/3.10/genindex-_.html | 1481 / 0 | 1800 / 68 | 1800 / 68 | 1608 / 4 | 1719 / 50 | 1623 / 19 | 1719 / 50 | — |
| docs.python.org/3.10/genindex-all.html | 58137 / 0 | 58376 / 68 | 58376 / 68 | 58264 / 4 | 58375 / 50 | 58279 / 19 | 58375 / 50 | — |
| docs.python.org/3.10/genindex.html | 69 / 0 | 391 / 68 | 391 / 68 | 196 / 4 | 307 / 50 | 211 / 19 | 307 / 50 | — |
| docs.python.org/3.10/glossary.html | 7963 / 0 | 8264 / 68 | 8264 / 68 | 8186 / 4 | 8302 / 50 | 8201 / 19 | 8302 / 50 | — |
| docs.python.org/3.10/howto/index.html | 135 / 0 | 553 / 68 | 553 / 68 | 356 / 4 | 468 / 51 | 372 / 20 | 468 / 51 | — |
| docs.python.org/3.10/installing/index.html | 1255 / 0 | 1808 / 68 | 1808 / 68 | 1612 / 4 | 1725 / 52 | 1629 / 21 | 1725 / 52 | — |
| docs.python.org/3.10/library/2to3.html | 2138 / 0 | 2593 / 68 | 2593 / 68 | 2445 / 4 | 2564 / 58 | 2468 / 27 | 2564 / 58 | — |
| docs.python.org/3.10/library/__future__.html | 568 / 0 | 1027 / 68 | 1027 / 68 | 829 / 4 | 944 / 54 | 848 / 23 | 944 / 54 | — |
| docs.python.org/3.10/library/__main__.html | 1810 / 0 | 2311 / 68 | 2311 / 68 | 2127 / 4 | 2247 / 54 | 2146 / 23 | 2247 / 54 | — |
| docs.python.org/3.10/library/_thread.html | 1141 / 0 | 1569 / 68 | 1569 / 68 | 1380 / 4 | 1495 / 54 | 1399 / 23 | 1495 / 54 | — |
| docs.python.org/3.10/library/abc.html | 1594 / 0 | 2031 / 68 | 2031 / 68 | 1843 / 4 | 1958 / 54 | 1862 / 23 | 1958 / 54 | — |
| docs.python.org/3.10/library/aifc.html | 1209 / 0 | 1636 / 68 | 1636 / 68 | 1456 / 4 | 1575 / 58 | 1479 / 27 | 1575 / 58 | — |
| docs.python.org/3.10/library/argparse.html | 10217 / 0 | 11122 / 68 | 11122 / 68 | 10816 / 4 | 11022 / 58 | 10839 / 27 | 11022 / 58 | — |
| docs.python.org/3.10/library/array.html | 1450 / 0 | 1874 / 68 | 1874 / 68 | 1697 / 4 | 1814 / 56 | 1718 / 25 | 1814 / 56 | — |
| docs.python.org/3.10/library/ast.html | 8584 / 0 | 9114 / 68 | 9114 / 68 | 8945 / 4 | 9112 / 54 | 8964 / 23 | 9112 / 54 | — |
| docs.python.org/3.10/library/asynchat.html | 1060 / 0 | 1543 / 68 | 1543 / 68 | 1353 / 4 | 1469 / 55 | 1373 / 24 | 1469 / 55 | — |
| docs.python.org/3.10/library/asyncio.html | 271 / 0 | 724 / 68 | 724 / 68 | 524 / 4 | 639 / 53 | 542 / 22 | 639 / 53 | — |
| docs.python.org/3.10/library/asyncore.html | 1826 / 0 | 2301 / 68 | 2301 / 68 | 2125 / 4 | 2240 / 54 | 2144 / 23 | 2240 / 54 | — |
| docs.python.org/3.10/library/atexit.html | 579 / 0 | 1062 / 68 | 1062 / 68 | 862 / 4 | 976 / 53 | 880 / 22 | 976 / 53 | — |
| docs.python.org/3.10/library/audioop.html | 1616 / 0 | 2082 / 68 | 2082 / 68 | 1869 / 4 | 1985 / 55 | 1889 / 24 | 1985 / 55 | — |
| docs.python.org/3.10/library/base64.html | 1616 / 0 | 2126 / 68 | 2126 / 68 | 1919 / 4 | 2038 / 57 | 1941 / 26 | 2038 / 57 | — |
| docs.python.org/3.10/library/bdb.html | 2171 / 0 | 2599 / 68 | 2599 / 68 | 2414 / 4 | 2528 / 53 | 2432 / 22 | 2528 / 53 | — |
| docs.python.org/3.10/library/binascii.html | 1225 / 0 | 1692 / 68 | 1692 / 68 | 1498 / 4 | 1616 / 56 | 1519 / 25 | 1616 / 56 | — |
| docs.python.org/3.10/library/binhex.html | 273 / 0 | 771 / 68 | 771 / 68 | 574 / 4 | 691 / 56 | 595 / 25 | 691 / 56 | — |
| docs.python.org/3.10/library/bisect.html | 1347 / 0 | 1876 / 68 | 1876 / 68 | 1640 / 4 | 1758 / 54 | 1659 / 23 | 1758 / 54 | — |
| docs.python.org/3.10/library/builtins.html | 200 / 0 | 658 / 68 | 658 / 68 | 459 / 4 | 573 / 53 | 477 / 22 | 573 / 53 | — |
| docs.python.org/3.10/library/bz2.html | 1666 / 0 | 2187 / 68 | 2187 / 68 | 1981 / 4 | 2100 / 55 | 2001 / 24 | 2100 / 55 | — |
| docs.python.org/3.10/library/calendar.html | 2245 / 0 | 2709 / 68 | 2709 / 68 | 2492 / 4 | 2607 / 54 | 2511 / 23 | 2607 / 54 | — |
| docs.python.org/3.10/library/cgi.html | 3396 / 0 | 3961 / 68 | 3961 / 68 | 3759 / 4 | 3875 / 55 | 3779 / 24 | 3875 / 55 | — |
| docs.python.org/3.10/library/cgitb.html | 568 / 0 | 1031 / 68 | 1031 / 68 | 827 / 4 | 944 / 56 | 848 / 25 | 944 / 56 | — |
| docs.python.org/3.10/library/chunk.html | 749 / 0 | 1209 / 68 | 1209 / 68 | 1014 / 4 | 1130 / 55 | 1034 / 24 | 1130 / 55 | — |
| docs.python.org/3.10/library/cmath.html | 1573 / 0 | 2094 / 68 | 2094 / 68 | 1910 / 4 | 2030 / 56 | 1931 / 25 | 2030 / 56 | — |
| docs.python.org/3.10/library/cmd.html | 1926 / 0 | 2402 / 68 | 2402 / 68 | 2209 / 4 | 2326 / 56 | 2230 / 25 | 2326 / 56 | — |
| docs.python.org/3.10/library/code.html | 1097 / 0 | 1575 / 68 | 1575 / 68 | 1374 / 4 | 1489 / 54 | 1393 / 23 | 1489 / 54 | — |
| docs.python.org/3.10/library/codecs.html | 8089 / 0 | 8731 / 68 | 8731 / 68 | 8530 / 4 | 8648 / 56 | 8551 / 25 | 8648 / 56 | — |
| docs.python.org/3.10/library/codeop.html | 475 / 0 | 912 / 68 | 912 / 68 | 712 / 4 | 827 / 54 | 731 / 23 | 827 / 54 | — |
| docs.python.org/3.10/library/collections.abc.html | 1989 / 0 | 2453 / 68 | 2453 / 68 | 2294 / 4 | 2414 / 56 | 2315 / 25 | 2414 / 56 | — |
| docs.python.org/3.10/library/collections.html | 7020 / 0 | 7592 / 68 | 7592 / 68 | 7389 / 4 | 7533 / 53 | 7407 / 22 | 7533 / 53 | — |
| docs.python.org/3.10/library/colorsys.html | 270 / 0 | 717 / 68 | 717 / 68 | 511 / 4 | 628 / 55 | 531 / 24 | 628 / 55 | — |
| docs.python.org/3.10/library/compileall.html | 1982 / 0 | 2493 / 68 | 2493 / 68 | 2271 / 4 | 2386 / 54 | 2290 / 23 | 2386 / 54 | — |
| docs.python.org/3.10/library/concurrent.futures.html | 2888 / 0 | 3251 / 68 | 3251 / 68 | 3187 / 4 | 3302 / 54 | 3206 / 23 | 3302 / 54 | — |
| docs.python.org/3.10/library/configparser.html | 6501 / 0 | 7095 / 68 | 7095 / 68 | 6852 / 4 | 6982 / 54 | 6871 / 23 | 6982 / 54 | — |
| docs.python.org/3.10/library/contextlib.html | 4524 / 0 | 5056 / 68 | 5056 / 68 | 4915 / 4 | 5038 / 55 | 4935 / 24 | 5038 / 55 | — |
| docs.python.org/3.10/library/contextvars.html | 1171 / 0 | 1637 / 68 | 1637 / 68 | 1458 / 4 | 1572 / 53 | 1476 / 22 | 1572 / 53 | — |
| docs.python.org/3.10/library/copy.html | 546 / 0 | 1011 / 68 | 1011 / 68 | 817 / 4 | 934 / 56 | 838 / 25 | 934 / 56 | — |
| docs.python.org/3.10/library/copyreg.html | 297 / 0 | 773 / 68 | 773 / 68 | 572 / 4 | 689 / 55 | 592 / 24 | 689 / 55 | — |
| docs.python.org/3.10/library/crypt.html | 870 / 0 | 1380 / 68 | 1380 / 68 | 1183 / 4 | 1300 / 56 | 1204 / 25 | 1300 / 56 | — |
| docs.python.org/3.10/library/csv.html | 3079 / 0 | 3553 / 68 | 3553 / 68 | 3374 / 4 | 3493 / 56 | 3395 / 25 | 3493 / 56 | — |
| docs.python.org/3.10/library/ctypes.html | 13276 / 0 | 13960 / 68 | 13960 / 68 | 13819 / 4 | 14006 / 57 | 13841 / 26 | 14006 / 57 | — |
| docs.python.org/3.10/library/curses.ascii.html | 882 / 0 | 1334 / 68 | 1334 / 68 | 1155 / 4 | 1271 / 55 | 1175 / 24 | 1271 / 55 | — |
| docs.python.org/3.10/library/curses.html | 9381 / 0 | 9874 / 68 | 9874 / 68 | 9702 / 4 | 9819 / 56 | 9723 / 25 | 9819 / 56 | — |
| docs.python.org/3.10/library/curses.panel.html | 454 / 0 | 947 / 68 | 947 / 68 | 763 / 4 | 881 / 57 | 785 / 26 | 881 / 57 | — |
| docs.python.org/3.10/library/dataclasses.html | 4336 / 0 | 4833 / 68 | 4833 / 68 | 4671 / 4 | 4785 / 53 | 4689 / 22 | 4785 / 53 | — |
| docs.python.org/3.10/library/datetime.html | 14043 / 0 | 14623 / 68 | 14623 / 68 | 14458 / 4 | 14601 / 56 | 14479 / 25 | 14601 / 56 | — |
| docs.python.org/3.10/library/dbm.html | 2055 / 0 | 2567 / 68 | 2567 / 68 | 2382 / 4 | 2498 / 55 | 2402 / 24 | 2498 / 55 | — |
| docs.python.org/3.10/library/decimal.html | 10530 / 0 | 11095 / 68 | 11095 / 68 | 10905 / 4 | 11070 / 58 | 10928 / 27 | 11070 / 58 | — |
| docs.python.org/3.10/library/dialog.html | 905 / 0 | 1411 / 68 | 1411 / 68 | 1212 / 4 | 1324 / 51 | 1228 / 20 | 1324 / 51 | — |
| docs.python.org/3.10/library/difflib.html | 4304 / 0 | 4881 / 68 | 4881 / 68 | 4617 / 4 | 4753 / 55 | 4637 / 24 | 4753 / 55 | — |
| docs.python.org/3.10/library/dis.html | 5494 / 0 | 5861 / 68 | 5861 / 68 | 5797 / 4 | 5915 / 55 | 5817 / 24 | 5915 / 55 | — |
| docs.python.org/3.10/library/distutils.html | 323 / 0 | 779 / 68 | 779 / 68 | 578 / 4 | 695 / 56 | 599 / 25 | 695 / 56 | — |
| docs.python.org/3.10/library/doctest.html | 10436 / 0 | 11124 / 68 | 11124 / 68 | 10855 / 4 | 10994 / 55 | 10875 / 24 | 10994 / 55 | — |
| docs.python.org/3.10/library/email.charset.html | 1141 / 0 | 1578 / 68 | 1578 / 68 | 1388 / 4 | 1502 / 53 | 1406 / 22 | 1502 / 53 | — |
| docs.python.org/3.10/library/email.contentmanager.html | 1161 / 0 | 1661 / 68 | 1661 / 68 | 1438 / 4 | 1552 / 53 | 1456 / 22 | 1552 / 53 | — |
| docs.python.org/3.10/library/email.encoders.html | 411 / 0 | 856 / 68 | 856 / 68 | 662 / 4 | 774 / 51 | 678 / 20 | 774 / 51 | — |
| docs.python.org/3.10/library/email.errors.html | 721 / 0 | 1166 / 68 | 1166 / 68 | 978 / 4 | 1093 / 54 | 997 / 23 | 1093 / 54 | — |
| docs.python.org/3.10/library/email.generator.html | 1903 / 0 | 2374 / 68 | 2374 / 68 | 2158 / 4 | 2272 / 53 | 2176 / 22 | 2272 / 53 | — |
| docs.python.org/3.10/library/email.header.html | 1325 / 0 | 1812 / 68 | 1812 / 68 | 1598 / 4 | 1713 / 52 | 1615 / 21 | 1713 / 52 | — |
| docs.python.org/3.10/library/email.headerregistry.html | 2644 / 0 | 3012 / 68 | 3012 / 68 | 2907 / 4 | 3021 / 53 | 2925 / 22 | 3021 / 53 | — |
| docs.python.org/3.10/library/email.html | 1220 / 0 | 1660 / 68 | 1660 / 68 | 1467 / 4 | 1585 / 57 | 1489 / 26 | 1585 / 57 | — |
| docs.python.org/3.10/library/email.iterators.html | 307 / 0 | 775 / 68 | 775 / 68 | 566 / 4 | 679 / 51 | 582 / 20 | 679 / 51 | — |
| docs.python.org/3.10/library/email.message.html | 4417 / 0 | 4902 / 68 | 4902 / 68 | 4694 / 4 | 4811 / 54 | 4713 / 23 | 4811 / 54 | — |
| docs.python.org/3.10/library/email.mime.html | 1416 / 0 | 1923 / 68 | 1923 / 68 | 1699 / 4 | 1817 / 57 | 1721 / 26 | 1817 / 57 | — |
| docs.python.org/3.10/library/email.parser.html | 1975 / 0 | 2500 / 68 | 2500 / 68 | 2274 / 4 | 2389 / 53 | 2292 / 22 | 2389 / 53 | — |
| docs.python.org/3.10/library/email.policy.html | 3961 / 0 | 4388 / 68 | 4388 / 68 | 4222 / 4 | 4339 / 52 | 4239 / 21 | 4339 / 52 | — |
| docs.python.org/3.10/library/email.utils.html | 1462 / 0 | 1908 / 68 | 1908 / 68 | 1703 / 4 | 1816 / 52 | 1720 / 21 | 1816 / 52 | — |
| docs.python.org/3.10/library/ensurepip.html | 718 / 0 | 1220 / 68 | 1220 / 68 | 1019 / 4 | 1135 / 55 | 1039 / 24 | 1135 / 55 | — |
| docs.python.org/3.10/library/enum.html | 5317 / 0 | 6130 / 68 | 6130 / 68 | 5890 / 4 | 6062 / 54 | 5909 / 23 | 6062 / 54 | — |
| docs.python.org/3.10/library/errno.html | 1472 / 0 | 1825 / 68 | 1825 / 68 | 1749 / 4 | 1865 / 55 | 1769 / 24 | 1865 / 55 | — |
| docs.python.org/3.10/library/faulthandler.html | 940 / 0 | 1470 / 68 | 1470 / 68 | 1269 / 4 | 1385 / 55 | 1289 / 24 | 1385 / 55 | — |
| docs.python.org/3.10/library/fcntl.html | 1235 / 0 | 1695 / 68 | 1695 / 68 | 1486 / 4 | 1605 / 57 | 1508 / 26 | 1605 / 57 | — |
| docs.python.org/3.10/library/filecmp.html | 883 / 0 | 1372 / 68 | 1372 / 68 | 1174 / 4 | 1291 / 55 | 1194 / 24 | 1291 / 55 | — |
| docs.python.org/3.10/library/fileinput.html | 1371 / 0 | 1842 / 68 | 1842 / 68 | 1630 / 4 | 1749 / 58 | 1653 / 27 | 1749 / 58 | — |
| docs.python.org/3.10/library/fnmatch.html | 383 / 0 | 851 / 68 | 851 / 68 | 652 / 4 | 769 / 55 | 672 / 24 | 769 / 55 | — |
| docs.python.org/3.10/library/fractions.html | 785 / 0 | 1238 / 68 | 1238 / 68 | 1050 / 4 | 1168 / 53 | 1068 / 22 | 1168 / 53 | — |
| docs.python.org/3.10/library/ftplib.html | 2732 / 0 | 3220 / 68 | 3220 / 68 | 3015 / 4 | 3133 / 54 | 3034 / 23 | 3133 / 54 | — |
| docs.python.org/3.10/library/functools.html | 3279 / 0 | 3803 / 68 | 3803 / 68 | 3586 / 4 | 3717 / 58 | 3609 / 27 | 3717 / 58 | — |
| docs.python.org/3.10/library/gc.html | 1628 / 0 | 2049 / 68 | 2049 / 68 | 1877 / 4 | 1994 / 54 | 1896 / 23 | 1994 / 54 | — |
| docs.python.org/3.10/library/getopt.html | 984 / 0 | 1462 / 68 | 1462 / 68 | 1261 / 4 | 1381 / 57 | 1283 / 26 | 1381 / 57 | — |
| docs.python.org/3.10/library/getpass.html | 260 / 0 | 713 / 68 | 713 / 68 | 515 / 4 | 630 / 54 | 534 / 23 | 630 / 54 | — |
| docs.python.org/3.10/library/gettext.html | 3929 / 0 | 4515 / 68 | 4515 / 68 | 4272 / 4 | 4387 / 54 | 4291 / 23 | 4387 / 54 | — |
| docs.python.org/3.10/library/glob.html | 666 / 0 | 1141 / 68 | 1141 / 68 | 933 / 4 | 1052 / 56 | 954 / 25 | 1052 / 56 | — |
| docs.python.org/3.10/library/graphlib.html | 1203 / 0 | 1674 / 68 | 1674 / 68 | 1482 / 4 | 1602 / 57 | 1504 / 26 | 1602 / 57 | — |
| docs.python.org/3.10/library/grp.html | 335 / 0 | 782 / 68 | 782 / 68 | 588 / 4 | 703 / 54 | 607 / 23 | 703 / 54 | — |
| docs.python.org/3.10/library/gzip.html | 1449 / 0 | 1965 / 68 | 1965 / 68 | 1756 / 4 | 1872 / 55 | 1776 / 24 | 1872 / 55 | — |
| docs.python.org/3.10/library/hashlib.html | 3609 / 0 | 4195 / 68 | 4195 / 68 | 3960 / 4 | 4093 / 56 | 3981 / 25 | 4093 / 56 | — |
| docs.python.org/3.10/library/heapq.html | 2153 / 0 | 2660 / 68 | 2660 / 68 | 2448 / 4 | 2565 / 54 | 2467 / 23 | 2565 / 54 | — |
| docs.python.org/3.10/library/hmac.html | 737 / 0 | 1207 / 68 | 1207 / 68 | 1010 / 4 | 1126 / 55 | 1030 / 24 | 1126 / 55 | — |
| docs.python.org/3.10/library/html.entities.html | 166 / 0 | 615 / 68 | 615 / 68 | 421 / 4 | 538 / 56 | 442 / 25 | 538 / 56 | — |
| docs.python.org/3.10/library/html.html | 193 / 0 | 651 / 68 | 651 / 68 | 450 / 4 | 566 / 55 | 470 / 24 | 566 / 55 | — |
| docs.python.org/3.10/library/html.parser.html | 1522 / 0 | 2027 / 68 | 2027 / 68 | 1833 / 4 | 1957 / 56 | 1854 / 25 | 1957 / 56 | — |
| docs.python.org/3.10/library/http.client.html | 2920 / 0 | 3389 / 68 | 3389 / 68 | 3209 / 4 | 3330 / 54 | 3228 / 23 | 3330 / 54 | — |
| docs.python.org/3.10/library/http.cookiejar.html | 3807 / 0 | 4309 / 68 | 4309 / 68 | 4142 / 4 | 4259 / 56 | 4163 / 25 | 4259 / 56 | — |
| docs.python.org/3.10/library/http.cookies.html | 1279 / 0 | 1755 / 68 | 1755 / 68 | 1570 / 4 | 1686 / 54 | 1589 / 23 | 1686 / 54 | — |
| docs.python.org/3.10/library/http.html | 1046 / 0 | 1519 / 68 | 1519 / 68 | 1321 / 4 | 1436 / 53 | 1339 / 22 | 1436 / 53 | — |
| docs.python.org/3.10/library/http.server.html | 2802 / 0 | 3255 / 68 | 3255 / 68 | 3083 / 4 | 3197 / 53 | 3101 / 22 | 3197 / 53 | — |
| docs.python.org/3.10/library/idle.html | 6334 / 0 | 6990 / 68 | 6990 / 68 | 6857 / 4 | 6969 / 50 | 6872 / 19 | 6969 / 50 | — |
| docs.python.org/3.10/library/imaplib.html | 3049 / 0 | 3517 / 68 | 3517 / 68 | 3332 / 4 | 3448 / 54 | 3351 / 23 | 3448 / 54 | — |
| docs.python.org/3.10/library/imghdr.html | 396 / 0 | 862 / 68 | 862 / 68 | 661 / 4 | 780 / 57 | 683 / 26 | 780 / 57 | — |
| docs.python.org/3.10/library/imp.html | 2270 / 0 | 2743 / 68 | 2743 / 68 | 2557 / 4 | 2673 / 55 | 2577 / 24 | 2673 / 55 | — |
| docs.python.org/3.10/library/importlib.html | 9186 / 0 | 9668 / 68 | 9668 / 68 | 9577 / 4 | 9694 / 55 | 9597 / 24 | 9694 / 55 | — |
| docs.python.org/3.10/library/importlib.metadata.html | 1419 / 0 | 1948 / 68 | 1948 / 68 | 1730 / 4 | 1863 / 51 | 1746 / 20 | 1863 / 51 | — |
| docs.python.org/3.10/library/index.html | 2282 / 0 | 2684 / 68 | 2684 / 68 | 2487 / 4 | 2601 / 53 | 2505 / 22 | 2601 / 53 | — |
| docs.python.org/3.10/library/inspect.html | 7199 / 0 | 7738 / 68 | 7738 / 68 | 7554 / 4 | 7678 / 54 | 7573 / 23 | 7678 / 54 | — |
| docs.python.org/3.10/library/io.html | 6375 / 0 | 6949 / 68 | 6949 / 68 | 6766 / 4 | 6885 / 57 | 6788 / 26 | 6885 / 57 | — |
| docs.python.org/3.10/library/ipaddress.html | 4907 / 0 | 5471 / 68 | 5471 / 68 | 5300 / 4 | 5441 / 54 | 5319 / 23 | 5441 / 54 | — |
| docs.python.org/3.10/library/itertools.html | 5234 / 0 | 5746 / 68 | 5746 / 68 | 5535 / 4 | 5655 / 57 | 5557 / 26 | 5655 / 57 | — |
| docs.python.org/3.10/library/json.html | 3807 / 0 | 4419 / 68 | 4419 / 68 | 4166 / 4 | 4291 / 55 | 4186 / 24 | 4291 / 55 | — |
| docs.python.org/3.10/library/keyword.html | 163 / 0 | 625 / 68 | 625 / 68 | 430 / 4 | 546 / 55 | 450 / 24 | 546 / 55 | — |
| docs.python.org/3.10/library/linecache.html | 386 / 0 | 846 / 68 | 846 / 68 | 645 / 4 | 763 / 56 | 666 / 25 | 763 / 56 | — |
| docs.python.org/3.10/library/locale.html | 3211 / 0 | 3683 / 68 | 3683 / 68 | 3502 / 4 | 3617 / 53 | 3520 / 22 | 3617 / 53 | — |
| docs.python.org/3.10/library/logging.config.html | 5080 / 0 | 5655 / 68 | 5655 / 68 | 5461 / 4 | 5575 / 53 | 5479 / 22 | 5575 / 53 | — |
| docs.python.org/3.10/library/logging.handlers.html | 6934 / 0 | 7443 / 68 | 7443 / 68 | 7281 / 4 | 7395 / 53 | 7299 / 22 | 7395 / 53 | — |
| docs.python.org/3.10/library/logging.html | 9093 / 0 | 9665 / 68 | 9665 / 68 | 9481 / 4 | 9597 / 55 | 9501 / 24 | 9597 / 55 | — |
| docs.python.org/3.10/library/lzma.html | 2417 / 0 | 2960 / 68 | 2960 / 68 | 2748 / 4 | 2865 / 56 | 2769 / 25 | 2865 / 56 | — |
| docs.python.org/3.10/library/mailbox.html | 7933 / 0 | 8407 / 68 | 8407 / 68 | 8282 / 4 | 8399 / 56 | 8303 / 25 | 8399 / 56 | — |
| docs.python.org/3.10/library/mailcap.html | 683 / 0 | 1151 / 68 | 1151 / 68 | 946 / 4 | 1062 / 54 | 965 / 23 | 1062 / 54 | — |
| docs.python.org/3.10/library/marshal.html | 851 / 0 | 1298 / 68 | 1298 / 68 | 1104 / 4 | 1220 / 55 | 1124 / 24 | 1220 / 55 | — |
| docs.python.org/3.10/library/math.html | 3306 / 0 | 3822 / 68 | 3822 / 68 | 3633 / 4 | 3750 / 53 | 3651 / 22 | 3750 / 53 | — |
| docs.python.org/3.10/library/mimetypes.html | 1466 / 0 | 1970 / 68 | 1970 / 68 | 1769 / 4 | 1887 / 56 | 1790 / 25 | 1887 / 56 | — |
| docs.python.org/3.10/library/mmap.html | 2045 / 0 | 2521 / 68 | 2521 / 68 | 2328 / 4 | 2443 / 54 | 2347 / 23 | 2443 / 54 | — |
| docs.python.org/3.10/library/modulefinder.html | 388 / 0 | 883 / 68 | 883 / 68 | 685 / 4 | 803 / 57 | 707 / 26 | 803 / 57 | — |
| docs.python.org/3.10/library/msilib.html | 2326 / 0 | 2951 / 68 | 2951 / 68 | 2675 / 4 | 2793 / 57 | 2697 / 26 | 2793 / 57 | — |
| docs.python.org/3.10/library/msvcrt.html | 736 / 0 | 1223 / 68 | 1223 / 68 | 1037 / 4 | 1156 / 58 | 1060 / 27 | 1156 / 58 | — |
| docs.python.org/3.10/library/multiprocessing.html | 16627 / 0 | 16934 / 68 | 16934 / 68 | 17116 / 4 | 17246 / 53 | 17134 / 22 | 17246 / 53 | — |
| docs.python.org/3.10/library/multiprocessing.shared_mem | 2070 / 0 | 2511 / 68 | 2511 / 68 | 2313 / 4 | 2442 / 58 | 2336 / 27 | 2442 / 58 | — |
| docs.python.org/3.10/library/netrc.html | 483 / 0 | 959 / 68 | 959 / 68 | 768 / 4 | 883 / 54 | 787 / 23 | 883 / 54 | — |
| docs.python.org/3.10/library/nis.html | 338 / 0 | 803 / 68 | 803 / 68 | 603 / 4 | 721 / 57 | 625 / 26 | 721 / 57 | — |
| docs.python.org/3.10/library/nntplib.html | 3114 / 0 | 3636 / 68 | 3636 / 68 | 3421 / 4 | 3546 / 54 | 3440 / 23 | 3546 / 54 | — |
| docs.python.org/3.10/library/numbers.html | 1026 / 0 | 1503 / 68 | 1503 / 68 | 1331 / 4 | 1447 / 55 | 1351 / 24 | 1447 / 55 | — |
| docs.python.org/3.10/library/operator.html | 2403 / 0 | 2949 / 68 | 2949 / 68 | 2704 / 4 | 2824 / 55 | 2724 / 24 | 2824 / 55 | — |
| docs.python.org/3.10/library/optparse.html | 10934 / 0 | 11683 / 68 | 11683 / 68 | 11559 / 4 | 11677 / 56 | 11580 / 25 | 11677 / 56 | — |
| docs.python.org/3.10/library/os.html | 24697 / 0 | 25322 / 68 | 25322 / 68 | 25098 / 4 | 25215 / 55 | 25118 / 24 | 25215 / 55 | — |
| docs.python.org/3.10/library/os.path.html | 2744 / 0 | 3193 / 68 | 3193 / 68 | 3011 / 4 | 3132 / 54 | 3030 / 23 | 3132 / 54 | — |
| docs.python.org/3.10/library/ossaudiodev.html | 2200 / 0 | 2678 / 68 | 2678 / 68 | 2503 / 4 | 2620 / 56 | 2524 / 25 | 2620 / 56 | — |
| docs.python.org/3.10/library/pathlib.html | 5049 / 0 | 5624 / 68 | 5624 / 68 | 5380 / 4 | 5569 / 54 | 5399 / 23 | 5569 / 54 | — |
| docs.python.org/3.10/library/pdb.html | 3220 / 0 | 3677 / 68 | 3677 / 68 | 3491 / 4 | 3608 / 54 | 3510 / 23 | 3608 / 54 | — |
| docs.python.org/3.10/library/pickle.html | 7266 / 0 | 7872 / 68 | 7872 / 68 | 7667 / 4 | 7785 / 54 | 7686 / 23 | 7785 / 54 | — |
| docs.python.org/3.10/library/pickletools.html | 600 / 0 | 1093 / 68 | 1093 / 68 | 895 / 4 | 1011 / 55 | 915 / 24 | 1011 / 55 | — |
| docs.python.org/3.10/library/pipes.html | 438 / 0 | 915 / 68 | 915 / 68 | 719 / 4 | 836 / 55 | 739 / 24 | 836 / 55 | — |
| docs.python.org/3.10/library/pkgutil.html | 1566 / 0 | 2034 / 68 | 2034 / 68 | 1833 / 4 | 1948 / 54 | 1852 / 23 | 1948 / 54 | — |
| docs.python.org/3.10/library/platform.html | 1359 / 0 | 1891 / 68 | 1891 / 68 | 1694 / 4 | 1812 / 57 | 1716 / 26 | 1812 / 57 | — |
| docs.python.org/3.10/library/plistlib.html | 759 / 0 | 1239 / 68 | 1239 / 68 | 1030 / 4 | 1148 / 57 | 1052 / 26 | 1148 / 57 | — |
| docs.python.org/3.10/library/poplib.html | 1308 / 0 | 1776 / 68 | 1776 / 68 | 1591 / 4 | 1706 / 54 | 1610 / 23 | 1706 / 54 | — |
| docs.python.org/3.10/library/posix.html | 587 / 0 | 1074 / 68 | 1074 / 68 | 876 / 4 | 994 / 57 | 898 / 26 | 994 / 57 | — |
| docs.python.org/3.10/library/pprint.html | 1887 / 0 | 2411 / 68 | 2411 / 68 | 2172 / 4 | 2295 / 54 | 2191 / 23 | 2295 / 54 | — |
| docs.python.org/3.10/library/profile.html | 4218 / 0 | 4756 / 68 | 4756 / 68 | 4561 / 4 | 4674 / 52 | 4578 / 21 | 4674 / 52 | — |
| docs.python.org/3.10/library/pty.html | 625 / 0 | 1103 / 68 | 1103 / 68 | 906 / 4 | 1020 / 53 | 924 / 22 | 1020 / 53 | — |
| docs.python.org/3.10/library/pwd.html | 370 / 0 | 825 / 68 | 825 / 68 | 631 / 4 | 746 / 54 | 650 / 23 | 746 / 54 | — |
| docs.python.org/3.10/library/py_compile.html | 976 / 0 | 1455 / 68 | 1455 / 68 | 1259 / 4 | 1375 / 55 | 1279 / 24 | 1375 / 55 | — |
| docs.python.org/3.10/library/pyclbr.html | 681 / 0 | 1160 / 68 | 1160 / 68 | 974 / 4 | 1090 / 55 | 994 / 24 | 1090 / 55 | — |
| docs.python.org/3.10/library/pydoc.html | 794 / 0 | 1243 / 68 | 1243 / 68 | 1043 / 4 | 1161 / 57 | 1065 / 26 | 1161 / 57 | — |
| docs.python.org/3.10/library/pyexpat.html | 4431 / 0 | 4885 / 68 | 4885 / 68 | 4742 / 4 | 4859 / 56 | 4763 / 25 | 4859 / 56 | — |
| docs.python.org/3.10/library/queue.html | 1520 / 0 | 1985 / 68 | 1985 / 68 | 1795 / 4 | 1911 / 55 | 1815 / 24 | 1911 / 55 | — |
| docs.python.org/3.10/library/quopri.html | 364 / 0 | 830 / 68 | 830 / 68 | 623 / 4 | 741 / 57 | 645 / 26 | 741 / 57 | — |
| docs.python.org/3.10/library/random.html | 3281 / 0 | 3806 / 68 | 3806 / 68 | 3606 / 4 | 3724 / 54 | 3625 / 23 | 3724 / 54 | — |
| docs.python.org/3.10/library/re.html | 9356 / 0 | 9952 / 68 | 9952 / 68 | 9753 / 4 | 9905 / 54 | 9772 / 23 | 9905 / 54 | — |
| docs.python.org/3.10/library/readline.html | 1626 / 0 | 2118 / 68 | 2118 / 68 | 1941 / 4 | 2056 / 54 | 1960 / 23 | 2056 / 54 | — |
| docs.python.org/3.10/library/reprlib.html | 740 / 0 | 1211 / 68 | 1211 / 68 | 1021 / 4 | 1137 / 54 | 1040 / 23 | 1137 / 54 | — |
| docs.python.org/3.10/library/resource.html | 1831 / 0 | 2296 / 68 | 2296 / 68 | 2128 / 4 | 2243 / 54 | 2147 / 23 | 2243 / 54 | — |
| docs.python.org/3.10/library/rlcompleter.html | 349 / 0 | 825 / 68 | 825 / 68 | 624 / 4 | 742 / 56 | 645 / 25 | 742 / 56 | — |
| docs.python.org/3.10/library/runpy.html | 1239 / 0 | 1707 / 68 | 1707 / 68 | 1506 / 4 | 1623 / 56 | 1527 / 25 | 1623 / 56 | — |
| docs.python.org/3.10/library/sched.html | 681 / 0 | 1157 / 68 | 1157 / 68 | 950 / 4 | 1065 / 53 | 968 / 22 | 1065 / 53 | — |
| docs.python.org/3.10/library/secrets.html | 795 / 0 | 1314 / 68 | 1314 / 68 | 1120 / 4 | 1242 / 58 | 1143 / 27 | 1242 / 58 | — |
| docs.python.org/3.10/library/select.html | 3079 / 0 | 3578 / 68 | 3578 / 68 | 3404 / 4 | 3520 / 55 | 3424 / 24 | 3520 / 55 | — |
| docs.python.org/3.10/library/selectors.html | 1205 / 0 | 1671 / 68 | 1671 / 68 | 1500 / 4 | 1615 / 54 | 1519 / 23 | 1615 / 54 | — |
| docs.python.org/3.10/library/shelve.html | 1303 / 0 | 1792 / 68 | 1792 / 68 | 1586 / 4 | 1701 / 54 | 1605 / 23 | 1701 / 54 | — |
| docs.python.org/3.10/library/shlex.html | 2634 / 0 | 3119 / 68 | 3119 / 68 | 2931 / 4 | 3052 / 54 | 2950 / 23 | 3052 / 54 | — |
| docs.python.org/3.10/library/shutil.html | 4501 / 0 | 5083 / 68 | 5083 / 68 | 4838 / 4 | 4956 / 54 | 4857 / 23 | 4956 / 54 | — |
| docs.python.org/3.10/library/signal.html | 3708 / 0 | 4214 / 68 | 4214 / 68 | 4045 / 4 | 4162 / 56 | 4066 / 25 | 4162 / 56 | — |
| docs.python.org/3.10/library/site.html | 1436 / 0 | 1895 / 68 | 1895 / 68 | 1717 / 4 | 1832 / 54 | 1736 / 23 | 1832 / 54 | — |
| docs.python.org/3.10/library/smtpd.html | 1546 / 0 | 2043 / 68 | 2043 / 68 | 1851 / 4 | 1965 / 53 | 1869 / 22 | 1965 / 53 | — |
| docs.python.org/3.10/library/smtplib.html | 3412 / 0 | 3903 / 68 | 3903 / 68 | 3707 / 4 | 3823 / 54 | 3726 / 23 | 3823 / 54 | — |
| docs.python.org/3.10/library/sndhdr.html | 308 / 0 | 757 / 68 | 757 / 68 | 559 / 4 | 676 / 56 | 580 / 25 | 676 / 56 | — |
| docs.python.org/3.10/library/socket.html | 11142 / 0 | 11663 / 68 | 11663 / 68 | 11493 / 4 | 11610 / 54 | 11512 / 23 | 11610 / 54 | — |
| docs.python.org/3.10/library/socketserver.html | 3148 / 0 | 3651 / 68 | 3651 / 68 | 3479 / 4 | 3596 / 56 | 3500 / 25 | 3596 / 56 | — |
| docs.python.org/3.10/library/spwd.html | 352 / 0 | 816 / 68 | 816 / 68 | 621 / 4 | 737 / 55 | 641 / 24 | 737 / 55 | — |
| docs.python.org/3.10/library/sqlite3.html | 8367 / 0 | 9053 / 68 | 9053 / 68 | 8886 / 4 | 9019 / 57 | 8908 / 26 | 9019 / 57 | — |
| docs.python.org/3.10/library/ssl.html | 14137 / 0 | 14692 / 68 | 14692 / 68 | 14602 / 4 | 14739 / 56 | 14623 / 25 | 14739 / 56 | — |
| docs.python.org/3.10/library/stat.html | 1676 / 0 | 2080 / 68 | 2080 / 68 | 1947 / 4 | 2062 / 54 | 1966 / 23 | 2062 / 54 | — |
| docs.python.org/3.10/library/statistics.html | 4959 / 0 | 5509 / 68 | 5509 / 68 | 5284 / 4 | 5437 / 54 | 5303 / 23 | 5437 / 54 | — |
| docs.python.org/3.10/library/string.html | 5002 / 0 | 5531 / 68 | 5531 / 68 | 5311 / 4 | 5439 / 54 | 5330 / 23 | 5439 / 54 | — |
| docs.python.org/3.10/library/stringprep.html | 610 / 0 | 1035 / 68 | 1035 / 68 | 855 / 4 | 970 / 54 | 874 / 23 | 970 / 54 | — |
| docs.python.org/3.10/library/struct.html | 3237 / 0 | 3793 / 68 | 3793 / 68 | 3574 / 4 | 3702 / 57 | 3596 / 26 | 3702 / 57 | — |
| docs.python.org/3.10/library/subprocess.html | 8245 / 0 | 8859 / 68 | 8859 / 68 | 8676 / 4 | 8795 / 53 | 8694 / 22 | 8795 / 53 | — |
| docs.python.org/3.10/library/sunau.html | 1076 / 0 | 1536 / 68 | 1536 / 68 | 1367 / 4 | 1485 / 57 | 1389 / 26 | 1485 / 57 | — |
| docs.python.org/3.10/library/symtable.html | 821 / 0 | 1292 / 68 | 1292 / 68 | 1130 / 4 | 1249 / 57 | 1152 / 26 | 1249 / 57 | — |
| docs.python.org/3.10/library/sys.html | 9831 / 0 | 10228 / 68 | 10228 / 68 | 10086 / 4 | 10204 / 55 | 10106 / 24 | 10204 / 55 | — |
| docs.python.org/3.10/library/sysconfig.html | 1372 / 0 | 1884 / 68 | 1884 / 68 | 1683 / 4 | 1802 / 57 | 1705 / 26 | 1802 / 57 | — |
| docs.python.org/3.10/library/syslog.html | 666 / 0 | 1130 / 68 | 1130 / 68 | 937 / 4 | 1053 / 55 | 957 / 24 | 1053 / 55 | — |
| docs.python.org/3.10/library/tabnanny.html | 271 / 0 | 723 / 68 | 723 / 68 | 530 / 4 | 646 / 55 | 550 / 24 | 646 / 55 | — |
| docs.python.org/3.10/library/tarfile.html | 6635 / 0 | 7156 / 68 | 7156 / 68 | 7002 / 4 | 7120 / 57 | 7024 / 26 | 7120 / 57 | — |
| docs.python.org/3.10/library/telnetlib.html | 1179 / 0 | 1662 / 68 | 1662 / 68 | 1474 / 4 | 1589 / 53 | 1492 / 22 | 1589 / 53 | — |
| docs.python.org/3.10/library/tempfile.html | 2306 / 0 | 2856 / 68 | 2856 / 68 | 2611 / 4 | 2730 / 56 | 2632 / 25 | 2730 / 56 | — |
| docs.python.org/3.10/library/termios.html | 529 / 0 | 1005 / 68 | 1005 / 68 | 806 / 4 | 922 / 55 | 826 / 24 | 922 / 55 | — |
| docs.python.org/3.10/library/test.html | 8154 / 0 | 8763 / 68 | 8763 / 68 | 8593 / 4 | 8710 / 56 | 8614 / 25 | 8710 / 56 | — |
| docs.python.org/3.10/library/textwrap.html | 1542 / 0 | 2016 / 68 | 2016 / 68 | 1793 / 4 | 1912 / 55 | 1813 / 24 | 1912 / 55 | — |
| docs.python.org/3.10/library/threading.html | 6512 / 0 | 7008 / 68 | 7008 / 68 | 6839 / 4 | 6953 / 53 | 6857 / 22 | 6953 / 53 | — |
| docs.python.org/3.10/library/time.html | 4751 / 0 | 5234 / 68 | 5234 / 68 | 5072 / 4 | 5192 / 55 | 5092 / 24 | 5192 / 55 | — |
| docs.python.org/3.10/library/timeit.html | 1940 / 0 | 2457 / 68 | 2457 / 68 | 2251 / 4 | 2375 / 58 | 2274 / 27 | 2375 / 58 | — |
| docs.python.org/3.10/library/tkinter.colorchooser.html | 120 / 0 | 577 / 68 | 577 / 68 | 377 / 4 | 492 / 54 | 396 / 23 | 492 / 54 | — |
| docs.python.org/3.10/library/tkinter.dnd.html | 311 / 0 | 768 / 68 | 768 / 68 | 566 / 4 | 682 / 55 | 586 / 24 | 682 / 55 | — |
| docs.python.org/3.10/library/tkinter.font.html | 486 / 0 | 894 / 68 | 894 / 68 | 727 / 4 | 842 / 54 | 746 / 23 | 842 / 54 | — |
| docs.python.org/3.10/library/tkinter.html | 6333 / 0 | 6895 / 68 | 6895 / 68 | 6766 / 4 | 6883 / 55 | 6786 / 24 | 6883 / 55 | — |
| docs.python.org/3.10/library/tkinter.messagebox.html | 161 / 0 | 626 / 68 | 626 / 68 | 402 / 4 | 517 / 54 | 421 / 23 | 517 / 54 | — |
| docs.python.org/3.10/library/tkinter.scrolledtext.html | 168 / 0 | 622 / 68 | 622 / 68 | 425 / 4 | 540 / 54 | 444 / 23 | 540 / 54 | — |
| docs.python.org/3.10/library/tkinter.tix.html | 2415 / 0 | 2882 / 68 | 2882 / 68 | 2744 / 4 | 2860 / 55 | 2764 / 24 | 2860 / 55 | — |
| docs.python.org/3.10/library/tkinter.ttk.html | 7241 / 0 | 7928 / 68 | 7928 / 68 | 7720 / 4 | 7835 / 54 | 7739 / 23 | 7835 / 54 | — |
| docs.python.org/3.10/library/token.html | 952 / 0 | 1367 / 68 | 1367 / 68 | 1223 / 4 | 1341 / 57 | 1245 / 26 | 1341 / 57 | — |
| docs.python.org/3.10/library/tokenize.html | 1398 / 0 | 1886 / 68 | 1886 / 68 | 1695 / 4 | 1811 / 55 | 1715 / 24 | 1811 / 55 | — |
| docs.python.org/3.10/library/trace.html | 1003 / 0 | 1518 / 68 | 1518 / 68 | 1326 / 4 | 1444 / 57 | 1348 / 26 | 1444 / 57 | — |
| docs.python.org/3.10/library/traceback.html | 2518 / 0 | 3039 / 68 | 3039 / 68 | 2819 / 4 | 2939 / 57 | 2841 / 26 | 2939 / 57 | — |
| docs.python.org/3.10/library/tracemalloc.html | 3466 / 0 | 4008 / 68 | 4008 / 68 | 3849 / 4 | 3964 / 54 | 3868 / 23 | 3964 / 54 | — |
| docs.python.org/3.10/library/tty.html | 159 / 0 | 608 / 68 | 608 / 68 | 408 / 4 | 523 / 54 | 427 / 23 | 523 / 54 | — |
| docs.python.org/3.10/library/turtle.html | 9367 / 0 | 10157 / 68 | 10157 / 68 | 9943 / 4 | 10135 / 53 | 9961 / 22 | 10135 / 53 | — |
| docs.python.org/3.10/library/types.html | 2140 / 0 | 2633 / 68 | 2633 / 68 | 2467 / 4 | 2588 / 59 | 2491 / 28 | 2588 / 59 | — |
| docs.python.org/3.10/library/typing.html | 10829 / 0 | 11365 / 68 | 11365 / 68 | 11300 / 4 | 11420 / 55 | 11320 / 24 | 11420 / 55 | — |
| docs.python.org/3.10/library/unicodedata.html | 813 / 0 | 1249 / 68 | 1249 / 68 | 1064 / 4 | 1179 / 53 | 1082 / 22 | 1179 / 53 | — |
| docs.python.org/3.10/library/unittest.html | 12854 / 0 | 13518 / 68 | 13518 / 68 | 13265 / 4 | 13382 / 54 | 13284 / 23 | 13382 / 54 | — |
| docs.python.org/3.10/library/unittest.mock.html | 13362 / 0 | 14188 / 68 | 14188 / 68 | 13813 / 4 | 14055 / 54 | 13832 / 23 | 14055 / 54 | — |
| docs.python.org/3.10/library/urllib.error.html | 302 / 0 | 751 / 68 | 751 / 68 | 561 / 4 | 678 / 56 | 582 / 25 | 678 / 56 | — |
| docs.python.org/3.10/library/urllib.html | 93 / 0 | 559 / 68 | 559 / 68 | 360 / 4 | 475 / 54 | 379 / 23 | 475 / 54 | — |
| docs.python.org/3.10/library/urllib.parse.html | 4143 / 0 | 4711 / 68 | 4711 / 68 | 4472 / 4 | 4594 / 55 | 4492 / 24 | 4594 / 55 | — |
| docs.python.org/3.10/library/urllib.request.html | 8250 / 0 | 8900 / 68 | 8900 / 68 | 8697 / 4 | 8823 / 56 | 8718 / 25 | 8823 / 56 | — |
| docs.python.org/3.10/library/urllib.robotparser.html | 401 / 0 | 847 / 68 | 847 / 68 | 656 / 4 | 772 / 54 | 675 / 23 | 772 / 54 | — |
| docs.python.org/3.10/library/uu.html | 417 / 0 | 875 / 68 | 875 / 68 | 672 / 4 | 789 / 56 | 693 / 25 | 789 / 56 | — |
| docs.python.org/3.10/library/uuid.html | 1375 / 0 | 1867 / 68 | 1867 / 68 | 1670 / 4 | 1789 / 57 | 1692 / 26 | 1789 / 57 | — |
| docs.python.org/3.10/library/venv.html | 3279 / 0 | 3798 / 68 | 3798 / 68 | 3598 / 4 | 3714 / 55 | 3618 / 24 | 3714 / 55 | — |
| docs.python.org/3.10/library/warnings.html | 3007 / 0 | 3586 / 68 | 3586 / 68 | 3352 / 4 | 3466 / 53 | 3370 / 22 | 3466 / 53 | — |
| docs.python.org/3.10/library/wave.html | 1015 / 0 | 1468 / 68 | 1468 / 68 | 1294 / 4 | 1411 / 56 | 1315 / 25 | 1411 / 56 | — |
| docs.python.org/3.10/library/weakref.html | 3188 / 0 | 3696 / 68 | 3696 / 68 | 3509 / 4 | 3632 / 53 | 3527 / 22 | 3632 / 53 | — |
| docs.python.org/3.10/library/webbrowser.html | 1102 / 0 | 1585 / 68 | 1585 / 68 | 1385 / 4 | 1500 / 54 | 1404 / 23 | 1500 / 54 | — |
| docs.python.org/3.10/library/winreg.html | 3520 / 0 | 4028 / 68 | 4028 / 68 | 3851 / 4 | 3967 / 54 | 3870 / 23 | 3967 / 54 | — |
| docs.python.org/3.10/library/winsound.html | 641 / 0 | 1072 / 68 | 1072 / 68 | 886 / 4 | 1002 / 55 | 906 / 24 | 1002 / 55 | — |
| docs.python.org/3.10/library/wsgiref.html | 4795 / 0 | 5318 / 68 | 5318 / 68 | 5144 / 4 | 5261 / 56 | 5165 / 25 | 5261 / 56 | — |
| docs.python.org/3.10/library/xdrlib.html | 1244 / 0 | 1700 / 68 | 1700 / 68 | 1531 / 4 | 1648 / 56 | 1552 / 25 | 1648 / 56 | — |
| docs.python.org/3.10/library/xml.dom.html | 5037 / 0 | 5540 / 68 | 5540 / 68 | 5426 / 4 | 5543 / 56 | 5447 / 25 | 5543 / 56 | — |
| docs.python.org/3.10/library/xml.dom.minidom.html | 1737 / 0 | 2261 / 68 | 2261 / 68 | 2052 / 4 | 2167 / 54 | 2071 / 23 | 2167 / 54 | — |
| docs.python.org/3.10/library/xml.dom.pulldom.html | 655 / 0 | 1146 / 68 | 1146 / 68 | 948 / 4 | 1066 / 57 | 970 / 26 | 1066 / 57 | — |
| docs.python.org/3.10/library/xml.etree.elementtree.html | 7550 / 0 | 8230 / 68 | 8230 / 68 | 7977 / 4 | 8104 / 55 | 7997 / 24 | 8104 / 55 | — |
| docs.python.org/3.10/library/xml.html | 922 / 0 | 1404 / 68 | 1404 / 68 | 1211 / 4 | 1324 / 52 | 1228 / 21 | 1324 / 52 | — |
| docs.python.org/3.10/library/xml.sax.handler.html | 2295 / 0 | 2771 / 68 | 2771 / 68 | 2604 / 4 | 2721 / 56 | 2625 / 25 | 2721 / 56 | — |
| docs.python.org/3.10/library/xml.sax.html | 1025 / 0 | 1524 / 68 | 1524 / 68 | 1326 / 4 | 1442 / 55 | 1346 / 24 | 1442 / 55 | — |
| docs.python.org/3.10/library/xml.sax.reader.html | 1633 / 0 | 2105 / 68 | 2105 / 68 | 1952 / 4 | 2068 / 55 | 1972 / 24 | 2068 / 55 | — |
| docs.python.org/3.10/library/xml.sax.utils.html | 541 / 0 | 1007 / 68 | 1007 / 68 | 802 / 4 | 917 / 53 | 820 / 22 | 917 / 53 | — |
| docs.python.org/3.10/library/xmlrpc.client.html | 2693 / 0 | 3224 / 68 | 3224 / 68 | 3038 / 4 | 3153 / 54 | 3057 / 23 | 3153 / 54 | — |
| docs.python.org/3.10/library/xmlrpc.server.html | 2007 / 0 | 2509 / 68 | 2509 / 68 | 2312 / 4 | 2427 / 54 | 2331 / 23 | 2427 / 54 | — |
| docs.python.org/3.10/library/zipapp.html | 2771 / 0 | 3319 / 68 | 3319 / 68 | 3116 / 4 | 3237 / 56 | 3137 / 25 | 3237 / 56 | — |
| docs.python.org/3.10/library/zipfile.html | 4384 / 0 | 4935 / 68 | 4935 / 68 | 4757 / 4 | 4875 / 55 | 4777 / 24 | 4875 / 55 | — |
| docs.python.org/3.10/library/zipimport.html | 959 / 0 | 1416 / 68 | 1416 / 68 | 1232 / 4 | 1349 / 56 | 1253 / 25 | 1349 / 56 | — |
| docs.python.org/3.10/library/zlib.html | 2078 / 0 | 2527 / 68 | 2527 / 68 | 2331 / 4 | 2447 / 55 | 2351 / 24 | 2447 / 55 | — |
| docs.python.org/3.10/library/zoneinfo.html | 2190 / 0 | 2738 / 68 | 2738 / 68 | 2545 / 4 | 2668 / 55 | 2565 / 24 | 2668 / 55 | — |
| docs.python.org/3.10/license.html | 6986 / 0 | 7625 / 68 | 7625 / 68 | 7445 / 4 | 7558 / 52 | 7462 / 21 | 7558 / 52 | — |
| docs.python.org/3.10/py-modindex.html | 4077 / 0 | 4420 / 68 | 4420 / 68 | 4208 / 4 | 4324 / 55 | 4228 / 24 | 4324 / 55 | — |
| docs.python.org/3.10/reference/index.html | 438 / 0 | 844 / 68 | 844 / 68 | 647 / 4 | 761 / 53 | 665 / 22 | 761 / 53 | — |
| docs.python.org/3.10/search.html | 21 / 0 | 340 / 68 | 340 / 68 | 145 / 4 | 390 / 184 | 294 / 153 | 390 / 184 | — |
| docs.python.org/3.10/tutorial/index.html | 982 / 0 | 1382 / 68 | 1382 / 68 | 1185 / 4 | 1298 / 52 | 1202 / 21 | 1298 / 52 | — |
| docs.python.org/3.10/using/index.html | 460 / 0 | 870 / 68 | 870 / 68 | 673 / 4 | 787 / 53 | 691 / 22 | 787 / 53 | — |
| docs.python.org/3.10/whatsnew/2.0.html | 9031 / 0 | 9636 / 68 | 9636 / 68 | 9440 / 4 | 9556 / 54 | 9459 / 23 | 9556 / 54 | — |
| docs.python.org/3.10/whatsnew/2.1.html | 5603 / 0 | 6202 / 68 | 6202 / 68 | 6016 / 4 | 6133 / 54 | 6035 / 23 | 6133 / 54 | — |
| docs.python.org/3.10/whatsnew/2.2.html | 8889 / 0 | 9506 / 68 | 9506 / 68 | 9306 / 4 | 9429 / 54 | 9325 / 23 | 9429 / 54 | — |
| docs.python.org/3.10/whatsnew/2.3.html | 13061 / 0 | 13822 / 68 | 13822 / 68 | 13604 / 4 | 13752 / 54 | 13623 / 23 | 13752 / 54 | — |
| docs.python.org/3.10/whatsnew/2.4.html | 9193 / 0 | 9879 / 68 | 9879 / 68 | 9664 / 4 | 9806 / 54 | 9683 / 23 | 9806 / 54 | — |
| docs.python.org/3.10/whatsnew/2.5.html | 14279 / 0 | 14998 / 68 | 14998 / 68 | 14804 / 4 | 14927 / 54 | 14823 / 23 | 14927 / 54 | — |
| docs.python.org/3.10/whatsnew/2.6.html | 18020 / 0 | 18895 / 68 | 18895 / 68 | 18673 / 4 | 18827 / 54 | 18692 / 23 | 18827 / 54 | — |
| docs.python.org/3.10/whatsnew/2.7.html | 16678 / 0 | 17596 / 68 | 17596 / 68 | 17381 / 4 | 17529 / 54 | 17400 / 23 | 17529 / 54 | — |
| docs.python.org/3.10/whatsnew/3.0.html | 5654 / 0 | 6289 / 68 | 6289 / 68 | 6095 / 4 | 6210 / 54 | 6114 / 23 | 6210 / 54 | — |
| docs.python.org/3.10/whatsnew/3.1.html | 2814 / 0 | 3356 / 68 | 3356 / 68 | 3149 / 4 | 3278 / 54 | 3168 / 23 | 3278 / 54 | — |
| docs.python.org/3.10/whatsnew/3.10.html | 12688 / 0 | 13749 / 68 | 13749 / 68 | 13627 / 4 | 13773 / 54 | 13646 / 23 | 13773 / 54 | — |
| docs.python.org/3.10/whatsnew/3.2.html | 14450 / 0 | 15360 / 68 | 15360 / 68 | 15093 / 4 | 15268 / 54 | 15112 / 23 | 15268 / 54 | — |
| docs.python.org/3.10/whatsnew/3.3.html | 13478 / 0 | 14601 / 68 | 14601 / 68 | 14419 / 4 | 14550 / 54 | 14438 / 23 | 14550 / 54 | — |
| docs.python.org/3.10/whatsnew/3.4.html | 15521 / 0 | 16605 / 68 | 16605 / 68 | 16408 / 4 | 16528 / 54 | 16427 / 23 | 16528 / 54 | — |
| docs.python.org/3.10/whatsnew/3.5.html | 12043 / 0 | 13260 / 68 | 13260 / 68 | 13052 / 4 | 13191 / 54 | 13071 / 23 | 13191 / 54 | — |
| docs.python.org/3.10/whatsnew/3.6.html | 12456 / 0 | 13727 / 68 | 13727 / 68 | 13533 / 4 | 13656 / 54 | 13552 / 23 | 13656 / 54 | — |
| docs.python.org/3.10/whatsnew/3.7.html | 13498 / 0 | 14690 / 68 | 14690 / 68 | 14509 / 4 | 14624 / 54 | 14528 / 23 | 14624 / 54 | — |
| docs.python.org/3.10/whatsnew/3.8.html | 11745 / 0 | 12704 / 68 | 12704 / 68 | 12486 / 4 | 12619 / 54 | 12505 / 23 | 12619 / 54 | — |
| docs.python.org/3.10/whatsnew/3.9.html | 8741 / 0 | 9585 / 68 | 9585 / 68 | 9408 / 4 | 9526 / 54 | 9427 / 23 | 9526 / 54 | — |
| docs.python.org/3.10/whatsnew/changelog.html | 183653 / 0 | 188265 / 68 | 188265 / 68 | 188054 / 4 | 188169 / 50 | 188069 / 19 | 188169 / 50 | — |
| docs.python.org/3.10/whatsnew/index.html | 2172 / 0 | 2587 / 68 | 2587 / 68 | 2389 / 4 | 2503 / 53 | 2407 / 22 | 2503 / 53 | — |
| docs.python.org/3.11 | 188 / 0 | 711 / 68 | 711 / 68 | 522 / 4 | 629 / 47 | 534 / 16 | 629 / 47 | — |
| docs.python.org/3.11/about.html | 180 / 0 | 606 / 68 | 606 / 68 | 410 / 4 | 522 / 52 | 427 / 21 | 522 / 52 | — |
| docs.python.org/3.11/bugs.html | 666 / 0 | 1106 / 68 | 1106 / 68 | 916 / 4 | 1028 / 52 | 933 / 21 | 1028 / 52 | — |
| docs.python.org/3.11/c-api/index.html | 430 / 0 | 842 / 68 | 842 / 68 | 646 / 4 | 759 / 53 | 664 / 22 | 759 / 53 | — |
| docs.python.org/3.11/contents.html | 20473 / 0 | 20856 / 68 | 20856 / 68 | 20659 / 4 | 20771 / 52 | 20676 / 21 | 20771 / 52 | — |
| docs.python.org/3.11/copyright.html | 58 / 0 | 462 / 68 | 462 / 68 | 264 / 4 | 374 / 50 | 279 / 19 | 374 / 50 | — |
| docs.python.org/3.11/distributing/index.html | 34 / 0 | 384 / 68 | 384 / 68 | 188 / 4 | 300 / 52 | 205 / 21 | 300 / 52 | — |
| docs.python.org/3.11/download.html | 261 / 0 | 585 / 68 | 585 / 68 | 391 / 4 | 501 / 50 | 406 / 19 | 501 / 50 | — |
| docs.python.org/3.11/extending/index.html | 623 / 0 | 1110 / 68 | 1110 / 68 | 915 / 4 | 1030 / 55 | 935 / 24 | 1030 / 55 | — |
| docs.python.org/3.11/faq/index.html | 48 / 0 | 456 / 68 | 456 / 68 | 260 / 4 | 373 / 53 | 278 / 22 | 373 / 53 | — |
| docs.python.org/3.11/glossary.html | 8454 / 0 | 8760 / 68 | 8760 / 68 | 8680 / 4 | 8795 / 50 | 8695 / 19 | 8795 / 50 | — |
| docs.python.org/3.11/howto/index.html | 140 / 0 | 556 / 68 | 556 / 68 | 360 / 4 | 471 / 51 | 376 / 20 | 471 / 51 | — |
| docs.python.org/3.11/installing/index.html | 1257 / 0 | 1816 / 68 | 1816 / 68 | 1621 / 4 | 1733 / 52 | 1638 / 21 | 1733 / 52 | — |
| docs.python.org/3.11/library/index.html | 2303 / 0 | 2707 / 68 | 2707 / 68 | 2511 / 4 | 2624 / 53 | 2529 / 22 | 2624 / 53 | — |
| docs.python.org/3.11/license.html | 7664 / 0 | 8309 / 68 | 8309 / 68 | 8130 / 4 | 8242 / 52 | 8147 / 21 | 8242 / 52 | — |
| docs.python.org/3.11/py-modindex.html | 4153 / 0 | 4498 / 68 | 4498 / 68 | 4287 / 4 | 4402 / 55 | 4307 / 24 | 4402 / 55 | — |
| docs.python.org/3.11/reference/index.html | 438 / 0 | 846 / 68 | 846 / 68 | 650 / 4 | 763 / 53 | 668 / 22 | 763 / 53 | — |
| docs.python.org/3.11/search.html | 13 / 0 | 334 / 68 | 334 / 68 | 147 / 4 | 437 / 230 | 342 / 199 | 437 / 230 | — |
| docs.python.org/3.11/tutorial/index.html | 996 / 0 | 1398 / 68 | 1398 / 68 | 1202 / 4 | 1314 / 52 | 1219 / 21 | 1314 / 52 | — |
| docs.python.org/3.11/using/index.html | 476 / 0 | 888 / 68 | 888 / 68 | 692 / 4 | 805 / 53 | 710 / 22 | 805 / 53 | — |
| docs.python.org/3.11/whatsnew/3.11.html | 13320 / 0 | 14517 / 68 | 14517 / 68 | 14330 / 4 | 14445 / 54 | 14349 / 23 | 14445 / 54 | — |
| docs.python.org/3.11/whatsnew/index.html | 2356 / 0 | 2773 / 68 | 2773 / 68 | 2576 / 4 | 2689 / 53 | 2594 / 22 | 2689 / 53 | — |
| docs.python.org/3.12 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.12/about.html | 185 / 0 | 609 / 68 | 609 / 68 | 415 / 4 | 527 / 52 | 432 / 21 | 527 / 52 | — |
| docs.python.org/3.12/bugs.html | 692 / 0 | 1130 / 68 | 1130 / 68 | 942 / 4 | 1054 / 52 | 959 / 21 | 1054 / 52 | — |
| docs.python.org/3.12/c-api/index.html | 414 / 0 | 824 / 68 | 824 / 68 | 630 / 4 | 743 / 53 | 648 / 22 | 743 / 53 | — |
| docs.python.org/3.12/contents.html | 19854 / 0 | 20235 / 68 | 20235 / 68 | 20040 / 4 | 20152 / 52 | 20057 / 21 | 20152 / 52 | — |
| docs.python.org/3.12/deprecations/index.html | 2848 / 0 | 3378 / 68 | 3378 / 68 | 3182 / 4 | 3292 / 50 | 3197 / 19 | 3292 / 50 | — |
| docs.python.org/3.12/download.html | 264 / 0 | 586 / 68 | 586 / 68 | 394 / 4 | 504 / 50 | 409 / 19 | 504 / 50 | — |
| docs.python.org/3.12/extending/index.html | 617 / 0 | 1102 / 68 | 1102 / 68 | 909 / 4 | 1024 / 55 | 929 / 24 | 1024 / 55 | — |
| docs.python.org/3.12/glossary.html | 8711 / 0 | 8999 / 68 | 8999 / 68 | 8909 / 4 | 9039 / 50 | 8924 / 19 | 9039 / 50 | — |
| docs.python.org/3.12/howto/index.html | 148 / 0 | 562 / 68 | 562 / 68 | 368 / 4 | 479 / 51 | 384 / 20 | 479 / 51 | — |
| docs.python.org/3.12/installing/index.html | 1254 / 0 | 1811 / 68 | 1811 / 68 | 1618 / 4 | 1730 / 52 | 1635 / 21 | 1730 / 52 | — |
| docs.python.org/3.12/library/index.html | 2287 / 0 | 2689 / 68 | 2689 / 68 | 2495 / 4 | 2608 / 53 | 2513 / 22 | 2608 / 53 | — |
| docs.python.org/3.12/license.html | 7715 / 0 | 8320 / 68 | 8320 / 68 | 8143 / 4 | 8255 / 52 | 8160 / 21 | 8255 / 52 | — |
| docs.python.org/3.12/py-modindex.html | 3653 / 0 | 3996 / 68 | 3996 / 68 | 3787 / 4 | 3902 / 55 | 3807 / 24 | 3902 / 55 | — |
| docs.python.org/3.12/reference/index.html | 448 / 0 | 854 / 68 | 854 / 68 | 660 / 4 | 773 / 53 | 678 / 22 | 773 / 53 | — |
| docs.python.org/3.12/tutorial/index.html | 995 / 0 | 1395 / 68 | 1395 / 68 | 1201 / 4 | 1313 / 52 | 1218 / 21 | 1313 / 52 | — |
| docs.python.org/3.12/using/index.html | 502 / 0 | 912 / 68 | 912 / 68 | 718 / 4 | 831 / 53 | 736 / 22 | 831 / 53 | — |
| docs.python.org/3.12/whatsnew/3.12.html | 15630 / 0 | 16742 / 68 | 16742 / 68 | 16524 / 4 | 16660 / 54 | 16543 / 23 | 16660 / 54 | — |
| docs.python.org/3.12/whatsnew/index.html | 2464 / 0 | 2879 / 68 | 2879 / 68 | 2684 / 4 | 2797 / 53 | 2702 / 22 | 2797 / 53 | — |
| docs.python.org/3.13 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.13/about.html | 185 / 0 | 609 / 68 | 609 / 68 | 415 / 4 | 527 / 52 | 432 / 21 | 527 / 52 | — |
| docs.python.org/3.13/c-api/index.html | 463 / 0 | 873 / 68 | 873 / 68 | 679 / 4 | 792 / 53 | 697 / 22 | 792 / 53 | — |
| docs.python.org/3.13/contents.html | 20945 / 0 | 21326 / 68 | 21326 / 68 | 21131 / 4 | 21243 / 52 | 21148 / 21 | 21243 / 52 | — |
| docs.python.org/3.13/copyright.html | 58 / 0 | 460 / 68 | 460 / 68 | 264 / 4 | 374 / 50 | 279 / 19 | 374 / 50 | — |
| docs.python.org/3.13/deprecations/index.html | 3129 / 0 | 3671 / 68 | 3671 / 68 | 3475 / 4 | 3585 / 50 | 3490 / 19 | 3585 / 50 | — |
| docs.python.org/3.13/download.html | 149 / 0 | 471 / 68 | 471 / 68 | 279 / 4 | 389 / 50 | 294 / 19 | 389 / 50 | — |
| docs.python.org/3.13/extending/index.html | 576 / 0 | 1062 / 68 | 1062 / 68 | 868 / 4 | 983 / 55 | 888 / 24 | 983 / 55 | — |
| docs.python.org/3.13/glossary.html | 10587 / 0 | 10850 / 68 | 10850 / 68 | 10785 / 4 | 10916 / 50 | 10800 / 19 | 10916 / 50 | — |
| docs.python.org/3.13/howto/index.html | 174 / 0 | 584 / 68 | 584 / 68 | 390 / 4 | 501 / 51 | 406 / 20 | 501 / 51 | — |
| docs.python.org/3.13/installing/index.html | 1017 / 0 | 1548 / 68 | 1548 / 68 | 1353 / 4 | 1465 / 52 | 1370 / 21 | 1465 / 52 | — |
| docs.python.org/3.13/library/index.html | 2124 / 0 | 2526 / 68 | 2526 / 68 | 2332 / 4 | 2445 / 53 | 2350 / 22 | 2445 / 53 | — |
| docs.python.org/3.13/license.html | 7891 / 0 | 8523 / 68 | 8523 / 68 | 8329 / 4 | 8441 / 52 | 8346 / 21 | 8441 / 52 | — |
| docs.python.org/3.13/py-modindex.html | 3540 / 0 | 3883 / 68 | 3883 / 68 | 3674 / 4 | 3789 / 55 | 3694 / 24 | 3789 / 55 | — |
| docs.python.org/3.13/tutorial/index.html | 1029 / 0 | 1429 / 68 | 1429 / 68 | 1235 / 4 | 1347 / 52 | 1252 / 21 | 1347 / 52 | — |
| docs.python.org/3.13/using/index.html | 281 / 0 | 691 / 68 | 691 / 68 | 497 / 4 | 610 / 53 | 515 / 22 | 610 / 53 | — |
| docs.python.org/3.13/whatsnew/3.13.html | 17269 / 0 | 18380 / 68 | 18380 / 68 | 18181 / 4 | 18302 / 54 | 18200 / 23 | 18302 / 54 | — |
| docs.python.org/3.13/whatsnew/index.html | 2535 / 0 | 2950 / 68 | 2950 / 68 | 2755 / 4 | 2868 / 53 | 2773 / 22 | 2868 / 53 | — |
| docs.python.org/3.14 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.14/about.html | 185 / 0 | 617 / 68 | 617 / 68 | 495 / 4 | 607 / 52 | 512 / 21 | 607 / 52 | — |
| docs.python.org/3.14/c-api/index.html | 556 / 0 | 974 / 68 | 974 / 68 | 852 / 4 | 965 / 53 | 870 / 22 | 965 / 53 | — |
| docs.python.org/3.14/contents.html | 22176 / 0 | 22570 / 68 | 22570 / 68 | 22442 / 4 | 22554 / 52 | 22459 / 21 | 22554 / 52 | — |
| docs.python.org/3.14/copyright.html | 58 / 0 | 468 / 68 | 468 / 68 | 344 / 4 | 454 / 50 | 359 / 19 | 454 / 50 | — |
| docs.python.org/3.14/deprecations/index.html | 3233 / 0 | 3782 / 68 | 3782 / 68 | 3659 / 4 | 3770 / 50 | 3674 / 19 | 3770 / 50 | — |
| docs.python.org/3.14/download.html | 129 / 0 | 451 / 68 | 451 / 68 | 259 / 4 | 369 / 50 | 274 / 19 | 369 / 50 | — |
| docs.python.org/3.14/extending/index.html | 576 / 0 | 1070 / 68 | 1070 / 68 | 948 / 4 | 1063 / 55 | 968 / 24 | 1063 / 55 | — |
| docs.python.org/3.14/glossary.html | 11322 / 0 | 11582 / 68 | 11582 / 68 | 11600 / 4 | 11731 / 50 | 11615 / 19 | 11731 / 50 | — |
| docs.python.org/3.14/howto/index.html | 178 / 0 | 596 / 68 | 596 / 68 | 474 / 4 | 585 / 51 | 490 / 20 | 585 / 51 | — |
| docs.python.org/3.14/library/index.html | 2207 / 0 | 2617 / 68 | 2617 / 68 | 2495 / 4 | 2608 / 53 | 2513 / 22 | 2608 / 53 | — |
| docs.python.org/3.14/py-modindex.html | 3602 / 0 | 3948 / 68 | 3948 / 68 | 3736 / 4 | 3851 / 55 | 3756 / 24 | 3851 / 55 | — |
| docs.python.org/3.14/reference/index.html | 465 / 0 | 879 / 68 | 879 / 68 | 757 / 4 | 870 / 53 | 775 / 22 | 870 / 53 | — |
| docs.python.org/3.14/tutorial/index.html | 1029 / 0 | 1437 / 68 | 1437 / 68 | 1315 / 4 | 1427 / 52 | 1332 / 21 | 1427 / 52 | — |
| docs.python.org/3.14/using/index.html | 285 / 0 | 703 / 68 | 703 / 68 | 581 / 4 | 694 / 53 | 599 / 22 | 694 / 53 | — |
| docs.python.org/3.14/whatsnew/3.14.html | 19859 / 0 | 21273 / 68 | 21273 / 68 | 21115 / 4 | 21256 / 54 | 21134 / 23 | 21256 / 54 | — |
| docs.python.org/3.14/whatsnew/index.html | 2583 / 0 | 3006 / 68 | 3006 / 68 | 2883 / 4 | 2996 / 53 | 2901 / 22 | 2996 / 53 | — |
| docs.python.org/3.15 | 191 / 0 | 709 / 67 | 709 / 67 | 525 / 4 | 629 / 46 | 537 / 16 | 629 / 46 | — |
| docs.python.org/3.15/about.html | 183 / 0 | 612 / 67 | 612 / 67 | 493 / 4 | 602 / 51 | 510 / 21 | 602 / 51 | — |
| docs.python.org/3.15/bugs.html | 650 / 0 | 1093 / 67 | 1093 / 67 | 980 / 4 | 1089 / 51 | 997 / 21 | 1089 / 51 | — |
| docs.python.org/3.15/c-api/index.html | 562 / 0 | 973 / 67 | 973 / 67 | 854 / 4 | 964 / 52 | 872 / 22 | 964 / 52 | — |
| docs.python.org/3.15/contents.html | 22587 / 0 | 22982 / 67 | 22982 / 67 | 22853 / 4 | 22962 / 51 | 22870 / 21 | 22962 / 51 | — |
| docs.python.org/3.15/deprecations/index.html | 3791 / 0 | 4385 / 67 | 4385 / 67 | 4265 / 4 | 4373 / 49 | 4280 / 19 | 4373 / 49 | — |
| docs.python.org/3.15/download.html | 129 / 0 | 448 / 67 | 448 / 67 | 259 / 4 | 366 / 49 | 274 / 19 | 366 / 49 | — |
| docs.python.org/3.15/extending/index.html | 607 / 0 | 1098 / 67 | 1098 / 67 | 979 / 4 | 1091 / 54 | 999 / 24 | 1091 / 54 | — |
| docs.python.org/3.15/howto/index.html | 179 / 0 | 594 / 67 | 594 / 67 | 475 / 4 | 583 / 50 | 491 / 20 | 583 / 50 | — |
| docs.python.org/3.15/library/index.html | 2227 / 0 | 2634 / 67 | 2634 / 67 | 2515 / 4 | 2625 / 52 | 2533 / 22 | 2625 / 52 | — |
| docs.python.org/3.15/license.html | 8580 / 0 | 9235 / 67 | 9235 / 67 | 9116 / 4 | 9225 / 51 | 9133 / 21 | 9225 / 51 | — |
| docs.python.org/3.15/py-modindex.html | 3639 / 0 | 3984 / 67 | 3984 / 67 | 3773 / 4 | 3885 / 54 | 3793 / 24 | 3885 / 54 | — |
| docs.python.org/3.15/tutorial/index.html | 1037 / 0 | 1442 / 67 | 1442 / 67 | 1323 / 4 | 1432 / 51 | 1340 / 21 | 1432 / 51 | — |
| docs.python.org/3.15/whatsnew/3.15.html | 12156 / 0 | 13177 / 67 | 13177 / 67 | 13022 / 4 | 13151 / 53 | 13041 / 23 | 13151 / 53 | — |
| docs.python.org/3.15/whatsnew/index.html | 2607 / 0 | 3027 / 67 | 3027 / 67 | 2907 / 4 | 3017 / 52 | 2925 / 22 | 3017 / 52 | — |
| docs.python.org/3.2 | 302 / 0 | 298 / 0 | 298 / 0 | — | 324 / 20 | 323 / 20 | 324 / 20 | — |
| docs.python.org/3.3 | 302 / 0 | 298 / 0 | 298 / 0 | — | 324 / 20 | 323 / 20 | 324 / 20 | — |
| docs.python.org/3.3/about.html | 314 / 0 | 319 / 0 | 319 / 0 | — | 338 / 22 | 337 / 22 | 338 / 22 | — |
| docs.python.org/3.3/bugs.html | 743 / 0 | 746 / 0 | 746 / 0 | — | 766 / 21 | 765 / 21 | 766 / 21 | — |
| docs.python.org/3.3/c-api/index.html | 411 / 0 | 416 / 0 | 416 / 0 | — | 436 / 23 | 435 / 23 | 436 / 23 | — |
| docs.python.org/3.3/contents.html | 14509 / 0 | 14515 / 0 | 14515 / 0 | — | 14533 / 22 | 14532 / 22 | 14533 / 22 | — |
| docs.python.org/3.3/copyright.html | 185 / 0 | 192 / 0 | 192 / 0 | — | 207 / 20 | 206 / 20 | 207 / 20 | — |
| docs.python.org/3.3/distutils/index.html | 869 / 0 | 871 / 0 | 871 / 0 | — | 893 / 22 | 892 / 22 | 893 / 22 | — |
| docs.python.org/3.3/download.html | 339 / 0 | 344 / 0 | 344 / 0 | — | 361 / 20 | 360 / 20 | 361 / 20 | — |
| docs.python.org/3.3/extending/index.html | 536 / 0 | 541 / 0 | 541 / 0 | — | 563 / 25 | 562 / 25 | 563 / 25 | — |
| docs.python.org/3.3/faq/index.html | 187 / 0 | 192 / 0 | 192 / 0 | — | 212 / 23 | 211 / 23 | 212 / 23 | — |
| docs.python.org/3.3/genindex.html | 211 / 0 | 216 / 0 | 216 / 0 | — | 233 / 20 | 232 / 20 | 233 / 20 | — |
| docs.python.org/3.3/glossary.html | 5691 / 0 | 5615 / 0 | 5615 / 0 | — | 5717 / 20 | 5712 / 20 | 5717 / 20 | — |
| docs.python.org/3.3/howto/index.html | 269 / 0 | 274 / 0 | 274 / 0 | — | 292 / 21 | 291 / 21 | 292 / 21 | — |
| docs.python.org/3.3/install/index.html | 6882 / 0 | 6931 / 0 | 6931 / 0 | — | 6906 / 22 | 6905 / 22 | 6906 / 22 | — |
| docs.python.org/3.3/library/index.html | 2526 / 0 | 2531 / 0 | 2531 / 0 | — | 2551 / 23 | 2550 / 23 | 2551 / 23 | — |
| docs.python.org/3.3/license.html | 6426 / 0 | 6431 / 0 | 6431 / 0 | — | 6450 / 22 | 6449 / 22 | 6450 / 22 | — |
| docs.python.org/3.3/py-modindex.html | 3876 / 0 | 3897 / 0 | 3897 / 0 | — | 3903 / 25 | 3902 / 25 | 3903 / 25 | — |
| docs.python.org/3.3/reference/index.html | 539 / 0 | 544 / 0 | 544 / 0 | — | 564 / 23 | 563 / 23 | 564 / 23 | — |
| docs.python.org/3.3/search.html | 118 / 0 | 123 / 0 | 123 / 0 | — | 144 / 24 | 143 / 24 | 144 / 24 | — |
| docs.python.org/3.3/tutorial/index.html | 1040 / 0 | 1045 / 0 | 1045 / 0 | — | 1064 / 22 | 1063 / 22 | 1064 / 22 | — |
| docs.python.org/3.3/using/index.html | 468 / 0 | 473 / 0 | 473 / 0 | — | 493 / 23 | 492 / 23 | 493 / 23 | — |
| docs.python.org/3.3/whatsnew/3.3.html | 14125 / 0 | 14113 / 0 | 14113 / 0 | — | 14166 / 24 | 14150 / 24 | 14166 / 24 | — |
| docs.python.org/3.3/whatsnew/index.html | 1424 / 0 | 1430 / 0 | 1430 / 0 | — | 1449 / 23 | 1448 / 23 | 1449 / 23 | — |
| docs.python.org/3.4 | 339 / 27 | 336 / 28 | 336 / 28 | — | 361 / 47 | 360 / 47 | 361 / 47 | — |
| docs.python.org/3.5 | 186 / 0 | 371 / 28 | 371 / 28 | — | 353 / 29 | 324 / 29 | 353 / 29 | — |
| docs.python.org/3.5/about.html | 180 / 0 | 397 / 28 | 397 / 28 | — | 374 / 34 | 345 / 34 | 374 / 34 | — |
| docs.python.org/3.5/bugs.html | 631 / 0 | 856 / 28 | 856 / 28 | — | 835 / 34 | 806 / 34 | 835 / 34 | — |
| docs.python.org/3.5/c-api/index.html | 323 / 0 | 535 / 28 | 535 / 28 | — | 513 / 35 | 484 / 35 | 513 / 35 | — |
| docs.python.org/3.5/contents.html | 16248 / 0 | 16441 / 28 | 16441 / 28 | — | 16417 / 34 | 16388 / 34 | 16417 / 34 | — |
| docs.python.org/3.5/copyright.html | 58 / 0 | 269 / 28 | 269 / 28 | — | 242 / 32 | 213 / 32 | 242 / 32 | — |
| docs.python.org/3.5/distributing/index.html | 986 / 0 | 1236 / 28 | 1236 / 28 | — | 1219 / 34 | 1190 / 34 | 1219 / 34 | — |
| docs.python.org/3.5/download.html | 255 / 0 | 413 / 28 | 413 / 28 | — | 389 / 32 | 360 / 32 | 389 / 32 | — |
| docs.python.org/3.5/extending/index.html | 559 / 0 | 811 / 28 | 811 / 28 | — | 792 / 37 | 763 / 37 | 792 / 37 | — |
| docs.python.org/3.5/glossary.html | 6315 / 0 | 6440 / 28 | 6440 / 28 | — | 6518 / 32 | 6485 / 32 | 6518 / 32 | — |
| docs.python.org/3.5/howto/index.html | 124 / 0 | 345 / 28 | 345 / 28 | — | 321 / 33 | 292 / 33 | 321 / 33 | — |
| docs.python.org/3.5/installing/index.html | 1203 / 0 | 1479 / 28 | 1479 / 28 | — | 1459 / 34 | 1430 / 34 | 1459 / 34 | — |
| docs.python.org/3.5/library/index.html | 2476 / 0 | 2685 / 28 | 2685 / 28 | — | 2663 / 35 | 2634 / 35 | 2663 / 35 | — |
| docs.python.org/3.5/license.html | 6671 / 0 | 6993 / 28 | 6993 / 28 | — | 6970 / 34 | 6941 / 34 | 6970 / 34 | — |
| docs.python.org/3.5/py-modindex.html | 3924 / 0 | 4099 / 28 | 4099 / 28 | — | 4063 / 37 | 4034 / 37 | 4063 / 37 | — |
| docs.python.org/3.5/using/index.html | 351 / 0 | 563 / 28 | 563 / 28 | — | 541 / 35 | 512 / 35 | 541 / 35 | — |
| docs.python.org/3.5/whatsnew/3.5.html | 11914 / 0 | 12519 / 28 | 12519 / 28 | — | 12513 / 36 | 12460 / 36 | 12513 / 36 | — |
| docs.python.org/3.5/whatsnew/index.html | 1490 / 0 | 1706 / 28 | 1706 / 28 | — | 1683 / 35 | 1654 / 35 | 1683 / 35 | — |
| docs.python.org/3.6 | 186 / 0 | 371 / 28 | 371 / 28 | — | 353 / 29 | 324 / 29 | 353 / 29 | — |
| docs.python.org/3.6/about.html | 180 / 0 | 397 / 28 | 397 / 28 | — | 374 / 34 | 345 / 34 | 374 / 34 | — |
| docs.python.org/3.6/bugs.html | 631 / 0 | 856 / 28 | 856 / 28 | — | 835 / 34 | 806 / 34 | 835 / 34 | — |
| docs.python.org/3.6/c-api/index.html | 325 / 0 | 537 / 28 | 537 / 28 | — | 515 / 35 | 486 / 35 | 515 / 35 | — |
| docs.python.org/3.6/contents.html | 17414 / 0 | 17607 / 28 | 17607 / 28 | — | 17583 / 34 | 17554 / 34 | 17583 / 34 | — |
| docs.python.org/3.6/copyright.html | 58 / 0 | 269 / 28 | 269 / 28 | — | 242 / 32 | 213 / 32 | 242 / 32 | — |
| docs.python.org/3.6/distributing/index.html | 976 / 0 | 1228 / 28 | 1228 / 28 | — | 1209 / 34 | 1180 / 34 | 1209 / 34 | — |
| docs.python.org/3.6/download.html | 255 / 0 | 413 / 28 | 413 / 28 | — | 389 / 32 | 360 / 32 | 389 / 32 | — |
| docs.python.org/3.6/extending/index.html | 623 / 0 | 875 / 28 | 875 / 28 | — | 856 / 37 | 827 / 37 | 856 / 37 | — |
| docs.python.org/3.6/glossary.html | 7083 / 0 | 7198 / 28 | 7198 / 28 | — | 7286 / 32 | 7253 / 32 | 7286 / 32 | — |
| docs.python.org/3.6/howto/index.html | 131 / 0 | 352 / 28 | 352 / 28 | — | 328 / 33 | 299 / 33 | 328 / 33 | — |
| docs.python.org/3.6/installing/index.html | 1285 / 0 | 1567 / 28 | 1567 / 28 | — | 1545 / 34 | 1516 / 34 | 1545 / 34 | — |
| docs.python.org/3.6/library/index.html | 2487 / 0 | 2696 / 28 | 2696 / 28 | — | 2674 / 35 | 2645 / 35 | 2674 / 35 | — |
| docs.python.org/3.6/license.html | 6672 / 0 | 6994 / 28 | 6994 / 28 | — | 6971 / 34 | 6942 / 34 | 6971 / 34 | — |
| docs.python.org/3.6/py-modindex.html | 3933 / 0 | 4108 / 28 | 4108 / 28 | — | 4072 / 37 | 4043 / 37 | 4072 / 37 | — |
| docs.python.org/3.6/reference/index.html | 428 / 0 | 643 / 28 | 643 / 28 | — | 621 / 35 | 592 / 35 | 621 / 35 | — |
| docs.python.org/3.6/search.html | 51 / 0 | 205 / 28 | 205 / 28 | — | 180 / 32 | 151 / 32 | 180 / 32 | — |
| docs.python.org/3.6/tutorial/index.html | 935 / 0 | 1141 / 28 | 1141 / 28 | — | 1118 / 34 | 1089 / 34 | 1118 / 34 | — |
| docs.python.org/3.6/using/index.html | 346 / 0 | 558 / 28 | 558 / 28 | — | 536 / 35 | 507 / 35 | 536 / 35 | — |
| docs.python.org/3.6/whatsnew/3.6.html | 12686 / 0 | 13340 / 28 | 13340 / 28 | — | 13330 / 36 | 13293 / 36 | 13330 / 36 | — |
| docs.python.org/3.6/whatsnew/index.html | 1657 / 0 | 1873 / 28 | 1873 / 28 | — | 1850 / 35 | 1821 / 35 | 1850 / 35 | — |
| docs.python.org/3.7 | 186 / 0 | 371 / 28 | 371 / 28 | — | 363 / 39 | 334 / 39 | 363 / 39 | — |
| docs.python.org/3.8 | 189 / 0 | 551 / 56 | 551 / 56 | — | 484 / 39 | 400 / 12 | 484 / 39 | — |
| docs.python.org/3.9 | 190 / 0 | 580 / 63 | 580 / 63 | — | 504 / 43 | 408 / 12 | 504 / 43 | — |
| docs.python.org/3/bugs.html | — | — | — | 980 / 4 | — | 997 / 21 | — | — |
| docs.python.org/3/library | — | — | — | — | — | — | — | 2394 / 0 |
| docs.python.org/3/library/__future__.html | — | — | — | — | — | — | — | 912 / 0 |
| docs.python.org/3/library/__main__.html | — | — | — | — | — | — | — | 1979 / 0 |
| docs.python.org/3/library/_thread.html | — | — | — | — | — | — | — | 1312 / 0 |
| docs.python.org/3/library/abc.html | — | — | — | — | — | — | — | 1771 / 0 |
| docs.python.org/3/library/aifc.html | — | — | — | — | — | — | — | 292 / 0 |
| docs.python.org/3/library/allos.html | — | — | — | — | — | — | — | 775 / 0 |
| docs.python.org/3/library/annotationlib.html | — | — | — | — | — | — | — | 4093 / 0 |
| docs.python.org/3/library/archiving.html | — | — | — | — | — | — | — | 487 / 0 |
| docs.python.org/3/library/argparse.html | — | — | — | — | — | — | — | 11203 / 0 |
| docs.python.org/3/library/array.html | — | — | — | — | — | — | — | 1716 / 0 |
| docs.python.org/3/library/ast.html | — | — | — | — | — | — | — | 10362 / 0 |
| docs.python.org/3/library/asynchat.html | — | — | — | — | — | — | — | 311 / 0 |
| docs.python.org/3/library/asyncio-api-index.html | — | — | — | — | — | — | — | 911 / 0 |
| docs.python.org/3/library/asyncio-dev.html | — | — | — | — | — | — | — | 2081 / 0 |
| docs.python.org/3/library/asyncio-eventloop.html | — | — | — | — | — | — | — | 9323 / 0 |
| docs.python.org/3/library/asyncio-exceptions.html | — | — | — | — | — | — | — | 468 / 0 |
| docs.python.org/3/library/asyncio-extending.html | — | — | — | — | — | — | — | 636 / 0 |
| docs.python.org/3/library/asyncio-future.html | — | — | — | — | — | — | — | 1379 / 0 |
| docs.python.org/3/library/asyncio-graph.html | — | — | — | — | — | — | — | 880 / 0 |
| docs.python.org/3/library/asyncio-llapi-index.html | — | — | — | — | — | — | — | 1914 / 0 |
| docs.python.org/3/library/asyncio-platforms.html | — | — | — | — | — | — | — | 573 / 0 |
| docs.python.org/3/library/asyncio-policy.html | — | — | — | — | — | — | — | 824 / 0 |
| docs.python.org/3/library/asyncio-protocol.html | — | — | — | — | — | — | — | 4244 / 0 |
| docs.python.org/3/library/asyncio-queue.html | — | — | — | — | — | — | — | 1292 / 0 |
| docs.python.org/3/library/asyncio-runner.html | — | — | — | — | — | — | — | 1071 / 0 |
| docs.python.org/3/library/asyncio-stream.html | — | — | — | — | — | — | — | 2264 / 0 |
| docs.python.org/3/library/asyncio-subprocess.html | — | — | — | — | — | — | — | 1651 / 0 |
| docs.python.org/3/library/asyncio-sync.html | — | — | — | — | — | — | — | 2032 / 0 |
| docs.python.org/3/library/asyncio-task.html | — | — | — | — | — | — | — | 6789 / 0 |
| docs.python.org/3/library/asyncio.html | — | — | — | — | — | — | — | 572 / 0 |
| docs.python.org/3/library/asyncore.html | — | — | — | — | — | — | — | 302 / 0 |
| docs.python.org/3/library/atexit.html | — | — | — | — | — | — | — | 872 / 0 |
| docs.python.org/3/library/audioop.html | — | — | — | — | — | — | — | 292 / 0 |
| docs.python.org/3/library/audit_events.html | — | — | — | — | — | — | — | 1847 / 0 |
| docs.python.org/3/library/base64.html | — | — | — | — | — | — | — | 2052 / 0 |
| docs.python.org/3/library/bdb.html | — | — | — | — | — | — | — | 2604 / 0 |
| docs.python.org/3/library/binary.html | — | — | — | — | — | — | — | 463 / 0 |
| docs.python.org/3/library/binascii.html | — | — | — | — | — | — | — | 1221 / 0 |
| docs.python.org/3/library/bisect.html | — | — | — | — | — | — | — | 1617 / 0 |
| docs.python.org/3/library/builtins.html | — | — | — | — | — | — | — | 431 / 0 |
| docs.python.org/3/library/bz2.html | — | — | — | — | — | — | — | 2097 / 0 |
| docs.python.org/3/library/calendar.html | — | — | — | — | — | — | — | 3889 / 0 |
| docs.python.org/3/library/cgi.html | — | — | — | — | — | — | — | 329 / 0 |
| docs.python.org/3/library/cgitb.html | — | — | — | — | — | — | — | 330 / 0 |
| docs.python.org/3/library/chunk.html | — | — | — | — | — | — | — | 301 / 0 |
| docs.python.org/3/library/cmath.html | — | — | — | — | — | — | — | 2209 / 0 |
| docs.python.org/3/library/cmd.html | — | — | — | — | — | — | — | 2237 / 0 |
| docs.python.org/3/library/cmdline.html | — | — | — | — | — | — | — | 444 / 0 |
| docs.python.org/3/library/cmdlinelibs.html | — | — | — | — | — | — | — | 334 / 0 |
| docs.python.org/3/library/code.html | — | — | — | — | — | — | — | 1407 / 0 |
| docs.python.org/3/library/codecs.html | — | — | — | — | — | — | — | 8946 / 0 |
| docs.python.org/3/library/codeop.html | — | — | — | — | — | — | — | 670 / 0 |
| docs.python.org/3/library/collections.abc.html | — | — | — | — | — | — | — | 2442 / 0 |
| docs.python.org/3/library/collections.html | — | — | — | — | — | — | — | 7302 / 0 |
| docs.python.org/3/library/colorsys.html | — | — | — | — | — | — | — | 457 / 0 |
| docs.python.org/3/library/compileall.html | — | — | — | — | — | — | — | 2258 / 0 |
| docs.python.org/3/library/compression.html | — | — | — | — | — | — | — | 377 / 0 |
| docs.python.org/3/library/compression.zstd.html | — | — | — | — | — | — | — | 5047 / 0 |
| docs.python.org/3/library/concurrency.html | — | — | — | — | — | — | — | 679 / 0 |
| docs.python.org/3/library/concurrent.futures.html | — | — | — | — | — | — | — | 4248 / 0 |
| docs.python.org/3/library/concurrent.html | — | — | — | — | — | — | — | 275 / 0 |
| docs.python.org/3/library/concurrent.interpreters.html | — | — | — | — | — | — | — | 1945 / 0 |
| docs.python.org/3/library/configparser.html | — | — | — | — | — | — | — | 7144 / 0 |
| docs.python.org/3/library/constants.html | — | — | — | — | — | — | — | 849 / 0 |
| docs.python.org/3/library/contextlib.html | — | — | — | — | — | — | — | 4996 / 0 |
| docs.python.org/3/library/contextvars.html | — | — | — | — | — | — | — | 1676 / 0 |
| docs.python.org/3/library/copy.html | — | — | — | — | — | — | — | 878 / 0 |
| docs.python.org/3/library/copyreg.html | — | — | — | — | — | — | — | 516 / 0 |
| docs.python.org/3/library/crypt.html | — | — | — | — | — | — | — | 344 / 0 |
| docs.python.org/3/library/crypto.html | — | — | — | — | — | — | — | 356 / 0 |
| docs.python.org/3/library/csv.html | — | — | — | — | — | — | — | 3499 / 0 |
| docs.python.org/3/library/ctypes.html | — | — | — | — | — | — | — | 15868 / 0 |
| docs.python.org/3/library/curses.ascii.html | — | — | — | — | — | — | — | 1238 / 0 |
| docs.python.org/3/library/curses.html | — | — | — | — | — | — | — | 10727 / 0 |
| docs.python.org/3/library/curses.panel.html | — | — | — | — | — | — | — | 677 / 0 |
| docs.python.org/3/library/custominterp.html | — | — | — | — | — | — | — | 315 / 0 |
| docs.python.org/3/library/dataclasses.html | — | — | — | — | — | — | — | 4930 / 0 |
| docs.python.org/3/library/datatypes.html | — | — | — | — | — | — | — | 688 / 0 |
| docs.python.org/3/library/datetime.html | — | — | — | — | — | — | — | 15139 / 0 |
| docs.python.org/3/library/dbm.html | — | — | — | — | — | — | — | 2563 / 0 |
| docs.python.org/3/library/debug.html | — | — | — | — | — | — | — | 484 / 0 |
| docs.python.org/3/library/decimal.html | — | — | — | — | — | — | — | 11401 / 0 |
| docs.python.org/3/library/development.html | — | — | — | — | — | — | — | 979 / 0 |
| docs.python.org/3/library/devmode.html | — | — | — | — | — | — | — | 1242 / 0 |
| docs.python.org/3/library/dialog.html | — | — | — | — | — | — | — | 1087 / 0 |
| docs.python.org/3/library/difflib.html | — | — | — | — | — | — | — | 4984 / 0 |
| docs.python.org/3/library/dis.html | — | — | — | — | — | — | — | 8612 / 0 |
| docs.python.org/3/library/distribution.html | — | — | — | — | — | — | — | 341 / 0 |
| docs.python.org/3/library/distutils.html | — | — | — | — | — | — | — | 312 / 0 |
| docs.python.org/3/library/doctest.html | — | — | — | — | — | — | — | 10845 / 0 |
| docs.python.org/3/library/email.charset.html | — | — | — | — | — | — | — | 1338 / 0 |
| docs.python.org/3/library/email.compat32-message.html | — | — | — | — | — | — | — | 4628 / 0 |
| docs.python.org/3/library/email.contentmanager.html | — | — | — | — | — | — | — | 1424 / 0 |
| docs.python.org/3/library/email.encoders.html | — | — | — | — | — | — | — | 616 / 0 |
| docs.python.org/3/library/email.errors.html | — | — | — | — | — | — | — | 980 / 0 |
| docs.python.org/3/library/email.examples.html | — | — | — | — | — | — | — | 1837 / 0 |
| docs.python.org/3/library/email.generator.html | — | — | — | — | — | — | — | 2024 / 0 |
| docs.python.org/3/library/email.header.html | — | — | — | — | — | — | — | 1651 / 0 |
| docs.python.org/3/library/email.headerregistry.html | — | — | — | — | — | — | — | 2829 / 0 |
| docs.python.org/3/library/email.html | — | — | — | — | — | — | — | 1328 / 0 |
| docs.python.org/3/library/email.iterators.html | — | — | — | — | — | — | — | 528 / 0 |
| docs.python.org/3/library/email.message.html | — | — | — | — | — | — | — | 4579 / 0 |
| docs.python.org/3/library/email.mime.html | — | — | — | — | — | — | — | 1661 / 0 |
| docs.python.org/3/library/email.parser.html | — | — | — | — | — | — | — | 2196 / 0 |
| docs.python.org/3/library/email.policy.html | — | — | — | — | — | — | — | 4165 / 0 |
| docs.python.org/3/library/email.utils.html | — | — | — | — | — | — | — | 1590 / 0 |
| docs.python.org/3/library/ensurepip.html | — | — | — | — | — | — | — | 993 / 0 |
| docs.python.org/3/library/enum.html | — | — | — | — | — | — | — | 5123 / 0 |
| docs.python.org/3/library/errno.html | — | — | — | — | — | — | — | 2005 / 0 |
| docs.python.org/3/library/exceptions.html | — | — | — | — | — | — | — | 6007 / 0 |
| docs.python.org/3/library/faulthandler.html | — | — | — | — | — | — | — | 1651 / 0 |
| docs.python.org/3/library/fcntl.html | — | — | — | — | — | — | — | 1860 / 0 |
| docs.python.org/3/library/filecmp.html | — | — | — | — | — | — | — | 1114 / 0 |
| docs.python.org/3/library/fileformats.html | — | — | — | — | — | — | — | 354 / 0 |
| docs.python.org/3/library/fileinput.html | — | — | — | — | — | — | — | 1586 / 0 |
| docs.python.org/3/library/filesys.html | — | — | — | — | — | — | — | 529 / 0 |
| docs.python.org/3/library/fnmatch.html | — | — | — | — | — | — | — | 758 / 0 |
| docs.python.org/3/library/fractions.html | — | — | — | — | — | — | — | 1387 / 0 |
| docs.python.org/3/library/ftplib.html | — | — | — | — | — | — | — | 3285 / 0 |
| docs.python.org/3/library/functional.html | — | — | — | — | — | — | — | 300 / 0 |
| docs.python.org/3/library/functions.html | — | — | — | — | — | — | — | 13267 / 0 |
| docs.python.org/3/library/functools.html | — | — | — | — | — | — | — | 4211 / 0 |
| docs.python.org/3/library/gc.html | — | — | — | — | — | — | — | 1987 / 0 |
| docs.python.org/3/library/getopt.html | — | — | — | — | — | — | — | 1504 / 0 |
| docs.python.org/3/library/getpass.html | — | — | — | — | — | — | — | 619 / 0 |
| docs.python.org/3/library/gettext.html | — | — | — | — | — | — | — | 3650 / 0 |
| docs.python.org/3/library/glob.html | — | — | — | — | — | — | — | 1190 / 0 |
| docs.python.org/3/library/graphlib.html | — | — | — | — | — | — | — | 1461 / 0 |
| docs.python.org/3/library/grp.html | — | — | — | — | — | — | — | 537 / 0 |
| docs.python.org/3/library/gzip.html | — | — | — | — | — | — | — | 1888 / 0 |
| docs.python.org/3/library/hashlib.html | — | — | — | — | — | — | — | 4253 / 0 |
| docs.python.org/3/library/heapq.html | — | — | — | — | — | — | — | 2756 / 0 |
| docs.python.org/3/library/hmac.html | — | — | — | — | — | — | — | 980 / 0 |
| docs.python.org/3/library/html.entities.html | — | — | — | — | — | — | — | 390 / 0 |
| docs.python.org/3/library/html.html | — | — | — | — | — | — | — | 439 / 0 |
| docs.python.org/3/library/html.parser.html | — | — | — | — | — | — | — | 1760 / 0 |
| docs.python.org/3/library/i18n.html | — | — | — | — | — | — | — | 347 / 0 |
| docs.python.org/3/library/idle.html | — | — | — | — | — | — | — | 6890 / 0 |
| docs.python.org/3/library/imaplib.html | — | — | — | — | — | — | — | 3648 / 0 |
| docs.python.org/3/library/imghdr.html | — | — | — | — | — | — | — | 329 / 0 |
| docs.python.org/3/library/imp.html | — | — | — | — | — | — | — | 310 / 0 |
| docs.python.org/3/library/importlib.html | — | — | — | — | — | — | — | 7805 / 0 |
| docs.python.org/3/library/importlib.metadata.html | — | — | — | — | — | — | — | 2820 / 0 |
| docs.python.org/3/library/importlib.resources.abc.html | — | — | — | — | — | — | — | 1067 / 0 |
| docs.python.org/3/library/importlib.resources.html | — | — | — | — | — | — | — | 1486 / 0 |
| docs.python.org/3/library/inspect.html | — | — | — | — | — | — | — | 8427 / 0 |
| docs.python.org/3/library/internet.html | — | — | — | — | — | — | — | 811 / 0 |
| docs.python.org/3/library/intro.html | — | — | — | — | — | — | — | 1512 / 0 |
| docs.python.org/3/library/io.html | — | — | — | — | — | — | — | 7118 / 0 |
| docs.python.org/3/library/ipaddress.html | — | — | — | — | — | — | — | 5187 / 0 |
| docs.python.org/3/library/ipc.html | — | — | — | — | — | — | — | 336 / 0 |
| docs.python.org/3/library/itertools.html | — | — | — | — | — | — | — | 5819 / 0 |
| docs.python.org/3/library/json.html | — | — | — | — | — | — | — | 4288 / 0 |
| docs.python.org/3/library/keyword.html | — | — | — | — | — | — | — | 393 / 0 |
| docs.python.org/3/library/language.html | — | — | — | — | — | — | — | 449 / 0 |
| docs.python.org/3/library/linecache.html | — | — | — | — | — | — | — | 624 / 0 |
| docs.python.org/3/library/locale.html | — | — | — | — | — | — | — | 4046 / 0 |
| docs.python.org/3/library/logging.config.html | — | — | — | — | — | — | — | 5867 / 0 |
| docs.python.org/3/library/logging.handlers.html | — | — | — | — | — | — | — | 7330 / 0 |
| docs.python.org/3/library/logging.html | — | — | — | — | — | — | — | 9825 / 0 |
| docs.python.org/3/library/lzma.html | — | — | — | — | — | — | — | 2718 / 0 |
| docs.python.org/3/library/mailbox.html | — | — | — | — | — | — | — | 8759 / 0 |
| docs.python.org/3/library/mailcap.html | — | — | — | — | — | — | — | 298 / 0 |
| docs.python.org/3/library/markup.html | — | — | — | — | — | — | — | 581 / 0 |
| docs.python.org/3/library/marshal.html | — | — | — | — | — | — | — | 1225 / 0 |
| docs.python.org/3/library/math.html | — | — | — | — | — | — | — | 4631 / 0 |
| docs.python.org/3/library/mimetypes.html | — | — | — | — | — | — | — | 2291 / 0 |
| docs.python.org/3/library/mm.html | — | — | — | — | — | — | — | 273 / 0 |
| docs.python.org/3/library/mmap.html | — | — | — | — | — | — | — | 2585 / 0 |
| docs.python.org/3/library/modulefinder.html | — | — | — | — | — | — | — | 629 / 0 |
| docs.python.org/3/library/modules.html | — | — | — | — | — | — | — | 440 / 0 |
| docs.python.org/3/library/msilib.html | — | — | — | — | — | — | — | 304 / 0 |
| docs.python.org/3/library/msvcrt.html | — | — | — | — | — | — | — | 1400 / 0 |
| docs.python.org/3/library/multiprocessing.html | — | — | — | — | — | — | — | 18264 / 0 |
| docs.python.org/3/library/multiprocessing.shared_memory | — | — | — | — | — | — | — | 2624 / 0 |
| docs.python.org/3/library/netdata.html | — | — | — | — | — | — | — | 495 / 0 |
| docs.python.org/3/library/netrc.html | — | — | — | — | — | — | — | 736 / 0 |
| docs.python.org/3/library/nis.html | — | — | — | — | — | — | — | 304 / 0 |
| docs.python.org/3/library/nntplib.html | — | — | — | — | — | — | — | 301 / 0 |
| docs.python.org/3/library/numbers.html | — | — | — | — | — | — | — | 1275 / 0 |
| docs.python.org/3/library/numeric.html | — | — | — | — | — | — | — | 572 / 0 |
| docs.python.org/3/library/operator.html | — | — | — | — | — | — | — | 2663 / 0 |
| docs.python.org/3/library/optparse.html | — | — | — | — | — | — | — | 11471 / 0 |
| docs.python.org/3/library/os.html | — | — | — | — | — | — | — | 29776 / 0 |
| docs.python.org/3/library/os.path.html | — | — | — | — | — | — | — | 3477 / 0 |
| docs.python.org/3/library/ossaudiodev.html | — | — | — | — | — | — | — | 295 / 0 |
| docs.python.org/3/library/pathlib.html | — | — | — | — | — | — | — | 8859 / 0 |
| docs.python.org/3/library/pdb.html | — | — | — | — | — | — | — | 4588 / 0 |
| docs.python.org/3/library/persistence.html | — | — | — | — | — | — | — | 603 / 0 |
| docs.python.org/3/library/pickle.html | — | — | — | — | — | — | — | 7372 / 0 |
| docs.python.org/3/library/pickletools.html | — | — | — | — | — | — | — | 803 / 0 |
| docs.python.org/3/library/pipes.html | — | — | — | — | — | — | — | 302 / 0 |
| docs.python.org/3/library/pkgutil.html | — | — | — | — | — | — | — | 1581 / 0 |
| docs.python.org/3/library/platform.html | — | — | — | — | — | — | — | 2106 / 0 |
| docs.python.org/3/library/plistlib.html | — | — | — | — | — | — | — | 1094 / 0 |
| docs.python.org/3/library/poplib.html | — | — | — | — | — | — | — | 1495 / 0 |
| docs.python.org/3/library/posix.html | — | — | — | — | — | — | — | 738 / 0 |
| docs.python.org/3/library/pprint.html | — | — | — | — | — | — | — | 2093 / 0 |
| docs.python.org/3/library/profile.html | — | — | — | — | — | — | — | 4490 / 0 |
| docs.python.org/3/library/pty.html | — | — | — | — | — | — | — | 879 / 0 |
| docs.python.org/3/library/pwd.html | — | — | — | — | — | — | — | 535 / 0 |
| docs.python.org/3/library/py_compile.html | — | — | — | — | — | — | — | 1195 / 0 |
| docs.python.org/3/library/pyclbr.html | — | — | — | — | — | — | — | 914 / 0 |
| docs.python.org/3/library/pydoc.html | — | — | — | — | — | — | — | 992 / 0 |
| docs.python.org/3/library/pyexpat.html | — | — | — | — | — | — | — | 4738 / 0 |
| docs.python.org/3/library/python.html | — | — | — | — | — | — | — | 764 / 0 |
| docs.python.org/3/library/queue.html | — | — | — | — | — | — | — | 2029 / 0 |
| docs.python.org/3/library/quopri.html | — | — | — | — | — | — | — | 590 / 0 |
| docs.python.org/3/library/random.html | — | — | — | — | — | — | — | 4206 / 0 |
| docs.python.org/3/library/re.html | — | — | — | — | — | — | — | 11123 / 0 |
| docs.python.org/3/library/readline.html | — | — | — | — | — | — | — | 2056 / 0 |
| docs.python.org/3/library/removed.html | — | — | — | — | — | — | — | 439 / 0 |
| docs.python.org/3/library/reprlib.html | — | — | — | — | — | — | — | 1226 / 0 |
| docs.python.org/3/library/resource.html | — | — | — | — | — | — | — | 2058 / 0 |
| docs.python.org/3/library/rlcompleter.html | — | — | — | — | — | — | — | 581 / 0 |
| docs.python.org/3/library/runpy.html | — | — | — | — | — | — | — | 1500 / 0 |
| docs.python.org/3/library/sched.html | — | — | — | — | — | — | — | 898 / 0 |
| docs.python.org/3/library/secrets.html | — | — | — | — | — | — | — | 1084 / 0 |
| docs.python.org/3/library/security_warnings.html | — | — | — | — | — | — | — | 507 / 0 |
| docs.python.org/3/library/select.html | — | — | — | — | — | — | — | 3356 / 0 |
| docs.python.org/3/library/selectors.html | — | — | — | — | — | — | — | 1466 / 0 |
| docs.python.org/3/library/shelve.html | — | — | — | — | — | — | — | 1556 / 0 |
| docs.python.org/3/library/shlex.html | — | — | — | — | — | — | — | 2795 / 0 |
| docs.python.org/3/library/shutil.html | — | — | — | — | — | — | — | 5342 / 0 |
| docs.python.org/3/library/signal.html | — | — | — | — | — | — | — | 4310 / 0 |
| docs.python.org/3/library/site.html | — | — | — | — | — | — | — | 1806 / 0 |
| docs.python.org/3/library/smtpd.html | — | — | — | — | — | — | — | 312 / 0 |
| docs.python.org/3/library/smtplib.html | — | — | — | — | — | — | — | 3632 / 0 |
| docs.python.org/3/library/sndhdr.html | — | — | — | — | — | — | — | 317 / 0 |
| docs.python.org/3/library/socket.html | — | — | — | — | — | — | — | 12781 / 0 |
| docs.python.org/3/library/socketserver.html | — | — | — | — | — | — | — | 3649 / 0 |
| docs.python.org/3/library/spwd.html | — | — | — | — | — | — | — | 325 / 0 |
| docs.python.org/3/library/sqlite3.html | — | — | — | — | — | — | — | 11571 / 0 |
| docs.python.org/3/library/ssl.html | — | — | — | — | — | — | — | 14512 / 0 |
| docs.python.org/3/library/stat.html | — | — | — | — | — | — | — | 1976 / 0 |
| docs.python.org/3/library/statistics.html | — | — | — | — | — | — | — | 6180 / 0 |
| docs.python.org/3/library/stdtypes.html | — | — | — | — | — | — | — | 31227 / 0 |
| docs.python.org/3/library/string.html | — | — | — | — | — | — | — | 5725 / 0 |
| docs.python.org/3/library/string.templatelib.html | — | — | — | — | — | — | — | 1768 / 0 |
| docs.python.org/3/library/stringprep.html | — | — | — | — | — | — | — | 794 / 0 |
| docs.python.org/3/library/struct.html | — | — | — | — | — | — | — | 3680 / 0 |
| docs.python.org/3/library/subprocess.html | — | — | — | — | — | — | — | 8821 / 0 |
| docs.python.org/3/library/sunau.html | — | — | — | — | — | — | — | 295 / 0 |
| docs.python.org/3/library/superseded.html | — | — | — | — | — | — | — | 398 / 0 |
| docs.python.org/3/library/symtable.html | — | — | — | — | — | — | — | 1648 / 0 |
| docs.python.org/3/library/sys.html | — | — | — | — | — | — | — | 12257 / 0 |
| docs.python.org/3/library/sys.monitoring.html | — | — | — | — | — | — | — | 2237 / 0 |
| docs.python.org/3/library/sys_path_init.html | — | — | — | — | — | — | — | 1191 / 0 |
| docs.python.org/3/library/sysconfig.html | — | — | — | — | — | — | — | 2337 / 0 |
| docs.python.org/3/library/syslog.html | — | — | — | — | — | — | — | 1227 / 0 |
| docs.python.org/3/library/tabnanny.html | — | — | — | — | — | — | — | 485 / 0 |
| docs.python.org/3/library/tarfile.html | — | — | — | — | — | — | — | 7535 / 0 |
| docs.python.org/3/library/telnetlib.html | — | — | — | — | — | — | — | 320 / 0 |
| docs.python.org/3/library/tempfile.html | — | — | — | — | — | — | — | 3089 / 0 |
| docs.python.org/3/library/termios.html | — | — | — | — | — | — | — | 842 / 0 |
| docs.python.org/3/library/test.html | — | — | — | — | — | — | — | 8442 / 0 |
| docs.python.org/3/library/text.html | — | — | — | — | — | — | — | 465 / 0 |
| docs.python.org/3/library/textwrap.html | — | — | — | — | — | — | — | 1749 / 0 |
| docs.python.org/3/library/threading.html | — | — | — | — | — | — | — | 7930 / 0 |
| docs.python.org/3/library/threadsafety.html | — | — | — | — | — | — | — | 3067 / 0 |
| docs.python.org/3/library/time.html | — | — | — | — | — | — | — | 5434 / 0 |
| docs.python.org/3/library/timeit.html | — | — | — | — | — | — | — | 2170 / 0 |
| docs.python.org/3/library/tk.html | — | — | — | — | — | — | — | 1017 / 0 |
| docs.python.org/3/library/tkinter.colorchooser.html | — | — | — | — | — | — | — | 341 / 0 |
| docs.python.org/3/library/tkinter.dnd.html | — | — | — | — | — | — | — | 533 / 0 |
| docs.python.org/3/library/tkinter.font.html | — | — | — | — | — | — | — | 684 / 0 |
| docs.python.org/3/library/tkinter.html | — | — | — | — | — | — | — | 6426 / 0 |
| docs.python.org/3/library/tkinter.messagebox.html | — | — | — | — | — | — | — | 1064 / 0 |
| docs.python.org/3/library/tkinter.scrolledtext.html | — | — | — | — | — | — | — | 381 / 0 |
| docs.python.org/3/library/tkinter.ttk.html | — | — | — | — | — | — | — | 6688 / 0 |
| docs.python.org/3/library/token.html | — | — | — | — | — | — | — | 1801 / 0 |
| docs.python.org/3/library/tokenize.html | — | — | — | — | — | — | — | 1643 / 0 |
| docs.python.org/3/library/tomllib.html | — | — | — | — | — | — | — | 792 / 0 |
| docs.python.org/3/library/trace.html | — | — | — | — | — | — | — | 1256 / 0 |
| docs.python.org/3/library/traceback.html | — | — | — | — | — | — | — | 3818 / 0 |
| docs.python.org/3/library/tracemalloc.html | — | — | — | — | — | — | — | 3657 / 0 |
| docs.python.org/3/library/tty.html | — | — | — | — | — | — | — | 605 / 0 |
| docs.python.org/3/library/turtle.html | — | — | — | — | — | — | — | 10964 / 0 |
| docs.python.org/3/library/types.html | — | — | — | — | — | — | — | 2466 / 0 |
| docs.python.org/3/library/typing.html | — | — | — | — | — | — | — | 19075 / 0 |
| docs.python.org/3/library/unicodedata.html | — | — | — | — | — | — | — | 1172 / 0 |
| docs.python.org/3/library/unittest.html | — | — | — | — | — | — | — | 13372 / 0 |
| docs.python.org/3/library/unittest.mock-examples.html | — | — | — | — | — | — | — | 6905 / 0 |
| docs.python.org/3/library/unittest.mock.html | — | — | — | — | — | — | — | 14261 / 0 |
| docs.python.org/3/library/unix.html | — | — | — | — | — | — | — | 352 / 0 |
| docs.python.org/3/library/urllib.error.html | — | — | — | — | — | — | — | 568 / 0 |
| docs.python.org/3/library/urllib.html | — | — | — | — | — | — | — | 333 / 0 |
| docs.python.org/3/library/urllib.parse.html | — | — | — | — | — | — | — | 4407 / 0 |
| docs.python.org/3/library/urllib.request.html | — | — | — | — | — | — | — | 8074 / 0 |
| docs.python.org/3/library/urllib.robotparser.html | — | — | — | — | — | — | — | 611 / 0 |
| docs.python.org/3/library/uu.html | — | — | — | — | — | — | — | 295 / 0 |
| docs.python.org/3/library/uuid.html | — | — | — | — | — | — | — | 2449 / 0 |
| docs.python.org/3/library/venv.html | — | — | — | — | — | — | — | 3779 / 0 |
| docs.python.org/3/library/warnings.html | — | — | — | — | — | — | — | 4247 / 0 |
| docs.python.org/3/library/wave.html | — | — | — | — | — | — | — | 1347 / 0 |
| docs.python.org/3/library/weakref.html | — | — | — | — | — | — | — | 3421 / 0 |
| docs.python.org/3/library/webbrowser.html | — | — | — | — | — | — | — | 1566 / 0 |
| docs.python.org/3/library/windows.html | — | — | — | — | — | — | — | 301 / 0 |
| docs.python.org/3/library/winreg.html | — | — | — | — | — | — | — | 3755 / 0 |
| docs.python.org/3/library/winsound.html | — | — | — | — | — | — | — | 977 / 0 |
| docs.python.org/3/library/wsgiref.html | — | — | — | — | — | — | — | 5199 / 0 |
| docs.python.org/3/library/xdrlib.html | — | — | — | — | — | — | — | 289 / 0 |
| docs.python.org/3/library/xml.dom.html | — | — | — | — | — | — | — | 5230 / 0 |
| docs.python.org/3/library/xml.dom.minidom.html | — | — | — | — | — | — | — | 1841 / 0 |
| docs.python.org/3/library/xml.dom.pulldom.html | — | — | — | — | — | — | — | 864 / 0 |
| docs.python.org/3/library/xml.etree.elementtree.html | — | — | — | — | — | — | — | 7753 / 0 |
| docs.python.org/3/library/xml.html | — | — | — | — | — | — | — | 827 / 0 |
| docs.python.org/3/library/xml.sax.handler.html | — | — | — | — | — | — | — | 2510 / 0 |
| docs.python.org/3/library/xml.sax.html | — | — | — | — | — | — | — | 1224 / 0 |
| docs.python.org/3/library/xml.sax.reader.html | — | — | — | — | — | — | — | 1859 / 0 |
| docs.python.org/3/library/xml.sax.utils.html | — | — | — | — | — | — | — | 780 / 0 |
| docs.python.org/3/library/xmlrpc.client.html | — | — | — | — | — | — | — | 2927 / 0 |
| docs.python.org/3/library/xmlrpc.html | — | — | — | — | — | — | — | 318 / 0 |
| docs.python.org/3/library/xmlrpc.server.html | — | — | — | — | — | — | — | 2252 / 0 |
| docs.python.org/3/library/zipapp.html | — | — | — | — | — | — | — | 2421 / 0 |
| docs.python.org/3/library/zipfile.html | — | — | — | — | — | — | — | 5543 / 0 |
| docs.python.org/3/library/zipimport.html | — | — | — | — | — | — | — | 1105 / 0 |
| docs.python.org/3/library/zlib.html | — | — | — | — | — | — | — | 2756 / 0 |
| docs.python.org/3/library/zoneinfo.html | — | — | — | — | — | — | — | 2485 / 0 |
| docs.python.org/3/license.html | — | — | — | 8679 / 4 | — | 8696 / 21 | — | — |
| docs.python.org/bugs.html | 650 / 0 | 1096 / 68 | 1096 / 68 | — | 1092 / 52 | — | 1092 / 52 | — |
| docs.python.org/license.html | 8155 / 0 | 8801 / 68 | 8801 / 68 | — | 8791 / 52 | — | 8791 / 52 | — |

</details>

