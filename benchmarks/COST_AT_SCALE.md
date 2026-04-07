# RAG Cost Analysis at Scale

How markcrawl's 2x chunk efficiency compounds as corpus size grows.

## Total Annual Cost (markcrawl vs crawlee)

Assumes 1,000 queries/day on Claude Sonnet 4. All costs annualized.

| Pages | MC Chunks | Crawlee Chunks | MC Total/yr | Crawlee Total/yr | Savings/yr | Savings % |
|---|---|---|---|---|---|---|
| 100 | 1,417 | 2,948 | $3,287 | $4,274 | **$987** | 23% |
| 1,000 | 14,173 | 29,480 | $3,302 | $4,306 | **$1,004** | 23% |
| 10,000 | 141,733 | 294,800 | $3,456 | $4,626 | **$1,170** | 25% |
| 100,000 | 1,417,333 | 2,948,000 | $4,994 | $7,826 | **$2,831** | 36% |
| 1,000,000 | 14,173,333 | 29,480,000 | $20,378 | $39,823 | **$19,445** | 49% |

At small scale, LLM query costs dominate and the savings are a flat ~$1K/yr.
At large scale, vector storage dominates and the savings grow linearly with corpus size.

## Cost Breakdown by Category

### Embedding costs (one-time ingestion)

| Pages | markcrawl | crawlee | Savings |
|---|---|---|---|
| 100 | $0.01 | $0.02 | $0.01 |
| 1,000 | $0.09 | $0.18 | $0.09 |
| 10,000 | $0.85 | $1.77 | $0.92 |
| 100,000 | $8.50 | $17.69 | $9.18 |
| 1,000,000 | $85.04 | $176.88 | $91.84 |

Embedding is cheap. Even at 1M pages the difference is under $100.

### Vector database storage (annual)

| Pages | markcrawl | crawlee | Savings/yr |
|---|---|---|---|
| 100 | $2 | $4 | $2 |
| 1,000 | $17 | $35 | $18 |
| 10,000 | $170 | $354 | $184 |
| 100,000 | $1,701 | $3,538 | $1,837 |
| 1,000,000 | $17,008 | $35,376 | **$18,368** |

Storage is the dominant cost at scale and scales linearly with chunk count.
At 1M pages, markcrawl saves $18K/yr on storage alone.

### LLM query costs (annual, 1K queries/day)

| Pages | markcrawl | crawlee | Savings/yr |
|---|---|---|---|
| any | $3,285 | $4,270 | **$986** |

LLM query cost is independent of corpus size (you always retrieve top-K chunks).
The savings come from crawlee needing K=13 instead of K=10 to match markcrawl's
answer quality, sending 30% more context tokens per query.

## Methodology

### Source data

All numbers derive from our benchmark of **92 queries across 8 sites** using
7 crawler tools. Full results in [ANSWER_QUALITY.md](ANSWER_QUALITY.md) and
[RETRIEVAL_COMPARISON.md](RETRIEVAL_COMPARISON.md).

Key measured values:

| Metric | markcrawl | crawlee | Source |
|---|---|---|---|
| Total chunks (8 sites, ~150 pages) | 2,126 | 4,422 | Retrieval benchmark |
| Chunks per page (average) | 14.17 | 29.48 | 2,126 / 150 pages |
| Chunk ratio | 1.0x | 2.08x | 29.48 / 14.17 |
| Answer quality (overall /5) | 3.91 | 3.80 | Answer quality benchmark |
| Quality advantage | +2.9% | baseline | (3.91 - 3.80) / 3.80 |

### Chunk count formula

```
chunks = pages x chunks_per_page

where:
  chunks_per_page(markcrawl) = 14.17   (2,126 chunks / 150 pages)
  chunks_per_page(crawlee)   = 29.48   (4,422 chunks / 150 pages)
```

### Embedding cost formula

```
embedding_cost = chunks x tokens_per_chunk x price_per_token

where:
  tokens_per_chunk = 300          (measured average across benchmark)
  price_per_token  = $0.02 / 1M  (OpenAI text-embedding-3-small, as of April 2026)
```

