"""
BLACKDARK — F4 Transfer Intent Probability.

Publishes numeric intent probabilities: Custody / Collateral / Directional.
Breaks Whale Alert myths: Transfers ≠ Trades.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def compute_transfer_intent(
    *,
    asset: str = "BTC",
    amount_usd: float = 5_000_000.0,
    from_label: str = "unknown",
    to_label: str = "unknown",
    funding_z: float | None = None,
    oi_change_percent: float | None = None,
) -> dict[str, Any]:
    asset_u = (asset or "BTC").upper()
    frm = (from_label or "unknown").lower()
    to = (to_label or "unknown").lower()

    custody = 40.0
    collateral = 30.0
    directional = 30.0

    exchange_words = {"binance", "coinbase", "okx", "kraken", "bybit", "exchange", "cold", "custody"}
    if any(w in frm for w in exchange_words) and any(w in to for w in exchange_words):
        custody, collateral, directional = 72.0, 18.0, 10.0
    elif "exchange" in to or any(w in to for w in {"binance", "coinbase", "okx"}):
        custody, collateral, directional = 25.0, 20.0, 55.0
    elif "exchange" in frm:
        custody, collateral, directional = 55.0, 25.0, 20.0

    if amount_usd >= 10_000_000:
        custody += 5
        directional -= 5

    # Derivatives conflict adjusts directional confidence band
    conflict = False
    if funding_z is not None and abs(float(funding_z)) > 1.5:
        conflict = True
        directional = max(5.0, directional - 8)
        custody += 4
        collateral += 4
    if oi_change_percent is not None and abs(float(oi_change_percent)) > 8:
        conflict = True

    total = custody + collateral + directional
    custody, collateral, directional = (
        round(100 * custody / total, 1),
        round(100 * collateral / total, 1),
        round(100 * directional / total, 1),
    )
    # Fix rounding drift
    directional = round(100.0 - custody - collateral, 1)

    dominant = max(
        ("custody", custody),
        ("collateral", collateral),
        ("directional", directional),
        key=lambda x: x[1],
    )[0]
    confidence_band = "wide" if conflict or frm == "unknown" else "moderate"
    share = (
        f"BLACKDARK Transfer Intent · {asset_u} ${amount_usd:,.0f} · "
        f"Custody {custody:.0f}% · Collateral {collateral:.0f}% · Directional {directional:.0f}% · "
        f"Transfers ≠ Trades · /transfer-intent · Not financial advice"
    )
    return {
        "feature_id": "F4",
        "surface": "transfer_intent_probability",
        "product_complete": False,
        "generated_at": _utcnow(),
        "asset": asset_u,
        "amount_usd": amount_usd,
        "from_label": from_label,
        "to_label": to_label,
        "probabilities": {
            "custody_percent": custody,
            "collateral_percent": collateral,
            "directional_percent": directional,
        },
        "dominant_intent": dominant,
        "confidence_band": confidence_band,
        "derivatives_conflict": conflict,
        "funding_z": funding_z,
        "oi_change_percent": oi_change_percent,
        "doctrine": "Transfers ≠ Trades — never treat a transfer as a buy/sell without intent probability",
        "headline": f"Dominant: {dominant} · Custody {custody:.0f}% · Dir {directional:.0f}%",
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/transfer-intent",
        "api": "/api/transfer-intent",
        "related": {"signal_vs_noise": "/api/whale/signal-vs-noise", "miss_feed": "/miss-feed"},
    }


async def build_transfer_intent_board(*, asset: str = "BTC") -> dict[str, Any]:
    """Enrich from whale classifier when available; always return product surface."""
    sample = compute_transfer_intent(asset=asset, amount_usd=8_500_000, from_label="unknown", to_label="binance")
    whale = {}
    try:
        from whale_signal_classifier import enrich_whale_narratives

        whale = await enrich_whale_narratives(limit=5)
        items = whale.get("items") or whale.get("alerts") or []
        if items:
            first = items[0]
            sample = compute_transfer_intent(
                asset=str(first.get("asset") or asset),
                amount_usd=float(first.get("amount_usd") or first.get("notional_usd") or 5_000_000),
                from_label=str(first.get("from_label") or first.get("from") or "unknown"),
                to_label=str(first.get("to_label") or first.get("to") or "unknown"),
                funding_z=first.get("funding_z"),
                oi_change_percent=first.get("oi_change_percent"),
            )
    except Exception:
        whale = {}
    return {
        **sample,
        "board": True,
        "whale_enrichment_available": bool(whale),
        "examples": [
            compute_transfer_intent(asset=asset, amount_usd=12_000_000, from_label="coinbase", to_label="cold"),
            compute_transfer_intent(asset=asset, amount_usd=3_000_000, from_label="unknown", to_label="binance"),
            sample,
        ],
    }
