"""Binding checks from Sat/Sun conversation audit — legal shield + pricing ladder."""
from __future__ import annotations

from pricing_catalog import TIERS, pricing_catalog


def _by_id():
    return {t["id"]: t for t in TIERS}


def test_founder_confirmed_price_ladder():
    by = _by_id()
    assert by["free"]["price_usd_month"] == 0
    assert by["free"]["name"] == "Proof Pass"
    assert by["pro"]["price_usd_month"] == 29
    assert by["whale"]["price_usd_month"] == 49
    assert by["whale"]["name"] == "Decision Desk"
    assert by["institutional"]["price_usd_month_from"] == 3000
    assert "3,000" in by["institutional"]["price_display"]
    assert "open" in by["institutional"]["price_display"].lower()


def test_pricing_tiers_order():
    ids = [t["id"] for t in TIERS]
    assert ids[:4] == ["free", "pro", "whale", "institutional"]
    cat = pricing_catalog()
    assert cat["currency"] == "USD"
    assert "MORNING_SESSION_FINAL_BINDING" in cat["binding"]


def test_no_rejected_199_whale_desk_in_catalog():
    blob = str(TIERS)
    assert "199" not in blob
    assert "Whale Desk" not in blob


def test_legal_shield_prefix_in_certificate_module():
    import decision_certificate as dc

    assert hasattr(dc, "LEGAL_SHIELD_PREFIX")
    assert "Not financial advice" in dc.LEGAL_SHIELD_PREFIX
    assert "Four-layer" in dc.LEGAL_SHIELD_PREFIX


def test_terms_contain_four_layer_shield():
    from legal_content import TERMS_OF_SERVICE

    assert "Four-layer legal shield" in TERMS_OF_SERVICE
    assert "Terms acknowledgement gate" in TERMS_OF_SERVICE


def test_safe_errors_no_leak():
    from safe_errors import public_error

    class Boom(Exception):
        pass

    msg = public_error(Boom("secret path /etc/passwd"), fallback="Request failed")
    assert "passwd" not in msg
    assert msg == "Request failed"


def test_dashboard_exposes_terms_ack_and_system_info():
    src = open("dashboard.py", encoding="utf-8").read()
    assert "/api/legal/ack-terms" in src
    assert "/system/info" in src
    assert "_legal_terms_ack_ok" in src
