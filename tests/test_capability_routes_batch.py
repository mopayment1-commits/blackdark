"""Tests — P0 capability routes (Route Sovereignty)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)

CAPABILITY_ROUTES = (
    ("/exchanges", "exchanges"),
    ("/stablecoins", "stablecoins"),
    ("/arbitrage", "arbitrage"),
    ("/brief", "brief"),
    ("/whales", "whales"),
)


@pytest.mark.parametrize("path,cap_id", CAPABILITY_ROUTES)
def test_capability_route_returns_html(path: str, cap_id: str):
    res = client.get(path)
    assert res.status_code == 200
    body = res.text
    assert f'data-capability="{cap_id}"' in body
    assert "capability_pages.js" in body
    assert "capability_core.js" in body


def test_intelligence_hub_template_renamed():
    res = client.get("/intelligence-ledger")
    assert res.status_code == 200
    assert "Intelligence Hub" in res.text
    assert "intelligence_hub_renderers.js" in res.text
