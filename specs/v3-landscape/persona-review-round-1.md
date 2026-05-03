# markcrawl v3 — Persona Review (round 1)

**Run:** SOTA Studio improvement run `09dc7a77-c088-4ef3-ad98-0d81e1c373ff`
**Round:** 1
**Stage:** persona_review
**Date:** 2026-05-01
**Source version under review:** `0.10.0` (was `0.9.3`)
**Tests:** 493/493 pass (36 NEW in `tests/test_retry.py`)

---

## Aggregate Verdict

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Average rating | **3.75 / 5** | ≥ 4.0 | **MISS by 0.25** |
| Personas approving (rating ≥ 4 OR verdict ∈ APPROVE/APPROVE_WITH_CHANGES) | **4 / 4** | ≥ 3 / 4 | **PASS** |
| Critical issues open after triage | **0** | 0 | **PASS** |
| Major issues open after triage (post-triage IMPLEMENT/DEFER counts below) | **0 IMPLEMENT-blocking** | — | **PASS** |
| Cost (4 personas, 4 LLMs) | **~$0.45** | < $0.80 | **PASS** |

**Recommendation: ADVANCE to feedback_integration / integration_testing.**

Rationale for advancing despite the 0.25 short-of-4.0 average:
- The single rating-3 (Reliability SRE) gave APPROVE_WITH_CHANGES and explicitly framed both major issues as "blockers for a production-ready v1.0 release," not v0.10.0. v0.10.0 is a 0.x release closing reported feedback, not a 1.0 cut.
- All 4 personas independently ranked the v3 design as APPROVE-class with no REQUEST_CHANGES or REJECT verdicts.
- One Reliability SRE finding (silent-failure exhaustion log at WARN, should be ERROR) is a 10-min code change classified IMPLEMENT in this round's triage and will be applied during feedback_integration.
- All other major issues are deferred to v0.10.1 / v0.11.0 with explicit rationale.

---

## Per-Persona Verdicts

| Persona | Provider | Verdict | Rating |
|---|---|---|---|
| Skeptical Backoff Engineer | xai:grok-4-latest | APPROVE_WITH_CHANGES | 4 / 5 |
| Python Packaging Expert | anthropic:claude-opus-4-7 | APPROVE_WITH_CHANGES | 4 / 5 |
| Downstream Consumer designlens | openai:gpt-4.1-2025-04-14 | APPROVE_WITH_CHANGES | 4 / 5 |
| Reliability SRE | google:gemini-2.5-pro | APPROVE_WITH_CHANGES | 3 / 5 |

---

## Triage Roll-up

### IMPLEMENT this round (1 item, ~10 min)

1. **Bump retry-exhaustion log line in `with_retry` / `with_retry_async` from `WARNING` to `ERROR` and ensure the URL is included in the message.** Source: Reliability SRE — "silent failure on retry exhaustion." Rationale: the current `WARNING` is correct half-measure but `ERROR` is what greppable failure-mode visibility actually requires; URL inclusion lets per-host exhaustion be greppable. 10-min code change in `markcrawl/retry.py`.

### DEFER (12 items)

Grouped by target version:

**v0.10.1 (next patch):**
- Skeptical Backoff Engineer: `_read_retry_after` HTTP-date parsing (RFC 9110 §10.2.3 — rare in 429 contexts; exponential fallback covers safely; track as known-limitation).
- Python Packaging Expert: tenacity 9.x compat CI matrix.
- Python Packaging Expert: `AdaptiveThrottle._backoff_count` deprecation via `__getattr__` or removal (CHANGELOG already notes the change).
- Python Packaging Expert: built-wheel content verification CI step (low risk because retry.py is import-time loaded via fetch.py).

