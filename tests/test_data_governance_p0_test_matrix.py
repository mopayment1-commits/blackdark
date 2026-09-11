"""Data Governance P0 matrix (DIG-001 bindings)."""

from __future__ import annotations

import time

from data_governance import assert_usage_allowed, list_sources, register_source, usage_rights_status
from data_governance.freshness import gate_admission
from data_governance.registry import SourceRecord


def test_registry_lists_default_sources():
    sources = list_sources()
    assert any(s["source_id"] == "coingecko" for s in sources)


def test_rights_allow_analytics_for_known_source():
    result = assert_usage_allowed("coingecko", purpose="analytics")
    assert result["allowed"] is True


def test_register_source_and_enforce():
    register_source(
        SourceRecord(
            "test_vendor",
            "Test Vendor",
            "L1_SOURCE",
            "trial",
            14,
            live_allowed=False,
        )
    )
    blocked = assert_usage_allowed("test_vendor", purpose="live_trading")
    assert blocked["allowed"] is False


def test_freshness_gate_admits_recent_payload():
    payload = {"source_id": "coingecko", "observed_at": time.time(), "purpose": "analytics"}
    result = gate_admission(payload, max_age_seconds=60)
    assert result["admitted"] is True
    assert result["decision_truth_admission_gate"] is True


def test_usage_rights_status():
    status = usage_rights_status()
    assert status["package"] == "data_governance"
    assert status["sources_registered"] >= 3
