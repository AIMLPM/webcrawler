"""Request-level retry policy for markcrawl HTTP fetches.

Wraps both the requests and httpx code paths in fetch.py with a uniform
exponential-backoff-with-jitter strategy that honors the server's
Retry-After header. See specs/v3-landscape/backoff-strategy-design.md.

Policy summary:
- 5 attempts max
- Full-jitter exponential backoff, 2s -> 30s cap
- Honor Retry-After header on 429 responses (capped at MAX_DELAY_S)
- Structured INFO log on every retry via the standard ``logging`` module
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_random_exponential,
)
from tenacity.wait import wait_base

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# Tenable defaults from the v3 landscape backoff-strategy design.
INITIAL_DELAY_S = 2.0
MAX_DELAY_S = 30.0
MULTIPLIER = 2.0
MAX_TRIES = 5


class _ExpoJitterRetryAfter(wait_base):
    """Full-jitter exponential backoff that honors Retry-After when present.

    Delegates the jitter math to ``tenacity.wait_random_exponential`` so the
    distribution is identical to vanilla tenacity backoff in the no-header
    case. When the server returns a parseable ``Retry-After`` header, that
    value (clamped to ``MAX_DELAY_S``) wins over the computed jitter.
    """

    def __init__(self, multiplier: float, maximum: float):
        self._maximum = maximum
        # Tenacity's wait_random_exponential gives full-jitter exponential:
        #   sleep = uniform(0, multiplier * 2 ** (attempt - 1)), capped at max.
        self._jitter = wait_random_exponential(multiplier=multiplier, max=maximum)

    def __call__(self, retry_state) -> float:
        # 1. Server-suggested wait wins if present and parseable.
        outcome = retry_state.outcome
        if outcome is not None and not outcome.failed:
            resp = outcome.result()
            retry_after = _read_retry_after(resp)
            if retry_after is not None:
                return min(retry_after, self._maximum)

        # 2. Otherwise fall back to full-jitter exponential.
        return self._jitter(retry_state)


def _read_retry_after(response: Any) -> Optional[float]:
    """Parse the Retry-After header (delta-seconds form). Returns None if absent
    or not a simple numeric value. HTTP-date form is intentionally not parsed —
    it's rare in 429 contexts and the exponential fallback covers the gap.
    """
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _is_retryable_response(resp: Any) -> bool:
    """True if the response carries a status code we should retry on."""
    if resp is None:
        return False
    status = getattr(resp, "status_code", getattr(resp, "status", 0))
    return status in RETRY_STATUS_CODES


def _log_before_sleep(retry_state) -> None:
    """Emit a structured INFO line for each retry attempt.

    Format: ``[retry] attempt=N status=... url=... sleep=Xs elapsed=Ys``.
    Captured by markcrawl's existing logger and amenable to downstream
    structured-log scraping.
    """
    sleep = retry_state.next_action.sleep if retry_state.next_action else 0.0
    elapsed = retry_state.seconds_since_start or 0.0
    outcome = retry_state.outcome

    status: str
    detail: str
    url = "<unknown>"
    try:
        if outcome is None:
            status = "?"
            detail = "no-outcome"
        elif outcome.failed:
            exc = outcome.exception()
            status = "exception"
            detail = repr(exc)
            # Best-effort URL pull. Several libraries (httpx, requests) hide
            # the request behind a descriptor that can raise on access when
            # the exception was constructed without a bound request — guard
            # the whole lookup so logging never breaks the retry loop.
            try:
                req = getattr(exc, "request", None)
                if req is not None:
                    url = str(getattr(req, "url", url))
            except Exception:
                pass
        else:
            resp = outcome.result()
            code = getattr(resp, "status_code", getattr(resp, "status", "?"))
            status = str(code)
            detail = f"HTTP {code}"
            try:
                req = getattr(resp, "request", None)
                if req is not None:
                    url = str(getattr(req, "url", url))
                else:
                    url = str(getattr(resp, "url", url))
            except Exception:
                pass
    except Exception as log_exc:  # pragma: no cover - defensive only
        status = "?"
        detail = f"log-error: {log_exc!r}"

    logger.info(
        "[retry] attempt=%d status_code=%s url=%s sleep=%.2fs elapsed=%.2fs detail=%s",
        retry_state.attempt_number,
        status,
        url,
        sleep,
        elapsed,
        detail,
    )


def _extract_url(args: tuple, kwargs: dict) -> str:
    """Best-effort URL extraction from a fetch_fn's call arguments for use
    in terminal-failure log lines (v3 SRE persona feedback). httpx + requests
    accept the URL as the first positional arg or as ``url=...``. Falls back
    to ``<unknown>`` rather than raising so logging never breaks the retry
    flow."""
    try:
        if "url" in kwargs and isinstance(kwargs["url"], str):
            return kwargs["url"]
        if args and isinstance(args[0], str):
            return args[0]
        if args:
            url_attr = getattr(args[0], "url", None)
            if url_attr is not None:
                return str(url_attr)
    except Exception:
        pass
    return "<unknown>"


def with_retry(
    fetch_fn: Callable[..., Any],
    *,
    transient_errors: tuple[type[BaseException], ...],
) -> Callable[..., Any]:
    """Wrap a no-arg fetch callable with markcrawl's standard retry policy.

    On terminal failure (all attempts exhausted with an exception), returns
    ``None`` to match today's caller behavior. On terminal failure where the
    last attempt produced a retryable HTTP response (e.g. 429), returns that
    response so the caller can treat it as a soft fail.
    """

    def wrapped(*args, **kwargs):
        retrying = Retrying(
            stop=stop_after_attempt(MAX_TRIES),
            wait=_ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S),
            retry=(
                retry_if_exception_type(transient_errors)
                | retry_if_result(_is_retryable_response)
            ),
            before_sleep=_log_before_sleep,
            reraise=False,
        )
        # v3 (SRE persona feedback round 1): extract URL for terminal-failure
        # logs so operators can see WHICH endpoint exhausted retries.
        url = _extract_url(args, kwargs)
        try:
            return retrying(fetch_fn, *args, **kwargs)
        except RetryError as retry_err:
            # Retries exhausted: tenacity wraps the final outcome here.
            last_outcome = retry_err.last_attempt
            if last_outcome is not None and not last_outcome.failed:
                # Final attempt produced a retryable HTTP response (e.g. 429
                # that never recovered). Hand it back so the caller can treat
                # it as a soft fail — mirrors the pre-tenacity behavior.
                # v3: ERROR (was WARN) per SRE persona feedback — terminal
                # retry exhaustion is operationally significant; should
                # surface in default logging.
                logger.error(
                    "[retry] gave up after %d attempts on retryable status: url=%s",
                    MAX_TRIES,
                    url,
                )
                return last_outcome.result()
            # Final attempt raised a transient exception. Match the pre-v0.10
            # callers in fetch.py that returned None on terminal failure.
            logger.error(
                "[retry] gave up after %d attempts: url=%s err=%r",
                MAX_TRIES,
                url,
                retry_err,
            )
            return None

    return wrapped


def with_retry_async(
    fetch_fn: Callable[..., Any],
    *,
    transient_errors: tuple[type[BaseException], ...],
) -> Callable[..., Any]:
    """Async sibling of :func:`with_retry` for ``httpx.AsyncClient`` paths.

    Uses tenacity's :class:`AsyncRetrying` so the same wait/retry/log policy
    applies to coroutines. Returns an async callable.
    """

    async def wrapped(*args, **kwargs):
        retrying = AsyncRetrying(
            stop=stop_after_attempt(MAX_TRIES),
            wait=_ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S),
            retry=(
                retry_if_exception_type(transient_errors)
                | retry_if_result(_is_retryable_response)
            ),
            before_sleep=_log_before_sleep,
            reraise=False,
        )
        url = _extract_url(args, kwargs)
        try:
            return await retrying(fetch_fn, *args, **kwargs)
        except RetryError as retry_err:
            last_outcome = retry_err.last_attempt
            if last_outcome is not None and not last_outcome.failed:
                logger.error(
                    "[retry] gave up after %d attempts on retryable status: url=%s",
                    MAX_TRIES,
                    url,
                )
                return last_outcome.result()
            logger.error(
                "[retry] gave up after %d attempts: url=%s err=%r",
                MAX_TRIES,
                url,
                retry_err,
            )
            return None

    return wrapped
