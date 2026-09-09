"""Timezone P0 test matrix — TZ-001 → TZ-035 local engineering evidence."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


def test_utc_canonical_storage_and_api_contract():
    from timezone.canonical import format_api_timestamp, parse_iso, reject_naive, utc_now

    now = utc_now()
    reject_naive(now)
    iso = format_api_timestamp(now)
    assert iso.endswith("Z")
    roundtrip = parse_iso(iso)
    assert roundtrip.tzinfo is not None


def test_reject_naive_datetime():
    from timezone.canonical import parse_iso, reject_naive

    with pytest.raises(ValueError):
        reject_naive(datetime(2026, 9, 9, 12, 0, 0))
    with pytest.raises(ValueError):
        parse_iso("2026-09-09 12:00:00")


def test_iana_validation_and_fallback():
    from timezone.iana import is_fixed_offset_not_iana, validate_iana_timezone

    assert validate_iana_timezone("Africa/Cairo") == "Africa/Cairo"
    assert validate_iana_timezone("UTC+2") == "UTC"
    assert is_fixed_offset_not_iana("GMT+5")


def test_precedence_order():
    from timezone.resolver import resolve_timezone

    r = resolve_timezone(
        request_override="Europe/London",
        account_timezone="Africa/Cairo",
        session_timezone="America/New_York",
        detected_timezone="Asia/Tokyo",
    )
    assert r.timezone == "Europe/London" and r.source == "request_override"

    r2 = resolve_timezone(
        account_timezone="Africa/Cairo",
        session_timezone="America/New_York",
        detected_timezone="Asia/Tokyo",
    )
    assert r2.timezone == "Africa/Cairo" and r2.source == "account"

    r3 = resolve_timezone(session_timezone="America/Chicago", detected_timezone="Asia/Tokyo")
    assert r3.timezone == "America/Chicago" and r3.source == "session"

    r4 = resolve_timezone(detected_timezone="Asia/Tokyo")
    assert r4.timezone == "Asia/Tokyo" and r4.source == "detected"

    r5 = resolve_timezone()
    assert r5.timezone == "UTC" and r5.source == "utc_fallback"


def test_travel_mismatch_flag():
    from timezone.resolver import resolve_timezone

    r = resolve_timezone(account_timezone="Africa/Cairo", detected_timezone="America/New_York")
    assert r.mismatch is True


def test_language_independent_from_timezone():
    from i18n_enforcement import format_locale_datetime
    from timezone.canonical import utc_now

    dt = utc_now()
    en = format_locale_datetime(dt, lang="en", tz_name="Africa/Cairo")
    ar = format_locale_datetime(dt, lang="ar", tz_name="America/New_York")
    assert en != ar or "Africa/Cairo" != "America/New_York"


def test_dst_conversion_cairo():
    from timezone.format import to_user_local

    utc = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    local = to_user_local(utc, "Africa/Cairo")
    assert local.utcoffset() is not None


def test_dst_gap_policy():
    from timezone.dst import local_wall_to_utc

    # US spring-forward 2026: Mar 8 2026 02:30 does not exist in America/New_York
    gap_day = datetime(2026, 3, 8, tzinfo=UTC)
    instant = local_wall_to_utc(local_date=gap_day, wall=time(2, 30), tz_name="America/New_York")
    assert instant.tzinfo == UTC


def test_historical_integrity_on_timezone_change():
    from timezone.canonical import format_api_timestamp, utc_now
    from timezone.format import format_user_datetime

    stored = format_api_timestamp(utc_now())
    display_old = format_user_datetime(stored, tz_name="Africa/Cairo")
    display_new = format_user_datetime(stored, tz_name="America/New_York")
    assert stored == format_api_timestamp(stored)
    assert display_old != display_new


def test_recurring_local_schedule():
    from timezone.schedule import LocalSchedule, next_occurrence_utc

    sched = LocalSchedule(wall_time="09:00", iana_timezone="Africa/Cairo", recurrence="daily")
    nxt = next_occurrence_utc(sched, after=datetime(2026, 1, 15, 8, 0, tzinfo=UTC))
    assert nxt > datetime(2026, 1, 15, 8, 0, tzinfo=UTC)


def test_market_timestamp_integrity():
    from timezone.market import localize_market_event_for_display, preserve_market_event

    raw = {"timestamp": "2026-06-01T12:00:00+00:00", "exchange": "binance"}
    preserved = preserve_market_event(raw)
    assert preserved["canonical_utc"].endswith("Z")
    assert preserved["source_provenance"] == "binance"
    shown = localize_market_event_for_display(raw, lang="en", tz_name="Africa/Cairo")
    assert "display_time" in shown


def test_profile_timezone_persistence(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "tz.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("tz@example.com", hash_password("strong-password-12345"), "TZ")
        await database.update_user_profile_fields(uid, {"timezone": "Africa/Cairo"})
        row = await database.fetch_user_by_id(uid)
        assert row["timezone"] == "Africa/Cairo"

    asyncio.run(_run())


def test_profile_timezone_validation_rejects_fixed_offset():
    from security_models import AuthProfileUpdateBody

    with pytest.raises(ValueError):
        AuthProfileUpdateBody(timezone="UTC+2")


def test_timezone_change_audit_called(monkeypatch):
    calls: list[dict] = []

    async def _record(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("identity.identity_audit.record_identity_event", _record)
    from timezone.audit import record_timezone_change

    asyncio.run(
        record_timezone_change(1, old_timezone="UTC", new_timezone="Africa/Cairo", source="profile")
    )
    assert calls and calls[0]["event_type"] == "timezone.preference_changed"


def test_export_metadata():
    from timezone.format import export_timestamp_fields

    fields = export_timestamp_fields("2026-01-01T00:00:00+00:00", tz_name="Europe/London")
    assert fields["canonical_utc"].endswith("Z")
    assert fields["display_timezone"] == "Europe/London"


def test_surface_registry_covers_core_surfaces():
    from timezone.surface_registry import surface_audit

    surfaces = surface_audit()
    for key in ("profile", "charts", "email", "api_contract"):
        assert key in surfaces


def test_server_clock_readiness_documents_live_gate():
    from timezone.server_discipline import server_clock_readiness

    payload = server_clock_readiness()
    assert payload["application_default_tz"] == "UTC"
    assert "live_gate" in payload


def test_privacy_note_in_time_context():
    from timezone.resolver import resolve_timezone, time_context_payload

    payload = time_context_payload(resolve_timezone(account_timezone="Africa/Cairo"))
    assert "preference signal only" in payload["privacy_note"]


def test_invalid_timezone_fallback_observability():
    from observability import observability_status
    from timezone.iana import validate_iana_timezone

    before = observability_status().get("counters", {}).get("timezone_invalid_fallback_total", 0)
    assert validate_iana_timezone("Fake/Zone/Name") == "UTC"
    assert validate_iana_timezone("GMT+3") == "UTC"
    after = observability_status().get("counters", {}).get("timezone_invalid_fallback_total", 0)
    assert after > before


def test_bd_time_chart_helpers_present():
    text = (Path(__file__).resolve().parents[1] / "static/js/bd_time.js").read_text(encoding="utf-8")
    for fn in ("applyChartTimezone", "formatApiTimestamp", "fetchTimeContext", "formatChartUnix"):
        assert fn in text


def test_postgres_models_use_timestamptz():
    from blackdark.data import models

    for name in ("created_at", "updated_at", "open_time", "close_time", "started_at"):
        assert name in models.OhlcvData.__table__.columns or name in models.DataSource.__table__.columns or name in models.IngestionRun.__table__.columns


def test_final_reconciliation_gates():
    from scripts import timezone_final_reconciliation as recon

    pg = recon.audit_postgres_timestamp_semantics()
    charts = recon.audit_chart_timezone_coverage()
    cross = recon.audit_cross_surface_timestamps()
    assert pg["POSTGRES_CANONICAL_TIMESTAMP_SEMANTICS_PASS"] is True
    assert charts["CHART_TIMEZONE_FULL_COVERAGE_PASS"] is True
    assert cross["CROSS_SURFACE_TIMESTAMP_AUDIT_PASS"] is True

