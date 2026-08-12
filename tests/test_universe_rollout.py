"""Tests for 100-exchange universe rollout."""

from __future__ import annotations

import json
from pathlib import Path

from universe_rollout import activate_full_universe, rollout_summary_json


def test_activate_full_universe_writes_manifest(tmp_path, monkeypatch):
    manifest_path = tmp_path / "operational_manifest.json"
    registry_path = tmp_path / "universe_registry.json"
    real_registry = Path(__file__).resolve().parent.parent / "data" / "universe_registry.json"
    registry_path.write_text(real_registry.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr("config.OPERATIONAL_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("config.DATA_DIR", tmp_path)
    monkeypatch.setattr("platform_universe.REGISTRY_PATH", registry_path)
    import platform_universe
    platform_universe.load_registry.cache_clear()

    result = activate_full_universe(save=True)
    assert result["exchanges"] >= 100
    assert result["approved"] is True
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["status"] == "approved"
    assert payload["review"]["approved"] is True
    assert len(payload["operational"]["exchanges"]) >= 100


def test_live_rollout_status_uses_dialect_safe_cutoff(tmp_path, monkeypatch):
    import asyncio

    import universe_rollout as ur

    monkeypatch.setattr(ur, "_registry_exchange_ids", lambda: ["binance", "okx"])
    monkeypatch.setattr(ur, "_manifest_is_approved", lambda: True)

    class _Rows:
        async def fetchall(self):
            return [("binance",), ("coinbase",)]

    class _DB:
        async def execute(self, query, params=None):
            assert "datetime(" not in query
            assert "timestamp >= ?" in query
            assert params and len(params) == 1
            return _Rows()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr("database.get_connection", lambda: _DB())

    async def _run():
        status = await ur.live_rollout_status()
        assert status["target_exchanges"] == 2
        assert status["healthy_exchanges"] == 1
        assert "binance" in status["healthy_sample"]
        assert status["manifest_approved"] is True

    asyncio.run(_run())
