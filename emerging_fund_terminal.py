"""
BLACKDARK — Emerging Fund Terminal (Section Z #4).

Onboarding posture for crypto funds under ~$50M: DD-ready packaging of
Public Accuracy Ledger + Decision Certificate + Evidence Pack summary.
Pricing posture for 10–50M AUM — not Bloomberg-tier.
"""

from __future__ import annotations

from typing import Any


async def build_fund_terminal_pack(*, fund_name: str = "Emerging Fund") -> dict[str, Any]:
    """Assemble export-oriented DD pack for small/emerging funds."""
    from decision_certificate import compliance_footer_block

    accuracy = {}
    evidence_public = {}
    locked = {}
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        accuracy = await build_public_accuracy_payload(recent_limit=8)
    except Exception as exc:
        accuracy = {"error": str(exc)}

    evidence_public = {
        "product_thesis": (
            "Decision Intelligence + Proven Predictive Accuracy + "
            "Proprietary Labeled Market Corpus"
        ),
        "differentiators": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
        "full_pack": "/api/due-diligence/evidence-pack",
        "access": "whale_or_admin",
    }

    try:
        from locked_predictions import glass_box_status

        locked = glass_box_status()
    except Exception:
        locked = {}

    oracle = accuracy.get("oracle") or {}
    proof = accuracy.get("proof_chain") or {}

    return {
        "fund_name": fund_name,
        "segment": "emerging_crypto_fund_sub_50m",
        "pricing_posture": {
            "target_aum_usd": "10M–50M",
            "note": "Priced for the underserved 78% of crypto funds — not billion-dollar desks.",
            "tiers": ["pro", "whale"],
            "checkout_pro": "/create-checkout-session?tier=pro",
            "checkout_whale": "/create-checkout-session?tier=whale",
        },
        "dd_export": {
            "public_accuracy_percent": oracle.get("average_accuracy_percent"),
            "total_predictions": oracle.get("total_predictions"),
            "proof_chain_valid": (proof.get("verify") or {}).get("valid"),
            "tip_hash": proof.get("tip_hash"),
            "accuracy_page": "/oracle-accuracy",
            "evidence_public": evidence_public,
            "locked_predictions": locked,
        },
        "allocator_checklist": [
            "Verify public accuracy ledger sample size and hit-rate",
            "Inspect audit chain tip hash integrity",
            "Review Net-Edge reject posture (quality over quantity)",
            "Confirm Contradiction Veto is fail-closed",
            "Request full Evidence Pack (Whale/Admin)",
        ],
        "onboarding_steps": [
            "Open /b2b#fund-terminal",
            "Review Public Accuracy Ledger",
            "Export Decision Certificates from live Oracle calls",
            "Upgrade Whale for full Evidence Pack download",
        ],
        "compliance": compliance_footer_block(
            surface="emerging_fund_terminal",
            trust_basis="public_accuracy_ledger + evidence_pack",
        ),
        "hero_deepening": ["public_accuracy_ledger", "b2b_evidence"],
    }
