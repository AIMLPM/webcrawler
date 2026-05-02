---
spec_version: 2
name: v0.10 Leaderboard Sweep — Reranker + Embedder Swap + Ecom Resilience
status: draft
size: XL
date: 2026-04-30
branch: feature/v010-leaderboard-sweep
depends_on:
  - "v0.9.9-rc1 tagged and merged to main (this spec assumes v0.9.9 baseline)"
affected_code:
  - markcrawl/retrieval.py            # new — reranker stage
  - markcrawl/embedder.py             # new — embedder abstraction with cost-aware default
  - markcrawl/core.py                 # ecom resilience hooks (retry-with-jitter, anti-bot UA rotation)
  - markcrawl/extract.py              # ecom product-page extractor
  - bench/local_replica/run.py        # rerank/embedder flags + per-category breakouts
  - bench/local_replica/sites_rotated.yaml  # new — rotated pool with queries (deferred from v0.9.9)
  - bench/local_replica/queries_rotated/    # new — per-rotated-site query sets
constitution_reviewed: false
---

# v0.10 Leaderboard Sweep — Reranker + Embedder Swap + Ecom Resilience

## Problem Statement

v0.9.9-rc1 defends markcrawl's 1st-place speed and ships the M6 dispatch
cascade, but leaves the leaderboard's **MRR gap** (we sit at ~0.59, crawlee
0.71) and **cost-at-scale** column (formula favors cheaper embedders we
haven't switched to yet) substantially open. v0.9.9's per-category
breakdown shows two categorically broken site classes that drag the
aggregate MRR down: **ecommerce** (newegg/ikea at 0.062 mean — 90%
under our other categories) and **news** (npr at 0.167). The
single-category misses cost more in the aggregate column than incremental
gains in the categories we already win.

The next public benchmark run is the visible test of v0.9.9 + this work.
**Four** high-leverage moves can plausibly take us from "1st speed, 5th
MRR" to **leading every column**:

1. **Chunk-size + overlap sweep (NEW Track D)** — public benchmark v2.0
   shows markcrawl chunks at avg **83 words** vs crawlee/playwright/
   colly at **252-259 words** (3× smaller). Our heading-driven splitter
   creates a chunk per ``##`` regardless of size. Smaller chunks have
   less retrieval context, especially on the **conceptual** category
   (markcrawl 0.407 vs crawlee 0.705) and **cross-page** (markcrawl
   0.000 vs everyone else 0.750). This is the single largest MRR gap
   driver and is fixable with chunker-only changes — no retrieval
   stage change needed. Sweep `(target_words × overlap_pct × strategy)`
   on cached crawls (autoresearch pattern: fixed metric, fast
   iteration, TSV-logged) to find the chunk shape that closes the gap.
2. **Cross-encoder reranker** on top retrieval candidates — a literature-
   well-established +0.05 to +0.10 MRR lift that **compounds across all
   categories** (text-strong AND text-weak). Additive on top of Track D's
   chunk-shape fix.
3. **Cheaper-and-equivalent embedder** — switch from
   `text-embedding-3-small` to a comparable open-source embedder
   (`BAAI/bge-large-en-v1.5` or `mixedbread-ai/mxbai-embed-large-v1`)
   running locally to halve or zero the cost-at-scale column without
   regressing MRR. Local inference = cost is GPU/CPU time, not API $.
4. **Ecommerce Playwright resilience** — diagnose newegg/ikea failure
   modes (likely a mix of anti-bot blocks + product-page extractor
   gaps) and ship targeted patches: UA rotation, retry-with-jitter,
   product-schema-aware extraction. Goal: lift ecom mean from 0.062
   to ≥0.30 (5×). This is the per-category fix that unlocks the
   aggregate.

**Out of scope:** answer-quality scoring (still future), public
benchmark methodology changes, deep-RL retrieval (out of band for the
schedule), site-specific hardcoded rules.

## Solution Summary

Four parallel tracks, joined at a single final-validation phase. Each
track is independently shippable; the joint validation gates the
v0.10-rc1 tag. **Track D runs first** because the chunker substrate it
produces (better chunk shape) propagates to every other track's MRR
measurement.

- **Track D (chunker, FIRST) — ✅ DONE 2026-05-01.** Autoresearch-style
  sweep across 56 configs (5 phases) on cached v0.9.9-rc1 crawls. New
  `min_words` parameter merges consecutive heading-driven small chunks
  toward a target size; new `section_overlap_words` parameter prefixes
  each chunk with the trailing N words of the previous chunk for
  boundary-recall safety. Both default to 0 (backward-compatible with
  v0.9.9). **Winner verified across 6 cached trial runs and on OpenAI
  3-small (production embedder):**

  ```python
  chunk_markdown(text,
      max_words=400,            # unchanged
      min_words=250,            # NEW
      section_overlap_words=40, # NEW
      strip_markdown_links=True, # NEW
  )
  ```

  Multi-trial median lift over baseline-v099:
  - st-mini, 6 trials: +0.0476 MRR (+14.0%, all 6 trials positive)
  - OpenAI 3-small, 3 trials: +0.0511 MRR (+15.2%, all 3 positive)

  Per-category gains (OpenAI 3-small): js-rendered +100%,
  code-example +71%, api-function +23%, conceptual +12%. Per-site:
  rust-book +0.31, kubernetes-docs +0.11, stripe-docs +0.07,
  react-dev +0.06, mdn-css +0.04, no real regressions.

  Cherry-pick ceiling (per-site dispatcher upper bound across 32
  configs): 0.4343 MRR = +24.4% over baseline. The single-config
  winner captures ~63% of that ceiling.

  Full report: [`bench/local_replica/track_d_report.md`](../bench/local_replica/track_d_report.md).
  Sweep results TSV: `bench/local_replica/chunk_sweep_results.tsv`.

- **Track A (reranker) — ❌ FAILED 2026-05-01.** Cross-encoder rerank
  stage implemented (`markcrawl/retrieval.py`, `--rerank` on the
  harness). Validated on the 11-site canonical pool using Track D's
  chunk shape: **mean MRR regressed −0.0131** (0.4031 → 0.3900) vs
  the SC-A1 bar of +0.030; two categories regressed beyond the SC
  threshold (mdn-css −0.094, huggingface-transformers −0.083); only
  rust-book (tutorial) gained robustly (+0.069). Latency at K=20
  averaged 241.7 ms/query on dev-laptop CPU vs the SC-A2 budget of
  100 ms. **Decision:** rerank stays opt-in (off by default); ms-marco
  cross-encoder bias toward natural-language prose hurts technical
  api-docs/reference content. Code retained as infrastructure for
  v0.11 per-class dispatch (rerank tutorial-class only) and alternate
  reranker models. Full report:
  [`bench/local_replica/track_a_report.md`](../bench/local_replica/track_a_report.md).

- **Track B (embedder) — ✅ PARTIAL DONE 2026-05-02.** Embedder ABC
  shipped (`markcrawl/embedder.py`, OpenAI + Local backends with
  asymmetric retrieval prefixes); `--embedder` flag on the harness;
  bake-off run on the 11-site canonical pool against 4 embedders (5th,
  nomic, aborted at 1/11 sites because `trust_remote_code` MPS forward
  pass projects 14 hr per embedder — its react-dev result was already
  worse than mxbai's). **Bake-off winner: `mixedbread-ai/mxbai-embed-
  large-v1` — 0.3859 MRR (Δ −0.0179 vs 3-small 0.4038), $0 cost at
  scale.** Passes SC-B1 (≤ $2,623 budget) and SC-B2 (within ±0.020
  band). 3-large fails SC-B1 (cost 6× over) AND ties on MRR; BGE-large
  fails SC-B2 by 0.008. The bake-off also corrected a stale
  `CHUNKS_PER_PAGE=3.0` constant in cost projection — observed under
  Track-D chunks is 10.49, so the real 3-small cost at scale is $5,246
  (not ~$1,500 as historically reported); mxbai net savings on a 50 M-
  page pipeline is **−$5,246/year**. **Default-flip deferred to v0.11**
  pending an extras-aware factory (`markcrawl[ml]` adds
  sentence-transformers + 1.3 GB model — too heavy for the default
  install). Full report:
  [`bench/local_replica/track_b_report.md`](../bench/local_replica/track_b_report.md).

- **Track C (ecom resilience)** — diagnose newegg/ikea via the
  `bench/local_replica/run.py` already-saved pages.jsonl from
  v0.9.9-rc1: which pages got crawled, how much markdown was
  extracted, what the queries asked vs what the chunks contain. Ship
  targeted fixes (UA rotation in Playwright, retry-on-empty,
  product-schema extractor) and validate against newegg/ikea + 3-5
  fresh ecom sites for non-overfit.

- **Cross-track final** — combined run with Track D's chunk shape +
  reranker + new embedder + ecom patches. Verify all 4 leadership-
  dimension columns improve vs v0.9.9-rc1 and that the per-category
  broken classes (cross-page, conceptual) recover.

## Success Criteria

- **SC-A1 — Reranker MRR lift.** **Given** the v0.9.9-rc1 retrieval
  pipeline as a baseline, **When** the reranker is enabled with K=20
  candidates, **Then** mean MRR across the canonical 11-site pool is
  **≥ baseline + 0.03** with no per-category regression > 0.05.
- **SC-A2 — Reranker latency budget.** **Given** the reranker enabled,
  **When** a single query is scored end-to-end (embed → top-K → rerank),
  **Then** added wallclock per query is **≤ 100 ms** at K=20 on the
  reference dev hardware.
- **SC-B1 — Embedder cost knee.** **Given** the new embedder selected
  by Track B, **When** the cost-at-scale formula is computed for 50M
  pages, **Then** it is **≤ runner-up ($5,464) AND ≤ v0.9.9-rc1 / 2**.
- **SC-B2 — Embedder MRR neutrality.** **Given** the same retrieval
  pipeline, **When** the embedder is swapped, **Then** mean MRR
  changes by **≤ 0.02 absolute** (we will not trade quality for cost).
- **SC-C1 — Ecommerce MRR floor.** **Given** the canonical newegg + ikea
  + 3 fresh ecom sites, **When** v0.10 is run, **Then** mean ecom MRR
  is **≥ 0.30** (currently 0.062) without any single-site < 0.10.
- **SC-C2 — Ecom crawl completion.** **Given** the canonical ecom sites,
  **When** v0.10 is run, **Then** **≤ 20%** of pages return < 50
  extracted words (currently 38% on newegg).
- **SC-D — Joint validation.** **Given** the final v0.10-rc1 build with
  all 3 tracks landed, **When** `bench/local_replica/run.py --label
  v010-rc1 --auto-scan --rerank --full-report` is run, **Then** all
  4 leadership dimensions improve vs v0.9.9-rc1 AND mean MRR is **≥
  0.65** AND no per-category MRR regression > 0.05.
- **SC-E — SC-7 carry-forward.** **Given** the deferred-from-v0.9.9
  rotated pool with queries authored, **When** `--rotated-pool
  --rotated-sample 30` is run, **Then** mean MRR ≥ 0.55 AND mean p/s
  ≥ 8 (the original v0.9.9 SC-7 target, now testable).

## Flow

Three parallel tracks. A and B are independent; C runs in parallel and
is its own diagnostic-then-fix loop. Final validation joins.

```
[Phase 0]  Branch from v0.9.9-rc1
                  │
                  ├─── Track A: Reranker ────────────────────┐
                  ├─── Track B: Embedder swap ───────────────┤
                  ├─── Track C: Ecom resilience ─────────────┤
                  └─── Track R: Author rotated-pool queries ─┤
                                                             │
                                                             ▼
                                              [Phase 1]  Joint validation
                                                             │
                                                             ▼
                                                v0.10-rc1 tag + push to CI
```

**Parallel discipline:** each track lands its own commits + tests. The
joint validation runs only after all three tracks' SC pass in isolation.
If any track fails its SC, the track is held; the others can still ship
under v0.10.x point releases.

## Detailed Steps

### Track A — Cross-encoder reranker

#### DS-A1: Profile current retrieval ceiling
- [x] Status: done (subsumed into DS-A3 — the validation run emits both
      cosine and rerank ranks per query, which gives the same recall/
      rank pivot directly).
  - **Output:** Per-query rank distribution in `runs/v010-rerank-A/<site>/
    report.json`. Aggregate: 53% of queries (55/104) miss top-20 entirely
    (recall-bounded, not rerank-fixable); 33% retrieved but unchanged by
    rerank; 6% improved; 9% worsened.

#### DS-A2: Implement rerank stage — ✅ done 2026-05-01
- [x] `markcrawl/retrieval.py` with `CrossEncoderReranker` (lazy
      model load, default `cross-encoder/ms-marco-MiniLM-L-6-v2`),
      re-exported from `markcrawl/__init__.py`.
- [x] `bench/local_replica/run.py` — `--rerank` and `--rerank-model`
      flags; `score_site` emits both baseline and rerank metrics +
      per-site latency in a single pass.
- [x] `tests/test_retrieval_rerank.py` — 14 tests, FakeModel-injected
      so no network/model download in CI.

#### DS-A3: Validate on canonical pool — ❌ failed 2026-05-01
- [x] Run executed: `bench/local_replica/runs/v010-rerank-A/`. Mean MRR
      lift **−0.0131** (need ≥+0.030); two per-category regressions
      beyond the SC threshold; latency 241.7 ms / query mean (budget
      100 ms). **Decision:** rerank stays opt-in; defaults unchanged.
      Full analysis + v0.11 follow-ups in
      [`bench/local_replica/track_a_report.md`](../bench/local_replica/track_a_report.md).

### Track B — Embedder swap

#### DS-B1: Embedder bake-off — ✅ done 2026-05-02
- [x] Ran 4 of 5 candidates on the canonical pool with cached
      crawls + Track-D chunks; nomic-text aborted at 1/11 sites
      (trust_remote_code MPS forward pass too slow — 14 hr projected,
      and its single-site result was already worse than mxbai's).
- [x] Output: `bench/local_replica/embedder_bakeoff.json` +
      `bench/local_replica/track_b_report.md`. Per-embedder MRR,
      per-category breakdown, SC-B1/B2 evaluation, cost-at-scale
      with the corrected `chunks_per_page=10.49` Track-D number.

#### DS-B2: Embedder abstraction + ship default — ✅ partial done 2026-05-02
- [x] `markcrawl/embedder.py` with `Embedder` ABC + `OpenAIEmbedder`
      + `LocalSentenceTransformerEmbedder` (with model-specific
      instruction prefixes for asymmetric retrieval). 23 tests,
      FakeOpenAIClient + monkey-patched SentenceTransformer.
- [x] `--embedder` flag on `bench/local_replica/run.py`; embed cache
      keyed by model_id; cost-at-scale consults active embedder.
- [ ] **Default flip deferred to v0.11.** Switching production
      default from `text-embedding-3-small` to a local
      sentence-transformers model pulls `markcrawl[ml]` (1.3 GB
      model checkpoint + torch) into the default install. Needs an
      extras-aware factory: pick mxbai when `[ml]` is installed,
      else fall back to OpenAI 3-small. That's a packaging change,
      not a Track B decision.

#### DS-B3: Validate joint MRR neutrality — ✅ done 2026-05-02
- [x] Bake-off table at `track_b_report.md` confirms mxbai-embed-
      large-v1 PASSES SC-B1 (cost $0 ≤ $2,623 budget) and SC-B2
      (Δ −0.0179 within ±0.020 band). BGE-large fails SC-B2 by
      0.008; 3-large fails SC-B1 by 13×. nomic-text aborted.

### Track C — Ecommerce resilience

#### DS-C1: Diagnose newegg + ikea failure modes
- [ ] Status: pending
  - **What:** Read v0.9.9-rc1 cached crawls for newegg + ikea. For each:
    (a) which pages got `pages.jsonl` entries vs were dropped, (b)
    extracted-word distribution, (c) HTTP status codes from the log,
    (d) which queries' answer-URLs were never crawled.
  - **Output:** `bench/local_replica/ecom_diagnosis.md` — root-cause
    breakdown per site (anti-bot rate, extraction failure, missing
    URL coverage).
  - **Failure mode:** If root cause is solely server-side anti-bot
    (e.g. 429 every 5th request), document and pivot to a single
    targeted patch (retry-with-backoff) rather than a full extractor
    rewrite.

#### DS-C2: Implement targeted resilience patches
- [ ] Status: pending
  - **What:** Based on DS-C1, ship one or more of:
    1. Playwright user-agent rotation pool (`markcrawl/core.py` +
       browser context override).
    2. Retry-on-empty-extract (3× with exponential jitter, capped at
       2× per-page time budget).
    3. Product-schema-aware extractor in `markcrawl/extract.py`
       (detect JSON-LD `Product`, prefer schema fields over scraped
       text for product pages).
    4. Per-class chunking override for ecom (smaller chunks, since
       product specs are dense).
  - **Output:** Commits per patch with isolated tests.
  - **Test:** `tests/test_extract_product_schema.py`,
    `tests/test_ecom_retry.py`.
  - **Failure mode:** Each patch must show isolated MRR lift on at
    least newegg or ikea before bundling. No patch that doesn't move
    the metric ships.

#### DS-C3: Generalization on fresh ecom sites
- [ ] Status: pending
  - **What:** Pick 3-5 fresh ecom sites (not in canonical or DS-4
    pools). Author 5-8 queries each. Run v0.10 + reranker + new
    embedder + ecom patches end-to-end. Verify SC-C1 + SC-C2.
  - **Output:** `bench/local_replica/sites_ecom_fresh.yaml` +
    `queries_rotated/<site>.json`. Comparison report.
  - **Failure mode:** If the canonical newegg/ikea recover but fresh
    sites do not, the patches are overfit. Generalize or document the
    constraints under which the patches hold.

### Track R — Author rotated-pool queries (carries forward v0.9.9 SC-7)

#### DS-R1: Curate ~30 rotated sites with queries
- [ ] Status: pending
  - **What:** Pick 30 sites from `bench/local_replica/sites_scrape_evals.yaml`
    + `sites_hand_curated.yaml` that are (a) reachable, (b) text-rich,
    (c) representative of the 6 url_classes (5 each). For each, author
    5-8 queries with `expected_url_contains` ground truth.
  - **Output:** `bench/local_replica/sites_rotated.yaml` with the 30
    sites + `bench/local_replica/queries_rotated/<slug>.json` per site.
  - **Test:** Smoke test that all queries load + at least one query
    per site has a hit in the existing v0.9.9 cached crawl (sanity).
  - **Failure mode:** Authoring queries is the bottleneck. If 30 is
    too many for one campaign, ship 15 with a per-class minimum of 2.

### Cross-track — Joint validation

#### DS-D1: Joint v0.10-rc1 run on canonical pool
- [ ] Status: pending
  - **What:** Run `bench/local_replica/run.py --label v010-rc1
    --auto-scan --rerank --embedder <chosen> --full-report
    --max-wallclock-per-site 600`. Compare to v0.9.9-rc1.
  - **Output:** `bench/local_replica/v010_release_report.md` with
    side-by-side comparison via `compare_runs.py`.
  - **SC gate:** SC-D + per-track SCs must all pass before tagging.

#### DS-D2: Rotated-pool SC-7 evaluation
- [ ] Status: pending
  - **What:** Now that DS-R1 has shipped queries, run
    `--rotated-pool --rotated-sample 30 --rerank --embedder <chosen>`.
    Verify SC-E (which is the original v0.9.9 SC-7).
  - **Output:** Update to `v010_release_report.md` with SC-E results.

#### DS-D3: Tag v0.10-rc1 + push
- [ ] Status: pending
  - **What:** All SC pass → `git tag v0.10-rc1`, push branch + tag.
    Trigger public CI benchmark run.
  - **Output:** Tag + release notes draft.

## Edge Cases

- **Reranker is GPU-bound on small machines.** The default model is
  CPU-friendly but cold-start import of `sentence_transformers + torch`
  is multi-second. Mitigation: lazy-import on first rerank call; cache
  the loaded model across queries via module-level singleton; document
  the cold-start tax in REPLICA.md.

- **Local embedder breaks reproducibility across machines.** Different
  GPU/CPU may yield slightly different float outputs (non-deterministic
  reductions). Mitigation: pin embedding model version; assert
  deterministic-mode in tests; accept ±0.001 cosine similarity drift
  cross-machine and document.

- **Ecom anti-bot evolves faster than our patches.** Newegg/ikea may
  refresh their bot detection between v0.10 ship and the public CI
  run, regressing our gains. Mitigation: SC-C2 measures *crawl
  completion* not just MRR, so we'll detect regressions in the
  replica before public CI; per-site patches accept eventual decay
  and we re-run the diagnosis loop quarterly.

- **Reranker hides retrieval bugs.** If we rely on rerank to fix
  retrieval, we never fix recall problems at the embedding/chunking
  layer. Mitigation: SC-A1's per-category cap (no >0.05 regression)
  forces the embedding layer to stay competitive; rerank is additive,
  not a crutch.

- **MRR mean improves but median drops.** A reranker that helps
  high-recall sites hugely and hurts low-recall sites slightly will
  show this pattern. Mitigation: report mean *and* median in
  `v010_release_report.md`; require both to move favorably.

## Artifacts / Output

```
markcrawl/
├── retrieval.py                   # NEW — reranker + retrieval pipeline
├── embedder.py                    # NEW — embedder abstraction
└── extract.py                     # MODIFIED — product-schema extractor

bench/local_replica/
├── recall_vs_rank.json            # NEW — DS-A1 output
├── embedder_bakeoff.json          # NEW — DS-B1 output
├── ecom_diagnosis.md              # NEW — DS-C1 output
├── sites_ecom_fresh.yaml          # NEW — DS-C3 input
├── sites_rotated.yaml             # NEW — DS-R1 output (carries v0.9.9 SC-7)
├── queries_rotated/               # NEW — per-rotated-site queries
└── v010_release_report.md         # NEW — DS-D1 output

specs/
└── v010-leaderboard-sweep.md      # this file
```

## Technical Decisions

| decision | choice | rationale |
|---|---|---|
| Reranker model | `cross-encoder/ms-marco-MiniLM-L-6-v2` | 22M params, MS-MARCO-trained, ~50ms/query CPU. Strong general retrieval reranker; widely benchmarked on BEIR; CPU-friendly default avoids forcing GPU on dev machines. |
| Reranker default | `--rerank` opt-in initially | Validate on canonical first; flip default to True after ≥1 leaderboard cycle confirms gain transfers to public CI. |
| Embedder candidates | OpenAI 3-small/3-large + 3 open-source | Covers cost extremes; 3-small is incumbent, 3-large is "go big or go home", BGE/mxbai/nomic are strong open competitors. |
| Embedder default if tied | local sentence-transformers | Cost-at-scale wins by 2 orders of magnitude when embedding is local; MRR neutrality (SC-B2) ensures we don't trade quality. |
| Ecom strategy | targeted patches over rewrite | Newegg + ikea each have specific failure modes (DS-C1 will name them). Targeted patches are cheaper to ship and easier to evaluate than a generalized resilience layer. |
| Track parallelism | three independent | Tracks share retrieval-pipeline edits (A, B) and crawl-pipeline edits (C); coordinated via `markcrawl/retrieval.py` interface. Joint validation gates the tag, not individual ship decisions. |

## Cost / Performance

| item | provider | paid via | estimated cost |
|---|---|---|---|
| Reranker model download | HuggingFace | free | $0 (one-time ~85MB) |
| Reranker CPU inference per validation run | local | none | $0 |
| Embedder bake-off — OpenAI 3-small | OpenAI | API | $0.02 (covered by v0.9.9 cache reuse) |
| Embedder bake-off — OpenAI 3-large | OpenAI | API | ~$0.08 (1 full canonical pool) |
| Embedder bake-off — local models | local | none | $0 (CPU minutes) |
| Local embedder dependency install | local | none | $0 (~2GB disk) |
| Ecom diagnosis (no new crawls) | local | none | $0 (cached crawls) |
| Ecom validation crawls (3-5 fresh sites) | local | none | $0 |
| Joint validation (canonical + rotated) | OpenAI rerank? | API + local | ~$0.30 |
| **Total v0.10 campaign cost** | | | **~$0.50, ~6-10 hours wallclock** |

Recurring at-scale economics post-ship: switching to a local embedder
takes the cost-at-scale dimension from ~$10K/50M-pages (current OpenAI
3-small estimate) to ~$200/50M-pages (electricity for CPU inference).
**That's the dimension column win.**

## Risk Assessment

| risk | likelihood | impact | mitigation |
|---|---|---|---|
| Reranker lift doesn't transfer from local replica to public CI | low | medium | reranker is model-only, no machine-specific behavior; replica accuracy is high for retrieval metrics |
| Local embedder MRR is 0.03+ below OpenAI on some category | medium | medium | SC-B2 caps MRR loss at 0.02; if violated, document and stay on OpenAI 3-large |
| Ecom anti-bot resists all targeted patches | medium | high | SC-C1 floor is 0.30 (5× current 0.062), achievable even with partial fix; document residual gap, ship anyway |
| Reranker latency overhead breaks pipeline-timing column | low | medium | SC-A2 caps at 100ms/query; degrade gracefully to top-K without rerank if needed |
| Joint integration breaks one of the three tracks | medium | high | each track lands with its own SC; joint validation is gate, not sequential dependency; if joint fails, ship best-of-three under v0.10.x point releases |
| Rotated-pool query authoring is the bottleneck | high | low (schedule slip only) | DS-R1 has explicit fallback to 15 sites with 2-per-class minimum |
| Embedder swap silently changes chunking economics | low | low | embedder_bakeoff.json captures chunks/page per embedder; cost formula uses observed chunks/page so the comparison stays honest |

## Evidence

| ID | claim | files | build | test suite | result |
|---|---|---|---|---|---|
| V-A1 | SC-A1 (rerank +0.03 MRR) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-A2 | SC-A2 (rerank ≤100ms/query) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-B1 | SC-B1 (cost ≤ runner-up / 2) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-B2 | SC-B2 (MRR neutrality ±0.02) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-C1 | SC-C1 (ecom MRR ≥0.30) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-C2 | SC-C2 (ecom completion ≥80%) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-D | SC-D (joint all 4 dims improve) | _pending_ | _pending_ | _pending_ | _pending_ |
| V-E | SC-E (rotated-pool MRR ≥0.55) | _pending_ | _pending_ | _pending_ | _pending_ |

## Open Questions

1. **Q1: Reranker — fine-tune on benchmark queries or off-the-shelf?**
   Off-the-shelf MS-MARCO MiniLM gets us most of the gain at ~$0
   training cost. Fine-tuning on the canonical pool's queries would
   risk overfit and require holdout discipline. **Default: off-the-shelf
   for v0.10; revisit fine-tune if v0.10 caps below crawlee.**

2. **Q2: Embedder — keep OpenAI option or local-only?** Recommend keeping
   OpenAI as a `--embedder openai-3-small` opt-in for users who don't
   want the 2GB local-model footprint. Default switches to local.

3. **Q3: Ecom — patches or full pivot to a different rendering
   strategy (e.g. headed Chromium with full residential proxies)?**
   Headed + proxies would likely solve newegg/ikea outright but adds
   meaningful infra cost. **Recommend patches for v0.10; consider
   headed-mode as v0.11+ topic if patches plateau.**

4. **Q4: Rotated-pool query authoring — manual or LLM-assisted?**
   Manual is higher quality but slow. LLM-generated queries with
   manual review is faster. **Default: LLM-assisted with two-pass
   review (generate, then audit each for ground-truth URL match).**

5. **Q5: SC-D requires all 4 dimensions improve. What if only 3 do?**
   The joint validation can pass with 3-of-4 if the 4th is unchanged
   (within ±5%) and the spec is amended at sign-off. **Default: hold
   strict on SC-D; release a v0.10.x point if one dimension regresses
   accidentally and we can isolate the cause.**
