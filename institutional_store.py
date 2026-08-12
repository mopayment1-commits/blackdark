"""Institutional operational store — DB authority (SQLite/Postgres) with JSONL export.

OMS / Decision / Memory / Alerts / Portfolio write here first.
JSON/JSONL files remain evidence exports only, not operational source of truth.
"""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

import config

_LOCK = threading.RLock()
_READY_FOR: str | None = None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _run(coro: Any) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nested: schedule on a fresh loop in a worker thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result(timeout=30)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _ensure_schema() -> None:
    from database import _apply_migrations, get_connection, init_db

    global _READY_FOR
    key = f"{getattr(config, 'DATABASE_URL', '')}|{getattr(config, 'DB_PATH', '')}"
    if _READY_FOR == key:
        return
    try:
        await init_db()
    except Exception:
        pass
    # Always re-apply migrations so new institutional tables appear on existing DBs.
    async with get_connection() as db:
        await _apply_migrations(db)
        await db.execute("SELECT 1 FROM inst_oms_orders LIMIT 1")
    _READY_FOR = key


def ensure_ready() -> None:
    with _LOCK:
        _run(_ensure_schema())


async def audit(
    *,
    org_id: str,
    surface: str,
    event_type: str,
    ref_id: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    async with __import__("database", fromlist=["get_connection"]).get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_audit_events (org_id, surface, event_type, ref_id, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                org_id,
                surface,
                event_type,
                ref_id or None,
                json.dumps(payload or {}, ensure_ascii=False),
                _utcnow(),
            ),
        )


def audit_sync(**kwargs: Any) -> None:
    ensure_ready()
    _run(audit(**kwargs))


# ---- OMS ----


async def oms_upsert(row: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_oms_orders (
                order_id, org_id, venue, symbol, side, quantity, filled_quantity,
                order_type, limit_price, state, idempotency_key, actor, venue_ack_id,
                history_json, reconcile_json, payload_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                filled_quantity=excluded.filled_quantity,
                state=excluded.state,
                venue_ack_id=excluded.venue_ack_id,
                history_json=excluded.history_json,
                reconcile_json=excluded.reconcile_json,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                row["order_id"],
                row["org_id"],
                row["venue"],
                row["symbol"],
                row["side"],
                float(row["quantity"]),
                float(row.get("filled_quantity") or 0),
                row.get("order_type") or "limit",
                row.get("limit_price"),
                row["state"],
                row["idempotency_key"],
                row.get("actor") or "system",
                row.get("venue_ack_id"),
                json.dumps(row.get("history") or [], ensure_ascii=False),
                json.dumps(row.get("reconcile"), ensure_ascii=False) if row.get("reconcile") else None,
                json.dumps({k: v for k, v in row.items() if k not in {"history", "reconcile"}}, ensure_ascii=False),
                row.get("created_at") or _utcnow(),
                row.get("updated_at") or _utcnow(),
            ),
        )
    await audit(
        org_id=str(row["org_id"]),
        surface="oms",
        event_type=f"state:{row['state']}",
        ref_id=str(row["order_id"]),
        payload={"state": row["state"], "symbol": row.get("symbol")},
    )
    return row


def oms_upsert_sync(row: dict[str, Any]) -> dict[str, Any]:
    ensure_ready()
    return _run(oms_upsert(row))


async def oms_get(order_id: str) -> dict[str, Any] | None:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        cur = await db.execute("SELECT * FROM inst_oms_orders WHERE order_id = ?", (order_id,))
        row = await cur.fetchone()
    if not row:
        return None
    d = dict(row)
    hist = json.loads(d.get("history_json") or "[]")
    recon = json.loads(d["reconcile_json"]) if d.get("reconcile_json") else None
    payload = json.loads(d.get("payload_json") or "{}")
    out = {**payload, **{k: d[k] for k in (
        "order_id", "org_id", "venue", "symbol", "side", "quantity", "filled_quantity",
        "order_type", "limit_price", "state", "idempotency_key", "actor", "venue_ack_id",
        "created_at", "updated_at",
    ) if k in d}}
    out["history"] = hist
    if recon is not None:
        out["reconcile"] = recon
    return out


def oms_get_sync(order_id: str) -> dict[str, Any] | None:
    ensure_ready()
    return _run(oms_get(order_id))


async def oms_get_by_idempotency(org_id: str, idempotency_key: str) -> dict[str, Any] | None:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT order_id FROM inst_oms_orders WHERE org_id = ? AND idempotency_key = ?",
            (org_id, idempotency_key),
        )
        row = await cur.fetchone()
    if not row:
        return None
    return await oms_get(str(dict(row)["order_id"]))


def oms_get_by_idempotency_sync(org_id: str, idempotency_key: str) -> dict[str, Any] | None:
    ensure_ready()
    return _run(oms_get_by_idempotency(org_id, idempotency_key))


async def oms_list(org_id: str) -> list[dict[str, Any]]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT order_id FROM inst_oms_orders WHERE org_id = ? ORDER BY updated_at DESC",
            (org_id,),
        )
        rows = await cur.fetchall()
    out = []
    for r in rows:
        item = await oms_get(str(dict(r)["order_id"]))
        if item:
            out.append(item)
    return out


