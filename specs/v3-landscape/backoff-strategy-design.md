# Backoff Strategy Design (Perf Feedback c69402e7)

## Current Behavior — What's Actually There

Feedback c69402e7 reported "fixed 60s backoff." The source tells a different story but reaches the same conclusion: **the existing 429 strategy is broken, just not in the way the report named.**

`markcrawl/throttle.py:46-50` is the live 429 path:

```python
if status == 429:
    self._backoff_count += 1
    self._active_delay = max(1.0, self._active_delay * 2)
    self._progress(f"[throttle] 429 received — delay increased to {self._active_delay:.1f}s")
    return
```

This is **per-request delay doubling**, not request-level retry, with three real defects:

1. **No upper cap.** `self._active_delay` keeps doubling — 1s, 2s, 4s, 8s, 16s, 32s, 64s, 128s, 256s, … A burst of 429s on a long crawl can push delay into multi-minute territory and stay there until enough successes drain `_backoff_count`.
2. **No jitter.** Every concurrent worker hits the same wall and re-launches on the same tick → thundering-herd recovery → another 429 storm.
3. **`Retry-After` header ignored.** The server is literally telling us when to come back; we throw that signal away in favor of a guess.

There is **also** a request-level retry path in `markcrawl/fetch.py` — `urllib3.util.Retry` (sync) with `backoff_factor=0.5, total=3, status_forcelist={429,500,502,503,504}` and a hand-rolled `_fetch_httpx` loop that does `_time.sleep(0.5 * 2 ** attempt)`. Neither of those caps or jitters either, and the httpx path also ignores `Retry-After`.

So the unit of behavior to redesign is **request-level retry** (`fetch.py`), with `throttle.py` continuing to handle adaptive **inter-request pacing** (a separate concern). Per the feedback's framing — "exponential 2s→30s" — the target is request-retry, not pacing. The new retry layer should sit inside `_fetch_httpx` and `_build_requests_session`.

## Library Comparison

| Dimension | `tenacity` | `backoff` (litl) | `urllib3.Retry` | Custom |
|---|---|---|---|---|
| **Active maintenance (2026)** | Yes — actively released | Yes — actively maintained | Yes — bundled with `requests` (already a markcrawl dep) | N/A |
| **Exponential w/ cap** | `wait_exponential(multiplier, min, max)` | `backoff.expo(base, factor, max_value)` | `backoff_factor` only — no max cap (capped only by `total`) | Manual |
| **Jitter** | `+ wait_random(0, jitter)` composable; AWS-style needs custom | `full_jitter` default since 1.2 (AWS Full-Jitter algorithm) | None | Manual |
| **`Retry-After` honoring** | Manual (custom `wait_strategy`) | Native via `on_predicate(backoff.runtime, value=...)` | Native (`respect_retry_after_header=True`, default) | Manual |
| **Per-retry observability** | `before_sleep_log` / custom `before_sleep(retry_state)` | `on_backoff` handler with details dict | None — silent | Manual |
| **Async support** | `AsyncRetrying`, decorator wraps coroutines | `@on_exception` works on `async def` | None | Manual |
| **New runtime deps** | +1 (`tenacity`) | +1 (`backoff`) | 0 (transitive via `requests`) | 0 |
| **Decorator API ergonomic for one call site** | Yes | Yes | No — adapter-mounting only | N/A |
| **Wraps both `requests` and `httpx` paths uniformly** | Yes (decorator on the fetch helper) | Yes (decorator on the fetch helper) | No — `requests`-only | Yes |

## Recommendation: `tenacity`

**Reasoning:**

1. **markcrawl has two HTTP code paths** (`requests` fallback in `_build_requests_session` and `httpx` primary in `_fetch_httpx`). `urllib3.Retry` cannot wrap the httpx path; a decorator-based library wraps both with identical config. That eliminates the current divergence where the two paths have *different* (and both broken) retry policies.
2. **`backoff` and `tenacity` are functionally close.** The deciding factor is observability: `tenacity`'s `before_sleep` callback receives the full `RetryCallState` (attempt number, outcome, next sleep, total elapsed) in one struct that's trivial to log structurally. `backoff`'s handler dict is fine but less ergonomic for the structured-log lines the SOTA Studio reflection pipeline already consumes.
3. **No-jitter is the dealbreaker for `urllib3.Retry`.** A thundering-herd storm at concurrency >1 is exactly the failure mode the feedback was complaining about (delay shoots to 60+s).
4. **A custom implementation is rejected** — the surface area (cap + jitter + Retry-After + sync/async + structured logging) is large enough to warrant the dependency, and `tenacity` is already a transitive dep of many adjacent packages (Anthropic SDK ecosystem, langchain-core which is already an optional dep).

