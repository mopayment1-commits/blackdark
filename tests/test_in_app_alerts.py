"""In-app alerts work without Telegram/SMTP."""

from __future__ import annotations

import pytest


def test_in_app_push_and_list():
    from in_app_alerts import inbox_stats, list_in_app_alerts, mark_read, push_in_app_alert

    row = push_in_app_alert("Test signal", "BTC ACT", payload={"asset": "BTC"}, level="signal")
    assert row["id"].startswith("ina_")
    rows = list_in_app_alerts(limit=10)
    assert any(r["id"] == row["id"] for r in rows)
    stats = inbox_stats()
    assert stats["total"] >= 1
    marked = mark_read(row["id"])
    assert marked and marked["read"] is True


@pytest.mark.asyncio
async def test_dispatch_alert_always_writes_inbox():
    from alert_service import dispatch_alert
    from in_app_alerts import list_in_app_alerts

    result = await dispatch_alert(
        "Oracle",
        "Do Not Touch ETH",
        payload={"asset": "ETH"},
        channels=["telegram", "email", "in_app"],
    )
    assert result["channels"].get("in_app") is True
    assert result.get("in_app_id")
    assert any(r["id"] == result["in_app_id"] for r in list_in_app_alerts(limit=20))


def test_arbitrage_catalog_requires_feature_in_source():
    from pathlib import Path

    src = Path("api/routers/arbitrage.py").read_text(encoding="utf-8")
    # catalog route must be gated like catalog/scan
    assert 'require_feature("arbitrage_catalog")' in src
    assert "@router.get(\"/catalog\")" in src
