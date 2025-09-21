from __future__ import annotations

import time
from typing import Dict


class TokenBucket:
    def __init__(self, rate_per_minute: int, burst: int):
        self.rate = rate_per_minute / 60.0
        self.capacity = float(burst)
        self.tokens = float(burst)
        self.timestamp = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.timestamp) * self.rate)
        self.timestamp = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


_buckets: Dict[str, TokenBucket] = {}


def check_rate_limit(key: str, rate_per_minute: int = 60, burst: int = 10) -> bool:
    bucket = _buckets.get(key)
    if not bucket:
        bucket = TokenBucket(rate_per_minute, burst)
        _buckets[key] = bucket
    return bucket.allow()


