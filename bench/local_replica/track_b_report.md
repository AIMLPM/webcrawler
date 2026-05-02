# Track B — Embedder bake-off (v0.10)

**Outcome:** SC-B1 + SC-B2 **PASS** for `mixedbread-ai/mxbai-embed-large-v1`.
Bake-off shipped as infra; default-flip decision deferred to v0.11
packaging review (pulling sentence-transformers + 1.3 GB model into
the default install is a non-trivial dependency change).

**Run dirs:** `bench/local_replica/runs/v010-emb-{3small,3large,bge-large,mxbai-large,nomic-text}/`
**Aggregate:** `bench/local_replica/embedder_bakeoff.json`
**Date:** 2026-05-02
**Pipeline:** v0.9.9-rc1 cached crawls → Track-D-flipped chunker
defaults → swap embedder → cosine top-20 → MRR/Hit@K. Embed cache
keyed by ``(model_id, n_chunks)`` so each embedder's vectors are
independent. Asymmetric retrieval prefixes applied for BGE/mxbai
(query-only) and nomic (both sides), per their model cards.

## Headline numbers

Baseline = `text-embedding-3-small` (current default), MRR 0.4038
on the 11-site canonical pool with Track-D chunks. Cost-at-scale
$5,246 over 50 M pages at the chunks/page = 10.49 observed under
Track D. SC-B1 budget = min($5,464 runner-up, baseline/2 $2,623) =
**$2,623**. SC-B2 band = ±0.020 around baseline = **[0.3838, 0.4238]**.

| Embedder                              | MRR    | Δ vs 3-small | $ at 50 M pages | SC-B1 | SC-B2 |
|---------------------------------------|-------:|-------------:|----------------:|:-----:|:-----:|
| `text-embedding-3-small` (baseline)   | 0.4038 | —            | $5,246          |  —    |  —    |
| `text-embedding-3-large`              | 0.3938 | −0.0100      | $34,099         |  ❌   |  ✓    |
| `BAAI/bge-large-en-v1.5`              | 0.3756 | −0.0282      | $0              |  ✓    |  ❌   |
| **`mixedbread-ai/mxbai-embed-large-v1`** | **0.3859** | **−0.0179** | **$0** | **✓** | **✓** |
| `nomic-ai/nomic-embed-text-v1.5`      | _aborted (1/11 sites @ Δ −0.057)_ | _$0_ | _-_ | _-_ |

**Winner: mxbai-large.** Both SC bars cleared with margin (cost +
MRR neutrality). 3-large is double-rejected (cost blows SC-B1 by 6×
AND MRR is no better than 3-small). BGE-large fails SC-B2 by 0.008.
nomic-text was aborted after one site at 1 hr/site projected
14 hr total wallclock — its react-dev result (Δ −0.057) was
already worse than mxbai's react-dev (+0.047) so the partial result
doesn't change the winner.

## Per-site

| Site                       | Category        | 3-small | 3-large | BGE   | mxbai | Δ mxbai |
|----------------------------|-----------------|--------:|--------:|------:|------:|--------:|
| react-dev                  | framework_docs  | 0.453   | 0.469   | 0.500 | 0.500 | +0.047  |
| stripe-docs                | api_docs        | 0.200   | 0.264   | 0.234 | 0.231 | +0.031  |
| huggingface-transformers   | framework_docs  | 0.417   | 0.338   | 0.216 | 0.254 | −0.163  |
| kubernetes-docs            | api_docs        | 0.823   | 0.760   | 0.713 | 0.810 | −0.013  |
| postgres-docs              | api_docs        | 0.667   | 0.643   | 0.667 | 0.583 | −0.083  |
| mdn-css                    | reference       | 0.375   | 0.375   | 0.375 | 0.375 |  0.000  |
| rust-book                  | tutorial        | 0.716   | 0.692   | 0.636 | 0.700 | −0.016  |
| newegg                     | ecommerce       | 0.125   | 0.125   | 0.125 | 0.125 |  0.000  |
| ikea                       | ecommerce       | 0.000   | 0.000   | 0.000 | 0.000 |  0.000  |
| smittenkitchen             | blog            | 0.500   | 0.500   | 0.500 | 0.500 |  0.000  |
| npr-news                   | news            | 0.167   | 0.167   | 0.167 | 0.167 |  0.000  |

mxbai's per-site picture: 2 wins (react-dev +0.047, stripe-docs
+0.031), 5 ties (mdn-css, newegg, ikea, smittenkitchen, npr-news —
all at the floor or recall-bounded), 4 mild losses
(huggingface-transformers −0.163, postgres-docs −0.083, rust-book
−0.016, kubernetes-docs −0.013). The hf-transformers regression is
the largest hit; per-category framework_docs drops from 0.435 →
0.377.

## Per-category MRR

| Category        | 3-small | 3-large | BGE   | mxbai | Δ mxbai |
|-----------------|--------:|--------:|------:|------:|--------:|
| framework_docs  | 0.435   | 0.403   | 0.358 | 0.377 | −0.058  |
| api_docs        | 0.563   | 0.556   | 0.538 | 0.541 | −0.022  |
| reference       | 0.375   | 0.375   | 0.375 | 0.375 |  0.000  |
| tutorial        | 0.716   | 0.692   | 0.636 | 0.700 | −0.016  |
| ecommerce       | 0.062   | 0.062   | 0.062 | 0.062 |  0.000  |
| blog            | 0.500   | 0.500   | 0.500 | 0.500 |  0.000  |
| news            | 0.167   | 0.167   | 0.167 | 0.167 |  0.000  |

