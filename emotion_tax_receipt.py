"""
BLACKDARK — Emotion Tax Receipt (brand viral atom).

Private-by-default educational estimate of cost from overriding system WAIT/Act.
Shareable anonymized card — habit + viral honesty.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote


def build_emotion_tax_receipt(
    *,
    user_key: str = "anon",
    overrides: int | None = None,
    follow_rate_percent: float | None = None,
    notional_usd: float = 1000.0,
) -> dict[str, Any]:
    """Estimate educational emotion-tax from discipline mirror stats when available."""
    uk = (user_key or "anon").strip() or "anon"
    fr = follow_rate_percent
    ov = overrides
    try:
        from discipline_mirror import personal_mirror

        mirror = personal_mirror(uk, limit=100) or {}
        if fr is None:
            fr = float(mirror.get("follow_rate_percent") or 0)
        if ov is None:
            ov = int(mirror.get("ignored_count") or 0)
        delta = mirror.get("delta_plain_english") or mirror.get("message")
    except Exception:
        mirror = {}
        delta = None
        if fr is None:
            fr = 0.0
        if ov is None:
            ov = 0

    # Educational model: each override vs WAIT assumed 0.35% adverse move on notional
    tax_per = float(notional_usd) * 0.0035
    tax = round(tax_per * float(ov), 2)
    anon = hashlib.sha256(uk.encode()).hexdigest()[:10]
    share = (
        f"BLACKDARK Emotion Tax · anon:{anon} · estimated ${tax:.0f} "
        f"from {ov} overrides (educational). Follow rate {fr}%. "
        f"Discipline > dopamine. /emotion-tax · Not financial advice"
    )
    return {
        "surface": "emotion_tax_receipt",
        "generated_at": datetime.now(UTC).isoformat(),
        "user_key_hash": anon,
        "follow_rate_percent": fr,
        "overrides": int(ov),
        "notional_usd_assumed": notional_usd,
        "estimated_emotion_tax_usd": tax,
        "model": "educational_0_35bps_per_override_v1",
        "delta": delta,
        "headline": f"Emotion tax ≈ ${tax:.0f}",
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/emotion-tax",
        "api": "/api/emotion-tax/receipt",
        "disclaimer": (
            "Educational estimate only — not accounting, not P&L truth, not financial advice. "
            "Private by default; share is anonymized."
        ),
    }
