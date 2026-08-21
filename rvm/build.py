"""Build and merge RVM matrix from baseline + V&V results."""

from __future__ import annotations

import asyncio
from typing import Any

from rvm.baseline import load_baseline
from rvm.models import RVMEntry, FinalStatus
from rvm.validate import (
    validate_capability,
    validate_commercial_gate,
    validate_control_entry,
    validate_institutional_gate,
    validate_platform_stage,
)
from rvm.verify import (
    verify_capability,
    verify_commercial_gate,
    verify_control_entry,
    verify_institutional_gate,
    verify_platform_stage,
)


def _merge_status(verification: dict[str, Any], validation: dict[str, Any]) -> FinalStatus:
    v_status = verification.get("status", "FAIL")
    val_status = validation.get("status", "FAIL")
    if v_status == "EXTERNAL_EVIDENCE_REQUIRED" or val_status == "EXTERNAL_EVIDENCE_REQUIRED":
        return "EXTERNAL_EVIDENCE_REQUIRED"
    if v_status == "PASS" and val_status == "PASS":
        return "PASS"
    return "FAIL"


def _reconcile_gap(gap_status: str | None, final: FinalStatus) -> tuple[bool, str]:
    """Flag conflicts between gap matrix and RVM final status."""
    if not gap_status:
        return True, ""
    mapping = {
        "VERIFIED_IMPLEMENTED": "PASS",
        "NOT_IMPLEMENTED": "FAIL",
        "PARTIALLY_IMPLEMENTED": "FAIL",
        "DUPLICATE/ALREADY_COVERED": "PASS",
        "EXTERNAL/BLOCKED": "EXTERNAL_EVIDENCE_REQUIRED",
    }
    expected = mapping.get(gap_status, None)
    if expected is None:
        return True, ""
    if expected == final:
        return True, ""
    return False, f"gap_matrix={gap_status} vs rvm={final}"


async def _process_requirement(req: dict[str, Any]) -> dict[str, Any]:
    req_id = req["id"]
    kind = req["kind"]
    gap_status = req.get("gap_matrix_status")

    if kind == "capability":
        cap_id = int(req_id.replace("CAP-", ""))
        verification = await verify_capability(cap_id)
        validation = await validate_capability(cap_id)
    elif kind == "control":
        verification = await verify_control_entry(req_id)
        validation = await validate_control_entry(req_id)
    elif kind == "platform":
        verification = await verify_platform_stage(req_id)
        validation = await validate_platform_stage(req_id)
    elif kind == "commercial":
        verification = await verify_commercial_gate(req_id)
        validation = await validate_commercial_gate(req_id)
    elif kind == "institutional":
        verification = await verify_institutional_gate(req_id)
        validation = await validate_institutional_gate(req_id)
    else:
        verification = {"status": "FAIL", "evidence": [], "detail": {}}
        validation = {"status": "FAIL", "evidence": [], "detail": {}}

    final = _merge_status(verification, validation)
    reconciled, conflict_note = _reconcile_gap(gap_status, final)
    external_step = validation.get("external_step") or verification.get("external_step")

    impl_evidence = list(verification.get("evidence") or [])
    runtime_evidence = list(validation.get("evidence") or [])

    return {
        **req,
        "verification_status": verification.get("status", "FAIL"),
        "validation_status": validation.get("status", "FAIL"),
        "final_status": final,
        "implementation_evidence": impl_evidence,
        "runtime_evidence": runtime_evidence,
        "verification_detail": verification.get("detail", {}),
        "validation_detail": validation.get("detail", {}),
        "external_step": external_step,
        "reconciled": reconciled,
        "notes": conflict_note,
    }


async def build_rvm_matrix(*, concurrency: int = 40) -> list[dict[str, Any]]:
    baseline = load_baseline()
    requirements = baseline["requirements"]
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(req: dict[str, Any]) -> dict[str, Any]:
        async with sem:
            return await _process_requirement(req)

    return await asyncio.gather(*[_bounded(r) for r in requirements])
