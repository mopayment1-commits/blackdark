"""Stablecoin de-peg protection (DTS-030)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-depeg-1.0"

DEFAULT_THRESHOLDS = {
    "warning_deviation_pct": 0.35,
    "material_deviation_pct": 0.75,
    "critical_deviation_pct": 1.5,
    "min_duration_sec": 30,
    "min_source_agreement": 2,
}


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _stablecoins(payload: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for token in ("USDT", "USDC", "DAI", "BUSD", "TUSD"):
        if token in str(payload.get("symbol") or payload.get("asset") or "").upper():
            found.append(token)
        if str(payload.get("quote_currency") or "").upper() == token:
            found.append(token)
    explicit = payload.get("stablecoin")
    if explicit:
        found.append(str(explicit).upper())
    return list(dict.fromkeys(found))


def evaluate_depeg_risk(payload: dict[str, Any]) -> dict[str, Any]:
    """Methodology-driven, source-aware depeg assessment."""
    tokens = _stablecoins(payload)
    if not tokens:
        return {
            "state": "NOT_APPLICABLE",
            "reason": "no_stablecoin_exposure_in_opportunity",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    thresholds = dict(DEFAULT_THRESHOLDS)
    if isinstance(payload.get("depeg_thresholds"), dict):
        thresholds.update({k: v for k, v in payload["depeg_thresholds"].items() if v is not None})

    assessments: list[dict[str, Any]] = []
    for token in tokens:
        assessments.append(_assess_token(payload, token, thresholds))

    worst = max(assessments, key=lambda a: {"normal": 0, "warning": 1, "material": 2, "critical": 3, "unavailable": -1}.get(a["risk_band"], 0))
    return {
        "state": worst.get("state", "AVAILABLE"),
        "tokens": assessments,
        "aggregate_risk_band": worst.get("risk_band"),
        "decision_impact": worst.get("decision_impact"),
        "methodology_version": METHODOLOGY_VERSION,
        "thresholds": thresholds,
        "timestamp_utc": _utc_now(),
        "live_validation": "LIVE_VALIDATION_PENDING",
    }


def _assess_token(payload: dict[str, Any], token: str, thresholds: dict[str, Any]) -> dict[str, Any]:
    quotes = payload.get("stablecoin_quotes") or payload.get("depeg_sources") or {}
    token_quotes = quotes.get(token) if isinstance(quotes, dict) else None
    if token_quotes is None:
        price = _optional_float(payload.get("stablecoin_price") or payload.get("peg_price"))
        if price is not None and token in str(payload.get("symbol") or ""):
            token_quotes = [{"source": "opportunity.stablecoin_price", "price": price, "timestamp_utc": _utc_now()}]
        else:
            return {
                "token": token,
                "state": "DEPEG_RISK_UNAVAILABLE",
                "risk_band": "unavailable",
                "decision_impact": "abstain",
                "reason": "insufficient_depeg_source_evidence",
            }

    if not isinstance(token_quotes, list):
        token_quotes = [token_quotes]

    parsed = []
    for row in token_quotes:
        if not isinstance(row, dict):
            continue
        px = _optional_float(row.get("price"))
        if px is None:
            continue
        deviation_pct = abs(px - 1.0) * 100.0
        parsed.append(
            {
                "source": row.get("source") or "unknown",
                "price": px,
                "deviation_pct": round(deviation_pct, 6),
                "timestamp_utc": row.get("timestamp_utc") or _utc_now(),
            }
        )

    if len(parsed) < int(thresholds.get("min_source_agreement", 2)):
        if len(parsed) == 1:
            deviation = parsed[0]["deviation_pct"]
            band, impact = _band(deviation, thresholds)
            return {
                "token": token,
                "state": "AVAILABLE",
                "risk_band": band,
                "decision_impact": impact,
                "sources": parsed,
                "uncertainty": {"state": "HIGH", "reason": "single_source_only"},
            }
        return {
            "token": token,
            "state": "DEPEG_RISK_UNAVAILABLE",
            "risk_band": "unavailable",
            "decision_impact": "abstain",
            "reason": "insufficient_source_agreement",
        }

    deviations = [p["deviation_pct"] for p in parsed]
    if max(deviations) - min(deviations) > thresholds["warning_deviation_pct"]:
        return {
            "token": token,
            "state": "AVAILABLE",
            "risk_band": "warning",
            "decision_impact": "degrade",
            "sources": parsed,
            "reason_codes": ["conflicting_depeg_sources"],
        }

    deviation = sum(deviations) / len(deviations)
    band, impact = _band(deviation, thresholds)
    return {
        "token": token,
        "state": "AVAILABLE",
        "risk_band": band,
        "decision_impact": impact,
        "sources": parsed,
        "deviation_pct": round(deviation, 6),
    }


def _band(deviation_pct: float, thresholds: dict[str, Any]) -> tuple[str, str]:
    if deviation_pct >= thresholds["critical_deviation_pct"]:
        return "critical", "reject"
    if deviation_pct >= thresholds["material_deviation_pct"]:
        return "material", "abstain"
    if deviation_pct >= thresholds["warning_deviation_pct"]:
        return "warning", "degrade"
    return "normal", "none"
