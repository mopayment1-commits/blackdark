"""Surface closure tests — TZ-003..030, TZ-034 (T2: control removal fails)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from blackdark.timezone import utc_now_iso
from blackdark.timezone.display import (
    chart_config,
    cross_surface_status,
    export_metadata,
    format_ai_output,
    format_billing,
    format_email,
    format_for_locale,
    format_notification,
    format_with_label,
    resolve_timezone_independent_of_country,
    resolve_timezone_independent_of_lang,
    timezone_detection_privacy,
)
from blackdark.timezone.schedules import RecurringSchedule, register_schedule


# --- TZ-016 timezone clarity ---


def test_format_with_label_includes_timezone_context():
    row = format_with_label("2026-03-08T12:00:00Z", "America/New_York")
    assert row["label"]
    assert "America/New_York" in row["label"]
    assert row["timezone"] == "America/New_York"


def test_tz016_control_removal_fails(monkeypatch):
    from blackdark.timezone.display import enrich_fields

    def _broken(*_a, **_k):
        raise RuntimeError("tz016_control_removed")

    monkeypatch.setattr("blackdark.timezone.display.format_with_label", _broken)
    with pytest.raises(RuntimeError, match="tz016_control_removed"):
        enrich_fields({"created_at": "2026-03-08T12:00:00Z"}, "UTC", "created_at")


# --- TZ-017 charts ---


def test_chart_config_explicit_display_timezone():
    cfg = chart_config("Europe/London")
    assert cfg["display_timezone"] == "Europe/London"
    assert cfg["mixing_forbidden"] is True
    assert cfg["axis_policy"] == "single_explicit_zone"


def test_market_klines_includes_chart_config():
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient

    from dashboard import app

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[[1_700_000_000_000, "1", "2", "0.5", "1.5", "10"]])
    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.get.return_value = mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    client = TestClient(app)
    with patch("api.routers.market.aiohttp.ClientSession", return_value=mock_session):
        res = client.get("/api/market/klines?symbol=BTC&interval=1h&limit=5")
    assert res.status_code == 200
    payload = res.json()
    assert "chart" in payload
    assert payload["chart"]["display_timezone"]


# --- TZ-019 AI outputs ---


def test_format_ai_output_uses_user_timezone():
    row = format_ai_output("2026-06-15T18:00:00Z", "Asia/Tokyo")
    assert row["timezone"] == "Asia/Tokyo"
    assert row["label"]
    assert "utc_label" in row


def test_timestamp_human_wires_format_ai_output(monkeypatch):
    from market_context import timestamp_human

    def _broken(*_a, **_k):
        raise RuntimeError("tz019_control_removed")

    monkeypatch.setattr("blackdark.timezone.display.format_ai_output", _broken)
    with pytest.raises(RuntimeError, match="tz019_control_removed"):
        timestamp_human(datetime(2026, 1, 1, tzinfo=UTC), user_timezone="America/Chicago")


# --- TZ-020 notifications ---


def test_in_app_alerts_localizes_created_at():
    from in_app_alerts import list_in_app_alerts, push_in_app_alert

    push_in_app_alert("test", "body", level="info")
    rows = list_in_app_alerts(user_timezone="America/Denver")
    assert rows
    assert rows[0].get("created_at_display")
    assert rows[0].get("display_timezone") == "America/Denver"


def test_tz020_control_removal_fails(monkeypatch):
    from in_app_alerts import list_in_app_alerts, push_in_app_alert

    push_in_app_alert("tz020", "body", level="info")

    def _broken(*_a, **_k):
        raise RuntimeError("tz020_control_removed")

    monkeypatch.setattr("blackdark.timezone.display.format_notification", _broken)
    with pytest.raises(RuntimeError, match="tz020_control_removed"):
        list_in_app_alerts(user_timezone="UTC")


# --- TZ-021 email ---


def test_format_email_localizes_time():
    line = format_email("2026-01-15T12:00:00Z", "Europe/Berlin", locale="de")
    assert line
    assert "Europe/Berlin" in line


def test_alert_service_email_localizes(monkeypatch):
    from alert_service import _localize_alert_body

    def _broken(*_a, **_k):
        raise RuntimeError("tz021_control_removed")

    monkeypatch.setattr("blackdark.timezone.display.format_email", _broken)
    with pytest.raises(RuntimeError, match="tz021_control_removed"):
        _localize_alert_body("hello", user_timezone="America/New_York")


# --- TZ-022 exports ---


def test_export_metadata_contract():
    meta = export_metadata("America/Los_Angeles")
    assert meta["canonical_storage"] == "UTC"
    assert meta["display_timezone"] == "America/Los_Angeles"
    assert meta["generated_at_utc"].endswith("Z")


def test_weekly_report_markdown_includes_timezone_metadata():
    from weekly_report import report_to_markdown

    md = report_to_markdown(
        {"generated_at": "2026-02-01T00:00:00Z", "narrative": "n", "highlights": []},
        display_timezone="America/New_York",
    )
    assert "Display timezone: America/New_York" in md
    assert "Generated (UTC):" in md


# --- TZ-025 recurring schedules ---


def test_recurring_schedule_iana_and_wall_clock():
    sched = register_schedule(
        RecurringSchedule(
            schedule_id="daily-brief",
            iana_zone="America/New_York",
            wall_clock_rule="0 9 * * 1-5",
            label="Weekday 9am ET",
        )
    )
    assert sched.iana_zone == "America/New_York"
    assert sched.wall_clock_rule == "0 9 * * 1-5"


def test_timezone_schedules_api():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    res = client.post(
        "/api/timezone/schedules",
        json={
            "schedule_id": "api-test",
            "iana_zone": "Europe/Paris",
            "wall_clock_rule": "30 8 * * *",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["iana_zone"] == "Europe/Paris"


# --- TZ-030 cross-surface ---


def test_cross_surface_registry_covers_required_surfaces():
    status = cross_surface_status()
    surfaces = set(status["surfaces"])
    for required in ("charts", "heroes", "alerts", "email", "notifications", "billing"):
        assert required in surfaces


def test_cross_surface_api():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/timezone/cross-surface")
    assert res.status_code == 200
    assert res.json()["count"] >= 8


# --- TZ-003 session detection persist ---


def test_timezone_session_endpoint_accepts_browser_zone():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    res = client.post(
        "/api/timezone/session",
        json={"timezone": "Africa/Cairo", "detected_browser": "Africa/Cairo"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["timezone"] == "Africa/Cairo"
    assert body["suggestion_only"] is True


# --- TZ-005 / TZ-006 profile persistence ---


@pytest.mark.asyncio
async def test_profile_timezone_save_persists_iana():
    from api.routers.auth import AuthProfileUpdateBody, _profile_update_fields

    user = {"id": 1, "timezone": "UTC", "email": "t@example.com"}
    fields = await _profile_update_fields(
        AuthProfileUpdateBody(timezone="America/Chicago"),
        user,
    )
    assert fields["timezone"] == "America/Chicago"


@pytest.mark.asyncio
async def test_profile_timezone_rejects_invalid_iana():
    from api.routers.auth import AuthProfileUpdateBody, _profile_update_fields

    user = {"id": 1, "timezone": "UTC"}
    with pytest.raises(ValueError, match="invalid_iana_timezone"):
        await _profile_update_fields(AuthProfileUpdateBody(timezone="Not/A_Zone"), user)


# --- TZ-009 / TZ-010 separation ---


def test_language_does_not_determine_timezone():
    tz_en = resolve_timezone_independent_of_lang(
        "ar",
        account_preference="America/New_York",
        detected_browser="Europe/Berlin",
    )
    tz_fr = resolve_timezone_independent_of_lang(
        "fr",
        account_preference="America/New_York",
        detected_browser="Europe/Berlin",
    )
    assert tz_en == tz_fr == "America/New_York"


def test_country_not_sole_timezone_source():
    resolved = resolve_timezone_independent_of_country(
        "US",
        account_preference=None,
        detected_browser="US",
    )
    assert resolved == "UTC"


# --- TZ-014 / TZ-015 display ---


def test_format_for_locale_integrates_i18n():
    row = format_for_locale("2026-04-01T12:00:00Z", "UTC", locale="ar")
    assert row["i18n_integrated"] is True
    assert row["locale"]


# --- TZ-018 ingestion UTC canonical ---


def test_ingestion_paths_use_canonical_utc():
    paths = [
        "decision_ledger.py",
        "signal_registry.py",
        "market_event_library.py",
        "failure_corpus.py",
        "oracle_audit_chain.py",
        "user_exposure_log.py",
    ]
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for rel in paths:
        text = (root / rel).read_text(encoding="utf-8")
        assert "blackdark.timezone" in text, f"{rel} missing canonical timezone import"


# --- TZ-023 activity logs ---


def test_security_events_localizes_for_user():
    from security_events import record_security_event, recent_security_events

    record_security_event("login_success", actor="user@example.com")
    out = recent_security_events(limit=5, user_timezone="America/Phoenix")
    assert out
    assert out[-1].get("iso_display")
    assert out[-1].get("display_timezone") == "America/Phoenix"


# --- TZ-024 billing ---


def test_format_billing_preserves_utc_authority():
    row = format_billing("2026-05-01T00:00:00Z", "Europe/London")
    assert row["billing_authority"] == "UTC"
    assert row["label"]


# --- TZ-029 i18n ---


def test_i18n_locale_does_not_change_timezone_field():
    row_de = format_for_locale("2026-01-01T00:00:00Z", "Asia/Singapore", locale="de")
    row_ar = format_for_locale("2026-01-01T00:00:00Z", "Asia/Singapore", locale="ar")
    assert row_de["timezone"] == row_ar["timezone"] == "Asia/Singapore"


# --- TZ-034 privacy ---


def test_timezone_detection_privacy_policy():
    policy = timezone_detection_privacy()
    assert policy["timezone_detection_is_preference_only"] is True
    assert policy["not_identity_proof"] is True


def test_privacy_status_includes_timezone_policy():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/privacy/status")
    assert res.status_code == 200
    body = res.json()
    assert body.get("timezone_detection", {}).get("not_identity_proof") is True
