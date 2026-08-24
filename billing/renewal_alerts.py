"""5-day renewal warning scanner — Phase 1 of Feature #9."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config

from billing.subscription_store import list_renewal_warning_candidates

logger = logging.getLogger("BLACKDARK.Billing.RenewalAlerts")

_SENT_PATH = Path("data/renewal_warnings_sent.jsonl")


def _warning_days() -> int:
    return int(getattr(config, "BILLING_RENEWAL_WARNING_DAYS", 5))


def _already_sent(user_id: int, period_end: str) -> bool:
    key = f"{user_id}:{period_end}"
    if not _SENT_PATH.exists():
        return False
    try:
        for line in _SENT_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("key") == key:
                return True
    except (OSError, json.JSONDecodeError):
        pass
    return False


def _mark_sent(user_id: int, period_end: str, *, email: str) -> None:
    key = f"{user_id}:{period_end}"
    row = {"key": key, "user_id": user_id, "email": email, "period_end": period_end, "sent_at": datetime.now(UTC).isoformat()}
    try:
        _SENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SENT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    except OSError:
        pass


async def run_renewal_warning_scan() -> dict[str, Any]:
    """
    Notify users whose subscription ends within BILLING_RENEWAL_WARNING_DAYS (default 5).
    Idempotent per user+period_end.
    """
    from in_app_alerts import push_in_app_alert

    days = _warning_days()
    candidates = await list_renewal_warning_candidates(warning_days=days)
    sent = 0
    skipped = 0
    for sub in candidates:
        uid = int(sub["user_id"])
        period_end = str(sub.get("current_period_end") or "")
        email = str(sub.get("email") or "")
        if _already_sent(uid, period_end):
            skipped += 1
            continue
        plan = str(sub.get("plan") or "pro").upper()
        try:
            end_dt = datetime.fromisoformat(period_end)
            days_left = max(0, (end_dt - datetime.now(UTC)).days)
        except ValueError:
            days_left = days
        push_in_app_alert(
            f"Subscription renews in {days_left} days",
            f"Your {plan} plan ends on {period_end[:10]}. Renew now to keep premium features active.",
            payload={"user_id": uid, "plan": sub.get("plan"), "period_end": period_end, "days_left": days_left},
            user_email=email or None,
            level="warning",
        )
        try:
            from distribution_compounding import track_subscription_event

            await track_subscription_event(
                event_type="subscription_renewal_warning",
                user_id=uid,
                payload={"plan": sub.get("plan"), "days_left": days_left, "period_end": period_end},
            )
        except Exception:
            pass
        _mark_sent(uid, period_end, email=email)
        sent += 1
    return {"warning_days": days, "candidates": len(candidates), "sent": sent, "skipped": skipped}
