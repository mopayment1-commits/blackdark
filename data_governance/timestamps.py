"""Clock timestamp integrity (DIG-032)."""

from __future__ import annotations

from typing import Any


def ensure_canonical_timestamps(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    try:
        from blackdark.timezone import utc_now_iso

        out.setdefault("created_at", utc_now_iso())
    except Exception:
        from datetime import UTC, datetime

        out.setdefault("created_at", datetime.now(UTC).isoformat())
    out.setdefault("timestamp_canonical", "UTC")
    return out
