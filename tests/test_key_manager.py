"""Tests for platform API key manager (no live network)."""

from __future__ import annotations

import os

import pytest

from bd_platform import key_manager


def test_keys_status_structure(monkeypatch):
    monkeypatch.delenv("LUNARCRUSH_API_KEY", raising=False)
    monkeypatch.delenv("COINMARKETCAL_API_KEY", raising=False)
    monkeypatch.delenv("DEBANK_API_KEY", raising=False)
    data = key_manager.keys_status()
    assert data["total"] == 3
    assert data["configured_count"] == 0
    assert len(data["keys"]) == 3
    ids = {k["id"] for k in data["keys"]}
    assert ids == {"lunarcrush", "coinmarketcal", "debank"}


def test_mask_short_and_long():
    assert key_manager._mask("") == ""
    assert key_manager._mask("abc") == "***"
    assert key_manager._mask("abcdefghij") == "abcd…ghij"


def test_upsert_env_line_replaces():
    lines = ["FOO=1", "LUNARCRUSH_API_KEY=old"]
    out = key_manager._upsert_env_line("LUNARCRUSH_API_KEY", "new", lines)
    assert out == ["FOO=1", "LUNARCRUSH_API_KEY=new"]


@pytest.mark.asyncio
async def test_save_platform_keys_skips_invalid(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LUNARCRUSH_API_KEY=\n", encoding="utf-8")
    monkeypatch.setattr(key_manager, "_ENV_PATH", env_file)

    async def fake_verify(_key):
        return {"valid": False, "message": "bad key"}

    monkeypatch.setattr(key_manager, "verify_lunarcrush", fake_verify)
    result = await key_manager.save_platform_keys({"lunarcrush": "bad-token"})
    assert result["saved_count"] == 0
    assert "LUNARCRUSH_API_KEY=bad-token" not in env_file.read_text(encoding="utf-8")
