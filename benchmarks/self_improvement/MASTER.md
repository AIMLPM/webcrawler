# Benchmark Self-Improvement Specs

**Purpose:** Modular review specs for the MarkCrawl benchmark suite. Each spec
can be executed independently or as part of a full audit.

**Last reviewed:** 2026-04-08

---

## How to use

Point the AI assistant to a specific spec when you want a focused review:

- "Review spec 01" -- code review of markcrawl core
- "Review spec 04" -- check reports against style guide
- "Run all specs" -- full audit (start to finish)

Each spec contains:
- **What to check** -- the specific files and concerns
- **How to check** -- commands, grep patterns, manual steps
- **What "good" looks like** -- pass/fail criteria

---

## Spec Index

| # | Spec | Scope | Key Files |
|---|------|-------|-----------|
| 01 | [MarkCrawl Code Review](01_markcrawl_code_review.md) | Core crawler package | `markcrawl/` package, `Dockerfile` |
| 02 | [Benchmark Code Review](02_benchmark_code_review.md) | Python benchmark scripts (no Docker) | `benchmark_*.py`, `quality_scorer.py`, `crawlee_worker.py`, `lint_reports.py` |
| 03 | [Docker Infrastructure Review](03_docker_infra_review.md) | Firecrawl Docker stack, benchmark Dockerfile | `firecrawl/`, `Dockerfile`, `benchmarks/Dockerfile` |
| 04 | [Report Style Compliance](04_report_style_compliance.md) | Markdown reports vs CLAUDE.md style guide | All `benchmarks/*.md` reports |
| 05 | [Cross-Report Data Consistency](05_cross_report_consistency.md) | Numbers agree across reports | SPEED, RETRIEVAL, ANSWER_QUALITY, COST reports + source data |
| 06 | [Resilience & Restart](06_resilience_restart.md) | Checkpointing, crash recovery, data integrity | All benchmark scripts, checkpoint dirs |
| 07 | [Report Data Quality](07_report_data_quality.md) | Fishy data detection, page count gaps, early warnings | All reports + source data + benchmark scripts |
| 08 | [Persona Reviews](08_persona_reviews.md) | Persona definitions, assignments, review guides | README, all reports, all specs |
| 09 | [Safeguards](09_safeguards.md) | Pre-commit validation, feedback preservation, invariant checks | All changes |
| -- | [Feedback Registry](feedback_registry.md) | Protected content from user/reviewer feedback | All files |
| -- | [check_invariants.py](check_invariants.py) | Automated invariant checker (run before committing) | README, reports, code |
| -- | [check_cross_report_consistency.py](check_cross_report_consistency.py) | Cross-report data consistency checker (run before committing) | README, SPEED, COST, ANSWER_QUALITY reports |

---

## Severity escalation

Any finding where a **published number** (README benchmark table, report
summary table) disagrees with its **source data** (the report or script that
produced the number) is automatically **CRITICAL**, regardless of which spec
catches it.

Published numbers are what readers see first and cite to others. Wrong numbers
in the README or a summary table destroy credibility in a way that a stale
methodology footnote does not. This rule exists because the April 2026 audit
predicted Spec 05 (cross-report consistency) would produce "2-4 inconsistencies"
but it turned out to be the only CRITICAL finding — the severity was
under-triaged because the process treated data mismatches the same as style nits.

**Examples of auto-CRITICAL findings:**
- README says "scrapy+md is fastest" but SPEED_COMPARISON.md ranks a different
  tool first
- README table shows chunks/page = 12.0 but COST_AT_SCALE source data says 10.1
- COST_AT_SCALE cites answer quality of 3.91 but ANSWER_QUALITY.md says 3.86

**Not auto-CRITICAL** (normal severity rules apply):
- A methodology footnote references an old date
- A cross-reference link points to a renamed section
- Tool name casing differs between reports

---

## DO NOT run benchmarks

