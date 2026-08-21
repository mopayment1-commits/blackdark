"""Institutional Evidence Room — reproducible closure snapshot for DD/procurement."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain
from cap978.closure import institutional_closure_978
from cap978.external_registry import external_registry_report
from cap978.verify import execute_extension, verify_functional_978
from cap646.runtime import execute_capability


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def _sample_executions() -> list[dict[str, Any]]:
    """Representative E2E execution proofs across base + extension + platform."""
    samples = [
        (47, "base_market"),
        (631, "data_spine"),
        (639, "net_edge_truth"),
        (642, "ai_provenance_footer"),
        (647, "extension_blocked"),
        (700, "extension_internal"),
        (850, "extension_internal"),
        (978, "extension_tail"),
    ]
    user = {"email": "evidence-room@blackdark.local", "tier": "whale"}
    proofs: list[dict[str, Any]] = []
    for cid, label in samples:
        if cid >= 647:
            result = await execute_extension(cid, user=user, params={"symbol": "BTC", "tier": "whale"})
        else:
            result = await execute_capability(cid, user=user, params={"symbol": "BTC", "tier": "whale"})
        proofs.append(
            {
                "label": label,
                "capability_id": cid,
                "success": result.get("success"),
                "classification": result.get("classification") or result.get("evidence_class"),
                "surface": result.get("surface"),
                "backend_module": result.get("backend_module"),
                "proof_hash": _sha256({k: result.get(k) for k in ("success", "surface", "backend_module", "capability_id")}),
            }
        )
    return proofs


async def build_evidence_room_snapshot(*, include_rows: bool = False, full_closure: bool = True) -> dict[str, Any]:
    if full_closure:
        closure = await institutional_closure_978()
    else:
        from cap646.waves import WAVE_A, WAVE_B

        sample_ids = list(WAVE_A) + list(WAVE_B) + list(range(647, 679))
        from cap978.closure import institutional_closure_978 as _close

        closure = await _close(sample=True)
        closure["verdict"] = "SAMPLE"
    controls = await verify_all_controls()
    chain = await verify_data_platform_chain(symbol="BTC")
    external = external_registry_report()
    executions = await _sample_executions()

    functional_samples = []
    for cid in (1, 17, 47, 631, 644, 645, 700, 978):
        functional_samples.append(await verify_functional_978(cid))

    snapshot = {
        "generated_at": _utcnow(),
        "product_thesis": "978-capability Decision Intelligence platform — evidence-first closure",
        "verdict": closure["verdict"],
        "internal_closure": {
            "INTERNAL_PARTIAL": closure["cap978"]["INTERNAL_PARTIAL"],
            "INTERNAL_NOT_IMPLEMENTED": closure["cap978"]["INTERNAL_NOT_IMPLEMENTED"],
            "FUNCTIONALLY_INCOMPLETE": closure["cap978"]["FUNCTIONALLY_INCOMPLETE"],
        },
        "cap978_counts": closure["cap978"]["counts"],
        "extension_counts": closure["cap978"]["extension_647_978"],
        "governing_controls": {
            "counts": controls["counts"],
            "internal_closure": controls["internal_closure"],
        },
        "platform_chain": {
            "verdict": chain["verdict"],
            "internal_closure": chain["internal_closure"],
            "e2e": chain.get("e2e"),
        },
        "external_registry_summary": {
            "total": external["total"],
            "counts": external["counts"],
        },
        "sample_executions": executions,
        "functional_verification_samples": [
            {"id": r["id"], "verdict": r["verdict"], "failure_reason": r.get("failure_reason")}
            for r in functional_samples
        ],
        "repro_commands": [
            "PYTHONPATH=/workspace pytest tests/cap646/ -q",
            "curl /api/cap646/closure/978",
            "curl /api/cap646/evidence-room",
            "curl /api/cap646/platform-chain/e2e?symbol=BTC",
        ],
        "snapshot_hash": "",
    }
    if include_rows:
        snapshot["external_registry_rows"] = external["rows"]
        snapshot["closure_detail"] = closure
    snapshot["snapshot_hash"] = _sha256({k: v for k, v in snapshot.items() if k != "snapshot_hash"})
    return snapshot
