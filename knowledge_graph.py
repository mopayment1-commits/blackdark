"""Phase 2 — Knowledge Graph: link assets, signals, decisions, outcomes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from compounding_common import dumps_json, loads_json, row_signature, utcnow, verify_row_signature
from audit_registry import hash_payload

logger = logging.getLogger("BLACKDARK.KnowledgeGraph")

NODE_TYPES = frozenset({"Asset", "Signal", "Decision", "Outcome", "User"})
EDGE_TYPES = frozenset({"predicted", "resulted_in", "influenced_by"})

_NODE_SIGN = ("node_id", "node_type", "label", "properties_json", "timestamp", "version")
_EDGE_SIGN = ("edge_id", "source_node_id", "target_node_id", "edge_type", "properties_json", "timestamp")


async def create_node(
    *,
    node_type: str,
    label: str | None = None,
    properties: dict[str, Any] | None = None,
    node_id: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    ntype = str(node_type)
    if ntype not in NODE_TYPES:
        raise ValueError(f"invalid node_type: {node_type}")

    nid = node_id or f"node_{uuid4().hex[:14]}"
    props = dumps_json(properties or {})
    row = {
        "node_id": nid,
        "node_type": ntype,
        "label": label or nid,
        "properties_json": props,
        "timestamp": utcnow(),
        "version": 1,
    }
    row["signature"] = row_signature(row, _NODE_SIGN)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO kg_nodes (node_id, node_type, label, properties_json, timestamp, version, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["node_id"],
                row["node_type"],
                row["label"],
                row["properties_json"],
                row["timestamp"],
                row["version"],
                row["signature"],
            ),
        )
    return _node_api(row)


async def create_edge(
    *,
    source_node_id: str,
    target_node_id: str,
    edge_type: str,
    properties: dict[str, Any] | None = None,
    edge_id: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    etype = str(edge_type)
    if etype not in EDGE_TYPES:
        raise ValueError(f"invalid edge_type: {edge_type}")

    eid = edge_id or f"edge_{uuid4().hex[:14]}"
    props = dumps_json(properties or {})
    row = {
        "edge_id": eid,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "edge_type": etype,
        "properties_json": props,
        "timestamp": utcnow(),
    }
    row["signature"] = row_signature(row, _EDGE_SIGN)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO kg_edges (
                edge_id, source_node_id, target_node_id, edge_type, properties_json, timestamp, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["edge_id"],
                row["source_node_id"],
                row["target_node_id"],
                row["edge_type"],
                row["properties_json"],
                row["timestamp"],
                row["signature"],
            ),
        )
    return _edge_api(row)


async def get_node(node_id: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        result = await db.execute(
            "SELECT * FROM kg_nodes WHERE node_id = ?",
            (node_id,),
        )
        raw = await result.fetchone()
    return _node_api(dict(raw)) if raw else None


async def ingest_decision(decision: dict[str, Any]) -> dict[str, Any]:
    """Auto-ingest Phase 1 decision into knowledge graph."""
    decision_id = str(decision.get("decision_id") or "")
    context = decision.get("context") or {}
    prediction = decision.get("prediction") or {}
    symbol = str(context.get("symbol") or prediction.get("symbol") or "UNKNOWN").upper()

    asset_nid = f"asset_{symbol}"
    existing_asset = await get_node(asset_nid)
    if not existing_asset:
        await create_node(
            node_id=asset_nid,
            node_type="Asset",
            label=symbol,
            properties={"symbol": symbol},
        )

    decision_nid = f"decision_{decision_id}"
    dnode = await get_node(decision_nid)
    if not dnode:
        await create_node(
            node_id=decision_nid,
            node_type="Decision",
            label=decision_id,
            properties={
                "decision_id": decision_id,
                "context": context,
                "prediction": prediction,
                "confidence": decision.get("confidence"),
                "outcome": decision.get("outcome"),
                "version": decision.get("version"),
            },
        )
        await create_edge(
            source_node_id=decision_nid,
            target_node_id=asset_nid,
            edge_type="predicted",
            properties={"symbol": symbol},
        )

    if str(decision.get("outcome") or "") in {"verified", "rejected"}:
        outcome_nid = f"outcome_{decision_id}_v{decision.get('version', 1)}"
        if not await get_node(outcome_nid):
            await create_node(
                node_id=outcome_nid,
                node_type="Outcome",
                label=outcome_nid,
                properties={"outcome": decision.get("outcome"), "decision_id": decision_id},
            )
            await create_edge(
                source_node_id=decision_nid,
                target_node_id=outcome_nid,
                edge_type="resulted_in",
            )
    return {"decision_id": decision_id, "asset_node": asset_nid, "decision_node": decision_nid}


async def query_graph(
    *,
    symbol: str | None = None,
    node_type: str | None = None,
    days: int = 30,
    decision_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    from database import get_connection

    cutoff = (datetime.now(UTC) - timedelta(days=max(1, days))).isoformat()
    clauses = ["timestamp >= ?"]
    params: list[Any] = [cutoff]

    if node_type:
        clauses.append("node_type = ?")
        params.append(node_type)
    if decision_id:
        clauses.append("(node_id = ? OR properties_json LIKE ?)")
        params.extend([f"decision_{decision_id}", f"%{decision_id}%"])
    if symbol:
        sym = symbol.upper()
        clauses.append("(label = ? OR properties_json LIKE ?)")
        params.extend([sym, f"%{sym}%"])

    where = " AND ".join(clauses)
    params.append(max(1, min(limit, 500)))

    async with get_connection() as db:
        nodes_result = await db.execute(
            f"""
            SELECT node_id, node_type, label, properties_json, timestamp, version, signature
            FROM kg_nodes WHERE {where}
            ORDER BY timestamp DESC LIMIT ?
            """,
            tuple(params),
        )
        nodes = [_node_api(dict(r)) for r in await nodes_result.fetchall()]
        node_ids = [n["node_id"] for n in nodes]
        edges: list[dict[str, Any]] = []
        if node_ids:
            placeholders = ",".join("?" for _ in node_ids)
            edges_result = await db.execute(
                f"""
                SELECT edge_id, source_node_id, target_node_id, edge_type,
                       properties_json, timestamp, signature
                FROM kg_edges
                WHERE source_node_id IN ({placeholders}) OR target_node_id IN ({placeholders})
                """,
                tuple(node_ids + node_ids),
            )
            edges = [_edge_api(dict(r)) for r in await edges_result.fetchall()]

    return {
        "query": {
            "symbol": symbol,
            "node_type": node_type,
            "days": days,
            "decision_id": decision_id,
        },
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


async def graph_stats() -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        n = await (await db.execute("SELECT COUNT(*) FROM kg_nodes")).fetchone()
        e = await (await db.execute("SELECT COUNT(*) FROM kg_edges")).fetchone()
    return {
        "nodes": int(list(n.values())[0] if isinstance(n, dict) else n[0]),
        "edges": int(list(e.values())[0] if isinstance(e, dict) else e[0]),
    }


def _node_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "node_id": row.get("node_id"),
        "node_type": row.get("node_type"),
        "label": row.get("label"),
        "properties": loads_json(row.get("properties_json")),
        "timestamp": row.get("timestamp"),
        "version": row.get("version", 1),
        "signature": row.get("signature"),
    }
    api["signature_valid"] = verify_row_signature({**row, **api}, _NODE_SIGN)
    return api


def _edge_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "edge_id": row.get("edge_id"),
        "source_node_id": row.get("source_node_id"),
        "target_node_id": row.get("target_node_id"),
        "edge_type": row.get("edge_type"),
        "properties": loads_json(row.get("properties_json")),
        "timestamp": row.get("timestamp"),
        "signature": row.get("signature"),
    }
    api["signature_valid"] = verify_row_signature({**row, **api}, _EDGE_SIGN)
    return api
