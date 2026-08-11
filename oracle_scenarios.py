"""
BLACKDARK — Lightweight Bull / Base / Bear scenario fan-out for Oracle payloads.

Probabilistic ranges derived from existing score/confidence/regime — not a full Monte Carlo desk.
"""

from __future__ import annotations

from typing import Any


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _safe_head(items: list[Any], n: int) -> list[Any]:
    if n <= 0 or not items:
        return []
    return items[: min(n, len(items))]


def _float_payload(payload: dict[str, Any], key: str, default: float) -> float:
    try:
        value = payload.get(key)
        if key == "confidence" and value is None:
            value = default
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _scenario_probabilities(verdict: str, score: float, abstain: bool) -> tuple[float, float, float]:
    if abstain or verdict in {"WAIT", "HOLD", "CAUTION"}:
        return 24.0 + (score - 50) * 0.15, 52.0, 24.0 - (score - 50) * 0.15
    if verdict in {"ACT", "BUY", "LONG"}:
        return 38.0 + (score - 55) * 0.2, 40.0, 22.0 - (score - 55) * 0.1
    if verdict in {"SELL", "SHORT"}:
        return 22.0 - (55 - score) * 0.1, 40.0, 38.0 + (55 - score) * 0.2
    return 25.0, 50.0, 25.0


def _normalize_probabilities(bull_p: float, base_p: float, bear_p: float) -> tuple[float, float, float]:
    bull_c = _clamp(bull_p)
    bear_c = _clamp(bear_p)
    # Derive base from residual so the parameter is not overwritten (S1226).
    base_c = _clamp(base_p if base_p > 0 else (100.0 - bull_c - bear_c))
    # Keep probabilities summing to ~100 when caller passes a residual base.
    if abs((bull_c + base_c + bear_c) - 100.0) > 1.0:
        base_c = _clamp(100.0 - bull_c - bear_c)
    total = bull_c + base_c + bear_c
    if total <= 0:
        total = 1.0
    return 100.0 * bull_c / total, 100.0 * base_c / total, 100.0 * bear_c / total


def _price_ranges(price: float, band: float) -> dict[str, Any]:
    if price <= 0:
        return {"bull": None, "base": None, "bear": None}
    return {
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


def _scenario_drivers(payload: dict[str, Any], score: float, regime: str, verdict: str) -> list[str]:
    drivers: list[str] = []
    explanation = payload.get("explanation")
    if isinstance(explanation, dict):
        factors = explanation.get("top_3_factors")
        if isinstance(factors, list):
            for factor in list(factors)[:3]:
                if isinstance(factor, dict):
                    label = factor.get("factor")
                    if label is None:
                        label = factor.get("label")
                    drivers.append(str(label or ""))
                else:
                    drivers.append(str(factor))
    drivers = [driver for driver in drivers if driver]
    if len(drivers) > 3:
        drivers = drivers[:3]
    if drivers:
        return drivers
    return [f"Opportunity score {score:.0f}", f"Regime {regime}", f"Verdict {verdict}"]


def _scenario_risks(*, abstain: bool, conf: float) -> list[str]:
    risks = []
    if abstain:
        risks.append("Dimension conflict — system prefers WAIT")
    if conf < 45:
        risks.append("Low model confidence — ranges are wider")
    risks.append("Probabilistic sketch only — not a forecast guarantee")
    return risks


def build_oracle_scenarios(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach three scenarios with approximate probabilities and ranges."""
    price = _float_payload(payload, "price", 0.0)
    score = _float_payload(payload, "opportunity_score", 50.0)
    conf = _float_payload(payload, "confidence", 50.0)

    verdict = str(payload.get("decision_action") or payload.get("verdict") or "WAIT").upper()
    regime = str(payload.get("market_regime") or payload.get("regime") or "unknown")
    conflict = payload.get("dimension_conflict") or {}
    abstain = bool(conflict.get("veto") or conflict.get("abstain"))

    bull_p, base_p, bear_p = _scenario_probabilities(verdict, score, abstain)

    # Confidence widens/narrows dispersion
    scale = 0.7 + (conf / 100.0) * 0.6
    bull_p, base_p, bear_p = _normalize_probabilities(
        bull_p * scale / max(scale, 0.01),
        base_p,
        bear_p * scale / max(scale, 0.01),
    )

    # Expected range band grows when confidence is low
    band = max(0.8, (100.0 - conf) / 100.0 * 6.0 + 1.2)  # percent
    ranges = _price_ranges(price, band)
    drivers = _scenario_drivers(payload, score, regime, verdict)
    risks = _scenario_risks(abstain=abstain, conf=conf)

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
                "drivers": _safe_head(drivers, 2),
                "risks": _safe_head(risks, 2),
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
                "drivers": _safe_head(drivers, 2),
                "risks": _safe_head(risks, 2),
            },
        },
        "confidence_pct": round(conf, 1),
    }
