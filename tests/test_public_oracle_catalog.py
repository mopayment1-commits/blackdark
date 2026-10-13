from __future__ import annotations

from fastapi.testclient import TestClient


def test_public_oracle_symbols_matches_universe_registry():
    from site_oracle_catalog import primary_oracle_catalog_symbols

    client = TestClient(__import__("dashboard").app)
    res = client.get("/api/public/oracle-symbols")
    assert res.status_code == 200
    body = res.json()
    expected = list(primary_oracle_catalog_symbols())
    assert body["count"] == len(expected)
    assert body["symbols"] == expected
    assert len(expected) >= 10


def test_landing_has_symbol_catalog_select():
    from dashboard import app

    html = TestClient(app).get("/").text
    assert 'id="symbolCatalog"' in html
    assert 'id="symbolInput"' in html
    assert "readonly" in html.split('id="symbolInput"', 1)[1][:200]
    assert 'BTC / ETH / SOL' not in html
    assert html.count('<option value="BTC"') >= 1
    assert html.count("<option value=") >= 50
