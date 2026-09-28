"""Verifier invariants for capability provenance (B1-R)."""

from __future__ import annotations

from typing import Any

from capability_provenance.contract import (
    ARTIFACT_GENERATION_STAMP_CLASS,
    CONTRACT_PATH,
    LEGACY_AMBIGUOUS_CLASS,
    VERIFICATION_BOUND_CLASS,
    load_contract,
)


class ProvenanceInvariantViolation(Exception):
    """Raised when a capability record violates provenance invariants."""


def verify_contract_loaded() -> dict[str, Any]:
    contract = load_contract()
    if not CONTRACT_PATH.is_file():
        raise ProvenanceInvariantViolation("capability provenance contract file missing")
    return contract


def classify_tested_source_sha(cap: dict[str, Any]) -> str:
    """Classify existing tested_source_sha without mutating the record."""
    tested = cap.get("tested_source_sha")
    if not tested:
        return LEGACY_AMBIGUOUS_CLASS

    status_change = cap.get("status_change") or {}
    verification = status_change.get("verification")
    status_sha = status_change.get("tested_sha")

    if verification and status_sha:
        if status_sha == tested:
            return VERIFICATION_BOUND_CLASS
        return LEGACY_AMBIGUOUS_CLASS

    semantic = cap.get("semantic_correction") or {}
    prior = semantic.get("prior_artifact_sha") or ""
    if prior and str(tested).startswith(str(prior)[:12]):
        return ARTIFACT_GENERATION_STAMP_CLASS

    if tested and not verification:
        return LEGACY_AMBIGUOUS_CLASS

    return LEGACY_AMBIGUOUS_CLASS


def verify_capability_record(cap: dict[str, Any], *, strict_post_b1r: bool = False) -> list[str]:
    """Return invariant violation messages for a capability record."""
    violations: list[str] = []
    cap_id = cap.get("capability_id", "<unknown>")
    tested = cap.get("tested_source_sha")
    status_change = cap.get("status_change") or {}
    verification = status_change.get("verification")
    status_sha = status_change.get("tested_sha")

    if verification and status_sha and tested and status_sha != tested:
        violations.append(
            f"{cap_id}: INV-003 status_change.tested_sha ({status_sha}) != tested_source_sha ({tested})"
        )

    if strict_post_b1r:
        classification = classify_tested_source_sha(cap)
        contract_version = (status_change.get("provenance_contract_version") or "").startswith("B1-R")
        if contract_version and classification == LEGACY_AMBIGUOUS_CLASS:
            violations.append(f"{cap_id}: post-B1-R record still classified {LEGACY_AMBIGUOUS_CLASS}")

        if contract_version and not verification:
            violations.append(f"{cap_id}: INV-001 post-B1-R tested_source_sha without verification payload")

    return violations


def verify_ssot_artifact(ssot: dict[str, Any], *, check_capabilities: bool = True) -> dict[str, Any]:
    """Verify SSOT artifact-level provenance and optionally scan capability records."""
    verify_contract_loaded()
    violations: list[str] = []
    legacy_counts: dict[str, int] = {}

    if check_capabilities:
        for cap in ssot.get("canonical_capabilities") or []:
            for msg in verify_capability_record(cap):
                violations.append(msg)
            cls = classify_tested_source_sha(cap)
            legacy_counts[cls] = legacy_counts.get(cls, 0) + 1

    git = ssot.get("git") or {}
    if not git.get("current_head_sha"):
        violations.append("INV-ARTIFACT: missing git.current_head_sha")

    return {
        "contract_version": load_contract()["contract_version"],
        "violations": violations,
        "legacy_classification_counts": legacy_counts,
        "ok": not violations,
    }
