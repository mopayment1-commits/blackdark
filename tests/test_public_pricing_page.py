"""Public /pricing page — sole visitor price surface."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_pricing_nav_points_to_pricing_route():
    from dashboard import app

    html = TestClient(app).get("/").text
    assert 'id="bdUtilPricing"' in html
    assert 'href="/pricing"' in html
    assert '/#pricing' not in html.split('id="bdUtilPricing"')[1].split(">", 1)[0]


def test_pricing_cards_layout():
    from dashboard import app

    page = TestClient(app).get("/pricing")
    assert page.status_code == 200
    text = page.text
    for name in ("Free", "Plus", "Pro", "Enterprise"):
        assert name in text
    assert "$0" in text
    assert "$29" in text and "/month" in text
    assert "$49" in text
    assert "Compare plans" in text
    assert 'id="enterprise"' in text
    assert "Talk to us" in text
    assert 'href="/login?next=/profile"' in text
    assert "Billing" in text
    assert 'href="/refund"' in text
    assert "Refund Policy" in text
    lowered = text.lower()
    for banned in ("lemon", "stripe", "kyc", "checkout url"):
        assert banned not in lowered
    assert "billingReadyLine" not in text
