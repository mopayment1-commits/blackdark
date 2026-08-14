"""Independent time-separated Oracle self-grade (not same-tick calibration).

Uses the immutable audit chain's already-resolved predictions. Those outcomes
were recorded after a later market window — they are not a self-label of the
current e2e tick.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def grade_historical_oracle_outcomes(*, min_resolved: int = 1) -> dict[str, Any]:
    """Return independent hit-rate from resolved chain rows (live-only)."""
    try:
        from oracle_track_record import public_track_record

        track = public_track_record()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "independent_of_this_tick": True,
            "reason": type(exc).__name__,
            "resolved_count": 0,
            "learning_self_grade": False,
            "same_tick_withheld": True,
            "proved_at": _utcnow(),
        }
    cum = track.get("cumulative") or {}
    resolved = int(cum.get("resolved_predictions") or 0)
    hit = float(cum.get("hit_rate_percent") or 0)
    ready = resolved >= min_resolved
    return {
        "ok": True,
        "source": "oracle_audit_chain",
        "independent_of_this_tick": True,
        "resolved_count": resolved,
        "hit_rate_percent": hit,
        "partial_rate_percent": cum.get("partial_rate_percent"),
        "hit_definition": cum.get("hit_definition") or "correct_only",
        "metrics_scope": cum.get("metrics_scope") or "live_only",
        "chain_valid": ((track.get("immutable_chain") or {}).get("valid")),
        "learning_self_grade": ready,
        "same_tick_withheld": True,
        "note": (
            "Self-grade uses previously resolved predictions vs later prices. "
            "The current e2e tick is never used as its own actual."
        ),
        "proved_at": _utcnow(),
    }
