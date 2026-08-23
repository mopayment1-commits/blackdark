"""Phase 7 — Corporate Value & Governance Assets (engineering evidence only)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from compounding_common import dumps_json, loads_json, utcnow

logger = logging.getLogger("BLACKDARK.CorporateCompounding")

_DATA_DIR = Path(__file__).resolve().parent / "data" / "corporate"
_EXTERNAL = {
    "legal_ip_registration": "EXTERNAL_DEPENDENCY — legal counsel required",
    "live_revenue_recognition": "EXTERNAL_DEPENDENCY — live PSP / billing keys required",
    "soc2_iso_certification": "EXTERNAL_DEPENDENCY — external auditor required",
}


async def register_ip_asset(
    *,
    asset_type: str,
    title: str,
    description: str | None = None,
    rights: dict[str, Any] | None = None,
    documentation_ref: str | None = None,
    asset_id: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    aid = asset_id or f"ip_{uuid4().hex[:12]}"
    now = utcnow()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO ip_registry (
                asset_id, asset_type, title, description, rights_json, documentation_ref, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                rights_json = excluded.rights_json,
                documentation_ref = excluded.documentation_ref,
                updated_at = excluded.updated_at
            """,
            (aid, asset_type, title, description, dumps_json(rights or {}), documentation_ref, now, now),
        )
    return {"asset_id": aid, "asset_type": asset_type, "title": title, "updated_at": now}


async def list_ip_registry() -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute("SELECT * FROM ip_registry ORDER BY updated_at DESC")).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        out.append(
            {
                "asset_id": d.get("asset_id"),
                "asset_type": d.get("asset_type"),
                "title": d.get("title"),
                "description": d.get("description"),
                "rights": loads_json(d.get("rights_json")),
                "documentation_ref": d.get("documentation_ref"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            }
        )
    return out


async def record_dd_entry(
    *,
    evidence_type: str,
    payload: dict[str, Any],
    inquiry_id: int | None = None,
) -> dict[str, Any]:
    from database import get_connection

    eid = f"dd_{uuid4().hex[:14]}"
    now = utcnow()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO corporate_dd_entries (entry_id, inquiry_id, evidence_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (eid, inquiry_id, evidence_type, dumps_json(payload), now),
        )
    return {"entry_id": eid, "inquiry_id": inquiry_id, "evidence_type": evidence_type, "created_at": now}


async def on_institutional_inquiry(inquiry_id: int, inquiry: dict[str, Any]) -> dict[str, Any]:
    return await record_dd_entry(
        inquiry_id=inquiry_id,
        evidence_type="institutional_inquiry",
        payload={
            "email": inquiry.get("email"),
            "company": inquiry.get("company"),
            "budget_usd": inquiry.get("budget_usd"),
            "message_preview": str(inquiry.get("message") or "")[:500],
        },
    )


async def compliance_status() -> dict[str, Any]:
    from regulatory_compliance_guard import regulatory_compliance_status

    base = regulatory_compliance_status()

    from trust_compounding import list_evidence
    from knowledge_graph import graph_stats

    return {
        **base,
        "institutional_compounding": {
            "audit_registry": True,
            "knowledge_graph": await graph_stats(),
            "trust_evidence_rows": len(await list_evidence(limit=5)),
        },
        "external_dependencies": _EXTERNAL,
        "generated_at": utcnow(),
    }


async def revenue_quality_metrics() -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        subs = await (await db.execute("SELECT COUNT(*) AS c FROM subscriptions")).fetchone()
        waitlist = await (await db.execute("SELECT COUNT(*) AS c FROM waitlist")).fetchone()
        inquiries = await (await db.execute("SELECT COUNT(*) AS c FROM institutional_inquiries")).fetchone()

    def _cell(row: Any) -> int:
        d = dict(row)
        return int(list(d.values())[0])

    return {
        "mrr_usd": None,
        "mrr_note": _EXTERNAL["live_revenue_recognition"],
        "active_subscriptions": _cell(subs) if subs else 0,
        "waitlist_count": _cell(waitlist) if waitlist else 0,
        "institutional_inquiries": _cell(inquiries) if inquiries else 0,
        "churn_rate": None,
        "ltv_usd": None,
        "data_source": "database_counters",
        "generated_at": utcnow(),
    }


async def build_data_room_snapshot() -> dict[str, Any]:
    from distribution_compounding import institutional_dashboard_data, seo_performance
    from learning_compounding import accuracy_track_record
    from trust_compounding import build_evidence_pack
    from runtime_verification import phase_verify_all

    ip_assets = await list_ip_registry()
    if not ip_assets:
        await seed_default_ip_registry()
        ip_assets = await list_ip_registry()

    snapshot = {
        "generated_at": utcnow(),
        "principle": "DON'T DELETE KNOWLEDGE — COMPOUND IT",
        "static_index": "docs/DATA_ROOM.md",
        "live_metrics": {
            "revenue": await revenue_quality_metrics(),
            "accuracy": await accuracy_track_record(limit=25),
            "seo": await seo_performance(),
            "dashboard": await institutional_dashboard_data(),
        },
        "ip_registry": ip_assets,
        "compliance": await compliance_status(),
        "phase_verification": await phase_verify_all(),
        "external_dependencies": _EXTERNAL,
    }
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = _DATA_DIR / "DATA_ROOM_SNAPSHOT.json"
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    await record_dd_entry(evidence_type="data_room_snapshot", payload={"path": str(out), "hash": out.stat().st_size})
    return snapshot


async def seed_default_ip_registry() -> None:
    defaults = [
        ("ip_signal_lexicon", "algorithm", "Sovereign Signal Lexicon", "signal_registry.py SIGNAL_TYPE_LEXICON", {"rights": "proprietary", "registration": _EXTERNAL["legal_ip_registration"]}, "signal_registry.py"),
        ("ip_oracle_engine", "model", "Unified Oracle Decision Engine", "oracle_unified + ml ensemble", {"rights": "proprietary"}, "ml/"),
        ("ip_audit_chain", "data", "Oracle Audit Hash Chain", "oracle_audit_chain.py", {"rights": "proprietary"}, "oracle_audit_chain.py"),
        ("ip_knowledge_graph", "schema", "Institutional Knowledge Graph", "kg_nodes/kg_edges", {"rights": "proprietary"}, "knowledge_graph.py"),
    ]
    for aid, atype, title, desc, rights, ref in defaults:
        await register_ip_asset(asset_type=atype, title=title, description=desc, rights=rights, documentation_ref=ref, asset_id=aid)
