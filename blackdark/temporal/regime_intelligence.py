"""Regime Intelligence Library (P3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

UNKNOWN_REGIME_FORCED_CLASSIFICATION = 0
RETROSPECTIVE_REGIME_LABEL_AS_FORWARD_TRUTH = 0
REGIME_LOOKAHEAD_LEAKAGE = 0
REGIME_CONTEXT_CONTAMINATION = 0

REGIME_CONTRACT_VERSION = "p3.0.0"


class KnownRegimeLabel(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    RANGE_BOUND = "range-bound"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    LIQUIDITY_STRESS = "liquidity_stress"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    DEPEG = "depeg"
    MARKET_WIDE_CRASH = "market_wide_crash"
    IDIOSYNCRATIC_ASSET_SHOCK = "idiosyncratic_asset_shock"
    EXCHANGE_OUTAGE = "exchange_outage"
    MACRO_SHOCK = "macro_shock"
    NEWS_SHOCK = "news_shock"
    CORRELATION_BREAK = "correlation_break"
    STRUCTURAL_BREAK = "structural_break"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RegimeContext:
    """Canonical regime context with temporal correctness."""

    regime_id_or_label: str
    classification_basis: str | None
    effective_interval: Mapping[str, str] | None
    observation_time: datetime | None
    available_at: datetime | None
    confidence_or_quality: float | None
    source_or_derivation: str | None
    version: str
    unknown_or_unclassified_state: bool
    retrospective_analysis: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "regime_id_or_label": self.regime_id_or_label,
            "classification_basis": self.classification_basis,
            "effective_interval": dict(self.effective_interval or {}),
            "observation_time": self.observation_time.isoformat() if self.observation_time else None,
            "available_at": self.available_at.isoformat() if self.available_at else None,
            "confidence_or_quality": self.confidence_or_quality,
            "source_or_derivation": self.source_or_derivation,
            "version": self.version,
            "unknown_or_unclassified_state": self.unknown_or_unclassified_state,
            "retrospective_analysis": self.retrospective_analysis,
        }


@dataclass(frozen=True, slots=True)
class RegimeSegmentEvaluation:
    regime_context: RegimeContext
    metrics: Mapping[str, Any]
    sample_count: int

    def to_metadata(self) -> dict[str, Any]:
        return {
            "regime_context": self.regime_context.to_metadata(),
            "metrics": dict(self.metrics),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True, slots=True)
class RegimeDecomposedEvaluation:
    overall_metrics: Mapping[str, Any]
    regime_segments: tuple[RegimeSegmentEvaluation, ...]
    unknown_regime_metrics: Mapping[str, Any]
    aggregate_hides_regime_failure: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "overall_metrics": dict(self.overall_metrics),
            "regime_segments": [s.to_metadata() for s in self.regime_segments],
            "unknown_regime_metrics": dict(self.unknown_regime_metrics),
            "aggregate_hides_regime_failure": self.aggregate_hides_regime_failure,
        }


def classify_regime(
    *,
    observation_time: datetime,
    available_at: datetime,
    evaluation_time: datetime,
    indicators: Mapping[str, Any],
    version: str = "regime-v1",
    retrospective: bool = False,
) -> RegimeContext:
    """Classify regime with PIT correctness — unknown if not legitimately knowable."""
    if available_at > evaluation_time:
        return RegimeContext(
            regime_id_or_label=KnownRegimeLabel.UNKNOWN.value,
            classification_basis=None,
            effective_interval=None,
            observation_time=observation_time,
            available_at=available_at,
            confidence_or_quality=None,
            source_or_derivation=None,
            version=version,
            unknown_or_unclassified_state=True,
            retrospective_analysis=retrospective,
        )

    volatility = indicators.get("volatility")
    trend = indicators.get("trend")
    if volatility is None and trend is None:
        return RegimeContext(
            regime_id_or_label=KnownRegimeLabel.UNKNOWN.value,
            classification_basis="insufficient_indicators",
            effective_interval=None,
            observation_time=observation_time,
            available_at=available_at,
            confidence_or_quality=None,
            source_or_derivation="regime_classifier",
            version=version,
            unknown_or_unclassified_state=True,
            retrospective_analysis=retrospective,
        )

    label = KnownRegimeLabel.RANGE_BOUND.value
    confidence = 0.5
    if trend == "up":
        label = KnownRegimeLabel.BULL.value
        confidence = 0.7
    elif trend == "down":
        label = KnownRegimeLabel.BEAR.value
        confidence = 0.7
    if volatility == "high":
        label = KnownRegimeLabel.HIGH_VOLATILITY.value
        confidence = 0.75
    elif volatility == "low":
        label = KnownRegimeLabel.LOW_VOLATILITY.value
        confidence = 0.75
    if indicators.get("liquidity_stress"):
        label = KnownRegimeLabel.LIQUIDITY_STRESS.value
    if indicators.get("depeg"):
        label = KnownRegimeLabel.DEPEG.value
    if indicators.get("exchange_outage"):
        label = KnownRegimeLabel.EXCHANGE_OUTAGE.value
    if indicators.get("macro_shock"):
        label = KnownRegimeLabel.MACRO_SHOCK.value
    if indicators.get("correlation_break"):
        label = KnownRegimeLabel.CORRELATION_BREAK.value
    if indicators.get("structural_break"):
        label = KnownRegimeLabel.STRUCTURAL_BREAK.value

    return RegimeContext(
        regime_id_or_label=label,
        classification_basis=str(indicators),
        effective_interval={
            "start": observation_time.isoformat(),
            "end": evaluation_time.isoformat(),
        },
        observation_time=observation_time,
        available_at=available_at,
        confidence_or_quality=confidence,
        source_or_derivation="regime_classifier",
        version=version,
        unknown_or_unclassified_state=False,
        retrospective_analysis=retrospective,
    )


def evaluate_by_regime(
    observations: Sequence[Mapping[str, Any]],
) -> RegimeDecomposedEvaluation:
    """TEMP-AR-0165, 0166: decompose evaluation by regime without hiding failures."""
    by_regime: dict[str, list[Mapping[str, Any]]] = {}
    unknown: list[Mapping[str, Any]] = []

    for obs in observations:
        regime = obs.get("regime_context")
        if regime is None or regime.get("unknown_or_unclassified_state"):
            unknown.append(obs)
            continue
        label = regime.get("regime_id_or_label", KnownRegimeLabel.UNKNOWN.value)
        by_regime.setdefault(label, []).append(obs)

    segments: list[RegimeSegmentEvaluation] = []
    regime_failures: list[bool] = []
    for label, items in sorted(by_regime.items()):
        success_rate = sum(1 for i in items if i.get("success")) / len(items) if items else 0.0
        metrics = {"success_rate": success_rate, "count": len(items)}
        regime_failures.append(success_rate < 0.5 and len(items) >= 2)
        ctx = RegimeContext(
            regime_id_or_label=label,
            classification_basis="aggregated",
            effective_interval=None,
            observation_time=None,
            available_at=None,
            confidence_or_quality=None,
            source_or_derivation="evaluation",
            version=REGIME_CONTRACT_VERSION,
            unknown_or_unclassified_state=False,
        )
        segments.append(RegimeSegmentEvaluation(regime_context=ctx, metrics=metrics, sample_count=len(items)))

    overall_success = (
        sum(1 for o in observations if o.get("success")) / len(observations) if observations else 0.0
    )
    aggregate_hides = overall_success >= 0.7 and any(regime_failures)

    return RegimeDecomposedEvaluation(
        overall_metrics={"success_rate": overall_success, "count": len(observations)},
        regime_segments=tuple(segments),
        unknown_regime_metrics={"count": len(unknown)},
        aggregate_hides_regime_failure=aggregate_hides,
    )
