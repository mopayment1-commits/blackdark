"""Launch-57 anonymous public visitor — a11y + mobile + display source registry batch."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from launch57.anonymous_public_display_sources import (
    BUILDER_STATUS,
    LicensePublicDisplay,
    PUBLIC_VISITOR_PAGES,
    build_governance_artifact,
    build_public_page_display_registry,
    build_public_page_table,
    gate_public_numeric_payload,
    resolve_public_display,
    verify_registry_completeness,
)

ROOT = Path(__file__).resolve().parents[2]
A11Y_CSS = ROOT / "static" / "css" / "public-visitor-a11y.css"
GOV_ARTIFACT = ROOT / "governance" / "launch57" / "BLACKDARK_LAUNCH57_ANONYMOUS_PUBLIC_DISPLAY_SOURCES.json"

PUBLIC_PAGE_PATHS = [p["path"] for p in PUBLIC_VISITOR_PAGES]


@pytest.fixture(autouse=True)
def disable_viral_rate_limits(monkeypatch):
    monkeypatch.setattr("viral_capacity.viral_middleware_enabled", lambda: False)


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_builder_status_pending_verification():
    assert BUILDER_STATUS == "PENDING_VERIFICATION"
    artifact = build_governance_artifact()
    assert artifact["pass_live_not_claimed"] is True
    assert artifact["legal_review_markers_open"] is True
    assert artifact["mica_uk_compliance_claim_forbidden"] is True


def test_registry_every_metric_has_license_status():
    verification = verify_registry_completeness()
    assert verification["all_metrics_have_license_status"] is True
    assert verification["missing_license_status"] == []
    for row in build_public_page_display_registry():
        assert row["license_public_display"] in {
            LicensePublicDisplay.KNOWN.value,
            LicensePublicDisplay.DELAYED.value,
            LicensePublicDisplay.BLOCKED.value,
        }


def test_break_public_number_without_license_status_fails():
    """Break test — registry row missing license must fail completeness check."""
    bad_row = {
        "metric_id": "break_no_license",
        "page_id": "landing",
        "license_public_display": "UNSPECIFIED",
    }
    allowed = {
        LicensePublicDisplay.KNOWN.value,
        LicensePublicDisplay.DELAYED.value,
        LicensePublicDisplay.BLOCKED.value,
    }
    assert bad_row["license_public_display"] not in allowed


def test_resolve_public_display_blocks_unlicensed_raw_provider():
    blocked = resolve_public_display(
        "landing_trust_pulse_price",
        42000.0,
        license_public_display=LicensePublicDisplay.BLOCKED.value,
    )
    assert blocked["display_allowed"] is False
    assert blocked["reason"] == "blocked_unlicensed_raw_provider"

    missing = resolve_public_display("unknown_metric", 1)
    assert missing["display_allowed"] is False
    assert missing["reason"] == "unknown_metric"

    no_license = resolve_public_display(
        "landing_trust_pulse_price",
        1.0,
        license_public_display="",
    )
    assert no_license["display_allowed"] is False
    assert no_license["reason"] == "missing_license_public_display"


def test_gate_public_numeric_payload_blocks_raw_when_blocked():
    ok = gate_public_numeric_payload({"price": 1.0}, "landing_trust_pulse_price")
    assert ok["allowed"] is True
    assert ok["license_public_display"] == LicensePublicDisplay.KNOWN.value

    blocked = gate_public_numeric_payload({"price": 1.0}, "break_no_license")
    assert blocked["allowed"] is False


def test_page_table_covers_scoped_public_pages():
    table = build_public_page_table()
    paths = {row["path"] for row in table}
    for page in PUBLIC_VISITOR_PAGES:
        assert page["path"] in paths
    landing = next(r for r in table if r["path"] == "/")
    assert landing["metric_count"] >= 5
    accuracy = next(r for r in table if r["path"] == "/oracle-accuracy")
    assert accuracy["metric_count"] >= 6


def test_governance_artifact_written():
    artifact = build_governance_artifact()
    GOV_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    GOV_ARTIFACT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    loaded = json.loads(GOV_ARTIFACT.read_text(encoding="utf-8"))
    assert loaded["builder_status"] == "PENDING_VERIFICATION"
    assert len(loaded["page_table"]) == len(PUBLIC_VISITOR_PAGES)


def test_a11y_css_has_focus_visible_and_narrow_viewport():
    css = A11Y_CSS.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "max-width: 400px" in css
    assert ".bd-site-footer" in css
    assert ".hero-cta" in css or ".cta-row" in css


@pytest.mark.parametrize("path", PUBLIC_PAGE_PATHS)
def test_public_pages_include_a11y_stylesheet(client, path: str):
    res = client.get(path)
    assert res.status_code == 200, path
    assert "/static/css/public-visitor-a11y.css" in res.text


@pytest.mark.parametrize("path", PUBLIC_PAGE_PATHS)
def test_public_pages_have_skip_links(client, path: str):
    res = client.get(path)
    html = res.text
    assert 'class="skip-link"' in html or "skip-link" in html
    assert "Skip to" in html


@pytest.mark.parametrize("path", PUBLIC_PAGE_PATHS)
def test_public_pages_footer_present(client, path: str):
    res = client.get(path)
    html = res.text
    assert 'id="site-footer"' in html or 'class="bd-site-footer"' in html
    assert "/terms" in html
    assert "/privacy" in html


@pytest.mark.parametrize("path", PUBLIC_PAGE_PATHS)
def test_public_pages_cta_present_on_narrow_viewport_css(client, path: str):
    """CSS contract: ≤400px rules keep CTA + footer visible."""
    css = A11Y_CSS.read_text(encoding="utf-8")
    assert "max-width: 400px" in css
    assert "visibility: visible" in css
    res = client.get(path)
    assert res.status_code == 200
    html = res.text
    has_cta = (
        "btn-primary" in html
        or 'class="btn ' in html
        or "hero-cta" in html
        or 'href="/login' in html
        or 'href="/#try-oracle"' in html
        or 'href="/oracle-accuracy"' in html
    )
    assert has_cta or path in {"/terms", "/privacy", "/disclaimer"}


def test_landing_freshness_chips_have_text_labels(client):
    res = client.get("/")
    html = res.text
    assert 'id="lpFresh"' in html
    assert 'id="oracleFreshnessLabel"' in html
    assert 'id="lpPriceFresh"' in html
    assert 'aria-hidden="true"' in html
    assert 'role="status"' in html


def test_landing_no_mica_uk_compliance_claims(client):
    res = client.get("/")
    html = res.text.lower()
    assert "mica compliant" not in html
    assert "uk compliant" not in html
    assert "mica/uk" not in html


def test_status_pills_have_text_not_color_only(client):
    res = client.get("/status")
    html = res.text
    assert 'class="status-pill"' in html
    assert 'aria-label="Overall status:' in html


def _color_only_chip_html() -> str:
    return '<div class="live-indicator"><span class="live-dot"></span></div>'


def _text_backed_chip_html() -> str:
    return (
        '<div class="live-indicator" role="status" aria-label="Freshness: LIVE">'
        '<span class="live-dot" aria-hidden="true"></span>'
        "<span>LIVE</span></div>"
    )


def test_break_color_only_chip_without_text_fails():
    """Break test — color-only status chip (dot, no text) must be detected."""
    bad = _color_only_chip_html()
    good = _text_backed_chip_html()

    def chip_has_text_alternative(fragment: str) -> bool:
        if re.search(r"<span[^>]*class=['\"][^'\"]*(?:live-dot|tp-mini-dot|status-dot)", fragment):
            if re.search(r"aria-label=['\"][^'\"]{3,}", fragment):
                return True
            if re.search(r"<span[^>]*>(?!\\s*</span>)[^<]{2,}</span>", fragment):
                return True
            return False
        return True

    assert chip_has_text_alternative(bad) is False
    assert chip_has_text_alternative(good) is True


def test_landing_template_chips_pass_color_only_guard():
    landing = (ROOT / "templates" / "landing.html").read_text(encoding="utf-8")
    for chip_id in ("lpFresh", "oracleFreshnessLabel", "lpPriceFresh"):
        assert chip_id in landing
    assert 'aria-hidden="true"' in landing
    assert "Freshness unknown" in landing or "pulse.live" in landing


def test_legal_pages_no_invented_license_language(client):
    for path in ("/terms", "/privacy", "/disclaimer"):
        res = client.get(path)
        html = res.text.lower()
        assert "pass_live" not in html
        assert "mica compliant" not in html
