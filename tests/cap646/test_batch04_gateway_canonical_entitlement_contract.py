"""CI contract: batch04 gateway entitlement must resolve canonical_id() — matches runtime."""

from __future__ import annotations

import pytest

PENDING_REUSED_CANONICAL: dict[int, int] = {
    159: 103,
}
ELITE_GATED_CANONICALS = frozenset({103, 161})
OVERLAP_BATCH01 = frozenset({175})


@pytest.mark.parametrize("duplicate_id,canonical_id", list(PENDING_REUSED_CANONICAL.items()))
def test_canonical_id_mapping(duplicate_id: int, canonical_id: int) -> None:
    from cap646.catalog import canonical_id as resolve_canonical

    assert resolve_canonical(duplicate_id) == canonical_id


@pytest.mark.parametrize("duplicate_id,canonical_id", list(PENDING_REUSED_CANONICAL.items()))
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


@pytest.mark.parametrize("capability_id,canonical_id", [(159, 103)])
@pytest.mark.asyncio
async def test_elite_gated_pending_reused_denied_at_gateway_for_free(
    capability_id: int, canonical_id: int
) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "free", "email": f"leak-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "free"},
    )
    assert result.get("error") == "entitlement_denied"
    assert result.get("success") is False
    assert result.get("production_spine") is None
    ent = result.get("entitlement") or {}
    assert ent.get("allowed") is False
    assert ent.get("capability_id") == canonical_id
    assert ent.get("reason") in {"teaser", "tier_insufficient"}


@pytest.mark.parametrize("capability_id,canonical_id", [(159, 103)])
@pytest.mark.asyncio
async def test_elite_gated_pending_reused_allowed_for_elite_tier(
    capability_id: int, canonical_id: int
) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "elite", "email": f"elite-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "elite"},
    )
    assert result.get("success") is True
    assert result.get("production_spine") == "batch04"
    link = result.get("catalog_link") or {}
    assert link.get("duplicate_of") == canonical_id
    assert link.get("classification") == "REUSED-LINK"


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01))
@pytest.mark.asyncio
async def test_overlap_batch01_routes_via_gateway(capability_id: int) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "pro", "email": f"overlap-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result.get("success") is True
    assert result.get("production_spine") == "batch01"


@pytest.mark.asyncio
async def test_distinct_whale_183_uses_own_canonical_not_130() -> None:
    from cap646.catalog import canonical_id as resolve_canonical
    from cap646.entitlements import entitlement_engine
    from cap646.institutional_gateway import gateway_execute

    assert resolve_canonical(183) == 183
    user = {"tier": "free", "email": "whale-free@blackdark.local"}
    runtime_ent = await entitlement_engine.check(183, user=user)
    assert runtime_ent.get("allowed") is True

    result = await gateway_execute(183, user=user, params={"symbol": "BTC", "tier": "free"})
    assert result.get("success") is True
    assert result.get("production_spine") == "batch04"
    link = result.get("catalog_link") or {}
    assert link.get("duplicate_of") == 130
    assert link.get("classification") == "REUSED-LINK"


@pytest.mark.parametrize("capability_id", [161])
@pytest.mark.asyncio
async def test_elite_gated_batch04_denied_for_free(capability_id: int) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "free", "email": f"elite-deny-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "free"},
    )
    assert result.get("error") == "entitlement_denied"
    assert result.get("success") is False


@pytest.mark.parametrize("capability_id", sorted({151, 189, 194}))
@pytest.mark.asyncio
async def test_batch04_dedicated_free_or_pro_allowed_at_gateway(capability_id: int) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "pro", "email": f"pro-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result.get("success") is True
    assert result.get("production_spine") == "batch04"
