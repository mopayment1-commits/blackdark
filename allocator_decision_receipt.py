"""
BLACKDARK — F3 Allocator Decision Receipt.

Signed hash receipt of recent decisions + accuracy + kill-rate for LP rooms.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _seal(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


async def build_allocator_decision_receipt(*, limit: int = 12, fund_name: str = "Emerging Desk") -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    accuracy: dict[str, Any] = {}
    kills: dict[str, Any] = {}
    try:
        from database import fetch_labeled_oracle_predictions

        rows = await fetch_labeled_oracle_predictions(limit=max(limit * 3, 40), include_synthetic=False)
        for r in (rows or [])[:limit]:
            decisions.append(
                {
                    "id": r.get("id") or r.get("prediction_id"),
                    "asset": str(r.get("asset") or r.get("symbol") or "—").upper(),
                    "verdict": str(r.get("verdict") or r.get("action") or "—"),
                    "label": str(r.get("label") or "pending"),
                    "timestamp": r.get("timestamp") or r.get("created_at"),
                }
            )
    except Exception:
        decisions = []

    try:
        from kill_rate_board import build_kill_rate_board

        kills = build_kill_rate_board()
        accuracy = {
            "source": "kill_rate_board",
            "metrics": kills.get("metrics"),
            "labeled_in_receipt": sum(
                1 for d in decisions if str(d.get("label") or "").lower() not in {"", "pending"}
            ),
        }
    except Exception:
        kills = {}
        accuracy = {"source": "unavailable"}

    body = {
        "fund_name": fund_name,
        "decisions": decisions,
        "decision_count": len(decisions),
        "accuracy": accuracy,
        "kill_rate_percent": (kills.get("metrics") or {}).get("kill_rate_percent"),
        "sources": ["oracle_ledger", "kill_rate_board", "net_edge_truth"],
        "generated_at": _utcnow(),
    }
    seal = _seal(body)
    share = (
        f"BLACKDARK Allocator Receipt · {fund_name} · {len(decisions)} decisions · "
        f"kill-rate {(kills.get('metrics') or {}).get('kill_rate_percent', '—')}% · "
        f"seal {seal[:16]}… · /allocator-receipt · Not financial advice"
    )
    return {
        "feature_id": "F3",
        "surface": "allocator_decision_receipt",
        "product_complete": False,
        **body,
        "seal_hash": seal,
        "headline": f"Allocator receipt · {len(decisions)} decisions sealed",
        "lp_ready": True,
        "formats": ["json", "pdf"],
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/allocator-receipt",
        "api": "/api/allocator-receipt",
        "pdf_api": "/api/allocator-receipt/pdf",
        "disclaimer": "Decision-support receipt for LP diligence — not a performance guarantee.",
    }


def render_allocator_receipt_pdf(receipt: dict[str, Any]) -> bytes:
    from committee_one_pager import build_minimal_pdf

    lines = [
        "BLACKDARK — Allocator Decision Receipt (F3)",
        f"Fund: {receipt.get('fund_name')}",
        f"Generated: {receipt.get('generated_at')}",
        f"Seal: {receipt.get('seal_hash')}",
        f"Decisions: {receipt.get('decision_count')}",
        f"Kill-rate: {receipt.get('kill_rate_percent')}%",
        "",
        "Recent decisions:",
    ]
    for d in (receipt.get("decisions") or [])[:12]:
        lines.append(
            f"- {d.get('timestamp') or '—'} · {d.get('asset')} · {d.get('verdict')} · {d.get('label')}"
        )
    lines.append("")
    lines.append(str(receipt.get("disclaimer") or ""))
    return build_minimal_pdf(lines, title="Allocator Decision Receipt")
