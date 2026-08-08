"""
BLACKDARK — Shareable MEV / Sandwich exposure report.

Public-safe, proof-oriented summary of sandwich/MEV risk posture.
Deepens Public Accuracy Ledger / Anti-Hype (prove risks, don't hype alpha).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_mev_sandwich_report(
    *,
    asset: str = "ETH",
    notional_usd: float = 10_000.0,
) -> dict[str, Any]:
    asset_u = (asset or "ETH").upper()
    notional = max(0.0, float(notional_usd or 0))
    # Conservative public heuristics — not a private mempool feed claim.
    estimated_sandwich_bps = 8.0 if asset_u in {"ETH", "WETH"} else 5.0
    estimated_cost = round(notional * estimated_sandwich_bps / 10_000.0, 4)
    mitigation = [
        "Prefer private/RPC relays when available (no guaranteed fill)",
        "Split size (Stealth Execution Advisor) to reduce attack surface",
        "Avoid predictable market orders in thin books",
        "Track Half-Life — do not chase a dying edge into sandwichable flow",
    ]
    share_text = (
        f"BLACKDARK MEV/Sandwich Report · {asset_u} · notional ${notional:,.0f} · "
        f"est. sandwich drag ~{estimated_sandwich_bps:.1f} bps (~${estimated_cost:,.2f}) · "
        f"mitigations published · verify posture on /oracle-accuracy · Not financial advice"
    )
    from decision_certificate import compliance_footer_block

    return {
        "title": "Shareable MEV / Sandwich Report",
        "asset": asset_u,
        "notional_usd": round(notional, 2),
        "estimated_sandwich_bps": estimated_sandwich_bps,
        "estimated_cost_usd": estimated_cost,
        "confidence": "heuristic_public_v1",
        "note": (
            "This is a shareable risk posture report — not a claim of private mempool alpha. "
            "We publish the drag estimate and mitigations (Prove it)."
        ),
        "mitigations": mitigation,
        "related": {
            "stealth_advisor": "/api/whale/stealth-advisor",
            "accuracy_ledger": "/oracle-accuracy",
            "half_life": "/api/oracle/half-life",
        },
        "share_text": share_text,
        "generated_at": datetime.now(UTC).isoformat(),
        "compliance": compliance_footer_block(
            surface="mev_sandwich_report",
            trust_basis="public_risk_posture + accuracy_ledger",
            data_sources="heuristic sandwich drag model · not private orderflow",
        ),
        "hero_deepening": "public_accuracy_ledger",
    }
