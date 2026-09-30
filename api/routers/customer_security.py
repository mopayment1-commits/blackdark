"""Customer-accessible security logs (CISA Secure by Demand)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from fastapi import Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import require_authenticated

router = APIRouter(prefix="/api/security", tags=["customer-security"], responses=COMMON_ERROR_RESPONSES)


@router.get("/vdp")
async def public_vulnerability_disclosure_policy() -> dict[str, Any]:
    """Public VDP summary (FINDING-13 / ISO 29147); full text in repo policy."""
    return {
        "surface": "vulnerability_disclosure_policy",
        "policy_document": "docs/security/VULNERABILITY_DISCLOSURE_POLICY.md",
        "normative_alignment": ["ISO/IEC 29147", "CISA Secure by Demand (2024)"],
        "security_txt": "/.well-known/security.txt",
        "reporting": {
            "channel": "security.txt Contact field",
            "include": ["description", "impact", "reproduction", "affected_urls", "contact"],
        },
        "safe_harbor": "Good-faith research under published VDP scope; prohibited activities listed in policy",
        "honesty": {"cisa_certification_claimed": False},
    }


@router.get("/customer-logs/export")
async def export_customer_security_logs(
    request: Request,
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10_000),
    user: dict = Depends(require_authenticated),
) -> Response:
    from customer_security_log_service import export_customer_logs

    actor = str(user.get("email") or user.get("id") or "user")
    org_id = user.get("org_id")
    body, media_type, filename = export_customer_logs(
        actor_email=actor,
        org_id=str(org_id) if org_id else None,
        format=format,
        limit=limit,
    )
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/launch57-closure-status")
async def launch57_closure_status_api(
    _user: Annotated[dict, Depends(require_authenticated)],
) -> dict[str, Any]:
    from launch57_assurance_closure import launch57_closure_status

    return launch57_closure_status()


@router.get("/customer-logs/policy")
async def customer_security_log_policy(
    _user: Annotated[dict, Depends(require_authenticated)],
) -> dict[str, Any]:
    from security_events import security_log_retention_days

    return {
        "policy_document": "docs/security/CUSTOMER_SECURITY_LOG_POLICY.md",
        "retention_days": security_log_retention_days(),
        "included_in_baseline": True,
        "additional_charge": False,
        "categories": ["configuration", "identity_token", "business_data_access"],
    }
