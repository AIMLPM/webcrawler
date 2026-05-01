# v0.9.9 Campaign Status

_Last updated 2026-04-30 — DS-4 complete, DS-8 in flight._

Current branch: `feature/speed-recovery-mrr-closure`. Spec:
[`specs/v099-speed-recovery-and-mrr-closure.md`](../../specs/v099-speed-recovery-and-mrr-closure.md).

## Progress

| DS | Title | Status | Notes |
|----|-------|--------|-------|
| DS-1 | Build local benchmark replica | ✅ done | `bench/local_replica/run.py` |
| DS-2 | Profile speed regression | ✅ done | sitemap parsing identified as main cost |
| DS-3 | Recover speed (cap + 8s timeout) | ✅ done | 5.84 → 7.55 p/s aggregate; ex-NPR ≈11 p/s |
| DS-3.5 | Parallelize async sitemap fetches | ✅ done | asyncio.gather with sem=10; 7 new tests; targets npr-news drag |
| DS-4 | Build labeled dataset | ✅ done | **171/171 labeled** (14 needs_render_js / 102 static_ok / 55 indeterminate); per-site 5-min wallclock cap survived 3+ Playwright hangs |
| DS-5 | Implement detection rules | ✅ done | M1..M6 with 28 unit tests |
| DS-6 | Run autoresearch sweep | ✅ done (full 171) | M6-cascade wins both at 80-site snapshot (bal_acc 0.713, FP 7.3%) and full 171 (bal_acc 0.664, **FP 2.9%**). M3 trip-wire **rejected** at both scales. |
| DS-7 | Ship winning cascade | ✅ done | R0–R3 shipped via `markcrawl/dispatch.py` + wired into core.py; R4 trip-wire NOT shipped (rejected by DS-6 at full data scale). |
| DS-8.1–8.5 | DS-8 pre-staging | ✅ done | spec drift fix, `--rotated-sample`, `--full-report`, SC-5 log line, SC-4 rebaseline |
| DS-8 | Final validation | ✅ done | v0.9.9-rc1: speed +6.6% vs v0.9.8 baseline, MRR flat (within noise), HF +0.164 MRR, all 4 leadership dimensions improved. Full report: [`v099_release_report.md`](v099_release_report.md). REPLICA.md ships calibration. |
| **TAG** | **v0.9.9-rc1** | ✅ ready | `git tag v0.9.9-rc1` after final commit |

## DS-2 findings (3 sites × 6 configs, 50 pages each)

| config             | npr-news | mdn-css | rust-book | mean   |
|--------------------|----------|---------|-----------|--------|
| baseline-defaults  | 0.20     | 2.46    | 14.85     | 5.84   |
| no-auto-scope      | 0.18     | 5.68    | 16.75     | 7.54   |
| no-auto-priority   | 0.21     | 4.88    | 16.30     | 7.13   |
| **no-sitemap**     | **3.91** | 6.51    | 17.15     | **9.19** |
| bare               | 3.48     | 9.50    | 6.09      | 6.36   |
| with-auto-scan     | 0.20     | 6.86    | 15.61     | 7.55   |

**Conclusions:**
1. **Sitemap parsing is the dominant regression** — disabling it gives the largest aggregate p/s win.
2. **`auto_scan=True` adds ≈0 overhead** — the v0.9.7 dispatch path is cheap; keep it.
3. **`auto_path_scope=False` HURTS rust-book by 8.7 p/s** — single-segment seeds need scope or BFS escapes off-topic. Don't drop it.

## DS-3 work landed

`commit 3927052` — cap sitemap URLs at `max(500, max_pages * 4)`. Wired
through both sync + async parsing paths in `markcrawl/robots.py`, with
the cap applied at `markcrawl/core.py` sitemap loops.

Measured (without DS-4 contention):
- npr-news: 0.20 → 0.52 p/s (+2.6×)
- mdn-css: 2.46 → 5.32 p/s (+2.2×)
- rust-book: unchanged
- aggregate: 5.84 → **7.55 p/s** (+29%)

