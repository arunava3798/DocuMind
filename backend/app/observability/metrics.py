"""Per-request metrics tracked via a ContextVar (latency, token usage, cost)."""
from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RequestMetrics:
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    est_cost_usd: float = 0.0
    timings_ms: dict = field(default_factory=dict)


_current: ContextVar[Optional[RequestMetrics]] = ContextVar("request_metrics", default=None)


def new_request() -> RequestMetrics:
    metrics = RequestMetrics()
    _current.set(metrics)
    return metrics


def current() -> Optional[RequestMetrics]:
    return _current.get()


def record_llm_usage(
    prompt_tokens: int, completion_tokens: int, total_tokens: int, cost_usd: float
) -> None:
    metrics = _current.get()
    if metrics is None:
        return
    metrics.llm_calls += 1
    metrics.prompt_tokens += prompt_tokens
    metrics.completion_tokens += completion_tokens
    metrics.total_tokens += total_tokens
    metrics.est_cost_usd += cost_usd


@contextmanager
def timed(name: str):
    """Accumulate elapsed milliseconds for a named stage into the current request."""
    start = time.perf_counter()
    try:
        yield
    finally:
        metrics = _current.get()
        if metrics is not None:
            elapsed = (time.perf_counter() - start) * 1000
            metrics.timings_ms[name] = round(metrics.timings_ms.get(name, 0.0) + elapsed, 1)
