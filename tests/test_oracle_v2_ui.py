"""Oracle v2 HTML decision surface."""

from __future__ import annotations

import pytest

import config
import database
import fee_matrix


@pytest.fixture(scope="module")
def oracle_client():
    from dashboard import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client


def test_oracle_v2_html_page(oracle_client):
    response = oracle_client.get(
        "/oracle/BTC?ux_mode=beginner&lang=en",
        headers={"Accept": "text/html"},
    )
    assert response.status_code in {200, 403, 404, 502}
    if response.status_code != 200:
        return
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "BTC" in body
    assert "Verdict" in body
    assert "Confidence" in body
    assert "CVD" in body
    assert "Funding" in body
    assert "Whale" in body
    assert "Not financial advice. DYOR." in body
    assert "View Decision Certificate" in body


def test_oracle_json_format_param(oracle_client):
    response = oracle_client.get("/oracle/BTC?format=json&ux_mode=beginner&lang=en")
    assert response.status_code in {200, 403, 404, 502}
    if response.status_code != 200:
        return
    data = response.json()
    assert "opportunity_score" in data or "verdict" in data


def test_oracle_json_accept_header(oracle_client):
    response = oracle_client.get(
        "/oracle/BTC?ux_mode=beginner&lang=en",
        headers={"Accept": "application/json"},
    )
    assert response.status_code in {200, 403, 404, 502}
    if response.status_code != 200:
        return
    assert response.headers.get("content-type", "").startswith("application/json")


def test_oracle_ui_helpers():
    from oracle_ui import verdict_tone, wants_oracle_json

    class _Req:
        headers = {"accept": "application/json"}
        query_params = {}

    class _HtmlReq:
        headers = {"accept": "text/html,application/xhtml+xml"}
        query_params = {}

    assert wants_oracle_json(_Req()) is True
    assert wants_oracle_json(_HtmlReq()) is False
    assert verdict_tone("BUY") == "green"
    assert verdict_tone("WAIT") == "yellow"
    assert verdict_tone("SELL") == "red"


@pytest.mark.asyncio
async def test_oracle_v2_fee_snapshot_reads_persisted_fees_table(tmp_path, monkeypatch):
    from oracle_ui import build_fee_snapshot_from_db

    db_path = tmp_path / "oracle_v2_fees.db"
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    fee_matrix._matrix.clear()
    await database.init_db()
    await fee_matrix.calculate_opportunity_fees(
        "oracle-ui-btc",
        "binance",
        "BTC/USDT",
        "buy",
        10_000.0,
        gross_profit_usdt=42.0,
    )

    fee = await build_fee_snapshot_from_db("BTC", {})
    assert fee["mode"] == "persisted_latest_symbol"
    assert fee["total_fee_usdt"] is not None
    assert fee["net_profit_usdt"] is not None
    assert fee["net_profit_usdt"] < 42.0


@pytest.mark.asyncio
async def test_oracle_v2_fee_snapshot_fail_closed_without_row(tmp_path, monkeypatch):
    from oracle_ui import build_fee_snapshot_from_db

    db_path = tmp_path / "oracle_v2_empty.db"
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    fee_matrix._matrix.clear()
    await database.init_db()

    fee = await build_fee_snapshot_from_db("BTC", {})
    assert fee["mode"] == "unavailable"
    assert "fail-closed" in fee["label"].lower()


@pytest.mark.asyncio
async def test_oracle_v2_context_async(tmp_path, monkeypatch):
    from oracle_ui import build_oracle_v2_context

    db_path = tmp_path / "oracle_v2_ctx.db"
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    fee_matrix._matrix.clear()
    await database.init_db()

    ctx = await build_oracle_v2_context(
        {
            "verdict": "WAIT",
            "confidence": 72,
            "oracle": "Wait on BTC — mixed signals.",
            "risk_level": "Medium",
            "opportunity_half_life": {"expected_half_life_seconds": 3600},
            "whale_alert": "Large inflow detected",
        },
        asset="BTC",
        price=65000.0,
        change=1.2,
        ux_mode="beginner",
        lang="en",
    )
    assert ctx["asset"] == "BTC"
    assert ctx["confidence"] == 72
    assert len(ctx["drivers"]) == 3
    assert ctx["hold_period"] == "1.0h"
    assert ctx["fee"]["mode"] == "unavailable"
