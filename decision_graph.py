"""Decision Graph — auditable MARKET→…→OUTCOME→LEARNING chain."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from confidence_truth import sanitize_confidence_field
from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("decision_graph.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"

NODE_KINDS = (
    "MARKET_STATE",
    "EVIDENCE",
    "CONTRADICTION",
    "HYPOTHESIS",
    "DECISION",
    "RISK",
    "EXECUTION_FEASIBILITY",
    "ACTION",
    "OUTCOME",
    "LEARNING",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append(row: dict[str, Any]) -> dict[str, Any]:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    try:
        from institutional_store import decision_append_sync

        decision_append_sync(row)
    except Exception:
        pass
    return row


def create_graph(*, market_state: dict[str, Any], actor: str = "system") -> dict[str, Any]:
    gid = f"dg_{uuid.uuid4().hex[:16]}"
    row = {
        "graph_id": gid,
        "kind": "MARKET_STATE",
        "payload": market_state,
        "parent_ids": [],
        "actor": actor,
        "created_at": _utcnow(),
    }
    return _append(row)


def add_node(
    graph_id: str,
    *,
    kind: str,
    payload: dict[str, Any],
    parent_ids: list[str] | None = None,
    confidence: Any = None,
    actor: str = "system",
) -> dict[str, Any]:
    kind = kind.strip().upper()
    if kind not in NODE_KINDS:
        raise ValueError(f"invalid_node_kind:{kind}")
    node_id = f"dn_{uuid.uuid4().hex[:16]}"
    body = dict(payload)
    if confidence is not None or "confidence" in body:
        body["confidence"] = sanitize_confidence_field(confidence if confidence is not None else body.get("confidence"))
    row = {
        "graph_id": graph_id,
        "node_id": node_id,
        "kind": kind,
        "payload": body,
        "parent_ids": list(parent_ids or []),
        "actor": actor,
        "created_at": _utcnow(),
    }
    return _append(row)


def record_decision_bundle(
    *,
    market_state: dict[str, Any],
    evidence: list[dict[str, Any]],
    contradictions: list[dict[str, Any]] | None = None,
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    risk: dict[str, Any],
    execution_feasibility: dict[str, Any],
    action: dict[str, Any] | None = None,
    confidence: Any = None,
    actor: str = "system",
) -> dict[str, Any]:
    """Create a full auditable chain in one call."""
    root = create_graph(market_state=market_state, actor=actor)
    gid = root["graph_id"]
    parents = [root.get("node_id") or root["graph_id"]]
    evid_ids = []
    for ev in evidence:
        n = add_node(gid, kind="EVIDENCE", payload=ev, parent_ids=parents, actor=actor)
        evid_ids.append(n["node_id"])
    contra_ids = []
    for c in contradictions or []:
        n = add_node(gid, kind="CONTRADICTION", payload=c, parent_ids=evid_ids or parents, actor=actor)
        contra_ids.append(n["node_id"])
    hyp = add_node(
        gid,
        kind="HYPOTHESIS",
        payload=hypothesis,
        parent_ids=evid_ids or parents,
        confidence=confidence,
        actor=actor,
    )
    dec = add_node(
        gid,
        kind="DECISION",
        payload=decision,
        parent_ids=[hyp["node_id"], *contra_ids],
        confidence=confidence,
        actor=actor,
    )
    risk_n = add_node(gid, kind="RISK", payload=risk, parent_ids=[dec["node_id"]], actor=actor)
    feas = add_node(
        gid,
        kind="EXECUTION_FEASIBILITY",
        payload=execution_feasibility,
        parent_ids=[dec["node_id"], risk_n["node_id"]],
        actor=actor,
    )
    action_n = None
    if action:
        action_n = add_node(
            gid,
            kind="ACTION",
            payload=action,
            parent_ids=[feas["node_id"]],
            actor=actor,
        )
    return {
        "graph_id": gid,
        "decision_node_id": dec["node_id"],
        "feasibility_node_id": feas["node_id"],
        "action_node_id": action_n["node_id"] if action_n else None,
        "queryable": True,
        "auditable": True,
    }


def query_graph(graph_id: str) -> list[dict[str, Any]]:
    path = ensure_under(_PATH, _DATA_BASE)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("graph_id") == graph_id:
                rows.append(row)
    return rows


def attach_outcome(graph_id: str, *, decision_node_id: str, outcome: dict[str, Any], actor: str = "system") -> dict[str, Any]:
    return add_node(
        graph_id,
        kind="OUTCOME",
        payload=outcome,
        parent_ids=[decision_node_id],
        actor=actor,
    )


def attach_learning(
    graph_id: str,
    *,
    outcome_node_id: str,
    learning: dict[str, Any],
    actor: str = "system",
) -> dict[str, Any]:
    # Continuous learning must not rewrite history — append-only learning node.
    payload = dict(learning)
    payload["look_ahead_leakage_guard"] = True
    payload["hindsight_rewrite_forbidden"] = True
    return add_node(
        graph_id,
        kind="LEARNING",
        payload=payload,
        parent_ids=[outcome_node_id],
        actor=actor,
    )


def graph_status() -> dict[str, Any]:
    path = ensure_under(_PATH, _DATA_BASE)
    count = 0
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            count = sum(1 for line in fh if line.strip())
    return {
        "surface": "decision_graph",
        "nodes_logged": count,
        "append_only": True,
        "api_wired": True,
        "product_complete": False,
        "note": "Queryable append-only decision graph with API. Learning nodes cannot mutate prior nodes.",
    }
