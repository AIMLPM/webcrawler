# Extraction Quality Comparison

<!-- style: v2, 2026-04-07 -->

markcrawl produces the cleanest crawler output tested -- 100% content signal with 4 words of preamble per page -- but trades 13% recall to get there (84% vs 97% for crawlee, colly+md, and playwright).

## What the metrics mean

Before looking at the numbers, here is what each column measures and why it matters for a RAG pipeline (Retrieval-Augmented Generation, where you split crawled text into chunks, embed them as vectors, and retrieve the best-matching chunks to answer a query).

- **Content signal** -- the percentage of a tool's output that is actual page content rather than navigation chrome (menus, footers, breadcrumbs). A tool scoring 75% means one word in four is boilerplate. Higher is better.

- **Preamble** -- the average number of words that appear *before* the first heading on each page. This is where nav chrome lives: version selectors, language pickers, sidebar menus, skip-to-content links. If a tool has preamble = 398, it is injecting nearly 400 words of navigation into the top of every page's Markdown output. Those 400 words end up in your first chunk, pulling its embedding away from the page's actual topic and toward generic nav keywords. A preamble of 4 means almost nothing precedes the real content.

- **Repeat rate** -- the fraction of sentences that appear on more than 50% of crawled pages. Real content shows up on one or two pages; nav text ("Home", "Next", the full sidebar menu) repeats on every page. A 5% repeat rate means 1 in 20 sentences in your vector index is duplicated boilerplate that will match irrelevant queries.

- **Junk/page** -- count of known boilerplate phrases detected per page (nav links, footer text, breadcrumbs, etc.), matched against a fixed pattern list.

- **Precision** -- of the sentences this tool outputs, what fraction do other tools also agree is real content? A tool with 10% precision is producing mostly text that no other tool considers real content.

- **Recall** -- of the sentences that the majority of tools agree is real content, what fraction did this tool capture? 84% recall means the tool missed 16% of agreed-upon content. 97% recall means almost nothing was dropped.

These metrics matter because nav chrome degrades RAG in two ways. First, chunks containing 200 words of nav links followed by 50 words of real content produce embeddings skewed toward nav keywords, so queries about the actual topic match less strongly. Second, the same nav sentences repeat on every page, flooding retrieval results with false positives.

## Summary table

All tools sorted by content signal (primary metric), descending. The table below covers all four test sites combined.

| Tool | Content signal | Preamble [1] | Repeat rate | Junk/page | Precision | Recall |
|---|---|---|---|---|---|---|
| **markcrawl** | **100%** | **4** | **0%** | **0.4** | **100%** | **84%** |
| firecrawl | 99% | 10 | 0% | 1.4 | 10% | 10% |
| scrapy+md | 84% | 221 ⚠ | 1% | 1.0 | 100% | 92% |
| crawlee | 81% | 275 ⚠ | 2% | 1.5 | 100% | 97% |
| colly+md | 81% | 267 ⚠ | 2% | 1.5 | 100% | 97% |
| playwright | 81% | 271 ⚠ | 2% | 1.5 | 100% | 97% |
| crawl4ai | 75% | 398 ⚠ | 2% | 0.9 | 100% | 88% |
| crawl4ai-raw | 75% | 398 ⚠ | 2% | 0.9 | 100% | 88% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 words).

## The noise vs recall trade-off

The central finding is a genuine tension between clean output and complete output.

**markcrawl is the cleanest tool by a wide margin.** Its 4-word average preamble is 69x lower than crawlee's 275 words and 99x lower than crawl4ai's 398 words. Its 0% repeat rate and 100% content signal mean that virtually every word in its output is real page content. For a RAG pipeline, this means smaller chunks, tighter embeddings, and fewer false-positive retrievals.

**That cleanliness comes at a real cost: 84% recall vs 97% for crawlee.** markcrawl's aggressive filtering removes some genuine content along with the boilerplate. Of the sentences that the majority of tools agree is real content, markcrawl misses 16%. crawlee, colly+md, and playwright capture 97% -- but they pay for it with 267-275 words of nav chrome prepended to every page and a 2% cross-page repeat rate.

**crawl4ai sits in a different spot on the curve.** It has the highest preamble (398 words) but only 88% recall -- worse than crawlee on both noise and completeness. Its preamble is dominated by fastapi-docs, where it injects 1,438 words of nav chrome per page (version selectors, language pickers, full sidebar navigation). On simpler sites like quotes-toscrape, all tools produce near-zero preamble.

**Firecrawl is an outlier for a different reason.** It appears clean on preamble (10 words) and content signal (99%), but has only 10% precision and 10% recall. It is capturing a mostly different set of content than every other tool -- not a noise problem but a coverage problem. Treat firecrawl results with caution for these test sites.

**What this means in practice:**

- If your RAG pipeline is sensitive to noise -- small chunk sizes, precision-oriented retrieval, or domains where nav keywords overlap with real queries -- markcrawl's clean output will produce better embeddings and fewer junk results, even with 13% less recall.
- If your pipeline is sensitive to missing content -- broad recall matters more than chunk purity, or you have post-processing to strip boilerplate -- crawlee or colly+md will capture more at the cost of noisier chunks.
- The [retrieval benchmark](RETRIEVAL_COMPARISON.md) shows this trade-off playing out directly: crawl4ai gets a 75% hit rate vs markcrawl's 69%, because the extra text that inflates preamble scores also contains keywords that help embeddings match queries. Retrieval mode (embedding vs hybrid vs reranked) matters more than crawler choice -- see that report for details.

---

## Per-site details

### quotes-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 179 | 0 | 1% | 0 | 2.6 | 0.0 | 100% | 100% |
| crawl4ai | 188 | 0 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| crawl4ai-raw | 188 | 0 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| scrapy+md | 188 | 0 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| crawlee | 191 | 3 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| colly+md | 191 | 3 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| playwright | 191 | 3 | 2% | 0 | 2.6 | 0.0 | 100% | 100% |
| firecrawl | 83 | 0 | 0% | 0 | 1.8 | 0.0 | 33% | 33% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

<details>
<summary>Sample output — first 40 lines of <code>quotes.toscrape.com</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# [Quotes to Scrape](/)

