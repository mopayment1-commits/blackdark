"""
BLACKDARK — Data lineage visualization for a recommendation/decision.
"""

from __future__ import annotations

from typing import Any


async def build_lineage_graph(*, symbol: str, decision_id: str | None = None) -> dict[str, Any]:
    """Trace source → normalization → model → UI for one symbol/decision."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    def add_node(node_id: str, label: str, node_type: str, meta: dict | None = None) -> None:
        nodes.append({"id": node_id, "label": label, "type": node_type, "meta": meta or {}})

    def add_edge(src: str, dst: str, label: str) -> None:
        edges.append({"from": src, "to": dst, "label": label})

    add_node("src_cex", "CEX feeds (Binance/OKX/Bybit)", "source")
    add_node("ingest", "aggregator.py + live_book_hub", "ingestion")
    add_node("norm", "exchange_adapters + canonical schema", "normalization")
    add_node("store", "pricing_logs / market_cache", "storage")
    add_node("engine", "oracle_unified.py", "engine")
    add_node("guard", "dimension_conflict_guard + regulatory_compliance_guard", "policy")
    add_node("ui", f"/oracle/{symbol.split('/')[0]}", "ui")

    add_edge("src_cex", "ingest", "REST/WS")
    add_edge("ingest", "norm", "normalize")
    add_edge("norm", "store", "persist/cache")
    add_edge("store", "engine", "features")
    add_edge("engine", "guard", "verdict")
    add_edge("guard", "ui", "render")

    provenance: dict[str, Any] = {}
    try:
        from data_provenance_score import compute_data_provenance_score

        provenance = compute_data_provenance_score(symbol=symbol)
        add_node("prov", "data_provenance_score", "provenance", provenance)
        add_edge("store", "prov", "score")
        add_edge("prov", "engine", "weight")
    except Exception:
        pass

    if decision_id:
        add_node("decision", decision_id, "decision")
        add_edge("engine", "decision", "certificate")
        add_edge("decision", "ui", "display")

    return {
        "symbol": symbol,
        "decision_id": decision_id,
        "nodes": nodes,
        "edges": edges,
        "provenance": provenance,
    }
