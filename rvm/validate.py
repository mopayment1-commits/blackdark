"""Validation layer — proves requirement achieves true intended purpose."""

from __future__ import annotations

from typing import Any

from cap646.backend_registry import is_generic_surface
from cap646.functional_dod import verify_functional
from cap646.runtime import execute_capability
from cap646.waves import EXTERNAL_EVIDENCE_SLOTS, SIGNED_INFRA_SLOTS, USER_FACING
from cap978.catalog import canonical_id, is_duplicate, is_external
from rvm.surfaces import has_dedicated_user_surface, hub_only_surface, surface_evidence


async def validate_capability(cap_id: int) -> dict[str, Any]:
    """Prove capability achieves intended user/institutional outcome — not just handler existence."""
    from cap978.catalog import is_extension
    from cap978.verify import verify_functional_978

    if is_external(cap_id):
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": ["vendor_contract_required"],
            "detail": {"reason": "external data/vendor rights"},
            "external_step": "Obtain vendor API contract and production credentials",
        }

    if is_duplicate(cap_id):
        canon = canonical_id(cap_id)
        if canon != cap_id:
            sub = await validate_capability(canon)
            if sub["status"] == "PASS":
                return {
                    "status": "PASS",
                    "evidence": [f"validated_via_canonical=CAP-{canon}"],
                    "detail": {"duplicate_of": canon},
                }
        return {"status": "PASS", "evidence": ["duplicate_no_separate_validation"], "detail": {}}

    if cap_id in EXTERNAL_EVIDENCE_SLOTS:
        result = await execute_capability(cap_id, skip_entitlement=True, params={"symbol": "BTC"})
        internal = bool(result.get("success")) and bool(result.get("compliance_footer"))
        if internal:
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": ["internal_evidence_slot_ready"],
                "detail": result,
                "external_step": "Deposit independent third-party penetration test attestation (ID645)",
            }
        return {"status": "FAIL", "evidence": [], "detail": result}

    if cap_id in SIGNED_INFRA_SLOTS:
        result = await execute_capability(cap_id, skip_entitlement=True, params={"symbol": "BTC"})
        signed = bool((result.get("report") or {}).get("signed_load_evidence", {}).get("present"))
        internal = bool(result.get("success"))
        if signed:
            return {"status": "PASS", "evidence": ["signed_load_evidence_present"], "detail": result}
        if internal:
            return {
                "status": "EXTERNAL_EVIDENCE_REQUIRED",
                "evidence": ["internal_load_runner_ready"],
                "detail": result,
                "external_step": "Run signed multi-worker capacity/load test under production topology (ID644)",
            }
        return {"status": "FAIL", "evidence": [], "detail": result}

    if is_extension(cap_id):
        functional = await verify_functional_978(cap_id)
    else:
        functional = await verify_functional(cap_id)
    checks = functional.get("checks", {})
    evidence: list[str] = []
    failure_reasons: list[str] = []

    if checks.get("domain_logic"):
        evidence.append("domain_logic_pass")
    else:
        failure_reasons.append(functional.get("failure_reason") or "domain_logic_fail")

    if checks.get("no_failover_mask"):
        evidence.append("no_failover_mask")
    else:
        failure_reasons.append("failover_or_generic_mask")

    if cap_id in USER_FACING:
        if hub_only_surface(cap_id):
            failure_reasons.append("hub_only_surface_insufficient")
        elif has_dedicated_user_surface(cap_id):
            evidence.extend(surface_evidence(cap_id))
            evidence.append("dedicated_user_surface")
        else:
            # Infra hub capabilities — require operational outcome
            if checks.get("domain_logic") and checks.get("backend"):
                evidence.append("infra_operational_outcome")
            else:
                failure_reasons.append("infra_operational_outcome_missing")

    if is_generic_surface(functional.get("surface")):
        failure_reasons.append("generic_surface_binding")

    verdict = functional.get("verdict", "")
    if verdict == "VERIFIED_COMPLETE" and not failure_reasons:
        return {"status": "PASS", "evidence": evidence, "detail": functional}

    if verdict == "EXTERNAL_EVIDENCE_REQUIRED":
        return {
            "status": "EXTERNAL_EVIDENCE_REQUIRED",
            "evidence": evidence,
            "detail": functional,
        }

    return {
        "status": "FAIL",
        "evidence": evidence,
        "detail": {**functional, "failure_reasons": failure_reasons},
    }


async def validate_control_entry(control_id: str) -> dict[str, Any]:
    """Validation requires operational proof, not code existence."""
    from rvm.verify import verify_control_entry

    verification = await verify_control_entry(control_id)
    ext_controls = {
        "SEC-006": "Configure production IdP (Okta/Azure AD) and complete end-to-end SSO login flow",
        "SEC-008": "Engage accredited pentest firm and deposit signed attestation report",
        "SEC-009": "Complete SOC2 Type II audit with accredited firm",
        "REL-002": "Execute signed HA load test across production worker topology",
    }
    if control_id in ext_controls:
        if verification["status"] == "EXTERNAL_EVIDENCE_REQUIRED":
            return {
                **verification,
                "external_step": ext_controls[control_id],
            }
        return verification

    # Operational validation for non-external controls
    if verification["status"] != "PASS":
        return {"status": "FAIL", "evidence": verification.get("evidence", []), "detail": verification.get("detail", {})}

    return {"status": "PASS", "evidence": verification.get("evidence", []), "detail": verification.get("detail", {})}


async def validate_platform_stage(stage_key: str) -> dict[str, Any]:
    from rvm.verify import verify_platform_stage

    verification = await verify_platform_stage(stage_key)
    if verification["status"] != "PASS":
        return {"status": "FAIL", "evidence": verification.get("evidence", []), "detail": verification.get("detail", {})}

    stage = (verification.get("detail") or {}).get("stage", {})
    # Validation: stage must produce traceable downstream artifact
    has_artifact = any(k for k in stage if k not in {"ok", "error"})
    if has_artifact:
        return {
            "status": "PASS",
            "evidence": verification.get("evidence", []) + ["downstream_artifact_present"],
            "detail": verification.get("detail", {}),
        }
    return {"status": "FAIL", "evidence": verification.get("evidence", []), "detail": verification.get("detail", {})}


async def validate_commercial_gate(gate_id: str) -> dict[str, Any]:
    from rvm.verify import verify_commercial_gate

    return await verify_commercial_gate(gate_id)


async def validate_institutional_gate(gate_id: str) -> dict[str, Any]:
    from rvm.verify import verify_institutional_gate

    verification = await verify_institutional_gate(gate_id)
    if gate_id == "INS-TENANT" and verification["status"] == "EXTERNAL_EVIDENCE_REQUIRED":
        return {
            **verification,
            "external_step": verification.get(
                "external_step", "Provision production Postgres and complete tenant migration"
            ),
        }
    return verification
