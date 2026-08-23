"""
BLACKDARK — Phase 1: Immutable Audit Log & Decision Registry.

Governing principle: DON'T DELETE KNOWLEDGE — COMPOUND IT.
Every audit entry and decision is structured, versioned, searchable,
attributable, and HMAC-signed for tamper evidence.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger("BLACKDARK.AuditRegistry")

_VALID_OUTCOMES = frozenset({"pending", "verified", "rejected", "expired"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _signing_key() -> str:
    return (
        os.getenv("AUDIT_SIGNING_KEY", "").strip()
        or os.getenv("SECRETS_MASTER_KEY", "").strip()
        or "blackdark-audit-dev-sign"
    )


def hash_payload(data: Any) -> str:
    """Stable SHA-256 over JSON-serialisable request/context data."""
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _sign_payload_dict(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hmac.new(_signing_key().encode(), raw, hashlib.sha256).hexdigest()


def sign_record(record: dict[str, Any]) -> str:
    """HMAC-SHA256 signature over canonical persisted fields."""
    return _sign_payload_dict(_canonical_sign_payload(record))


def _canonical_sign_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Fields included in tamper-evidence signatures."""
    if "decision_id" in record:
        context = record.get("context")
        prediction = record.get("prediction")
        return {
            "decision_id": record.get("decision_id"),
            "context": context if isinstance(context, str) else json.dumps(context or {}, sort_keys=True, default=str),
            "prediction": prediction if isinstance(prediction, str) else json.dumps(prediction or {}, sort_keys=True, default=str),
            "confidence": float(record.get("confidence") or 0),
            "timestamp": record.get("timestamp"),
            "outcome": record.get("outcome"),
            "version": int(record.get("version") or 1),
        }
    meta = record.get("metadata_json")
    if meta is None and "metadata" in record:
        meta = json.dumps(record.get("metadata") or {}, ensure_ascii=False, sort_keys=True, default=str)
    return {
        "timestamp": record.get("timestamp"),
        "actor": record.get("actor"),
        "action": record.get("action"),
        "payload_hash": record.get("payload_hash"),
        "outcome": record.get("outcome"),
        "request_method": record.get("request_method"),
        "request_path": record.get("request_path"),
        "metadata_json": meta or "{}",
    }


def verify_record_signature(record: dict[str, Any]) -> bool:
    sig = str(record.get("signature") or "")
    if not sig:
        return False
    expected = _sign_payload_dict(_canonical_sign_payload(record))
    return hmac.compare_digest(sig, expected)


def request_payload_fingerprint(
    *,
    method: str,
    path: str,
    query: str,
    body_bytes: bytes | None,
) -> str:
    body_hash = hashlib.sha256(body_bytes or b"").hexdigest()
    return hash_payload(
        {
            "method": method.upper(),
            "path": path,
            "query": query,
            "body_sha256": body_hash,
        }
    )


async def record_audit_log(
    *,
    actor: str,
    action: str,
    payload_hash: str,
    outcome: str,
    request_method: str | None = None,
    request_path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an immutable signed audit log row."""
    from database import get_connection

    ts = _utcnow()
    row = {
        "timestamp": ts,
        "actor": str(actor or "system")[:256],
        "action": str(action or "unknown")[:512],
        "payload_hash": str(payload_hash)[:128],
        "outcome": str(outcome or "unknown")[:128],
        "request_method": (request_method or "")[:16] or None,
        "request_path": (request_path or "")[:512] or None,
        "metadata_json": json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True, default=str),
    }
    row["signature"] = sign_record(row)

    async with get_connection() as db:
        cur = await db.execute(
            """
            INSERT INTO audit_logs (
                timestamp, actor, action, payload_hash, outcome,
                signature, request_method, request_path, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["timestamp"],
                row["actor"],
                row["action"],
                row["payload_hash"],
                row["outcome"],
                row["signature"],
                row["request_method"],
                row["request_path"],
                row["metadata_json"],
            ),
        )
        row_id = getattr(cur, "lastrowid", None)

    row["id"] = row_id
    row["signature_valid"] = True
    return row


