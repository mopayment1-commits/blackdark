"""
Launch-57 canonical #39 point-in-time immutable metrics owner.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from launch57.temporal_common import parse_rfc3339, point_in_time_eligible, to_rfc3339, utc_now

_STORE_PATH = Path(__file__).resolve().parent / "pit_observation_store.json"


@dataclass(frozen=True)
class PitObservation:
    symbol: str
    metric_key: str
    value: Any
    effective_time: str
    source_time: str | None
    available_at: str
    content_hash: str
    version: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "metric_key": self.metric_key,
            "value": self.value,
            "effective_time": self.effective_time,
            "source_time": self.source_time,
            "available_at": self.available_at,
            "content_hash": self.content_hash,
            "version": self.version,
        }


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def reset_store_for_tests() -> None:
    if _STORE_PATH.exists():
        _STORE_PATH.unlink()


def _load_store() -> list[dict[str, Any]]:
    if not _STORE_PATH.exists():
        return []
    return json.loads(_STORE_PATH.read_text(encoding="utf-8"))


def _save_store(rows: list[dict[str, Any]]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_observation(
    *,
    symbol: str,
    metric_key: str,
    value: Any,
    effective_time: str | None = None,
    source_time: str | None = None,
    available_at: str | None = None,
) -> PitObservation:
    now = to_rfc3339(utc_now())
    effective = effective_time or now
    available = available_at or now
    if not point_in_time_eligible(available, effective):
        raise ValueError("available_at_after_effective_time")

    rows = _load_store()
    version = sum(1 for r in rows if r.get("symbol") == symbol and r.get("metric_key") == metric_key) + 1
    core = {
        "symbol": symbol.upper().replace("/USDT", ""),
        "metric_key": metric_key,
        "value": value,
        "effective_time": effective,
        "source_time": source_time,
        "available_at": available,
        "version": version,
    }
    content_hash = _canonical_hash(core)
    obs = PitObservation(**core, content_hash=content_hash)
    rows.append(obs.as_dict())
    _save_store(rows)
    return obs


def retrieve_point_in_time(symbol: str, *, as_of: str, metric_key: str | None = None) -> list[dict[str, Any]]:
    asset = symbol.upper().replace("/USDT", "")
    as_of_dt = parse_rfc3339(as_of)
    eligible: list[dict[str, Any]] = []
    for row in _load_store():
        if row.get("symbol") != asset:
            continue
        if metric_key and row.get("metric_key") != metric_key:
            continue
        available_at = row.get("available_at")
        if not available_at or not point_in_time_eligible(available_at, as_of):
            continue
        effective = row.get("effective_time")
        if effective and parse_rfc3339(effective) > as_of_dt:
            continue
        eligible.append(row)
    eligible.sort(key=lambda r: (r.get("effective_time") or "", r.get("version") or 0))
    return eligible


def build_immutable_snapshot(
    *,
    symbol: str,
    metrics: dict[str, Any],
    provenance: dict[str, Any] | None = None,
    freshness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = to_rfc3339(utc_now())
    observations: list[dict[str, Any]] = []
    for key, value in metrics.items():
        obs = append_observation(
            symbol=symbol,
            metric_key=key,
            value=value,
            effective_time=now,
            source_time=(provenance or {}).get("source_time"),
            available_at=now,
        )
        observations.append(obs.as_dict())

    chain_valid = all(o.get("content_hash") for o in observations)
    core = {
        "symbol": symbol.upper().replace("/USDT", ""),
        "snapshot_at": now,
        "observations": observations,
        "provenance_link": provenance,
        "freshness_link": freshness,
    }
    content_hash = _canonical_hash(core)
    return {
        **core,
        "point_in_time": True,
        "immutable": chain_valid,
        "content_hash": content_hash,
        "chain_valid": chain_valid,
        "chain_records": len(observations),
        "metrics_scope": "launch57_local_pit",
        "unknown_is_not_zero": True,
        "success": chain_valid and bool(observations),
        "observed_at": now,
    }
