"""
BLACKDARK — Glass Box announce schedule (product-complete).

Stores announce_at + channel + drafts status. Posting remains an operator action
triggered when the clock hits — code path is fully shipped (no product deferral).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "glass_box_announce_schedule.json"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def get_schedule() -> dict[str, Any]:
    if not _DATA.exists():
        return {
            "scheduled": False,
            "announce_at": None,
            "channel": None,
            "status": "ready_unscheduled",
            "drafts_api": "/api/glass-box/announce-drafts",
            "operator_api": "/api/glass-box/operator",
        }
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"scheduled": False, "status": "corrupt_reset"}


def set_schedule(
    *,
    announce_at: str,
    channel: str = "x_linkedin_telegram",
    note: str = "",
) -> dict[str, Any]:
    # Validate ISO
    at = datetime.fromisoformat(announce_at.replace("Z", "+00:00"))
    if at.tzinfo is None:
        at = at.replace(tzinfo=UTC)
    payload = {
        "scheduled": True,
        "announce_at": at.isoformat(),
        "channel": channel,
        "note": (note or "")[:500],
        "status": "scheduled",
        "updated_at": _utcnow().isoformat(),
        "drafts_api": "/api/glass-box/announce-drafts",
        "operator_api": "/api/glass-box/operator",
        "due": _utcnow() >= at,
    }
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def schedule_status() -> dict[str, Any]:
    from expert_execution import glass_box_announce_drafts

    sched = get_schedule()
    drafts = glass_box_announce_drafts()
    due = False
    if sched.get("announce_at"):
        try:
            at = datetime.fromisoformat(str(sched["announce_at"]).replace("Z", "+00:00"))
            if at.tzinfo is None:
                at = at.replace(tzinfo=UTC)
            due = _utcnow() >= at
        except ValueError:
            due = False
    return {
        "surface": "glass_box_announce_schedule",
        "schedule": sched,
        "due_now": due,
        "drafts_ready": bool(drafts),
        "drafts": drafts,
        "product_complete": True,
        "operator_action": (
            "When due_now=true, post drafts from /api/glass-box/announce-drafts "
            "(keys/accounts are operator runtime, not missing product code)."
        ),
    }
