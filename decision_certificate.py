"""
BLACKDARK — Decision Certificate (Hero #6).

Exportable, shareable proof for a single Oracle decision:
prediction_id + chain_hash + sentence + timestamp.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_decision_certificate(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe Decision Certificate from an Oracle response."""
    body = {
        "asset": str(payload.get("symbol") or payload.get("asset") or "").upper(),
        "prediction_id": payload.get("prediction_id"),
        "chain_hash": payload.get("chain_hash") or (payload.get("proof") or {}).get("chain_hash"),
        "decision_action": payload.get("decision_action") or payload.get("verdict"),
        "decision_sentence": payload.get("decision_sentence") or payload.get("oracle"),
        "opportunity_score": payload.get("opportunity_score"),
        "truth_score": (payload.get("net_edge_truth") or {}).get("truth_score"),
        "half_life_seconds": (payload.get("opportunity_half_life") or {}).get(
            "expected_half_life_seconds"
        ),
        "market_regime": payload.get("market_regime"),
        "ux_mode": payload.get("ux_mode"),
        "issued_at": _utcnow(),
        "public_accuracy": "/oracle-accuracy",
        "engine": payload.get("unified_engine") or "unified_multimodal_v1",
    }
    raw = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    body["certificate_hash"] = hashlib.sha256(raw).hexdigest()
    body["share_text"] = (
        f"BLACKDARK Decision Certificate · {body['asset']} · "
        f"{body['decision_action']} · score {body['opportunity_score']} · "
        f"id={body['prediction_id']} · verify {body['public_accuracy']}"
    )
    body["compliance"] = compliance_footer_block(
        surface="decision_certificate",
        trust_basis="public_accuracy_ledger + audit_hash_chain",
    )
    return body


def compliance_footer_block(
    *,
    surface: str,
    trust_basis: str,
    data_sources: str = "live market + institutional context + labeled flywheel",
) -> dict[str, str]:
    """Anti-Hype Compliance Footer (Section Z #5) — shared under AI outputs."""
    return {
        "surface": surface,
        "data_source": data_sources,
        "trust_basis": trust_basis,
        "disclaimer": (
            "Not financial advice. AI cannot guarantee future returns. "
            "Verify claims on the Public Accuracy Ledger. No secret alpha promises."
        ),
        "regulator_note": "Built for auditability against AI-washing enforcement patterns (prove-it, not trust-me).",
    }
