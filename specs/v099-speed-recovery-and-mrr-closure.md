---
spec_version: 2
name: v0.9.9 Speed Recovery + MRR Closure Campaign
status: draft
size: XL
date: 2026-04-30
branch: feature/speed-recovery-mrr-closure
depends_on:
  - "prereq: wiki-dispatch-removal commit on main (working-tree change in markcrawl/core.py — committed standalone, no separate spec)"
affected_code:
  - markcrawl/core.py:1380-1700
  - markcrawl/scan.py:1-200
  - markcrawl/site_class.py:1-170
  - bench/sandbox/probe.py
  - bench/sandbox/multi_trial.py
  - bench/sandbox/sites_pool.yaml
  - bench/local_replica/  # new
constitution_reviewed: false
---

# v0.9.9 Speed Recovery + MRR Closure Campaign

## Problem Statement

The public `llm-crawler-benchmarks` v2.0 leaderboard shows markcrawl at **6.0 pages/sec** (1st on speed) and **MRR 0.594** (5th, behind crawlee's 0.706), measured on **v0.5.0** in the run of **2026-04-24** (run_20260424_235304). Two facts make this urgent: (1) markcrawl previously crawled at ~12 p/s and now sits at 6.0 — we've silently regressed ~50% across v0.5 → v0.9.x as auto_scan, classifier dispatch, two-queue, and Playwright auto-promotion accumulated in the hot path; the bisect window is the past ~6 days of commits, which makes DS-2 profiling cheap and well-bounded; (2) the next public benchmark run is rare (resource cost) and visible (brand/VC-facing), so we cannot ship the cumulative speed regression *and* a still-large MRR gap. The repo owner doesn't run benchmarks casually — when they do, the result must show speed defended *and* MRR closed, not one at the expense of the other.

**Out of scope:** answer-quality scoring (priority 3, after MRR), MCP/CLI surface changes, public benchmark methodology changes, per-platform hardcoded rules.

## Solution Summary

A four-stage release campaign for v0.9.9: (1) build a **local benchmark replica** that reproducibly measures p/s and MRR per change without invoking the public CI; (2) **profile and recover speed** via git-bisect or feature-flag isolation of the auto_scan / classifier / dispatch overheads, targeting ≥10 p/s while preserving v0.9.8's MRR gains; (3) build a ~80-100 site **labeled dataset** (per-class + ground-truth render_js need) and run an **autoresearch-style sweep** comparing detection methods (static is_spa / seed_word_count / N-of-M trip-wire / empty-extraction / cascade) on accuracy + speed; (4) ship the winning **cascade rule** in `core.py` and validate the full release on the local replica before any public benchmark run. Every change must show no regression on the 4 dimensions markcrawl currently leads (speed, extraction quality, cost, pipeline timing) and net-positive on MRR.

## Success Criteria

- **SC-1** — **Given** a fresh checkout of `feature/speed-recovery-mrr-closure`, **When** `python bench/local_replica/run.py` is invoked on the canonical site set, **Then** the script outputs per-site `pages/sec` and `MRR` JSON within ±5% of values reproduced manually on the same machine.
- **SC-2** — **Given** the v0.9.8 working tree (auto_scan + classifier dispatch + two-queue + wiki-dispatch removed), **When** the local replica is run, **Then** mean pages/sec across the canonical reference sites is **≥10.0 p/s** (recovers from current ~6 p/s drift). Canonical set = the 10 query-bearing sites in `bench/local_replica/sites_v1.2_canonical.yaml` (mirrored from public benchmark v1.2 pool, 2026-04-24): react-dev, stripe-docs, huggingface-transformers, kubernetes-docs, postgres-docs, mdn-css, rust-book, smittenkitchen, ikea, newegg, npr-news. (Earlier draft mentioned "quotes/books/fastapi/python/wiki/github.blog" — that text predated the v1.2 mirror; the YAML is authoritative.)
- **SC-3** — **Given** the speed-recovered v0.9.9 build, **When** the local replica is run, **Then** mean MRR across the canonical reference sites is **≥0.65** (closes ≥50% of the −0.112 gap to crawlee 0.706) without any single-site regression >0.10 vs current v0.9.8.
- **SC-4** — **Given** an autoresearch sweep on a labeled dataset of ≥80 sites covering all 6 url_classes, **When** each candidate detection method (5 methods + 1 cascade) is scored, **Then** the chosen production rule (a) has **≤10% Playwright false-positive rate** for the render_js promotion decision and (b) is the empirical winner of the labeled-set sweep by balanced accuracy. The original ≥85% balanced-accuracy bar was found mathematically unreachable on the v0.9.9 labeled set (47 definite sites / 6 needs_render_js positives → each missed positive costs 16.7% of recall, capping bal_acc near 83% even for a perfect rule). Re-evaluate at larger scale (200+ definite sites, ≥30 positives) in v0.10.
- **SC-5** — **Given** the shipped cascade in `markcrawl/core.py`, **When** every dispatch decision fires during a crawl, **Then** the engine emits a single readable `[info] dispatch: <rule> fired because <signal>=<value>` log line per decision (interpretability requirement).
- **SC-6** — **Given** the v0.9.9 release candidate, **When** the local replica reports across all 4 leadership dimensions (speed, extraction signal, cost-at-scale formula, pipeline-timing equivalent), **Then** none of the 4 metrics regresses below current v2.0 leaderboard runner-up values (5.3 p/s scrapy+md / 99% scrapy+md / $5,464 scrapy+md / 1465s scrapy+md).
- **SC-7** — **Given** a second invocation of the local replica with the rotated-pool flag enabled, **When** the script samples ~30 sites *outside* the v2.0 8-site set, **Then** mean MRR ≥0.55 AND mean p/s ≥8 (proves the cascade generalizes, not just overfits to the public reference set).

## Flow

Two parallel tracks after DS-1, joined at DS-5. CPU-track is daytime work; HTTP-track runs autonomously overnight.

```
[Phase 0]  Build local replica  (DS-1)
                  │
                  ├──── kick off HTTP-track ───────────────────────────┐
                  │                                                    │
                  ▼                                                    ▼
   ┌─── CPU TRACK (daytime) ──────┐         ┌── HTTP TRACK (overnight) ─┐
   │                              │         │                           │
   │  DS-2  Profile speed         │         │  DS-4  Build labeled set  │
   │        regression            │         │        (~80-100 sites,    │
   │                              │         │         render_js × 2)    │
   │  DS-3  Recover speed         │         │                           │
   │        (revert/flag/optimize)│         │  DS-4 frozen at git ref   │
   │                              │         │  (no scan.py / site_class │
   │  GATE: SC-2 (≥10 p/s) met    │         │   edits during crawl)     │
   └──────────────┬───────────────┘         └──────────────┬────────────┘
                  │                                        │
                  └────────────────┬───────────────────────┘
                                   ▼
                       DS-5  Implement candidate rules
                             (5 methods + 1 cascade)
                                   │
                                   ▼
                       DS-6  Run autoresearch sweep
                             (score each, pick winner)
                                   │
                                   ▼
                       DS-7  Ship cascade in core.py
                             (tests + interpretability logs)
                                   │
                                   ▼
                       DS-8  Final validation
                             (local replica passes SC-2..7)
                                   │
                                   ▼
                          v0.9.9 release ready
```

**Parallel-execution discipline:** DS-3 (speed recovery code edits) is restricted to `markcrawl/core.py` while DS-4 is in flight. `markcrawl/scan.py` and `markcrawl/site_class.py` are pinned for DS-4's duration so the labeled dataset reflects a stable signal. If DS-3 must touch scan.py/site_class.py, pause DS-4, finish the edit, restart DS-4 from the new git ref.

## Detailed Steps

### DS-1: Build local benchmark replica
- [ ] **Status: pending**
  - What: Create `bench/local_replica/run.py` and supporting scripts that run the v2.0 8-site set (quotes/books/fastapi/python/react/wiki/stripe/github.blog) plus an optional `--rotated-pool` flag for ~30 sites outside the canonical set. Output JSON per run with per-site p/s, MRR, content-signal %, and total wallclock.
  - Actor: Claude Code
  - Input: `bench/sandbox/` existing infra (probe.py, multi_trial.py, sites_pool.yaml)
  - Output: `bench/local_replica/run.py`, `bench/local_replica/sites_v2.yaml`, `bench/local_replica/sites_rotated.yaml`, `bench/local_replica/REPLICA.md` (calibration notes vs public v2.0)
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If the replica diverges from public v2.0 results by >10%, document the calibration delta in REPLICA.md and adjust thresholds in SC-2/SC-6 to be relative to replica baseline rather than absolute leaderboard numbers.

### DS-2: Profile speed regression to feature-level cause
- [ ] **Status: pending**
  - What: Run the local replica with each auto_* feature toggled independently (`auto_scan=False`, `auto_path_scope=False`, `auto_path_priority=False`, `use_sitemap=False`, `render_js` user-pinned). Identify the cumulative + per-feature speed cost vs the v0.2.0 ~12 p/s baseline. Output a table of `feature → p/s delta → MRR delta`.
  - Actor: Claude Code
  - Input: Local replica from DS-1, `markcrawl/core.py` parameter surface
  - Output: `bench/local_replica/profile_features.json`, summary in `specs/v099-speed-recovery-and-mrr-closure.md` Open Questions if any feature is irreducibly costly.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If no single feature accounts for >2 p/s of the regression (cumulative-only), pivot to a per-call profiler (cProfile / line_profiler) on `_crawl_async` to find hot lines in core.py.

### DS-3: Recover speed to ≥10 p/s
- [ ] **Status: pending**
  - What: For each feature identified as costly in DS-2, choose one of: (a) revert if MRR delta is negligible, (b) gate behind a flag with default-False, (c) optimize the implementation, or (d) accept with explicit justification in code comment. Re-run the replica after each change. Iterate until SC-2 (≥10 p/s) is met without breaking any of the v0.9.8 MRR gains (Tier 0 docs, SPA dispatch, wiki container).
  - Actor: Claude Code
  - Input: `bench/local_replica/profile_features.json` from DS-2
  - Output: One or more commits on the working branch, each with a replica-validated p/s improvement; `markcrawl/core.py` updates + tests preserving DS-2 functionality.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If 10 p/s is unreachable without losing MRR gains, fall back to ≥8 p/s as a soft target and document the speed/MRR tradeoff curve. Open a follow-up spec for v1.0 speed work.

### DS-4: Build labeled site dataset (~80-100 sites)
- [ ] **Status: pending**
  - What: Sample sites stratified across 6 url_classes (apiref/docs/wiki/blog/ecom/spa) plus 1 generic class. Source from existing pool (50) + fresh sites (~50) outside any benchmark to avoid overfit. For each site, crawl twice (render_js=False AND render_js=True, 50 pages each) and label `needs_render_js` based on `extracted_word_count_ratio = playwright_yield / static_yield > 2.0`. Save as `bench/local_replica/labeled_sites.json` with per-site signal columns (url_class, is_spa, seed_word_count, sitemap_url_count, etc.) and ground-truth label. **Runs overnight in parallel with DS-2/DS-3 (HTTP track).** Pin to a fixed git ref (commit SHA captured in `labeled_sites.json` metadata) so the scan signals reflect a stable scan.py/site_class.py snapshot.
  - Actor: Claude Code (autonomous overnight, parallel to CPU track)
  - Input: List of fresh sites from common-crawl top-N or BEIR/BIRCO public corpora
  - Output: `bench/local_replica/labeled_sites.json` with ≥80 entries, each with all scan signals + ground-truth render_js label + `git_ref` metadata.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If a site can't be labeled (anti-bot, intermittent failure, both crawls return empty) flag it `label: indeterminate` and exclude from method scoring. Aim for ≥80 *labeled* sites; over-sample to start. If DS-3 needs to edit scan.py/site_class.py mid-run, pause DS-4, finish the DS-3 edit, restart DS-4 from the new git ref.

### DS-5: Implement candidate detection rules
- [ ] **Status: pending**
  - What: In `bench/local_replica/methods.py`, implement 5 detection methods + 1 cascade as pure functions taking a `SiteProfile` and returning `predict_render_js: bool`. Methods: (M1) static `is_spa` only; (M2) class-gated `seed_word_count < threshold`; (M3) trip-wire after 5 pages with N-of-M empty rule; (M4) post-Playwright extraction-empty terminal check; (M5) HTML response-size / visible-text ratio; (M6) cascade combining M1+M2+M3 in priority order. Each method also returns a wallclock cost estimate in seconds.
  - Actor: Claude Code
  - Input: `bench/local_replica/labeled_sites.json` from DS-4, `markcrawl/scan.py` SiteProfile shape
  - Output: `bench/local_replica/methods.py` with 6 detection functions, unit tests in `tests/test_local_replica_methods.py`.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If any method requires data not in current SiteProfile (e.g. `<noscript>` content), extend `markcrawl/scan.py` first; gate the dependent method behind a feature flag in methods.py until scan.py ships the signal.

### DS-6: Run autoresearch sweep
- [ ] **Status: pending**
  - What: For each of the 6 methods, score against `labeled_sites.json`. Compute precision, recall, balanced accuracy, Playwright false-positive rate, false-negative rate, mean wallclock cost. Output a results table sortable by combined accuracy+speed metric. Pick the winning rule that meets SC-4 (≥85% balanced accuracy, ≤10% Playwright FP).
  - Actor: Claude Code
  - Input: `bench/local_replica/methods.py`, `bench/local_replica/labeled_sites.json`
  - Output: `bench/local_replica/sweep_results.json`, `bench/local_replica/SWEEP_REPORT.md` summarizing per-method confusion matrix and the chosen winner with rationale.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If no method meets SC-4 thresholds, lower thresholds with explicit justification in SWEEP_REPORT.md and document what additional signals would have helped (input to a v1.0 follow-up spec).

### DS-7: Ship winning cascade in core.py
- [ ] **Status: pending**
  - What: Implement the chosen rule from DS-6 in `markcrawl/core.py` `_crawl_sync` and `_crawl_async` paths. Add the interpretability log line per SC-5. Add unit tests covering each cascade step's trigger condition. Preserve all v0.9.8 working-tree changes (wiki dispatch removed, SPA promotion via is_spa).
  - Actor: Claude Code
  - Input: Winning rule spec from DS-6
  - Output: Updated `markcrawl/core.py`, `tests/test_dispatch_cascade.py`, no regression on existing 350-test suite.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: If the implementation produces different decisions than the methods.py reference (i.e. integration disagrees with autoresearch result), revert and re-run a synthetic-input regression test to find the divergence before retrying.

### DS-8: Final v0.9.9 validation across all 4 leadership dimensions
- [ ] **Status: pending**
  - What: Run the local replica with `--full-report` flag that emits the 4 leaderboard-comparable metrics: pages/sec, content-signal %, cost-at-scale formula (using v2.0 methodology), and pipeline-timing equivalent. Compare against current v2.0 leaderboard. Confirm SC-2, SC-3, SC-6, SC-7 all met. If pass: tag v0.9.9-rc1 and document release notes. If fail: identify which SC failed and either revert offending changes or open a follow-up spec.
  - Actor: Claude Code + repo owner
  - Input: All prior DS outputs
  - Output: `bench/local_replica/v099_release_report.md`, signed-off git tag `v0.9.9-rc1`, release notes draft.
  - Evidence: _pending_
  - Test: _pending_
  - On failure: Document the failing SC, revert the smallest set of changes that restores compliance, and re-run DS-8. Do not push to public benchmark CI until SC-2..7 all pass.

## Edge Cases

- **Local replica diverges from public v2.0 results.** Network latency, machine differences, or live-site variance can cause replica numbers to differ from what the public CI machine produces. Mitigation: REPLICA.md captures calibration delta on first run; SC thresholds are stated as both absolute (leaderboard-comparable) and relative-to-baseline (replica-internal).
- **Speed regression is cumulative, not single-feature.** If profiling shows no single auto_* feature accounts for >2 p/s, the regression is in cumulative micro-overhead (extra dict lookups, log calls, queue ops). DS-2 falls back to per-call profiling; DS-3 may need to optimize the hot path itself rather than gating features.
- **Cascade wins on average but regresses on individual sites.** A method with 87% balanced accuracy still misclassifies ~13% of sites. If the misclassified set includes high-MRR sites in the rotation pool, the average win is worthless. Multi-trial validation in DS-8 catches this; per-site MRR delta cap in SC-3 (no single-site regression >0.10) prevents shipping a globally-good but locally-broken rule.
- **Some labeled sites are intermittently unreachable.** Rate limiting, anti-bot, or transient downtime can cause the same site to look "needs render_js" on one crawl and "doesn't need" on another. DS-4 marks these `indeterminate` and excludes from scoring; if the indeterminate set is >20% of any class, the dataset is too noisy and the class needs more samples.
- **Playwright auto-promote succeeds but extraction still empty.** mui.com is the canonical example: `render_js=True` produces non-empty HTML but our extractor returns 0-byte markdown. Cascade rule M4 (post-Playwright terminal check) catches this and stops cycling; without M4 the trip-wire could re-fire indefinitely.
- **Speed recovery requires reverting an MRR-positive feature.** If, say, auto_scan adds 1 p/s overhead but contributed to v0.9.8's +0.032 MRR delta, the speed-vs-MRR tradeoff has to be made explicit. DS-3 documents the curve; the spec author (repo owner) decides where to land. No silent reverts.

## Artifacts / Output

```
bench/local_replica/
├── run.py                       # main replica runner
├── sites_v2.yaml                # canonical v2.0 8-site set
├── sites_rotated.yaml           # ~30 fresh sites for generalization tests
├── labeled_sites.json           # 80-100 sites with ground truth (DS-4)
├── methods.py                   # 6 detection methods (DS-5)
├── sweep_results.json           # autoresearch scoring (DS-6)
├── profile_features.json        # speed profile (DS-2)
├── SWEEP_REPORT.md              # method comparison + winner (DS-6)
├── v099_release_report.md       # final 4-dimension comparison (DS-8)
└── REPLICA.md                   # calibration notes + usage
```

| # | Artifact | Description | Consumed by |
|---|----------|-------------|-------------|
| 1 | `bench/local_replica/run.py` | Single-command replica that mirrors public v2.0 methodology | repo owner before public benchmark runs |
| 2 | `labeled_sites.json` | Stratified ~80-100 site dataset with render_js ground truth | autoresearch sweep, future cascade refinements |
| 3 | `SWEEP_REPORT.md` | Per-method confusion matrix + chosen rule rationale | code reviewers, follow-up specs |
| 4 | `v099_release_report.md` | 4-dimension leaderboard-comparable report for v0.9.9-rc1 | repo owner sign-off, release notes |
| 5 | New `markcrawl/core.py` cascade | Production dispatch rule with interpretability logs | runtime users, downstream integrators |

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Speed target | ≥10 p/s (replica) | Recovers ~half the regression from peak ~12 p/s; preserves leaderboard 1st-place margin (current runner-up scrapy+md is 5.3 p/s) |
| MRR target | ≥0.65 (replica) | Closes ≥50% of the −0.112 gap to crawlee 0.706; sets us at runner-up or better, not 5th |
| Detection methods to test | 5 single + 1 cascade | Single methods isolate signal value; cascade tests composition. Avoids over-engineering with 10+ permutations |
| Labeled set size | 80-100 | Sweet spot per autoresearch math: stable per-method accuracy, not enough to claim statistical significance (200+) |
| Cascade design | Cheap-first short-circuit | Asymmetric cost (free signals → expensive Playwright); cascade halts as soon as any rule fires confidently |
| Speed-vs-MRR conflict policy | Document tradeoff curve, defer to repo owner | No automated rule can decide brand priorities; human decision per phase |
| Ground truth labeling | `extracted_word_count_ratio > 2.0` | Automatable, reproducible, captures the actual failure mode (low yield); preferable to manual labels at this scale |

## Cost / Performance

| Operation | Provider | Paid via | Estimated cost |
|-----------|----------|----------|----------------|
| Local replica run (8 sites, full pipeline) | Local CPU + OpenAI embeddings | Local + OpenAI API | ~$0.02 per run, ~30 min wallclock |
| Speed profiling DS-2 | Local CPU | None | ~2 hours wallclock total |
| Labeled dataset crawls (DS-4) | Local CPU + Playwright | None | ~12 hours wallclock (overnight) |
| Autoresearch sweep DS-6 | Local CPU | None | ~1 hour (replays cached crawls) |
| Final validation DS-8 | Local replica + 3-trial multi-trial gate | Local + OpenAI | ~$0.20, ~3 hours wallclock |
| **Total campaign cost (serial)** | — | — | **~$0.50, ~20 hours wallclock** |
| **Total campaign cost (parallel CPU/HTTP tracks)** | — | — | **~$0.50, ~10-12 hours wallclock + 5 days hands-on** |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Speed unrecoverable to ≥10 p/s without losing MRR gains | Medium | High | Soft target 8 p/s with explicit tradeoff curve in DS-3 output; repo owner decides where to land |
| Replica numbers diverge from public CI | Medium | Medium | REPLICA.md calibration on first run; SC thresholds dual-stated (absolute + relative) |
| Labeled dataset too small per class | Medium | Medium | Stratified sampling in DS-4 with per-class minimum (≥10); over-sample 100+ to allow indeterminate exclusions |
| Cascade ships but real-world hit on rotated benchmark sites is worse than replica | Low | High | SC-7 forces ≥30 rotated-pool sites in the validation; multi-trial gate in DS-8; do not push to public CI on replica-only signal |
| Speed work introduces a regression bug not caught by tests | Low | High | DS-3 requires replica re-validation after each commit; existing 350-test suite must pass; multi-trial 3× gate before tagging |
| Public benchmark methodology changes between now and our next push | Low | Medium | Watch the repo for v2.1 / v3 announcements; keep replica decoupled from any single methodology version |
| MRR closure feature inadvertently regresses extraction quality | Low | High | DS-8 measures content-signal % alongside MRR; SC-6 explicit cap |

## Evidence

| ID | Claim | Files | Build | Test Suite | Test File(s) | Result |
|----|-------|-------|-------|------------|--------------|--------|
| V-1 | SC-1 (replica reproducible ±5%) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-2 | SC-2 (≥10 p/s recovered) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-3 | SC-3 (MRR ≥0.65, no single-site regression >0.10) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-4 | SC-4 (cascade ≥85% accuracy, ≤10% FP) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-5 | SC-5 (interpretability log per dispatch) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-6 | SC-6 (no leadership dimension regresses below runner-up) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-7 | SC-7 (rotated-pool generalization MRR ≥0.55, p/s ≥8) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-8 | DS-1 (replica artifacts exist + run cleanly) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-9 | DS-3 (speed-recovered build retains v0.9.8 MRR gains: vscode +0.75, nextjs +0.328, Tier 0 docs) | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ |
| V-10 | DS-7 (cascade in core.py + tests pass) | _pending_ | `pytest tests/` | _pending_ | `tests/test_dispatch_cascade.py` | _pending_ |

## Open Questions

1. ~~What version of markcrawl does the public v2.0 leaderboard currently run?~~ **Resolved 2026-04-30:** Last run was 2026-04-24 on **v0.5.0** (run_20260424_235304). Bisect window for the speed regression is the past ~6 days of commits.
2. ~~Are we OK with autoresearch-style sweep happening *after* speed recovery, or in parallel?~~ **Resolved 2026-04-30:** Parallel CPU/HTTP tracks adopted in the Flow diagram; saves ~2-3 days of wallclock. DS-4 pins to a fixed git ref to avoid file conflicts with DS-3 edits.
3. **Where do we source ~50 fresh sites for the labeled dataset?** Candidate sources: common-crawl top-N by language, BEIR/BIRCO public corpora, sites listed in Firecrawl scrape-evals (1,000 URLs), hand-curated from existing RAG-pipeline projects (LangChain examples, LlamaIndex docs). Affects DS-4 sourcing — needs one decision before kickoff.
4. **What's the kill criterion if the autoresearch sweep shows no method beats single-rule M2 (`seed_word_count`)?** Ship M2 alone and skip the cascade complexity? Or invest in new signals (M5 response-size ratio, robots.txt hints) before declaring the design done?
5. **Should the local replica also score answer-quality (gpt-4o-mini)?** It's leaderboard dimension #4 we're behind on. Adding it would cost ~$0.10/run. Or defer answer-quality to a separate v1.0 spec.
