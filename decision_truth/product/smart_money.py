"""DTS-031 / DTS-032 — Smart Money context with attribution confidence."""

from __future__ import annotations

from typing import Any


def build_smart_money_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach smart money as decision context, not standalone truth."""
    raw = payload.get("smart_money_context") or payload.get("whale_context") or {}
    symbol = payload.get("symbol")

    attributions: list[dict[str, Any]] = []
    for key in ("wallet", "whale", "cluster", "fund", "exchange_wallet"):
        entry = raw.get(key) or raw.get(f"{key}_attribution")
        if entry:
            attributions.append(_normalize_attribution(key, entry))

    if not attributions and raw.get("attributions"):
        for item in raw.get("attributions") or []:
            if isinstance(item, dict):
                attributions.append(_normalize_attribution(str(item.get("type") or "unknown"), item))

    context_links = {
        "funding": raw.get("funding") or payload.get("funding_context"),
        "exchange_flows": raw.get("exchange_flows"),
        "price_reaction": raw.get("price_reaction") or {"note": "association_only"},
        "liquidity": (payload.get("decision_truth") or {}).get("contract", {}).get("execution_feasibility"),
        "sentiment": raw.get("sentiment") if raw.get("sentiment_defensible") else None,
        "prior_behavior": raw.get("prior_behavior"),
    }

    return {
        "context_only": True,
        "not_standalone_decision_driver": True,
        "symbol": symbol,
        "attributions": attributions,
        "context_links": context_links,
        "methodology_version": "dts-p5-smart-money-1.0",
        "derived_from": "canonical_context_attachment",
    }


def _normalize_attribution(kind: str, entry: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(entry, str):
        entry = {"label": entry}
    confidence = entry.get("confidence")
    if confidence is None and entry.get("confidence_percent") is not None:
        confidence = float(entry["confidence_percent"]) / 100.0
    state = "AVAILABLE" if confidence is not None and float(confidence) >= 0.5 else "ATTRIBUTION_UNCERTAIN"
    if confidence is None:
        state = "ATTRIBUTION_UNCERTAIN"
    return {
        "type": kind,
        "label": entry.get("label") or entry.get("name"),
        "confidence": confidence,
        "confidence_state": state,
        "source": entry.get("source") or "unknown",
        "provenance": entry.get("provenance") or {},
        "freshness": entry.get("freshness") or entry.get("as_of"),
        "methodology_version": entry.get("methodology_version"),
        "uncertainty_state": entry.get("uncertainty_state") or ("high" if state == "ATTRIBUTION_UNCERTAIN" else "moderate"),
    }