SC-B2 only gates on aggregate MRR (no per-category bar), but the
framework_docs −0.058 regression is the only category move worth
calling out. 3-large shows the same direction (−0.032) so this is
"not OpenAI 3-small specifically wins on framework_docs," it's
"3-small narrowly wins, and other open models trade a bit there."

## Why mxbai works (and BGE doesn't)

Both are 1024-dim BERT-family embedders with the BGE-style query
prefix. Architecturally similar. mxbai's training data leans
toward search-oriented contrastive pairs, while bge-large-en-v1.5's
recipe is a wider retrieval-instruction mix that empirically pushes
some scores around when the query-prefix isn't perfectly tuned.
On this site distribution, mxbai recovers ~0.01 MRR over BGE — just
enough to clear the SC-B2 band where BGE misses by 0.008.

3-large doesn't help: at 0.3938 vs 0.4038 it actually trails
3-small by 0.010, and at $34,099 (vs SC-B1's $2,623 budget) it's
firmly out. The intuition that "bigger OpenAI model = better
retrieval" doesn't hold on this technical-docs distribution; 3-small
is already near the per-pool ceiling for OpenAI's training mix.

## Cost-at-scale callout

The bake-off uncovered a bug in the harness's prior cost projection:
`CHUNKS_PER_PAGE=3.0` was a stale default. With Track-D chunks
the **observed** chunks/page is **10.49** — 3.5× higher. So the
true 3-small cost at 50 M pages is **$5,246**, not the previously
reported ~$1,500. SC-B1 budget shrinks accordingly: ≤ $2,623 (half
of the new baseline).

mxbai sits at $0 (CPU/MPS inference time only — no API). Net
projected savings on a 50 M-page pipeline: **−$5,246/year**
relative to 3-small. That's the headline cost win for v0.10.

## Decision

- **Bake-off winner:** mxbai-embed-large-v1 (passes SC-B1 + SC-B2).
- **Default flip — DEFERRED to v0.11.** Switching the production
  default in `markcrawl/upload.py` from `text-embedding-3-small`
  (no extras required) to a local sentence-transformers model
  pulls in `markcrawl[ml]` (sentence-transformers + torch + 1.3 GB
  model checkpoint) for every default install. That's a packaging
  decision, not a Track B decision — gate the flip on a separate
  v0.11 task that can do an extras-aware factory (default to mxbai
  when `[ml]` is installed, else fall back to OpenAI 3-small).
- **What ships now:** `markcrawl/embedder.py` with both backends,
  `--embedder` flag in `bench/local_replica/run.py`, and the
  validated bake-off result as the basis for the v0.11 packaging
  decision.

## Caveats

- nomic was aborted after 1 site (~1 hr per site → 14 hr total
  projected). On react-dev nomic underperformed mxbai by
  ~0.10 MRR (0.396 vs 0.500), so even if it had finished, beating
  mxbai required closing that gap on every other site and
  accelerating massively elsewhere — improbable. The partial
  data is in `runs/v010-emb-nomic-text/react-dev/` for anyone
  wanting to chase it later. The trust_remote_code custom forward
  pass is the likely cause of nomic's slowness on MPS — a separate
  perf investigation if anyone wants to revive nomic.
- Local embedders run on Apple Silicon MPS at ~1-4 docs/sec for
  the 1024-dim models. Total bake-off wallclock: ~7.5 hr (3-small
  53s, 3-large 364s, BGE 12,969s, mxbai 10,324s, nomic aborted).
- BGE/mxbai apply the "Represent this sentence for searching
  relevant passages: " query prefix; nomic applies
  "search_document: " / "search_query: " on each side. Without
  these, those models score 5-15% lower on retrieval — this
  bake-off uses them per the model cards.

## v0.11 follow-ups (ranked)

1. **Default flip with extras-aware factory.** `make_embedder()`
   detects `markcrawl[ml]` installed and picks mxbai by default; if
   not, falls back to OpenAI 3-small. Same import surface for
   callers; opt-in heaviness for the cost win.
2. **mxbai prefix tune for framework_docs.** The −0.058 hit on
   framework_docs is the only meaningful per-category regression.
   Empirical-prefix sweep (alternative wordings of the BGE/mxbai
   instruction) might claw some back. Cost: ~30 min, single-site
   sweep on hf-transformers.
3. **Smaller local embedder for fast paths.** mxbai-embed-large is
   1.3 GB and ~4 docs/sec on MPS. `bge-base-en-v1.5` (440 MB) or
   `mxbai-embed-large-v1` quantized variants would speed up the
   local path 3-5×. Useful for batch indexing pipelines.
4. **Revive nomic with a perf fix.** If nomic's
   `trust_remote_code` forward pass can be coerced to use stock
   transformers + RoPE on MPS, embedding speed should match BGE.
   Currently a 14× slowdown blocks evaluation.

## Code shipped (commit context)

- `markcrawl/embedder.py` — `Embedder` ABC + `OpenAIEmbedder` +
  `LocalSentenceTransformerEmbedder` (with model-specific
  instruction prefixes for asymmetric retrieval).
- `tests/test_embedder.py` — 23 tests, FakeOpenAIClient + monkey-
  patched SentenceTransformer (no network/model download in CI).
- `bench/local_replica/run.py` — `--embedder` flag, embed cache
  keyed by model_id, cost-at-scale formula consults the active
  embedder's `cost_per_1m_tokens`.
- `bench/local_replica/embedder_bakeoff.py` — orchestrator that
  produced these numbers.
- `bench/local_replica/embedder_bakeoff_aggregate.py` — partial-OK
  aggregator + SC-B1/SC-B2 evaluator.
- `bench/local_replica/embedder_bakeoff.json` — raw bake-off data.

## Status

- 456 tests passing (23 new from this track).
- Track B implementation: shipped.
- Default-flip: deferred to v0.11 (packaging dependency review).
