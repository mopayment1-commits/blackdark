"""CI contract: gateway entitlement must resolve canonical_id() — matches runtime.

Prevents REUSED-LINK split-brain where gateway.check(duplicate) allows free
but runtime.check(canonical) denies pro (GET Entitlement Bypass pattern).
"""

from __future__ import annotations

import pytest

REUSED_LINK_PAIRS: dict[int, int] = {
    106: 63,
    107: 64,
    110: 69,
    125: 85,
}
PRO_GATED_CANONICALS = frozenset({69, 85})


@pytest.mark.parametrize("duplicate_id,canonical_id", list(REUSED_LINK_PAIRS.items()))
def test_canonical_id_mapping(duplicate_id: int, canonical_id: int) -> None:
    from cap646.catalog import canonical_id as resolve_canonical

    assert resolve_canonical(duplicate_id) == canonical_id


@pytest.mark.parametrize("duplicate_id,canonical_id", list(REUSED_LINK_PAIRS.items()))
@pytest.mark.asyncio
async def test_gateway_entitlement_matches_runtime_canonical(
    duplicate_id: int, canonical_id: int
) -> None:
    from cap646.catalog import canonical_id as resolve_canonical
    from cap646.entitlements import entitlement_engine
    from cap646.institutional_gateway import gateway_execute

    assert resolve_canonical(duplicate_id) == canonical_id
    user = {"tier": "free", "email": f"contract-free-{duplicate_id}@blackdark.local"}

    runtime_ent = await entitlement_engine.check(canonical_id, user=user)
    gateway_result = await gateway_execute(
        duplicate_id, user=user, params={"symbol": "BTC", "tier": "free"}
    )
    gateway_ent = gateway_result.get("entitlement") or {}
    if not gateway_ent and isinstance(gateway_result.get("gateway"), dict):
        gateway_ent = gateway_result["gateway"].get("entitlement") or {}

    assert gateway_ent.get("allowed") == runtime_ent.get("allowed"), (
        f"#{duplicate_id}: gateway allowed={gateway_ent.get('allowed')} "
        f"runtime canonical #{canonical_id} allowed={runtime_ent.get('allowed')}"
    )
    assert gateway_ent.get("reason") == runtime_ent.get("reason")
    assert gateway_ent.get("required_tier") == runtime_ent.get("required_tier")
    assert gateway_ent.get("capability_id") == canonical_id

    if not runtime_ent.get("allowed"):
        assert gateway_result.get("error") == "entitlement_denied"
        assert gateway_result.get("success") is False
        assert gateway_result.get("production_spine") is None
        assert gateway_result.get("canonical_capability_id") == canonical_id
        assert gateway_result.get("requested_capability_id") == duplicate_id


@pytest.mark.parametrize("duplicate_id,canonical_id", [(110, 69), (125, 85)])
@pytest.mark.asyncio
async def test_pro_gated_reused_link_denied_at_gateway_not_runtime_leak(
    duplicate_id: int, canonical_id: int
) -> None:
    """Free tier must be blocked at gateway before execute_capability (no accidental allow)."""
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        duplicate_id,
        user={"tier": "free", "email": f"leak-{duplicate_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "free"},
    )
    assert result.get("error") == "entitlement_denied"
    assert result.get("success") is False
    assert result.get("production_spine") is None
    ent = result.get("entitlement") or {}
    assert ent.get("allowed") is False
    assert ent.get("capability_id") == canonical_id
    assert ent.get("reason") in {"teaser", "tier_insufficient"}


@pytest.mark.parametrize("duplicate_id,canonical_id", [(110, 69), (125, 85)])
@pytest.mark.asyncio
async def test_pro_gated_reused_link_allowed_for_pro_tier(
    duplicate_id: int, canonical_id: int
) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        duplicate_id,
        user={"tier": "pro", "email": f"pro-{duplicate_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result.get("success") is True
    assert result.get("production_spine") == "batch03"
    link = result.get("catalog_link") or {}
    assert link.get("duplicate_of") == canonical_id
    assert link.get("classification") == "REUSED-LINK"


@pytest.mark.parametrize("duplicate_id,canonical_id", [(106, 63), (107, 64)])
@pytest.mark.asyncio
async def test_free_canonical_reused_link_allowed_at_gateway(
    duplicate_id: int, canonical_id: int
) -> None:
    from cap646.entitlements import entitlement_engine
    from cap646.institutional_gateway import gateway_execute

    user = {"tier": "free", "email": f"free-{duplicate_id}@blackdark.local"}
    runtime_ent = await entitlement_engine.check(canonical_id, user=user)
    assert runtime_ent.get("allowed") is True

    result = await gateway_execute(duplicate_id, user=user, params={"symbol": "BTC", "tier": "free"})
    assert result.get("success") is True
    assert result.get("production_spine") == "batch03"
    link = result.get("catalog_link") or {}
    assert link.get("duplicate_of") == canonical_id
