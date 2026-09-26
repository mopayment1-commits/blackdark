"""Supplemental Memorandum (21 Sep 2026) — public layer compliance tests."""

from __future__ import annotations

from starlette.requests import Request

from supplemental_public_compliance import (
    CONDITIONS_MET_REVIEW_LINE,
    EU_OPTIONAL_ANALYTICS_BANNER_BODY,
    apply_supplemental_public_layer,
    is_eea_request,
    map_public_decision_action,
    optional_analytics_allowed,
    optional_analytics_banner_payload,
    scrub_prohibited_phrases,
    scrub_regulatory_claims,
)

EU_BANNER_BODY_SECTION_8_4 = (
    "BLACKDARK uses strictly necessary technologies to operate and secure the service. "
    "With your permission, we may also use optional analytics technologies to understand how the service is used. "
    "Optional technologies remain disabled unless you choose to accept them. "
    "You can accept, reject, or manage your preferences."
)


def _request(headers: dict[str, str] | None = None, cookies: dict[str, str] | None = None) -> Request:
    merged = dict(headers or {})
    if cookies:
        merged["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in merged.items()],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
        "scheme": "http",
        "http_version": "1.1",
    }
    return Request(scope)


def test_eu_optional_analytics_banner_body_section_8_4_literal():
    assert EU_OPTIONAL_ANALYTICS_BANNER_BODY == EU_BANNER_BODY_SECTION_8_4
    payload = optional_analytics_banner_payload(_request(headers={"CF-IPCountry": "DE"}))
    assert payload["body"] == EU_BANNER_BODY_SECTION_8_4


def test_visitor_sees_conditions_met_not_act():
    out = apply_supplemental_public_layer(
        {"decision_action": "ACT", "symbol": "BTC", "verdict": "Buy Now"},
        user=None,
    )
    assert out["decision_action"] == "CONDITIONS MET"
    assert "ACT" not in str(out.get("decision_sentence", ""))
    assert CONDITIONS_MET_REVIEW_LINE in str(out.get("conditions_met_review", ""))


def test_map_public_decision_action_replaces_act():
    assert map_public_decision_action("ACT") == "CONDITIONS MET"
    assert map_public_decision_action("WAIT") == "WAIT"


def test_scrub_trade_ctas_and_guaranteed_pricing():
    dirty = "Buy Now — Start Trading for Guaranteed 20% returns. Best crypto to buy."
    clean = scrub_prohibited_phrases(dirty)
    assert "Buy Now" not in clean
    assert "Start Trading" not in clean
    assert "Guaranteed" not in clean
    assert "Best crypto to buy" not in clean


def test_scrub_regulatory_license_claims():
    text = "We are FCA authorised and MiCA regulated with UK compliant badges."
    clean = scrub_regulatory_claims(text)
    assert "FCA authorised" not in clean
    assert "MiCA regulated" not in clean
    assert "market-data and analytical technology" in clean


def test_eu_visitor_no_optional_analytics_before_accept():
    req = _request(headers={"CF-IPCountry": "DE"})
    assert is_eea_request(req) is True
    assert optional_analytics_allowed(req) is False
    req_accept = _request(
        headers={"CF-IPCountry": "DE"},
        cookies={"bd_optional_analytics": "accept"},
    )
    assert optional_analytics_allowed(req_accept) is True


def test_eu_reject_blocks_optional_analytics_next_request():
    req = _request(
        headers={"CF-IPCountry": "FR"},
        cookies={"bd_optional_analytics": "reject"},
    )
    assert optional_analytics_allowed(req) is False


def test_sanitize_oracle_payload_public_layer():
    from security_sanitize import sanitize_oracle_payload

    out = sanitize_oracle_payload(
        {"verdict": "Buy Now", "decision_action": "ACT", "symbol": "ETH"},
        user=None,
    )
    assert out["decision_action"] == "CONDITIONS MET"
    assert CONDITIONS_MET_REVIEW_LINE in str(out.get("conditions_met_review", ""))
