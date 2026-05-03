"""Unit tests for markcrawl.retry — exponential backoff with jitter, Retry-After
honoring, and exhaust-then-return-last-response semantics.

These tests cover the v0.10.0 replacement of the hand-rolled doubling loops
that previously lived in fetch.py and throttle.py. See
specs/v3-landscape/backoff-strategy-design.md.
"""
from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from markcrawl.retry import (
    INITIAL_DELAY_S,
    MAX_DELAY_S,
    MAX_TRIES,
    MULTIPLIER,
    RETRY_STATUS_CODES,
    _ExpoJitterRetryAfter,
    _is_retryable_response,
    _read_retry_after,
    with_retry,
)


def _resp(status_code: int, retry_after: str | None = None):
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return SimpleNamespace(status_code=status_code, headers=headers)


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------

class TestReadRetryAfter:
    def test_returns_float_for_integer_header(self):
        assert _read_retry_after(_resp(429, "5")) == 5.0

    def test_returns_float_for_decimal_header(self):
        assert _read_retry_after(_resp(429, "2.5")) == 2.5

    def test_lowercase_header_works(self):
        resp = SimpleNamespace(status_code=429, headers={"retry-after": "3"})
        assert _read_retry_after(resp) == 3.0

    def test_returns_none_when_header_absent(self):
        assert _read_retry_after(_resp(429)) is None

    def test_returns_none_for_http_date_form(self):
        # HTTP-date form is intentionally not parsed.
        assert _read_retry_after(_resp(429, "Wed, 21 Oct 2026 07:28:00 GMT")) is None

    def test_returns_none_for_negative(self):
        assert _read_retry_after(_resp(429, "-1")) is None

    def test_returns_none_when_no_headers_attr(self):
        assert _read_retry_after(SimpleNamespace(status_code=429)) is None


# ---------------------------------------------------------------------------
# Status detection
# ---------------------------------------------------------------------------

class TestIsRetryableResponse:
    @pytest.mark.parametrize("code", sorted(RETRY_STATUS_CODES))
    def test_retryable_codes(self, code):
        assert _is_retryable_response(_resp(code)) is True

    @pytest.mark.parametrize("code", [200, 201, 301, 304, 400, 401, 403, 404])
    def test_non_retryable_codes(self, code):
        assert _is_retryable_response(_resp(code)) is False

    def test_none_response(self):
        assert _is_retryable_response(None) is False


# ---------------------------------------------------------------------------
# Wait strategy
# ---------------------------------------------------------------------------

class TestExpoJitterRetryAfter:
    def test_retry_after_header_overrides_jitter(self):
        wait = _ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S)
        retry_state = SimpleNamespace(
            outcome=SimpleNamespace(
                failed=False,
                result=lambda: _resp(429, "7"),
            ),
            attempt_number=1,
        )
        assert wait(retry_state) == 7.0

    def test_retry_after_clamped_to_max(self):
        wait = _ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S)
        retry_state = SimpleNamespace(
            outcome=SimpleNamespace(
                failed=False,
                result=lambda: _resp(429, "9999"),
            ),
            attempt_number=1,
        )
        assert wait(retry_state) == MAX_DELAY_S

    def test_falls_back_to_jitter_when_no_header(self):
        wait = _ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S)
        retry_state = SimpleNamespace(
            outcome=SimpleNamespace(
                failed=False,
                result=lambda: _resp(429),
            ),
            attempt_number=3,
        )
        # Should be in [0, multiplier * 2 ** (attempt-1)] = [0, 8] capped at 30.
        delay = wait(retry_state)
        assert 0 <= delay <= MAX_DELAY_S

    def test_falls_back_to_jitter_when_outcome_failed(self):
        wait = _ExpoJitterRetryAfter(multiplier=MULTIPLIER, maximum=MAX_DELAY_S)
        retry_state = SimpleNamespace(
            outcome=SimpleNamespace(failed=True),
            attempt_number=2,
        )
        delay = wait(retry_state)
        assert 0 <= delay <= MAX_DELAY_S


# ---------------------------------------------------------------------------
# with_retry decorator integration
# ---------------------------------------------------------------------------

class TestWithRetry:
    def test_success_first_attempt_no_retry(self):
        calls = []

        def ok():
            calls.append(1)
            return _resp(200)

        out = with_retry(ok, transient_errors=(Exception,))()
        assert len(calls) == 1
        assert out.status_code == 200

    def test_recovers_after_one_429(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                return _resp(429, "0")  # retry-after=0 → no wall sleep
            return _resp(200)

        out = with_retry(flaky, transient_errors=(Exception,))()
        assert len(calls) == 2
        assert out.status_code == 200

    def test_exhausts_and_returns_last_response_on_persistent_429(self):
        calls = []

        def err():
            calls.append(1)
            return _resp(429, "0")

        out = with_retry(err, transient_errors=(Exception,))()
        assert len(calls) == MAX_TRIES
        # Important: returns the final 429 (not None) so the caller can
        # treat it as a soft fail, mirroring pre-tenacity behavior.
        assert out is not None
        assert out.status_code == 429

    def test_returns_none_on_persistent_exception(self):
        def boom():
            raise ValueError("nope")

        # Force-zero the wait so the test runs fast.
        with patch("markcrawl.retry._ExpoJitterRetryAfter.__call__", return_value=0):
            out = with_retry(boom, transient_errors=(ValueError,))()
        assert out is None

    def test_non_transient_exception_is_not_retried(self):
        calls = []

        def boom():
            calls.append(1)
            raise RuntimeError("not in transient_errors tuple")

        # RuntimeError is not in the transient tuple → tenacity raises out.
        with pytest.raises(RuntimeError):
            with_retry(boom, transient_errors=(ValueError,))()
        assert len(calls) == 1

    def test_non_retryable_status_is_not_retried(self):
        calls = []

        def four_oh_four():
            calls.append(1)
            return _resp(404)

        out = with_retry(four_oh_four, transient_errors=(Exception,))()
        assert len(calls) == 1
        assert out.status_code == 404

    def test_retry_after_is_honored_end_to_end(self):
        # Server says Retry-After: 1. Verify we waited at least that long
        # between attempts (one retry → ~1s elapsed minimum).
        calls = []

        def slow_recovery():
            calls.append(1)
            if len(calls) == 1:
                return _resp(429, "1")
            return _resp(200)

        t0 = time.time()
        out = with_retry(slow_recovery, transient_errors=(Exception,))()
        elapsed = time.time() - t0
        assert out.status_code == 200
        assert elapsed >= 0.95  # ~1s minus scheduling slop


# ---------------------------------------------------------------------------
# Constants — sanity check policy values from the v3 landscape design.
# ---------------------------------------------------------------------------

class TestPolicyConstants:
    def test_initial_delay_matches_design(self):
        assert INITIAL_DELAY_S == 2.0

    def test_max_delay_matches_design(self):
        assert MAX_DELAY_S == 30.0

    def test_multiplier_matches_design(self):
        assert MULTIPLIER == 2.0

    def test_max_tries_matches_design(self):
        assert MAX_TRIES == 5

    def test_status_codes_match_design(self):
        assert RETRY_STATUS_CODES == frozenset({429, 500, 502, 503, 504})
