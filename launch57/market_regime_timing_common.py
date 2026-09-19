"""
Launch-57 canonical cross-signal timing owner for B7 (#7, #11–#20, #25–#30, #37).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.evidence_class_common import assess_user_evidence_class
from launch57.temporal_common import parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-market-regime-timing-common-1.0"
B7_LAUNCH_NUMBERS: frozenset[int] = frozenset(
    {7, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 37}
)
DEFAULT_HORIZON_SEC = 86_400.0
HORIZON_COMPATIBILITY_RATIO_MAX = 4.0
ALIGNMENT_TOLERANCE_SEC = 300.0


@dataclass(frozen=True)
class SignalTemporalInput:
    signal_id: str
    observed_time: str
    horizon_sec: float
    source: str | None = None
    evidence_class: str | None = None
    user_facing_label: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "observed_time": self.observed_time,
            "horizon_sec": self.horizon_sec,
            "source": self.source,
            "canonical_evidence_class": self.evidence_class,
            "user_facing_evidence_label": self.user_facing_label,
        }


@dataclass(frozen=True)
class CrossSignalTimingAssessment:
    compatible_horizons: bool
    timestamps_aligned: bool
    delayed_vs_live_distinguishable: bool
    temporal_mismatch: bool
    recommended_action: str
    aligned_signals: tuple[SignalTemporalInput, ...]
    horizon_spread_ratio: float | None
    max_skew_sec: float | None
    live_signal_count: int
    delayed_signal_count: int
    sim_signal_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "compatible_horizons": self.compatible_horizons,
            "timestamps_aligned": self.timestamps_aligned,
            "delayed_vs_live_distinguishable": self.delayed_vs_live_distinguishable,
            "temporal_mismatch": self.temporal_mismatch,
            "recommended_action": self.recommended_action,
            "aligned_signals": [s.as_dict() for s in self.aligned_signals],
            "horizon_spread_ratio": self.horizon_spread_ratio,
            "max_skew_sec": self.max_skew_sec,
            "live_signal_count": self.live_signal_count,
            "delayed_signal_count": self.delayed_signal_count,
            "sim_signal_count": self.sim_signal_count,
            "methodology_version": METHODOLOGY_VERSION,
        }


def _parse_instant(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return to_rfc3339(parse_rfc3339(str(value)))


def _horizon_sec(raw: Any) -> float:
    if raw is None:
        return DEFAULT_HORIZON_SEC
    try:
        return max(1.0, float(raw))
    except (TypeError, ValueError):
        return DEFAULT_HORIZON_SEC


def normalize_signal_input(raw: dict[str, Any], *, default_id: str) -> SignalTemporalInput | None:
    observed = _parse_instant(
        raw.get("observed_time")
        or raw.get("event_time")
        or raw.get("source_time")
        or raw.get("timestamp")
        or raw.get("decision_time")
    )
    if observed is None:
        return None
    evidence = assess_user_evidence_class(raw)
    return SignalTemporalInput(
        signal_id=str(raw.get("signal_id") or raw.get("id") or default_id),
        observed_time=observed,
        horizon_sec=_horizon_sec(raw.get("horizon_sec") or raw.get("horizon_seconds")),
        source=raw.get("source"),
        evidence_class=evidence.canonical_evidence_class,
        user_facing_label=evidence.user_facing_label,
    )


def collect_signals_from_context(
    payload: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> list[SignalTemporalInput]:
    signals: list[SignalTemporalInput] = []
    explicit = list(payload.get("signals") or payload.get("cross_signals") or [])
    for idx, raw in enumerate(explicit):
        if isinstance(raw, dict):
            normalized = normalize_signal_input(raw, default_id=f"signal_{idx}")
            if normalized:
                signals.append(normalized)

    if spine:
        spine_signal = {
            "signal_id": "data_spine",
            "observed_time": (spine.get("data_spine") or {}).get("timestamp") or spine.get("timestamp"),
            "horizon_sec": payload.get("horizon_sec") or DEFAULT_HORIZON_SEC,
            "source": (spine.get("data_spine") or {}).get("source") or spine.get("source"),
            "evidence_class": spine.get("evidence_class"),
            "freshness_state": spine.get("freshness_state"),
        }
        normalized = normalize_signal_input(spine_signal, default_id="data_spine")
        if normalized:
            signals.append(normalized)

    if body and not signals:
        fallback = {
            "signal_id": str(body.get("surface") or "primary"),
            "observed_time": to_rfc3339(utc_now()),
            "horizon_sec": payload.get("horizon_sec") or DEFAULT_HORIZON_SEC,
            "source": body.get("source"),
            "freshness_state": body.get("freshness_state"),
        }
        normalized = normalize_signal_input(fallback, default_id="primary")
        if normalized:
            signals.append(normalized)

    return signals


def align_signals_for_comparison(signals: list[SignalTemporalInput]) -> list[SignalTemporalInput]:
    """Return signals sorted by observed_time for canonical cross-signal comparison order."""
    return sorted(signals, key=lambda s: s.observed_time)


def assess_cross_signal_timing(
    payload: dict[str, Any],
    signals: list[SignalTemporalInput],
) -> CrossSignalTimingAssessment:
    if not signals:
        return CrossSignalTimingAssessment(
            compatible_horizons=True,
            timestamps_aligned=True,
            delayed_vs_live_distinguishable=True,
            temporal_mismatch=False,
            recommended_action="WAIT",
            aligned_signals=(),
            horizon_spread_ratio=None,
            max_skew_sec=None,
            live_signal_count=0,
            delayed_signal_count=0,
            sim_signal_count=0,
        )

    aligned = align_signals_for_comparison(signals)
    horizons = [s.horizon_sec for s in aligned]
    min_h = min(horizons)
    max_h = max(horizons)
    ratio = max_h / min_h if min_h > 0 else float("inf")
    compatible_horizons = ratio <= HORIZON_COMPATIBILITY_RATIO_MAX

    instants = [parse_rfc3339(s.observed_time) for s in aligned]
    skew_sec = (max(instants) - min(instants)).total_seconds() if len(instants) > 1 else 0.0
    tolerance = float(payload.get("alignment_tolerance_sec") or ALIGNMENT_TOLERANCE_SEC)
    timestamps_aligned = skew_sec <= tolerance

    labels = {s.user_facing_label for s in aligned if s.user_facing_label}
    live_count = sum(1 for s in aligned if s.user_facing_label == "LIVE")
    delayed_count = sum(1 for s in aligned if s.user_facing_label == "DELAYED")
    sim_count = sum(1 for s in aligned if s.user_facing_label == "SIM")
    delayed_vs_live_distinguishable = len(labels) <= 1 or ("LIVE" in labels and "SIM" not in labels)

    mixing_live_sim = "LIVE" in labels and "SIM" in labels
    temporal_mismatch = not compatible_horizons or not timestamps_aligned or mixing_live_sim

    if temporal_mismatch:
        recommended = "ABSTAIN" if mixing_live_sim or not compatible_horizons else "WAIT"
    else:
        recommended = "ACT"

    return CrossSignalTimingAssessment(
        compatible_horizons=compatible_horizons,
        timestamps_aligned=timestamps_aligned,
        delayed_vs_live_distinguishable=delayed_vs_live_distinguishable,
        temporal_mismatch=temporal_mismatch,
        recommended_action=recommended,
        aligned_signals=tuple(aligned),
        horizon_spread_ratio=round(ratio, 4) if ratio != float("inf") else None,
        max_skew_sec=round(skew_sec, 3),
        live_signal_count=live_count,
        delayed_signal_count=delayed_count,
        sim_signal_count=sim_count,
    )
