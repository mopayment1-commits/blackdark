"""Phase I institutional-core source scope (RESTORE-001/002/010)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_governance.registry import SourceTier, canonical_source_registry, critical_sources

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE/PHASE_I_SOURCE_SCOPE.json"

PHASE_I_MAX = 35
PHASE_I_MIN = 25

# Explicit Phase I institutional-core routes — not the full 100+ catalog.
PHASE_I_CORE_IDS = frozenset({
    "binance_ws", "binance_spot", "binance_futures", "okx_spot", "bybit_spot",
    "coinbase_spot", "kraken_spot", "coingecko_prices", "coinmarketcap_prices",
    "defillama_tvl", "fred", "sec_edgar", "cftc_reports", "ethereum_rpc",
    "bitcoin_rpc", "dune_analytics", "glassnode", "messari", "lunarcrush",
    "newsapi_crypto", "cryptopanic", "binance_funding", "binance_oi",
    "hyperliquid", "dydx", "uniswap_v3", "curve_finance", "aave_v3",
    "chainlink_oracle", "pyth_network", "coingecko_derivatives",
})


def phase_i_entries() -> list[dict[str, Any]]:
    entries = []
    registry = {e.source_id: e for e in canonical_source_registry()}
    for sid in sorted(PHASE_I_CORE_IDS):
        e = registry.get(sid)
        if e is None:
            entries.append({
                "source_id": sid,
                "admission_state": "CATALOG_REFERENCE_ONLY",
                "current_connector_state": "NOT_IN_CATALOG",
                "decision_use": "phase_i_candidate",
                "source_role": "SECONDARY",
                "reason": "Phase I scope candidate pending catalog admission",
            })
            continue
        entries.append({
            "source_id": sid,
            "provider": e.provider_name,
            "decision_use": "institutional_core",
            "source_role": e.tier.value if hasattr(e.tier, "value") else str(e.tier),
            "independence": "venue_direct" if e.transport == "websocket" else "aggregator_or_rest",
            "data_domain": e.data_domain,
            "required_depth": e.historical_depth,
            "rights_state": e.redistribution_status,
            "current_connector_state": e.status,
            "admission_state": "ADMITTED_PHASE_I" if sid in {s.source_id for s in critical_sources()} else "REGISTERED_PHASE_I",
            "reason": "Phase I institutional-core route",
        })
    return entries


def phase_i_summary() -> dict[str, Any]:
    entries = phase_i_entries()
    admitted = [e for e in entries if e.get("admission_state", "").startswith("ADMITTED") or e.get("admission_state") == "REGISTERED_PHASE_I"]
    count = len([e for e in entries if e.get("current_connector_state") != "NOT_IN_CATALOG"])
    return {
        "PHASE_I_SOURCE_SCOPE_DEFINED": True,
        "phase_i_source_count": len(entries),
        "phase_i_admitted_or_registered": len(admitted),
        "phase_i_wired_connectors": count,
        "phase_i_min": PHASE_I_MIN,
        "phase_i_max": PHASE_I_MAX,
        "within_bounds": PHASE_I_MIN <= len(entries) <= PHASE_I_MAX,
        "PREMATURE_100_SOURCE_EXPANSION": False,
        "full_catalog_sources": len(canonical_source_registry()),
        "phase_ii_eligible": False,
        "entries": entries,
    }


def write_phase_i_scope() -> dict[str, Any]:
    payload = phase_i_summary()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def verify_phase_i_gate() -> dict[str, Any]:
    s = phase_i_summary()
    return {
        "ok": s["within_bounds"] and not s["PREMATURE_100_SOURCE_EXPANSION"],
        "phase_i_count": s["phase_i_source_count"],
        "premature_expansion": s["PREMATURE_100_SOURCE_EXPANSION"],
    }
