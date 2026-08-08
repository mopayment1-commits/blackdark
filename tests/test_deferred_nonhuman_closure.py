"""Closure tests for deferred non-human engineering gaps."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


FOOTER_TEMPLATES = [
    "templates/login.html",
    "templates/profile.html",
    "templates/reset_password.html",
    "templates/success.html",
    "templates/oracle_accuracy.html",
    "templates/platform.html",
    "templates/b2b.html",
    "templates/docs_public.html",
    "templates/discipline.html",
    "templates/coin.html",
    "templates/dashboard.html",
    "templates/landing.html",
    "templates/utility.html",
    "templates/legal.html",
]


def test_site_footer_included_on_public_surfaces():
    for path in FOOTER_TEMPLATES:
        src = (ROOT / path).read_text(encoding="utf-8")
        assert "partials/site_footer.html" in src, path


def test_cancel_page_and_route():
    util = (ROOT / "templates/utility.html").read_text(encoding="utf-8")
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert "page == 'cancel'" in util
    assert '"page": "cancel"' in dash
    assert '"/cancel"' in dash
    assert "utility.html" in dash


def test_orphan_index_has_no_inter_or_purple():
    idx = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com/css2?family=Inter" not in idx
    assert "#a78bfa" not in idx
    assert "Inter" not in idx
    assert "/dashboard" in idx
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "Syne" in notices and "IBM Plex" in notices
    assert "Inter, Tajawal" not in notices


def test_trust_pulse_previous_factors_wire():
    dash_py = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    dash_html = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "previous_factors" in dash_py
    assert "previous_factors" in dash_html
    assert "JSON.stringify(prev.factors" in dash_html


def test_dashboard_stream_and_operate_digest_ui():
    html = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "startDashboardStream" in html
    assert "/api/dashboard/stream" in html
    assert 'id="operate-digest"' in html
    assert "loadDailyReport" in html
    assert "loadSubscriberValue" in html
    assert "/api/reports/daily" in html
    assert "/api/subscriber/value" in html
    profile = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    assert "loadSubscriberValue" in profile
    assert "/api/subscriber/value" in profile


def test_identity_debug_hard_off_and_production_guard(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    from identity_service import debug_tokens_enabled

    assert debug_tokens_enabled() is False

    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LEMON_SQUEEZY_CHECKOUT_PRO", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    ids = {c["id"]: c for c in report["checks"]}
    assert "identity_debug_tokens_off" in ids
    assert ids["identity_debug_tokens_off"]["ok"] is False
    assert "identity_debug_tokens_off" in report["required_failures"]


def test_footer_ctx_passed_on_key_routes():
    src = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert 'login.html", _footer_ctx()' in src
    assert 'profile.html", _footer_ctx()' in src
    assert 'oracle_accuracy.html", _footer_ctx()' in src
    assert 'platform.html", _footer_ctx()' in src
    assert 'discipline.html", _footer_ctx()' in src
    assert "**_footer_ctx()" in src


def test_sitemap_has_no_dead_pricing_path():
    src = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert '"/pricing"' not in src


def test_shape_pulse_uses_previous_factors():
    import time

    from trust_pulse import _shape_pulse

    payload = {
        "symbol": "BTC",
        "decision_action": "ACT",
        "decision_sentence": "Act with proof.",
        "tier": "pro",
        "oqs_why": {
            "top_3_factors": [
                {"factor": "Flow", "detail": "in", "source": "cvvd"},
                {"factor": "Regime", "detail": "risk-on", "source": "ctx"},
            ]
        },
        "decision_certificate": {"certificate_hash": "abc"},
        "_pulse_meta": {"fetched_at": time.time()},
    }
    pulse = _shape_pulse(
        payload,
        previous_action="WAIT",
        previous_factors=[{"factor": "Old momentum", "detail": "", "source": ""}],
    )
    cont = pulse.get("continuity") or {}
    assert cont.get("locked") is not True
    assert cont.get("flipped") is True
    assert "Flow" in (cont.get("new_factors") or []) or "Regime" in (cont.get("new_factors") or [])
