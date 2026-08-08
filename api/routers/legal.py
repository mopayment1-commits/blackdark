"""Legal / terms acceptance + system classification API."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request, Response

from api.deps import optional_user
from legal_shield import CONSENT_ACK_TEXT, system_classification_payload
from terms_consent import (
    TERMS_COOKIE,
    TERMS_VERSION,
    has_accepted_terms,
    record_terms_acceptance,
    terms_status_payload,
)

router = APIRouter(tags=["legal"])


@router.get("/api/legal/terms-status")
async def terms_status(request: Request, user: dict | None = Depends(optional_user)):
    accepted = await has_accepted_terms(request, user)
    return terms_status_payload(accepted)


@router.post("/api/legal/accept-terms")
async def accept_terms(
    request: Request,
    response: Response,
    user: dict | None = Depends(optional_user),
    body: dict = Body(default={}),
):
    """
    Explicit consent gate (Layer 3).
    Client must send ack=true confirming CONSENT_ACK_TEXT.
    """
    ack = body.get("ack") in {True, "true", 1, "1", "yes"}
    ack_text = str(body.get("ack_text") or "").strip()
    if not ack:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail={
                "error": "ack_required",
                "message": "You must explicitly acknowledge the consent text.",
                "ack_text": CONSENT_ACK_TEXT,
            },
        )
    if ack_text and ack_text != CONSENT_ACK_TEXT:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail={
                "error": "ack_text_mismatch",
                "message": "Consent text mismatch.",
                "ack_text": CONSENT_ACK_TEXT,
            },
        )

    ip = request.client.host if request.client else ""
    result = await record_terms_acceptance(
        user=user,
        source=str(body.get("source") or "consent_modal"),
        ip=ip,
    )
    result["ack_text"] = CONSENT_ACK_TEXT
    secure = request.url.scheme == "https"
    response.set_cookie(
        key=TERMS_COOKIE,
        value=TERMS_VERSION,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=365 * 24 * 3600,
        path="/",
    )
    return result


@router.get("/api/status")
async def api_status():
    """Public system status including Layer-2 classification metadata."""
    payload = system_classification_payload()
    payload["ok"] = True
    payload["service"] = "blackdark"
    return payload


@router.get("/system/info")
async def system_info():
    """Alias surface for institutional scanners / buyers."""
    return system_classification_payload()


@router.get("/api/legal/shield")
async def legal_shield_status():
    return system_classification_payload()
