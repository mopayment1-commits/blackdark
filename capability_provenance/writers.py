"""Single-writer contract for capability provenance fields (B1-R)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from capability_provenance.contract import INCOMPLETE_VERDICTS, load_contract


class ProvenanceWriteError(ValueError):
    """Raised when a provenance write violates the B1-R contract."""


@dataclass(frozen=True, slots=True)
class VerificationEvent:
    """Documented capability verification executed at source_sha."""

    event_type: str
    source_sha: str
    verification: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    executed_at: str | None = None

    def __post_init__(self) -> None:
        if len(self.source_sha) != 40:
            raise ProvenanceWriteError("source_sha must be a 40-character git commit SHA")
        if not self.evidence_refs:
            raise ProvenanceWriteError("evidence_refs must be non-empty")
        if not self.verification:
            raise ProvenanceWriteError("verification payload must be non-empty")
        verdict = str(self.verification.get("verdict") or "")
        if verdict in INCOMPLETE_VERDICTS:
            raise ProvenanceWriteError(f"verification verdict {verdict!r} cannot stamp tested_source_sha")


def _validate_event(event: VerificationEvent) -> None:
    contract = load_contract()
    allowed_types = {
        entry["event_type"]
        for entry in contract["writer_matrix"]
        if entry["field"] == "tested_source_sha"
    }
    if "ACTUAL_VERIFICATION" not in allowed_types:
        raise ProvenanceWriteError("contract missing ACTUAL_VERIFICATION writer matrix entry")


def record_verification_event(
    cap: dict[str, Any],
    event: VerificationEvent,
    *,
    status_change_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write actual verification provenance and bound status-change metadata."""
    _validate_event(event)
    executed_at = event.executed_at or datetime.now(UTC).isoformat()

    cap["tested_source_sha"] = event.source_sha
    cap["last_verified_at"] = executed_at

    status_change = {
        "tested_sha": event.source_sha,
        "timestamp": executed_at,
        "verification": dict(event.verification),
        "evidence": list(event.evidence_refs),
        "provenance_event_type": event.event_type,
        "provenance_contract_version": load_contract()["contract_version"],
    }
    if status_change_extra:
        status_change.update(status_change_extra)
    cap["status_change"] = status_change
    return cap


def record_artifact_composition(ssot: dict[str, Any], head_sha: str, generated_at: str | None = None) -> dict[str, Any]:
    """Update artifact-scope composition provenance only; never touch per-cap tested_source_sha."""
    if len(head_sha) != 40:
        raise ProvenanceWriteError("head_sha must be a 40-character git commit SHA")
    ssot.setdefault("git", {})
    ssot["git"]["current_head_sha"] = head_sha
    ssot["generated_at"] = generated_at or datetime.now(UTC).isoformat()
    ssot.setdefault("provenance_contract", {})
    ssot["provenance_contract"]["contract_version"] = load_contract()["contract_version"]
    ssot["provenance_contract"]["artifact_composition_head_sha"] = head_sha
    return ssot


def record_semantic_correction(
    cap: dict[str, Any],
    *,
    head_sha: str,
    prior_artifact_sha: str,
    provenance: str,
    corrected_at: str | None = None,
) -> dict[str, Any]:
    """Artifact-only metadata correction; must not mutate tested_source_sha."""
    cap["semantic_correction"] = {
        "corrected_at": corrected_at or datetime.now(UTC).isoformat(),
        "head_sha": head_sha,
        "prior_artifact_sha": prior_artifact_sha,
        "provenance": provenance,
        "provenance_contract_version": load_contract()["contract_version"],
    }
    return cap


def record_live_applicability_correction(
    cap: dict[str, Any],
    *,
    head_sha: str,
    previous_live_status: str,
    new_live_status: str,
    reason: str,
) -> dict[str, Any]:
    """Live applicability dimension correction; must not mutate tested_source_sha."""
    cap.setdefault("status_change", {})
    cap["status_change"]["live_applicability_correction"] = {
        "previous_live_status": previous_live_status,
        "new_live_status": new_live_status,
        "reason": reason,
        "composition_head_sha": head_sha,
        "provenance_contract_version": load_contract()["contract_version"],
    }
    return cap


def forbid_tested_source_sha_assignment(cap: dict[str, Any], operation: str) -> None:
    """Guard helper for artifact-only code paths."""
    raise ProvenanceWriteError(
        f"{operation} must not assign tested_source_sha; use record_verification_event instead"
    )