async def fetch_audit_logs(
    *,
    start: str | None = None,
    end: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    from database import get_connection

    clauses: list[str] = []
    params: list[Any] = []
    if start:
        clauses.append("timestamp >= ?")
        params.append(start)
    if end:
        clauses.append("timestamp <= ?")
        params.append(end)
    if actor:
        clauses.append("actor = ?")
        params.append(actor)
    if action:
        clauses.append("action = ?")
        params.append(action)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 10_000)))

    async with get_connection() as db:
        result = await db.execute(
            f"""
            SELECT id, timestamp, actor, action, payload_hash, outcome,
                   signature, request_method, request_path, metadata_json
            FROM audit_logs
            {where}
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        )
        rows = await result.fetchall()

    out: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        meta = row.pop("metadata_json", None)
        if meta:
            try:
                row["metadata"] = json.loads(meta)
            except json.JSONDecodeError:
                row["metadata"] = {}
        row["signature_valid"] = verify_record_signature(row)
        out.append(row)
    return out


def export_audit_logs_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    fields = [
        "id",
        "timestamp",
        "actor",
        "action",
        "payload_hash",
        "outcome",
        "signature",
        "request_method",
        "request_path",
        "signature_valid",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fields})
    return buf.getvalue()


async def create_decision(
    *,
    context: dict[str, Any],
    prediction: dict[str, Any],
    confidence: float,
    actor: str = "system",
    decision_id: str | None = None,
    outcome: str = "pending",
) -> dict[str, Any]:
    """Create a versioned decision registry entry (version 1)."""
    from database import get_connection

    if outcome not in _VALID_OUTCOMES:
        outcome = "pending"

    did = decision_id or f"dec_{uuid4().hex[:16]}"
    ts = _utcnow()
    row = {
        "decision_id": did,
        "context": json.dumps(context or {}, ensure_ascii=False, sort_keys=True, default=str),
        "prediction": json.dumps(prediction or {}, ensure_ascii=False, sort_keys=True, default=str),
        "confidence": float(confidence),
        "timestamp": ts,
        "outcome": outcome,
        "version": 1,
    }
    row["signature"] = sign_record(row)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO decisions (
                decision_id, context, prediction, confidence,
                timestamp, outcome, version, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["decision_id"],
                row["context"],
                row["prediction"],
                row["confidence"],
                row["timestamp"],
                row["outcome"],
                row["version"],
                row["signature"],
            ),
        )

    await record_audit_log(
        actor=actor,
        action="decision.create",
        payload_hash=hash_payload({"decision_id": did, "version": 1}),
        outcome=f"created:{outcome}",
        request_path=f"/api/decisions/{did}",
        metadata={"decision_id": did, "version": 1},
    )
    return _decision_row_to_api(row)


async def create_decision_version(
    *,
    decision_id: str,
    context: dict[str, Any] | None = None,
    prediction: dict[str, Any] | None = None,
    confidence: float | None = None,
    outcome: str | None = None,
    actor: str = "system",
) -> dict[str, Any] | None:
    """Bump decision version — prior versions remain immutable."""
    from database import get_connection

    latest = await get_decision(decision_id)
    if not latest:
        return None

    next_version = int(latest.get("version") or 1) + 1
    ctx = context if context is not None else latest.get("context") or {}
    pred = prediction if prediction is not None else latest.get("prediction") or {}
    conf = float(confidence) if confidence is not None else float(latest.get("confidence") or 0)
    out = outcome if outcome is not None else str(latest.get("outcome") or "pending")
    if out not in _VALID_OUTCOMES:
        out = "pending"

    ts = _utcnow()
    row = {
        "decision_id": decision_id,
        "context": json.dumps(ctx, ensure_ascii=False, sort_keys=True, default=str),
        "prediction": json.dumps(pred, ensure_ascii=False, sort_keys=True, default=str),
        "confidence": conf,
        "timestamp": ts,
        "outcome": out,
        "version": next_version,
    }
    row["signature"] = sign_record(row)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO decisions (
                decision_id, context, prediction, confidence,
                timestamp, outcome, version, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["decision_id"],
                row["context"],
                row["prediction"],
                row["confidence"],
                row["timestamp"],
                row["outcome"],
                row["version"],
                row["signature"],
            ),
        )

    await record_audit_log(
        actor=actor,
        action="decision.version",
        payload_hash=hash_payload({"decision_id": decision_id, "version": next_version}),
        outcome=f"versioned:{out}",
        request_path=f"/api/decisions/{decision_id}",
        metadata={"decision_id": decision_id, "version": next_version},
    )
    return _decision_row_to_api(row)


async def get_decision(decision_id: str, *, version: int | None = None) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        if version is not None:
            result = await db.execute(
                """
                SELECT decision_id, context, prediction, confidence,
                       timestamp, outcome, version, signature
                FROM decisions
                WHERE decision_id = ? AND version = ?
                """,
                (decision_id, int(version)),
            )
        else:
            result = await db.execute(
                """
                SELECT decision_id, context, prediction, confidence,
                       timestamp, outcome, version, signature
                FROM decisions
                WHERE decision_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (decision_id,),
            )
        raw = await result.fetchone()

    if not raw:
        return None

    api_row = _decision_row_to_api(dict(raw))
    versions = await list_decision_versions(decision_id)
    api_row["versions"] = versions
    api_row["version_count"] = len(versions)
    return api_row


