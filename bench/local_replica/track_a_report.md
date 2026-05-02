# Track A — Cross-encoder reranker (v0.10)

**Outcome:** SC-A1 **FAILS**. Rerank stays opt-in (`--rerank` flag);
defaults remain cosine-only. Code shipped as infrastructure for
future per-class dispatch experiments.

**Run:** `bench/local_replica/runs/v010-rerank-A/`
**Date:** 2026-05-01
**Pipeline:** v0.9.9-rc1 cached crawls → Track-D-flipped chunker
defaults → text-embedding-3-small → cosine top-20 → cross-encoder
rerank → MRR/Hit@K.

## Headline numbers

| Metric                    | Value      | SC bar          | Pass? |
|---------------------------|-----------:|-----------------|------:|
| Mean MRR (cosine baseline)| 0.4031     | —               |   —   |
| Mean MRR (with rerank)    | 0.3900     | baseline + 0.03 |  ❌   |
| **Rerank lift**           | **−0.0131**| ≥ +0.03         |  ❌   |
| Per-category regressions  | 2 sites    | none > 0.05     |  ❌   |
| Rerank latency mean       | 241.7 ms   | ≤ 100 ms        |  ❌   |
| Rerank latency p95        | 353.1 ms   | ≤ 100 ms        |  ❌   |

Both SC-A1 (MRR) and SC-A2 (latency) fail.

## Per-site

11-site canonical pool, Track-D chunking on, OpenAI 3-small embedder,
top-K = 20 for both stages. Reranker:
`cross-encoder/ms-marco-MiniLM-L-6-v2`.

| Site                       | Category        | Baseline | Rerank | Δ        |
|---------------------------|-----------------|---------:|-------:|---------:|
| huggingface-transformers   | framework_docs  | 0.417    | 0.333  | **−0.083** |
| ikea                       | ecommerce       | 0.000    | 0.000  | 0.000    |
| kubernetes-docs            | api_docs        | 0.823    | 0.844  | +0.021   |
| mdn-css                    | reference       | 0.375    | 0.281  | **−0.094** |
| newegg                     | ecommerce       | 0.125    | 0.125  | 0.000    |
| npr-news                   | news            | 0.167    | 0.167  | 0.000    |
| postgres-docs              | api_docs        | 0.667    | 0.667  | 0.000    |
| react-dev                  | framework_docs  | 0.453    | 0.422  | −0.031   |
| rust-book                  | tutorial        | 0.708    | 0.777  | **+0.069** |
| smittenkitchen             | blog            | 0.500    | 0.500  | 0.000    |
| stripe-docs                | api_docs        | 0.200    | 0.175  | −0.025   |

Two sites benefit (rust-book +0.069, kubernetes-docs +0.021), four
regress (mdn-css and huggingface-transformers regress beyond the SC
0.05 threshold), five are tied.

## Per-query — where rerank actually moves rank

Across the 104 canonical queries:

| Outcome                          | Queries  | %    |
|---------------------------------|---------:|-----:|
| Miss in both (recall ceiling)    | 55       | 53%  |
| Retrieved & unchanged by rerank  | 34       | 33%  |
| Rerank improves rank             | 6        |  6%  |
| Rerank worsens rank              | 9        |  9%  |

**Reads:** the dominant failure is recall (53% of queries don't have
the answer in the cosine top-20 at all — rerank cannot fix those).
Among queries where the answer **is** in the candidate pool, rerank
flips ~30% of them — and the flips are net negative (9 worse vs 6
better). The single largest improvement was on rust-book (a query
moved from rank 6 to rank 1); the single largest regression was also
on rust-book (a query moved from rank 1 to rank 11) — net rust-book
still gained because two other queries improved, but the dispersion
is real.

## Why it doesn't work here

The default reranker (`ms-marco-MiniLM-L-6-v2`) is trained on
MS-MARCO, a web-QA corpus where queries are short natural-language
questions matched against passage prose. The canonical pool here is
heavily technical:

- **api_docs / framework_docs / reference** — chunks are dense with
  code, signatures, headings, and short imperative descriptions. The
  cross-encoder's pretraining bias toward "natural prose" lets it
  promote linguistically fluent but topically wrong passages over
  the correct (terser) ones. Three of four regressions are in these
  categories.
- **tutorial** (rust-book) — narrative prose; matches the model's
  training distribution. This is the only category with a robust
  win.

This matches a known result in the rerank literature: out-of-domain
cross-encoders frequently underperform a strong first-stage retriever
on specialized technical corpora unless fine-tuned.

## Latency

Even ignoring MRR, SC-A2 (≤100 ms/query at K=20) is missed by 2.4×
on dev hardware (M-series Mac, CPU). Cross-encoder forward passes
are ~12 ms each on this CPU; K=20 → ~240 ms, matching the measured
241.7 ms mean. The spec's "<50 ms" estimate assumed a tighter
batch/prefill regime than `sentence_transformers.CrossEncoder`
delivers in practice.

## Decision

- **Defaults stay cosine-only.** `--rerank` remains an opt-in flag
  on `bench/local_replica/run.py`. `markcrawl/retrieval.py` ships as
  infrastructure (with tests) but is not wired into
  `markcrawl/upload.py` or any production path.
- **No regression risk to v0.10.** The chunker defaults flip from
  Track D is the v0.10 MRR change; Track A produces no functional
  default change.

## v0.11 follow-ups (ranked by EV)

1. **Per-class rerank dispatch.** Rerank only on tutorial-class
   sites (where the +0.069 lift held). Use `markcrawl/site_class.py`
   classifier — same pattern v0.9.7 uses for chunker dispatch.
   Estimated lift: +0.005 to +0.01 aggregate (1-2 sites benefit, no
   regressions).
2. **Recall fix before rerank.** 53% of queries miss the answer in
   top-20 entirely; chunking, embedder, or crawl coverage is the
   real lever for those. Track B (embedder bake-off) and Track C
   (ecom resilience) target the recall ceiling directly.
3. **Different reranker model.** Try `bge-reranker-base` or
   `mxbai-rerank-large` on the same harness. Both are
   technical-corpus-friendlier per published evals. Cost: 1 hour +
   ~$0 (CPU inference).
4. **K_retrieve > K_final.** Retrieve top-50 from cosine, rerank to
   top-20. Lets rerank promote rank-21–50 hits into the visible
   window; needs a recall-vs-rank profile to confirm there are
   enough retrievable answers in the rank-21–50 band to matter.
5. **Latency budget review.** If rerank ever does land, the spec's
   100 ms/query is not realistic for K=20 on CPU with current
   open-source cross-encoders; either revise the budget or restrict
   to GPU-only deployments.

## Code shipped (commit context)

- `markcrawl/retrieval.py` — `CrossEncoderReranker` class, lazy
  model load, public re-export from `markcrawl/__init__.py`.
- `tests/test_retrieval_rerank.py` — 14 tests, all passing without
  network or model download (FakeModel-injected).
- `bench/local_replica/run.py` — `--rerank` and `--rerank-model`
  flags. `score_site` now emits both baseline and rerank MRR in a
  single pass when rerank is enabled. Per-site latency
  (mean/p95) tracked.
- 433 tests pass (was 419 pre-Track-A).
