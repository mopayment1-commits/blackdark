"""
BLACKDARK — Monthly Losing Trade report (Section هـ).

Public, honest report of incorrect / partial Oracle outcomes — the opposite
of competitor highlight reels. Deepens Public Accuracy Ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


async def build_monthly_losing_report(*, limit: int = 25) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions

    rows = await fetch_labeled_oracle_predictions(limit=800, include_synthetic=False)
    misses = [
        r
        for r in (rows or [])
        if str(r.get("label") or "").lower() in {"incorrect", "partial"}
    ]
    misses.sort(key=lambda r: str(r.get("timestamp") or r.get("created_at") or ""), reverse=True)
    sample = misses[:limit]
    public = [
        {
            "prediction_id": r.get("id") or r.get("prediction_id"),
            "asset": r.get("asset"),
            "verdict": r.get("verdict"),
            "label": r.get("label"),
            "score": r.get("opportunity_score"),
            "timestamp": r.get("timestamp") or r.get("created_at"),
        }
        for r in sample
    ]
    thesis = (
        "We publish misses, not just wins — the Glass Box posture. "
        "Competitors show highlights; we show the full ledger."
    )
    share_text = (
        f"BLACKDARK Monthly Losing Trade Report · {len(misses)} labeled misses in window · "
        f"full public ledger at /oracle-accuracy#losing · Prove it, not trust me · Not financial advice"
    )
    return {
        "title": "Monthly Losing Trade Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thesis": thesis,
        "total_labeled_misses_in_window": len(misses),
        "sample": public,
        "share_text": share_text,
        "public_accuracy_page": "/oracle-accuracy",
        "hero_deepening": "public_accuracy_ledger",
        "compliance": {
            "disclaimer": "Not financial advice. Past misses do not predict future results. Verify on the Public Accuracy Ledger.",
            "trust_basis": "public_accuracy_ledger + labeled_flywheel",
        },
    }
