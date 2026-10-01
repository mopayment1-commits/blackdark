"""Behavioral coverage for governance.timezone_governance."""

from __future__ import annotations

from datetime import UTC, datetime

from governance.timezone_governance import (
    ensure_utc_aware,
    format_user_facing_timestamp,
    parse_canonical_timestamp,
    resolve_user_timezone,
    timezone_status,
    to_user_local,
    utc_now_iso,
    validate_iana_timezone,
)


def test_utc_and_parse_paths():
    assert "T" in utc_now_iso()
    naive = datetime(2026, 1, 1, 12, 0, 0)
    assert ensure_utc_aware(naive).tzinfo is not None
    assert parse_canonical_timestamp(None) is None
    assert parse_canonical_timestamp("") is None
    assert parse_canonical_timestamp("not-a-date") is None
    parsed = parse_canonical_timestamp("2026-01-01T12:00:00Z")
    assert parsed is not None and parsed.tzinfo is not None


def test_resolve_and_format_user_facing():
    bad = resolve_user_timezone("Not/A/Zone")
    assert bad["fallback_used"] is True
    good = resolve_user_timezone("UTC")
    assert good["timezone"] == "UTC"
    assert validate_iana_timezone("UTC") is True
    out = format_user_facing_timestamp("2026-01-01T12:00:00+00:00", "UTC", lang="en")
    assert out["naive"] is False
    assert out["display"]
    missing = format_user_facing_timestamp("bad", "UTC")
    assert missing["naive"] is True


def test_to_user_local_and_status():
    now = datetime.now(UTC)
    local = to_user_local(now, "America/New_York")
    assert local.tzinfo is not None
    status = timezone_status()
    assert status["canonical_storage"] == "UTC"
    assert status["supported_zones_count"] > 0
