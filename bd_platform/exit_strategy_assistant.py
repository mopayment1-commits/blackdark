"""
Exit Strategy Assistant — Feature #156 (Sprint 2, with #125 Oracle).

Recommended Exit Zone — NOT a mandatory sell order.
Editable zone with reasoning: resistance, RSI, liquidity trend.

Legal framing: suggestion only — decision remains with the user.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExitStrategy")

_FEATURE_ID = 156
_PREFS_PATH = Path("data/exit_zone_preferences.json")
_LEGAL_DISCLAIMER = (
    "Recommended Exit Zone is a suggestion only — not a mandatory sell order. "
    "This is not financial advice. The decision is yours."
)
_LEGAL_DISCLAIMER_AR = (
    "منطقة الخروج المقترحة هي اقتراح فقط — ليست أمر بيع حتمي. "
    "هذا ليس نصيحة مالية. القرار لك."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_prefs() -> dict[str, Any]:
    if not _PREFS_PATH.is_file():
        return {"zones": {}}
    try:
        return json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"zones": {}}


def _save_prefs(prefs: dict[str, Any]) -> None:
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    prefs["updated_at"] = _utcnow()
    _PREFS_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def _round_price(p: float) -> float:
    if p >= 10_000:
        return round(p, 0)
    if p >= 100:
        return round(p, 2)
    return round(p, 4)


async def compute_recommended_exit_zone(
    asset: str,
    *,
    entry_price: float | None = None,
    custom_zone_low: float | None = None,
    custom_zone_high: float | None = None,
) -> dict[str, Any]:
    """Compute editable Recommended Exit Zone with reasoning."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    from bd_platform.free_market_data import binance_futures_snapshot

    snap = await binance_futures_snapshot(sym)
    mark = float(snap.get("mark_price") or 0)
    if mark <= 0:
        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "asset": sym,
            "error": "price_unavailable",
            "disclaimer": _LEGAL_DISCLAIMER,
            "sla_met": elapsed <= 2000,
            "timestamp": _utcnow(),
        }

    reasons: list[dict[str, str]] = []
    rsi: float | None = None

    try:
        from technical_analysis import build_ta_bundle

        ta = await build_ta_bundle(sym)
        rsi = ta.get("rsi")
        if rsi is not None and float(rsi) > 70:
            reasons.append({
                "factor": "rsi_overbought",
                "detail": f"RSI {rsi:.1f} > 70 — overbought territory",
                "weight": "high",
            })
    except Exception:
        logger.debug("TA bundle unavailable for exit zone", exc_info=True)

    # Historical resistance proxy — recent high + round number
    change_pct = float(snap.get("change_24h_pct") or 0)
    resistance = mark * (1.03 + min(0.05, max(0, change_pct) / 200))
    reasons.append({
        "factor": "historical_resistance",
        "detail": f"Resistance proxy at {_round_price(resistance)} (24h momentum adjusted)",
        "weight": "medium",
    })

    # Liquidity declining signal
    try:
        from bd_platform.liquidity_health_check import analyze_liquidity_health

        liq = await analyze_liquidity_health(sym)
        if liq.get("ok"):
            conc = (liq.get("concentration") or {}).get("concentration_risk")
            if conc in {"high", "medium"}:
                reasons.append({
                    "factor": "liquidity_concern",
                    "detail": f"Liquidity concentration risk: {conc}",
                    "weight": "medium",
                })
    except Exception:
        pass

    zone_low = custom_zone_low if custom_zone_low is not None else _round_price(mark * 1.02)
    zone_high = custom_zone_high if custom_zone_high is not None else _round_price(resistance)
    if zone_low > zone_high:
        zone_low, zone_high = zone_high, zone_low

    # Oracle hook (#125)
    oracle_block: dict[str, Any] = {}
    try:
        from ai_oracle import OpportunityExplanation, get_single_sentence_oracle

        explanation = OpportunityExplanation(
            kind="cross_exchange",
            asset=sym,
            summary=f"Exit zone analysis for {sym}",
            reasons=[r["detail"] for r in reasons],
            risk_factors=[],
            confidence_percent=65.0,
        )
        oracle = await get_single_sentence_oracle(sym, 55.0, explanation)
        oracle_block = {
            "verdict": oracle.verdict,
            "sentence": oracle.sentence,
            "integrated_feature": "#125",
        }
    except Exception:
        oracle_block = {"integrated_feature": "#125", "available": False}

    elapsed = (time.perf_counter() - t0) * 1000
    display_en = (
        f"🟡 Exit Zone: ${_round_price(zone_low):,.0f} - ${_round_price(zone_high):,.0f}. "
        f"This is a suggestion — the decision is yours."
    )
    display_ar = (
        f"🟡 منطقة خروج مقترحة: ${_round_price(zone_low):,.0f} - ${_round_price(zone_high):,.0f}. "
        f"هذا اقتراح — القرار لك."
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": sym,
        "current_price_usd": mark,
        "entry_price_usd": entry_price,
        "exit_zone": {
            "low_usd": zone_low,
            "high_usd": zone_high,
            "editable": True,
            "user_customized": custom_zone_low is not None or custom_zone_high is not None,
        },
        "status_emoji": "🟡",
        "reasons": reasons,
        "rsi": rsi,
        "display_en": display_en,
        "display_ar": display_ar,
        "oracle": oracle_block,
        "disclaimer": _LEGAL_DISCLAIMER,
        "disclaimer_ar": _LEGAL_DISCLAIMER_AR,
        "not_mandatory_sell": True,
        "integrated_features": ["#125"],
        "sla_met": elapsed <= 2000,
        "latency_ms": round(elapsed, 1),
        "timestamp": _utcnow(),
    }


def save_user_exit_zone(
    asset: str,
    *,
    zone_low: float,
    zone_high: float,
    user_id: str = "default",
) -> dict[str, Any]:
    """Persist user-edited exit zone."""
    prefs = _load_prefs()
    zones = prefs.setdefault("zones", {})
    key = f"{user_id}:{asset.upper()}"
    zones[key] = {
        "asset": asset.upper(),
        "zone_low": zone_low,
        "zone_high": zone_high,
        "saved_at": _utcnow(),
    }
    _save_prefs(prefs)
    return {"ok": True, "saved": True, "key": key, "zone": zones[key]}


def exit_strategy_status() -> dict[str, Any]:
    prefs = _load_prefs()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Exit Strategy Assistant",
        "not_mandatory_sell": True,
        "editable_zones": True,
        "saved_preferences": len(prefs.get("zones") or {}),
        "integrated_features": ["#125"],
        "disclaimer": _LEGAL_DISCLAIMER,
        "timestamp": _utcnow(),
    }
