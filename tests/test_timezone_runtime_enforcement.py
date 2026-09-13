"""Runtime timezone enforcement — UTC canon, IANA, DST, audit (T2)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from blackdark.timezone import (
    DstResolution,
    TimePolicyViolation,
    audit_timezone_change,
    ensure_aware_utc,
    format_iso_z,
    parse_to_utc,
    persist_timezone_audit,
    resolve_local_to_utc,
    resolve_timezone,
    safe_timezone,
    time_enforce_enabled,
    to_display_tz,
    utc_now,
    utc_now_iso,
    validate_iana_timezone,
)
from zoneinfo import available_timezones


def test_time_enforce_default_on():
    assert time_enforce_enabled() is True


def test_time_enforce_cannot_disable_in_production(monkeypatch):
    monkeypatch.setenv("BLACKDARK_TIME_ENFORCE", "0")
    monkeypatch.setenv("APP_ENV", "production")
    assert time_enforce_enabled() is True


def test_utc_now_is_aware():
    assert utc_now().tzinfo is not None


def test_format_iso_z_uses_z_suffix():
    dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    assert format_iso_z(dt).endswith("Z")


def test_ensure_aware_utc_rejects_naive_when_enforced(monkeypatch):
    monkeypatch.setenv("BLACKDARK_TIME_ENFORCE", "1")
    with pytest.raises(TimePolicyViolation, match="naive"):
        ensure_aware_utc(datetime(2026, 1, 1, 0, 0, 0))


def test_validate_iana_timezone_rejects_invalid():
    assert validate_iana_timezone("America/New_York") is True
    assert validate_iana_timezone("Not/A_Zone") is False


def test_safe_timezone_fallback_invalid():
    assert safe_timezone("Not/A_Zone") == "UTC"
    assert safe_timezone("America/Chicago") == "America/Chicago"


def test_resolve_timezone_precedence():
    resolved = resolve_timezone(
        request_override="Europe/London",
        account_preference="America/New_York",
        session_preference="Asia/Tokyo",
        detected_browser="Africa/Cairo",
    )
    assert resolved == "Europe/London"


def test_resolve_preserves_account_over_detected():
    resolved = resolve_timezone(
        account_preference="America/New_York",
        detected_browser="Europe/Berlin",
    )
    assert resolved == "America/New_York"


def test_dst_conversion_new_york():
    # US spring forward 2026-03-08 — 12:00 UTC → 08:00 EDT
    instant = datetime(2026, 3, 8, 12, 0, 0, tzinfo=UTC)
    local = to_display_tz(instant, "America/New_York")
    assert local.hour == 8
    assert "New_York" in str(local.tzinfo) or local.tzname() in {"EDT", "EST"}


def test_dst_fold_ambiguous_local():
    # Fall back 2026-11-01 01:30 local is ambiguous in America/New_York
    earlier = resolve_local_to_utc(
        datetime(2026, 11, 1, 1, 30, 0),
        "America/New_York",
        dst=DstResolution.EARLIER,
    )
    later = resolve_local_to_utc(
        datetime(2026, 11, 1, 1, 30, 0),
        "America/New_York",
        dst=DstResolution.LATER,
    )
    assert earlier != later
    assert (later - earlier).total_seconds() == 3600


def test_dst_gap_rejected():
    # Spring forward gap 2026-03-08 02:30 does not exist in New York
    with pytest.raises(TimePolicyViolation):
        resolve_local_to_utc(
            datetime(2026, 3, 8, 2, 30, 0),
            "America/New_York",
            dst=DstResolution.REJECT_GAP,
        )


def test_parse_to_utc_epoch_ms_conversion():
    sec = parse_to_utc(1_700_000_000)
    ms = parse_to_utc(1_700_000_000_000)
    assert sec is not None and ms is not None
    assert abs((ms - sec).total_seconds()) < 1


def test_models_use_timezone_aware_columns():
    from blackdark.data.models import DataSource

    col = DataSource.__table__.c.created_at
    assert col.type.timezone is True


def test_decision_ledger_uses_canonical_iso():
    from decision_ledger import _utcnow

    ts = _utcnow()
    assert ts.endswith("Z") or "+" in ts


def test_historical_integrity_unchanged_on_tz_change():
    stored = utc_now_iso()
    instant = parse_to_utc(stored)
    assert instant is not None
    display_ny = to_display_tz(instant, "America/New_York")
    display_uk = to_display_tz(instant, "Europe/London")
    assert parse_to_utc(format_iso_z(display_ny)) == instant
    assert parse_to_utc(format_iso_z(display_uk)) == instant


def test_persist_timezone_audit(tmp_path: Path):
    path = tmp_path / "tz_audit.jsonl"
    row = audit_timezone_change(
        user_id=42,
        old_tz="UTC",
        new_tz="America/Chicago",
        source="test",
    )
    persisted = persist_timezone_audit(row, audit_path=path)
    assert path.is_file()
    loaded = json.loads(path.read_text(encoding="utf-8").strip())
    assert loaded["new_timezone"] == "America/Chicago"
    assert persisted["event"] == "timezone_preference_change"


def test_iana_tzdb_available():
    assert "America/New_York" in available_timezones()
    assert len(available_timezones()) > 400


def test_naive_iso_export_rejected_when_enforced(monkeypatch):
    monkeypatch.setenv("BLACKDARK_TIME_ENFORCE", "1")
    with pytest.raises(TimePolicyViolation):
        format_iso_z(datetime(2026, 1, 1, 0, 0, 0))
