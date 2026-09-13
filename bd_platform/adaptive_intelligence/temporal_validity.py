"""Temporal validity / confidence decay — spec §26 (no Grinold attribution)."""

from __future__ import annotations

from typing import Any


def compute_temporal_validity(
    *,
    observed_at: float,
    horizon_sec: float = 3600.0,
    staleness_sec: float = 0.0,
    calibration_available: bool = False,
) -> dict[str, Any]:
    age = max(0.0, staleness_sec)
    if calibration_available:
        decay = max(0.0, 1.0 - (age / max(horizon_sec, 1.0)))
    else:
        decay = None
    return {
        "observed_at": observed_at,
        "horizon_sec": horizon_sec,
        "staleness_sec": age,
        "calibration_available": calibration_available,
        "decay_factor": decay,
        "next_recheck": "on_stale_or_regime_change" if not calibration_available else f"within_{int(horizon_sec)}s",
        "grinold_attribution": False,
    }
