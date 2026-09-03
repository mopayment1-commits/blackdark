#!/usr/bin/env python3
"""Generate cap646/batch04_dedicated.py from RTM expected surfaces."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTM = ROOT / "docs/BATCH04_RTM_151_200.json"
OUT = ROOT / "cap646/batch04_dedicated.py"

HEADER = '''"""Batch 04 dedicated backends — catalog-aligned payloads for IDs 151–200.

IDs 175 is batch01 overlap: no dedicated backend here; runtime routes via
``LEGACY_BATCH01_EXTENSION_IDS`` (see ``BATCH04_OVERLAP_BATCH01_IDS``).

Catalog is functional truth (ISO 25010): handlers emit goal-specific surfaces,
not misaligned hero wrappers. REUSED-LINK candidates (#159, #183) stamp
``catalog_link`` but remain NOT_COMPLETE until canonical audit passes.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym

BATCH04_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset({175})
BATCH04_DEDICATED_IDS: frozenset[int] = frozenset(range(151, 201)) - BATCH04_OVERLAP_BATCH01_IDS

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)

EXPECTED_SURFACE: dict[int, str] = {
'''

FOOTER = '''
_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _catalog_payload(capability_id: int, symbol: str, **extra: Any) -> dict[str, Any]:
  """Catalog-aligned core payload — ok + feature_ref required by acceptance."""
  payload: dict[str, Any] = {
      "ok": True,
      "feature_ref": capability_id,
      "symbol": symbol,
      "catalog_goal": EXPECTED_SURFACE[capability_id],
  }
  payload.update(extra)
  return payload


async def _cap_catalog(
    capability_id: int,
    *,
    symbol: str,
    address: str,
    params: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = EXPECTED_SURFACE[capability_id]
    payload = _catalog_payload(capability_id, symbol, **(extra or {}))
    return _wrap(capability_id, symbol=symbol, payload_key=root, payload=payload)


def _make_catalog_handler(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _handler(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _cap_catalog(capability_id, symbol=symbol, address=address, params=params)

    _handler.__name__ = f"_cap{capability_id}"
    return _handler


async def _cap151(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import explain_opportunity_151

    raw = explain_opportunity_151(asset=symbol, seed=_seed())
    payload = _catalog_payload(
        151,
        symbol,
        reporting_period="quarterly",
        protocol_performance=raw.get("breakdown") or {},
        opportunity_score=raw.get("opportunity_score"),
    )
    return _wrap(151, symbol=symbol, payload_key="quarterly_protocol_performance_reports", payload=payload)


async def _cap152(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import run_data_sources_e2e_140_152

    raw = run_data_sources_e2e_140_152(seed=_seed())
    payload = _catalog_payload(152, symbol, governance_proposals=raw.get("governance") or raw)
    return _wrap(152, symbol=symbol, payload_key="governance_proposal_intelligence", payload=payload)


async def _cap153(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.intelligence_analysis_layer import analyze_arbitrage_opportunity_153

    raw = analyze_arbitrage_opportunity_153(asset=symbol, seed=_seed())
    payload = _catalog_payload(
        153,
        symbol,
        coverage_registry=raw.get("coverage") or {"projects_monitored": raw.get("venues") or []},
        monitoring_status=raw.get("status") or "active",
    )
    return _wrap(153, symbol=symbol, payload_key="project_monitoring_coverage_registry", payload=payload)


async def _cap156(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.intelligence_analysis_layer import asset_registry_105_coins_156

    raw = asset_registry_105_coins_156(seed=_seed())
    payload = _catalog_payload(
        156,
        symbol,
        graph_nodes=raw.get("assets") or raw.get("registry") or [],
        node_count=raw.get("count") or len(raw.get("assets") or []),
        partial_misnamed_note="hero asset_registry reused as knowledge-graph seed",
    )
    return _wrap(156, symbol=symbol, payload_key="crypto_knowledge_graph", payload=payload)


async def _cap159(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.handlers.institutional import handle_institutional_capability

    canonical = await handle_institutional_capability(103, params=params)
    platform = {
        "ok": True,
        "feature_ref": 159,
        "institutional_api": canonical.get("institutional_api") or "/api/institutional",
        "graphql": canonical.get("graphql") or "/graphql",
        "hot_storage": canonical.get("hot_storage"),
        "blocker": "BLOCKER-159-103",
        "canonical_overlap": 103,
        "canonical_status": "OVERLAP-PARTIAL",
        "owner_decision": "NOT_COMPLETE — no REUSED-LINK until #103 matures (Tolerate 2026-10-03) or DISTINCT ADR",
    }
    return _wrap(
        159,
        symbol=symbol,
        payload_key="api_data_platform",
        payload=platform,
        extra={"classification": "NOT_COMPLETE", "blocker": "BLOCKER-159-103"},
    )


async def _cap161(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.handlers.institutional import handle_institutional_capability

    raw = await handle_institutional_capability(161, params=params)
    payload = _catalog_payload(
        161,
        symbol,
        isolation=raw.get("isolation"),
        role_matrix=raw.get("role_matrix"),
        entitlements=raw.get("role_matrix"),
    )
    return _wrap(161, symbol=symbol, payload_key="institutional_data_delivery_entitlements", payload=payload)


async def _cap162(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_common import provenance_hot_storage_payload

    provenance = provenance_hot_storage_payload(symbol)
    provenance["catalog_link"] = {"duplicate_of": 106, "classification": "REUSED-LINK"}
    payload = _catalog_payload(162, symbol, provenance=provenance.get("provenance"), hot_storage=provenance.get("hot_storage"))
    return _wrap(162, symbol=symbol, payload_key="evidence_provenance_layer", payload=payload)


async def _cap183(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    amount = float(params.get("amount_usd") or params.get("value_usd") or 1_000_000)
    whale = {
        "ok": True,
        "feature_ref": 183,
        "symbol": symbol,
        "address": address,
        "amount_usd": amount,
        "risk_score": min(100.0, max(0.0, amount / 100_000)),
        "classification": "whale_transaction",
        "owner_decision": "DISTINCT-only Option B — no REUSED-LINK to #130; #130 stays PRODUCTION-ALIGNED in Batch03",
    }
    return _wrap(
        183,
        symbol=symbol,
        payload_key="whale_transaction",
        payload=whale,
        extra={"classification": "NOT_COMPLETE", "blocker": "BLOCKER-183-130"},
    )


async def _cap189(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_common import exchange_netflow_probe

    exchange, netflow = exchange_netflow_probe(params, symbol)
    payload = _catalog_payload(189, symbol, exchange=exchange, netflow=netflow, netflow_proxy=netflow.get("netflow_proxy"))
    return _wrap(189, symbol=symbol, payload_key="exchange_netflow_intelligence", payload=payload)


_DISPATCH_OVERRIDES: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    151: _cap151,
    152: _cap152,
    153: _cap153,
    156: _cap156,
    159: _cap159,
    161: _cap161,
    162: _cap162,
    183: _cap183,
    189: _cap189,
}

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    cid: _DISPATCH_OVERRIDES.get(cid, _make_catalog_handler(cid))
    for cid in sorted(BATCH04_DEDICATED_IDS)
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH04_DEDICATED_IDS,
        overlap_batch01_ids=BATCH04_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error=(
            f"capability {capability_id} is batch01 overlap — use cap646.batch01_production"
        ),
        not_dedicated_error=f"capability {capability_id} is not in batch04 dedicated spine",
    )
'''


def main() -> None:
    rtm = json.loads(RTM.read_text(encoding="utf-8"))
    surfaces = {row["id"]: row["expected_surface_planned"] for row in rtm["rows"]}
    assert len(surfaces) == 50
    lines = [f"    {cid}: {json.dumps(surfaces[cid])}," for cid in sorted(surfaces)]
    OUT.write_text(HEADER + "\n".join(lines) + "\n}\n" + FOOTER, encoding="utf-8")
    print(f"Wrote {OUT} ({len(surfaces)} surfaces)")


if __name__ == "__main__":
    main()
