"""Tests — On-Chain Address Intelligence Module (#10 + #19 + #20 unified)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from bd_platform.address_intelligence import (
    _bootstrap_history,
    _normalize_address,
    _snapshot_key,
    balance_history,
    balance_updates,
    search_address,
)


def test_normalize_address_evm():
    assert _normalize_address("0xAbC", "ethereum") == "0xabc"


def test_snapshot_key_chain_specific():
    k1 = _snapshot_key("0xabc", "ethereum")
    k2 = _snapshot_key("0xabc", "polygon")
    assert k1 != k2
    assert k1.startswith("ethereum:")


def test_bootstrap_history_proxy():
    series = _bootstrap_history(100_000, days=7, source="test")
    assert len(series) == 8  # 7 proxy + 1 current
    assert series[-1]["proxy"] is False
    assert series[0]["proxy"] is True


@pytest.mark.asyncio
async def test_search_address_mock(monkeypatch):
    async def fake_balance(addr):
        return {"available": True, "source": "test", "address": addr, "total_usd": 50_000}

    async def fake_labels(addr):
        return {"available": True, "labels": [{"label": "vitalik.eth", "source": "test"}]}

    async def fake_clusters(addr):
        return {"available": True, "clusters": [], "center_label": "vitalik.eth"}

    async def fake_arkham(*args, **kwargs):
        return {"ok": False, "data_state": "MISSING"}

    monkeypatch.setattr("bd_platform.free_integrations.wallet_balance", fake_balance)
    monkeypatch.setattr("bd_platform.free_integrations.wallet_labels", fake_labels)
    monkeypatch.setattr("bd_platform.free_integrations.wallet_clusters", fake_clusters)
    monkeypatch.setattr(
        "blackdark.ingestion.arkham_connector.fetch_entity_intelligence_input", fake_arkham
    )

    out = await search_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", chain="ethereum")
    assert out["ok"] is True
    assert out["capability"] == "address_search"
    assert out["feature"] == "#10"
    assert out["chain"] == "ethereum"
    assert out["chain_id"] == 1
    assert out["total_usd"] == 50_000
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_balance_history_mock(monkeypatch, tmp_path):
    snap = tmp_path / "snapshots.jsonl"
    key = _snapshot_key("0xabc", "ethereum")
    snap.write_text(
        json.dumps(
            {
                "key": key,
                "address": "0xabc",
                "chain": "ethereum",
                "total_usd": 90_000,
                "source": "test",
                "timestamp": "2026-08-20T12:00:00+00:00",
            }
        )
        + "\n"
        + json.dumps(
            {
                "key": key,
                "address": "0xabc",
                "chain": "ethereum",
                "total_usd": 100_000,
                "source": "test",
                "timestamp": "2026-08-24T12:00:00+00:00",
            }
        )
        + "\n"
    )
    monkeypatch.setattr("bd_platform.address_intelligence._SNAPSHOT_PATH", snap)

    async def fake_balance(addr):
        return {"available": True, "source": "test", "total_usd": 100_000}

    monkeypatch.setattr("bd_platform.free_integrations.wallet_balance", fake_balance)

    out = await balance_history("0xabc", chain="ethereum", days=30)
    assert out["ok"] is True
    assert out["capability"] == "balance_history"
    assert out["feature"] == "#19"
    assert out["chain_id"] == 1
    assert out["point_count"] >= 2
    assert out["proxy_bootstrap"] is False


@pytest.mark.asyncio
async def test_balance_updates_diff(monkeypatch, tmp_path):
    snap = tmp_path / "snapshots.jsonl"
    key = _snapshot_key("0xdef", "polygon")
    snap.write_text(
        json.dumps(
            {
                "key": key,
                "address": "0xdef",
                "chain": "polygon",
                "total_usd": 80_000,
                "source": "test",
                "timestamp": "2026-08-23T12:00:00+00:00",
            }
        )
        + "\n"
    )
    monkeypatch.setattr("bd_platform.address_intelligence._SNAPSHOT_PATH", snap)

    async def fake_balance(addr):
        return {"available": True, "source": "test", "total_usd": 85_000}

    monkeypatch.setattr("bd_platform.free_integrations.wallet_balance", fake_balance)

    out = await balance_updates("0xdef", chain="polygon")
    assert out["ok"] is True
    assert out["capability"] == "balance_updates"
    assert out["feature"] == "#20"
    assert out["chain"] == "polygon"
    assert out["chain_id"] == 137
    assert out["latest_update"]["delta_usd"] == 5000
    assert out["latest_update"]["direction"] == "inflow"


def test_address_intelligence_api(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "addr.db"
    snap = tmp_path / "snapshots.jsonl"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.setattr("bd_platform.address_intelligence._SNAPSHOT_PATH", snap)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    async def fake_search(address, *, chain="ethereum"):
        return {
            "ok": True,
            "address": address,
            "chain": chain,
            "total_usd": 1000,
            "sla_met": True,
            "latency_ms": 50,
            "data_state": "LIVE",
        }

    async def fake_history(address, *, chain="ethereum", days=30):
        return {
            "ok": True,
            "series": [{"total_usd": 1000, "timestamp": "2026-08-24T12:00:00+00:00"}],
            "point_count": 1,
            "proxy_bootstrap": False,
            "current_usd": 1000,
            "chain": chain,
            "latency_ms": 40,
        }

    async def fake_updates(address, *, chain="ethereum", limit=20):
        return {
            "ok": True,
            "headline": "Balance unchanged: $+0.00",
            "feed": [],
            "feed_count": 0,
            "chain": chain,
            "latency_ms": 30,
        }

    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    monkeypatch.setattr("bd_platform.address_intelligence.balance_history", fake_history)
    monkeypatch.setattr("bd_platform.address_intelligence.balance_updates", fake_updates)

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert c.get(f"/api/platform/address-intelligence/search?address={addr}").status_code == 200
    assert c.get(f"/api/platform/address-intelligence/history?address={addr}").status_code == 200
    assert c.get(f"/api/platform/address-intelligence/updates?address={addr}").status_code == 200
    r = c.get("/address-intelligence")
    assert r.status_code == 200
    assert "Address Intelligence" in r.text
