"""Adaptive throttle — adjusts request delay based on server response signals."""
from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AdaptiveThrottle:
    """Three-layer adaptive throttle:

    1. Crawl-delay from robots.txt (floor)
    2. Response-time proportional — slow servers get more delay
    3. 429 backoff — double delay on rate-limit, decay on success
    """

    def __init__(self, base_delay: float, progress: Callable[[str], None]):
        self._base_delay = base_delay
        self._active_delay = base_delay
        self._response_times: List[float] = []
        self._response_time_window = 10
        self._slow_threshold = 0.5
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
        """Adapt delay based on server response time and status codes."""
        if response is None:
            return

        status = getattr(response, "status_code", getattr(response, "status", 0))
        if status == 429:
            self._backoff_count += 1
            self._active_delay = max(1.0, self._active_delay * 2)
            self._progress(f"[throttle] 429 received — delay increased to {self._active_delay:.1f}s")
            return

        if self._backoff_count > 0:
            self._backoff_count = max(0, self._backoff_count - 1)
            if self._backoff_count == 0:
                self._active_delay = self._base_delay

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
        if avg_response > self._slow_threshold and self._backoff_count == 0:
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
