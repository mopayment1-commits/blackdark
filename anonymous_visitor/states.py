"""Explicit authorization/product states — AV §2."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ProductAuthState(StrEnum):
    ANONYMOUS = "ANONYMOUS"
    FREE_ACCOUNT = "FREE_ACCOUNT"
    PAID_INDIVIDUAL = "PAID_INDIVIDUAL"
    INSTITUTIONAL = "INSTITUTIONAL"


def resolve_product_state(user: dict[str, Any] | None) -> ProductAuthState:
    if user is None:
        return ProductAuthState.ANONYMOUS
    tier = str(user.get("tier") or "free").lower().strip()
    if tier in {"institutional", "whale", "enterprise"}:
        return ProductAuthState.INSTITUTIONAL
    if tier in {"pro", "elite", "quant", "paid"}:
        return ProductAuthState.PAID_INDIVIDUAL
    return ProductAuthState.FREE_ACCOUNT


def states_status() -> dict[str, Any]:
    return {
        "states": [s.value for s in ProductAuthState],
        "default_anonymous": ProductAuthState.ANONYMOUS.value,
        "real_authorization_states": True,
    }
