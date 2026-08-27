"""
Decision Graph (#47) — interactive causal graph from live platform data.

NOT a static flowchart. Builds AI-linked causal chains:
"Fed macro stress → whale sell pressure → liquidation cascade → BTC -5%"

Requirements: interactive nodes, real data (#48 inputs), causal edges, ≤2s SLA.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.DecisionGraph")

CAUSAL_EDGE_TYPES = frozenset({"because", "then", "influenced", "triggered", "resulted_in"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _node(
    *,
    node_id: str,
    node_type: str,
    label: str,
    category: str,
    detail: dict[str, Any] | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "label": label,
        "category": category,
        "detail": detail or {},
        "confidence": confidence,
        "clickable": True,
        "interactive": True,
    }


def _edge(
    *,
    source: str,
    target: str,
    relation: str,
    label: str | None = None,
    weight: float | None = None,
) -> dict[str, Any]:
    rel = relation if relation in CAUSAL_EDGE_TYPES else "influenced"
    return {
        "from": source,
        "to": target,
        "relation": rel,
        "label": label or rel,
        "weight": weight,
        "causal": True,
    }


def _evidence_nodes_from_inputs(inputs: dict[str, Any], asset: str) -> tuple[list[dict], list[dict], str | None]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root_evidence: str | None = None

    macro = inputs.get("twelvedata_macro") or inputs.get("macro_context") or {}
    if macro.get("ok"):
        nid = f"ev_macro_{asset.lower()}"
        headline = macro.get("correlation_narrative") or macro.get("headline") or "Macro context"
        nodes.append(
            _node(
                node_id=nid,
                node_type="evidence",
                label=str(headline)[:120],
                category="macro",
                detail={"quotes": macro.get("quotes"), "source": "twelvedata_macro"},
                confidence=0.75,
            )
        )
        root_evidence = nid

    ofi = inputs.get("order_flow_intelligence") or {}
    if ofi.get("ok") and ofi.get("headline"):
        nid = f"ev_flow_{asset.lower()}"
        nodes.append(
            _node(
                node_id=nid,
                node_type="evidence",
                label=str(ofi["headline"])[:120],
                category="order_flow",
                detail={"taker_buy_ratio": ofi.get("taker_buy_ratio"), "reversal_prob": ofi.get("reversal_probability")},
                confidence=0.7,
            )
        )
        if root_evidence:
            edges.append(_edge(source=nid, target=root_evidence, relation="because", label="amplifies macro move"))
        else:
            root_evidence = nid

    flows = inputs.get("exchange_flows") or {}
    if flows.get("ok") and flows.get("headline"):
        nid = f"ev_onchain_{asset.lower()}"
        nodes.append(
            _node(
                node_id=nid,
                node_type="evidence",
                label=str(flows["headline"])[:120],
                category="on_chain",
                detail={"netflow_usd": flows.get("netflow_usd"), "risk_delta": flows.get("risk_score_delta")},
                confidence=0.8,
            )
        )
        if root_evidence:
            edges.append(_edge(source=nid, target=root_evidence, relation="because", label="on-chain pressure"))
        else:
            root_evidence = nid

    news = inputs.get("news_context") or {}
    if news.get("ok") and news.get("ai_context_line"):
        nid = f"ev_news_{asset.lower()}"
        nodes.append(
            _node(
                node_id=nid,
                node_type="evidence",
                label=str(news["ai_context_line"])[:120],
                category="news",
                detail={"high_impact_count": len([a for a in (news.get("articles") or []) if a.get("high_impact")])},
                confidence=0.65,
            )
        )
        if root_evidence:
            edges.append(_edge(source=nid, target=root_evidence, relation="triggered", label="news catalyst"))

    cvd = inputs.get("futures_cvd") or {}
    if cvd.get("ok") and cvd.get("headline"):
        nid = f"ev_cvd_{asset.lower()}"
        nodes.append(
            _node(
                node_id=nid,
                node_type="evidence",
                label=str(cvd["headline"])[:120],
                category="derivatives",
                detail={"cvd_trend": cvd.get("cvd_trend")},
                confidence=0.72,
            )
        )
        if root_evidence:
            edges.append(_edge(source=nid, target=root_evidence, relation="influenced", label="futures positioning"))

    return nodes, edges, root_evidence


async def build_causal_decision_graph(
    *,
    asset: str = "BTC",
    focus_node: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Interactive causal decision graph — evidence → decision → outcome chain.
    """
    t0 = time.perf_counter()
    sym = asset.upper()

    from bd_platform.decision_engine_inputs import gather_decision_inputs

    inputs = await gather_decision_inputs(sym)
    evidence_nodes, evidence_edges, root_ev = _evidence_nodes_from_inputs(inputs, sym)

    nodes = list(evidence_nodes)
    edges = list(evidence_edges)

    decision_nid = f"decision_{sym.lower()}"
    risk_delta = float(inputs.get("risk_score_delta") or 0)
    verdict = "elevated_risk" if risk_delta >= 1.5 else "neutral" if risk_delta <= 0.5 else "caution"
    decision_label = f"AI decision context for {sym}: {verdict.replace('_', ' ')}"
    nodes.append(
        _node(
            node_id=decision_nid,
            node_type="decision",
            label=decision_label,
            category="decision",
            detail={
                "asset": sym,
                "risk_score_delta": risk_delta,
                "headlines": inputs.get("headlines") or [],
                "verdict": verdict,
            },
            confidence=min(0.95, 0.6 + risk_delta * 0.1),
        )
    )
    if root_ev:
        edges.append(_edge(source=root_ev, target=decision_nid, relation="then", label="leads to decision"))
    else:
        for ev in evidence_nodes[:3]:
            edges.append(_edge(source=ev["id"], target=decision_nid, relation="influenced"))

    outcome_nid = f"outcome_{sym.lower()}"
    try:
        from database import fetch_labeled_oracle_predictions

        labeled = await fetch_labeled_oracle_predictions(limit=5, include_synthetic=False)
        recent = next(
            (r for r in (labeled or []) if str(r.get("asset") or r.get("symbol") or "").upper().startswith(sym)),
            None,
        )
    except Exception:
        recent = None

    if recent:
        label = recent.get("label") or "pending"
        outcome_label = f"Outcome: {label} — {recent.get('verdict') or recent.get('action') or 'signal'}"
        nodes.append(
            _node(
                node_id=outcome_nid,
                node_type="outcome",
                label=outcome_label[:120],
                category="outcome",
                detail={"label": label, "prediction_id": recent.get("id") or recent.get("prediction_id")},
                confidence=0.9 if label == "correct" else 0.5,
            )
        )
        edges.append(_edge(source=decision_nid, target=outcome_nid, relation="resulted_in", label="observed outcome"))

    narrative_parts: list[str] = []
    for ev in evidence_nodes[:2]:
        narrative_parts.append(ev["label"])
    if narrative_parts:
        narrative = " → ".join(narrative_parts) + f" → {decision_label}"
    else:
        narrative = decision_label

    if focus_node:
        focus = next((n for n in nodes if n["id"] == focus_node), None)
    else:
        focus = nodes[0] if nodes else None

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#47",
        "surface": "decision_graph",
        "asset": sym,
        "interactive": True,
        "causal": True,
        "ai_generated": True,
        "nodes": nodes[:limit],
        "edges": edges[: max(limit, len(edges))],
        "focus_node": focus,
        "narrative": narrative,
        "count_nodes": len(nodes),
        "count_edges": len(edges),
        "data_sources": ["decision_engine_inputs", "oracle_labels", "silent_data_layer"],
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "disclaimer": "Causal graph from live data — educational, not financial advice.",
        "timestamp": _utcnow(),
    }


async def expand_node(*, node_id: str, asset: str = "BTC") -> dict[str, Any]:
    """Interactive click handler — return node detail + downstream causal chain."""
    graph = await build_causal_decision_graph(asset=asset, focus_node=node_id)
    node = next((n for n in graph.get("nodes") or [] if n["id"] == node_id), None)
    if not node:
        return {"ok": False, "error": "node_not_found", "node_id": node_id}
    downstream = [e for e in graph.get("edges") or [] if e.get("from") == node_id]
    upstream = [e for e in graph.get("edges") or [] if e.get("to") == node_id]
    return {
        "ok": True,
        "feature": "#47",
        "node": node,
        "upstream_edges": upstream,
        "downstream_edges": downstream,
        "related_narrative": graph.get("narrative"),
        "timestamp": _utcnow(),
    }
