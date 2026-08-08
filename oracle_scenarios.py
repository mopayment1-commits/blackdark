"""
BLACKDARK — Lightweight Bull / Base / Bear scenario fan-out for Oracle payloads.

Probabilistic ranges derived from existing score/confidence/regime — not a full Monte Carlo desk.
"""

from __future__ import annotations

from typing import Any


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def build_oracle_scenarios(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach three scenarios with approximate probabilities and ranges."""
    try:
        price = float(payload.get("price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    try:
        score = float(payload.get("opportunity_score") or 50)
    except (TypeError, ValueError):
        score = 50.0
    try:
        conf = float(payload.get("confidence") if payload.get("confidence") is not None else 50)
    except (TypeError, ValueError):
        conf = 50.0

    verdict = str(payload.get("decision_action") or payload.get("verdict") or "WAIT").upper()
    regime = str(payload.get("market_regime") or payload.get("regime") or "unknown")
    conflict = payload.get("dimension_conflict") or {}
    abstain = bool(conflict.get("veto") or conflict.get("abstain"))

    # Center base probability on WAIT / ACT posture
    if abstain or verdict in {"WAIT", "HOLD", "CAUTION"}:
        base_p = 52.0
        bull_p = 24.0 + (score - 50) * 0.15
        bear_p = 24.0 - (score - 50) * 0.15
    elif verdict in {"ACT", "BUY", "LONG"}:
        bull_p = 38.0 + (score - 55) * 0.2
        base_p = 40.0
        bear_p = 22.0 - (score - 55) * 0.1
    elif verdict in {"SELL", "SHORT"}:
        bear_p = 38.0 + (55 - score) * 0.2
        base_p = 40.0
        bull_p = 22.0 - (55 - score) * 0.1
    else:
        base_p, bull_p, bear_p = 50.0, 25.0, 25.0

    # Confidence widens/narrows dispersion
    scale = 0.7 + (conf / 100.0) * 0.6
    bull_p = _clamp(bull_p * scale / max(scale, 0.01))
    bear_p = _clamp(bear_p * scale / max(scale, 0.01))
    base_p = _clamp(100.0 - bull_p - bear_p)
    total = bull_p + base_p + bear_p or 1.0
    bull_p, base_p, bear_p = (100.0 * bull_p / total, 100.0 * base_p / total, 100.0 * bear_p / total)

    # Expected range band grows when confidence is low
    band = max(0.8, (100.0 - conf) / 100.0 * 6.0 + 1.2)  # percent
    if price <= 0:
        ranges = {"bull": None, "base": None, "bear": None}
    else:
        ranges = {
            "bull": {
                "low": round(price * (1 + band * 0.15 / 100), 6),
                "high": round(price * (1 + band / 100), 6),
            },
            "base": {
                "low": round(price * (1 - band * 0.35 / 100), 6),
                "high": round(price * (1 + band * 0.35 / 100), 6),
            },
            "bear": {
                "low": round(price * (1 - band / 100), 6),
                "high": round(price * (1 - band * 0.15 / 100), 6),
            },
        }

    drivers = []
    if payload.get("explanation"):
        factors = (payload.get("explanation") or {}).get("top_3_factors") or []
        for f in factors[:3]:
            if isinstance(f, dict):
                drivers.append(str(f.get("factor") or f.get("label") or ""))
            else:
                drivers.append(str(f))
    drivers = [d for d in drivers if d][:3]
    if not drivers:
        drivers = [f"Opportunity score {score:.0f}", f"Regime {regime}", f"Verdict {verdict}"]

    risks = []
    if abstain:
        risks.append("Dimension conflict — system prefers WAIT")
    if conf < 45:
        risks.append("Low model confidence — ranges are wider")
    risks.append("Probabilistic sketch only — not a forecast guarantee")

    return {
        "engine": "oracle_scenarios_v1",
        "disclaimer": (
            "Scenario probabilities are a lightweight fan-out from score/confidence/regime. "
            "Not Monte Carlo, not financial advice."
        ),
        "regime": regime,
        "scenarios": {
            "bull": {
                "probability_pct": round(bull_p, 1),
                "expected_range": ranges["bull"],
                "label": "Bull",
                "drivers": drivers[:2],
                "risks": risks[:2],
            },
            "base": {
                "probability_pct": round(base_p, 1),
                "expected_range": ranges["base"],
                "label": "Base",
                "drivers": drivers,
                "risks": risks,
            },
            "bear": {
                "probability_pct": round(bear_p, 1),
                "expected_range": ranges["bear"],
                "label": "Bear",
                "drivers": drivers[:2],
                "risks": risks[:2],
            },
        },
        "confidence_pct": round(conf, 1),
    }
