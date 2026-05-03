"""Adaptive throttle — adjusts request delay based on server response signals."""
from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AdaptiveThrottle:
    """Two-layer adaptive throttle:

    1. Crawl-delay from robots.txt (floor)
    2. Response-time proportional — slow servers get more delay

    429 / rate-limit handling is **not** in this throttle. As of v0.10.0 it
    lives in :mod:`markcrawl.retry` (request-level exponential backoff with
    jitter and ``Retry-After`` honoring). The two layers compose: throttle
    decides "wait N seconds *between* requests"; retry decides "this request
    failed, wait M seconds, try *again*". Both used to react to 429s, which
    caused double-waiting and uncapped delay drift; only the retry layer
    does now.
    """

    def __init__(self, base_delay: float, progress: Callable[[str], None]):
        self._base_delay = base_delay
        self._active_delay = base_delay
        self._response_times: List[float] = []
        self._response_time_window = 10
        self._slow_threshold = 0.5
        # Retained as a no-op attribute for backwards compatibility with
        # callers (and tests) that previously inspected ``_backoff_count``.
        # Always 0 in v0.10.0+ — see class docstring.
        self._backoff_count = 0
        self._progress = progress

    @property
    def active_delay(self) -> float:
        return self._active_delay

    @property
    def base_delay(self) -> float:
        return self._base_delay

    @base_delay.setter
    def base_delay(self, value: float) -> None:
        self._base_delay = value
        self._active_delay = value

    def update(self, response) -> None:
        """Adapt delay based on server response time.

        429 responses are intentionally ignored here — :mod:`markcrawl.retry`
        owns rate-limit backoff (with jitter and ``Retry-After`` honoring) so
        keeping a doubling-on-429 branch in the throttle would double-wait
        and undermine the retry layer's exponential schedule.
        """
        if response is None:
            return

        # Skip 429s entirely; the retry layer will have already replayed the
        # request before we ever observe a non-retryable outcome here.
        status = getattr(response, "status_code", getattr(response, "status", 0))
        if status == 429:
            return

        response_time = 0.0
        try:
            elapsed = getattr(response, "elapsed", None)
            if elapsed is not None:
                response_time = float(elapsed.total_seconds())
        except (TypeError, AttributeError):
            pass

        self._response_times.append(response_time)
        if len(self._response_times) > self._response_time_window:
            self._response_times = self._response_times[-self._response_time_window:]

        avg_response = sum(self._response_times) / len(self._response_times) if self._response_times else 0
        if avg_response > self._slow_threshold:
            self._active_delay = max(self._base_delay, avg_response * 0.5)

    @staticmethod
    def parse_crawl_delay(robots_text: str, user_agent: str = "*") -> Optional[float]:
        """Extract Crawl-delay for a given user-agent from robots.txt."""
        ua = user_agent.lower()
        current_agents: List[str] = []
        delay_by_agent: Dict[str, float] = {}

        for raw_line in robots_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip().lower()
                current_agents.append(agent)
            elif lower.startswith("crawl-delay:"):
                try:
                    val = float(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    continue
                agents_to_assign = current_agents if current_agents else ["*"]
                for agent in agents_to_assign:
                    if agent not in delay_by_agent:
                        delay_by_agent[agent] = val
                current_agents = []
            else:
                current_agents = []

        for candidate in [ua, "*"]:
            if candidate in delay_by_agent:
                return delay_by_agent[candidate]
        return None
