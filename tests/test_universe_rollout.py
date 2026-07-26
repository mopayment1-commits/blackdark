"""Tests for 100-exchange universe rollout."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

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


def test_rollout_summary_json():
    data = rollout_summary_json()
    assert "registry_exchanges" in data
    assert data["registry_exchanges"] >= 100