def oms_list_sync(org_id: str) -> list[dict[str, Any]]:
    ensure_ready()
    return _run(oms_list(org_id))


# ---- Decision / Memory ----


async def decision_append(row: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_decision_nodes
                (graph_id, node_id, kind, payload_json, parent_ids, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["graph_id"],
                row.get("node_id"),
                row["kind"],
                json.dumps(row.get("payload") or {}, ensure_ascii=False),
                json.dumps(row.get("parent_ids") or [], ensure_ascii=False),
                row.get("actor"),
                row.get("created_at") or _utcnow(),
            ),
        )
    return row


def decision_append_sync(row: dict[str, Any]) -> dict[str, Any]:
    ensure_ready()
    return _run(decision_append(row))


async def decision_query(graph_id: str) -> list[dict[str, Any]]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT * FROM inst_decision_nodes WHERE graph_id = ? ORDER BY id ASC",
            (graph_id,),
        )
        rows = await cur.fetchall()
    out = []
    for r in rows:
        d = dict(r)
        out.append(
            {
                "graph_id": d["graph_id"],
                "node_id": d.get("node_id"),
                "kind": d["kind"],
                "payload": json.loads(d.get("payload_json") or "{}"),
                "parent_ids": json.loads(d.get("parent_ids") or "[]"),
                "actor": d.get("actor"),
                "created_at": d.get("created_at"),
            }
        )
    return out


def decision_query_sync(graph_id: str) -> list[dict[str, Any]]:
    ensure_ready()
    return _run(decision_query(graph_id))


async def memory_remember(row: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    await _ensure_schema()
    mid = row.get("memory_id") or f"im_{uuid.uuid4().hex[:16]}"
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_memory (memory_id, kind, graph_id, payload_json, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                mid,
                row["kind"],
                row.get("graph_id") or "",
                json.dumps(row.get("payload") or {}, ensure_ascii=False),
                row.get("actor") or "system",
                row.get("created_at") or _utcnow(),
            ),
        )
    return {**row, "memory_id": mid}


def memory_remember_sync(row: dict[str, Any]) -> dict[str, Any]:
    ensure_ready()
    return _run(memory_remember(row))


# ---- Portfolio ----


async def portfolio_upsert_position(row: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    await _ensure_schema()
    pid = row.get("position_id") or f"pos_{uuid.uuid4().hex[:12]}"
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_portfolio_positions (
                position_id, org_id, asset, symbol, side, quantity, notional_usd,
                unrealized_pnl_usd, venue, source_order_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(position_id) DO UPDATE SET
                quantity=excluded.quantity,
                notional_usd=excluded.notional_usd,
                unrealized_pnl_usd=excluded.unrealized_pnl_usd,
                updated_at=excluded.updated_at
            """,
            (
                pid,
                row["org_id"],
                row["asset"],
                row.get("symbol"),
                row.get("side") or "long",
                row.get("quantity"),
                row.get("notional_usd"),
                row.get("unrealized_pnl_usd") or 0,
                row.get("venue"),
                row.get("source_order_id"),
                _utcnow(),
            ),
        )
    return {**row, "position_id": pid}


def portfolio_upsert_position_sync(row: dict[str, Any]) -> dict[str, Any]:
    ensure_ready()
    return _run(portfolio_upsert_position(row))


async def portfolio_list(org_id: str) -> list[dict[str, Any]]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT * FROM inst_portfolio_positions WHERE org_id = ? ORDER BY updated_at DESC",
            (org_id,),
        )
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


def portfolio_list_sync(org_id: str) -> list[dict[str, Any]]:
    ensure_ready()
    return _run(portfolio_list(org_id))


# ---- Alerts ----


async def alert_upsert(row: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    await _ensure_schema()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO inst_alerts (
                alert_id, org_id, severity, channel, message, dedupe_key,
                status, delivery_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alert_id) DO UPDATE SET
                status=excluded.status,
                delivery_json=excluded.delivery_json
            """,
            (
                row["alert_id"],
                row["org_id"],
                row["severity"],
                row["channel"],
                row["message"],
                row["dedupe_key"],
                row["status"],
                json.dumps(row.get("delivery") or {}, ensure_ascii=False),
                row.get("created_at") or _utcnow(),
            ),
        )
    return row


def alert_upsert_sync(row: dict[str, Any]) -> dict[str, Any]:
    ensure_ready()
    return _run(alert_upsert(row))


def store_status() -> dict[str, Any]:
    from postgres_backend import use_postgres

    ensure_ready()
    return {
        "surface": "institutional_store",
        "authority": "postgres" if use_postgres() else "sqlite",
        "db_path": str(config.DB_PATH),
        "tables": [
            "inst_oms_orders",
            "inst_decision_nodes",
            "inst_memory",
            "inst_alerts",
            "inst_portfolio_positions",
            "inst_audit_events",
        ],
        "jsonl_is_export_only": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
