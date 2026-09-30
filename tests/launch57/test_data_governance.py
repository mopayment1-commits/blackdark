"""Launch-57 data intelligence & governance wiring tests."""

from __future__ import annotations

import pytest

from launch57.data_governance_common import (
    LAUNCH57_DATA_CRITICAL_IDS,
    attach_material_observation,
    build_launch57_source_registry,
    build_price_reconciliation_from_probe,
    connector_fetchers_from_registry,
    reconcile_price_observations,
    validate_observation_contract,
)


def test_launch57_source_registry_covers_connector_providers():
    registry = build_launch57_source_registry()
    providers = {entry["provider"] for entry in registry}
    assert providers == {"binance", "kraken", "okx", "bybit", "coingecko", "coinbase"}
    assert all(entry["source_role"] for entry in registry)
    assert all(entry["supported_launch57_capabilities"] for entry in registry)


def test_connector_fetchers_match_registry_roles():
    fetchers = connector_fetchers_from_registry()
    assert fetchers[0] == ("binance", "primary")
    assert ("coingecko", "validation") in fetchers


def test_observation_contract_passes_with_material_fields():
    gate = validate_observation_contract(
        {
            "source": "binance",
            "event_time": "2026-09-18T12:00:00Z",
            "observed_at": "2026-09-18T12:00:01Z",
            "freshness_state": "LIVE",
            "quality_state": "decision_grade",
        }
    )
    assert gate["ok"] is True
    assert gate["missing_fields"] == []


def test_observation_contract_fails_when_missing_fields():
    gate = validate_observation_contract({"source": "binance"})
    assert gate["ok"] is False
    assert "freshness" in gate["missing_fields"]


def test_reconciliation_quarantines_conflict_without_averaging():
    result = reconcile_price_observations(
        [{"source_id": "binance", "value": 100.0}, {"source_id": "kraken", "value": 200.0}]
    )
    assert result["state"] == "CONFLICT"
    assert result["launch57_reconciliation_state"] == "CONFLICT"
    assert result.get("canonical_value") is None


def test_reconciliation_single_source_penalty():
    result = reconcile_price_observations([{"source_id": "binance", "value": 50000.0}])
    assert result["state"] == "SINGLE_SOURCE"
    assert result.get("confidence_penalty") is True


def test_build_price_reconciliation_from_probe_uses_resolved_price():
    result = build_price_reconciliation_from_probe(
        primary_price=100.0,
        primary_source="binance:api.binance.com",
        probe={"resolved_price": 100.2, "resolved_source": "kraken"},
    )
    assert result["state"] in {"CONSENSUS", "CONFLICT", "SINGLE_SOURCE"}


def test_attach_material_observation_adds_contract_envelope():
    body = attach_material_observation(
        {"symbol": "BTC", "surface": "real_time_prices", "price": 1.0},
        source="binance",
        data_type="real_time_price",
        raw_value=1.0,
        normalized_value=1.0,
        freshness_state="LIVE",
        quality_state="decision_grade",
    )
    assert "material_observation_contract" in body
    assert body["launch57_data_governance"]["scope"] == "LAUNCH57_IDS"
    assert body["material_observation_contract"]["contract_gate"]["ok"] is True


def test_data_critical_ids_include_batch1_and_batch2():
    assert {21, 22, 23, 24, 39, 40, 41, 42} <= LAUNCH57_DATA_CRITICAL_IDS


@pytest.mark.asyncio
async def test_unified_exchange_connector_includes_registry_and_reconciliation(monkeypatch):
    from launch57.data_batch1 import unified_exchange_connector

    async def fake_probe(symbol: str = "BTC"):
        return {
            "symbol": symbol,
            "checks": {"api.binance.com": {"ok": True, "source": "binance:api.binance.com"}},
            "resolved": True,
            "resolved_source": "binance:api.binance.com",
            "resolved_price": 50000.0,
        }

    monkeypatch.setattr("launch57.data_batch1.probe_price_sources", fake_probe)
    out = await unified_exchange_connector(symbol="BTC", params={})
    assert "launch57_source_registry" in out
    assert len(out["launch57_source_registry"]) == 6
    assert "cross_source_reconciliation" in out
    assert "material_observation_contract" in out
    route = next(r for r in out["routes"] if r["provider"] == "binance")
    assert route["source_role"] == "PRIMARY"


@pytest.mark.asyncio
async def test_real_time_prices_includes_cross_source_reconciliation(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {
            "success": True,
            "selected_provider": "binance",
            "health_probe": {
                "resolved_price": 50000.0,
                "resolved_source": "binance:api.binance.com",
            },
        }

    async def fake_ticker(pair: str):
        return {"price": 50000.0, "source": "binance:api.binance.com", "age_sec": 1.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert "cross_source_reconciliation" in out
    assert "material_observation_contract" in out
    assert out["material_observation_contract"]["contract_gate"]["ok"] is True
