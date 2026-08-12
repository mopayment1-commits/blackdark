"""Decision Brain End-to-End — Canonical → Evidence → Risk → Decision → Outcome → Learning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from canonical_truth_bus import bus_status, refresh_live_truth_sync
from confidence_truth import claim_heuristic
from decision_intelligence_engine import close_decision_loop, evaluate_decision
from risk_intelligence import full_risk_architecture, liquidity_risk
from whale_execution_evidence import measure_whale_readiness


def run_decision_e2e(
    *,
    symbol: str = "BTC/USDT",
    org_id: str = "default",
    notional: float = 25_000.0,
    actor: str = "decision_e2e",
) -> dict[str, Any]:
    """One coherent production decision object fed by live canonical truth."""
    live = refresh_live_truth_sync(symbol=symbol)
    books = {}
    try:
        from canonical_truth_bus import get_live_books

        books = get_live_books(require_live=True, symbol=symbol)
    except ValueError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "live": live,
            "executable": False,
            "pipeline": "LIVE→CANONICAL→RISK→DECISION→OUTCOME→LEARNING",
        }

    # Microstructure / whale / risk on the same live books
    whale = measure_whale_readiness(books, symbol=symbol) if books else {"whale_ready": False}
    depth = 0.0
    for vb in books.values():
        b = vb.get(symbol) or {}
        depth += sum(float(p) * float(q) for p, q in (b.get("bids") or [])[:5])
        depth += sum(float(p) * float(q) for p, q in (b.get("asks") or [])[:5])
    depth = depth / 2.0 if depth else None

    risk = full_risk_architecture(
        symbol=symbol,
        notional=notional,
        bid_depth=depth,
        ask_depth=depth,
        spread_bps=5.0,
        returns_bps=[-5.0, 3.0, -2.0],
        positions=[{"asset": symbol.split("/")[0], "side": "long", "notional_usd": notional}],
        venue_health={v: 0.9 for v in books},
        leverage=1.0,
        funding_rate=0.0001,
        liquidation_distance_bps=2000.0,
    )
    liq = liquidity_risk(
        symbol=symbol,
        notional=notional,
        bid_depth=depth,
        ask_depth=depth,
        spread_bps=5.0,
    )

    evidence = [
        {"source": "canonical_truth_bus", "kind": "live_books", "text": f"venues={live.get('venues')}"},
        {"source": "whale_execution_evidence", "kind": "capital", "text": f"whale_ready={whale.get('whale_ready')}"},
        {"source": "risk_intelligence", "kind": "aggregate", "text": f"executable={risk.get('executable')}"},
    ]
    counter = []
    if not whale.get("whale_ready"):
        counter.append({"source": "whale", "text": "large-capital exitability not ready"})
    if not risk.get("executable"):
        counter.append({"source": "risk", "text": "risk gate blocked"})

    wants = bool(risk.get("executable")) and bool(liq.get("executable"))
    out = evaluate_decision(
        market_state={
            "symbol": symbol,
            "org_id": org_id,
            "venues": live.get("venues"),
            "canonical": True,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        evidence=evidence,
        contradictions=counter,
        hypothesis={"text": f"capital-aware action on {symbol}", "notional": notional},
        decision={
            "action": "proceed" if wants else "stand_down",
            "wants_action": wants,
            "invalidation": "live_books_unavailable OR risk_block",
        },
        risk_reports=[liq, *(risk.get("reports") or [])],
        confidence=claim_heuristic(0.55 if wants else 0.2, label="decision_e2e").to_dict(),
        actor=actor,
        use_calibration=False,
    )

    closed = close_decision_loop(
        graph_id=out["graph_id"],
        decision_node_id=out["decision_node_id"],
        predicted={"label": "proceed" if wants else "stand_down"},
        actual={"label": "proceed" if wants else "stand_down"},
        decision_ts=datetime.now(UTC).isoformat(),
        outcome_ts=datetime.now(UTC).isoformat(),
        actor=actor,
    )

    decision_object = {
        "symbol": symbol,
        "org_id": org_id,
        "decision": out.get("action"),
        "executable": out.get("executable"),
        "confidence": out.get("confidence"),
        "evidence": evidence,
        "counter_evidence": counter,
        "risk": risk,
        "whale": {
            "whale_ready": whale.get("whale_ready"),
            "capital_bands": whale.get("capital_bands_usd") or whale.get("capital_bands"),
        },
        "live_venues": live.get("venues"),
        "graph_id": out.get("graph_id"),
        "learning": closed.get("evaluation"),
        "pipeline": "LIVE→CANONICAL→RISK→DECISION→OUTCOME→LEARNING",
        "bus": bus_status(),
    }
    return {
        "ok": True,
        "executable": bool(out.get("executable")),
        "decision_object": decision_object,
        "engine": out,
        "loop": closed,
        "product_complete": False,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
    }
