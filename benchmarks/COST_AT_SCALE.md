# RAG Cost Analysis at Scale

How crawler choice affects your RAG pipeline costs as corpus size grows.

Benchmarked 7 crawler tools across 8 sites (92 queries). Each tool crawled the
same pages, then we chunked, embedded, and tested retrieval + LLM answer quality.
The results show that tools differ on two dimensions that affect cost: **chunk
efficiency** (how many chunks per page) and **answer quality** (how good the
LLM's answers are from those chunks).

---

## All Tools Compared

Measured across ~150 pages on 8 sites (92 queries, scored by GPT-4o-mini judge):

| Tool | Chunks | Chunks/page | vs markcrawl | Answer Quality (/5) | vs markcrawl |
|---|---|---|---|---|---|
| **markcrawl** | **2,126** | **14.2** | **1.00x** | **3.91** | **baseline** |
| scrapy+md | 2,574 | 17.2 | 1.21x | 3.86 | -1.3% |
| crawl4ai | 3,539 | 23.6 | 1.66x | 3.82 | -2.3% |
| crawl4ai-raw | 3,540 | 23.6 | 1.67x | 3.84 | -1.8% |
| colly+md | 3,884 | 25.9 | 1.83x | 3.83 | -2.0% |
| playwright | 4,167 | 27.8 | 1.96x | 3.74 | -4.3% |
| crawlee | 4,422 | 29.5 | 2.08x | 3.80 | -2.8% |

Markcrawl produces the fewest chunks and the highest answer quality. The closest
competitor is **scrapy+md** (21% more chunks, similar quality). The widest gap
is with **crawlee** (108% more chunks, 2.8% lower quality).

Full results: [Answer quality](ANSWER_QUALITY.md) | [Retrieval quality](RETRIEVAL_COMPARISON.md) | [Speed](SPEED_COMPARISON.md)

---

## Cost Drivers

There are two independent cost drivers in a RAG pipeline, and they scale
with different things:

1. **Storage costs** scale with how many pages you crawl (corpus size)
2. **Query costs** scale with how many questions users ask (query volume)

### Part 1: Storage Costs (scale with pages)

Every page gets chunked, embedded, and stored in a vector database. More chunks
per page = higher cost. Storage includes one-time embedding + ongoing vector DB.

| Pages | markcrawl | scrapy+md | crawl4ai | colly+md | playwright | crawlee |
|---|---|---|---|---|---|---|
| 100 | $2 | $2 | $3 | $4 | $4 | $4 |
| 1,000 | $17 | $21 | $28 | $32 | $34 | $36 |
| 10,000 | $171 | $207 | $283 | $315 | $336 | $356 |
| 100,000 | $1,710 | $2,069 | $2,832 | $3,148 | $3,363 | $3,556 |
| 1,000,000 | $17,093 | $20,693 | $28,322 | $31,477 | $33,628 | $35,553 |

At 1M pages, markcrawl saves **$3,600/yr vs scrapy+md** and **$18,460/yr vs crawlee**
on storage alone. The savings scale linearly — 10x more pages = 10x more savings.

### Part 2: Query Costs (scale with query volume)

Every query retrieves top-K chunks and sends them to an LLM. Markcrawl's cleaner
chunks produce the best answers at K=10. Tools with noisier chunks need a higher K
to compensate, sending more tokens per query.

Estimated K needed to match markcrawl's answer quality:

| Tool | Quality at K=10 | Estimated K to match | Tokens/query |
|---|---|---|---|
| markcrawl | 3.91 (baseline) | 10 | 3,000 |
| scrapy+md | 3.86 (-1.3%) | ~12 | 3,600 |
| crawl4ai | 3.82 (-2.3%) | ~13 | 3,900 |
| crawl4ai-raw | 3.84 (-1.8%) | ~12 | 3,600 |
| colly+md | 3.83 (-2.0%) | ~13 | 3,900 |
| playwright | 3.74 (-4.3%) | ~15 | 4,500 |
| crawlee | 3.80 (-2.8%) | ~13 | 3,900 |

Annual LLM query cost (Claude Sonnet at $3.00/1M input tokens):

| Queries/day | markcrawl | scrapy+md | crawl4ai | crawlee | playwright |
|---|---|---|---|---|---|
| 100 | $329 | $394 | $427 | $427 | $493 |
| 1,000 | $3,285 | $3,942 | $4,270 | $4,270 | $4,928 |
| 10,000 | $32,850 | $39,420 | $42,705 | $42,705 | $49,275 |
| 100,000 | $328,500 | $394,200 | $427,050 | $427,050 | $492,750 |

---

## Combined: Total Annual Cost

Add storage (from corpus size) + queries (from daily volume) = total annual cost.

### All tools at 100K pages, 1K queries/day

| Tool | Storage/yr | Queries/yr | Total/yr | vs markcrawl |
|---|---|---|---|---|
| **markcrawl** | **$1,710** | **$3,285** | **$4,995** | **—** |
| scrapy+md | $2,069 | $3,942 | $6,011 | +$1,016 |
| crawl4ai | $2,832 | $4,270 | $7,102 | +$2,107 |
| crawl4ai-raw | $2,846 | $3,942 | $6,788 | +$1,793 |
| colly+md | $3,148 | $4,270 | $7,418 | +$2,423 |
| crawlee | $3,556 | $4,270 | $7,826 | +$2,831 |
| playwright | $3,363 | $4,928 | $8,291 | +$3,296 |

### Common scenarios (markcrawl vs all tools)

**Scenario A: Small app (1K pages, 100 queries/day)**

| Tool | Total/yr | vs markcrawl |
|---|---|---|
| markcrawl | $346 | — |
| scrapy+md | $417 | +$71 |
| crawl4ai | $459 | +$113 |
| crawlee | $467 | +$121 |
| playwright | $527 | +$181 |

**Scenario B: Mid-size product (100K pages, 1K queries/day)**

| Tool | Total/yr | vs markcrawl |
|---|---|---|
| markcrawl | $4,995 | — |
| scrapy+md | $6,011 | +$1,016 |
| crawl4ai | $7,102 | +$2,107 |
| crawlee | $7,826 | +$2,831 |
| playwright | $8,291 | +$3,296 |

**Scenario C: Large-scale RAG (1M pages, 10K queries/day)**

| Tool | Total/yr | vs markcrawl |
|---|---|---|
| markcrawl | $49,943 | — |
| scrapy+md | $60,113 | +$10,170 |
| crawl4ai | $71,027 | +$21,084 |
| crawlee | $78,258 | +$28,315 |
| playwright | $82,903 | +$32,960 |

---

## Head-to-Head: markcrawl vs scrapy+md (closest competitor)

Scrapy+md is markcrawl's closest competitor on both chunk efficiency and answer
quality. Here's how they compare at every scale:

| Pages | MC Chunks | Scrapy Chunks | MC Storage/yr | Scrapy Storage/yr | Storage Savings |
|---|---|---|---|---|---|
| 100 | 1,417 | 1,716 | $2 | $2 | $0.40 |
| 1,000 | 14,173 | 17,160 | $17 | $21 | $4 |
| 10,000 | 141,733 | 171,600 | $171 | $207 | $36 |
| 100,000 | 1,417,333 | 1,716,000 | $1,710 | $2,069 | $360 |
| 1,000,000 | 14,173,333 | 17,160,000 | $17,093 | $20,693 | $3,600 |

| Queries/day | MC Queries/yr | Scrapy Queries/yr | Query Savings |
|---|---|---|---|
| 100 | $329 | $394 | $66 |
| 1,000 | $3,285 | $3,942 | $657 |
| 10,000 | $32,850 | $39,420 | $6,570 |

The margin vs scrapy+md is narrower than vs crawlee — roughly **17% savings**
across all scales instead of 36%. But markcrawl still leads on both dimensions:
fewer chunks (1.21x) and higher answer quality (+1.3%).

---

## Methodology

### Source data

All numbers derive from our benchmark of **92 queries across 8 sites** using
7 crawler tools. Full results in [ANSWER_QUALITY.md](ANSWER_QUALITY.md) and
[RETRIEVAL_COMPARISON.md](RETRIEVAL_COMPARISON.md).

Measured values for all tools:

| Tool | Total chunks | Chunks/page | Answer quality (/5) |
|---|---|---|---|
| markcrawl | 2,126 | 14.17 | 3.91 |
| scrapy+md | 2,574 | 17.16 | 3.86 |
| crawl4ai | 3,539 | 23.59 | 3.82 |
| crawl4ai-raw | 3,540 | 23.60 | 3.84 |
| colly+md | 3,884 | 25.89 | 3.83 |
| playwright | 4,167 | 27.78 | 3.74 |
| crawlee | 4,422 | 29.48 | 3.80 |

All tools crawled the same ~150 pages across 8 sites. Chunks were created with
the same chunker (300-word max, 50-word overlap). Quality was scored by a
GPT-4o-mini judge on correctness, relevance, completeness, and usefulness (1-5
each), averaged to an overall score.

### Chunk count formula

```
chunks = pages x chunks_per_page

where chunks_per_page is measured per-tool (see table above)
```

### Storage cost formula

Storage = embedding (one-time) + vector DB hosting (ongoing).

**Embedding:**
```
embedding_cost = chunks x tokens_per_chunk x price_per_token

where:
  tokens_per_chunk = 300          (measured average across benchmark)
  price_per_token  = $0.02 / 1M  (OpenAI text-embedding-3-small, April 2026)
```

**Vector database:**
```
annual_storage = (chunks / 1,000) x cost_per_1K_vectors_per_month x 12

where:
  cost_per_1K_vectors_per_month = $0.10
```

**Embedding pricing source:** [OpenAI pricing](https://openai.com/pricing)
- `text-embedding-3-small`: $0.02 per 1M tokens
- `text-embedding-3-large`: $0.13 per 1M tokens (6.5x more, same formula applies)

**Vector DB pricing source** ($0.10/1K/month is a mid-range across providers):

| Provider | Plan | Approximate cost | Source |
|---|---|---|---|
| Pinecone | Serverless (s1) | ~$0.08-0.12/1K vectors/mo | [pinecone.io/pricing](https://www.pinecone.io/pricing/) |
| Pinecone | Standard (p1) | ~$0.096/1K vectors/mo | [pinecone.io/pricing](https://www.pinecone.io/pricing/) |
| Qdrant | Cloud | ~$0.085/GB/mo (~$0.05-0.10/1K) | [qdrant.tech/pricing](https://qdrant.tech/pricing/) |
| Weaviate | Cloud | ~$0.095/1K vectors/mo | [weaviate.io/pricing](https://weaviate.io/pricing) |

Vector size: 1536 dimensions (text-embedding-3-small) x 4 bytes = 6,144 bytes/vector,
plus ~2KB metadata per chunk. Self-hosted is cheaper but requires ops overhead.

### Query cost formula

```
annual_query_cost = K x tokens_per_chunk x queries_per_day x 365 x price_per_token

where:
  K                 = estimated retrieval depth to match markcrawl quality (see table)
  tokens_per_chunk  = 300
  price_per_token   = $3.00 / 1M  (Claude Sonnet input, April 2026)
```

**Estimating K per tool:** Markcrawl scores 3.91/5 with K=10. Each tool's K is
scaled proportionally to its chunk ratio: `K = 10 x (tool_chunks / markcrawl_chunks)`,
capped at 15. This reflects needing more chunks to find the same signal in noisier
output. It's a conservative model — the actual relationship between K and quality
is non-linear, and some quality gap may persist regardless of K.

**LLM pricing source:** [Anthropic pricing](https://www.anthropic.com/pricing)
- Claude Sonnet: $3.00 per 1M input tokens
- Claude Opus: $15.00 per 1M input tokens (5x multiplier)
- Claude Haiku: $0.80 per 1M input tokens

### Retrieval degradation at scale (not modeled)

The quality gaps measured at 150 pages likely grow at larger corpus sizes.
More chunks in the vector index = more "distractor" vectors competing for
top-K retrieval slots. Research on dense retrieval shows precision degrades
approximately with log(N).

```
At 1M pages:
  markcrawl:  log2(14.2M) = 23.8 difficulty factor
  scrapy+md:  log2(17.2M) = 24.0  (+1.0% harder)
  crawl4ai:   log2(23.6M) = 24.5  (+2.9% harder)
  crawlee:    log2(29.5M) = 24.8  (+4.2% harder)
  playwright: log2(27.8M) = 24.7  (+3.8% harder)
```

This effect is not captured in our benchmark (which tests ~150 pages) but
would widen quality gaps at production scale.

### What this analysis does NOT include

- **Crawl compute**: markcrawl is 25-40% faster (see [SPEED_COMPARISON.md](SPEED_COMPARISON.md)),
  saving server time, but hard to dollarize without knowing infrastructure.
- **Re-indexing costs**: pages change and need re-embedding; the chunk ratio
  applies to every re-index cycle.
- **Output token costs**: only input tokens are modeled. Output costs are
  roughly equal across tools since answer length is similar.
- **Retrieval compute**: vector similarity search scales with index size.
  Smaller indexes are faster to query (relevant at >10M vectors).
- **Human cost of bad answers**: quality gaps mean some queries produce
  noticeably worse answers. At 1K queries/day, even a 1% gap is 10
  degraded answers daily.
