"""P6 DTS cross-cutting delivery — timezone, i18n, accessibility."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from decision_truth import govern_decision_payload
from decision_truth.cross_cutting import apply_cross_cutting_delivery
from decision_truth.cross_cutting.i18n import validate_38_locale_coverage
from decision_truth.cross_cutting.locales import CANONICAL_38_LOCALES, normalize_dts_locale
from governance.timezone_governance import (
    ensure_utc_aware,
    format_user_facing_timestamp,
    parse_canonical_timestamp,
    resolve_user_timezone,
    to_user_local,
)
from accessibility_audit_service import audit_dts_accessibility_metadata


def _complete_payload(**overrides):
    base = {
        "symbol": "BTC",
        "kind": "cross_exchange",
        "quote_age_ms": 120,
        "data_quality_score": 80,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "liquidity_ok": True,
        "risk_ok": True,
        "net_profit_usdt": 10,
        "quote_amount": 1000,
        "depth_usd": 250000,
        "fill_probability": 0.92,
        "total_slippage_bps": 3,
        "trading_fees_usdt": 0.2,
        "withdrawal_fee_usdt": 0.05,
        "live_duration_seconds": 8,
        "estimated_recipients": 5,
        "timestamp": "2026-09-14T12:00:00+00:00",
    }
    base.update(overrides)
    return base


def test_utc_canonical_storage_contract():
    ts = parse_canonical_timestamp("2026-09-14T12:00:00Z")
    assert ts is not None
    assert ts.tzinfo is not None
    assert ensure_utc_aware(ts).tzinfo == UTC


def test_user_timezone_rendering():
    rendered = format_user_facing_timestamp("2026-09-14T12:00:00Z", "America/New_York")
    assert rendered["canonical_utc"] is not None
    assert rendered["user_local"] is not None
    assert rendered["canonical_mutated"] is False
    assert "America" in rendered["timezone"]["timezone"] or rendered["timezone"]["timezone"] == "America/New_York"


def test_dst_transition_behavior():
    # US spring forward — 2026-03-08 06:30 UTC -> EST/EDT boundary region
    ts = parse_canonical_timestamp("2026-03-08T06:30:00Z")
    local = to_user_local(ts, "America/New_York")
    assert local.fold == 0


def test_invalid_timezone_fallback():
    resolved = resolve_user_timezone("Not/A_Real_Zone")
    assert resolved["fallback_used"] is True
    assert resolved["timezone"] == "UTC"


def test_review_outcome_timestamps_consistent():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    tz = out.get("dts_timezone") or {}
    assert tz.get("canonical_storage") == "UTC"
    assert "canonical_timestamps" in tz
    assert tz.get("duplicate_authority") is False


def test_no_canonical_timestamp_mutation_on_presentation():
    canonical = "2026-09-14T12:00:00+00:00"
    rendered = format_user_facing_timestamp(canonical, "Europe/London")
    assert rendered["canonical_utc"].startswith("2026-09-14T12:00:00")


def test_dts_reasons_rendered_through_canonical_i18n():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    i18n = out.get("dts_i18n") or {}
    assert i18n.get("canonical_message_keys") is True
    assert i18n.get("why_not", {}).get("message_keys_used") is True
    assert i18n.get("decision_state_label")


def test_why_not_translated_ar():
    out = govern_decision_payload(_complete_payload(liquidity_ok=False, depth_usd=1), run_data_governance=False)
    out_ar = apply_cross_cutting_delivery(out, lang="ar")
    i18n = out_ar.get("dts_i18n") or {}
    assert i18n.get("locale") == "ar"
    assert i18n.get("why_not", {}).get("human_explanation")
    assert i18n.get("why_not", {}).get("message_keys_used") is True


def test_rejection_abstention_messages_translated():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    loc = out.get("dts_i18n") or {}
    assert loc.get("no_decision_label")
    assert loc.get("rejection_summary") or loc.get("no_decision", {}).get("reason")


def test_simulation_risk_evidence_disclosures_translated():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    loc = out.get("dts_i18n") or {}
    assert loc.get("six_heroes", {}).get("labels_localized") is True
    assert loc.get("daily_evidence_autopsy", {}).get("section_labels")


def test_38_locale_coverage_validation():
    report = validate_38_locale_coverage()
    assert report["locale_count"] == 38
    assert report["ok"] is True
    assert len(CANONICAL_38_LOCALES) == 38


def test_missing_key_fallback():
    from i18n_service import t

    text = t("dts.state.available", "cs")
    assert text and text.strip()


def test_interpolation_safety():
    from i18n_service import t

    text = t("dts.why.net_edge", "en", bps=12)
    assert "12" in text
    assert "{" not in text


def test_no_hardcoded_english_in_intended_dts_paths():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    loc = out.get("dts_i18n") or {}
    assert loc.get("locale")
    assert loc.get("why_not", {}).get("human_explanation")
    assert "message_keys_used" in loc.get("why_not", {})


def test_keyboard_traversal_metadata():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    a11y = out.get("dts_accessibility") or {}
    assert a11y["global"]["keyboard_navigation"] is True


def test_focus_visibility_and_order():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    global_a11y = (out.get("dts_accessibility") or {}).get("global") or {}
    assert global_a11y.get("visible_focus") is True
    assert global_a11y.get("focus_order_documented") is True


def test_screen_reader_accessible_labels():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    state = (out.get("dts_accessibility") or {}).get("state_presentation") or {}
    assert state.get("accessible_name")
    assert state.get("text_label")


def test_no_color_only_risk_evidence_meaning():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    assert (out.get("dts_accessibility") or {}).get("global", {}).get("color_only_meaning") is False


def test_accessible_no_decision_reject_abstain_states():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    state = (out.get("dts_accessibility") or {}).get("state_presentation") or {}
    assert state.get("symbol")
    assert state.get("text_label")
    audit = audit_dts_accessibility_metadata(out.get("dts_accessibility"))
    assert audit["ok"] is True


def test_chart_result_textual_alternatives():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    alt = (out.get("dts_accessibility") or {}).get("global", {}).get("chart_text_alternative")
    assert alt and isinstance(alt, str)


def test_status_error_announcements():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    assert (out.get("dts_accessibility") or {}).get("global", {}).get("status_announcements") is True


def test_responsive_zoom_text_resize_metadata():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    g = (out.get("dts_accessibility") or {}).get("global") or {}
    assert g.get("responsive_zoom_supported") is True
    assert g.get("text_resize_supported") is True


def test_accessibility_automated_checks():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    audit = audit_dts_accessibility_metadata(out.get("dts_accessibility"))
    assert audit["ok"] is True
    assert audit["issues"] == []


def test_p5_regression_product_experience_still_present():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    assert out.get("product_experience")
    assert out.get("dts_timezone")
    assert out.get("dts_i18n")
    assert out.get("dts_accessibility")


def test_cross_cutting_authorities_not_duplicated():
    cc = govern_decision_payload(_complete_payload(), run_data_governance=False).get("dts_cross_cutting") or {}
    assert cc.get("duplicate_timezone_authority") is False
    assert cc.get("parallel_translation_system") is False
