"""
Public Content Hub — Features #177 + #182 (merged).

Unified engine for Chart/Idea Sharing and Public Dashboard Sharing.
- Snapshot + version on publish (immutable vs draft edits)
- Privacy: private | unlisted | public
- Watermark: Powered by BLACKDARK + signup link
- Public access: view + clone only — no public editing
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PublicContentHub")

_FEATURE_IDS = (177, 182)
_STORE_PATH = Path("data/public_content_hub.json")
_WATERMARK_TEXT = "Powered by BLACKDARK"
_SIGNUP_URL = "/create-checkout-session?tier=pro"
Privacy = Literal["private", "unlisted", "public"]
ContentType = Literal["chart", "idea", "dashboard"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _item_id() -> str:
    return f"cnt_{secrets.token_urlsafe(10)}"


def _public_slug() -> str:
    return secrets.token_urlsafe(12)


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return {"items": {}}
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"items": {}}


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _watermark_block() -> dict[str, Any]:
    return {
        "text": _WATERMARK_TEXT,
        "signup_url": _SIGNUP_URL,
        "immutable": True,
    }


def _public_url_for(content_type: str, slug: str) -> str:
    if content_type == "dashboard":
        return f"/share/dashboard/{slug}"
    return f"/share/content/{slug}"


def create_content(
    *,
    owner_id: str,
    title: str,
    content_type: ContentType = "chart",
    content_data: dict[str, Any] | None = None,
    notes: str = "",
    privacy: Privacy = "private",
    dashboard_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a draft chart, idea, or dashboard share — not yet published."""
    store = _load_store()
    item_id = _item_id()
    now = _utcnow()
    row = {
        "id": item_id,
        "owner_id": str(owner_id),
        "content_type": content_type,
        "title": title.strip() or "Untitled",
        "content_data": content_data or {},
        "dashboard_metadata": dashboard_metadata or {},
        "notes": notes,
        "privacy": privacy,
        "published": False,
        "version": 0,
        "immutable_snapshot": None,
        "snapshot_hash": None,
        "public_slug": None,
        "public_url": None,
        "watermark": None,
        "permissions": {
            "public_editing": False,
            "clone_allowed": True,
            "view_only": True,
        },
        "created_at": now,
        "updated_at": now,
        "published_at": None,
    }
    store["items"][item_id] = row
    _save_store(store)
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "content": _public_row(row, include_snapshot=False),
    }


def publish_content(
    *,
    item_id: str,
    owner_id: str,
    privacy: Privacy = "unlisted",
) -> dict[str, Any]:
    """Publish immutable snapshot — frozen at publish time. Increments version."""
    store = _load_store()
    row = store.get("items", {}).get(item_id)
    if not row:
        return {"ok": False, "error": "content_not_found"}
    if str(row.get("owner_id")) != str(owner_id):
        return {"ok": False, "error": "access_denied"}

    version = int(row.get("version") or 0) + 1
    snapshot = {
        "title": row.get("title"),
        "content_type": row.get("content_type"),
        "content_data": json.loads(json.dumps(row.get("content_data") or {})),
        "dashboard_metadata": json.loads(json.dumps(row.get("dashboard_metadata") or {})),
        "notes": row.get("notes"),
        "version": version,
        "captured_at": _utcnow(),
    }
    slug = row.get("public_slug") or _public_slug()
    content_type = str(row.get("content_type") or "chart")
    row["immutable_snapshot"] = snapshot
    row["snapshot_hash"] = _snapshot_hash(snapshot)
    row["privacy"] = privacy
    row["published"] = True
    row["version"] = version
    row["published_at"] = _utcnow()
    row["updated_at"] = row["published_at"]
    row["public_slug"] = slug
    row["public_url"] = _public_url_for(content_type, slug)
    row["watermark"] = _watermark_block()
    store["items"][item_id] = row
    _save_store(store)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "content": _public_row(row, include_snapshot=True),
        "version": version,
        "message": (
            "Immutable snapshot published — edits to the draft will not change this view. "
            "Public access is view + clone only."
        ),
    }


def update_content_draft(
    *,
    item_id: str,
    owner_id: str,
    title: str | None = None,
    content_data: dict[str, Any] | None = None,
    dashboard_metadata: dict[str, Any] | None = None,
    notes: str | None = None,
    privacy: Privacy | None = None,
) -> dict[str, Any]:
    """Update owner draft — does NOT mutate published immutable snapshot."""
    store = _load_store()
    row = store.get("items", {}).get(item_id)
    if not row:
        return {"ok": False, "error": "content_not_found"}
    if str(row.get("owner_id")) != str(owner_id):
        return {"ok": False, "error": "access_denied"}

    if title is not None:
        row["title"] = title
    if content_data is not None:
        row["content_data"] = content_data
    if dashboard_metadata is not None:
        row["dashboard_metadata"] = dashboard_metadata
    if notes is not None:
        row["notes"] = notes
    if privacy is not None:
        row["privacy"] = privacy
    row["updated_at"] = _utcnow()
    store["items"][item_id] = row
    _save_store(store)

    return {
        "ok": True,
        "content": _public_row(row, include_snapshot=bool(row.get("published"))),
        "published_snapshot_unchanged": bool(row.get("published")),
    }


