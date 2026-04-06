# Production RAG Retrieval: Research for Benchmark Design

> Research compiled April 2026. Focused on 2024-2025 findings relevant to benchmarking
> a web crawler's output quality for RAG use cases.

---

## Table of Contents

1. [How Many Chunks Do Production Systems Retrieve?](#1-how-many-chunks-do-production-systems-retrieve)
2. [Retrieval Evaluation Metrics](#2-retrieval-evaluation-metrics)
3. [Reranking in Production RAG](#3-reranking-in-production-rag)
4. [RAG Pipeline Architectures](#4-rag-pipeline-architectures)
5. [Chunk Quality vs Quantity](#5-chunk-quality-vs-quantity)
6. [Standard RAG Benchmarks](#6-standard-rag-benchmarks)
7. [Embedding Models in Production](#7-embedding-models-in-production)
8. [Chunk Size and Overlap](#8-chunk-size-and-overlap)
9. [Implications for Web Crawler Benchmarking](#9-implications-for-web-crawler-benchmarking)

---

## 1. How Many Chunks Do Production Systems Retrieve?

### Framework Defaults

| Framework   | Default top-k | Notes |
|-------------|---------------|-------|
| LlamaIndex  | 5             | `similarity_top_k=5` in default query engine |
| LangChain   | 4             | Default `k=4` in vector store retrievers |

These defaults are starting points. Production systems almost always tune this value.

### Anthropic's Contextual Retrieval Benchmark (2024)

Anthropic's [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) research is the most rigorous public study on top-k values for RAG:

- **Initial retrieval**: Top 150 chunks (broad recall stage)
- **After reranking**: Top 20 chunks passed to the LLM
- **Testing variations**: Tested 5, 10, and 20 chunks; **20 was most effective**
- Passing top-20 chunks to the model proved more effective than using fewer chunks

### Production Patterns

| Stage | Typical K | Purpose |
|-------|-----------|---------|
| Initial embedding retrieval | 20-150 | Maximize recall; fast bi-encoder search |
| After reranking | 3-20 | Maximize precision; slow cross-encoder scoring |
| Passed to LLM | 3-20 | Context window budget vs. answer quality |

**Key insight**: Production systems do NOT use top-1 or top-3 from raw embedding search. They retrieve broadly (high K) and narrow down via reranking.

---

## 2. Retrieval Evaluation Metrics

### Metric Definitions

**Recall@K** -- What fraction of all relevant documents appear in the top-K results?
```
Recall@K = (relevant items in top-K) / (total relevant items)
```
Common K values: 1, 3, 5, 10, 20. Higher K gives higher recall but measures a looser bar.

**Precision@K** -- What fraction of the top-K results are relevant?
```
Precision@K = (relevant items in top-K) / K
```

**MRR (Mean Reciprocal Rank)** -- Average of 1/rank of the first relevant result across queries.
```
MRR = (1/N) * sum(1 / rank_i)
```
Useful when you care about the *first* relevant hit (e.g., single-answer questions).

**MAP (Mean Average Precision)** -- Mean of average precision across queries. Rewards systems that rank *all* relevant items higher. Best for multi-document relevance.

**NDCG@K (Normalized Discounted Cumulative Gain)** -- Accounts for both relevance *and* position, with logarithmic discount for lower-ranked items. Values relevance grades (not just binary relevant/not-relevant).
```
DCG@K = sum(relevance_i / log2(i + 1))
NDCG@K = DCG@K / ideal_DCG@K
```

### Which Metrics Matter Most for RAG?

| Metric | RAG Relevance | When to Use |
|--------|---------------|-------------|
| **Recall@K** | **Critical** | If the relevant chunk isn't retrieved, the LLM can't answer. This is the floor. |
| **NDCG@K** | High | Correlates most strongly with end-to-end RAG quality. Target NDCG@10 > 0.8. |
| **MRR** | Medium | Matters for single-answer factoid questions. Less relevant for synthesis tasks. |
| **MAP** | Medium | Good for evaluating multi-document retrieval scenarios. |
| **Precision@K** | Lower | Less critical because LLMs can filter noise; recall matters more than precision for retrieval. |

### Important Caveat (2025 Research)

Recent research ([arxiv 2510.21440](https://arxiv.org/html/2510.21440v1)) shows that classical IR metrics like NDCG, MAP, and MRR fail to adequately predict RAG performance because they assume monotonically decreasing document utility with rank position. New approaches like **eRAG** score each document based on the quality of the LLM's response when receiving only that document as context, showing better correlation with end-to-end RAG performance.

**Practical finding**: Improving retrieval recall from 80% to 95% may only improve answer quality by 5-10% if the generation model poorly utilizes the retrieved context.

### Recommendation for Crawler Benchmarking

For a web crawler benchmark, **Recall@K** is the right primary metric because:
- It directly measures "did the retrieval system find the right content?"
- It's simple, interpretable, and doesn't require relevance grading
- The crawler's job is to produce content that *can be found* -- downstream reranking handles precision

Measure at multiple K values: **Recall@1, Recall@5, Recall@10, Recall@20**.

---

## 3. Reranking in Production RAG

### Two-Stage Retrieval is Standard

Nearly all production RAG systems in 2024-2025 use a two-stage pipeline:

```
Query --> Bi-encoder retrieval (top-20 to top-150) --> Cross-encoder reranking (top-3 to top-20) --> LLM
```

### Why Two Stages?

- **Bi-encoders** (embedding models): Fast (~1ms per query), but lower precision. Pre-compute document embeddings offline.
- **Cross-encoders** (rerankers): Slow (~10ms per pair), but much higher precision. Score each query-document pair jointly.

You can't run cross-encoders against millions of documents. You *need* the fast first stage.

### Performance Impact

- Reranking improves retrieval precision by **30-50%** in production systems
- Databricks research shows reranking can improve retrieval quality by **up to 48%**
- Anthropic found reranking reduced retrieval failure by **67%** when combined with contextual retrieval

### Popular Reranking Models (2024-2025)

| Model | Parameters | Notes |
|-------|-----------|-------|
| Cohere Rerank v3 | Proprietary | Most widely used commercial reranker |
| BAAI/bge-reranker-v2-m3 | 278M | Best open-weight reranker for English + multilingual |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | 22M | Lightweight, widely used open-source |
| Jina Reranker v2 | 137M | Good balance of speed and quality |

### Latency Budget

- Reranking 50 documents: ~1.5 seconds (Databricks benchmark)
- Reranking 100 documents: should be < 300ms with optimized models
- If reranking exceeds 500ms, reduce the candidate set size

### Implications for Crawler Benchmarking

Since production systems use reranking, the initial retrieval stage's job is **recall, not precision**. A crawler benchmark should therefore:
- Evaluate at **higher K values** (K=10, K=20) to match what rerankers receive
- Not penalize noisy results heavily -- rerankers handle that
- Focus on whether the *correct* chunk is *somewhere* in the top-K

---

## 4. RAG Pipeline Architectures

### The Three Paradigms

#### Naive RAG (2023)
```
Query --> Embed --> Vector Search (top-k) --> Concatenate with query --> LLM --> Response
```
- Fixed retriever (BM25 or single embedding model)
- No query transformation, no reranking
- Suffers from low precision and fragmented context

#### Advanced RAG (2024)
```
Query --> Query Rewriting/Expansion --> Hybrid Search (vector + BM25) --> Reranking --> LLM --> Response
```
- Pre-retrieval: query rewriting, HyDE, multi-query expansion (3-5 reformulations)
- Retrieval: hybrid search combining dense vectors + sparse BM25
- Post-retrieval: cross-encoder reranking, context compression
- This is the standard for "production RAG" in 2025

#### Modular/Agentic RAG (2025)
```
Query --> Router/Planner --> [Retriever | Web Search | SQL | Graph DB] --> Evaluator --> LLM --> Response
                                                                              |
                                                                              v
                                                                    (iterate if low confidence)
```
- Components are swappable modules
- AI agent decides retrieval strategy dynamically
- Iterative refinement: re-retrieve if initial results are insufficient
- Multi-agent architectures for complex queries

### What Most Production Systems Actually Use

The majority of production systems in 2025 are **Advanced RAG** -- hybrid search with reranking. Modular/agentic RAG is growing but still limited to sophisticated teams. Naive RAG persists in prototypes and demos.

### Implications for Crawler Benchmarking

A crawler benchmark should assume the **Advanced RAG** architecture as the target consumer:
- Content will be chunked and embedded
- Both semantic (vector) and keyword (BM25) retrieval will be used
- Reranking will follow initial retrieval
- The crawler's output quality affects every stage: better markdown means better chunks, better embeddings, and better keyword matching

---

## 5. Chunk Quality vs Quantity

### Quality Defines the Ceiling

> "The quality of your text chunking doesn't just set a baseline for your RAG system's performance; it defines the upper limit."

This finding from multiple 2024-2025 studies is the single most important insight for crawler benchmarking.

### Key Research Findings

**Adaptive chunking vs. fixed-size (2025)**:
- Adaptive chunking aligned to logical topic boundaries: **87% accuracy**
- Fixed-size baseline: **13% accuracy**
- This 74-point gap shows that chunk boundary quality is transformative

**Semantic chunking impact**:
- Up to **9% recall improvement** over naive fixed-size splitting
- The wrong strategy creates a **9% recall gap** between best and worst approaches

**Vectara NAACL 2025 study**:
- Fixed-size chunking consistently outperformed semantic chunking on realistic document sets
- Suggests that simple approaches work well when the *input content is clean*

### The Garbage In, Garbage Out Problem

When source content is noisy (navigation elements, ads, boilerplate):
- Chunks contain irrelevant text mixed with useful content
- Embeddings become less accurate (noisy signal)
- Keyword search matches on irrelevant terms
- Reranking can partially compensate, but fundamentally "you can't retrieve what isn't there"

When source content is clean:
- Even simple fixed-size chunking produces good results
- Embeddings capture semantic meaning accurately
- Keyword search matches on substantive terms only
- The entire pipeline performs better

### Implications for Crawler Benchmarking

This is the strongest argument for benchmarking crawler output quality:
1. **Clean content from crawlers --> better chunks --> better embeddings --> better retrieval**
2. No amount of sophisticated RAG engineering compensates for garbage input
3. The crawler is the *first* quality gate in the pipeline
4. A crawler that strips boilerplate, preserves structure, and outputs clean markdown directly improves every downstream stage

---

## 6. Standard RAG Benchmarks

### Retrieval-Focused Benchmarks

**BEIR (Benchmarking-IR)**
- 17 datasets spanning diverse text retrieval tasks
- The standard for evaluating embedding models in IR
- Domains: bio-medical, finance, scientific, web search, etc.
- Primary metric: NDCG@10

**MTEB (Massive Text Embedding Benchmark)**
- 58 datasets, 112 languages, 8 embedding tasks
- Hosted on Hugging Face; incorporates BEIR
- Tasks: retrieval, classification, clustering, reranking, etc.
- The leaderboard for comparing embedding models

### RAG-Specific Benchmarks

**RAGAS (Retrieval Augmented Generation Assessment)**
- Framework for reference-free RAG evaluation
- Four core metrics:
  - **Faithfulness**: Is the response factually consistent with retrieved context? (0-1)
  - **Answer Relevancy**: Is the response relevant to the original query? (0-1)
  - **Context Precision**: Are retrieved documents useful for answering? (0-1)
  - **Context Recall**: Do retrieved documents cover all relevant aspects? (0-1)
- Does not require ground-truth human annotations
- Uses LLM-as-judge to compute metrics

**CRAG (Comprehensive RAG Benchmark) -- KDD Cup 2024**
- Evaluates RAG across diverse domains and question types
- Three tasks with varying access to external sources
- Tests real-world complexity: web pages, knowledge graphs

**RAGBench (2024)**
- Explainable benchmark for RAG systems
- Provides diagnostic information about failure modes

### Other Notable Benchmarks
- LegalBench-RAG: domain-specific legal retrieval
- T2-RAGBench: temporal reasoning in RAG
- WixQA: real production question-answering

### Implications for Crawler Benchmarking

Our crawler benchmark is distinct from these: we're not evaluating the embedding model or the LLM. We're evaluating **content quality at the ingestion stage**. The closest analogy is measuring how the crawler's output affects **Context Recall** (RAGAS) -- does the crawled content, once chunked and embedded, allow the retrieval system to find the right information?

---

## 7. Embedding Models in Production

### Current Landscape (2025-2026)

#### Proprietary

| Model | MTEB Score | Cost (per 1M tokens) | Dimensions | Notes |
|-------|-----------|----------------------|------------|-------|
| Cohere embed-v4 | 65.2 | ~$0.10 | 1024 | Top MTEB; multilingual + multimodal |
| OpenAI text-embedding-3-large | 64.6 | $0.13 | 3072 (variable) | Variable dimensions; can truncate to 256 |
| OpenAI text-embedding-3-small | 62.3 | $0.02 | 1536 | Best cost/performance ratio |
| Voyage AI voyage-3 | ~64 | $0.06 | 1024 | Strong on code and technical content |

#### Open-Source

| Model | MTEB Score | Parameters | Notes |
|-------|-----------|-----------|-------|
| BGE-M3 | 63.0 | 568M | Dense + sparse + multi-vector; MIT license |
| Nomic Embed v1.5 | ~62 | 137M | Fast; good for real-time systems |
| E5-Mistral-7B | ~63 | 7B | LLM-based; high quality but slow |
| all-MiniLM-L6-v2 | ~56 | 22M | Fast baseline for prototyping |

### Practical Recommendations

- **Startup/MVP**: all-MiniLM-L6-v2 (free, fast)
- **Production, quality matters**: Cohere embed-v4 or OpenAI text-embedding-3-large
- **Production, budget matters**: BGE-M3 self-hosted
- **Multilingual**: Cohere embed-v4 or BGE-M3
- **Privacy-critical**: BGE-M3 (MIT license, self-hosted)

### Implications for Crawler Benchmarking

For a crawler benchmark, the choice of embedding model is a **confound** -- we want to measure crawler quality, not embedding model quality. Options:
1. **Use a single standard model** (e.g., OpenAI text-embedding-3-small) for consistency
2. **Test across multiple models** to show crawler quality holds regardless of embedding model
3. **Use the most common production model** for relevance (OpenAI embeddings are dominant)

Our current benchmark uses OpenAI text-embedding-3-small, which is a reasonable default: cheap, widely used, and adequate for measuring relative differences between crawlers.

---

## 8. Chunk Size and Overlap

### Benchmark-Validated Defaults

The current consensus from 2024-2025 benchmarks:

| Parameter | Recommended Default | Range |
|-----------|-------------------|-------|
| Chunk size | **512 tokens** | 256-1024 tokens depending on query type |
| Overlap | **10-20% of chunk size** (50-100 tokens) | Minimum 10%; 15% optimal in FinanceBench |

### NVIDIA 2024 Benchmark Results

Tested 7 chunking strategies across 5 datasets:

| Strategy | Average Accuracy | Std Dev | Notes |
|----------|-----------------|---------|-------|
| **Page-level** | **0.648** | **0.107** | Most consistent across datasets |
| Token-based (512) | 0.645 | 0.12 | Near-equivalent to page-level |
| Token-based (1024) | 0.640 | 0.13 | Better for analytical queries |
| Token-based (256) | 0.620 | 0.15 | Better for factoid queries |
| Token-based (128) | 0.603 | 0.18 | Too fragmented |

### Query-Type Sensitivity

| Query Type | Optimal Chunk Size | Why |
|------------|-------------------|-----|
| Factoid (single fact) | 256-512 tokens | Smaller = more precise signal |
| Analytical (reasoning) | 1024+ tokens | Needs surrounding context |
| Multi-hop (connecting ideas) | Page-level or 1024 | Needs broader context |

### Overlap Matters

- Skipping overlap is the third most common chunking mistake
- Even 10% overlap recovers context lost at chunk boundaries
- 15% overlap performed best on FinanceBench with 1024-token chunks

### Anthropic's Contextual Retrieval Parameters

- Chunk size: **800 tokens**
- Context window prepended to each chunk: **50-100 tokens** (generated by LLM)
- This "contextual chunk" approach reduced retrieval failure by 49-67%

### Implications for Crawler Benchmarking

Our benchmark should use **standard chunking parameters** so results generalize:
- **512 tokens with 10-20% overlap** as the default
- Recursive character splitting (preserves paragraphs and sentences)
- Test at multiple chunk sizes if feasible (256, 512, 1024) to show robustness

The key question for a crawler benchmark: does cleaner crawler output produce better chunks *regardless* of chunk size? If yes, that's a strong signal that crawler quality matters.

---

## 9. Implications for Web Crawler Benchmarking

### The Core Argument

A web crawler sits at the very beginning of the RAG pipeline:

```
Web Page --> Crawler --> Markdown --> Chunker --> Embedder --> Vector DB --> Retriever --> Reranker --> LLM
```

Every downstream component depends on what the crawler produces. Research shows:
1. Chunk quality defines the **ceiling** of RAG performance (Section 5)
2. Clean content makes even simple chunking strategies effective (Vectara NAACL 2025)
3. No amount of reranking compensates for missing content (can't retrieve what wasn't crawled)

### Recommended Benchmark Design

Based on this research, a web crawler retrieval benchmark should:

#### Metrics
- **Primary**: Recall@K at K=5, K=10, K=20
- **Secondary**: MRR (for single-answer queries), NDCG@10 (for graded relevance if available)
- Recall@K is the right choice because the crawler's job is to ensure relevant content *can be found*, not to rank it

#### K Values
- **K=5**: Matches the "what if there's no reranker?" scenario (framework defaults)
- **K=10**: Matches the "modest reranking" scenario
- **K=20**: Matches Anthropic's recommended pipeline (retrieve 150, rerank to 20)
- Reporting at multiple K values shows how sensitive results are to the retrieval budget

#### Chunking Parameters
- **Default**: 512 tokens, 10-20% overlap, recursive character splitting
- This matches the most widely validated configuration
- Consider testing at 256 and 1024 tokens as sensitivity analysis

#### Embedding Model
- Use a single standard model for consistency (OpenAI text-embedding-3-small is reasonable)
- The goal is to measure *relative* differences between crawlers, not absolute retrieval quality

#### What to Measure
1. **Content completeness**: Does the crawled markdown contain the information needed to answer test queries?
2. **Retrieval success**: Once chunked and embedded, can the relevant chunks be found?
3. **Boilerplate impact**: Does navigation/footer/ad content degrade retrieval by polluting chunks?
4. **Structure preservation**: Do headings, lists, and code blocks survive crawling and aid retrieval?

#### Comparison to Existing Benchmarks

| Benchmark | Measures | Our Benchmark Measures |
|-----------|----------|----------------------|
| BEIR/MTEB | Embedding model quality | Crawler output quality |
| RAGAS | End-to-end RAG pipeline | Content quality at ingestion |
| CRAG | RAG system across domains | Crawler across website types |

Our benchmark fills a gap: no existing benchmark measures how the **content extraction step** (crawling) affects downstream retrieval quality.

### Design Decisions Summary

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Primary metric | Recall@K | Matches retrieval stage's job (recall, not precision) |
| K values | 5, 10, 20 | Covers no-reranker to full-pipeline scenarios |
| Chunk size | 512 tokens | Benchmark-validated default; most common in production |
| Overlap | 50-100 tokens (10-20%) | Consensus from NVIDIA and FinanceBench studies |
| Embedding model | OpenAI text-embedding-3-small | Widely used, affordable, adequate for relative comparison |
| Query types | Mix of factoid + analytical | Different chunk sizes favor different query types |

---

## Sources

### Anthropic
- [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) -- Top-k values, retrieval failure rates, contextual chunking

### NVIDIA
- [Finding the Best Chunking Strategy for Accurate AI Responses](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/) -- Chunk size benchmarks across 5 datasets

### Frameworks
- [LlamaIndex: Building Performant RAG for Production](https://developers.llamaindex.ai/python/framework/optimizing/production_rag/) -- Default configurations, optimization strategies
- [Pinecone: Rerankers and Two-Stage Retrieval](https://www.pinecone.io/learn/series/rag/rerankers/) -- Cross-encoder architecture

### Benchmarks and Evaluation
- [RAGAS Documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) -- Metric definitions
- [Weaviate: Retrieval Evaluation Metrics](https://weaviate.io/blog/retrieval-evaluation-metrics) -- Metric comparisons
- [RAGBench](https://arxiv.org/abs/2407.11005) -- RAG system benchmarking
- [Redefining Retrieval Evaluation in the Era of LLMs](https://arxiv.org/html/2510.21440v1) -- eRAG and metric limitations

### Embedding Models
- [Ailog: Best Embedding Models 2025](https://app.ailog.fr/en/blog/guides/choosing-embedding-models) -- MTEB scores and comparisons
- [PremAI: Best Embedding Models for RAG 2026](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/) -- Cost and performance rankings

### Chunking and Quality
- [Firecrawl: Best Chunking Strategies for RAG 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag) -- Strategy comparisons
- [LangCopilot: Document Chunking for RAG](https://langcopilot.com/posts/2025-10-11-document-chunking-for-rag-practical-guide) -- 70% accuracy boost findings

### Architecture
- [MarkTechPost: Evolution of RAGs](https://www.marktechpost.com/2024/04/01/evolution-of-rags-naive-rag-advanced-rag-and-modular-rag-architectures/) -- Naive vs Advanced vs Modular RAG
- [Orq.ai: RAG Architecture Explained 2025](https://orq.ai/blog/rag-architecture) -- Production architecture patterns
- [Ailog: Cross-Encoder Reranking Improves RAG Accuracy by 40%](https://app.ailog.fr/en/blog/news/reranking-cross-encoders-study) -- Reranking impact data

### RAG Evaluation Guides
- [GetMaxim: Complete Guide to RAG Evaluation 2025](https://www.getmaxim.ai/articles/complete-guide-to-rag-evaluation-metrics-methods-and-best-practices-for-2025/) -- Comprehensive metric guide
- [Label Your Data: RAG Evaluation 2026](https://labelyourdata.com/articles/llm-fine-tuning/rag-evaluation) -- Enterprise benchmarks
- [NVIDIA: Evaluating Retriever for Enterprise-Grade RAG](https://developer.nvidia.com/blog/evaluating-retriever-for-enterprise-grade-rag/) -- Enterprise retrieval evaluation
