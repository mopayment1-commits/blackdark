"""Tests — Exchange Registry #401."""

from __future__ import annotations

import json

import pytest

from bd_platform import exchange_registry as er


@pytest.fixture
def registry_seed(tmp_path, monkeypatch):
    exchanges = {
        f"ex_{i}": {
            "exchange_id": f"ex_{i}",
            "name": f"Exchange {i}",
            "rank": i,
            "venue_type": "cex" if i <= 50 else "dex",
            "status": "active",
            "logo_url": f"/static/img/exchanges/ex_{i}.svg",
            "api_endpoints": {"rest": f"https://api.ex{i}.com"},
            "metadata": {"fee_tier_bps": 10, "supports_funding_rates": i <= 50},
        }
        for i in range(1, 101)
    }
    p = tmp_path / "exchange_registry_seed.json"
    p.write_text(json.dumps({
        "exchanges": exchanges,
        "integrations": {"no_standalone_ai_engine": True},
    }), encoding="utf-8")
    monkeypatch.setattr(er, "_SEED_PATH", p)
    return p


def test_status_feature_401(registry_seed):
    status = er.exchange_registry_status()
    assert status["feature_id"] == 401
    assert status["no_standalone_ai_engine"] is True
    assert status["summary"]["count_valid"] is True


def test_hundred_exchanges(registry_seed):
    catalog = er.build_exchange_catalog()
    assert len(catalog) == 100


def test_get_exchange(registry_seed):
    row = er.get_exchange("ex_1")
    assert row["ok"] is True
    assert row["rank"] == 1
    assert row["api_endpoints"]


def test_venue_type_filter(registry_seed):
    cex = er.build_exchange_catalog(venue_type="cex")
    dex = er.build_exchange_catalog(venue_type="dex")
    assert len(cex) == 50
    assert len(dex) == 50


def test_reconciliation(registry_seed):
    result = er.run_reconciliation_tests()
    assert result["all_passed"] is True


def test_api_routes(registry_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/data-layer/exchange-registry/status").status_code == 200
    r = c.get("/api/platform/intelligence-ledger/data-layer/exchange-registry?limit=100")
    assert r.status_code == 200
    assert r.json()["summary"]["exchange_count"] == 100
    assert c.get("/api/platform/intelligence-ledger/data-layer/exchange-registry/lookup?exchange_id=ex_1").status_code == 200
