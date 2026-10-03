"""Anti-cherry-picking controls (DTS-058)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from decision_truth.outcome_ledger import get_preregistration

METHODOLOGY_VERSION = "dts-p4-anti-cherry-picking-1.0"


def validate_performance_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Ensure performance claims are reproducible from canonical ledger records."""
    violations: list[str] = []
    decision_id = claim.get("decision_id")
    if claim.get("retroactive_horizon_change"):
        violations.append("retroactive_horizon_change")
    if claim.get("retroactive_threshold_change"):
        violations.append("retroactive_threshold_change")
    if claim.get("subset_selection") and not claim.get("subset_disclosed"):
        violations.append("undisclosed_subset_selection")
    if claim.get("losses_omitted"):
        violations.append("losses_omitted_from_claim")

    reproducible = False
    if decision_id:
        prereg = get_preregistration(str(decision_id))
        if prereg:
            expected_hash = prereg.get("evidence_snapshot_hash")
            claim_hash = claim.get("evidence_snapshot_hash")
            if expected_hash and claim_hash and expected_hash == claim_hash:
                reproducible = True
            elif not claim_hash:
                violations.append("missing_evidence_snapshot_hash")
        else:
            violations.append("claim_without_preregistered_decision")

    if claim.get("post_outcome_preregistration"):
        violations.append("post_outcome_preregistration")

    return {
        "allowed": not violations,
        "violations": violations,
        "reproducible_from_ledger": reproducible,
        "methodology_version": METHODOLOGY_VERSION,
    }


def hash_claim_inputs(inputs: dict[str, Any]) -> str:
    payload = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
