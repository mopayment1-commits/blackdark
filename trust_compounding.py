"""Phase 5 — Trust Compounding: evidence, certificates, trust reports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from audit_registry import hash_payload
from compounding_common import dumps_json, loads_json, row_signature, utcnow, verify_row_signature

logger = logging.getLogger("BLACKDARK.TrustCompounding")

_EVIDENCE_SIGN = ("evidence_id", "evidence_type", "payload_json", "payload_hash", "timestamp")
_CERT_SIGN = ("certificate_id", "subject", "payload_hash", "timestamp")


async def store_evidence(*, evidence_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    eid = f"ev_{uuid4().hex[:14]}"
    body = dumps_json(payload)
    phash = hash_payload(payload)
    row = {
        "evidence_id": eid,
        "evidence_type": evidence_type,
        "payload_json": body,
        "payload_hash": phash,
        "timestamp": utcnow(),
    }
    row["signature"] = row_signature(row, _EVIDENCE_SIGN)
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO trust_evidence (evidence_id, evidence_type, payload_json, payload_hash, timestamp, signature)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (row["evidence_id"], row["evidence_type"], row["payload_json"], row["payload_hash"], row["timestamp"], row["signature"]),
        )
    return _evidence_api(row)


async def issue_proof_certificate(*, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
    from database import get_connection

    cid = f"cert_{uuid4().hex[:14]}"
    phash = hash_payload(payload)
    row = {
        "certificate_id": cid,
        "subject": subject,
        "payload_hash": phash,
        "timestamp": utcnow(),
    }
    row["signature"] = row_signature(row, _CERT_SIGN)
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO proof_certificates (certificate_id, subject, payload_hash, timestamp, signature)
            VALUES (?, ?, ?, ?, ?)
            """,
            (row["certificate_id"], row["subject"], row["payload_hash"], row["timestamp"], row["signature"]),
        )
    api = _cert_api(row)
    api["payload"] = payload
    return api


async def get_certificate(certificate_id: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        raw = await (await db.execute(
            "SELECT * FROM proof_certificates WHERE certificate_id = ?", (certificate_id,)
        )).fetchone()
    return _cert_api(dict(raw)) if raw else None


async def trust_os_enhanced() -> dict[str, Any]:
    from trust_os import trust_os_manifest

    manifest = trust_os_manifest()
    from learning_compounding import accuracy_track_record

    track = await accuracy_track_record(limit=50)
    evidence = await list_evidence(limit=20)
    manifest["historical_evidence"] = {
        "evidence_count": len(evidence),
        "accuracy_track_record": track.get("oracle", {}),
        "learning_outcomes": track.get("learning_registry", {}).get("outcomes", 0),
    }
    manifest["evidence_pack_path"] = "/api/trust/evidence-pack"
    return manifest


async def list_evidence(*, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute(
            "SELECT * FROM trust_evidence ORDER BY timestamp DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        )).fetchall()
    return [_evidence_api(dict(r)) for r in rows]


async def build_evidence_pack() -> dict[str, Any]:
    from learning_compounding import accuracy_track_record, missed_opportunities
    from knowledge_graph import graph_stats

    track = await accuracy_track_record(limit=100)
    misses = await missed_opportunities(limit=25)
    graph = await graph_stats()
    evidence_items = await list_evidence(limit=50)

    pack = {
        "generated_at": utcnow(),
        "principle": "DON'T DELETE KNOWLEDGE — COMPOUND IT",
        "sections": {
            "accuracy_track_record": track,
            "missed_opportunities": misses,
            "knowledge_graph": graph,
            "trust_evidence": evidence_items,
        },
        "verify": {
            "oracle_accuracy_page": "/oracle-accuracy",
            "public_accuracy_api": "/api/oracle/accuracy",
            "proof_arena": "/api/proof-arena/status",
        },
    }
    await store_evidence(evidence_type="evidence_pack", payload={"hash": hash_payload(pack), "sections": list(pack["sections"].keys())})
    return pack


async def generate_trust_report_markdown() -> str:
    pack = await build_evidence_pack()
    oracle = pack["sections"]["accuracy_track_record"].get("oracle", {})
    lines = [
        "# BLACKDARK Trust Report",
        "",
        f"Generated: {pack['generated_at']}",
        "",
        "## Forward Track Record",
        f"- Resolved predictions: {oracle.get('resolved_count', 0)}",
        f"- Hit rate: {oracle.get('hit_rate_percent', 0)}%",
        "",
        "## Knowledge Graph",
        f"- Nodes: {pack['sections']['knowledge_graph'].get('nodes', 0)}",
        f"- Edges: {pack['sections']['knowledge_graph'].get('edges', 0)}",
        "",
        "## Evidence Items",
        f"- Stored trust evidence rows: {len(pack['sections']['trust_evidence'])}",
        "",
        "Verify: /oracle-accuracy · /api/trust/evidence-pack",
        "",
        "_Not financial advice. Engineering evidence only._",
    ]
    return "\n".join(lines)


async def proof_arena_with_certificate() -> dict[str, Any]:
    from proof_arena import build_week_board

    board = build_week_board()
    cert = await issue_proof_certificate(
        subject="proof_arena_weekly",
        payload={"week_id": board.get("week_id"), "timestamp": utcnow()},
    )
    return {"board": board, "certificate": cert}


def _evidence_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "evidence_id": row.get("evidence_id"),
        "evidence_type": row.get("evidence_type"),
        "payload": loads_json(row.get("payload_json")),
        "payload_hash": row.get("payload_hash"),
        "timestamp": row.get("timestamp"),
        "signature": row.get("signature"),
    }
    sign_row = {**row, "payload_json": row.get("payload_json")}
    api["signature_valid"] = verify_row_signature(sign_row, _EVIDENCE_SIGN)
    return api


def _cert_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "certificate_id": row.get("certificate_id"),
        "subject": row.get("subject"),
        "payload_hash": row.get("payload_hash"),
        "timestamp": row.get("timestamp"),
        "signature": row.get("signature"),
    }
    api["signature_valid"] = verify_row_signature(row, _CERT_SIGN)
    return api
