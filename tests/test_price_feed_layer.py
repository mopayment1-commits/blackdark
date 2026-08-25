"""Tests — #283 Price Feed Layer (Sprint 0 infrastructure, not standalone)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import price_feed_layer as pfl


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "price_feed_layer_seed.json"
    seed.write_text(
        json.dumps({
            "streaming": {
                "mode": "websocket",
                "fallback": "rest_poll",
                "venues_connected": 3,
                "venues_total": 4,
            },
            "assets": {
                "BTC": [
                    {
                        "venue": "binance",
                        "pair": "BTC/USDT",
                        "bid": 100.0,
                        "ask": 100.1,
                        "latency_ms": 40,
                        "snapshot_age_ms": 150,
                        "streaming": True,
                    },
                ],
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pfl, "_SEED_PATH", seed)
    return seed


def test_not_standalone_infrastructure(isolated_seed):
    status = pfl.price_feed_layer_status()
    assert status["feature_id"] == 283
    assert status["standalone"] is False
    assert status["archived_standalone_ticket"] is True
    assert status["infrastructure_layer"] is True


def test_freshness_visible_on_quotes(isolated_seed):
    prices = pfl.get_live_prices("BTC")
    assert prices["ok"] is True
    assert prices["freshness_on_all_quotes"] is True
    quote = prices["quotes"][0]
    assert quote["freshness"]["freshness_visible"] is True
    assert quote["freshness"]["latency_visible"] is True


def test_latency_freshness_acceptance(isolated_seed):
    freshness = pfl.build_freshness_block(latency_ms=40, snapshot_age_ms=150)
    assert freshness["latency_ms"] == 40
    assert freshness["snapshot_age_ms"] == 150
    assert freshness["stale"] is False
    assert "Latency:" in freshness["display"]


def test_stale_detection(isolated_seed):
    freshness = pfl.build_freshness_block(latency_ms=100, snapshot_age_ms=8000)
    assert freshness["stale"] is True


def test_scope_lock_no_dashboard(isolated_seed):
    scope = pfl.build_scope_lock()
    assert scope["not_standalone_feature"] is True
    assert scope["no_separate_dashboard"] is True
    assert "Landing Page" in scope["serves"]


def test_streaming_status(isolated_seed):
    streaming = pfl.build_streaming_status()
    assert streaming["mode"] == "websocket"
    assert "Venues:" in streaming["display"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/price-feed/status").status_code == 200
    resp = c.get("/api/platform/price-feed/live?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["freshness_on_all_quotes"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/price_feed_layer_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 283
    assert seed["archived_standalone_ticket"] is True
    assert "BTC" in seed["assets"]