Pricing source: [OpenAI Embeddings pricing](https://openai.com/pricing)
- `text-embedding-3-small`: $0.02 per 1M tokens
- `text-embedding-3-large`: $0.13 per 1M tokens (6.5x more expensive, same formula applies)

### Vector database storage formula

```
monthly_storage_cost = (chunks / 1,000) x cost_per_1K_vectors_per_month
annual_storage_cost  = monthly_storage_cost x 12

where:
  cost_per_1K_vectors_per_month = $0.10
```

This is a mid-range estimate across managed vector database providers:

| Provider | Plan | Approximate cost | Source |
|---|---|---|---|
| Pinecone | Serverless (s1) | ~$0.08-0.12/1K vectors/mo | [pinecone.io/pricing](https://www.pinecone.io/pricing/) |
| Pinecone | Standard (p1) | ~$0.096/1K vectors/mo | [pinecone.io/pricing](https://www.pinecone.io/pricing/) |
| Qdrant | Cloud | ~$0.085/GB/mo (~$0.05-0.10/1K vectors) | [qdrant.tech/pricing](https://qdrant.tech/pricing/) |
| Weaviate | Cloud | ~$0.095/1K vectors/mo | [weaviate.io/pricing](https://weaviate.io/pricing) |

Vector size assumptions: 1536 dimensions (OpenAI text-embedding-3-small) x 4 bytes (float32) = 6,144 bytes per vector, plus ~2KB metadata overhead per chunk.

Self-hosted storage is cheaper but requires ops overhead. The $0.10/1K/month
figure represents typical managed-service pricing.

### LLM query cost formula

```
annual_query_cost = tokens_per_query x queries_per_day x 365 x price_per_token

where:
  tokens_per_query(markcrawl) = K x avg_chunk_tokens = 10 x 300 = 3,000
  tokens_per_query(crawlee)   = K x avg_chunk_tokens = 13 x 300 = 3,900
  queries_per_day             = 1,000
  price_per_token             = $3.00 / 1M  (Claude Sonnet input pricing)
```

Why K=13 for crawlee: markcrawl scores 3.91/5 answer quality with K=10.
Crawlee scores 3.80/5 with K=10 (2.9% lower). To compensate for noisier
chunks, crawlee needs ~30% more context (K=13) to match markcrawl's
answer quality. This is a conservative estimate — the actual K needed
may be higher, or the quality gap may simply persist regardless of K.

LLM pricing source: [Anthropic pricing](https://www.anthropic.com/pricing)
- Claude Sonnet: $3.00 per 1M input tokens
- Claude Opus: $15.00 per 1M input tokens (5x multiplier on all query costs)
- Claude Haiku: $0.80 per 1M input tokens

### Retrieval degradation at scale

The 2.9% quality gap measured at 150 pages likely grows at larger scales.
With 2x more chunks in the vector index, crawlee has 2x more "distractor"
vectors competing for top-K retrieval slots.

```
difficulty_factor = log2(total_chunks)

At 1M pages:
  markcrawl: log2(14.2M) = 23.8
  crawlee:   log2(29.5M) = 24.8  (+4.2% harder)
```

Research on dense retrieval shows precision degrades approximately with
log(N) as index size grows. This effect is not captured in our benchmark
(which only tests ~150 pages) but would widen the quality gap at scale.

### What this analysis does NOT include

- **Crawl time**: markcrawl is 25-40% faster than crawlee (see [SPEED_COMPARISON.md](SPEED_COMPARISON.md)),
  which saves compute time but is hard to dollarize without knowing infrastructure.
- **Re-indexing costs**: if pages change and need re-embedding, the 2x chunk
  ratio applies to every re-index cycle.
- **Output token costs**: only input tokens are modeled. Output costs are
  roughly equal across tools since answer length is similar.
- **Retrieval compute**: vector similarity search time scales with index size.
  A 2x smaller index is faster to query (relevant at >10M vectors).
- **Human cost of bad answers**: the 2.9% quality gap means ~3 in 100 queries
  produce a noticeably worse answer. At 1K queries/day, that's ~30 degraded
  answers daily.