async def list_decision_versions(decision_id: str) -> list[int]:
    from database import get_connection

    async with get_connection() as db:
        result = await db.execute(
            """
            SELECT version FROM decisions
            WHERE decision_id = ?
            ORDER BY version ASC
            """,
            (decision_id,),
        )
        rows = await result.fetchall()
    return [int(dict(r)["version"]) for r in rows]


async def search_decisions(
    *,
    start: str | None = None,
    end: str | None = None,
    outcome: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Search latest version per decision_id within optional filters."""
    from database import get_connection

    clauses: list[str] = []
    params: list[Any] = []
    if start:
        clauses.append("d.timestamp >= ?")
        params.append(start)
    if end:
        clauses.append("d.timestamp <= ?")
        params.append(end)
    if outcome:
        clauses.append("d.outcome = ?")
        params.append(outcome)

    where = f"AND {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 1000)))

    async with get_connection() as db:
        result = await db.execute(
            f"""
            SELECT d.decision_id, d.context, d.prediction, d.confidence,
                   d.timestamp, d.outcome, d.version, d.signature
            FROM decisions d
            INNER JOIN (
                SELECT decision_id, MAX(version) AS max_version
                FROM decisions
                GROUP BY decision_id
            ) latest
                ON d.decision_id = latest.decision_id
               AND d.version = latest.max_version
            WHERE 1=1 {where}
            ORDER BY d.timestamp DESC
            LIMIT ?
            """,
            tuple(params),
        )
        rows = await result.fetchall()

    out: list[dict[str, Any]] = []
    sym_upper = (symbol or "").upper()
    for raw in rows:
        item = _decision_row_to_api(dict(raw))
        if sym_upper:
            ctx = item.get("context") or {}
            pred = item.get("prediction") or {}
            hay = json.dumps({**ctx, **pred}, default=str).upper()
            if sym_upper not in hay:
                continue
        out.append(item)
    return out


def _decision_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    api = dict(row)
    for key in ("context", "prediction"):
        raw = api.get(key)
        if isinstance(raw, str):
            try:
                api[key] = json.loads(raw)
            except json.JSONDecodeError:
                api[key] = {"raw": raw}
    api["signature_valid"] = verify_record_signature(api)
    return api


async def resolve_actor_from_request(request: Any) -> str:
    """Best-effort actor attribution for middleware audit rows."""
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer ") and len(auth) > 20:
        return f"bearer:{hash_payload(auth[-32:])[:12]}"
    api_key = (request.headers.get("X-API-Key") or "").strip()
    if api_key:
        return f"api_key:{hash_payload(api_key)[:12]}"
    cookie = (request.cookies.get("bd_token") or "").strip()
    if cookie:
        return f"session:{hash_payload(cookie)[:12]}"
    client = getattr(request, "client", None)
    if client and getattr(client, "host", None):
        return f"ip:{client.host}"
    return "anonymous"


async def log_api_request(
    *,
    request: Any,
    response_status: int,
    body_bytes: bytes | None = None,
) -> None:
    """Middleware helper — records every /api/ call with provenance."""
    path = request.url.path or ""
    if not path.startswith("/api/"):
        return
    # Avoid recursive noise from high-volume export polling
    if path.startswith("/api/audit/export"):
        return

    try:
        actor = await resolve_actor_from_request(request)
        fingerprint = request_payload_fingerprint(
            method=request.method,
            path=path,
            query=str(request.url.query or ""),
            body_bytes=body_bytes,
        )
        await record_audit_log(
            actor=actor,
            action=f"api.{request.method.lower()}",
            payload_hash=fingerprint,
            outcome=f"http_{int(response_status)}",
            request_method=request.method,
            request_path=path,
            metadata={
                "status_code": int(response_status),
                "query": str(request.url.query or ""),
            },
        )
    except Exception:
        logger.exception("Failed to persist API audit log for %s", path)
