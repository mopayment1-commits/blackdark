"""Independent time-separated Oracle self-grade (not same-tick calibration).

Pairs prediction_created → prediction_resolved on the immutable chain.
A pair counts only when resolve timestamp is strictly later than create.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

MIN_INDEPENDENT_SECONDS = 60


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_chain_rows() -> list[dict[str, Any]]:
    from oracle_track_record import _read_all_records

    return _read_all_records()


def _pair_independent_outcomes(
    rows: list[dict[str, Any]],
    *,
    min_delta_seconds: int,
) -> list[dict[str, Any]]:
    from oracle_integrity import is_synthetic_prediction

    created: dict[str, dict[str, Any]] = {}
    resolved: dict[str, dict[str, Any]] = {}
    for row in rows:
        pid = str(row.get("prediction_id") or "")
        if not pid:
            continue
        if is_synthetic_prediction(row):
            continue
        event = str(row.get("event") or "")
        if event == "prediction_created" or (row.get("resolved") is False and "price_at_prediction" in row):
            created[pid] = row
        if event == "prediction_resolved" or row.get("resolved") is True:
            resolved[pid] = row

    pairs: list[dict[str, Any]] = []
    for pid, res in resolved.items():
        cre = created.get(pid)
        t_res = _parse_ts(res.get("timestamp"))
        t_cre = _parse_ts((cre or {}).get("timestamp")) if cre else None
        delta = None
        if t_cre and t_res:
            delta = (t_res - t_cre).total_seconds()
        independent = False
        if delta is not None and delta >= min_delta_seconds:
            independent = True
        elif cre is None and res.get("price_after_24h") not in (None, "", 0, 0.0):
            # Labeling pipeline records a later window even if create row is absent.
            independent = True
            delta = 24 * 3600
        if not independent:
            continue
        label = str(res.get("label") or res.get("outcome") or "").strip().lower()
        pairs.append(
            {
                "prediction_id": pid,
                "asset": res.get("asset"),
                "label": label,
                "delta_seconds": delta,
                "price_at_prediction": res.get("price_at_prediction"),
                "price_after_24h": res.get("price_after_24h"),
            }
        )
    return pairs


def grade_historical_oracle_outcomes(
    *,
    min_resolved: int = 1,
    min_delta_seconds: int = MIN_INDEPENDENT_SECONDS,
) -> dict[str, Any]:
    """Return independent hit-rate from time-separated chain pairs (live-only)."""
    try:
        rows = _read_chain_rows()
        from oracle_audit_chain import verify_chain

        verify = verify_chain()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "independent_of_this_tick": True,
            "reason": type(exc).__name__,
            "resolved_count": 0,
            "independent_pairs": 0,
            "learning_self_grade": False,
            "same_tick_withheld": True,
            "min_delta_seconds": min_delta_seconds,
            "proved_at": _utcnow(),
        }

    pairs = _pair_independent_outcomes(rows, min_delta_seconds=min_delta_seconds)
    correct = sum(1 for p in pairs if p.get("label") == "correct")
    hit = round(correct / len(pairs) * 100, 2) if pairs else 0.0
    ready = len(pairs) >= min_resolved
    return {
        "ok": True,
        "source": "oracle_audit_chain_paired",
        "independent_of_this_tick": True,
        "resolved_count": len(pairs),
        "independent_pairs": len(pairs),
        "hit_rate_percent": hit,
        "hit_definition": "correct_only",
        "metrics_scope": "live_only_time_separated",
        "chain_valid": bool(verify.get("valid")),
        "min_delta_seconds": min_delta_seconds,
        "sample": pairs[:8],
        "learning_self_grade": ready,
        "same_tick_withheld": True,
        "note": (
            "Self-grade pairs create→resolve with a later timestamp. "
            "The current e2e tick is never used as its own actual."
        ),
        "proved_at": _utcnow(),
    }
