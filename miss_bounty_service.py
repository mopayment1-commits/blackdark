"""Verified Miss Bounty — 20% off one subscription month (manual review)."""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from billing.plan_registry import PLAN_RANK, normalize_plan
from billing.subscription_engine import resolve_entitlements_for_user

ACCEPTED_PER_90_DAYS = 1
DAILY_SITE_APPROVALS = 3
DECISION_MIN_AGE_HOURS = 24
REVIEW_SLA_HOURS = 48
POST_REJECT_EXTRA_CLAIMS_30D = 1
PRICE_REL_TOLERANCE = 0.0005
DISCOUNT_PERCENT = 20
DISCOUNT_MONTHS = 1


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_prediction_id(decision_link: str) -> int | None:
    raw = (decision_link or "").strip()
    if raw.isdigit():
        return int(raw)
    m = re.search(r"(?:prediction[_-]?id=|#pred-?|/prediction/)(\d+)", raw, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"id[=:](\d+)", raw, re.I)
    if m:
        return int(m.group(1))
    return None


def _host(url: str) -> str:
    try:
        return (urlparse(url.strip()).hostname or "").lower()
    except Exception:
        return ""


def _prices_agree(a: float, b: float) -> bool:
    if a <= 0 or b <= 0:
        return False
    mid = (a + b) / 2.0
    return abs(a - b) / mid <= PRICE_REL_TOLERANCE


def _is_paid_plan(plan: str) -> bool:
    return PLAN_RANK.get(normalize_plan(plan), 0) >= PLAN_RANK["pro"]


async def _user_is_paid(user_id: int) -> bool:
    ent = await resolve_entitlements_for_user(int(user_id))
    plan = str(ent.get("effective_plan") or "free")
    if not _is_paid_plan(plan):
        return False
    return bool(ent.get("entitlement_allowed"))


async def _decision_eligible(prediction_id: int) -> tuple[bool, str, dict[str, Any] | None]:
    from database import fetch_oracle_prediction_public_row

    row = await fetch_oracle_prediction_public_row(prediction_id)
    if not row:
        return False, "Decision not found on public ledger", None
    if not row.get("resolved"):
        return False, "Decision not yet resolved on ledger", row
    label = str(row.get("label") or "").lower()
    if label != "incorrect":
        return False, "Only verified incorrect decisions qualify", row
    resolved_at = row.get("resolved_at") or row.get("timestamp")
    if not resolved_at:
        return False, "Missing resolution timestamp", row
    try:
        res_dt = datetime.fromisoformat(str(resolved_at).replace("Z", "+00:00"))
        if res_dt.tzinfo is None:
            res_dt = res_dt.replace(tzinfo=UTC)
    except ValueError:
        return False, "Invalid resolution timestamp", row
    age = _utcnow() - res_dt
    if age < timedelta(hours=DECISION_MIN_AGE_HOURS):
        return False, f"Decision must be on ledger for >{DECISION_MIN_AGE_HOURS}h", row
    return True, "ok", row


async def build_claim_eligibility(
    *,
    user_id: int | None,
    prediction_id: int,
) -> dict[str, Any]:
    ok_dec, reason, pred = await _decision_eligible(prediction_id)
    eligible = ok_dec
    reasons: list[str] = []
    if not ok_dec:
        reasons.append(reason)

    paid = False
    if user_id is None:
        reasons.append("Sign in with a paid plan to claim")
    else:
        paid = await _user_is_paid(user_id)
        if not paid:
            reasons.append("Paid subscription required at time of claim")

    if user_id is not None and ok_dec and paid:
        gate_ok, gate_reason = await _user_claim_limits_ok(user_id)
        if not gate_ok:
            eligible = False
            reasons.append(gate_reason)

    return {
        "prediction_id": prediction_id,
        "eligible": eligible and not reasons,
        "reasons": reasons,
        "decision": {
            "asset": (pred or {}).get("asset"),
            "verdict": (pred or {}).get("verdict"),
            "label": (pred or {}).get("label"),
            "timestamp": (pred or {}).get("timestamp"),
            "resolved_at": (pred or {}).get("resolved_at"),
        }
        if pred
        else None,
        "reward": {
            "type": "subscription_discount",
            "percent": DISCOUNT_PERCENT,
            "months": DISCOUNT_MONTHS,
            "note": "20% off one subscription month (not cash/USDT)",
        },
    }


async def _user_claim_limits_ok(user_id: int) -> tuple[bool, str]:
    from miss_bounty_store import user_miss_bounty_claims_since

    now = _utcnow()
    since_90 = (now - timedelta(days=90)).isoformat()
    approved = await user_miss_bounty_claims_since(
        user_id, since_iso=since_90, statuses=("approved",)
    )
    if len(approved) >= ACCEPTED_PER_90_DAYS:
        return False, "One accepted bounty per 90 days"

    since_30 = (now - timedelta(days=30)).isoformat()
    recent = await user_miss_bounty_claims_since(user_id, since_iso=since_30)
    rejections = [c for c in recent if c.get("status") in {"rejected", "auto_rejected"}]
    if rejections:
        latest_reject = max(rejections, key=lambda c: str(c.get("created_at") or ""))
        reject_at = str(latest_reject.get("created_at") or "")
        after = [c for c in recent if str(c.get("created_at") or "") > reject_at]
        if len(after) >= POST_REJECT_EXTRA_CLAIMS_30D:
            return False, "Only one follow-up claim allowed within 30 days after a rejection"

    return True, "ok"


