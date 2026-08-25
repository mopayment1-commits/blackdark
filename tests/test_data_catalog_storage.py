"""Tests — #214 Data Catalog + #215 Data Storage Infrastructure (merged, not standalone)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_catalog as dc
from bd_platform import data_storage_infrastructure as dsi


# ── #214 Data Catalog (merged) ─────────────────────────────────────────────────


@pytest.fixture
def isolated_catalog(tmp_path, monkeypatch):
    seed = tmp_path / "metric_catalog_seed.json"
    seed.write_text(
        json.dumps([
            {
                "metric_id": "price_usd",
                "name": "Price",
                "category": "market",
                "frequency": "real-time",
                "stabilization_sec": 1,
                "mutability": "mutable",
                "access": "free",
                "assets": ["BTC", "ETH"],
                "api_endpoint": "/api/v1/platform/price",
                "ui_surface": "dashboard",
                "source": "binance",
            },
            {
                "metric_id": "mvrv_proxy",
                "name": "MVRV",
                "category": "onchain",
                "frequency": "1h",
                "stabilization_sec": 3600,
                "mutability": "immutable_daily",
                "access": "pro",
                "assets": ["BTC"],
                "api_endpoint": "/api/v1/platform/onchain",
                "ui_surface": "research_lab",
                "source": "research_lab",
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(dc, "_SEED_PATH", seed)
    return seed


def test_not_standalone_feature(isolated_catalog):
    status = dc.data_catalog_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 214
    assert "Data Catalog" in status["merged_into"]


def test_registry_from_production_truth(isolated_catalog):
    reg = dc.build_metric_registry_from_production()
    assert reg["generated_from_production"] is True
    assert reg["metric_count"] >= 2
    assert all(m.get("production_truth") for m in reg["metrics"][:2])


def test_metric_metadata_fields(isolated_catalog):
    reg = dc.build_metric_registry_from_production()
    price = next(m for m in reg["metrics"] if m["metric_id"] == "price_usd")
    assert price["category"] == "market"
    assert price["frequency"] == "real-time"
    assert price["stabilization_sec"] == 1
    assert price["mutability"] == "mutable"
    assert price["access"] == "free"
    assert "BTC" in price["assets"]


def test_searchable_availability_matrix(isolated_catalog):
    result = dc.search_metric_availability(asset="BTC")
    assert result["count"] >= 2
    assert all(row["available"] for row in result["availability_matrix"])


def test_automated_parity_tests(isolated_catalog):
    parity = dc.run_parity_tests()
    assert parity["automated_parity_tests"] is True
    assert parity["passed"] >= 1
    assert parity["all_passed"] is True


def test_metric_detail(isolated_catalog):
    detail = dc.get_metric_detail("price_usd")
    assert detail["ok"] is True
    assert detail["metric"]["api_endpoint"]


def test_full_seed_file_exists():
    rows = json.loads(Path("data/metric_catalog_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 10


# ── #215 Data Storage Infrastructure (merged) ──────────────────────────────────


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    policy = tmp_path / "retention_policy.json"
    monkeypatch.setattr(dsi, "_POLICY_PATH", policy)
    return policy


def test_storage_not_standalone(isolated_storage):
    status = dsi.data_storage_infrastructure_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 215
    assert status["retention_policy_versioned"] is True


def test_retention_policy_versioned(isolated_storage):
    policy = dsi.get_retention_policy()
    assert policy["retention_policy_versioned"] is True
    assert "version" in policy["policy"]
    assert "Retention Policy v" in policy["display"]


def test_no_silent_loss_policy(isolated_storage):
    status = dsi.data_storage_infrastructure_status()
    assert status["no_silent_loss"] is True
    assert status["deterministic_retrieval"] is True


@pytest.mark.asyncio
async def test_restore_test_deterministic(isolated_storage, monkeypatch, tmp_path):
    import config

    monkeypatch.setattr(config, "HOT_STORAGE_DIR", tmp_path / "hot")
    result = await dsi.run_restore_test(tier="tier1_hot")
    assert result["restore_test"] == "passed"
    assert result["deterministic_retrieval"] is True


@pytest.mark.asyncio
async def test_migration_safety_check(isolated_storage, monkeypatch):
    async def fake_arch():
        return {"issues": ["No critical storage issues detected."], "tiers": {}}

    monkeypatch.setattr("storage_tier_manager.storage_architecture_status", fake_arch)
    result = await dsi.run_migration_safety_check()
    assert "migration_safe" in result
    assert result["no_silent_loss"] is not None


@pytest.mark.asyncio
async def test_storage_tier_status(isolated_storage, monkeypatch):
    async def fake_arch():
        return {
            "architecture": "multi_tier",
            "tiers": {"tier1_hot": {"name": "Hot", "spool_mb": 10}},
            "cost_guard": {},
            "compliance": {},
            "issues": [],
            "hot_pipeline": {},
        }

    monkeypatch.setattr("storage_tier_manager.storage_architecture_status", fake_arch)
    result = await dsi.get_storage_tier_status()
    assert result["architecture"] == "multi_tier"
    assert result["no_silent_loss_policy"] is True
    assert len(result["cost_latency_evidence"]) >= 1


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)

    catalog = c.get("/api/platform/data-catalog/status")
    assert catalog.status_code == 200
    assert catalog.json()["standalone"] is False

    parity = c.post("/api/platform/data-catalog/parity-test")
    assert parity.status_code == 200
    assert parity.json()["automated_parity_tests"] is True

    storage = c.get("/api/platform/data-storage/status")
    assert storage.status_code == 200
    assert storage.json()["standalone"] is False

    policy = c.get("/api/platform/data-storage/retention-policy")
    assert policy.status_code == 200
    assert policy.json()["retention_policy_versioned"] is True
