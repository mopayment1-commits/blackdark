"""Unified data governance pipeline — evaluates all data truth gates."""

from __future__ import annotations

from typing import Any

from data_governance.decision_surface import build_decision_surface
from data_governance.fallback import evaluate_fallback
from data_governance.freshness import attach_data_freshness
from data_governance.gates import evaluate_data_gates
from data_governance.historical_depth import attach_historical_depth
from data_governance.l2_l3 import attach_l2_l3_policy
from data_governance.normalization import normalize_payload
from data_governance.provenance import attach_provenance
from data_governance.quality import attach_quality
from data_governance.raw_landing import land_raw_record
from data_governance.reconciliation import reconcile_prices
from data_governance.reliability import score_source
from data_governance.rights import ensure_source_rights
from data_governance.timestamps import attach_timestamps


def evaluate_data_governance(
    payload: dict[str, Any],
    *,
    symbol: str | None = None,
    source_id: str = "oracle",
    slo_class: str = "T0",
    lang: str = "en",
    land_raw: bool = True,
) -> dict[str, Any]:
    """Run full data governance evaluation and attach results."""
    out = dict(payload)
    sym = str(symbol or out.get("symbol") or out.get("asset") or "BTC").upper()

    if land_raw:
        raw_ref = land_raw_record(source_id=source_id, payload={k: v for k, v in out.items() if not str(k).startswith("data_governance")})
        out["raw_evidence_id"] = raw_ref.get("raw_id")

    out = attach_timestamps(out)
    out = normalize_payload(out, vendor=source_id)
    out = attach_data_freshness(out, slo_class=slo_class)
    out = attach_quality(out)
    out = reconcile_prices(out)
    out = attach_historical_depth(out, methodology_id="net_edge")
    out = attach_l2_l3_policy(out, feature="execution_feasibility")
    out = attach_provenance(out, symbol=sym)
    out = evaluate_fallback(out)

    rights = ensure_source_rights(source_id, operation="display")
    rel = score_source(source_id if source_id != "oracle" else "binance_ws")

    dg_freshness = out.get("data_governance_freshness") or {
        "freshness_state": out.get("freshness_state"),
        "age_seconds": out.get("age_seconds"),
    }
    dg_quality = out.get("data_governance_quality") or {"quality_state": out.get("data_quality_state")}
    dg_provenance = out.get("data_governance_provenance") or {"traceable": False}

    out["data_governance"] = {
        "freshness": dg_freshness,
        "quality": dg_quality,
        "historical_depth": out.get("historical_depth"),
        "l2_l3_policy": out.get("l2_l3_policy"),
        "provenance": dg_provenance,
        "source_rights": rights,
        "reliability": rel,
        "reconciliation": out.get("reconciliation"),
        "fallback_policy": out.get("fallback_policy"),
        "timestamps": out.get("timestamps"),
        "gates": None,
    }

    gates = evaluate_data_gates(out)
    out["data_governance"]["gates"] = gates
    out["data_governance_state"] = gates["data_governance_state"]
    out["data_governance_failed_gates"] = gates.get("failed_gates")

    surface = build_decision_surface(out, lang=lang)
    out["todays_decision_surface"] = surface
    out["user_facing_provenance"] = surface.get("G_evidence_strip")

    return out


def data_governance_status() -> dict[str, Any]:
    from data_governance.credentials import credential_status
    from data_governance.legal import legal_register_status
    from data_governance.methodology import methodology_registry_status
    from data_governance.observability import observability_dashboard
    from data_governance.registry import registry_summary
    from data_governance.retention import retention_status
    from data_governance.schema_evolution import schema_evolution_status
    from data_governance.slo import slo_registry_status

    return {
        "registry": registry_summary(),
        "credentials": credential_status(),
        "slo": slo_registry_status(),
        "methodology": methodology_registry_status(),
        "retention": retention_status(),
        "schema_evolution": schema_evolution_status(),
        "legal": legal_register_status(),
        "observability": observability_dashboard(),
    }
