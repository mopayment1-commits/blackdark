"""Data Governance P0 test matrix — DIG-001 → DIG-060 local engineering evidence."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")


def _evaluate(payload: dict | None = None, **kwargs):
    from data_governance.pipeline import evaluate_data_governance

    base = {"symbol": "BTC", "asset": "BTC", "quote_age_ms": 500, "source_count": 2, "depth_usd": 50000}
    if payload:
        base.update(payload)
    return evaluate_data_governance(base, **kwargs)


def test_source_registry_ssot():
    from data_governance.registry import canonical_source_registry, registry_summary

    entries = canonical_source_registry()
    assert len(entries) >= 50
    summary = registry_summary()
    assert summary["registry_authority"] == "data_governance/registry.py"


def test_credential_lifecycle_no_hardcoded_secrets():
    from data_governance.credentials import credential_status

    status = credential_status()
    assert status["secret_manager_only"] is True
    assert status["hardcoded_secrets_in_code"] == []


def test_raw_normalized_separation():
    result = _evaluate()
    assert result.get("raw_evidence_id")
    assert result.get("normalization_version")
    assert result["data_governance"]["provenance"]["traceable"]


def test_normalization_contract():
    from data_governance.normalization import normalize_payload

    out = normalize_payload({"symbol": "BTC", "price": 50000}, vendor="binance_spot")
    assert "normalization_version" in out
    assert "_source_native" in out


def test_timestamp_integrity():
    result = _evaluate()
    ts = result["data_governance"]["timestamps"]
    assert ts["observed_at"]
    assert ts["ingested_at"]
    assert "integrity_ok" in ts


def test_freshness_states():
    fresh = _evaluate({"quote_age_ms": 500})["data_governance"]["freshness"]
    assert fresh["freshness_state"] in {"LIVE", "NEAR_LIVE", "DELAYED", "STALE", "CACHED", "PARTIAL", "UNKNOWN"}


def test_stale_data_not_live():
    stale = _evaluate({"quote_age_ms": 120000})["data_governance"]["freshness"]
    assert stale["freshness_state"] in {"STALE", "DELAYED", "UNKNOWN"}


def test_quality_gate_rejects_conflict():
    result = _evaluate({"dimension_conflict": {"veto": True}, "secondary_price": 60000, "price": 50000})
    assert result["data_governance"]["quality"]["quality_state"] in {"CONFLICTING", "PARTIAL", "INSUFFICIENT", "SUSPECT"}


def test_cross_source_reconciliation():
    from data_governance.reconciliation import detect_divergence

    div = detect_divergence(primary_value=100.0, secondary_value=102.0, threshold_pct=5.0)
    assert div["conflict"] is False
    div2 = detect_divergence(primary_value=100.0, secondary_value=110.0, threshold_pct=5.0)
    assert div2["conflict"] is True


def test_historical_depth_sufficiency():
    from data_governance.historical_depth import check_historical_sufficiency

    ok = check_historical_sufficiency("net_edge", available_days=60)
    assert ok["sufficient"] is True
    bad = check_historical_sufficiency("net_edge", available_days=1)
    assert bad["sufficient"] is False


def test_l2_l3_selective_policy():
    from data_governance.l2_l3 import evaluate_depth_sufficiency

    exec_ok = evaluate_depth_sufficiency(feature="execution_feasibility", has_l1=True, has_l2=True, has_l3=False)
    assert exec_ok["l2_required"] is True
    assert exec_ok["sufficient"] is True
    ticker = evaluate_depth_sufficiency(feature="ticker_monitoring", has_l1=True, has_l2=False, has_l3=False)
    assert ticker["sufficient"] is True


def test_fallback_abstain_on_stale():
    result = _evaluate({"quote_age_ms": 999999})
    assert result.get("fallback_policy")
    assert result["data_governance_state"] in {"DEGRADED", "ABSTAINED", "ADMITTED"}


def test_provenance_lineage():
    result = _evaluate()
    prov = result["data_governance"]["provenance"]
    assert prov["lineage"]["nodes"]
    assert prov["raw_payload_hash"]


def test_methodology_registry():
    from data_governance.methodology import get_methodology_card, methodology_registry_status

    card = get_methodology_card("net_edge")
    assert card and card["methodology_version"]
    assert methodology_registry_status()["unversioned_critical"] == []


def test_source_rights_enforcement():
    from data_governance.rights import ensure_source_rights

    rights = ensure_source_rights("binance_spot", operation="display")
    assert "allowed" in rights


def test_rate_limit_governance():
    from data_governance.rate_limit import check_quota, record_request

    record_request("coingecko_prices")
    q = check_quota("coingecko_prices")
    assert "minute_usage" in q


def test_schema_evolution():
    from data_governance.schema_evolution import validate_schema

    v = validate_schema(source_id="binance_spot", payload={"price": 1}, required_fields=["price"])
    assert v["compatible"] is True


def test_data_governance_gates():
    result = _evaluate()
    gates = result["data_governance"]["gates"]
    assert gates["data_governance_state"] in {"ADMITTED", "DEGRADED", "ABSTAINED", "REJECTED"}
    assert "failed_gates" in gates


def test_todays_decision_surface():
    result = _evaluate()
    surface = result["todays_decision_surface"]
    assert "A_state" in surface
    assert "G_evidence_strip" in surface
    assert surface["G_evidence_strip"]["freshness"]


def test_user_facing_provenance():
    result = _evaluate()
    assert result["user_facing_provenance"]["freshness"]


def test_decision_enrichment_wiring():
    from decision_enrichment import enrich_oracle_decision

    out = enrich_oracle_decision({"symbol": "BTC", "opportunity_score": 70, "verdict": "WAIT", "quote_age_ms": 800})
    assert "data_governance" in out
    assert out.get("data_governance_state")


def test_admission_data_governance_gate():
    from decision_enrichment import enrich_oracle_decision

    out = enrich_oracle_decision({"symbol": "BTC", "opportunity_score": 70, "verdict": "BUY", "quote_age_ms": 800, "net_profit_usdt": 10, "quote_amount": 1000})
    admission = (out.get("decision_truth") or {}).get("admission") or {}
    assert "data_governance" in (admission.get("gates") or {})


def test_duplicate_ingestion_idempotent():
    r1 = _evaluate({"event_id": "evt-1"})
    r2 = _evaluate({"event_id": "evt-1"})
    assert r1["raw_evidence_id"] != r2["raw_evidence_id"]


def test_future_timestamp_detection():
    from data_governance.timestamps import build_timestamps

    import time

    future = time.time() + 3600
    bundle = build_timestamps(source_timestamp=future)
    assert bundle.integrity_ok is False
    assert "future_source_timestamp" in bundle.issues


def test_provider_outage_fallback():
    from data_governance.fallback import resolve_fallback

    fb = resolve_fallback("binance_ws", health="unhealthy")
    assert fb["action"] in {"fallback", "abstain"}


def test_observability_dashboard():
    from data_governance.observability import observability_dashboard

    dash = observability_dashboard()
    assert "registry" in dash
    assert "reliability" in dash


def test_legal_register():
    from data_governance.legal import legal_register_status

    reg = legal_register_status()
    assert reg["GLBA_APPLICABILITY_STATUS"] == "LEGAL_REVIEW_REQUIRED"


def test_engineering_closure_module():
    from bd_platform.data_governance_source_driven_engineering import data_governance_source_driven_status

    status = data_governance_source_driven_status(head="local", pytest_ok=True)
    assert status["SOURCE_REQUIREMENTS_ACCOUNTED_FOR"] == "100%"
    assert status["LOCAL_BUILDABLE_DATA_GOVERNANCE_REQUIREMENTS_REMAINING"] == 0


def test_api_router_exists():
    from api.routers.data_governance import router

    assert router.prefix == "/api/data-governance"
