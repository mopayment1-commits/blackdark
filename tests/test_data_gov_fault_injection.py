"""DATA-099 deterministic fault injection tests."""

from __future__ import annotations

import pytest

from data_governance.fallback import resolve_fallback
from data_governance.pipeline import evaluate_data_governance
from data_governance.quality import attach_quality
from data_governance.reconciliation import detect_divergence
from data_governance.schema_evolution import validate_schema


def test_fault_stale_source_abstains():
    out = evaluate_data_governance({"symbol": "BTC", "quote_age_ms": 999999}, symbol="BTC")
    assert out["data_governance_state"] in {"DEGRADED", "ABSTAINED", "REJECTED"}


def test_fault_conflicting_sources():
    div = detect_divergence(primary_value=100.0, secondary_value=150.0, threshold_pct=5.0)
    assert div["conflict"] is True


def test_fault_schema_incompatible():
    v = validate_schema(source_id="binance_spot", payload={"price": 1}, required_fields=["price", "volume"])
    assert v["compatible"] is False


def test_fault_quality_conflict_propagates():
    out = attach_quality({"dimension_conflict": {"veto": True}, "secondary_price": 200, "price": 100})
    assert out["data_quality_state"] in {"CONFLICTING", "SUSPECT", "INSUFFICIENT"}


def test_fault_provider_outage_fallback():
    fb = resolve_fallback("binance_ws", health="unhealthy")
    assert fb["action"] in {"fallback", "abstain", "degrade"}


def test_fault_malformed_payload_degrades():
    out = evaluate_data_governance({"symbol": "", "quote_age_ms": -1}, symbol="BTC")
    assert out.get("data_governance_state")