NPR remains slow because of npr.org server-side latency, not our overhead.
Without npr-news in the average: ex-NPR aggregate ≈ 11 p/s — that's
above the SC-2 target.

## DS-3 levers still untried

If we need to push aggregate above 10 p/s including NPR-style sites:
1. **Parallelize async sitemap child-fetches** with `asyncio.gather` —
   currently sequential. Plausible 2-3× on multi-tenant sitemap indexes.
2. **Cap sitemap fetches by COUNT not just URL count** — limit recursion
   to e.g. 20 child sitemap fetches regardless of URL accumulation.
3. **`auto_path_priority` hot loop optimization** — costs ~0.5 p/s in
   the profile; might be cheaply optimizable.
4. **Skip sitemap when scan reveals huge sitemap + narrow seed scope** —
   use scan's `sitemap_huge` flag to bypass parse when path scope will
   filter out most URLs anyway.

## DS-4 in progress

171 sites × 2 modes (static + Playwright). Pinned to git ref
`7077755a703f599232900d9fa5156202ad51ec71`. Output:
`bench/local_replica/labeled_sites.json` (incremental save every 5).

Sample early labels:
- `findchips-com` → needs_render_js (ratio 152×) ✓
- `oc-eco-br` → indeterminate (no static yield)
- `daifuku-com` → static_ok (ratio 1.0)
- `mopsov-twse-com-tw` → needs_render_js (1520×, but URL also failed Playwright fetch)

Estimated completion: ~10 more hours at current rate.

## DS-6 sweep result (80-site snapshot, 47 definite)

| method | bal_acc | precision | recall | FP rate | n_definite | cost/site |
|---|---|---|---|---|---|---|
| **M6-cascade** | **0.713** | 0.500 | 0.500 | 7.3% | 47 | 2.07s |
| M2-seed-words | 0.642 | 0.500 | 0.333 | 4.9% | 47 | 0.00s |
| M1-is-spa | 0.583 | 1.000 | 0.167 | 0.0% | 47 | 0.00s |
| **M3-trip-wire** | **0.447** | 0.000 | 0.000 | 10.5% | 19 | 2.50s |
| M5-ratio | — | — | — | — | 0 | (no html-bytes signal) |

Positive class is small (6/47 ≈ 13%) — recall is high-variance. M3 produced 2 FP / 0 TP across 19 firings; would degrade the cascade if shipped. Re-run sweep on full 171 once DS-4 finishes if you want tighter intervals; the directional verdict (M3 rejected) won't flip.

## Key git refs

```
7c6e264 DS-7 (early): production cascade module markcrawl/dispatch.py
b1a7ab5 DS-3 v2: cap per-sitemap-fetch timeout at 8s
2d72ecf docs: campaign status snapshot
3927052 DS-3 partial: cap sitemap parsing at max(500, max_pages*4) URLs
c5f2785 DS-5/DS-6/DS-2: cascade methods + sweep runner + feature profiler
7077755 DS-1: local benchmark replica + labeled-dataset crawler  ← DS-4 pinned here
af8a548 specs: add v0.9.9 speed recovery + MRR closure campaign
2b281b5 core: remove wiki BFS-priority dispatch from auto_scan  (on main)
```

Total tests: 405 (28 method tests + 27 dispatch tests = 55 new on the campaign branch). All passing.

## Remaining wallclock budget

- DS-3 final iteration: ~1-2 hours (one of the 4 levers above)
- DS-4 completion: ~10 hours overnight
- DS-6 sweep: ~10 minutes after DS-4 done
- DS-7 ship cascade: ~1-2 hours coding + tests
- DS-8 final validation: ~1-2 hours full canonical pool run

Total to v0.9.9-rc1 tag: ~12-16 hours of mostly-overnight wallclock.
