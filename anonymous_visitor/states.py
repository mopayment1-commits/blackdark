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
    from auth_service import normalize_tier

    tier = normalize_tier(user.get("tier"))
    if tier == "institutional":
        return ProductAuthState.INSTITUTIONAL
    if tier in {"pro", "elite", "quant", "whale"}:
        return ProductAuthState.PAID_INDIVIDUAL
    return ProductAuthState.FREE_ACCOUNT


def states_status() -> dict[str, Any]:
    return {
        "states": [s.value for s in ProductAuthState],
        "default_anonymous": ProductAuthState.ANONYMOUS.value,
        "real_authorization_states": True,
    }
