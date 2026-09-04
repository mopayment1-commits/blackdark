"""CI contract: batch05 REUSED-LINK #214/#245 — public GET, gateway, runtime, batch05 facade.

Locks the GET Entitlement Bypass pattern fixed for batch03/04:
gateway entitlement must match entitlement_engine.check(canonical_id),
and public GET must route via execute_capability (batch01 spine), not batch05 facade.
"""

from __future__ import annotations

import pytest

OVERLAP_BATCH01_REUSED_LINK = frozenset({214, 245})
SYMBOLS = ["BTC", "ETH"]


def _gateway_entitlement(gateway_result: dict) -> dict:
    ent = gateway_result.get("entitlement") or {}
    if not ent and isinstance(gateway_result.get("gateway"), dict):
        ent = gateway_result["gateway"].get("entitlement") or {}
    return ent


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
def test_canonical_id_is_identity(capability_id: int) -> None:
    from cap646.catalog import canonical_id as resolve_canonical

    assert resolve_canonical(capability_id) == capability_id


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
@pytest.mark.parametrize("tier", ["free", "pro", "elite"])
@pytest.mark.asyncio
async def test_gateway_entitlement_matches_runtime_canonical(capability_id: int, tier: str) -> None:
    from cap646.catalog import canonical_id as resolve_canonical
    from cap646.entitlements import entitlement_engine
    from cap646.institutional_gateway import gateway_execute

    canonical = resolve_canonical(capability_id)
    user = {"tier": tier, "email": f"contract-{tier}-{capability_id}@blackdark.local"}

    runtime_ent = await entitlement_engine.check(canonical, user=user)
    gateway_result = await gateway_execute(
        capability_id, user=user, params={"symbol": "BTC", "tier": tier}
    )
    gateway_ent = _gateway_entitlement(gateway_result)

    assert gateway_ent.get("allowed") == runtime_ent.get("allowed"), (
        f"#{capability_id} tier={tier}: gateway allowed={gateway_ent.get('allowed')} "
        f"runtime canonical #{canonical} allowed={runtime_ent.get('allowed')}"
    )
    assert gateway_ent.get("reason") == runtime_ent.get("reason")
    assert gateway_ent.get("required_tier") == runtime_ent.get("required_tier")
    assert gateway_ent.get("capability_id") == canonical

    if not runtime_ent.get("allowed"):
        assert gateway_result.get("error") == "entitlement_denied"
        assert gateway_result.get("success") is False
        assert gateway_result.get("production_spine") is None
        assert gateway_result.get("canonical_capability_id") == canonical
        assert gateway_result.get("requested_capability_id") == capability_id


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
@pytest.mark.parametrize("tier", ["free", "pro"])
@pytest.mark.asyncio
async def test_batch05_facade_entitlement_matches_runtime_canonical(
    capability_id: int, tier: str
) -> None:
    """batch05_production.execute must gate on canonical_id when user is supplied."""
    from cap646.catalog import canonical_id as resolve_canonical
    from cap646.entitlements import entitlement_engine
    from cap646.batch05_production import execute as batch05_execute

    canonical = resolve_canonical(capability_id)
    user = {"tier": tier, "email": f"facade-{tier}-{capability_id}@blackdark.local"}

    runtime_ent = await entitlement_engine.check(canonical, user=user)
    facade_result = await batch05_execute(
        capability_id, user=user, params={"symbol": "BTC", "tier": tier}
    )
    facade_ent = facade_result.get("entitlement") or {}

    if not runtime_ent.get("allowed"):
        assert facade_result.get("success") is False
        assert facade_ent.get("allowed") is False
        assert facade_ent.get("capability_id") == canonical
        return

    assert facade_result.get("success") is True
    assert facade_result.get("production_spine") == "batch05"
    assert facade_result.get("classification") == "REUSED-LINK"


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
@pytest.mark.asyncio
async def test_public_get_uses_execute_capability_batch01_spine(capability_id: int) -> None:
    """GET /api/cap646/{id} is the end-user path — must not stamp batch05 facade spine."""
    from cap646.runtime import execute_capability
    from cap978.unified import execute_unified
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    http = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
    assert http.status_code == 200
    body = http.json()

    unified = await execute_unified(capability_id, params={"symbol": "BTC", "tier": "pro"})
    runtime = await execute_capability(
        capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"}
    )

    assert body.get("success") is True
    assert body.get("production_spine") == "batch01"
    assert body.get("backend_module") == "cap646.batch01_production"
    assert unified.get("production_spine") == "batch01"
    assert runtime.get("production_spine") == "batch01"
    assert body.get("surface") == unified.get("surface") == runtime.get("surface")


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
@pytest.mark.asyncio
async def test_gateway_routes_overlap_to_batch01_spine(capability_id: int) -> None:
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user={"tier": "pro", "email": f"overlap-{capability_id}@blackdark.local"},
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result.get("success") is True
    assert result.get("production_spine") == "batch01"
    assert result.get("backend_module") == "cap646.batch01_production"


@pytest.mark.parametrize("capability_id", sorted(OVERLAP_BATCH01_REUSED_LINK))
@pytest.mark.asyncio
async def test_batch05_facade_payload_parity_with_runtime(capability_id: int) -> None:
    """Facade path (programmatic) must return same domain semantics as public runtime."""
    from cap646.batch05_production import execute as batch05_execute
    from cap646.runtime import execute_capability

    runtime = await execute_capability(
        capability_id, skip_entitlement=True, params={"symbol": "BTC"}
    )
    facade = await batch05_execute(capability_id, skip_entitlement=True, params={"symbol": "BTC"})

    assert runtime.get("success") is True
    assert facade.get("success") is True
    assert runtime.get("surface") == facade.get("surface")
    assert facade.get("catalog_link", {}).get("classification") == "REUSED-LINK"
    assert facade.get("catalog_link", {}).get("canonical_spine") == "batch01"

    if capability_id == 214:
        assert runtime.get("count", 0) > 0
        assert len(runtime.get("watchlists", {}).get("items", [])) >= 1
        assert len(facade.get("watchlists", {}).get("items", [])) >= 1
    if capability_id == 245:
        assert "freshness_chip" in runtime or "executable_fresh" in runtime
        assert "freshness_chip" in facade or "executable_fresh" in facade
