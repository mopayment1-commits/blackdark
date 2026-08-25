"""
Chart / Idea Sharing — Feature #177 compatibility layer.

Delegates to Public Content Hub (#177 + #182 merged).
"""

from __future__ import annotations

from typing import Any

from bd_platform.public_content_hub import (
    clone_content,
    create_content,
    get_public_view,
    list_user_content,
    publish_content,
    public_content_hub_status,
    update_content_draft,
)


def create_chart_share(
    *,
    owner_id: str,
    title: str,
    chart_type: str = "idea",
    chart_data: dict[str, Any] | None = None,
    notes: str = "",
    privacy: str = "private",
) -> dict[str, Any]:
    result = create_content(
        owner_id=owner_id,
        title=title,
        content_type="idea" if chart_type == "idea" else "chart",
        content_data=chart_data or {},
        notes=notes,
        privacy=privacy,  # type: ignore[arg-type]
    )
    if result.get("ok"):
        share = result.pop("content", {})
        result["share"] = share
        result["feature_id"] = 177
    return result


def publish_chart_share(*, share_id: str, owner_id: str, privacy: str = "unlisted") -> dict[str, Any]:
    result = publish_content(item_id=share_id, owner_id=owner_id, privacy=privacy)  # type: ignore[arg-type]
    if result.get("ok"):
        share = result.pop("content", {})
        result["share"] = share
        result["feature_id"] = 177
    return result


def update_chart_share(
    *,
    share_id: str,
    owner_id: str,
    title: str | None = None,
    chart_data: dict[str, Any] | None = None,
    notes: str | None = None,
    privacy: str | None = None,
) -> dict[str, Any]:
    result = update_content_draft(
        item_id=share_id,
        owner_id=owner_id,
        title=title,
        content_data=chart_data,
        notes=notes,
        privacy=privacy,  # type: ignore[arg-type]
    )
    if result.get("ok"):
        share = result.pop("content", {})
        result["share"] = share
    return result


def get_public_chart_view(slug: str) -> dict[str, Any]:
    result = get_public_view(slug)
    if result.get("ok"):
        snap = result.get("snapshot") or {}
        result["chart_type"] = snap.get("content_type")
        result["snapshot"] = {
            "title": snap.get("title"),
            "chart_type": snap.get("content_type"),
            "chart_data": snap.get("content_data"),
            "notes": snap.get("notes"),
            "captured_at": snap.get("captured_at"),
        }
        result["feature_id"] = 177
    return result


def list_user_chart_shares(owner_id: str, *, limit: int = 50) -> dict[str, Any]:
    result = list_user_content(owner_id, limit=limit)
    if result.get("ok"):
        result["shares"] = result.pop("items", [])
        result["feature_id"] = 177
    return result


def chart_sharing_status() -> dict[str, Any]:
    status = public_content_hub_status()
    status["feature_id"] = 177
    status["title"] = "Chart / Idea Sharing (Public Content Hub)"
    return status


def clone_chart_share(*, share_id: str, owner_id: str) -> dict[str, Any]:
    result = clone_content(item_id=share_id, owner_id=owner_id)
    if result.get("ok"):
        share = result.pop("content", {})
        result["share"] = share
        result["feature_id"] = 177
    return result