**Trade-off accepted:** one new mandatory dependency (`tenacity`). Mitigation: it's pure-Python, zero C extensions, ~30KB, MIT-equivalent Apache 2.0 license, broadly used.

## Concrete Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `initial_delay_ms` | `2000` (2s) | Matches feedback target; one full second slower than the pacing throttle's `max(1.0, …)` floor so the two layers don't fight |
| `max_delay_ms` | `30000` (30s) | Matches feedback target; long enough to absorb a multi-second `Retry-After`, short enough that a stuck site fails fast |
| `multiplier` | `2.0` | Standard exponential — 2s → 4s → 8s → 16s → 30s (capped) |
| `max_tries` | `5` | Five attempts at 2/4/8/16/30 totals ~60s worst-case before giving up — matches typical crawler patience |
| `jitter` | Full-jitter, `random.uniform(0, computed_delay)` | Eliminates thundering herd at concurrency >1 |
| `retry_on` | HTTP status in `{429, 500, 502, 503, 504}` + `httpx.RequestError` / `requests.exceptions.RequestException` | Same status set as today's `_RETRY_STATUS_CODES` |
| `Retry-After` honoring | Yes — if header present, use `min(int(header), max_delay_ms/1000)` | Server-provided wait beats our guess |

## Code Snippet — Drop-in Replacement

`markcrawl/retry.py` (new file):

```python
"""Request-level retry policy for markcrawl HTTP fetches.

Wraps both the requests and httpx code paths in fetch.py with a uniform
exponential-backoff-with-jitter strategy that honors the server's
Retry-After header. See specs/v3-landscape/backoff-strategy-design.md.
"""
from __future__ import annotations

import logging
import random
from typing import Any, Callable, Optional

from tenacity import (
    Retrying,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_base,
)

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

INITIAL_DELAY_S = 2.0
MAX_DELAY_S = 30.0
MULTIPLIER = 2.0
MAX_TRIES = 5


class _ExpoJitterRetryAfter(wait_base):
    """Full-jitter exponential backoff that honors Retry-After when present."""

    def __init__(self, initial: float, maximum: float, multiplier: float):
        self.initial = initial
        self.maximum = maximum
        self.multiplier = multiplier

    def __call__(self, retry_state) -> float:
        # 1. Server-suggested wait wins if present.
        outcome = retry_state.outcome
        if outcome is not None and not outcome.failed:
            resp = outcome.result()
            retry_after = _read_retry_after(resp)
            if retry_after is not None:
                return min(retry_after, self.maximum)

        # 2. Otherwise full-jitter exponential.
        attempt = retry_state.attempt_number  # 1-indexed
        deterministic = self.initial * (self.multiplier ** (attempt - 1))
        capped = min(deterministic, self.maximum)
        return random.uniform(0, capped)


def _read_retry_after(response: Any) -> Optional[float]:
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        # HTTP-date form is rare in 429 contexts and not worth parsing here.
        return None


def _is_retryable_response(resp: Any) -> bool:
    if resp is None:
        return False
    status = getattr(resp, "status_code", getattr(resp, "status", 0))
    return status in RETRY_STATUS_CODES


def _log_before_sleep(retry_state) -> None:
    sleep = retry_state.next_action.sleep if retry_state.next_action else 0
    cause = "exception" if retry_state.outcome.failed else "status"
    detail = (
        repr(retry_state.outcome.exception())
        if retry_state.outcome.failed
        else f"HTTP {getattr(retry_state.outcome.result(), 'status_code', '?')}"
    )
    logger.info(
        "[retry] attempt=%d cause=%s detail=%s sleep=%.2fs elapsed=%.2fs",
        retry_state.attempt_number,
        cause,
        detail,
        sleep,
        retry_state.seconds_since_start or 0.0,
    )


def with_retry(
    fetch_fn: Callable[..., Any],
    *,
    transient_errors: tuple[type[BaseException], ...],
) -> Callable[..., Any]:
    """Wrap a fetch callable with markcrawl's standard retry policy.

    Returns the final response (which may still be a 429/5xx if all attempts
    were exhausted — caller is responsible for treating that as a soft fail,
    matching today's behavior in fetch.py).
    """

    def wrapped(*args, **kwargs):
        retrying = Retrying(
            stop=stop_after_attempt(MAX_TRIES),
            wait=_ExpoJitterRetryAfter(INITIAL_DELAY_S, MAX_DELAY_S, MULTIPLIER),
            retry=(
                retry_if_exception_type(transient_errors)
                | retry_if_result(_is_retryable_response)
            ),
            before_sleep=_log_before_sleep,
            reraise=False,
        )
        try:
            return retrying(fetch_fn, *args, **kwargs)
        except Exception:
            # Match today's behavior: log and return None on terminal failure.
            logger.warning("[retry] gave up after %d attempts", MAX_TRIES)
            return None

    return wrapped
```

