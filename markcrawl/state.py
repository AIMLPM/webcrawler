"""Crawl state persistence — save/load for resume support."""
from __future__ import annotations

import json
import os
from collections import deque
from typing import Deque, Dict, List, Optional, Set

STATE_FILENAME = ".crawl_state.json"


def save_state(
    state_path: str,
    seen_urls: Set[str],
    seen_content: Set[str],
    to_visit: Deque[str],
    saved_count: int,
    seeds: List[str],
) -> None:
    state = {
        "seen_urls": list(seen_urls),
        "seen_content": list(seen_content),
        "to_visit": list(to_visit),
        "saved_count": saved_count,
        "seeds": seeds,
    }
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, state_path)


def load_state(state_path: str) -> Optional[Dict]:
    if not os.path.isfile(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)
