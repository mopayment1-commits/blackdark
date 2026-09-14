"""DTS-025 — Six Heroes default from canonical Decision Truth outputs."""

from __future__ import annotations

from typing import Any


HERO_KEYS = (
    "my_capital",
    "market_state",
    "best_verified_opportunity",
    "main_risk",
    "smart_money_evidence",
    "todays_decision_brief",
)


def build_six_heroes(payload: dict[str, Any]) -> dict[str, Any]:
    """Project Six Heroes from governed payload — no recomputation."""
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    state = str(payload.get("decision_truth_state") or contract.get("decision_state") or "UNAVAILABLE")
    portfolio = payload.get("portfolio_summary") or payload.get("portfolio_risk") or {}
    lifecycle = ((payload.get("decision_truth") or {}).get("evidence_lifecycle") or {})

    heroes = {
        "my_capital": _hero(
            "my_capital",
            portfolio if portfolio else None,
            unavailable_reason="portfolio_not_connected" if not portfolio else None,
        ),
        "market_state": _hero(
            "market_state",
            _market_state(payload),
            unavailable_reason=None if payload.get("symbol") else "market_context_unavailable",
        ),
        "best_verified_opportunity": _hero(
            "best_verified_opportunity",
            _best_opportunity(payload, state, contract) if state == "AVAILABLE" else None,
            unavailable_reason="no_admitted_opportunity" if state != "AVAILABLE" else None,
            degraded=state == "DEGRADED",
        ),
        "main_risk": _hero(
            "main_risk",
            _main_risk(contract, payload),
            unavailable_reason="risk_context_unavailable" if not contract.get("risk") else None,
        ),
        "smart_money_evidence": _hero(
            "smart_money_evidence",
            _smart_money_hero(payload, lifecycle),
            unavailable_reason="smart_money_unavailable" if not payload.get("smart_money_context") else None,
        ),
        "todays_decision_brief": _hero(
            "todays_decision_brief",
            _brief_hero(payload),
            unavailable_reason="daily_brief_unavailable",
        ),
    }
    return {
        "heroes": heroes,
        "hero_keys": list(HERO_KEYS),
        "derived_from": "canonical_decision_truth",
        "no_ui_recomputation": True,
        "methodology_version": "dts-p5-six-heroes-1.0",
    }


def _hero(
    key: str,
    data: dict[str, Any] | None,
    *,
    unavailable_reason: str | None = None,
    degraded: bool = False,
) -> dict[str, Any]:
    if data is None:
        return {
            "hero": key,
            "state": "UNAVAILABLE",
            "unavailable_reason": unavailable_reason or "data_unavailable",
            "data": None,
        }
    if degraded:
        return {"hero": key, "state": "DEGRADED", "data": data}
    return {"hero": key, "state": "AVAILABLE", "data": data}


def _market_state(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": payload.get("symbol"),
        "regime": payload.get("regime") or payload.get("market_regime"),
        "freshness": ((payload.get("decision_truth") or {}).get("contract") or {}).get("freshness"),
        "evidence_class": ((payload.get("decision_truth") or {}).get("contract") or {}).get("evidence_class"),
    }


def _best_opportunity(payload: dict[str, Any], state: str, contract: dict[str, Any]) -> dict[str, Any]:
    net = contract.get("net_edge") or payload.get("net_edge_truth") or {}
    return {
        "symbol": payload.get("symbol"),
        "decision_state": state,
        "expected_net_edge_bps": net.get("expected_net_edge_bps"),
        "grade": contract.get("grade"),
        "evidence_class": contract.get("evidence_class"),
        "execution_score": (contract.get("execution_feasibility") or {}).get("score"),
    }


def _main_risk(contract: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    risk = contract.get("risk") or {}
    pre = risk.get("portfolio_pre_impact") or risk.get("pre_impact") or payload.get("portfolio_pre_impact")
    return {
        "risk_ok": risk.get("ok"),
        "pre_impact": pre,
        "reverse_stress": risk.get("reverse_stress"),
        "invalidation_condition": contract.get("invalidation_condition"),
    }


def _smart_money_hero(payload: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any] | None:
    sm = payload.get("smart_money_context")
    if not sm and not lifecycle.get("provenance"):
        return None
    return {
        "context_only": True,
        "smart_money": sm,
        "evidence_grade": ((payload.get("decision_truth") or {}).get("contract") or {}).get("grade"),
        "note": "Context for decision — not standalone truth claim",
    }


def _brief_hero(payload: dict[str, Any]) -> dict[str, Any] | None:
    changes = payload.get("material_changes")
    if not changes and not payload.get("decision_truth"):
        return None
    return {
        "material_changes_count": len(changes or []),
        "decision_state": payload.get("decision_truth_state"),
        "has_governed_decision": bool(payload.get("decision_truth")),
    }
