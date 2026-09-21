from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 5,
    base_delay: float = 0.75,
) -> T:
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as exc:
            if attempt >= max_retries or not _is_retryable(exc):
                raise
            # Exponential backoff + random jitter, matching the training kit's
            # retry-shield pattern.
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)
    raise RuntimeError("Retry loop exited unexpectedly.")

def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status in {408, 409, 429} or (status is not None and status >= 500):
        return True
    name = exc.__class__.__name__.lower()
    return any(token in name for token in ("timeout", "connection", "rate", "server"))
