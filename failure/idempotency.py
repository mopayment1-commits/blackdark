"""Durable idempotency facade over api/idempotency (ERR-007)."""

from __future__ import annotations

from typing import Any

from api import idempotency as _legacy


def check_idempotency(key: str | None) -> tuple[bool, dict[str, Any] | None]:
    return _legacy.check_idempotency(key)


def store_idempotency(key: str | None, status_code: int, body: dict[str, Any]) -> None:
    _legacy.store_idempotency(key, status_code, body)


def idempotent_response(key: str | None, status_code: int, body: dict[str, Any]):
    return _legacy.idempotent_response(key, status_code, body)


SENSITIVE_OPERATIONS = frozenset(
    {
        "billing.payment",
        "billing.subscription_change",
        "account.delete",
        "report.paid_generate",
        "execution.order",
    }
)


def requires_idempotency(operation: str) -> bool:
    return operation in SENSITIVE_OPERATIONS or operation.startswith("billing.")