[Login](/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."
by J.K. Rowling
[(about)](/author/J-K-Rowling)

Tags:
[abilities](/tag/abilities/page/1/)
[choices](/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[inspirational](/tag/inspirational/page/1/)
[life](/tag/life/page/1/)
[live](/tag/live/page/1/)
[miracle](/tag/miracle/page/1/)
[miracles](/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."
by Jane Austen
[(about)](/author/Jane-Austen)

Tags:
[aliteracy](/tag/aliteracy/page/1/)
[books](/tag/books/page/1/)
```

**crawl4ai**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [change](https://quotes.toscrape.com/tag/change/page/1/) [deep-thoughts](https://quotes.toscrape.com/tag/deep-thoughts/page/1/) [thinking](https://quotes.toscrape.com/tag/thinking/page/1/) [world](https://quotes.toscrape.com/tag/world/page/1/)
"It is our choices, Harry, that show what we truly are, far more than our abilities." by J.K. Rowling [(about)](https://quotes.toscrape.com/author/J-K-Rowling)
Tags: [abilities](https://quotes.toscrape.com/tag/abilities/page/1/) [choices](https://quotes.toscrape.com/tag/choices/page/1/)
"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/) [life](https://quotes.toscrape.com/tag/life/page/1/) [live](https://quotes.toscrape.com/tag/live/page/1/) [miracle](https://quotes.toscrape.com/tag/miracle/page/1/) [miracles](https://quotes.toscrape.com/tag/miracles/page/1/)
"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid." by Jane Austen [(about)](https://quotes.toscrape.com/author/Jane-Austen)
Tags: [aliteracy](https://quotes.toscrape.com/tag/aliteracy/page/1/) [books](https://quotes.toscrape.com/tag/books/page/1/) [classic](https://quotes.toscrape.com/tag/classic/page/1/) [humor](https://quotes.toscrape.com/tag/humor/page/1/)
"Imperfection is beauty, madness is genius and it's better to be absolutely ridiculous than absolutely boring." by Marilyn Monroe [(about)](https://quotes.toscrape.com/author/Marilyn-Monroe)
Tags: [be-yourself](https://quotes.toscrape.com/tag/be-yourself/page/1/) [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/)
"Try not to become a man of success. Rather become a man of value." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [adulthood](https://quotes.toscrape.com/tag/adulthood/page/1/) [success](https://quotes.toscrape.com/tag/success/page/1/) [value](https://quotes.toscrape.com/tag/value/page/1/)
"It is better to be hated for what you are than to be loved for what you are not." by Andre Gide [(about)](https://quotes.toscrape.com/author/Andre-Gide)
Tags: [life](https://quotes.toscrape.com/tag/life/page/1/) [love](https://quotes.toscrape.com/tag/love/page/1/)
"I have not failed. I've just found 10,000 ways that won't work." by Thomas A. Edison [(about)](https://quotes.toscrape.com/author/Thomas-A-Edison)
Tags: [edison](https://quotes.toscrape.com/tag/edison/page/1/) [failure](https://quotes.toscrape.com/tag/failure/page/1/) [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/) [paraphrased](https://quotes.toscrape.com/tag/paraphrased/page/1/)
"A woman is like a tea bag; you never know how strong it is until it's in hot water." by Eleanor Roosevelt [(about)](https://quotes.toscrape.com/author/Eleanor-Roosevelt)
Tags: [misattributed-eleanor-roosevelt](https://quotes.toscrape.com/tag/misattributed-eleanor-roosevelt/page/1/)
"A day without sunshine is like, you know, night." by Steve Martin [(about)](https://quotes.toscrape.com/author/Steve-Martin)
Tags: [humor](https://quotes.toscrape.com/tag/humor/page/1/) [obvious](https://quotes.toscrape.com/tag/obvious/page/1/) [simile](https://quotes.toscrape.com/tag/simile/page/1/)
  * [Next →](https://quotes.toscrape.com/page/2/)


## Top Ten tags
[love](https://quotes.toscrape.com/tag/love/) [inspirational](https://quotes.toscrape.com/tag/inspirational/) [life](https://quotes.toscrape.com/tag/life/) [humor](https://quotes.toscrape.com/tag/humor/) [books](https://quotes.toscrape.com/tag/books/) [reading](https://quotes.toscrape.com/tag/reading/) [friendship](https://quotes.toscrape.com/tag/friendship/) [friends](https://quotes.toscrape.com/tag/friends/) [truth](https://quotes.toscrape.com/tag/truth/) [simile](https://quotes.toscrape.com/tag/simile/)
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**crawl4ai-raw**
```
#  [Quotes to Scrape](https://quotes.toscrape.com/)
[Login](https://quotes.toscrape.com/login)
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [change](https://quotes.toscrape.com/tag/change/page/1/) [deep-thoughts](https://quotes.toscrape.com/tag/deep-thoughts/page/1/) [thinking](https://quotes.toscrape.com/tag/thinking/page/1/) [world](https://quotes.toscrape.com/tag/world/page/1/)
"It is our choices, Harry, that show what we truly are, far more than our abilities." by J.K. Rowling [(about)](https://quotes.toscrape.com/author/J-K-Rowling)
Tags: [abilities](https://quotes.toscrape.com/tag/abilities/page/1/) [choices](https://quotes.toscrape.com/tag/choices/page/1/)
"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/) [life](https://quotes.toscrape.com/tag/life/page/1/) [live](https://quotes.toscrape.com/tag/live/page/1/) [miracle](https://quotes.toscrape.com/tag/miracle/page/1/) [miracles](https://quotes.toscrape.com/tag/miracles/page/1/)
"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid." by Jane Austen [(about)](https://quotes.toscrape.com/author/Jane-Austen)
Tags: [aliteracy](https://quotes.toscrape.com/tag/aliteracy/page/1/) [books](https://quotes.toscrape.com/tag/books/page/1/) [classic](https://quotes.toscrape.com/tag/classic/page/1/) [humor](https://quotes.toscrape.com/tag/humor/page/1/)
"Imperfection is beauty, madness is genius and it's better to be absolutely ridiculous than absolutely boring." by Marilyn Monroe [(about)](https://quotes.toscrape.com/author/Marilyn-Monroe)
Tags: [be-yourself](https://quotes.toscrape.com/tag/be-yourself/page/1/) [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/)
"Try not to become a man of success. Rather become a man of value." by Albert Einstein [(about)](https://quotes.toscrape.com/author/Albert-Einstein)
Tags: [adulthood](https://quotes.toscrape.com/tag/adulthood/page/1/) [success](https://quotes.toscrape.com/tag/success/page/1/) [value](https://quotes.toscrape.com/tag/value/page/1/)
"It is better to be hated for what you are than to be loved for what you are not." by Andre Gide [(about)](https://quotes.toscrape.com/author/Andre-Gide)
Tags: [life](https://quotes.toscrape.com/tag/life/page/1/) [love](https://quotes.toscrape.com/tag/love/page/1/)
"I have not failed. I've just found 10,000 ways that won't work." by Thomas A. Edison [(about)](https://quotes.toscrape.com/author/Thomas-A-Edison)
Tags: [edison](https://quotes.toscrape.com/tag/edison/page/1/) [failure](https://quotes.toscrape.com/tag/failure/page/1/) [inspirational](https://quotes.toscrape.com/tag/inspirational/page/1/) [paraphrased](https://quotes.toscrape.com/tag/paraphrased/page/1/)
"A woman is like a tea bag; you never know how strong it is until it's in hot water." by Eleanor Roosevelt [(about)](https://quotes.toscrape.com/author/Eleanor-Roosevelt)
Tags: [misattributed-eleanor-roosevelt](https://quotes.toscrape.com/tag/misattributed-eleanor-roosevelt/page/1/)
"A day without sunshine is like, you know, night." by Steve Martin [(about)](https://quotes.toscrape.com/author/Steve-Martin)
Tags: [humor](https://quotes.toscrape.com/tag/humor/page/1/) [obvious](https://quotes.toscrape.com/tag/obvious/page/1/) [simile](https://quotes.toscrape.com/tag/simile/page/1/)
  * [Next →](https://quotes.toscrape.com/page/2/)


## Top Ten tags
[love](https://quotes.toscrape.com/tag/love/) [inspirational](https://quotes.toscrape.com/tag/inspirational/) [life](https://quotes.toscrape.com/tag/life/) [humor](https://quotes.toscrape.com/tag/humor/) [books](https://quotes.toscrape.com/tag/books/) [reading](https://quotes.toscrape.com/tag/reading/) [friendship](https://quotes.toscrape.com/tag/friendship/) [friends](https://quotes.toscrape.com/tag/friends/) [truth](https://quotes.toscrape.com/tag/truth/) [simile](https://quotes.toscrape.com/tag/simile/)
Quotes by: [GoodReads.com](https://www.goodreads.com/quotes)
Made with ❤ by [Zyte](https://www.zyte.com)
```

**scrapy+md**
```
# [Quotes to Scrape](/)

[Login](/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."
by J.K. Rowling
[(about)](/author/J-K-Rowling)

Tags:
[abilities](/tag/abilities/page/1/)
[choices](/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[inspirational](/tag/inspirational/page/1/)
[life](/tag/life/page/1/)
[live](/tag/live/page/1/)
[miracle](/tag/miracle/page/1/)
[miracles](/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."
by Jane Austen
[(about)](/author/Jane-Austen)

Tags:
[aliteracy](/tag/aliteracy/page/1/)
[books](/tag/books/page/1/)
```

**crawlee**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."
by J.K. Rowling
[(about)](/author/J-K-Rowling)

Tags:
[abilities](/tag/abilities/page/1/)
[choices](/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[inspirational](/tag/inspirational/page/1/)
[life](/tag/life/page/1/)
[live](/tag/live/page/1/)
[miracle](/tag/miracle/page/1/)
[miracles](/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."
by Jane Austen
[(about)](/author/Jane-Austen)
```

**colly+md**
```
  


Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."
by J.K. Rowling
[(about)](/author/J-K-Rowling)

Tags:
[abilities](/tag/abilities/page/1/)
[choices](/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[inspirational](/tag/inspirational/page/1/)
[life](/tag/life/page/1/)
[live](/tag/live/page/1/)
[miracle](/tag/miracle/page/1/)
[miracles](/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."
by Jane Austen
[(about)](/author/Jane-Austen)
```

**playwright**
```
Quotes to Scrape



# [Quotes to Scrape](/)

[Login](/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[change](/tag/change/page/1/)
[deep-thoughts](/tag/deep-thoughts/page/1/)
[thinking](/tag/thinking/page/1/)
[world](/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."
by J.K. Rowling
[(about)](/author/J-K-Rowling)

Tags:
[abilities](/tag/abilities/page/1/)
[choices](/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."
by Albert Einstein
[(about)](/author/Albert-Einstein)

Tags:
[inspirational](/tag/inspirational/page/1/)
[life](/tag/life/page/1/)
[live](/tag/live/page/1/)
[miracle](/tag/miracle/page/1/)
[miracles](/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."
by Jane Austen
[(about)](/author/Jane-Austen)
```

**firecrawl**
```
# [Quotes to Scrape](http://quotes.toscrape.com/)

[Login](http://quotes.toscrape.com/login)

"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."by Albert Einstein [(about)](http://quotes.toscrape.com/author/Albert-Einstein)

Tags:


[change](http://quotes.toscrape.com/tag/change/page/1/) [deep-thoughts](http://quotes.toscrape.com/tag/deep-thoughts/page/1/) [thinking](http://quotes.toscrape.com/tag/thinking/page/1/) [world](http://quotes.toscrape.com/tag/world/page/1/)

"It is our choices, Harry, that show what we truly are, far more than our abilities."by J.K. Rowling [(about)](http://quotes.toscrape.com/author/J-K-Rowling)

Tags:


[abilities](http://quotes.toscrape.com/tag/abilities/page/1/) [choices](http://quotes.toscrape.com/tag/choices/page/1/)

"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle."by Albert Einstein [(about)](http://quotes.toscrape.com/author/Albert-Einstein)

Tags:


[inspirational](http://quotes.toscrape.com/tag/inspirational/page/1/) [life](http://quotes.toscrape.com/tag/life/page/1/) [live](http://quotes.toscrape.com/tag/live/page/1/) [miracle](http://quotes.toscrape.com/tag/miracle/page/1/) [miracles](http://quotes.toscrape.com/tag/miracles/page/1/)

"The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid."by Jane Austen [(about)](http://quotes.toscrape.com/author/Jane-Austen)

Tags:


[aliteracy](http://quotes.toscrape.com/tag/aliteracy/page/1/) [books](http://quotes.toscrape.com/tag/books/page/1/) [classic](http://quotes.toscrape.com/tag/classic/page/1/) [humor](http://quotes.toscrape.com/tag/humor/page/1/)

"Imperfection is beauty, madness is genius and it's better to be absolutely ridiculous than absolutely boring."by Marilyn Monroe [(about)](http://quotes.toscrape.com/author/Marilyn-Monroe)

Tags:


[be-yourself](http://quotes.toscrape.com/tag/be-yourself/page/1/) [inspirational](http://quotes.toscrape.com/tag/inspirational/page/1/)

"Try not to become a man of success. Rather become a man of value."by Albert Einstein [(about)](http://quotes.toscrape.com/author/Albert-Einstein)
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| quotes.toscrape.com | 271 / 0 | 282 / 0 | 282 / 0 | 282 / 0 | 285 / 3 | 285 / 3 | 285 / 3 | 252 / 0 |
| quotes.toscrape.com/author/Albert-Einstein | — | — | — | — | — | — | — | 620 / 0 |
| quotes.toscrape.com/author/J-K-Rowling | 650 / 0 | 658 / 0 | 658 / 0 | 658 / 0 | 661 / 3 | 661 / 3 | 661 / 3 | — |
| quotes.toscrape.com/author/Jane-Austen | 333 / 0 | 341 / 0 | 341 / 0 | 341 / 0 | 344 / 3 | 344 / 3 | 344 / 3 | — |
| quotes.toscrape.com/author/Steve-Martin | 139 / 0 | 147 / 0 | 147 / 0 | 147 / 0 | 150 / 3 | 150 / 3 | 150 / 3 | — |
| quotes.toscrape.com/login | 7 / 0 | 15 / 0 | 15 / 0 | 15 / 0 | 18 / 3 | 18 / 3 | 18 / 3 | — |
| quotes.toscrape.com/page/139 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/299 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/372 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/454 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/539 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/676 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/683 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/796 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/896 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/page/933 | — | — | — | — | — | — | — | 13 / 0 |
| quotes.toscrape.com/tableful/tag/christianity/page/1 | — | — | — | — | — | — | — | 84 / 0 |
| quotes.toscrape.com/tableful/tag/fairy-tales/page/1 | — | — | — | — | — | — | — | 81 / 0 |
| quotes.toscrape.com/tableful/tag/good/page/1 | — | — | — | — | — | — | — | 72 / 0 |
| quotes.toscrape.com/tag/be-yourself/page/1 | 46 / 0 | 54 / 0 | 54 / 0 | 54 / 0 | 57 / 3 | 57 / 3 | 57 / 3 | — |
| quotes.toscrape.com/tag/change/page/1 | 53 / 0 | 61 / 0 | 61 / 0 | 61 / 0 | 64 / 3 | 64 / 3 | 64 / 3 | — |
| quotes.toscrape.com/tag/humor/page/1 | 284 / 0 | 295 / 0 | 295 / 0 | 295 / 0 | 298 / 3 | 298 / 3 | 298 / 3 | — |
| quotes.toscrape.com/tag/inspirational/page/1 | 484 / 0 | 495 / 0 | 495 / 0 | 495 / 0 | 498 / 3 | 498 / 3 | 498 / 3 | — |
| quotes.toscrape.com/tag/live/page/1 | 59 / 0 | 67 / 0 | 67 / 0 | 67 / 0 | 70 / 3 | 70 / 3 | 70 / 3 | — |
| quotes.toscrape.com/tag/miracle/page/1 | 59 / 0 | 67 / 0 | 67 / 0 | 67 / 0 | 70 / 3 | 70 / 3 | 70 / 3 | — |
| quotes.toscrape.com/tag/miracles/page/1 | 59 / 0 | 67 / 0 | 67 / 0 | 67 / 0 | 70 / 3 | 70 / 3 | 70 / 3 | — |
| quotes.toscrape.com/tag/obvious/page/1 | 40 / 0 | 48 / 0 | 48 / 0 | 48 / 0 | 51 / 3 | 51 / 3 | 51 / 3 | — |
| quotes.toscrape.com/tag/thinking/page/1 | 85 / 0 | 93 / 0 | 93 / 0 | 93 / 0 | 96 / 3 | 96 / 3 | 96 / 3 | — |
| quotes.toscrape.com/tag/truth | 117 / 0 | 125 / 0 | 125 / 0 | 125 / 0 | 128 / 3 | 128 / 3 | 128 / 3 | — |

</details>

### books-toscrape

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 298 | 8 | 0% | 0 | 1.8 | 0.0 | 100% | 99% |
| crawl4ai | 511 | 177 ⚠ | 1% | 0 | 11.4 | 0.0 | 100% | 99% |
| crawl4ai-raw | 511 | 177 ⚠ | 1% | 0 | 11.4 | 0.0 | 100% | 99% |
| scrapy+md | 400 | 101 ⚠ | 1% | 0 | 1.8 | 0.0 | 100% | 99% |
| crawlee | 408 | 109 ⚠ | 1% | 0 | 1.8 | 0.0 | 100% | 100% |
| colly+md | 408 | 109 ⚠ | 1% | 0 | 1.8 | 0.0 | 100% | 100% |
| playwright | 408 | 109 ⚠ | 1% | 0 | 1.8 | 0.0 | 100% | 100% |
| firecrawl | 513 | 18 | 0% | 0 | 9.1 | 0.0 | 2% | 3% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

<details>
<summary>Sample output — first 40 lines of <code>books.toscrape.com/catalogue/category/books_1/index.html</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
* [Home](../../../index.html)
* Books

# Books

**1000** results - showing **1** to **20**.

**Warning!** This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning.

1. ### [A Light in the ...](../../a-light-in-the-attic_1000/index.html "A Light in the Attic")

   £51.77

   In stock

   Add to basket
2. ### [Tipping the Velvet](../../tipping-the-velvet_999/index.html "Tipping the Velvet")

   £53.74

   In stock

   Add to basket
3. ### [Soumission](../../soumission_998/index.html "Soumission")

   £50.10

   In stock

   Add to basket
4. ### [Sharp Objects](../../sharp-objects_997/index.html "Sharp Objects")

   £47.82

   In stock

   Add to basket
5. ### [Sapiens: A Brief History ...](../../sapiens-a-brief-history-of-humankind_996/index.html "Sapiens: A Brief History of Humankind")

   £54.23
```

**crawl4ai**
```
[Books to Scrape](https://books.toscrape.com/index.html) We love being scraped!
  * [Home](https://books.toscrape.com/index.html)
  * Books


  * [ **Books** ](https://books.toscrape.com/catalogue/category/books_1/index.html)
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
    * [ Business ](https://books.toscrape.com/catalogue/category/books/business_35/index.html)
```

**crawl4ai-raw**
```
[Books to Scrape](https://books.toscrape.com/index.html) We love being scraped!
  * [Home](https://books.toscrape.com/index.html)
  * Books


  * [ **Books** ](https://books.toscrape.com/catalogue/category/books_1/index.html)
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
    * [ Business ](https://books.toscrape.com/catalogue/category/books/business_35/index.html)
```

**scrapy+md**
```
[Books to Scrape](../../../index.html) We love being scraped!

* [Home](../../../index.html)
* Books

* [**Books**](index.html)
  + [Travel](../books/travel_2/index.html)
  + [Mystery](../books/mystery_3/index.html)
  + [Historical Fiction](../books/historical-fiction_4/index.html)
  + [Sequential Art](../books/sequential-art_5/index.html)
  + [Classics](../books/classics_6/index.html)
  + [Philosophy](../books/philosophy_7/index.html)
  + [Romance](../books/romance_8/index.html)
  + [Womens Fiction](../books/womens-fiction_9/index.html)
  + [Fiction](../books/fiction_10/index.html)
  + [Childrens](../books/childrens_11/index.html)
  + [Religion](../books/religion_12/index.html)
  + [Nonfiction](../books/nonfiction_13/index.html)
  + [Music](../books/music_14/index.html)
  + [Default](../books/default_15/index.html)
  + [Science Fiction](../books/science-fiction_16/index.html)
  + [Sports and Games](../books/sports-and-games_17/index.html)
  + [Add a comment](../books/add-a-comment_18/index.html)
  + [Fantasy](../books/fantasy_19/index.html)
  + [New Adult](../books/new-adult_20/index.html)
  + [Young Adult](../books/young-adult_21/index.html)
  + [Science](../books/science_22/index.html)
  + [Poetry](../books/poetry_23/index.html)
  + [Paranormal](../books/paranormal_24/index.html)
  + [Art](../books/art_25/index.html)
  + [Psychology](../books/psychology_26/index.html)
  + [Autobiography](../books/autobiography_27/index.html)
  + [Parenting](../books/parenting_28/index.html)
  + [Adult Fiction](../books/adult-fiction_29/index.html)
  + [Humor](../books/humor_30/index.html)
  + [Horror](../books/horror_31/index.html)
  + [History](../books/history_32/index.html)
  + [Food and Drink](../books/food-and-drink_33/index.html)
  + [Christian Fiction](../books/christian-fiction_34/index.html)
  + [Business](../books/business_35/index.html)
```

**crawlee**
```
Books |
Books to Scrape - Sandbox




[Books to Scrape](../../../index.html) We love being scraped!

* [Home](../../../index.html)
* Books

* [**Books**](index.html)
  + [Travel](../books/travel_2/index.html)
  + [Mystery](../books/mystery_3/index.html)
  + [Historical Fiction](../books/historical-fiction_4/index.html)
  + [Sequential Art](../books/sequential-art_5/index.html)
  + [Classics](../books/classics_6/index.html)
  + [Philosophy](../books/philosophy_7/index.html)
  + [Romance](../books/romance_8/index.html)
  + [Womens Fiction](../books/womens-fiction_9/index.html)
  + [Fiction](../books/fiction_10/index.html)
  + [Childrens](../books/childrens_11/index.html)
  + [Religion](../books/religion_12/index.html)
  + [Nonfiction](../books/nonfiction_13/index.html)
  + [Music](../books/music_14/index.html)
  + [Default](../books/default_15/index.html)
  + [Science Fiction](../books/science-fiction_16/index.html)
  + [Sports and Games](../books/sports-and-games_17/index.html)
  + [Add a comment](../books/add-a-comment_18/index.html)
  + [Fantasy](../books/fantasy_19/index.html)
  + [New Adult](../books/new-adult_20/index.html)
  + [Young Adult](../books/young-adult_21/index.html)
  + [Science](../books/science_22/index.html)
  + [Poetry](../books/poetry_23/index.html)
  + [Paranormal](../books/paranormal_24/index.html)
  + [Art](../books/art_25/index.html)
  + [Psychology](../books/psychology_26/index.html)
  + [Autobiography](../books/autobiography_27/index.html)
  + [Parenting](../books/parenting_28/index.html)
  + [Adult Fiction](../books/adult-fiction_29/index.html)
```

**colly+md**
```
  


Books |
Books to Scrape - Sandbox




[Books to Scrape](../../../index.html) We love being scraped!

* [Home](../../../index.html)
* Books

* [**Books**](index.html)
  + [Travel](../books/travel_2/index.html)
  + [Mystery](../books/mystery_3/index.html)
  + [Historical Fiction](../books/historical-fiction_4/index.html)
  + [Sequential Art](../books/sequential-art_5/index.html)
  + [Classics](../books/classics_6/index.html)
  + [Philosophy](../books/philosophy_7/index.html)
  + [Romance](../books/romance_8/index.html)
  + [Womens Fiction](../books/womens-fiction_9/index.html)
  + [Fiction](../books/fiction_10/index.html)
  + [Childrens](../books/childrens_11/index.html)
  + [Religion](../books/religion_12/index.html)
  + [Nonfiction](../books/nonfiction_13/index.html)
  + [Music](../books/music_14/index.html)
  + [Default](../books/default_15/index.html)
  + [Science Fiction](../books/science-fiction_16/index.html)
  + [Sports and Games](../books/sports-and-games_17/index.html)
  + [Add a comment](../books/add-a-comment_18/index.html)
  + [Fantasy](../books/fantasy_19/index.html)
  + [New Adult](../books/new-adult_20/index.html)
  + [Young Adult](../books/young-adult_21/index.html)
  + [Science](../books/science_22/index.html)
  + [Poetry](../books/poetry_23/index.html)
  + [Paranormal](../books/paranormal_24/index.html)
  + [Art](../books/art_25/index.html)
  + [Psychology](../books/psychology_26/index.html)
```

**playwright**
```
Books |
Books to Scrape - Sandbox




[Books to Scrape](../../../index.html) We love being scraped!

* [Home](../../../index.html)
* Books

* [**Books**](index.html)
  + [Travel](../books/travel_2/index.html)
  + [Mystery](../books/mystery_3/index.html)
  + [Historical Fiction](../books/historical-fiction_4/index.html)
  + [Sequential Art](../books/sequential-art_5/index.html)
  + [Classics](../books/classics_6/index.html)
  + [Philosophy](../books/philosophy_7/index.html)
  + [Romance](../books/romance_8/index.html)
  + [Womens Fiction](../books/womens-fiction_9/index.html)
  + [Fiction](../books/fiction_10/index.html)
  + [Childrens](../books/childrens_11/index.html)
  + [Religion](../books/religion_12/index.html)
  + [Nonfiction](../books/nonfiction_13/index.html)
  + [Music](../books/music_14/index.html)
  + [Default](../books/default_15/index.html)
  + [Science Fiction](../books/science-fiction_16/index.html)
  + [Sports and Games](../books/sports-and-games_17/index.html)
  + [Add a comment](../books/add-a-comment_18/index.html)
  + [Fantasy](../books/fantasy_19/index.html)
  + [New Adult](../books/new-adult_20/index.html)
  + [Young Adult](../books/young-adult_21/index.html)
  + [Science](../books/science_22/index.html)
  + [Poetry](../books/poetry_23/index.html)
  + [Paranormal](../books/paranormal_24/index.html)
  + [Art](../books/art_25/index.html)
  + [Psychology](../books/psychology_26/index.html)
  + [Autobiography](../books/autobiography_27/index.html)
  + [Parenting](../books/parenting_28/index.html)
  + [Adult Fiction](../books/adult-fiction_29/index.html)
```

**firecrawl**
```
- [Home](http://books.toscrape.com/index.html)
- Books

# Books

**1000** results - showing **1** to **20**.




**Warning!** This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning.

01. [![A Light in the Attic](http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg)](http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html)




    ### [A Light in the ...](http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html "A Light in the Attic")




    £51.77




    In stock



    Add to basket
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| books.toscrape.com | 397 / 5 | 702 / 232 | 702 / 232 | 531 / 130 | 539 / 138 | 539 / 138 | 539 / 138 | 515 / 5 |
| books.toscrape.com/catalogue/a-light-in-the-attic_1000/ | 269 / 12 | 276 / 24 | 276 / 24 | 284 / 19 | 295 / 30 | 295 / 30 | 295 / 30 | — |
| books.toscrape.com/catalogue/category/books/academic_40 | 51 / 6 | 282 / 233 | 282 / 233 | 185 / 131 | 192 / 138 | 192 / 138 | 192 / 138 | — |
| books.toscrape.com/catalogue/category/books/art_25/inde | 169 / 6 | 422 / 233 | 422 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | — |
| books.toscrape.com/catalogue/category/books/autobiograp | 169 / 6 | 412 / 233 | 412 / 233 | 303 / 131 | 310 / 138 | 310 / 138 | 310 / 138 | — |
| books.toscrape.com/catalogue/category/books/biography_3 | 145 / 6 | 410 / 233 | 410 / 233 | 279 / 131 | 286 / 138 | 286 / 138 | 286 / 138 | — |
| books.toscrape.com/catalogue/category/books/business_35 | 296 / 6 | 612 / 233 | 612 / 233 | 430 / 131 | 437 / 138 | 437 / 138 | 437 / 138 | — |
| books.toscrape.com/catalogue/category/books/childrens_1 | 366 / 6 | 642 / 233 | 642 / 233 | 500 / 131 | 507 / 138 | 507 / 138 | 507 / 138 | — |
| books.toscrape.com/catalogue/category/books/christian-f | 140 / 7 | 388 / 234 | 388 / 234 | 274 / 132 | 282 / 140 | 282 / 140 | 282 / 140 | — |
| books.toscrape.com/catalogue/category/books/christian_4 | 96 / 6 | 342 / 233 | 342 / 233 | 230 / 131 | 237 / 138 | 237 / 138 | 237 / 138 | — |
| books.toscrape.com/catalogue/category/books/classics_6/ | 326 / 6 | 593 / 233 | 593 / 233 | 460 / 131 | 467 / 138 | 467 / 138 | 467 / 138 | — |
| books.toscrape.com/catalogue/category/books/contemporar | 84 / 6 | 320 / 233 | 320 / 233 | 218 / 131 | 225 / 138 | 225 / 138 | 225 / 138 | — |
| books.toscrape.com/catalogue/category/books/crime_51/in | 58 / 6 | 296 / 233 | 296 / 233 | 192 / 131 | 199 / 138 | 199 / 138 | 199 / 138 | — |
| books.toscrape.com/catalogue/category/books/cultural_49 | 46 / 6 | 274 / 233 | 274 / 233 | 180 / 131 | 187 / 138 | 187 / 138 | 187 / 138 | — |
| books.toscrape.com/catalogue/category/books/default_15/ | 439 / 6 | 777 / 233 | 777 / 233 | 573 / 131 | 580 / 138 | 580 / 138 | 580 / 138 | — |
| books.toscrape.com/catalogue/category/books/erotica_50/ | 44 / 6 | 271 / 233 | 271 / 233 | 178 / 131 | 185 / 138 | 185 / 138 | 185 / 138 | — |
| books.toscrape.com/catalogue/category/books/fantasy_19/ | 436 / 6 | 764 / 233 | 764 / 233 | 570 / 131 | 577 / 138 | 577 / 138 | 577 / 138 | — |
| books.toscrape.com/catalogue/category/books/food-and-dr | 548 / 8 | 978 / 235 | 978 / 235 | 682 / 133 | 691 / 142 | 691 / 142 | 691 / 142 | — |
| books.toscrape.com/catalogue/category/books/health_47/i | 124 / 6 | 384 / 233 | 384 / 233 | 258 / 131 | 265 / 138 | 265 / 138 | 265 / 138 | — |
| books.toscrape.com/catalogue/category/books/historical- | 391 / 7 | 681 / 234 | 681 / 234 | 525 / 132 | 533 / 140 | 533 / 140 | 533 / 140 | — |
| books.toscrape.com/catalogue/category/books/history_32/ | 447 / 6 | 822 / 233 | 822 / 233 | 581 / 131 | 588 / 138 | 588 / 138 | 588 / 138 | — |
| books.toscrape.com/catalogue/category/books/horror_31/i | 275 / 6 | 524 / 233 | 524 / 233 | 409 / 131 | 416 / 138 | 416 / 138 | 416 / 138 | — |
| books.toscrape.com/catalogue/category/books/humor_30/in | 239 / 6 | 529 / 233 | 529 / 233 | 373 / 131 | 380 / 138 | 380 / 138 | 380 / 138 | — |
| books.toscrape.com/catalogue/category/books/mystery_3/i | 407 / 6 | 710 / 233 | 710 / 233 | 541 / 131 | 548 / 138 | 548 / 138 | 548 / 138 | — |
| books.toscrape.com/catalogue/category/books/nonfiction_ | 501 / 6 | 887 / 233 | 887 / 233 | 635 / 131 | 642 / 138 | 642 / 138 | 642 / 138 | — |
| books.toscrape.com/catalogue/category/books/novels_46/i | 53 / 6 | 286 / 233 | 286 / 233 | 187 / 131 | 194 / 138 | 194 / 138 | 194 / 138 | — |
| books.toscrape.com/catalogue/category/books/paranormal_ | 52 / 6 | 284 / 233 | 284 / 233 | 186 / 131 | 193 / 138 | 193 / 138 | 193 / 138 | — |
| books.toscrape.com/catalogue/category/books/parenting_2 | 53 / 6 | 286 / 233 | 286 / 233 | 187 / 131 | 194 / 138 | 194 / 138 | 194 / 138 | — |
| books.toscrape.com/catalogue/category/books/philosophy_ | 236 / 6 | 516 / 233 | 516 / 233 | 370 / 131 | 377 / 138 | 377 / 138 | 377 / 138 | — |
| books.toscrape.com/catalogue/category/books/poetry_23/i | 355 / 6 | 642 / 233 | 642 / 233 | 489 / 131 | 496 / 138 | 496 / 138 | 496 / 138 | — |
| books.toscrape.com/catalogue/category/books/politics_48 | 94 / 6 | 340 / 233 | 340 / 233 | 228 / 131 | 235 / 138 | 235 / 138 | 235 / 138 | — |
| books.toscrape.com/catalogue/category/books/psychology_ | 184 / 6 | 460 / 233 | 460 / 233 | 318 / 131 | 325 / 138 | 325 / 138 | 325 / 138 | — |
| books.toscrape.com/catalogue/category/books/religion_12 | 180 / 6 | 453 / 233 | 453 / 233 | 314 / 131 | 321 / 138 | 321 / 138 | 321 / 138 | — |
| books.toscrape.com/catalogue/category/books/romance_8/i | 412 / 6 | 716 / 233 | 716 / 233 | 546 / 131 | 553 / 138 | 553 / 138 | 553 / 138 | — |
| books.toscrape.com/catalogue/category/books/science-fic | 322 / 7 | 615 / 234 | 615 / 234 | 456 / 132 | 464 / 140 | 464 / 140 | 464 / 140 | — |
| books.toscrape.com/catalogue/category/books/science_22/ | 350 / 6 | 690 / 233 | 690 / 233 | 484 / 131 | 491 / 138 | 491 / 138 | 491 / 138 | — |
| books.toscrape.com/catalogue/category/books/sequential- | 441 / 7 | 774 / 234 | 774 / 234 | 575 / 132 | 583 / 140 | 583 / 140 | 583 / 140 | — |
| books.toscrape.com/catalogue/category/books/short-stori | 46 / 7 | 273 / 234 | 273 / 234 | 180 / 132 | 188 / 140 | 188 / 140 | 188 / 140 | — |
| books.toscrape.com/catalogue/category/books/spiritualit | 171 / 6 | 447 / 233 | 447 / 233 | 305 / 131 | 312 / 138 | 312 / 138 | 312 / 138 | — |
| books.toscrape.com/catalogue/category/books/sports-and- | 137 / 8 | 391 / 235 | 391 / 235 | 271 / 133 | 280 / 142 | 280 / 142 | 280 / 142 | — |
| books.toscrape.com/catalogue/category/books/thriller_37 | 211 / 6 | 465 / 233 | 465 / 233 | 345 / 131 | 352 / 138 | 352 / 138 | 352 / 138 | — |
| books.toscrape.com/catalogue/category/books/travel_2/in | — | — | — | — | — | — | — | 345 / 6 |
| books.toscrape.com/catalogue/category/books/womens-fict | 330 / 7 | 614 / 234 | 614 / 234 | 464 / 132 | 472 / 140 | 472 / 140 | 472 / 140 | — |
| books.toscrape.com/catalogue/category/books/young-adult | 386 / 7 | 676 / 234 | 676 / 234 | 520 / 132 | 528 / 140 | 528 / 140 | 528 / 140 | — |
| books.toscrape.com/catalogue/category/books_1/index.htm | 395 / 4 | 700 / 231 | 700 / 231 | 529 / 129 | 536 / 136 | 536 / 136 | 536 / 136 | 513 / 4 |
| books.toscrape.com/catalogue/far-from-true-promise-fall | — | — | — | — | — | — | — | 516 / 21 |
| books.toscrape.com/catalogue/its-only-the-himalayas_981 | 448 / 11 | 480 / 22 | 480 / 22 | 463 / 18 | 473 / 28 | 473 / 28 | 473 / 28 | — |
| books.toscrape.com/catalogue/libertarianism-for-beginne | 411 / 10 | 442 / 20 | 442 / 20 | 426 / 17 | 435 / 26 | 435 / 26 | 435 / 26 | — |
| books.toscrape.com/catalogue/olio_984/index.html | 462 / 8 | 491 / 16 | 491 / 16 | 477 / 15 | 484 / 22 | 484 / 22 | 484 / 22 | — |
| books.toscrape.com/catalogue/page-2.html | 413 / 5 | 726 / 232 | 726 / 232 | 547 / 130 | 555 / 138 | 555 / 138 | 555 / 138 | — |
| books.toscrape.com/catalogue/rip-it-up-and-start-again_ | 371 / 13 | 407 / 26 | 407 / 26 | 386 / 20 | 398 / 32 | 398 / 32 | 398 / 32 | — |
| books.toscrape.com/catalogue/scott-pilgrims-precious-li | 383 / 16 | 428 / 31 | 428 / 31 | 398 / 23 | 412 / 37 | 412 / 37 | 412 / 37 | — |
| books.toscrape.com/catalogue/set-me-free_988/index.html | 365 / 11 | 411 / 21 | 411 / 21 | 380 / 18 | 389 / 27 | 389 / 27 | 389 / 27 | — |
| books.toscrape.com/catalogue/shakespeares-sonnets_989/i | 375 / 9 | 421 / 18 | 421 / 18 | 390 / 16 | 398 / 24 | 398 / 24 | 398 / 24 | — |
| books.toscrape.com/catalogue/sharp-objects_997/index.ht | 420 / 9 | 427 / 18 | 427 / 18 | 435 / 16 | 443 / 24 | 443 / 24 | 443 / 24 | — |
| books.toscrape.com/catalogue/soumission_998/index.html | 297 / 8 | 304 / 16 | 304 / 16 | 312 / 15 | 319 / 22 | 319 / 22 | 319 / 22 | — |
| books.toscrape.com/catalogue/starving-hearts-triangular | 436 / 13 | 486 / 26 | 486 / 26 | 451 / 20 | 463 / 32 | 463 / 32 | 463 / 32 | — |
| books.toscrape.com/catalogue/the-black-maria_991/index. | 696 / 10 | 742 / 20 | 742 / 20 | 711 / 17 | 720 / 26 | 720 / 26 | 720 / 26 | — |
| books.toscrape.com/catalogue/the-coming-woman-a-novel-b | 789 / 22 | 818 / 44 | 818 / 44 | 804 / 29 | 825 / 50 | 825 / 50 | 825 / 50 | — |
| books.toscrape.com/catalogue/the-dirty-little-secrets-o | 489 / 16 | 508 / 32 | 508 / 32 | 504 / 23 | 519 / 38 | 519 / 38 | 519 / 38 | — |
| books.toscrape.com/catalogue/the-requiem-red_995/index. | 350 / 11 | 362 / 21 | 362 / 21 | 365 / 18 | 374 / 27 | 374 / 27 | 374 / 27 | — |
| books.toscrape.com/catalogue/tipping-the-velvet_999/ind | 290 / 11 | 298 / 21 | 298 / 21 | 305 / 18 | 314 / 27 | 314 / 27 | 314 / 27 | — |
| books.toscrape.com/catalogue/a-la-mode-120-recipes-in-6 | — | — | — | — | — | — | — | 637 / 55 |
| books.toscrape.com/catalogue/a-walk-to-remember_312/ind | — | — | — | — | — | — | — | 501 / 15 |
| books.toscrape.com/catalogue/becoming-wise-an-inquiry-i | — | — | — | — | — | — | — | 819 / 29 |
| books.toscrape.com/catalogue/benjamin-franklin-an-ameri | — | — | — | — | — | — | — | 783 / 17 |
| books.toscrape.com/catalogue/beowulf_126/index.html | — | — | — | — | — | — | — | 415 / 9 |
| books.toscrape.com/catalogue/bright-lines_11/index.html | — | — | — | — | — | — | — | 474 / 11 |
| books.toscrape.com/catalogue/carry-on-warrior-thoughts- | — | — | — | — | — | — | — | 437 / 21 |
| books.toscrape.com/catalogue/category/books/historical- | — | — | — | — | — | — | — | 494 / 7 |
| books.toscrape.com/catalogue/category/books/nonfiction_ | — | — | — | — | — | — | — | 685 / 6 |
| books.toscrape.com/catalogue/category/books/sequential- | — | — | — | — | — | — | — | 611 / 7 |
| books.toscrape.com/catalogue/catherine-the-great-portra | — | — | — | — | — | — | — | 681 / 21 |
| books.toscrape.com/catalogue/counting-thyme_142/index.h | — | — | — | — | — | — | — | 503 / 11 |
| books.toscrape.com/catalogue/david-and-goliath-underdog | — | — | — | — | — | — | — | 409 / 29 |
| books.toscrape.com/catalogue/find-her-detective-dd-warr | — | — | — | — | — | — | — | 514 / 21 |
| books.toscrape.com/catalogue/foundation-foundation-publ | — | — | — | — | — | — | — | 426 / 18 |
| books.toscrape.com/catalogue/fruits-basket-vol-9-fruits | — | — | — | — | — | — | — | 321 / 22 |
| books.toscrape.com/catalogue/greek-mythic-history_698/i | — | — | — | — | — | — | — | 468 / 13 |
| books.toscrape.com/catalogue/in-her-wake_980/index.html | — | — | — | — | — | — | — | 434 / 13 |
| books.toscrape.com/catalogue/in-the-country-we-love-my- | — | — | — | — | — | — | — | 610 / 23 |
| books.toscrape.com/catalogue/jane-eyre_27/index.html | — | — | — | — | — | — | — | 400 / 11 |
| books.toscrape.com/catalogue/kill-em-and-leave-searchin | — | — | — | — | — | — | — | 840 / 31 |
| books.toscrape.com/catalogue/let-it-out-a-journey-throu | — | — | — | — | — | — | — | 655 / 21 |
| books.toscrape.com/catalogue/life-after-life_187/index. | — | — | — | — | — | — | — | 474 / 13 |
| books.toscrape.com/catalogue/life-of-pi_475/index.html | — | — | — | — | — | — | — | 338 / 13 |
| books.toscrape.com/catalogue/mexican-today-new-and-redi | — | — | — | — | — | — | — | 585 / 27 |
| books.toscrape.com/catalogue/more-than-music-chasing-th | — | — | — | — | — | — | — | 423 / 23 |
| books.toscrape.com/catalogue/neither-here-nor-there-tra | — | — | — | — | — | — | — | 492 / 21 |
| books.toscrape.com/catalogue/original-fake_203/index.ht | — | — | — | — | — | — | — | 524 / 12 |
| books.toscrape.com/catalogue/pet-sematary_726/index.htm | — | — | — | — | — | — | — | 332 / 11 |
| books.toscrape.com/catalogue/political-suicide-missteps | — | — | — | — | — | — | — | 545 / 53 |
| books.toscrape.com/catalogue/saga-volume-1-saga-collect | — | — | — | — | — | — | — | 441 / 22 |
| books.toscrape.com/catalogue/shtum_733/index.html | — | — | — | — | — | — | — | 406 / 9 |
| books.toscrape.com/catalogue/slow-states-of-collapse-po | — | — | — | — | — | — | — | 517 / 17 |
| books.toscrape.com/catalogue/the-bhagavad-gita_60/index | — | — | — | — | — | — | — | 451 / 13 |
| books.toscrape.com/catalogue/the-giver-the-giver-quarte | — | — | — | — | — | — | — | 393 / 19 |
| books.toscrape.com/catalogue/the-gunning-of-america-bus | — | — | — | — | — | — | — | 714 / 31 |
| books.toscrape.com/catalogue/the-last-girl-the-dominion | — | — | — | — | — | — | — | 539 / 22 |
| books.toscrape.com/catalogue/the-murder-of-roger-ackroy | — | — | — | — | — | — | — | 524 / 23 |
| books.toscrape.com/catalogue/the-nerdy-nummies-cookbook | — | — | — | — | — | — | — | 670 / 35 |
| books.toscrape.com/catalogue/the-nightingale_267/index. | — | — | — | — | — | — | — | 558 / 11 |
| books.toscrape.com/catalogue/the-power-of-now-a-guide-t | — | — | — | — | — | — | — | 592 / 25 |
| books.toscrape.com/catalogue/the-purest-hook-second-cir | — | — | — | — | — | — | — | 495 / 21 |
| books.toscrape.com/catalogue/the-rose-the-dagger-the-wr | — | — | — | — | — | — | — | 582 / 29 |
| books.toscrape.com/catalogue/the-shack_576/index.html | — | — | — | — | — | — | — | 407 / 11 |
| books.toscrape.com/catalogue/the-songs-of-the-gods_763/ | — | — | — | — | — | — | — | 407 / 17 |
| books.toscrape.com/catalogue/the-suffragettes-little-bl | — | — | — | — | — | — | — | 453 / 19 |
| books.toscrape.com/catalogue/the-whale_501/index.html | — | — | — | — | — | — | — | 387 / 11 |
| books.toscrape.com/catalogue/thinking-fast-and-slow_289 | — | — | — | — | — | — | — | 570 / 15 |
| books.toscrape.com/catalogue/this-is-where-it-ends_771/ | — | — | — | — | — | — | — | 371 / 18 |
| books.toscrape.com/catalogue/twenty-yawns_773/index.htm | — | — | — | — | — | — | — | 384 / 11 |
| books.toscrape.com/catalogue/vampire-girl-vampire-girl- | — | — | — | — | — | — | — | 481 / 17 |
| books.toscrape.com/catalogue/vegan-vegetarian-omnivore- | — | — | — | — | — | — | — | 758 / 27 |
| books.toscrape.com/catalogue/vogue-colors-a-to-z-a-fash | — | — | — | — | — | — | — | 449 / 25 |
| books.toscrape.com/catalogue/ways-of-seeing_94/index.ht | — | — | — | — | — | — | — | 524 / 13 |
| books.toscrape.com/catalogue/when-breath-becomes-air_55 | — | — | — | — | — | — | — | 552 / 15 |
| books.toscrape.com/catalogue/wild-swans_782/index.html | — | — | — | — | — | — | — | 418 / 12 |

</details>

### fastapi-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 2460 | 0 | 0% | 29 | 25.8 | 24.4 | 100% | 67% |
| crawl4ai | 3991 | 1438 ⚠ | 5% | 29 | 25.8 | 24.4 | 100% | 93% |
| crawl4ai-raw | 3989 | 1437 ⚠ | 5% | 29 | 25.8 | 24.4 | 100% | 93% |
| scrapy+md | 3258 | 781 ⚠ | 3% | 48 | 25.8 | 24.4 | 100% | 67% |
| crawlee | 3580 | 1019 ⚠ | 4% | 96 | 25.8 | 24.4 | 100% | 99% |
| colly+md | 3581 | 1001 ⚠ | 4% | 96 | 25.8 | 24.4 | 100% | 99% |
| playwright | 3563 | 1001 ⚠ | 4% | 96 | 25.8 | 24.4 | 100% | 99% |
| firecrawl | 1795 | 3 | 0% | 46 | 10.8 | 4.5 | 6% | 5% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

This is the site where preamble differences are largest. crawl4ai's 1,438-word preamble comes from version selectors, language pickers, sponsor banners, and full sidebar navigation repeated on every page -- accounting for approximately 36% of crawl4ai's total output. markcrawl strips all of it (0 words preamble) but captures only 67% of the agreed-upon content vs 99% for crawlee. scrapy+md matches markcrawl's 67% recall despite having 781 words of preamble, suggesting its content filtering is inconsistent rather than aggressive.

<details>
<summary>Sample output — first 40 lines of <code>fastapi.tiangolo.com/external-links</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# External Links[¶](#external-links "Permanent link")

**FastAPI** has a great community constantly growing.

There are many posts, articles, tools, and projects, related to **FastAPI**.

You could easily use a search engine or video platform to find many resources related to FastAPI.

Info

Before, this page used to list links to external articles.

But now that FastAPI is the backend framework with the most GitHub stars across languages, and the most starred and used framework in Python, it no longer makes sense to attempt to list all articles written about it.

## GitHub Repositories[¶](#github-repositories "Permanent link")

Most starred [GitHub repositories with the topic `fastapi`](https://github.com/topics/fastapi):

[★ 42397 - full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) by [@fastapi](https://github.com/fastapi).

[★ 34997 - Hello-Python](https://github.com/mouredev/Hello-Python) by [@mouredev](https://github.com/mouredev).

[★ 21857 - serve](https://github.com/jina-ai/serve) by [@jina-ai](https://github.com/jina-ai).

[★ 20868 - HivisionIDPhotos](https://github.com/Zeyi-Lin/HivisionIDPhotos) by [@Zeyi-Lin](https://github.com/Zeyi-Lin).

[★ 17770 - sqlmodel](https://github.com/fastapi/sqlmodel) by [@fastapi](https://github.com/fastapi).

[★ 16897 - fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) by [@zhanymkanov](https://github.com/zhanymkanov).

[★ 16878 - Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) by [@Evil0ctal](https://github.com/Evil0ctal).

[★ 13614 - SurfSense](https://github.com/MODSetter/SurfSense) by [@MODSetter](https://github.com/MODSetter).

[★ 12780 - machine-learning-zoomcamp](https://github.com/DataTalksClub/machine-learning-zoomcamp) by [@DataTalksClub](https://github.com/DataTalksClub).

[★ 11752 - fastapi_mcp](https://github.com/tadata-org/fastapi_mcp) by [@tadata-org](https://github.com/tadata-org).

[★ 11203 - awesome-fastapi](https://github.com/mjhea0/awesome-fastapi) by [@mjhea0](https://github.com/mjhea0).
```

**crawl4ai**
```
[ Skip to content ](https://fastapi.tiangolo.com/external-links/#external-links)
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
External Links 
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


[ ](https://fastapi.tiangolo.com/external-links/?q= "Share")
Initializing search 
[ fastapi/fastapi 
  * 0.135.3
  * 96.9k
  * 9k
```

**crawl4ai-raw**
```
[ Skip to content ](https://fastapi.tiangolo.com/external-links/#external-links)
[ **FastAPI Cloud** waiting list 🚀 ](https://fastapicloud.com)
[ Follow **@fastapi** on **X (Twitter)** to stay updated ](https://x.com/fastapi)
[ Follow **FastAPI** on **LinkedIn** to stay updated ](https://www.linkedin.com/company/fastapi)
[ **FastAPI and friends** newsletter 🎉 ](https://fastapi.tiangolo.com/newsletter/)
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/blockbee-banner.png) ](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/scalar-banner.svg) ](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/propelauth-banner.png) ](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/zuplo-banner.png) ](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/liblab-banner.png) ](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from fastapi")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/render-banner.svg) ](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/coderabbit-banner.png) ](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/subtotal-banner.svg) ](https://subtotal.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=open-source "Making Retail Purchases Actionable for Brands and Developers")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/railway-banner.png) ](https://docs.railway.com/guides/fastapi?utm_medium=integration&utm_source=docs&utm_campaign=fastapi "Deploy enterprise applications at startup speed")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/serpapi-banner.png) ](https://serpapi.com/?utm_source=fastapi_website "SerpApi: Web Search API")
[ sponsor ![](https://fastapi.tiangolo.com/img/sponsors/greptile-banner.png) ](https://www.greptile.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=fastapi_sponsor_page "Greptile: The AI Code Reviewer")
[ ![logo](https://fastapi.tiangolo.com/img/icon-white.svg) ](https://fastapi.tiangolo.com/ "FastAPI")
FastAPI 
External Links 
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


[ ](https://fastapi.tiangolo.com/external-links/?q= "Share")
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

* [FastAPI](..)
* [Features](../features/)
* [Learn](../learn/)

  Learn
  + [Python Types Intro](../python-types/)
  + [Concurrency and async / await](../async/)
  + [Environment Variables](../environment-variables/)
  + [Virtual Environments](../virtual-environments/)
  + [Tutorial - User Guide](../tutorial/)

    Tutorial - User Guide
    - [First Steps](../tutorial/first-steps/)
    - [Path Parameters](../tutorial/path-params/)
    - [Query Parameters](../tutorial/query-params/)
    - [Request Body](../tutorial/body/)
    - [Query Parameters and String Validations](../tutorial/query-params-str-validations/)
    - [Path Parameters and Numeric Validations](../tutorial/path-params-numeric-validations/)
    - [Query Parameter Models](../tutorial/query-param-models/)
    - [Body - Multiple Parameters](../tutorial/body-multiple-params/)
    - [Body - Fields](../tutorial/body-fields/)
    - [Body - Nested Models](../tutorial/body-nested-models/)
    - [Declare Request Example Data](../tutorial/schema-extra-example/)
    - [Extra Data Types](../tutorial/extra-data-types/)
    - [Cookie Parameters](../tutorial/cookie-params/)
    - [Header Parameters](../tutorial/header-params/)
    - [Cookie Parameter Models](../tutorial/cookie-param-models/)
    - [Header Parameter Models](../tutorial/header-param-models/)
    - [Response Model - Return Type](../tutorial/response-model/)
    - [Extra Models](../tutorial/extra-models/)
    - [Response Status Code](../tutorial/response-status-code/)
    - [Form Data](../tutorial/request-forms/)
    - [Form Models](../tutorial/request-form-models/)
    - [Request Files](../tutorial/request-files/)
    - [Request Forms and Files](../tutorial/request-forms-and-files/)
    - [Handling Errors](../tutorial/handling-errors/)
```

**crawlee**
```
External Links - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}




.grecaptcha-badge {
visibility: hidden;
}




[Skip to content](https://fastapi.tiangolo.com/external-links/#external-links)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)
```

**colly+md**
```
External Links - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}




[Skip to content](#external-links)

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
External Links - FastAPI




:root{--md-text-font:"Roboto";--md-code-font:"Roboto Mono"}



\_\_md\_scope=new URL("..",location),\_\_md\_hash=e=>[...e].reduce(((e,\_)=>(e<<5)-e+\_.charCodeAt(0)),0),\_\_md\_get=(e,\_=localStorage,t=\_\_md\_scope)=>JSON.parse(\_.getItem(t.pathname+"."+e)),\_\_md\_set=(e,\_,t=localStorage,a=\_\_md\_scope)=>{try{t.setItem(a.pathname+"."+e,JSON.stringify(\_))}catch(e){}}




[Skip to content](https://fastapi.tiangolo.com/external-links/#external-links)

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
[Skip to content](https://fastapi.tiangolo.com/external-links/#external-links)

# External Links [¶](https://fastapi.tiangolo.com/external-links/\#external-links)

**FastAPI** has a great community constantly growing.

There are many posts, articles, tools, and projects, related to **FastAPI**.

You could easily use a search engine or video platform to find many resources related to FastAPI.

Info

Before, this page used to list links to external articles.

But now that FastAPI is the backend framework with the most GitHub stars across languages, and the most starred and used framework in Python, it no longer makes sense to attempt to list all articles written about it.

## GitHub Repositories [¶](https://fastapi.tiangolo.com/external-links/\#github-repositories)

Most starred [GitHub repositories with the topic `fastapi`](https://github.com/topics/fastapi):

[★ 42397 - full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) by [@fastapi](https://github.com/fastapi).

[★ 34997 - Hello-Python](https://github.com/mouredev/Hello-Python) by [@mouredev](https://github.com/mouredev).

[★ 21857 - serve](https://github.com/jina-ai/serve) by [@jina-ai](https://github.com/jina-ai).

[★ 20868 - HivisionIDPhotos](https://github.com/Zeyi-Lin/HivisionIDPhotos) by [@Zeyi-Lin](https://github.com/Zeyi-Lin).

[★ 17770 - sqlmodel](https://github.com/fastapi/sqlmodel) by [@fastapi](https://github.com/fastapi).

[★ 16897 - fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) by [@zhanymkanov](https://github.com/zhanymkanov).

[★ 16878 - Douyin\_TikTok\_Download\_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) by [@Evil0ctal](https://github.com/Evil0ctal).

[★ 13614 - SurfSense](https://github.com/MODSetter/SurfSense) by [@MODSetter](https://github.com/MODSetter).

[★ 12780 - machine-learning-zoomcamp](https://github.com/DataTalksClub/machine-learning-zoomcamp) by [@DataTalksClub](https://github.com/DataTalksClub).

[★ 11752 - fastapi\_mcp](https://github.com/tadata-org/fastapi_mcp) by [@tadata-org](https://github.com/tadata-org).
```

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| fastapi.tiangolo.com | 2230 / 0 | 3991 / 1538 | 3979 / 1526 | 3092 / 839 | 3374 / 1071 | 3404 / 1054 | 3357 / 1054 | 2605 / 3 |
| fastapi.tiangolo.com/_llm-test | — | — | — | — | — | — | — | 1819 / 3 |
| fastapi.tiangolo.com/advanced/additional-responses | 1274 / 0 | 2648 / 1332 | 2648 / 1332 | 2008 / 718 | 2344 / 960 | 2337 / 941 | 2325 / 941 | — |
| fastapi.tiangolo.com/advanced/async-tests | 646 / 0 | 1991 / 1308 | 1991 / 1308 | 1354 / 692 | 1682 / 928 | 1678 / 911 | 1665 / 911 | — |
| fastapi.tiangolo.com/advanced/events | 1500 / 0 | 2886 / 1356 | 2886 / 1356 | 2240 / 724 | 2554 / 960 | 2559 / 943 | 2537 / 943 | — |
| fastapi.tiangolo.com/advanced/json-base64-bytes | 743 / 0 | 2096 / 1314 | 2096 / 1314 | 1462 / 703 | 1799 / 947 | 1790 / 928 | 1780 / 928 | — |
| fastapi.tiangolo.com/advanced/openapi-callbacks | 1746 / 0 | 3155 / 1376 | 3155 / 1376 | 2510 / 748 | 2831 / 986 | 2832 / 967 | 2812 / 967 | — |
| fastapi.tiangolo.com/advanced/stream-data | 2723 / 0 | 4109 / 1354 | 4111 / 1356 | 3465 / 726 | 3785 / 962 | 3788 / 945 | 3768 / 945 | — |
| fastapi.tiangolo.com/advanced/websockets | 1638 / 0 | 3050 / 1374 | 3046 / 1374 | 2397 / 743 | 2714 / 979 | 2714 / 960 | 2695 / 960 | — |
| fastapi.tiangolo.com/alternatives | — | — | — | — | — | — | — | 3479 / 3 |
| fastapi.tiangolo.com/async | — | — | — | — | — | — | — | 3875 / 3 |
| fastapi.tiangolo.com/benchmarks | — | — | — | — | — | — | — | 733 / 3 |
| fastapi.tiangolo.com/contributing | — | — | — | — | — | — | — | 1800 / 3 |
| fastapi.tiangolo.com/de/reference/parameters | — | — | — | — | — | — | — | 11716 / 2 |
| fastapi.tiangolo.com/de/tutorial/body-multiple-params | — | — | — | — | — | — | — | 1598 / 2 |
| fastapi.tiangolo.com/deployment/fastapicloud | 295 / 0 | 1650 / 1308 | 1637 / 1306 | 1005 / 694 | 1310 / 932 | 1326 / 913 | 1311 / 913 | — |
| fastapi.tiangolo.com/editor-support | — | — | — | — | — | — | — | 517 / 3 |
| fastapi.tiangolo.com/environment-variables | — | — | — | — | — | — | — | 1364 / 3 |
| fastapi.tiangolo.com/es/tutorial/path-operation-configu | — | — | — | — | — | — | — | 1132 / 3 |
| fastapi.tiangolo.com/external-links | 699 / 0 | 1999 / 1254 | 1999 / 1254 | 1375 / 660 | 1712 / 896 | 1699 / 879 | 1695 / 879 | 907 / 3 |
| fastapi.tiangolo.com/fastapi-cli | — | — | — | — | — | — | — | 797 / 3 |
| fastapi.tiangolo.com/fastapi-people | — | — | — | — | — | — | — | 2386 / 3 |
| fastapi.tiangolo.com/features | — | — | — | — | — | — | — | 1357 / 3 |
| fastapi.tiangolo.com/fr/tutorial/background-tasks | — | — | — | — | — | — | — | 1274 / 3 |
| fastapi.tiangolo.com/help-fastapi | — | — | — | — | — | — | — | 2142 / 3 |
| fastapi.tiangolo.com/history-design-future | — | — | — | — | — | — | — | 822 / 3 |
| fastapi.tiangolo.com/how-to/authentication-error-status | 194 / 0 | 1492 / 1254 | 1492 / 1254 | 861 / 651 | 1208 / 899 | 1191 / 880 | 1189 / 880 | — |
| fastapi.tiangolo.com/ja/tutorial/request-forms | — | — | — | — | — | — | — | 420 / 1 |
| fastapi.tiangolo.com/learn | 35 / 0 | 1322 / 1241 | 1322 / 1241 | 697 / 646 | 1030 / 880 | 1015 / 863 | 1013 / 863 | — |
| fastapi.tiangolo.com/management | — | — | — | — | — | — | — | 420 / 3 |
| fastapi.tiangolo.com/management-tasks | — | — | — | — | — | — | — | 1998 / 3 |
| fastapi.tiangolo.com/newsletter | — | — | — | — | — | — | — | 318 / 3 |
| fastapi.tiangolo.com/project-generation | — | — | — | — | — | — | — | 285 / 3 |
| fastapi.tiangolo.com/pt | 2344 / 0 | 4216 / 1644 | 4216 / 1644 | 3308 / 941 | 3596 / 1175 | 3626 / 1158 | 3579 / 1158 | — |
| fastapi.tiangolo.com/reference | 44 / 0 | 1334 / 1241 | 1334 / 1241 | 706 / 646 | 1044 / 880 | 1029 / 863 | 1027 / 863 | — |
| fastapi.tiangolo.com/reference/fastapi | 29527 / 0 | 31322 / 1454 | 31322 / 1454 | 30321 / 778 | 30633 / 1016 | 30640 / 997 | 30614 / 997 | — |
| fastapi.tiangolo.com/reference/middleware | 1030 / 0 | 2490 / 1410 | 2490 / 1410 | 1811 / 765 | 2150 / 999 | 2135 / 982 | 2133 / 982 | — |
| fastapi.tiangolo.com/reference/openapi/models | 3708 / 0 | 7394 / 3186 | 7394 / 3186 | 5672 / 1948 | 6009 / 2186 | 5992 / 2167 | 5990 / 2167 | — |
| fastapi.tiangolo.com/reference/templating | 623 / 0 | 1974 / 1276 | 1974 / 1276 | 1314 / 675 | 1655 / 913 | 1640 / 896 | 1638 / 896 | — |
| fastapi.tiangolo.com/resources | 14 / 0 | 1302 / 1241 | 1302 / 1241 | 676 / 646 | 1012 / 880 | 997 / 863 | 995 / 863 | — |
| fastapi.tiangolo.com/ru | 2074 / 0 | 3844 / 1537 | 3844 / 1537 | 2931 / 834 | 3214 / 1067 | 3244 / 1050 | 3197 / 1050 | — |
| fastapi.tiangolo.com/ru/tutorial/request-forms | — | — | — | — | — | — | — | 708 / 3 |
| fastapi.tiangolo.com/tutorial/body-nested-models | 1463 / 0 | 2929 / 1443 | 2927 / 1441 | 2270 / 791 | 2586 / 1033 | 2597 / 1014 | 2567 / 1014 | — |
| fastapi.tiangolo.com/tutorial/extra-models | 1219 / 0 | 2649 / 1405 | 2647 / 1403 | 1998 / 763 | 2313 / 999 | 2322 / 982 | 2308 / 994 | — |
| fastapi.tiangolo.com/tutorial/security | 687 / 0 | 2012 / 1290 | 2010 / 1288 | 1381 / 678 | 1703 / 912 | 1702 / 895 | 1686 / 895 | — |
| fastapi.tiangolo.com/tutorial/security/simple-oauth2 | 3596 / 0 | 5078 / 1455 | 5078 / 1455 | 4405 / 793 | 4724 / 1037 | 4741 / 1020 | 4707 / 1020 | — |
| fastapi.tiangolo.com/tutorial/server-sent-events | 1449 / 0 | 2839 / 1361 | 2837 / 1359 | 2195 / 730 | 2515 / 968 | 2518 / 951 | 2498 / 951 | — |
| fastapi.tiangolo.com/zh/tutorial/security | — | — | — | — | — | — | — | 407 / 1 |

</details>

### python-docs

| Tool | Avg words | Preamble [1] | Repeat rate | Junk found | Headings | Code blocks | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| markcrawl | 2321 | 0 | 0% | 19 | 3.4 | 2.4 | 100% | 68% |
| crawl4ai | 2709 | 59 ⚠ | 1% | 85 | 9.8 | 2.4 | 100% | 59% |
| crawl4ai-raw | 2709 | 59 ⚠ | 1% | 85 | 9.8 | 2.4 | 100% | 59% |
| scrapy+md | 3112 | 4 | 0% | 70 | 10.4 | 2.9 | 100% | 100% |
| crawlee | 2654 | 46 | 0% | 85 | 9.8 | 2.4 | 100% | 90% |
| colly+md | 2571 | 19 | 0% | 85 | 9.8 | 2.4 | 100% | 91% |
| playwright | 2654 | 46 | 0% | 85 | 9.8 | 2.4 | 100% | 90% |
| firecrawl | 7709 | 0 | 0% | 120 | 23.4 | 29.4 | 0% | 0% |

**[1]** Avg words per page before the first heading (nav chrome). **⚠** = likely nav/boilerplate problem (preamble >50 or repeat rate >20%).

markcrawl's 68% recall is higher than crawl4ai's 59% on this site, despite markcrawl having zero preamble vs crawl4ai's 59 words. crawl4ai injects more noise *and* misses more content here. scrapy+md achieves 100% recall with only 4 words of preamble, making it the strongest tool on this particular site.

<details>
<summary>Sample output — first 40 lines of <code>docs.python.org/3.15</code></summary>

This shows what each tool outputs at the *top* of the same page.
Nav boilerplate appears here before the real content starts.

**markcrawl**
```
# Python 3.15.0a7 documentation

Welcome! This is the official documentation for Python 3.15.0a7.

**Documentation sections:**

|  |  |
| --- | --- |
| [What's new in Python 3.15?](whatsnew/3.15.html)   Or [all "What's new" documents since Python 2.0](whatsnew/index.html)  [Tutorial](tutorial/index.html)  Start here: a tour of Python's syntax and features  [Library reference](library/index.html)  Standard library and builtins  [Language reference](reference/index.html)  Syntax and language elements  [Python setup and usage](using/index.html)  How to install, configure, and use Python  [Python HOWTOs](howto/index.html)  In-depth topic manuals | [Installing Python modules](installing/index.html)  Third-party modules and PyPI.org  [Distributing Python modules](distributing/index.html)  Publishing modules for use by other people  [Extending and embedding](extending/index.html)  For C/C++ programmers  [Python's C API](c-api/index.html)  C API reference  [FAQs](faq/index.html)  Frequently asked questions (with answers!)  [Deprecations](deprecations/index.html)  Deprecated functionality |

**Indices, glossary, and search:**

|  |  |
| --- | --- |
| [Global module index](py-modindex.html)  All modules and libraries  [General index](genindex.html)  All functions, classes, and terms  [Glossary](glossary.html)  Terms explained | [Search page](search.html)  Search this documentation  [Complete table of contents](contents.html)  Lists all sections and subsections |

**Project information:**

|  |  |
| --- | --- |
| [Reporting issues](bugs.html)  [Contributing to docs](https://devguide.python.org/documentation/help-documenting/)  [Download the documentation](download.html) | [History and license of Python](license.html)  [Copyright](copyright.html)  [About the documentation](about.html) |
```

**crawl4ai**
```
[ ![Python logo](https://docs.python.org/3.15/_static/py.svg) ](https://www.python.org/) 3.15.0a7 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
### Download
[Download these documents](https://docs.python.org/3.15/download.html)
### Docs by version
  * [Python 3.15 (in development)](https://docs.python.org/3.15/)
  * [Python 3.14 (stable)](https://docs.python.org/3.14/)
  * [Python 3.13 (stable)](https://docs.python.org/3.13/)
  * [Python 3.12 (security-fixes)](https://docs.python.org/3.12/)
  * [Python 3.11 (security-fixes)](https://docs.python.org/3.11/)
  * [Python 3.10 (security-fixes)](https://docs.python.org/3.10/)
  * [Python 3.9 (EOL)](https://docs.python.org/3.9/)
  * [Python 3.8 (EOL)](https://docs.python.org/3.8/)
  * [Python 3.7 (EOL)](https://docs.python.org/3.7/)
  * [Python 3.6 (EOL)](https://docs.python.org/3.6/)
  * [Python 3.5 (EOL)](https://docs.python.org/3.5/)
  * [Python 3.4 (EOL)](https://docs.python.org/3.4/)
  * [Python 3.3 (EOL)](https://docs.python.org/3.3/)
  * [Python 3.2 (EOL)](https://docs.python.org/3.2/)
  * [Python 3.1 (EOL)](https://docs.python.org/3.1/)
  * [Python 3.0 (EOL)](https://docs.python.org/3.0/)
  * [Python 2.7 (EOL)](https://docs.python.org/2.7/)
  * [Python 2.6 (EOL)](https://docs.python.org/2.6/)
  * [All versions](https://www.python.org/doc/versions/)


### Other resources
  * [PEP Index](https://peps.python.org/)
  * [Beginner's Guide](https://wiki.python.org/moin/BeginnersGuide)
  * [Book List](https://wiki.python.org/moin/PythonBooks)
  * [Audio/Visual Talks](https://www.python.org/doc/av/)
  * [Python Developer's Guide](https://devguide.python.org/)


### Navigation
  * [index](https://docs.python.org/3.15/genindex.html "General Index")
  * [modules](https://docs.python.org/3.15/py-modindex.html "Python Module Index") |
  * ![Python logo](https://docs.python.org/3.15/_static/py.svg)
  * [Python](https://www.python.org/) »
```

**crawl4ai-raw**
```
[ ![Python logo](https://docs.python.org/3.15/_static/py.svg) ](https://www.python.org/) 3.15.0a7 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7 3.6 3.5 3.4 3.3 3.2 3.1 3.0 2.7 2.6
Greek | Ελληνικά English Spanish | español French | français Italian | italiano Japanese | 日本語 Korean | 한국어 Polish | polski Brazilian Portuguese | Português brasileiro Romanian | Românește Turkish | Türkçe Simplified Chinese | 简体中文 Traditional Chinese | 繁體中文
Theme  Auto Light Dark
### Download
[Download these documents](https://docs.python.org/3.15/download.html)
### Docs by version
  * [Python 3.15 (in development)](https://docs.python.org/3.15/)
  * [Python 3.14 (stable)](https://docs.python.org/3.14/)
  * [Python 3.13 (stable)](https://docs.python.org/3.13/)
  * [Python 3.12 (security-fixes)](https://docs.python.org/3.12/)
  * [Python 3.11 (security-fixes)](https://docs.python.org/3.11/)
  * [Python 3.10 (security-fixes)](https://docs.python.org/3.10/)
  * [Python 3.9 (EOL)](https://docs.python.org/3.9/)
  * [Python 3.8 (EOL)](https://docs.python.org/3.8/)
  * [Python 3.7 (EOL)](https://docs.python.org/3.7/)
  * [Python 3.6 (EOL)](https://docs.python.org/3.6/)
  * [Python 3.5 (EOL)](https://docs.python.org/3.5/)
  * [Python 3.4 (EOL)](https://docs.python.org/3.4/)
  * [Python 3.3 (EOL)](https://docs.python.org/3.3/)
  * [Python 3.2 (EOL)](https://docs.python.org/3.2/)
  * [Python 3.1 (EOL)](https://docs.python.org/3.1/)
  * [Python 3.0 (EOL)](https://docs.python.org/3.0/)
  * [Python 2.7 (EOL)](https://docs.python.org/2.7/)
  * [Python 2.6 (EOL)](https://docs.python.org/2.6/)
  * [All versions](https://www.python.org/doc/versions/)


### Other resources
  * [PEP Index](https://peps.python.org/)
  * [Beginner's Guide](https://wiki.python.org/moin/BeginnersGuide)
  * [Book List](https://wiki.python.org/moin/PythonBooks)
  * [Audio/Visual Talks](https://www.python.org/doc/av/)
  * [Python Developer's Guide](https://devguide.python.org/)


### Navigation
  * [index](https://docs.python.org/3.15/genindex.html "General Index")
  * [modules](https://docs.python.org/3.15/py-modindex.html "Python Module Index") |
  * ![Python logo](https://docs.python.org/3.15/_static/py.svg)
  * [Python](https://www.python.org/) »
```

**scrapy+md**
```
Theme
Auto
Light
Dark

### Download

[Download these documents](download.html)

### Docs by version

* [Python 3.15 (in development)](https://docs.python.org/3.15/)
* [Python 3.14 (stable)](https://docs.python.org/3.14/)
* [Python 3.13 (stable)](https://docs.python.org/3.13/)
* [Python 3.12 (security-fixes)](https://docs.python.org/3.12/)
* [Python 3.11 (security-fixes)](https://docs.python.org/3.11/)
* [Python 3.10 (security-fixes)](https://docs.python.org/3.10/)
* [Python 3.9 (EOL)](https://docs.python.org/3.9/)
* [Python 3.8 (EOL)](https://docs.python.org/3.8/)
* [Python 3.7 (EOL)](https://docs.python.org/3.7/)
* [Python 3.6 (EOL)](https://docs.python.org/3.6/)
* [Python 3.5 (EOL)](https://docs.python.org/3.5/)
* [Python 3.4 (EOL)](https://docs.python.org/3.4/)
* [Python 3.3 (EOL)](https://docs.python.org/3.3/)
* [Python 3.2 (EOL)](https://docs.python.org/3.2/)
* [Python 3.1 (EOL)](https://docs.python.org/3.1/)
* [Python 3.0 (EOL)](https://docs.python.org/3.0/)
* [Python 2.7 (EOL)](https://docs.python.org/2.7/)
* [Python 2.6 (EOL)](https://docs.python.org/2.6/)
* [All versions](https://www.python.org/doc/versions/)

### Other resources

* [PEP Index](https://peps.python.org/)
* [Beginner's Guide](https://wiki.python.org/moin/BeginnersGuide)
* [Book List](https://wiki.python.org/moin/PythonBooks)
* [Audio/Visual Talks](https://www.python.org/doc/av/)
* [Python Developer's Guide](https://devguide.python.org/)

### Navigation
```

**crawlee**
```
3.15.0a7 Documentation




@media only screen {
table.full-width-table {
width: 100%;
}
}



3.15.0a73.143.133.123.113.103.93.83.73.63.53.43.33.23.13.02.72.6

Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文

Theme
Auto
Light
Dark

### Download

[Download these documents](download.html)
```

**colly+md**
```
3.15.0a7 Documentation




@media only screen {
table.full-width-table {
width: 100%;
}
}



Theme
Auto
Light
Dark

### Download

[Download these documents](download.html)

### Docs by version

* [Python 3.15 (in development)](https://docs.python.org/3.15/)
* [Python 3.14 (stable)](https://docs.python.org/3.14/)
```

**playwright**
```
3.15.0a7 Documentation




@media only screen {
table.full-width-table {
width: 100%;
}
}



3.15.0a73.143.133.123.113.103.93.83.73.63.53.43.33.23.13.02.72.6

Greek | ΕλληνικάEnglishSpanish | españolFrench | françaisItalian | italianoJapanese | 日本語Korean | 한국어Polish | polskiBrazilian Portuguese | Português brasileiroRomanian | RomâneșteTurkish | TürkçeSimplified Chinese | 简体中文Traditional Chinese | 繁體中文

Theme
Auto
Light
Dark

### Download

[Download these documents](download.html)
```

**firecrawl** -- no output for this URL

</details>

<details>
<summary>Per-page word counts and preamble [1]</summary>

| URL | markcrawl words / preamble [1] | crawl4ai words / preamble [1] | crawl4ai-raw words / preamble [1] | scrapy+md words / preamble [1] | crawlee words / preamble [1] | colly+md words / preamble [1] | playwright words / preamble [1] | firecrawl words / preamble [1] |
|---|---|---|---|---|---|---|---|---|
| docs.python.org/3.1 | 320 / 0 | 315 / 0 | 315 / 0 | — | 341 / 20 | 341 / 20 | 341 / 20 | — |
| docs.python.org/3.10 | 190 / 0 | 711 / 68 | 711 / 68 | 521 / 4 | 629 / 47 | 533 / 16 | 629 / 47 | — |
| docs.python.org/3.10/contents.html | 19401 / 0 | 19782 / 68 | 19782 / 68 | 19584 / 4 | 19697 / 52 | 19601 / 21 | 19697 / 52 | — |
| docs.python.org/3.10/download.html | 277 / 0 | 599 / 68 | 599 / 68 | 404 / 4 | 515 / 50 | 419 / 19 | 515 / 50 | — |
| docs.python.org/3.10/glossary.html | 7963 / 0 | 8264 / 68 | 8264 / 68 | 8186 / 4 | 8302 / 50 | 8201 / 19 | 8302 / 50 | — |
| docs.python.org/3.10/howto/index.html | 135 / 0 | 553 / 68 | 553 / 68 | 356 / 4 | 468 / 51 | 372 / 20 | 468 / 51 | — |
| docs.python.org/3.10/py-modindex.html | 4077 / 0 | 4420 / 68 | 4420 / 68 | 4208 / 4 | 4324 / 55 | 4228 / 24 | 4324 / 55 | — |
| docs.python.org/3.10/tutorial/index.html | 982 / 0 | 1382 / 68 | 1382 / 68 | 1185 / 4 | 1298 / 52 | 1202 / 21 | 1298 / 52 | — |
| docs.python.org/3.10/using/index.html | 460 / 0 | 870 / 68 | 870 / 68 | 673 / 4 | 787 / 53 | 691 / 22 | 787 / 53 | — |
| docs.python.org/3.10/whatsnew/index.html | 2172 / 0 | 2587 / 68 | 2587 / 68 | 2389 / 4 | 2503 / 53 | 2407 / 22 | 2503 / 53 | — |
| docs.python.org/3.11 | 188 / 0 | 711 / 68 | 711 / 68 | 522 / 4 | 629 / 47 | 534 / 16 | 629 / 47 | — |
| docs.python.org/3.12 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.13 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.14 | 191 / 0 | 712 / 68 | 712 / 68 | 525 / 4 | 632 / 47 | 537 / 16 | 632 / 47 | — |
| docs.python.org/3.15 | 191 / 0 | 709 / 67 | 709 / 67 | 525 / 4 | 629 / 46 | 537 / 16 | 629 / 46 | — |
| docs.python.org/3.2 | 302 / 0 | 298 / 0 | 298 / 0 | — | 324 / 20 | 323 / 20 | 324 / 20 | — |
| docs.python.org/3.5 | 186 / 0 | 371 / 28 | 371 / 28 | — | 353 / 29 | 324 / 29 | 353 / 29 | — |
| docs.python.org/3.9 | 190 / 0 | 580 / 63 | 580 / 63 | — | 504 / 43 | 408 / 12 | 504 / 43 | — |
| docs.python.org/3/bugs.html | — | — | — | 980 / 4 | — | 997 / 21 | — | — |
| docs.python.org/3/library | — | — | — | — | — | — | — | 2390 / 0 |
| docs.python.org/3/library/argparse.html | — | — | — | — | — | — | — | 11424 / 0 |
| docs.python.org/3/library/cmdlinelibs.html | — | — | — | — | — | — | — | 331 / 0 |
| docs.python.org/3/library/constants.html | — | — | — | — | — | — | — | 843 / 0 |
| docs.python.org/3/library/ctypes.html | — | — | — | — | — | — | — | 16118 / 0 |
| docs.python.org/3/library/enum.html | — | — | — | — | — | — | — | 5264 / 0 |
| docs.python.org/3/library/exceptions.html | — | — | — | — | — | — | — | 6035 / 0 |
| docs.python.org/3/library/ftplib.html | — | — | — | — | — | — | — | 3335 / 0 |
| docs.python.org/3/library/functions.html | — | — | — | — | — | — | — | 13286 / 0 |
| docs.python.org/3/library/intro.html | — | — | — | — | — | — | — | 1501 / 0 |
| docs.python.org/3/library/logging.html | — | — | — | — | — | — | — | 9849 / 0 |
| docs.python.org/3/library/math.html | — | — | — | — | — | — | — | 4745 / 0 |
| docs.python.org/3/library/multiprocessing.html | — | — | — | — | — | — | — | 18558 / 0 |
| docs.python.org/3/library/readline.html | — | — | — | — | — | — | — | 2099 / 0 |
| docs.python.org/3/library/socket.html | — | — | — | — | — | — | — | 12777 / 0 |
| docs.python.org/3/library/stdtypes.html | — | — | — | — | — | — | — | 31375 / 0 |
| docs.python.org/3/library/struct.html | — | — | — | — | — | — | — | 3707 / 0 |
| docs.python.org/3/library/tokenize.html | — | — | — | — | — | — | — | 1650 / 0 |
| docs.python.org/3/library/winsound.html | — | — | — | — | — | — | — | 996 / 0 |
| docs.python.org/3/library/xml.etree.elementtree.html | — | — | — | — | — | — | — | 7888 / 0 |
| docs.python.org/3/license.html | — | — | — | 8679 / 4 | — | 8696 / 21 | — | — |
| docs.python.org/bugs.html | 650 / 0 | 1096 / 68 | 1096 / 68 | — | 1092 / 52 | — | 1092 / 52 | — |
| docs.python.org/license.html | 8155 / 0 | 8801 / 68 | 8801 / 68 | — | 8791 / 52 | — | 8791 / 52 | — |

</details>

---

## Methodology

### What was measured

Four automated metrics -- no LLM or human review required:

1. **Junk phrases** -- known boilerplate strings (nav, footer, breadcrumbs) found in output. Detected via a fixed list of common site chrome patterns.
2. **Preamble** -- average words per page appearing *before* the first heading. Nav chrome (version selectors, language pickers, prev/next links) lives here. A tool with a high preamble count is injecting site chrome into every chunk.
3. **Cross-page repeat rate** -- fraction of sentences that appear on more than 50% of pages. Real content appears on at most a few pages; nav text repeats everywhere. High repeat rate = nav boilerplate polluting every chunk in the RAG index.
4. **Precision and recall** -- each tool's output is compared against the majority-agreement set across all tools. Precision measures what fraction of a tool's output the other tools also agree is real content. Recall measures what fraction of the majority-agreed content this tool captured.

Note on the consensus approach: "precision" and "recall" here are relative to inter-tool agreement, not to a gold-standard human annotation. A tool that systematically misses content that every other tool captures will show low recall. A tool that outputs content no other tool considers real will show low precision. This is a practical proxy, not a ground truth measurement.

### Test sites

- **quotes-toscrape** -- simple static site, minimal nav chrome. Good baseline.
- **books-toscrape** -- e-commerce catalog, moderate nav (category sidebar, breadcrumbs).
- **fastapi-docs** -- heavily navved documentation site (MkDocs). Sponsor banners, language pickers, version selectors. This is where preamble differences are largest.
- **python-docs** -- official Python documentation, similar nav structure to fastapi-docs but different rendering.

### What was NOT measured

- **Retrieval quality** -- whether output quality translates to better search hit rates. See [RETRIEVAL_COMPARISON.md](RETRIEVAL_COMPARISON.md).
- **Answer quality** -- whether retrieved chunks produce better LLM answers. See [ANSWER_QUALITY.md](ANSWER_QUALITY.md).
- **Speed** -- how long each tool takes to crawl. See [SPEED_COMPARISON.md](SPEED_COMPARISON.md).
- **Cost** -- API and infrastructure costs at scale. See [COST_AT_SCALE.md](COST_AT_SCALE.md).
- **Human-labeled ground truth** -- all quality metrics use automated or consensus-based methods. A human editorial review of sampled output would be needed to validate these measurements.

See [METHODOLOGY.md](METHODOLOGY.md) for full test setup, tool configurations, and fairness decisions.
