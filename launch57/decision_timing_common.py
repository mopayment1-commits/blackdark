"""
Launch-57 canonical decision-timing owner for B4 (#2 Oracle + #3 Decision Certificate).

Zero legacy/PARKED runtime dependencies on cap646.evidence_class or decision_certificate.py.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from launch57.evidence_class_common import EvidenceClassAssessment, assess_user_evidence_class
from launch57.temporal_common import (
    TemporalEnvelope,
    attach_temporal_envelope,
    local_render_instant,
    parse_rfc3339,
    to_rfc3339,
    utc_now,
)

METHODOLOGY_VERSION = "launch57-decision-timing-common-1.0"
CERTIFICATE_HASH_VERSION = "launch57-certificate-hash-v1"

_HASH_EXCLUDE = frozenset(
    {
        "watermark",
        "upgrade_cta",
        "tier",
        "share_text",
        "share_urls",
        "export_text",
        "compliance",
        "display",
        "local_render",
        "verify_url",
        "permalink",
        "methodology_version",
        "certificate_hash_version",
    }
)


@dataclass(frozen=True)
class DecisionTimingContext:
    decision_time: str
    issued_at: str
    certificate_timestamp: str
    review_time: str | None = None
    recheck_time: str | None = None
    invalidation_time: str | None = None
    invalidation_event: str | None = None
    display_timezone: str = "UTC"
    local_render_decision_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_time": self.decision_time,
            "issued_at": self.issued_at,
            "certificate_timestamp": self.certificate_timestamp,
            "review_time": self.review_time,
            "recheck_time": self.recheck_time,
            "invalidation_time": self.invalidation_time,
            "invalidation_event": self.invalidation_event,
            "display_timezone": self.display_timezone,
            "local_render_decision_time": self.local_render_decision_time,
            "methodology_version": METHODOLOGY_VERSION,
            "canonical_timezone_policy": "UTC_storage_display_separate",
        }


def _parse_optional_instant(value: Any, *, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    return to_rfc3339(parse_rfc3339(str(value)))


def _validate_not_before(candidate: str | None, decision_time: str, *, field_name: str) -> str | None:
    if candidate is None:
        return None
    if parse_rfc3339(candidate) < parse_rfc3339(decision_time):
        raise ValueError(f"{field_name}_before_decision_time")
    return candidate


def resolve_emission_instant() -> str:
    return to_rfc3339(utc_now())


def build_decision_timing_context(
    payload: dict[str, Any],
    *,
    display_timezone: str | None = None,
    require_authoritative_decision_time: bool = False,
) -> DecisionTimingContext | None:
    """Assemble canonical decision timing from governed payload; fail closed when required."""
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")

    decision_raw = governed.get("decision_time") or payload.get("decision_time")
    if decision_raw is None:
        if require_authoritative_decision_time:
            return None
        decision_raw = resolve_emission_instant()

    decision_time = _parse_optional_instant(decision_raw, field_name="decision_time")
    if decision_time is None:
        return None

    issued_raw = governed.get("issued_at") or payload.get("issued_at") or decision_time
    issued_at = _parse_optional_instant(issued_raw, field_name="issued_at") or decision_time

    cert_raw = governed.get("certificate_timestamp") or payload.get("certificate_timestamp") or issued_at
    certificate_timestamp = _parse_optional_instant(cert_raw, field_name="certificate_timestamp") or issued_at

    review_time = _validate_not_before(
        _parse_optional_instant(governed.get("review_time") or payload.get("review_time"), field_name="review_time"),
        decision_time,
        field_name="review_time",
    )
    recheck_time = _validate_not_before(
        _parse_optional_instant(governed.get("recheck_time") or payload.get("recheck_time"), field_name="recheck_time"),
        decision_time,
        field_name="recheck_time",
    )

    invalidation = governed.get("invalidation") if isinstance(governed.get("invalidation"), dict) else {}
    invalidation_time = _parse_optional_instant(
        invalidation.get("invalidation_time") or governed.get("invalidation_time"),
        field_name="invalidation_time",
    )
    invalidation_event = invalidation.get("invalidation_event") or governed.get("invalidation_event")

    local_render = local_render_instant(parse_rfc3339(decision_time), zone)

    return DecisionTimingContext(
        decision_time=decision_time,
        issued_at=issued_at,
        certificate_timestamp=certificate_timestamp,
        review_time=review_time,
        recheck_time=recheck_time,
        invalidation_time=invalidation_time,
        invalidation_event=str(invalidation_event) if invalidation_event else None,
        display_timezone=zone,
        local_render_decision_time=local_render,
    )


def snapshot_decision_time_evidence_state(
    payload: dict[str, Any],
    *,
    display_timezone: str | None = None,
) -> EvidenceClassAssessment:
    """Decision-time evidence snapshot via canonical #6 owner (B3 trust gate)."""
    return assess_user_evidence_class(payload, display_timezone=display_timezone)