Self-improvement reviews are **read-only analysis + documentation/code fixes**.
Do NOT execute any of the following during a review — they take hours and
consume API credits:

- `benchmark_all_tools.py` (crawls 8 sites with 8 tools — several hours)
- `benchmark_retrieval.py` (embeds all pages, runs 92 queries — 1-2 hours + OpenAI costs)
- `benchmark_answer_quality.py` (LLM-judges 92 answers — 30+ min + OpenAI costs)
- `benchmark_quality.py` (scores all pages — 10-30 min)
- `benchmark_markcrawl.py` (live crawl — 10-30 min)

**You MAY run:** `check_invariants.py`, `lint_reports.py`, `preflight.py`,
`grep`, `cat`, `wc`, `python -c` one-liners for data validation, and any
read-only inspection commands.

If a review identifies stale data or a re-run is needed, **flag it as a
finding** using the format in [Pending Findings](#pending-findings) below.
Do not execute the re-run.

## Safeguards (MUST READ)

Every self-improvement change must pass through [Spec 09](09_safeguards.md):

1. Check the [Feedback Registry](feedback_registry.md) — don't undo documented feedback
2. Run `python benchmarks/self_improvement/check_invariants.py` — verify invariants
3. Run `python benchmarks/lint_reports.py` — verify report style
4. Review the diff — no unintended removals

---

## Persona Assignment Matrix

Each spec is reviewed by at least 2 personas. See [08_persona_reviews.md](08_persona_reviews.md)
for full persona definitions and per-spec checklists.

| Spec | LLM Agent | Junior Dev | Principal Eng | Product Manager |
|------|-----------|------------|---------------|-----------------|
| 01 MarkCrawl Code | | x | x | |
| 02 Benchmark Code | | x | x | |
| 03 Docker Infra | | | x | |
| 04 Report Style | x | x | | x |
| 05 Cross-Report Consistency | | | x | x |
| 06 Resilience | | x | x | |
| 07 Report Data Quality | | x | x | x |
| README & Docs | x | x | | x |

---

## Data Lineage (quick reference)

```
                     .url_cache.json
                           |
                           v
                 benchmark_all_tools.py
                   /         |         \
                  v          v          v
             runs/run_*/  SPEED_COMPARISON.md  QUALITY_COMPARISON.md
                  |
        +---------+---------+---------+
        v         v         v         v
  benchmark_   benchmark_  benchmark_  benchmark_
  retrieval.py answer_     quality.py  markcrawl.py
        |      quality.py      |           |
        v         v            v           v
  RETRIEVAL_   ANSWER_     (feeds into   MARKCRAWL_
  COMPARISON   QUALITY     QUALITY_      RESULTS.md
  .md          .md         COMPARISON)
        \         |
         \        v
          +-> COST_AT_SCALE.md  (hand-written, derives from above)
              METHODOLOGY.md    (hand-written reference)
```

## Cache Locations

| Cache | Location | Key | Cleared By |
|-------|----------|-----|------------|
| URL discovery | `.url_cache.json` | site name | `--refresh-urls` |
| Speed checkpoint | `.benchmark_checkpoint.json` | run args hash | `--no-resume` |
| Embeddings | `embed_cache/` | SHA256 of text batch | `--fresh` |
| Retrieval results | `retrieval_checkpoints/` | `run__tool__site__config` | `--fresh` or manual delete |
| Answer quality | `answer_quality_checkpoints/` | `run__tool__site` | `--fresh` or manual delete |

---

## Pending Findings

Actionable items identified during self-improvement reviews that cannot be
resolved in a read-only review (e.g., benchmark re-runs needed, user
decisions required). Remove items from this list when resolved — the
resolution goes into a git commit.

### PF-001: MARKCRAWL_RESULTS.md is stale

- **Filed:** 2026-04-08
- **Found by:** Spec 07 review
- **Type:** BENCHMARK-RERUN
- **Scripts to re-run:**
  - [ ] `benchmark_markcrawl.py` (~10-30 min, no API cost)
- **What triggered this:** MARKCRAWL_RESULTS.md was generated on 2026-04-05
  but report and style fixes were applied on 2026-04-08. The headline
  numbers (5.99 pages/sec, 227 pages) may be outdated.
- **Stale files:** `benchmarks/MARKCRAWL_RESULTS.md`
- **Reports that will change:** MARKCRAWL_RESULTS.md only (self-benchmark,
  no cross-report dependencies)
- **Estimated effort:** 10-30 min runtime, no API cost
- **Resolved:** _pending_

### PF-002: Missing fastapi-docs "file uploads" retrieval query

- **Filed:** 2026-04-08
- **Found by:** Spec 07 review (from 2026-04-06 next-steps list)
- **Type:** BENCHMARK-RERUN
- **Scripts to re-run:**
  - [ ] `benchmark_retrieval.py` (~1-2 hours, ~$2 OpenAI embedding cost)
  - [ ] `benchmark_answer_quality.py` (~30 min, ~$0.50 OpenAI cost)
- **What triggered this:** The fastapi-docs query set has no query about
  file uploads (a common FastAPI feature). Adding it would increase the
  query set from 92 to 93 and require re-running retrieval + answer quality.
- **Stale files:** retrieval and answer quality checkpoints for all tools
  on fastapi-docs
- **Reports that will change:** RETRIEVAL_COMPARISON.md, ANSWER_QUALITY.md,
  COST_AT_SCALE.md (query count references)
- **Estimated effort:** ~2 hours + ~$2.50 OpenAI costs
- **Resolved:** _pending_

<!--
When adding findings, replace the "no pending findings" line with entries
using the format below. When the last finding is resolved, restore the
"no pending findings" line.

### PF-NNN: Short title

- **Filed:** YYYY-MM-DD
- **Found by:** Spec NN review
- **Type:** BENCHMARK-RERUN / USER-DECISION / EXTERNAL-DEPENDENCY
- **What:** Description of what was found
- **Why it matters:** Impact if not addressed
- **Action needed:** What the user should do
- **Estimated effort:** e.g., "2-3 hours + ~$0.50 OpenAI costs"
- **Resolved:** _(fill in when done: date, commit hash, or "won't fix" + reason)_
-->

### Reporting format: benchmark re-run needed

When a review determines that benchmark data is stale and a re-run is
required, use this specific format so the user can quickly assess scope
and cost:

```markdown
### PF-NNN: Benchmark re-run needed — [short reason]

- **Filed:** YYYY-MM-DD
- **Found by:** Spec NN review
- **Type:** BENCHMARK-RERUN
- **Scripts to re-run:**
  - [ ] `benchmark_all_tools.py` (~3-5 hours, no API cost)
  - [ ] `benchmark_retrieval.py` (~1-2 hours, ~$2 OpenAI embedding cost)
  - [ ] `benchmark_answer_quality.py` (~30 min, ~$0.50 OpenAI cost)
  - [ ] `benchmark_quality.py` (~10 min, no API cost)
  _(check only the scripts that need re-running)_
- **What triggered this:** [e.g., "colly page counts changed after async
  fix but retrieval checkpoints still reflect old 25-page data"]
- **Stale files:** [list specific checkpoints or reports affected]
- **Reports that will change:** [which .md files will be regenerated]
- **Estimated effort:** [time + cost]
- **Resolved:** _pending_
```

### Reporting format: user decision needed

```markdown
### PF-NNN: [decision title]

- **Filed:** YYYY-MM-DD
- **Found by:** Spec NN review
- **Type:** USER-DECISION
- **Question:** [the specific decision the user needs to make]
- **Options:**
  - A: [option and trade-off]
  - B: [option and trade-off]
- **Recommendation:** [which option and why, or "no recommendation"]
- **Resolved:** _pending_
```