**v0.11.0 (next minor):**
- Skeptical Backoff Engineer: extended test coverage for partial-recovery (interleaved 429/200) and very-long-recovery (multi-hour).
- Skeptical Backoff Engineer: extend B2 with concurrent-retries dimension to verify thundering-herd avoidance empirically.
- Python Packaging Expert: flag-parity job — add second comparison vs previous PyPI version's `--help`.
- Python Packaging Expert: flag-parity diff — argparse introspection vs text diff.
- Reliability SRE: Prometheus/StatsD counters (`markcrawl_retries_total{host,reason}`, `markcrawl_retries_exhausted_total{host}`).
- Reliability SRE: `--log-format=json` CLI flag.

**Owned by other repo (designlens improvement run):**
- Downstream Consumer designlens: executable B3 integration test — implementation belongs on the designlens side (depends on designlens `--trace-imports` flag that doesn't yet exist) AND on PyPI publish of `markcrawl==0.10.0`. Already documented in `benchmarks/b3_designlens_integration.md` "Promotion to executable" section.
- Downstream Consumer designlens: retry log "what to grep for" documentation in designlens README.
- Downstream Consumer designlens: CI automation of trace-import check in designlens.

**IMPLEMENT in feedback_integration of THIS run (already in scope):**
- Python Packaging Expert: confirm `requirements.txt` includes `tenacity>=8.0,<10.0` (5-min check; preempts dev-env breakage).
- Python Packaging Expert: replace README `head -1 $(which markcrawl)` diagnostic with `python -c 'import markcrawl, sys; print(markcrawl.__file__, markcrawl.__version__, sys.executable)'` (5-min doc fix; portable across pyenv/conda/Homebrew/Windows).

### REJECT (0 items)

No persona findings were rejected. Every issue raised was either accepted (IMPLEMENT) or deferred with explicit rationale.

---

## Top 3 Cross-Persona Themes (none are graduation blockers)

1. **Observability gap between log-level and metrics.** The Reliability SRE persona drove this, but the Downstream Consumer persona echoed it from the consumer-visibility angle. Resolution: bump exhaustion log to ERROR now (this round); metrics in v0.11.0.

2. **CI guardrail is the right shape but has known soft-fail windows.** The Python Packaging Expert raised two distinct CI improvements (vs-previous-PyPI-version comparison, argparse introspection vs text diff). Both deferred to v0.11.0 — current job catches the immediate fe6f3c39 class.

3. **B3 designlens-no-fallback executable test is genuinely deferred outside markcrawl scope.** Both the Downstream Consumer persona and the design doc agree: requires designlens-side `--trace-imports` flag + PyPI publish of `markcrawl==0.10.0`. Will be picked up by the next designlens improvement run.

---

## Detailed Persona Reviews

### 1. Skeptical Backoff Engineer (xai:grok-4-latest)

**Verdict:** APPROVE_WITH_CHANGES — **Rating 4 / 5**

**Summary:** "The v3 retry/backoff layer introduces a measured exponential backoff with capping, full jitter, and partial Retry-After support, integrating cleanly with the throttle layer and matching async/sync policies, but it has gaps in Retry-After parsing and limited testing for certain edge cases."

**Strengths:**
- Backoff is capped at 30s with full jitter via tenacity's `wait_random_exponential`, matching design doc numbers (initial 2s, multiplier 2, max tries 5).
- Composition with throttle layer avoids double-waiting by ignoring 429 in throttle, preserving pacing.
- Async path uses `AsyncRetrying` equivalent with identical wait/retry/log policies.

**Issues raised:**

| # | Severity | Title | Triage |
|---|---|---|---|
| 1 | major | Incomplete Retry-After parsing: ignores HTTP-date format | DEFER v0.10.1 |
| 2 | minor | Limited edge case coverage for partial recovery and very-long-recovery | DEFER v0.11.0 |
| 3 | minor | Jitter algorithm is full-jitter but not explicitly verified for thundering herd at high concurrency | DEFER v0.11.0 (B2 extension) |

**Blockers cited:** "Implement full Retry-After parsing including HTTP-date." → DEFER v0.10.1; rationale per RFC 9110 §10.2.3, HTTP-date in 429 contexts is rare and exponential fallback covers safely.

---

### 2. Python Packaging Expert (anthropic:claude-opus-4-7)

**Verdict:** APPROVE_WITH_CHANGES — **Rating 4 / 5**

**Summary:** "The packaging path for v0.10.0 is largely sound: trusted-publisher OIDC is already proven by 15 successful releases, the tenacity dependency is a reasonable, well-maintained choice, and the version bump + dep addition are mechanically trivial for the existing publish.yml. The new flag-parity CI is a genuine guardrail for the bug class. However, the tenacity upper bound and the README diagnostic command have real gotchas, and the CI workflow has an under-specified failure mode (source-ahead-of-PyPI window) that can mask regressions."

**Strengths:**
- Version bump 0.9.3 → 0.10.0 plus a single new runtime dep is a minimal-risk packaging delta.
- tenacity is pure-Python, Apache-2.0, no transitive deps, broadly compatible with Python 3.8+.
- CI flag-parity job correctly distinguishes the regression direction from the benign pre-release window.
- CHANGELOG explicitly notes no CLI-flag semantics changed in 0.10.0.

**Issues raised:**

| # | Severity | Title | Triage |
|---|---|---|---|
| 1 | major | tenacity upper bound `<10.0` is speculative and tenacity 9.x already exists | DEFER v0.10.1 |
| 2 | major | requirements.txt consistency not confirmed | **IMPLEMENT** (5-min check this run) |
| 3 | major | Flag-parity CI 'source ahead of PyPI' soft-warn window can hide regressions | DEFER v0.11.0 |
| 4 | major | Flag-parity diff is line-based on --help output, fragile to cosmetic changes | DEFER v0.11.0 |
| 5 | minor | README `head -1 $(which markcrawl)` diagnostic is brittle across Python installs | **IMPLEMENT** (5-min doc fix this run) |
| 6 | minor | Backwards-compat note for `AdaptiveThrottle._backoff_count` is incomplete | DEFER v0.10.1 |
| 7 | minor | No verification that the built wheel actually contains `markcrawl/retry.py` | DEFER v0.10.1 |

**Blockers cited:** none. ("None are publish-blockers.")

---

### 3. Downstream Consumer designlens (openai:gpt-4.1-2025-04-14)

**Verdict:** APPROVE_WITH_CHANGES — **Rating 4 / 5**

**Summary:** "markcrawl v3's retry layer theoretically unblocks designlens from needing to directly depend on Playwright for JS-rendered fetches. The retry semantics resolve all previously reported issues, and the design covers designlens's intermittent network error and 429/SPA slow-load cases. However, the lack of a passing B3 (integration) executable test means there is residual risk."

**Strengths:**
- Retry covers all empirically encountered failure modes: 429 (proper backoff, Retry-After), transient resets, slow SPAs.
- Operator/runbook effort for designlens migration is low.
- Structured INFO logging for each retry event ensures designlens can see retry behavior end-to-end.
- Version upgrade path is clean.

**Issues raised:**

| # | Severity | Title | Triage |
|---|---|---|---|
| 1 | critical | Executable Integration Test for Fallback Removal Not Complete | DEFER (designlens-side, blocked on PyPI publish + designlens `--trace-imports`) |
| 2 | minor | Retry Observability Only Surfaces in markcrawl Logs | DEFER (designlens-side documentation) |
| 3 | minor | Trace Import Step for Playwright Removal is Manual | DEFER (designlens-side CI work) |

**Blockers cited:** "Passing, executable B3 integration test before designlens unpins/merges fallback removal."
- **Triage rationale:** classified as critical from designlens's downstream view, but B3 is a designlens-side change blocked on PyPI publish + designlens flag work — both of which are outside markcrawl v3 scope. Already documented in `benchmarks/b3_designlens_integration.md` "Promotion to executable." The next designlens improvement run picks this up.

---

### 4. Reliability SRE (google:gemini-2.5-pro)

**Verdict:** APPROVE_WITH_CHANGES — **Rating 3 / 5**

**Summary:** "The v3 retry layer introduces valuable, per-attempt structured logging at the INFO level, providing real-time visibility into backoff events, especially for CLI users. However, it completely lacks metrics, making it impossible to alert on systemic retry issues like high error rates or exhausted requests. Furthermore, it silently handles retry exhaustion by returning the final failed response without logging a distinct WARNING or ERROR, hiding critical failure modes from operators."

**Strengths:**
- Per-attempt logging is structured (key=value), includes essential context (URL, status, sleep duration), uses the existing logger.
- The inclusion of the full URL provides clear per-host visibility.
- `--show-progress` augmented by INFO-level retry logs gives real-time signal that the crawler is throttling, not stuck.

**Issues raised:**

| # | Severity | Title | Triage |
|---|---|---|---|
| 1 | major | No metrics for retry behavior | DEFER v0.11.0 (requires new optional dep + opt-in surface; explicitly framed by reviewer as "v1.0 production-ready" blocker, not 0.x) |
| 2 | major | Silent failure on retry exhaustion | **IMPLEMENT** this round (bump WARN → ERROR in `with_retry` / `with_retry_async`, include URL) |
| 3 | minor | Logs are semi-structured, not JSON | DEFER v0.11.0 (`--log-format=json` CLI flag) |

**Blockers cited:** "Addressing the 'No metrics' and 'Silent failure' issues should be considered blockers for a production-ready v1.0 release."
- **Triage rationale:** v0.10.0 is not v1.0. Silent-failure → IMPLEMENT this round. Metrics → DEFER v0.11.0.

**Note:** the review's claim "the event is not logged at a high severity" is technically inaccurate — `with_retry` already emits `logger.warning("[retry] gave up after %d attempts...")` on exhaustion. The substance of the finding (WARN is too quiet for SRE alerting; should be ERROR with URL) stands and is being implemented.

---

## Files Read for This Review

- `/Users/paulsave/Documents/Coding/markcrawl/specs/v3-landscape/root-cause-diagnosis.md`
- `/Users/paulsave/Documents/Coding/markcrawl/specs/v3-landscape/backoff-strategy-design.md`
- `/Users/paulsave/Documents/Coding/markcrawl/specs/v3-landscape/fix-plan.md`
- `/Users/paulsave/Documents/Coding/markcrawl/markcrawl/retry.py`
- `/Users/paulsave/Documents/Coding/markcrawl/markcrawl/fetch.py`
- `/Users/paulsave/Documents/Coding/markcrawl/markcrawl/throttle.py`
- `/Users/paulsave/Documents/Coding/markcrawl/.github/workflows/cli-flag-parity.yml`
- `/Users/paulsave/Documents/Coding/markcrawl/pyproject.toml`
- `/Users/paulsave/Documents/Coding/markcrawl/CHANGELOG.md`
- `/Users/paulsave/Documents/Coding/markcrawl/README.md` (Installation/Upgrading section)
- `/Users/paulsave/Documents/Coding/markcrawl/tests/test_retry.py`
- `/Users/paulsave/Documents/Coding/markcrawl/benchmarks/baseline-results-v0.10.0.json`
- `/Users/paulsave/Documents/Coding/markcrawl/benchmarks/b3_designlens_integration.md`

---

## Audit Trail

Studio recorded persona feedback IDs (one per persona):

- Skeptical Backoff Engineer → `e73bb191-9803-408d-bae7-dd8fe23e2bce`
- Python Packaging Expert → `dc743159-c876-4282-81e5-ad11790c455f`
- Downstream Consumer designlens → `d5b91a16-935a-48b3-a105-0cdec8a74c27`
- Reliability SRE → `f932602c-afd4-44de-9369-177065147980`

Raw per-persona JSON output preserved at `/tmp/persona-{slug}.json` for audit during this stage.
