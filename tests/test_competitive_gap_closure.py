"""Competitive gap closure: Decimal money, referral loop, compliance, PWA shell."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest


def test_money_decimal_helpers():
    from money import D, money_float, money_round, money_str, net_after_fees, usd_to_cents

    assert D("0.1") + D("0.2") == Decimal("0.3")
    assert money_round(1.005) == Decimal("1.01")
    assert money_str(12.3) == "12.30"
    assert money_float("9.999") == 10.0
    assert net_after_fees(100, 10) == Decimal("90.0000")
    assert usd_to_cents("19.99") == 1999


def test_referral_code_normalize_and_generate():
    from referral_service import generate_referral_code, normalize_referral_code

    assert normalize_referral_code(" ab-cd12 ") == "ABCD12"
    assert normalize_referral_code("no") == ""
    code = generate_referral_code("alice@example.com")
    assert normalize_referral_code(code)
    assert 6 <= len(code) <= 16


@pytest.mark.asyncio
async def test_referral_apply_and_stats(tmp_path, monkeypatch):
    import config

    db_path = tmp_path / "ref.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark.io")

    from database import init_db
    from referral_service import apply_referral_on_signup, ensure_user_referral_code, referral_stats

    await init_db()

    from auth_service import register_user

    referrer = await register_user("referrer@example.com", "password123", "Referrer")
    referrer_id = int(referrer["user"]["id"])
    code = await ensure_user_referral_code(referrer_id, "referrer@example.com")

    invited = await register_user(
        "invited@example.com",
        "password123",
        "Invited",
        referral_code=code,
    )
    assert invited.get("referral", {}).get("applied") is True

    stats = await referral_stats(referrer_id)
    assert stats["referral_code"] == code
    assert stats["successful_referrals"] >= 1
    assert stats["share_url"].endswith(f"/?ref={code}")
    assert "blackdark.io" in stats["share_url"]

    # Self-referral must fail closed
    self_res = await apply_referral_on_signup(
        new_user_id=referrer_id,
        new_email="referrer@example.com",
        referral_code=code,
    )
    assert self_res["applied"] is False


def test_compliance_page_and_pwa_assets_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "templates" / "offline.html").is_file()
    assert (root / "static" / "sw.js").is_file()
    assert (root / "static" / "manifest.json").is_file()
    assert (root / "static" / "icon-192.png").is_file()
    assert (root / "money.py").is_file()
    assert (root / "referral_service.py").is_file()

    from legal_content import LEGAL_PAGES

    assert "compliance" in LEGAL_PAGES
    body = LEGAL_PAGES["compliance"]["html"]
    assert "analytical" in body.lower() or "Anti-Hype" in body


def test_templates_wire_referral_and_pwa():
    root = Path(__file__).resolve().parents[1]
    landing = (root / "templates" / "landing.html").read_text(encoding="utf-8")
    login = (root / "templates" / "login.html").read_text(encoding="utf-8")
    dashboard = (root / "templates" / "dashboard.html").read_text(encoding="utf-8")
    b2b = (root / "templates" / "b2b.html").read_text(encoding="utf-8")

    assert "captureReferralFromUrl" in landing
    assert "/compliance" in landing
    assert "serviceWorker.register('/sw.js'" in landing
    assert "referral_code" in login
    assert "bd_ref" in login
    assert "Invite &amp; earn" in dashboard or "Invite & earn" in dashboard
    assert "serviceWorker.register('/sw.js'" in dashboard
    assert "bootFundTerminalDeepLink" in b2b
    assert "fundOnboardingChecklist" in b2b


def test_sw_offline_shell():
    sw = Path(__file__).resolve().parents[1] / "static" / "sw.js"
    text = sw.read_text(encoding="utf-8")
    assert "/offline" in text
    assert "blackdark-v4" in text
