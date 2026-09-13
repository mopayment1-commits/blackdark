"""Entitlement enforcement for Adaptive surfaces — spec §31 (AIE-020)."""

from __future__ import annotations

from typing import Any


async def check_adaptive_entitlement(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
    org_id: str | None = None,
) -> dict[str, Any]:
    from cap646.entitlements import entitlement_engine

    ent = await entitlement_engine.check(capability_id, user=user, org_id=org_id)
    allowed = bool(ent.get("allowed"))
    return {
        "capability_id": capability_id,
        "allowed": allowed,
        "entitlement": ent,
        "bypass_forbidden": True,
        "authority": "cap646/entitlements.py",
    }


def subscription_preview(capability_id: int, *, entitled: bool) -> dict[str, Any]:
    """Honest subscription discovery — no live claim behind paywall (spec §20)."""
    if entitled:
        return {"capability_id": capability_id, "preview_mode": "full", "upgrade_required": False}
    return {
        "capability_id": capability_id,
        "preview_mode": "metadata_only",
        "upgrade_required": True,
        "live_claim_hidden": True,
        "explanation": "Preview shows capability metadata only; live personalized results require entitlement.",
    }
