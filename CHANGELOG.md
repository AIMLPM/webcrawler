# Changelog

All notable changes to MarkCrawl are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project follows [SemVer](https://semver.org/) once it reaches 1.0.

## [0.10.0] - 2026-05-01

### Added
- **Tenacity-backed HTTP retry policy** in the new module `markcrawl.retry`.
  Full-jitter exponential backoff: 5 attempts, 2 s starting delay, 30 s cap.
  Honors the server's `Retry-After` header on 429 responses (clamped to the
  30 s ceiling). Emits one structured INFO log line per retry — `[retry]
  attempt=N status_code=… url=… sleep=Xs elapsed=Ys detail=…`. Applied
  uniformly to both the `httpx` (`_fetch_httpx`, `fetch_async`) and
  `requests` (`_fetch_requests`) code paths so both transports follow the
  same policy.
- **`tests/test_retry.py`** — 36 new unit tests covering header parsing,
  retryable-status detection, the wait strategy, end-to-end retry behavior,
  and policy-constant invariants.
- **CI source-vs-published parity check** at
  `.github/workflows/cli-flag-parity.yml`. Triggers on push to `main` and on
  every `v*` tag. Installs the local source as a wheel, captures `markcrawl
  --help`, force-reinstalls the latest published wheel, captures `--help`
  again, and diffs. Hard-fails on any mismatch when the source version is
  already on PyPI; soft-warns when source is ahead (expected pre-release
  window). Catches the source-vs-PyPI divergence class that produced bug
  fe6f3c39.
- **`tenacity>=8.0,<10.0`** declared in `pyproject.toml` and
  `requirements.txt` install requirements.

### Changed
- **`markcrawl/throttle.py` no longer reacts to 429 responses.** Rate-limit
  backoff is now owned exclusively by the retry layer. `AdaptiveThrottle`
  continues to manage inter-request pacing (response-time proportional and
  `robots.txt` Crawl-delay floor) — both layers now compose cleanly without
  double-waiting. The previous uncapped doubling-from-1 s branch in
  `throttle.update()` (lines 46–50 in 0.9.x) was removed; an explicit
  early-return on 429 keeps the response-time signal clean. Tests updated:
  `tests/test_core.py::test_update_throttle_429_is_ignored` and
  `test_update_throttle_429_does_not_disturb_pacing` codify the new contract.
- **`markcrawl/fetch.py::_build_requests_session` no longer mounts a
  `urllib3.util.Retry` adapter.** Transport-level retry was conflicting with
  the new request-level retry layer; consolidating to the tenacity layer
  removes the double-retry surface and the silent transport-level
  no-jitter behavior.
- **`fetch_async` rewritten** to use `tenacity.AsyncRetrying` via
  `markcrawl.retry.with_retry_async` for a single source of truth on the
  retry policy across sync and async paths.

### Documentation
- **README.md** — new "Installation / Upgrading" section near the top with
  `pip install --upgrade` guidance, an explanation of the stale-install
  failure mode, and `head -1 $(which markcrawl)` as the canonical
  diagnostic for "which Python owns my binary".
- **specs/v3-landscape/** — three design docs from the v3 landscape stage
  (`root-cause-diagnosis.md`, `backoff-strategy-design.md`, `fix-plan.md`)
  document the bug investigation, library comparison, and operator runbook.

### Migration notes for downstream consumers
- No CLI-flag changes — every flag in 0.9.x remains in 0.10.0 with identical
  semantics. The retry behavior change is internal and transparent.
- Anyone subclassing `AdaptiveThrottle` and overriding `update()` should be
  aware that `_backoff_count` is now permanently 0 (kept as a public
  attribute for backward compatibility).
- Library consumers calling `markcrawl.fetch.fetch()` directly will see the
  same return contract: a response object on success / exhausted-soft-fail,
  or `None` when the underlying transport raises a transient error five
  times in a row.

## [0.9.3] - 2026-04-26

Last release before the v3 retry overhaul. See git log for the 0.5.0 → 0.9.3
release history (multi-site discovery, screenshot pipeline, image download,
smart-sample, dry-run, etc.).

[0.10.0]: https://github.com/AIMLPM/markcrawl/releases/tag/v0.10.0
[0.9.3]: https://github.com/AIMLPM/markcrawl/releases/tag/v0.9.3