async def _site_daily_approvals_ok() -> tuple[bool, str]:
    from miss_bounty_store import count_miss_bounty_approved_on_day

    day = _utcnow().date().isoformat()
    count = await count_miss_bounty_approved_on_day(day)
    if count >= DAILY_SITE_APPROVALS:
        return False, "Daily site approval cap reached (3/day)"
    return True, "ok"


async def submit_miss_bounty_claim(
    *,
    user_id: int,
    decision_link: str,
    source_a_url: str,
    source_b_url: str,
    source_a_close: float,
    source_b_close: float,
) -> dict[str, Any]:
    from miss_bounty_store import insert_miss_bounty_claim

    prediction_id = _parse_prediction_id(decision_link)
    if prediction_id is None:
        raise ValueError("Could not parse prediction id from decision link")

    elig = await build_claim_eligibility(user_id=user_id, prediction_id=prediction_id)
    if not elig.get("eligible"):
        raise ValueError("; ".join(elig.get("reasons") or ["Not eligible"]))

    ha, hb = _host(source_a_url), _host(source_b_url)
    if not ha or not hb:
        raise ValueError("Both source URLs must be valid https links")
    if ha == hb:
        raise ValueError("Sources must be from different domains")

    if not _prices_agree(float(source_a_close), float(source_b_close)):
        public_ref = f"mb_{secrets.token_hex(6)}"
        review_due = (_utcnow() + timedelta(hours=REVIEW_SLA_HOURS)).isoformat()
        claim_id = await insert_miss_bounty_claim(
            {
                "public_ref": public_ref,
                "user_id": user_id,
                "prediction_id": prediction_id,
                "decision_link": decision_link.strip(),
                "source_a_url": source_a_url.strip(),
                "source_b_url": source_b_url.strip(),
                "source_a_close": source_a_close,
                "source_b_close": source_b_close,
                "agreed_close": None,
                "status": "auto_rejected",
                "auto_reject_reason": "Closing prices differ between the two sources",
                "review_due_at": review_due,
            }
        )
        return {
            "claim_id": claim_id,
            "public_ref": public_ref,
            "status": "auto_rejected",
            "message": "Auto-rejected: closing prices differ between sources",
        }

    agreed = round((float(source_a_close) + float(source_b_close)) / 2.0, 8)
    public_ref = f"mb_{secrets.token_hex(6)}"
    review_due = (_utcnow() + timedelta(hours=REVIEW_SLA_HOURS)).isoformat()
    claim_id = await insert_miss_bounty_claim(
        {
            "public_ref": public_ref,
            "user_id": user_id,
            "prediction_id": prediction_id,
            "decision_link": decision_link.strip(),
            "source_a_url": source_a_url.strip(),
            "source_b_url": source_b_url.strip(),
            "source_a_close": source_a_close,
            "source_b_close": source_b_close,
            "agreed_close": agreed,
            "status": "pending_review",
            "auto_reject_reason": None,
            "review_due_at": review_due,
        }
    )
    return {
        "claim_id": claim_id,
        "public_ref": public_ref,
        "status": "pending_review",
        "review_due_at": review_due,
        "message": "Claim submitted for manual review (up to 48 hours)",
    }


async def approve_miss_bounty_claim(claim_id: int, *, reviewer_note: str = "") -> dict[str, Any]:
    from miss_bounty_store import fetch_miss_bounty_claim, update_miss_bounty_claim

    claim = await fetch_miss_bounty_claim(claim_id)
    if not claim:
        raise ValueError("Claim not found")
    if claim.get("status") != "pending_review":
        raise ValueError("Claim is not pending review")

    site_ok, site_reason = await _site_daily_approvals_ok()
    if not site_ok:
        raise ValueError(site_reason)

    user_id = int(claim["user_id"])
    since_90 = (_utcnow() - timedelta(days=90)).isoformat()
    from miss_bounty_store import user_miss_bounty_claims_since

    if await user_miss_bounty_claims_since(user_id, since_iso=since_90, statuses=("approved",)):
        raise ValueError("User already has an approved bounty in the last 90 days")

    now = _utcnow().isoformat()
    await update_miss_bounty_claim(
        claim_id,
        status="approved",
        reviewed_at=now,
        reviewer_note=(reviewer_note or "Approved — 20% off one subscription month").strip(),
    )
    await _grant_subscription_discount(user_id, claim_id=int(claim_id))
    return {"claim_id": claim_id, "status": "approved", "reward": {"percent": DISCOUNT_PERCENT, "months": DISCOUNT_MONTHS}}


async def reject_miss_bounty_claim(claim_id: int, *, reviewer_note: str = "") -> dict[str, Any]:
    from miss_bounty_store import fetch_miss_bounty_claim, update_miss_bounty_claim

    claim = await fetch_miss_bounty_claim(claim_id)
    if not claim:
        raise ValueError("Claim not found")
    if claim.get("status") != "pending_review":
        raise ValueError("Claim is not pending review")
    now = _utcnow().isoformat()
    await update_miss_bounty_claim(
        claim_id,
        status="rejected",
        reviewed_at=now,
        reviewer_note=(reviewer_note or "Rejected after manual review").strip(),
    )
    return {"claim_id": claim_id, "status": "rejected"}


async def _grant_subscription_discount(user_id: int, *, claim_id: int) -> None:
    from database import fetch_user_by_id
    from miss_bounty_store import insert_miss_bounty_reward

    user = await fetch_user_by_id(user_id)
    if not user:
        return
    await insert_miss_bounty_reward(
        user_id=user_id,
        claim_id=claim_id,
        discount_percent=DISCOUNT_PERCENT,
        billing_months=DISCOUNT_MONTHS,
    )
