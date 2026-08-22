"""Didit live KYC integration — sessions, webhooks, institutional case sync."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

_LOCK = threading.Lock()
_PROCESSED_EVENTS: set[str] = set()

DIDIT_API_BASE = "https://verification.didit.me"
WEBHOOK_PATH = "/api/webhooks/didit"

_STATUS_TO_DECISION = {
    "approved": "approved",
    "declined": "rejected",
    "in review": "pending_review",
    "resubmitted": "needs_info",
    "abandoned": "rejected",
    "awaiting user": "needs_info",
    "not started": "pending_review",
    "in progress": "pending_review",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _base_url() -> str:
    return (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")


def webhook_url() -> str:
    base = _base_url()
    if not base:
        return WEBHOOK_PATH
    return f"{base}{WEBHOOK_PATH}"


def didit_config() -> dict[str, str]:
    return {
        "api_key": (os.getenv("DIDIT_API_KEY") or "").strip(),
        "webhook_secret": (
            os.getenv("DIDIT_WEBHOOK_SECRET")
            or os.getenv("DIDIT_WEBHOOK_SECRET_KEY")
            or ""
        ).strip(),
        "workflow_id": (os.getenv("DIDIT_WORKFLOW_ID") or "").strip(),
    }


def didit_api_configured() -> bool:
    return bool(didit_config()["api_key"])


def didit_configured() -> bool:
    cfg = didit_config()
    return bool(cfg["api_key"] and cfg["webhook_secret"])


def didit_live_ready() -> bool:
    cfg = didit_config()
    return bool(cfg["api_key"] and cfg["webhook_secret"] and cfg["workflow_id"])


def _shorten_floats(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _shorten_floats(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_shorten_floats(x) for x in data]
    if isinstance(data, float) and data.is_integer():
        return int(data)
    return data


def verify_webhook_signature(
    body_json: dict[str, Any],
    *,
    signature_v2: str | None,
    signature_simple: str | None,
    timestamp: str | None,
    secret: str,
) -> bool:
    if not timestamp or not secret:
        return False
    try:
        if abs(int(time.time()) - int(timestamp)) > 300:
            return False
    except ValueError:
        return False

    if signature_v2:
        canonical = json.dumps(
            _shorten_floats(body_json),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        expected = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature_v2, expected):
            return True

    if signature_simple:
        canonical = ":".join(
            [
                str(body_json.get("timestamp", "")),
                str(body_json.get("session_id", "")),
                str(body_json.get("status", "")),
                str(body_json.get("webhook_type", "")),
            ]
        )
        expected = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature_simple, expected):
            return True
    return False


def _map_status(status: str) -> str:
    return _STATUS_TO_DECISION.get(str(status or "").strip().lower(), "pending_review")


async def create_verification_session(
    *,
    email: str,
    legal_name: str,
    country: str,
    case_id: str,
    org_id: str | None = None,
) -> dict[str, Any]:
    cfg = didit_config()
    if not cfg["api_key"] or not cfg["workflow_id"]:
        raise ValueError("didit_not_configured")
    callback = f"{_base_url()}/institutional?kyc=1" if _base_url() else None
    payload: dict[str, Any] = {
        "workflow_id": cfg["workflow_id"],
        "vendor_data": case_id,
        "metadata": {
            "case_id": case_id,
            "email": email.strip().lower(),
            "legal_name": legal_name.strip(),
            "country": country.strip().upper()[:2],
            "org_id": org_id,
        },
        "contact_details": {
            "email": email.strip().lower(),
            "email_lang": "en",
            "send_notification_emails": False,
        },
    }
    if callback:
        payload["callback"] = callback
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{DIDIT_API_BASE}/v3/session/",
            headers={"x-api-key": cfg["api_key"], "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    return {
        "session_id": data.get("session_id"),
        "verification_url": data.get("url"),
        "status": data.get("status"),
        "vendor_data": data.get("vendor_data"),
        "provider": "didit",
        "live": True,
    }


def process_webhook_event(body: dict[str, Any]) -> dict[str, Any]:
    """Apply Didit webhook to institutional KYC case ledger (idempotent)."""
    event_id = str(body.get("event_id") or "")
    if event_id:
        with _LOCK:
            if event_id in _PROCESSED_EVENTS:
                return {"ok": True, "duplicate": True, "event_id": event_id}
            _PROCESSED_EVENTS.add(event_id)
            if len(_PROCESSED_EVENTS) > 5000:
                _PROCESSED_EVENTS.clear()

    webhook_type = str(body.get("webhook_type") or "")
    if webhook_type not in {"status.updated", "data.updated"}:
        return {"ok": True, "ignored": webhook_type or "unknown"}

    session_id = str(body.get("session_id") or "")
    status = str(body.get("status") or "")
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
    vendor_data = str(body.get("vendor_data") or metadata.get("case_id") or "")
    email = str(metadata.get("email") or "").strip().lower()
    legal_name = str(metadata.get("legal_name") or "").strip()
    country = str(metadata.get("country") or "").strip().upper()[:2]
    org_id = metadata.get("org_id")
    decision = _map_status(status)

    from institutional_commerce import apply_didit_kyc_update, open_kyc_case

    if vendor_data:
        updated = apply_didit_kyc_update(
            case_id=vendor_data,
            session_id=session_id,
            provider_status=status,
            decision=decision,
            event_id=event_id,
            environment=str(body.get("environment") or "live"),
        )
        if updated:
            return {"ok": True, "case_id": vendor_data, "status": status, "decision": decision}

    if email:
        case = open_kyc_case(
            email=email,
            legal_name=legal_name or email.split("@")[0],
            country=country or "US",
            org_id=org_id,
            provider="didit",
            session_id=session_id,
            provider_status=status,
            status=decision if decision != "pending_review" else "pending_review",
        )
        return {"ok": True, "created_case_id": case["case_id"], "status": status, "decision": decision}

    fallback_id = f"kyc_{uuid4().hex[:12]}"
    case = open_kyc_case(
        email=f"didit+{session_id[:8]}@blackdark.local",
        legal_name="Didit Session",
        country="US",
        provider="didit",
        session_id=session_id,
        provider_status=status,
        status=decision,
    )
    return {"ok": True, "created_case_id": case["case_id"], "fallback": True, "status": status}


def didit_status() -> dict[str, Any]:
    cfg = didit_config()
    return {
        "provider": "didit",
        "configured": didit_configured(),
        "api_configured": didit_api_configured(),
        "live_ready": didit_live_ready(),
        "workflow_id_set": bool(cfg["workflow_id"]),
        "webhook_url": webhook_url(),
        "api": {
            "create_session": "POST /api/institutional/commerce/kyc/didit/session",
            "webhook": f"POST {WEBHOOK_PATH}",
        },
    }
