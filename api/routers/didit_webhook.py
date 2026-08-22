"""Public Didit KYC webhook receiver."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES

logger = logging.getLogger("BLACKDARK.DiditWebhook")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"], responses=COMMON_ERROR_RESPONSES)


@router.post("/didit")
async def didit_webhook(request: Request) -> dict:
    from didit_kyc import didit_config, process_webhook_event, verify_webhook_signature

    cfg = didit_config()
    secret = cfg.get("webhook_secret") or ""
    if not secret:
        raise HTTPException(status_code=503, detail="didit_webhook_secret_not_configured")

    raw = await request.body()
    try:
        body = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid_json") from exc

    sig_v2 = request.headers.get("x-signature-v2") or request.headers.get("X-Signature-V2")
    sig_simple = request.headers.get("x-signature-simple") or request.headers.get("X-Signature-Simple")
    ts = request.headers.get("x-timestamp") or request.headers.get("X-Timestamp")
    if not verify_webhook_signature(
        body,
        signature_v2=sig_v2,
        signature_simple=sig_simple,
        timestamp=ts,
        secret=secret,
    ):
        raise HTTPException(status_code=401, detail="invalid_signature")

    try:
        result = process_webhook_event(body)
    except Exception:
        logger.exception("didit_webhook_processing_failed event_id=%s", body.get("event_id"))
        raise HTTPException(status_code=500, detail="processing_failed") from None
    return result


@router.get("/didit")
async def didit_webhook_health() -> dict:
    from didit_kyc import didit_status, webhook_url

    st = didit_status()
    return {
        "surface": "didit_kyc_webhook",
        "method": "POST",
        "url": webhook_url(),
        "configured": st["configured"],
        "live_ready": st["live_ready"],
    }