def attach_decision_temporal_envelope(
    body: dict[str, Any],
    timing: DecisionTimingContext,
) -> dict[str, Any]:
    envelope = TemporalEnvelope(
        decision_time=timing.decision_time,
        event_time=timing.decision_time,
        observed_time=timing.issued_at,
        ingested_at=timing.issued_at,
        processed_at=timing.certificate_timestamp,
        updated_at=timing.certificate_timestamp,
    )
    out = attach_temporal_envelope(dict(body), envelope)
    out["decision_timing"] = timing.as_dict()
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_decision_time": timing.local_render_decision_time,
    }
    return out


def compute_certificate_hash(canonical_body: dict[str, Any]) -> str:
    hash_body = {
        k: v
        for k, v in canonical_body.items()
        if k not in _HASH_EXCLUDE and not str(k).startswith("display_")
    }
    raw = json.dumps(hash_body, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_launch57_decision_certificate(
    payload: dict[str, Any],
    *,
    timing: DecisionTimingContext,
    evidence: EvidenceClassAssessment,
) -> dict[str, Any]:
    """Launch-57-local certificate builder with deterministic hash from canonical fields."""
    tier = str(payload.get("tier") or "free").strip().lower()
    is_free = tier in ("", "free")
    watermark = "Free Proof" if is_free else None

    canonical_body = {
        "asset": str(payload.get("symbol") or payload.get("asset") or "").upper(),
        "prediction_id": payload.get("prediction_id"),
        "chain_hash": payload.get("chain_hash") or (payload.get("proof") or {}).get("chain_hash"),
        "decision_action": payload.get("decision_action") or payload.get("verdict"),
        "decision_sentence": payload.get("decision_sentence") or payload.get("oracle"),
        "opportunity_score": payload.get("opportunity_score"),
        "truth_score": (payload.get("net_edge_truth") or {}).get("truth_score"),
        "decision_time": timing.decision_time,
        "issued_at": timing.issued_at,
        "certificate_timestamp": timing.certificate_timestamp,
        "review_time": timing.review_time,
        "recheck_time": timing.recheck_time,
        "invalidation_time": timing.invalidation_time,
        "invalidation_event": timing.invalidation_event,
        "canonical_evidence_class": evidence.canonical_evidence_class,
        "user_facing_evidence_label": evidence.user_facing_label,
        "decision_time_evidence_state": evidence.to_payload(),
        "engine": payload.get("unified_engine") or "launch57_unified_v1",
        "certificate_hash_version": CERTIFICATE_HASH_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
    }

    body = dict(canonical_body)
    body["tier"] = "free" if is_free else tier
    body["watermark"] = watermark
    body["certificate_hash"] = compute_certificate_hash(canonical_body)
    body["owner"] = "launch57.decision_timing_common"
    body["compliance"] = {
        "surface": "decision_certificate",
        "trust_basis": "launch57_evidence_class_common + decision_timing_common",
        "disclaimer": "Not financial advice. Verify claims on the Public Accuracy Ledger.",
    }
    return body


def build_oracle_decision_record(
    payload: dict[str, Any],
    *,
    timing: DecisionTimingContext,
    evidence: EvidenceClassAssessment,
    action: str,
    sentence: str,
) -> dict[str, Any]:
    return {
        "launch_item_id": 2,
        "surface": "single_sentence_oracle",
        "symbol": payload.get("symbol"),
        "success": True,
        "decision_action": action,
        "decision_sentence": sentence,
        "single_sentence_oracle": {
            "action": action,
            "sentence": sentence,
            "shareable": True,
        },
        "hero": "HERO_1_SINGLE_SENTENCE_ORACLE",
        "decision_time_evidence_state": evidence.to_payload(),
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "single_sentence_oracle",
        "binding_source": "launch57_phase2_trust_batch1",
        "b4_decision_timing_owner": "launch57.decision_timing_common",
    }
