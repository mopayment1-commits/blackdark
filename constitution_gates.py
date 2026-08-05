"""
BLACKDARK — Constitution gate helpers (binding Product Constitution).

Applies D2 Contradiction Veto, D4 Half-Life kill, and D8 Signal Registry
annotation on opportunity rows after D3 Net-Edge Truth.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.ConstitutionGates")

HALF_LIFE_REMAIN_KILL_SEC = 2.0
HALF_LIFE_DISAPPEAR_KILL = 0.92


def _mark_not_executable(row: dict[str, Any], reason: str) -> None:
    row["execution_feasibility"] = "not_executable"
    risks = list(row.get("risk_factors") or [])
    if reason not in risks:
        risks.append(reason)
    row["risk_factors"] = risks


def apply_half_life_kill(row: dict[str, Any]) -> dict[str, Any]:
    """D4: kill opportunities that are already dead or nearly gone."""
    half = row.get("opportunity_half_life") or {}
    try:
        remain = float(half.get("remaining_seconds"))
    except (TypeError, ValueError):
        remain = None
    try:
        p_gone = float(half.get("disappearance_probability") or 0.0)
    except (TypeError, ValueError):
        p_gone = 0.0

    killed = False
    if remain is not None and remain <= HALF_LIFE_REMAIN_KILL_SEC:
        killed = True
    if p_gone >= HALF_LIFE_DISAPPEAR_KILL:
        killed = True
    if killed:
        row["half_life_killed"] = True
        _mark_not_executable(row, "half_life_kill")
    return row


def apply_contradiction_veto(
    row: dict[str, Any],
    *,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """D2: attach dimension_conflict and fail-closed on veto/abstain."""
    try:
        from dimension_conflict_guard import apply_dimension_conflict_guard
        from weight_aggregator import compute_modal_breakdown

        asset = str(row.get("asset") or "BTC")
        breakdown = compute_modal_breakdown(asset, institutional_context)
        score_proxy = float(row.get("confidence_percent") or row.get("opportunity_score") or 50)
        _, conflict_meta = apply_dimension_conflict_guard(score_proxy, breakdown)
        row["dimension_conflict"] = conflict_meta
        row["market_regime"] = breakdown.get("market_regime")
        if conflict_meta.get("veto") or conflict_meta.get("abstain"):
            row["conflict_vetoed"] = bool(conflict_meta.get("veto"))
            row["conflict_abstain"] = bool(conflict_meta.get("abstain"))
            _mark_not_executable(row, "dimension_conflict_veto")
    except Exception:
        logger.debug("contradiction veto on row failed", exc_info=True)
        row.setdefault("dimension_conflict", {"severity": "none", "veto": False, "abstain": False})
    return row


def register_opportunity_signal(row: dict[str, Any]) -> dict[str, Any]:
    """D8: persist labeled lexicon row for moat (best-effort)."""
    try:
        from signal_registry import register_from_evaluation

        reg = register_from_evaluation(
            {
                "kind": row.get("kind") or "arbitrage",
                "asset": row.get("asset") or "BTC",
                "opportunity_score": row.get("confidence_percent") or row.get("opportunity_score") or 0,
                "net_profit_usdt": row.get("net_profit_usdt") or 0,
                "oracle": {"verdict": "Buy Now" if row.get("execution_feasibility") in {"full", "partial"} else "Do Not Touch"},
                "payload": row,
            }
        )
        row["signal_registry"] = {
            "signal_id": reg.get("signal_id"),
            "features_hash": reg.get("features_hash"),
            "label": reg.get("label"),
        }
    except Exception:
        logger.debug("signal registry on row failed", exc_info=True)
    return row


def apply_constitution_gates_to_scan(
    rows: list[dict[str, Any]],
    *,
    institutional_context: dict[str, Any] | None = None,
    register_limit: int = 12,
) -> list[dict[str, Any]]:
    """
    Post Net-Edge constitution stack for live arb scan:
      Half-Life kill → Contradiction Veto → Signal Registry (top N)
    """
    out: list[dict[str, Any]] = []
    registered = 0
    for row in rows:
        r = dict(row)
        apply_half_life_kill(r)
        apply_contradiction_veto(r, institutional_context=institutional_context)
        # Register candidates that still look real (or vetoed/rejected for labeled corpus).
        if registered < register_limit:
            register_opportunity_signal(r)
            registered += 1
        out.append(r)
    return out


def is_alertable(row: dict[str, Any]) -> bool:
    """True when constitution gates allow alerting / auto-exec consideration."""
    if row.get("execution_feasibility") == "not_executable":
        return False
    if row.get("truth_rejected") or (row.get("net_edge_truth") or {}).get("reject"):
        return False
    if row.get("half_life_killed"):
        return False
    conflict = row.get("dimension_conflict") or {}
    if conflict.get("veto") or conflict.get("abstain"):
        return False
    return True


def ensure_execution_gates(opportunity: dict[str, Any]) -> dict[str, Any]:
    """
    Fail-closed for execution: recompute missing Truth / Half-Life / Conflict.
    Mutates and returns the opportunity dict.
    """
    opp = dict(opportunity)

    if not isinstance(opp.get("net_edge_truth"), dict) or "reject" not in (opp.get("net_edge_truth") or {}):
        try:
            from net_edge_truth import compute_net_edge_truth

            opp["net_edge_truth"] = compute_net_edge_truth(opp)
        except Exception:
            opp["net_edge_truth"] = {"enabled": False, "reject": True, "error": "unavailable"}
            opp["gates_missing"] = True

    if not isinstance(opp.get("opportunity_half_life"), dict) or opp.get("opportunity_half_life", {}).get(
        "remaining_seconds"
    ) is None:
        try:
            from opportunity_tracker import estimate_opportunity_half_life

            opp["opportunity_half_life"] = estimate_opportunity_half_life(opp)
        except Exception:
            opp["opportunity_half_life"] = {
                "remaining_seconds": 0,
                "disappearance_probability": 1.0,
                "error": "unavailable",
            }
            opp["gates_missing"] = True

    if not isinstance(opp.get("dimension_conflict"), dict):
        apply_contradiction_veto(opp)

    apply_half_life_kill(opp)
    return opp
