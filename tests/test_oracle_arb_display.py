"""Oracle arb opportunity display (paid endpoint)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "arb_disp.db"))
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_arb_endpoint_requires_auth(client):
    res = client.get("/api/oracle/arb-opportunities/BTC")
    assert res.status_code == 401


def test_arb_public_endpoint_no_auth(client):
    res = client.get("/api/oracle/arb-opportunities/public")
    assert res.status_code == 200
    body = res.json()
    assert "opportunities" in body
    assert isinstance(body["opportunities"], list)


def test_oracle_accuracy_has_arb_section(client):
    res = client.get("/oracle-accuracy")
    assert res.status_code == 200
    assert "arb-opportunities-panel" in res.text
    assert "Arb Opportunities" in res.text


def test_landing_has_arb_button_markup(client):
    html = client.get("/").text
    assert "lpArbBtn" in html
    assert "View Arb Opportunities" in html


def test_pairwise_limit():
    from oracle_arb_display import _pairwise_from_compare

    compare = {
        "venues": [
            {"exchange": "binance", "best_ask": 100.0, "best_bid": 99.5},
            {"exchange": "okx", "best_ask": 100.2, "best_bid": 100.1},
            {"exchange": "bybit", "best_ask": 100.1, "best_bid": 100.05},
        ]
    }
    rows = _pairwise_from_compare(compare, "BTC", 5)
    assert len(rows) <= 5
    assert rows[0]["price_diff_percent"] > 0
