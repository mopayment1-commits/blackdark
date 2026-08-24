"""
Chart / Idea Sharing — Feature #177 (Sprint 2 Growth Engine).

Simple flow: Share → Public Link → Immutable Snapshot.

Privacy: private | unlisted | public
Immutable snapshot on publish — original edits do not change published view.
Watermark on all public charts: "Powered by BLACKDARK" + signup link.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ChartSharing")

_FEATURE_ID = 177
_STORE_PATH = Path("data/chart_shares.json")
_WATERMARK_TEXT = "Powered by BLACKDARK"
_SIGNUP_URL = "/create-checkout-session?tier=pro"
Privacy = Literal["private", "unlisted", "public"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _share_id() -> str:
    return f"shr_{secrets.token_urlsafe(10)}"


def _public_slug() -> str:
    return secrets.token_urlsafe(12)


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return {"shares": {}}
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"shares": {}}


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_chart_share(
    *,
    owner_id: str,
    title: str,
    chart_type: str = "idea",
    chart_data: dict[str, Any] | None = None,
    notes: str = "",
    privacy: Privacy = "private",
) -> dict[str, Any]:
    """Create a saved chart/idea — draft, not yet published."""
    store = _load_store()
    share_id = _share_id()
    now = _utcnow()
    row = {
        "id": share_id,
        "owner_id": str(owner_id),
        "title": title.strip() or "Untitled chart",
        "chart_type": chart_type,
        "chart_data": chart_data or {},
        "notes": notes,
        "privacy": privacy,
        "published": False,
        "immutable_snapshot": None,
        "snapshot_hash": None,
        "public_slug": None,
        "public_url": None,
        "watermark": None,
        "created_at": now,
        "updated_at": now,
        "published_at": None,
    }
    store["shares"][share_id] = row
    _save_store(store)
    return {"ok": True, "feature_id": _FEATURE_ID, "share": _public_row(row, include_snapshot=False)}


def publish_chart_share(
    *,
    share_id: str,
    owner_id: str,
    privacy: Privacy = "unlisted",
) -> dict[str, Any]:
    """
    Publish immutable snapshot — frozen at publish time.
    Original chart edits after publish do NOT affect public view.
    """
    store = _load_store()
    row = store.get("shares", {}).get(share_id)
    if not row:
        return {"ok": False, "error": "share_not_found"}
    if str(row.get("owner_id")) != str(owner_id):
        return {"ok": False, "error": "access_denied"}

    snapshot = {
        "title": row.get("title"),
        "chart_type": row.get("chart_type"),
        "chart_data": json.loads(json.dumps(row.get("chart_data") or {})),
        "notes": row.get("notes"),
        "captured_at": _utcnow(),
    }
    slug = row.get("public_slug") or _public_slug()
    row["immutable_snapshot"] = snapshot
    row["snapshot_hash"] = _snapshot_hash(snapshot)
    row["privacy"] = privacy
    row["published"] = True
    row["published_at"] = _utcnow()
    row["updated_at"] = row["published_at"]
    row["public_slug"] = slug
    row["public_url"] = f"/share/chart/{slug}"
    row["watermark"] = {
        "text": _WATERMARK_TEXT,
        "signup_url": _SIGNUP_URL,
        "immutable": True,
    }
    store["shares"][share_id] = row
    _save_store(store)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "share": _public_row(row, include_snapshot=True),
        "message": "Immutable snapshot published — edits to original will not change this view",
    }


def update_chart_share(
    *,
    share_id: str,
    owner_id: str,
    title: str | None = None,
    chart_data: dict[str, Any] | None = None,
    notes: str | None = None,
    privacy: Privacy | None = None,
) -> dict[str, Any]:
    """Update draft or original — does NOT mutate published immutable snapshot."""
    store = _load_store()
    row = store.get("shares", {}).get(share_id)
    if not row:
        return {"ok": False, "error": "share_not_found"}
    if str(row.get("owner_id")) != str(owner_id):
        return {"ok": False, "error": "access_denied"}

    if title is not None:
        row["title"] = title
    if chart_data is not None:
        row["chart_data"] = chart_data
    if notes is not None:
        row["notes"] = notes
    if privacy is not None:
        row["privacy"] = privacy
    row["updated_at"] = _utcnow()
    store["shares"][share_id] = row
    _save_store(store)

    return {
        "ok": True,
        "share": _public_row(row, include_snapshot=bool(row.get("published"))),
        "published_snapshot_unchanged": bool(row.get("published")),
    }


def get_public_chart_view(slug: str) -> dict[str, Any]:
    """Public/unlisted view — returns immutable snapshot only."""
    store = _load_store()
    for row in store.get("shares", {}).values():
        if row.get("public_slug") != slug:
            continue
        if row.get("privacy") == "private":
            return {"ok": False, "error": "private_share"}
        if not row.get("published") or not row.get("immutable_snapshot"):
            return {"ok": False, "error": "not_published"}
        snap = row["immutable_snapshot"]
        return {
            "ok": True,
            "feature_id": _FEATURE_ID,
            "view": "public",
            "title": snap.get("title"),
            "chart_type": snap.get("chart_type"),
            "snapshot": snap,
            "snapshot_hash": row.get("snapshot_hash"),
            "immutable": True,
            "watermark": row.get("watermark") or {"text": _WATERMARK_TEXT, "signup_url": _SIGNUP_URL},
            "published_at": row.get("published_at"),
            "privacy": row.get("privacy"),
        }
    return {"ok": False, "error": "share_not_found"}


def list_user_chart_shares(owner_id: str, *, limit: int = 50) -> dict[str, Any]:
    store = _load_store()
    rows = [
        _public_row(r, include_snapshot=False)
        for r in store.get("shares", {}).values()
        if str(r.get("owner_id")) == str(owner_id)
    ]
    rows.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return {"ok": True, "feature_id": _FEATURE_ID, "shares": rows[:limit], "count": len(rows[:limit])}


def _public_row(row: dict[str, Any], *, include_snapshot: bool) -> dict[str, Any]:
    out = {
        "id": row.get("id"),
        "title": row.get("title"),
        "chart_type": row.get("chart_type"),
        "privacy": row.get("privacy"),
        "published": bool(row.get("published")),
        "public_url": row.get("public_url"),
        "public_slug": row.get("public_slug"),
        "snapshot_hash": row.get("snapshot_hash"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "published_at": row.get("published_at"),
    }
    if include_snapshot and row.get("immutable_snapshot"):
        out["immutable_snapshot"] = row["immutable_snapshot"]
        out["watermark"] = row.get("watermark")
    return out


def chart_sharing_status() -> dict[str, Any]:
    store = _load_store()
    shares = list(store.get("shares", {}).values())
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Chart / Idea Sharing",
        "privacy_modes": ["private", "unlisted", "public"],
        "immutable_on_publish": True,
        "watermark": _WATERMARK_TEXT,
        "signup_url": _SIGNUP_URL,
        "total_shares": len(shares),
        "published_count": sum(1 for s in shares if s.get("published")),
        "flow": "Share → Public Link → Immutable Snapshot",
        "timestamp": _utcnow(),
    }
