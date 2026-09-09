"""Retry taxonomy, bounded backoff, and jitter (ERR-008, ERR-009)."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from failure.dimensions import RetryPolicy

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryBudget:
    max_attempts: int = 5
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 30.0
    jitter_ratio: float = 0.25


DEFAULT_BUDGET = RetryBudget()


def classify_retry_policy(
    *,
    status_code: int | None = None,
    failure_class: str | None = None,
    indeterminate: bool = False,
    validation: bool = False,
    auth: bool = False,
) -> RetryPolicy:
    if indeterminate:
        return RetryPolicy.RECONCILE_FIRST
    if validation or auth:
        return RetryPolicy.DO_NOT_RETRY
    if status_code == 429:
        return RetryPolicy.SAFE_AUTO_RETRY
    if status_code in {502, 503, 504}:
        return RetryPolicy.SAFE_AUTO_RETRY
    if status_code and 400 <= status_code < 500:
        return RetryPolicy.DO_NOT_RETRY
    if failure_class in {"PAYMENT_PROVIDER", "BILLING", "RECONCILIATION"}:
        return RetryPolicy.RECONCILE_FIRST
    if failure_class in {"VALIDATION", "AUTHENTICATION", "AUTHORIZATION", "SECURITY"}:
        return RetryPolicy.DO_NOT_RETRY
    if failure_class in {"TIMEOUT", "NETWORK", "UPSTREAM", "CACHE", "QUEUE"}:
        return RetryPolicy.SAFE_AUTO_RETRY
    return RetryPolicy.SAFE_USER_RETRY


def compute_backoff(attempt: int, budget: RetryBudget = DEFAULT_BUDGET, *, retry_after: int | None = None) -> float:
    if retry_after is not None and retry_after > 0:
        return float(retry_after)
    exp = min(budget.max_delay_seconds, budget.base_delay_seconds * (2 ** max(0, attempt - 1)))
    jitter = exp * budget.jitter_ratio * random.random()
    return min(budget.max_delay_seconds, exp + jitter)


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    budget: RetryBudget = DEFAULT_BUDGET,
    retry_policy: RetryPolicy = RetryPolicy.SAFE_AUTO_RETRY,
    retry_after: int | None = None,
    on_retry: Callable[[int, float], None] | None = None,
) -> T:
    if retry_policy in {RetryPolicy.DO_NOT_RETRY, RetryPolicy.RECONCILE_FIRST}:
        return fn()
    last_exc: Exception | None = None
    for attempt in range(1, budget.max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt >= budget.max_attempts:
                break
            delay = compute_backoff(attempt, budget, retry_after=retry_after)
            if on_retry:
                on_retry(attempt, delay)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
