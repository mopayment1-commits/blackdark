"""Wave 4 — Launch-57 dispatch isolation: no silent legacy/generic delegate."""

from __future__ import annotations

import pytest

from launch57.dispatch_isolation import (
    Launch57LegacyBypassBlocked,
    block_legacy_delegate_for_launch57,
    launch57_bound_capability_ids,
)


def test_launch57_bound_capability_ids_non_empty():
    ids = launch57_bound_capability_ids()
    assert 504 in ids
    assert 47 in ids
    assert all(i > 0 for i in ids)


def test_legacy_delegate_blocked_for_launch57_bound_cap():
    with pytest.raises(Launch57LegacyBypassBlocked, match="launch57_isolation"):
        block_legacy_delegate_for_launch57(504)


@pytest.mark.asyncio
async def test_institutional_execute_blocks_legacy_for_launch57_cap(monkeypatch):
    monkeypatch.setattr("launch57.data_batch1.LAUNCH57_BATCH1_CAP_IDS", frozenset())

    from cap646.institutional_official_production import execute

    with pytest.raises(Launch57LegacyBypassBlocked):
        await execute(504, params={"symbol": "BTC"})


def test_command_home_kill_switch_returns_503_not_success(monkeypatch):
    from fastapi.testclient import TestClient

    from dashboard import app

    async def broken(*a, **k):
        raise RuntimeError("kill_switch_edge_ui_batch2")

    import launch57.edge_ui_batch2 as mod

    monkeypatch.setattr(mod, "six_heroes_command_home", broken)
    client = TestClient(app)
    client.cookies.set("bd_token", "wave4-kill-switch")
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 503
    body = res.json()
    detail = body.get("detail") if isinstance(body.get("detail"), dict) else body
    assert detail.get("success") is False
    assert "kill_switch" in str(detail.get("reason", ""))
