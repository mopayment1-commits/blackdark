"""
QuickTake / Analyst Insight Feed — Feature #184 (BLACKDARK Daily Brief).

Evidence-linked publishing with moderation. No ungrounded claims.

Each insight contains:
  1. Claim
  2. Evidence (chart/data links)
  3. Source (data collection timestamp)
  4. Confidence score
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.QuickTake")

_FEATURE_ID = 184
_STORE_PATH = Path("data/quicktake_insights.json")
_MODERATION_STATES = ("draft", "pending_moderation", "published", "rejected")
ModerationState = Literal["draft", "pending_moderation", "published", "rejected"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _insight_id() -> str:
    return f"qt_{secrets.token_urlsafe(8)}"


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return {"insights": {}}
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"insights": {}}


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _validate_quantitative_claims(claims: list[dict[str, Any]]) -> tuple[bool, str]:
    """Reject ungrounded quantitative claims — every number must have evidence."""
    for claim in claims:
        text = str(claim.get("claim") or "")
        has_number = any(ch.isdigit() for ch in text)
        evidence = claim.get("evidence") or []
        if has_number and not evidence:
            return False, f"Ungrounded quantitative claim: {text[:80]}"
        if not claim.get("source"):
            return False, "Every claim must include source metadata"
    return True, "ok"


def create_insight(
    *,
    author: str,
    title: str,
    summary: str,
    claims: list[dict[str, Any]],
    chart_refs: list[dict[str, Any]] | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Create draft insight — requires evidence on quantitative claims."""
    valid, reason = _validate_quantitative_claims(claims)
    if not valid:
        return {"ok": False, "error": "ungrounded_claim", "detail": reason}

    store = _load_store()
    iid = _insight_id()
    now = _utcnow()
    row = {
        "id": iid,
        "product": "BLACKDARK Daily Brief",
        "author": author,
        "title": title,
        "summary": summary,
        "claims": claims,
        "chart_refs": chart_refs or [],
        "confidence": confidence,
        "moderation_state": "draft",
        "moderation_notes": None,
        "published_at": None,
        "created_at": now,
        "updated_at": now,
    }
    store["insights"][iid] = row
    _save_store(store)
    return {"ok": True, "feature_id": _FEATURE_ID, "insight": row}


def submit_for_moderation(*, insight_id: str, author: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("insights", {}).get(insight_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    if row.get("author") != author:
        return {"ok": False, "error": "access_denied"}
    valid, reason = _validate_quantitative_claims(row.get("claims") or [])
    if not valid:
        return {"ok": False, "error": "ungrounded_claim", "detail": reason}
    row["moderation_state"] = "pending_moderation"
    row["updated_at"] = _utcnow()
    _save_store(store)
    return {"ok": True, "insight_id": insight_id, "moderation_state": "pending_moderation"}


def moderate_insight(
    *,
    insight_id: str,
    action: str,
    moderator: str,
    notes: str = "",
) -> dict[str, Any]:
    """Moderation gate — publish or reject."""
    store = _load_store()
    row = store.get("insights", {}).get(insight_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    if action not in {"approve", "reject"}:
        return {"ok": False, "error": "invalid_action"}

    if action == "approve":
        row["moderation_state"] = "published"
        row["published_at"] = _utcnow()
    else:
        row["moderation_state"] = "rejected"
    row["moderation_notes"] = notes
    row["moderated_by"] = moderator
    row["updated_at"] = _utcnow()
    _save_store(store)
    return {"ok": True, "insight_id": insight_id, "moderation_state": row["moderation_state"]}


def list_published_insights(*, limit: int = 10) -> dict[str, Any]:
    store = _load_store()
    rows = [
        r for r in store.get("insights", {}).values() if r.get("moderation_state") == "published"
    ]
    rows.sort(key=lambda r: r.get("published_at") or "", reverse=True)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product": "BLACKDARK Daily Brief",
        "insights": rows[:limit],
        "count": len(rows[:limit]),
        "timestamp": _utcnow(),
    }


async def generate_daily_brief(*, asset: str = "BTC") -> dict[str, Any]:
    """Auto-generate 1-2 evidence-linked daily briefs from platform data."""
    import asyncio

    from blackdark.api.canonical_intelligence import (
        get_market_health_intelligence,
        get_price_intelligence,
        get_risk_score_intelligence,
    )

    sym = asset.upper()
    price, health, risk = await asyncio.gather(
        get_price_intelligence(sym),
        get_market_health_intelligence(sym),
        get_risk_score_intelligence(sym),
    )

    claims: list[dict[str, Any]] = []
    if health.get("ok"):
        claims.append(
            {
                "claim": f"{sym} market health score is {health.get('overall_score')} ({health.get('overall_status')})",
                "evidence": [{"type": "api", "url": f"/api/v1/blackdark/market-health/{sym}"}],
                "source": health.get("freshness", {}).get("as_of"),
                "confidence": health.get("overall_score"),
            }
        )
    if price.get("ok") and price.get("price_usd") is not None:
        claims.append(
            {
                "claim": f"{sym} aggregated price is ${price.get('price_usd'):,.2f} across {price.get('source_count')} sources",
                "evidence": [{"type": "api", "url": f"/api/v1/blackdark/price/{sym}"}],
                "source": price.get("freshness", {}).get("as_of"),
                "confidence": 90 if price.get("price_verified") else 70,
            }
        )
    if risk.get("ok") and risk.get("confidence_score") is not None:
        claims.append(
            {
                "claim": f"{sym} confidence score is {risk.get('confidence_score')} (experimental)",
                "evidence": [{"type": "api", "url": f"/api/v1/blackdark/risk-score/{sym}"}],
                "source": risk.get("freshness", {}).get("as_of"),
                "confidence": risk.get("confidence_score"),
            }
        )

    if not claims:
        return {"ok": False, "error": "insufficient_data_for_brief"}

    title = f"BLACKDARK Daily Brief — {sym} ({_utcnow()[:10]})"
    summary = f"Auto-generated brief for {sym} with {len(claims)} evidence-linked claims."
    created = create_insight(
        author="blackdark_research",
        title=title,
        summary=summary,
        claims=claims,
        confidence=float(health.get("overall_score") or 50),
    )
    if created.get("ok"):
        iid = created["insight"]["id"]
        moderate_insight(insight_id=iid, action="approve", moderator="auto_generator", notes="Auto-published internal brief")
    return created


def quicktake_status() -> dict[str, Any]:
    store = _load_store()
    insights = list(store.get("insights", {}).values())
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product": "BLACKDARK Daily Brief",
        "moderation_required": True,
        "no_ungrounded_claims": True,
        "total_insights": len(insights),
        "published": sum(1 for i in insights if i.get("moderation_state") == "published"),
        "pending": sum(1 for i in insights if i.get("moderation_state") == "pending_moderation"),
        "timestamp": _utcnow(),
    }
