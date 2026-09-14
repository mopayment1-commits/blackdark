"""DTS-035 — Evidence-backed sentences for material claims."""

from __future__ import annotations

from typing import Any


def validate_material_claims(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate or degrade material claims lacking evidence backing."""
    claims: list[dict[str, Any]] = []
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})

    candidates = [
        ("decision_state", str(payload.get("decision_truth_state") or ""), contract),
        ("grade", str(contract.get("grade") or ""), contract),
        ("evidence_class", str(contract.get("evidence_class") or ""), contract),
    ]
    net = contract.get("net_edge") or {}
    if net.get("expected_net_edge_bps") is not None:
        candidates.append(("expected_net_edge_bps", str(net["expected_net_edge_bps"]), net))

    for claim_type, text, source_pack in candidates:
        if not text or text == "UNAVAILABLE":
            continue
        ref = _claim_evidence_ref(payload, contract, source_pack)
        status = "verified" if ref.get("source") and (ref.get("timestamp") or ref.get("freshness")) else "degraded"
        if status == "degraded" and claim_type in {"grade", "expected_net_edge_bps"}:
            status = "suppressed" if not ref.get("evidence_class") else "qualified"
        claims.append(
            {
                "claim_type": claim_type,
                "text": text,
                "status": status,
                "evidence": ref,
            }
        )

    narrative = str(payload.get("narrative") or "")
    if narrative:
        ref = _claim_evidence_ref(payload, contract, contract)
        claims.append(
            {
                "claim_type": "narrative",
                "text": narrative[:200],
                "status": "verified" if ref.get("source") else "degraded",
                "evidence": ref,
            }
        )

    ungrounded = [c for c in claims if c["status"] in {"degraded", "suppressed"}]
    return {
        "claims": claims,
        "total_material_claims": len(claims),
        "ungrounded_count": len(ungrounded),
        "all_grounded": len(ungrounded) == 0,
        "methodology_version": "dts-p5-evidence-backed-sentences-1.0",
    }


def _claim_evidence_ref(payload: dict[str, Any], contract: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    prov = contract.get("provenance_context") or pack.get("provenance_context") or {}
    fresh = contract.get("freshness") or {}
    return {
        "source": prov.get("source") or payload.get("source") or ("decision_truth" if contract else None),
        "timestamp": fresh.get("as_of") or payload.get("timestamp"),
        "freshness": fresh.get("state") or fresh.get("freshness_state"),
        "evidence_class": contract.get("evidence_class"),
        "methodology_version": contract.get("methodology_version") or pack.get("methodology_version"),
        "decision_id": payload.get("decision_id"),
    }
