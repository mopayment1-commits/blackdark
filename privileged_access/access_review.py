"""Periodic access recertification (FDS-23 / SDG-18)."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

ReviewDecision = Literal["KEEP", "REVOKE", "MODIFY"]
_DEFAULT_CADENCE_DAYS = int(os.getenv("ACCESS_REVIEW_CADENCE_DAYS", "90"))


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "access_review_evidence.jsonl"


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def record_access_review(
    *,
    reviewer: str,
    subject: str,
    grant_type: str,
    decision: ReviewDecision,
    reason: str,
    next_review_days: int | None = None,
) -> dict[str, Any]:
    cadence = _DEFAULT_CADENCE_DAYS if next_review_days is None else next_review_days
    now = time.time()
    rec = {
        "recorded_at": _utcnow_iso(),
        "reviewer": reviewer.strip().lower(),
        "subject": subject.strip().lower(),
        "grant_type": grant_type,
        "decision": decision,
        "reason": reason.strip(),
        "next_review_at": now + cadence * 86400,
        "cadence_days": cadence,
    }
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def list_access_reviews(limit: int = 100) -> list[dict[str, Any]]:
    path = _ledger_path()
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def overdue_reviews(now: float | None = None) -> list[dict[str, Any]]:
    now = now if now is not None else time.time()
    latest: dict[str, dict[str, Any]] = {}
    for rec in list_access_reviews(limit=1000):
        subj = str(rec.get("subject") or "")
        latest[subj] = rec
    overdue: list[dict[str, Any]] = []
    for subj, rec in latest.items():
        if float(rec.get("next_review_at") or 0) < now:
            overdue.append({"subject": subj, "last_review": rec})
    return overdue


def privileged_inventory() -> list[dict[str, Any]]:
    from security_auth import admin_emails

    items = [
        {
            "subject": email,
            "grant_type": "human_admin_email",
            "review_required": True,
        }
        for email in sorted(admin_emails())
    ]
    return items


def access_review_status() -> dict[str, Any]:
    return {
        "cadence_days": _DEFAULT_CADENCE_DAYS,
        "inventory_count": len(privileged_inventory()),
        "overdue_count": len(overdue_reviews()),
        "evidence_path": str(_ledger_path()),
    }
