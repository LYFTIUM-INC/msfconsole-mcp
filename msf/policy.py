#!/usr/bin/env python3
import time
from collections import deque
from typing import Deque

DEFAULT_DENY = (
    "rm ",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",  # fork bomb
)


def is_denied(command: str) -> bool:
    cmd = command.strip().lower()
    return any(bad in cmd for bad in DEFAULT_DENY)


class RateLimiter:
    def __init__(self, max_calls: int = 20, window_secs: int = 60) -> None:
        self.max_calls = max_calls
        self.window_secs = window_secs
        self.calls: Deque[float] = deque()

    def allow(self) -> bool:
        now = time.time()
        # Pop old calls
        while self.calls and now - self.calls[0] > self.window_secs:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            return False
        self.calls.append(now)
        return True
