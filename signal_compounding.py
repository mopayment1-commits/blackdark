"""Phase 3 — Market Memory & Signal Compounding."""

from __future__ import annotations

import logging
import statistics
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from audit_registry import hash_payload
from compounding_common import dumps_json, loads_json, row_signature, utcnow, verify_row_signature

logger = logging.getLogger("BLACKDARK.SignalCompounding")

_SIGNAL_SIGN = (
    "signal_id",
    "symbol",
    "signal_type",
    "value_json",
    "confidence",
    "source",
    "timestamp",
    "version",
    "payload_hash",
)


async def store_signal(
    *,
    symbol: str,
    signal_type: str,
    value: Any,
    confidence: float,
    source: str,
    signal_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    sid = signal_id or f"sig_{uuid4().hex[:14]}"
    sym = str(symbol).upper()
    ts = timestamp or utcnow()
    value_json = dumps_json({"value": value})
    payload_hash = hash_payload({"signal_id": sid, "symbol": sym, "value": value, "ts": ts})

    async with get_connection() as db:
        latest = await (
            await db.execute(
                "SELECT MAX(version) AS v FROM market_signals WHERE signal_id = ?",
                (sid,),
            )
        ).fetchone()
        version = int((dict(latest).get("v") if latest else 0) or 0) + 1

    row = {
        "signal_id": sid,
        "symbol": sym,
        "signal_type": signal_type,
        "value_json": value_json,
        "confidence": float(confidence),
        "source": source,
        "timestamp": ts,
        "version": version,
        "payload_hash": payload_hash,
    }
    row["signature"] = row_signature(row, _SIGNAL_SIGN)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO market_signals (
                signal_id, symbol, signal_type, value_json, confidence, source,
                timestamp, version, payload_hash, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["signal_id"],
                row["symbol"],
                row["signal_type"],
                row["value_json"],
                row["confidence"],
                row["source"],
                row["timestamp"],
                row["version"],
                row["payload_hash"],
                row["signature"],
            ),
        )

    try:
        from knowledge_graph import create_edge, create_node, get_node

        sig_node = f"signal_{sid}"
        if not await get_node(sig_node):
            await create_node(
                node_id=sig_node,
                node_type="Signal",
                label=sid,
                properties={"signal_id": sid, "signal_type": signal_type, "symbol": sym},
            )
            asset_node = f"asset_{sym}"
            if await get_node(asset_node):
                await create_edge(
                    source_node_id=sig_node,
                    target_node_id=asset_node,
                    edge_type="influenced_by",
                )
    except Exception:
        logger.exception("KG signal ingest failed for %s", sid)

    return _signal_api(row)


async def signal_history(symbol: str, *, limit: int = 100) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        result = await db.execute(
            """
            SELECT signal_id, symbol, signal_type, value_json, confidence, source,
                   timestamp, version, payload_hash, signature
            FROM market_signals
            WHERE symbol = ?
            ORDER BY timestamp DESC, version DESC
            LIMIT ?
            """,
            (symbol.upper(), max(1, min(limit, 1000))),
        )
        rows = await result.fetchall()
    return [_signal_api(dict(r)) for r in rows]


async def signal_diff(symbol: str, *, from_ts: str, to_ts: str) -> dict[str, Any]:
    history = await signal_history(symbol, limit=500)
    in_window = [h for h in history if from_ts <= str(h["timestamp"]) <= to_ts]
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in in_window:
        by_id.setdefault(row["signal_id"], []).append(row)

    changes = []
    for sid, versions in by_id.items():
        versions.sort(key=lambda r: (r["timestamp"], r["version"]))
        if len(versions) < 2:
            continue
        first, last = versions[0], versions[-1]
        if first["value"] != last["value"] or first["confidence"] != last["confidence"]:
            changes.append(
                {
                    "signal_id": sid,
                    "signal_type": last["signal_type"],
                    "from": {"timestamp": first["timestamp"], "version": first["version"], "value": first["value"], "confidence": first["confidence"]},
                    "to": {"timestamp": last["timestamp"], "version": last["version"], "value": last["value"], "confidence": last["confidence"]},
                }
            )
    return {"symbol": symbol.upper(), "from": from_ts, "to": to_ts, "change_count": len(changes), "changes": changes}


async def signal_correlate(symbols: list[str]) -> dict[str, Any]:
    from database import get_connection

    syms = [s.upper() for s in symbols if s]
    if len(syms) < 2:
        return {"symbols": syms, "correlations": [], "note": "need at least 2 symbols"}

    series: dict[str, list[float]] = {s: [] for s in syms}
    async with get_connection() as db:
        for sym in syms:
            result = await db.execute(
                """
                SELECT confidence FROM market_signals
                WHERE symbol = ?
                ORDER BY timestamp DESC LIMIT 50
                """,
                (sym,),
            )
            rows = await result.fetchall()
            series[sym] = [float(dict(r)["confidence"]) for r in rows]

    correlations = []
    for i, a in enumerate(syms):
        for b in syms[i + 1 :]:
            xs, ys = series[a], series[b]
            n = min(len(xs), len(ys))
            if n < 3:
                correlations.append({"pair": [a, b], "samples": n, "coefficient": None, "strength": "insufficient_data"})
                continue
            xs, ys = xs[:n], ys[:n]
            try:
                coeff = statistics.correlation(xs, ys)
            except Exception:
                coeff = None
            strength = "weak"
            if coeff is not None:
                ac = abs(coeff)
                strength = "strong" if ac >= 0.7 else "moderate" if ac >= 0.4 else "weak"
            correlations.append({"pair": [a, b], "samples": n, "coefficient": coeff, "strength": strength})
    return {"symbols": syms, "correlations": correlations}


def persist_registry_signal(row: dict[str, Any]) -> None:
    """Sync hook from signal_registry.register_signal (best-effort)."""
    import asyncio

    sym = str(row.get("symbol") or row.get("asset") or "UNKNOWN").upper()
    try:
        asyncio.get_running_loop().create_task(
            store_signal(
                symbol=sym,
                signal_type=str(row.get("signal_type") or "oracle_direction"),
                value=row.get("features") or row.get("value") or row,
                confidence=float(row.get("confidence") or row.get("weight") or 0.5),
                source=str(row.get("source") or row.get("provenance", {}).get("source") or "signal_registry"),
                signal_id=str(row.get("signal_id") or ""),
            )
        )
    except RuntimeError:
        asyncio.run(
            store_signal(
                symbol=sym,
                signal_type=str(row.get("signal_type") or "oracle_direction"),
                value=row.get("features") or row.get("value") or row,
                confidence=float(row.get("confidence") or 0.5),
                source=str(row.get("source") or "signal_registry"),
                signal_id=str(row.get("signal_id") or ""),
            )
        )
    except Exception:
        logger.exception("signal registry SQL sync failed")


def _signal_api(row: dict[str, Any]) -> dict[str, Any]:
    val = loads_json(row.get("value_json"))
    api = {
        "signal_id": row.get("signal_id"),
        "symbol": row.get("symbol"),
        "signal_type": row.get("signal_type"),
        "value": val.get("value") if isinstance(val, dict) and "value" in val else val,
        "confidence": row.get("confidence"),
        "source": row.get("source"),
        "timestamp": row.get("timestamp"),
        "version": row.get("version", 1),
        "payload_hash": row.get("payload_hash"),
        "signature": row.get("signature"),
    }
    sign_row = {**row, "value_json": row.get("value_json") or dumps_json({"value": api["value"]})}
    api["signature_valid"] = verify_row_signature(sign_row, _SIGNAL_SIGN)
    return api
