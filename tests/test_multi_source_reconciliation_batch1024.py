"""Tests — Multi-Source Ingest & Reconciliation Layer (#1024 Data Engine)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import multi_source_reconciliation as msr


@pytest.fixture
def msr_seed() -> dict:
    return json.loads(Path("data/multi_source_reconciliation_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    msr.reset_multi_source_state()
    yield
    msr.reset_multi_source_state()


def test_1024_status_no_standalone(msr_seed):
    status = msr.multi_source_status_1024(seed=msr_seed)
    assert status["standalone_rejected"] is True
    assert status["merged_into"] == "Data Engine"
    assert status["policy"]["min_sources_per_type"] == 2
    assert status["thresholds_pct"]["price"] == 0.5


def test_two_sources_per_type(msr_seed):
    sources = msr.multi_source_status_1024(seed=msr_seed)["sources"]
    assert len(sources["price"]) >= 2
    assert len(sources["volume"]) >= 2
    assert len(sources["onchain"]) >= 2
    price_ids = {s["id"] for s in sources["price"]}
    assert "binance" in price_ids
    assert "coingecko" in price_ids


def test_cross_validation_within_tolerance(msr_seed):
    result = msr.cross_validate_pair(
        data_type="price",
        source_a="binance",
        value_a=42000.0,
        source_b="coingecko",
        value_b=42050.0,
        seed=msr_seed,
    )
    assert result["within_tolerance"] is True
    assert result["variance_pct"] < 0.5


def test_cross_validation_divergence(msr_seed):
    result = msr.cross_validate_pair(
        data_type="price",
        source_a="binance",
        value_a=42000.0,
        source_b="coingecko",
        value_b=45000.0,
        seed=msr_seed,
    )
    assert result["within_tolerance"] is False


def test_price_reconciliation_ok(msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is True
    assert result["status"] == "reconciled"
    assert result["confidence"] in ("High", "Medium")
    assert "tag" in result["provenance"]
    assert result["fee_db"]["fee_db_logged"] is True


def test_divergence_suppressed_with_badge(msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 45000.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is False
    assert result["suppress_output"] is True
    assert result["badge"] == "Data Degraded"


def test_failover_insufficient_sources(msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is True
    assert result["status"] == "failover_active"
    assert result["suppress_output"] is False
    assert result["badge"] == "Source Switched"
    assert result["confidence"] == "Medium"
    assert result["failover"]["within_sla"] is True
    assert result["failover"]["source_to"] == "coingecko"


def test_automatic_failover_health_check_latency(msr_seed):
    health = msr.check_source_health(
        data_type="price",
        source_id="binance",
        ok=True,
        latency_ms=300.0,
        seed=msr_seed,
    )
    assert health["slow"] is True
    assert health["unhealthy"] is True
    assert health["trigger_reason"] == "latency_exceeded"


def test_failover_audit_trail(msr_seed):
    msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    audit = msr.get_failover_audit_trail()
    assert audit["count"] >= 1
    assert audit["append_only"] is True
    event = audit["audit_trail"][-1]
    assert event["source_from"] == "binance"
    assert event["source_to"] == "coingecko"
    assert "duration_ms" in event


def test_failover_status(msr_seed):
    msr.reconcile_volume(
        observations=[
            {"source": "coinmarketcap", "value": 1_200_000_000.0, "ok": False},
            {"source": "thegraph", "value": 1_210_000_000.0, "ok": True},
        ],
        seed=msr_seed,
    )
    status = msr.get_failover_status(seed=msr_seed)
    assert status["automatic_failover_engine"] is True
    assert status["per_type"]["volume"]["failover_active"] is True


def test_primary_recovery_validation(msr_seed):
    msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    recovery = msr.check_primary_recovery(data_type="price", primary_ok=True, seed=msr_seed)
    assert recovery["validation_in_progress"] is True
    assert recovery["confidence"] == "Medium"


def test_failover_incident_alert_threshold(msr_seed):
    for _ in range(4):
        msr.execute_automatic_failover(
            data_type="price",
            source_from="binance",
            source_to="coingecko",
            reason="source_failure",
            backup_value=42000.0,
            seed=msr_seed,
        )
    recent = msr.get_failover_audit_trail(limit=10)
    assert recent["count"] >= 4


def test_all_sources_down_still_degraded(msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": False},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is False
    assert result["suppress_output"] is True
    assert result["badge"] == "Data Degraded"


def test_volume_reconciliation(msr_seed):
    result = msr.reconcile_volume(
        observations=[
            {"source": "coinmarketcap", "value": 1_200_000_000.0, "ok": True},
            {"source": "thegraph", "value": 1_210_000_000.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is True
    assert result["real_volume_ref"] == 992


def test_onchain_reconciliation(msr_seed):
    result = msr.reconcile_onchain(
        observations=[
            {"source": "alchemy", "value": 19_500_000.0, "ok": True},
            {"source": "quicknode", "value": 19_501_950.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert result["ok"] is True
    assert result["onchain_extension_ref"] == 12


def test_cache_hit(msr_seed):
    msr.reconcile_price(symbol="ETH", seed=msr_seed)
    cached = msr.reconcile_price(symbol="ETH", seed=msr_seed)
    assert cached.get("cache_hit") is True


def test_sprint1_gate(msr_seed):
    gate = msr.check_sprint1_gate_1024(seed=msr_seed)
    assert gate["sprint_1_allowed"] is True
    assert gate["blocks_sprint_1"] is True


def test_e2e_all_checks(msr_seed):
    e2e = msr.run_multi_source_e2e_1024(seed=msr_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
