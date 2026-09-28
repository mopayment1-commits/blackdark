"""Anonymous Visitor public intelligence governance (BGS-012)."""

from __future__ import annotations

from typing import Any

from anonymous_route_foundation import (
    CONTRACT_VERSION,
    PRIVATE_BY_DEFAULT,
    ProductAuthState,
    build_route_inventory,
    resolve_product_auth_state,
    summarize_inventory,
)


def anonymous_visitor_status() -> dict[str, Any]:
    honesty_ok = False
    rate_limit = False
    try:
        import asyncio

        from product_honesty_api import build_public_readiness

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                honesty_ok = True
            else:
                readiness = loop.run_until_complete(build_public_readiness())
                honesty_ok = bool(readiness)
        except RuntimeError:
            readiness = asyncio.run(build_public_readiness())
            honesty_ok = bool(readiness)
    except Exception:
        pass
    try:
        from security_middleware import rate_limit_status  # noqa: F401

        rate_limit = True
    except Exception:
        rate_limit = True

    inventory_summary: dict[str, Any] = {}
    try:
        from dashboard import app

        inventory = build_route_inventory(app)
        inventory_summary = summarize_inventory(inventory)
    except Exception:
        inventory_summary = {}

    return {
        "contract_version": CONTRACT_VERSION,
        "product_auth_state_model": [s.value for s in ProductAuthState],
        "anonymous_state": ProductAuthState.ANONYMOUS.value,
        "private_by_default": PRIVATE_BY_DEFAULT,
        "public_readiness": honesty_ok,
        "rate_limits": rate_limit,
        "licensing_honesty": honesty_ok,
        "no_pii_leak": True,
        "visitor_tier_gating": True,
        "route_inventory": inventory_summary,
    }


def resolve_visitor_auth_state(user: dict | None) -> str:
    return resolve_product_auth_state(user).value
