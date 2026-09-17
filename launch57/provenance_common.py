"""
Launch-57 canonical #40 data quality & provenance owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from launch57.temporal_common import (
    AvailabilityState,
    TemporalEnvelope,
    attach_temporal_envelope,
    build_market_temporal_envelope,
    to_rfc3339,
    utc_now,
    validate_provider_timestamp,
)


class QualityState(str, Enum):
    DECISION_GRADE = "decision_grade"
    CAUTION = "caution"
    DEGRADED = "degraded"
    INSUFFICIENT = "insufficient"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProvenanceRecord:
    symbol: str
    source_authority: str | None
    lineage: list[str]
    quality_state: QualityState
    quality_score: float | None
    observed_at: str
    source_time: str | None
    availability_state: AvailabilityState
    timestamp_unit: str | None
    posture: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "source_authority": self.source_authority,
            "lineage": self.lineage,
            "quality_state": self.quality_state.value,
            "quality_score": self.quality_score,
            "band": self.quality_state.value,
            "observed_at": self.observed_at,
            "source_time": self.source_time,
            "availability_state": self.availability_state.value,
            "timestamp_unit": self.timestamp_unit,
            "posture": self.posture,
            "unknown_is_not_zero": True,
        }


def _lineage_from_params(params: dict[str, Any]) -> list[str]:
    explicit = params.get("lineage")
    if isinstance(explicit, list) and explicit:
        return [str(x) for x in explicit]
    source = params.get("source_authority") or params.get("source")
    if source:
        return ["launch57.provenance_common", f"source:{source}"]
    return ["launch57.provenance_common", "source:unknown"]


def build_provenance_record(
    *,
    symbol: str,
    params: dict[str, Any] | None = None,
) -> tuple[ProvenanceRecord, TemporalEnvelope]:
    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    source_raw = params.get("source_time")
    source_validation = validate_provider_timestamp(source_raw) if source_raw is not None else None
    if source_raw is not None and source_validation and not source_validation.ok:
        raise ValueError(f"provider_timestamp_invalid:{source_validation.error}")

    observed = utc_now()
    lineage = _lineage_from_params(params)
    source_authority = params.get("source_authority") or params.get("source")
    explicit_quality = params.get("quality_state")
    explicit_score = params.get("quality_score")

    if explicit_quality in {s.value for s in QualityState}:
        quality_state = QualityState(explicit_quality)
    elif source_authority and source_validation and source_validation.ok:
        quality_state = QualityState.DECISION_GRADE
    elif source_authority:
        quality_state = QualityState.CAUTION
    else:
        quality_state = QualityState.UNKNOWN

    if quality_state == QualityState.UNKNOWN:
        quality_score = None
    else:
        quality_score = float(explicit_score) if explicit_score is not None else (
            85.0 if quality_state == QualityState.DECISION_GRADE else 60.0 if quality_state == QualityState.CAUTION else None
        )

    envelope = build_market_temporal_envelope(
        source_raw=source_raw,
        source_unit=source_validation.unit if source_validation else None,
        observed_at=observed,
        ingested_at=observed,
        processed_at=observed,
    )
    record = ProvenanceRecord(
        symbol=asset,
        source_authority=str(source_authority) if source_authority else None,
        lineage=lineage,
        quality_state=quality_state,
        quality_score=quality_score,
        observed_at=to_rfc3339(observed),
        source_time=to_rfc3339(source_validation.canonical) if source_validation and source_validation.canonical else None,
        availability_state=envelope.availability_state,
        timestamp_unit=envelope.timestamp_unit,
        posture="verified_local" if quality_state == QualityState.DECISION_GRADE else "degraded_or_unknown",
    )
    return record, envelope


def attach_provenance_payload(body: dict[str, Any], record: ProvenanceRecord, envelope: TemporalEnvelope) -> dict[str, Any]:
    out = dict(body)
    prov = record.as_dict()
    out["provenance"] = prov
    out["data_provenance"] = prov
    out["quality_state"] = prov["quality_state"]
    out["user_disclosure"] = {
        "question": "من أين الرقم؟",
        "band": prov.get("band"),
        "posture": prov.get("posture"),
        "score": prov.get("quality_score"),
        "lineage": prov.get("lineage"),
        "availability_state": prov.get("availability_state"),
        "unknown_is_not_zero": True,
    }
    out["observed_at"] = prov["observed_at"]
    return attach_temporal_envelope(out, envelope)


def normalization_report_from_provenance(record: ProvenanceRecord, envelope: TemporalEnvelope) -> dict[str, Any]:
    prov = record.as_dict()
    success = record.quality_state not in {QualityState.INSUFFICIENT, QualityState.UNKNOWN}
    return attach_provenance_payload(
        {
            "schema_version": "launch57_provenance_v1",
            "symbol": record.symbol,
            "success": success,
            "normalization_policy": "launch57_local_no_legacy_delegate",
        },
        record,
        envelope,
    )