def get_public_view(slug: str) -> dict[str, Any]:
    """Public/unlisted view — immutable snapshot only, with watermark."""
    store = _load_store()
    for row in store.get("items", {}).values():
        if row.get("public_slug") != slug:
            continue
        if row.get("privacy") == "private":
            return {"ok": False, "error": "private_content"}
        if not row.get("published") or not row.get("immutable_snapshot"):
            return {"ok": False, "error": "not_published"}
        snap = row["immutable_snapshot"]
        return {
            "ok": True,
            "feature_ids": list(_FEATURE_IDS),
            "view": "public",
            "content_type": snap.get("content_type") or row.get("content_type"),
            "title": snap.get("title"),
            "snapshot": snap,
            "snapshot_hash": row.get("snapshot_hash"),
            "version": row.get("version"),
            "immutable": True,
            "watermark": row.get("watermark") or _watermark_block(),
            "permissions": row.get("permissions") or {"public_editing": False, "clone_allowed": True},
            "published_at": row.get("published_at"),
            "privacy": row.get("privacy"),
            "clone_endpoint": f"/api/platform/share/content/{row.get('id')}/clone",
        }
    return {"ok": False, "error": "content_not_found"}


def clone_content(*, item_id: str, owner_id: str) -> dict[str, Any]:
    """Clone published snapshot into a new private draft for the requester."""
    store = _load_store()
    row = store.get("items", {}).get(item_id)
    if not row:
        return {"ok": False, "error": "content_not_found"}
    if not row.get("published") or not row.get("immutable_snapshot"):
        return {"ok": False, "error": "not_published"}

    perms = row.get("permissions") or {}
    if not perms.get("clone_allowed", True):
        return {"ok": False, "error": "clone_not_allowed"}

    if row.get("privacy") == "private" and str(row.get("owner_id")) != str(owner_id):
        return {"ok": False, "error": "access_denied"}

    snap = row["immutable_snapshot"]
    cloned = create_content(
        owner_id=owner_id,
        title=f"{snap.get('title') or 'Untitled'} (clone)",
        content_type=snap.get("content_type") or row.get("content_type") or "chart",  # type: ignore[arg-type]
        content_data=json.loads(json.dumps(snap.get("content_data") or {})),
        dashboard_metadata=json.loads(json.dumps(snap.get("dashboard_metadata") or {})),
        notes=str(snap.get("notes") or ""),
        privacy="private",
    )
    if cloned.get("ok"):
        cloned["cloned_from"] = item_id
        cloned["cloned_version"] = snap.get("version") or row.get("version")
    return cloned


def list_user_content(owner_id: str, *, limit: int = 50) -> dict[str, Any]:
    store = _load_store()
    rows = [
        _public_row(r, include_snapshot=False)
        for r in store.get("items", {}).values()
        if str(r.get("owner_id")) == str(owner_id)
    ]
    rows.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "items": rows[:limit],
        "count": len(rows[:limit]),
    }


async def capture_dashboard_snapshot(
    *,
    owner_id: str,
    title: str,
    asset: str = "BTC",
    privacy: Privacy = "private",
) -> dict[str, Any]:
    """Helper — capture Market Radar dashboard as shareable content (#182)."""
    from bd_platform.market_radar_dashboard import build_market_radar_dashboard

    dashboard = await build_market_radar_dashboard(asset)
    return create_content(
        owner_id=owner_id,
        title=title.strip() or f"Market Radar — {asset.upper()}",
        content_type="dashboard",
        content_data={"dashboard": dashboard},
        dashboard_metadata={
            "focus_asset": asset.upper(),
            "surface": "market_radar_dashboard",
            "feature_ids": dashboard.get("feature_ids") or [155, 140, 186, 142, 139],
        },
        privacy=privacy,
    )


def _public_row(row: dict[str, Any], *, include_snapshot: bool) -> dict[str, Any]:
    out = {
        "id": row.get("id"),
        "title": row.get("title"),
        "content_type": row.get("content_type"),
        "privacy": row.get("privacy"),
        "published": bool(row.get("published")),
        "version": row.get("version") or 0,
        "public_url": row.get("public_url"),
        "public_slug": row.get("public_slug"),
        "snapshot_hash": row.get("snapshot_hash"),
        "permissions": row.get("permissions"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "published_at": row.get("published_at"),
    }
    if include_snapshot and row.get("immutable_snapshot"):
        out["immutable_snapshot"] = row["immutable_snapshot"]
        out["watermark"] = row.get("watermark")
    return out


def public_content_hub_status() -> dict[str, Any]:
    store = _load_store()
    items = list(store.get("items", {}).values())
    return {
        "ok": True,
        "engine": "Public Content Hub",
        "feature_ids": list(_FEATURE_IDS),
        "merged_features": {
            177: "Chart / Idea Sharing",
            182: "Public Dashboard Sharing",
        },
        "content_types": ["chart", "idea", "dashboard"],
        "privacy_modes": ["private", "unlisted", "public"],
        "immutable_on_publish": True,
        "versioned_snapshots": True,
        "public_editing": False,
        "public_actions": ["view", "clone"],
        "watermark": _WATERMARK_TEXT,
        "signup_url": _SIGNUP_URL,
        "total_items": len(items),
        "published_count": sum(1 for s in items if s.get("published")),
        "flow": "Create → Publish snapshot → Share link → View / Clone",
        "timestamp": _utcnow(),
    }
