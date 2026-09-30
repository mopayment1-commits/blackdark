"""Timestamp integrity — UTC-aware source/observed/ingested/processed."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class TimestampBundle:
    source_timestamp: str | None
    observed_at: str
    ingested_at: str
    processed_at: str
    source_to_observed_ms: float | None
    observed_to_ingested_ms: float
    integrity_ok: bool
    issues: tuple[str, ...]


def _parse_ts(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 1e12 else float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def build_timestamps(
    *,
    source_timestamp: Any = None,
    observed_at: float | None = None,
    ingested_at: float | None = None,
) -> TimestampBundle:
    now = time.time()
    obs = observed_at or now
    ing = ingested_at or now
    src = _parse_ts(source_timestamp)
    issues: list[str] = []
    if src and src > now + 60:
        issues.append("future_source_timestamp")
    if src and src < now - 86400 * 365 * 10:
        issues.append("implausible_source_timestamp")
    src_to_obs = (obs - src) * 1000.0 if src else None
    obs_to_ing = (ing - obs) * 1000.0
    if obs_to_ing < 0:
        issues.append("impossible_ordering")
    return TimestampBundle(
        source_timestamp=datetime.fromtimestamp(src, UTC).isoformat() if src else None,
        observed_at=datetime.fromtimestamp(obs, UTC).isoformat(),
        ingested_at=datetime.fromtimestamp(ing, UTC).isoformat(),
        processed_at=datetime.now(UTC).isoformat(),
        source_to_observed_ms=round(src_to_obs, 2) if src_to_obs is not None else None,
        observed_to_ingested_ms=round(obs_to_ing, 2),
        integrity_ok=not issues,
        issues=tuple(issues),
    )


def attach_timestamps(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    bundle = build_timestamps(
        source_timestamp=out.get("source_timestamp") or out.get("as_of"),
        observed_at=_parse_ts(out.get("observed_at")) or _parse_ts(out.get("quote_ts")),
        ingested_at=_parse_ts(out.get("ingested_at")),
    )
    out["timestamps"] = {
        "source_timestamp": bundle.source_timestamp,
        "observed_at": bundle.observed_at,
        "ingested_at": bundle.ingested_at,
        "processed_at": bundle.processed_at,
        "source_to_observed_ms": bundle.source_to_observed_ms,
        "observed_to_ingested_ms": bundle.observed_to_ingested_ms,
        "integrity_ok": bundle.integrity_ok,
        "issues": list(bundle.issues),
    }
    return out