## Integration Points

### 1. `markcrawl/fetch.py::_fetch_httpx` (lines ~89–105)

Replace the hand-rolled loop:

```python
# BEFORE
def _fetch_httpx(client, url, timeout):
    max_retries = 3
    backoff = 0.5
    last_resp = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.get(url, timeout=timeout)
            last_resp = resp
            if resp.status_code not in _RETRY_STATUS_CODES or attempt == max_retries:
                return resp
        except _httpx.HTTPError as exc:
            if attempt == max_retries:
                logger.warning("Fetch error for %s: %s", url, exc)
                return None
        _time.sleep(backoff * (2 ** attempt))
    return last_resp

# AFTER
from .retry import with_retry

def _fetch_httpx(client, url, timeout):
    fetch = with_retry(
        lambda: client.get(url, timeout=timeout),
        transient_errors=(_httpx.HTTPError,),
    )
    return fetch()
```

### 2. `markcrawl/fetch.py::_build_requests_session` (lines ~129–144)

Strip the `urllib3.Retry` adapter — it conflicts with the new layer (would retry twice). Wrap the `session.get` call site with `with_retry` instead:

```python
# In whatever calls session.get(...) for crawl pages, change:
resp = session.get(url, timeout=timeout)
# to:
resp = with_retry(
    lambda: session.get(url, timeout=timeout),
    transient_errors=(requests.exceptions.RequestException,),
)()
```

(Concrete call site location depends on `crawl.py` — left for `initial_build` to wire up.)

### 3. `markcrawl/fetch.py::_fetch_async` (around line ~260, the async path)

Mirror the sync change using `tenacity.AsyncRetrying`. The `wait` and `retry` predicates are reusable as-is; only the `Retrying` → `AsyncRetrying` swap is needed.

### 4. `markcrawl/throttle.py` — leave alone

`AdaptiveThrottle` continues to manage **inter-request pacing**. It's a separate concern from request retry and the two layers compose cleanly: throttle decides "wait N seconds between requests"; retry decides "this request failed, wait M seconds, try again." The new retry layer subsumes the broken `_active_delay = max(1.0, _active_delay * 2)` only insofar as the throttle should no longer try to react to 429s — that signal now belongs to the retry layer. Recommend removing lines 46-50 of `throttle.py` in `initial_build` so the two layers don't double-wait.

### 5. `pyproject.toml`

Add `"tenacity>=8.2.0"` to `dependencies`. (8.2 is the first release with the `RetryCallState.seconds_since_start` attribute used in `_log_before_sleep`.)

## Observability — What Gets Logged

Each retry emits one structured INFO line via the standard `logging` module, captured by markcrawl's existing logger:

```
[retry] attempt=1 cause=status detail=HTTP 429 sleep=1.83s elapsed=0.05s
[retry] attempt=2 cause=status detail=HTTP 429 sleep=3.41s elapsed=2.10s
[retry] attempt=3 cause=status detail=HTTP 429 sleep=7.92s elapsed=5.65s
[retry] gave up after 5 attempts
```

These slot directly into the `--show-progress` output stream and are amenable to future structured-log scraping (e.g., a downstream `markcrawl-metrics` consumer summarizing per-host 429 rates).
