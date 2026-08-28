"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from security_auth import require_admin, require_authenticated

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/privacy", tags=["privacy"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def privacy_status():
    from bd_platform.infrastructure_gdpr_compliance_layer import gdpr_compliance_status_1023

    legacy = {}
    try:
        from gdpr_service import gdpr_compliance_status

        legacy = gdpr_compliance_status()
    except Exception:
        pass
    status = gdpr_compliance_status_1023()
    status["legacy"] = legacy
    return status


@router.get("/gdpr/status")
async def gdpr_status():
    from bd_platform.infrastructure_gdpr_compliance_layer import gdpr_compliance_status_1023

    return gdpr_compliance_status_1023()


@router.get("/gdpr/residency")
async def gdpr_residency():
    from bd_platform.infrastructure_gdpr_compliance_layer import get_data_residency_map_1023

    return get_data_residency_map_1023()


@router.get("/gdpr/retention")
async def gdpr_retention():
    from bd_platform.infrastructure_gdpr_compliance_layer import get_retention_alignment_1023

    return get_retention_alignment_1023()


@router.get("/gdpr/dpo")
async def gdpr_dpo():
    from bd_platform.infrastructure_gdpr_compliance_layer import get_dpo_contact_1023

    return get_dpo_contact_1023()


@router.get("/gdpr/breach-playbook")
async def gdpr_breach_playbook():
    from bd_platform.infrastructure_gdpr_compliance_layer import get_breach_notification_playbook_1023

    return get_breach_notification_playbook_1023()


@router.get("/gdpr/minimization")
async def gdpr_minimization():
    from bd_platform.infrastructure_gdpr_compliance_layer import get_data_minimization_policy_1023

    return get_data_minimization_policy_1023()


@router.get("/gdpr/production-gate")
async def gdpr_production_gate():
    from bd_platform.infrastructure_gdpr_compliance_layer import check_production_gate_1023

    return check_production_gate_1023()


@router.post("/gdpr/consent", responses=COMMON_ERROR_RESPONSES)
async def gdpr_consent(
    data: dict = Body(default={}),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.infrastructure_gdpr_compliance_layer import record_explicit_consent_1023

    result = record_explicit_consent_1023(
        user_id=user.get("id"),
        consent_type=data.get("consent_type", "sensitive_data"),
        granted=bool(data.get("granted", False)),
        preticked=bool(data.get("preticked", False)),
        lang=data.get("lang", "en"),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/gdpr/portability", responses=COMMON_ERROR_RESPONSES)
async def gdpr_portability(
    fmt: str = Query("json"),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.infrastructure_gdpr_compliance_layer import export_portable_data_1023

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    return await export_portable_data_1023(email=email, fmt=fmt)


@router.post("/dsr/export", responses=COMMON_ERROR_RESPONSES)
async def dsr_export(user: dict = Depends(require_authenticated)):
    """Authenticated user exports their own data (GDPR Art. 15/20)."""
    from bd_platform.infrastructure_gdpr_compliance_layer import export_portable_data_1023

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    return await export_portable_data_1023(email=email, fmt="json")


@router.post("/dsr/erase", responses=COMMON_ERROR_RESPONSES)
async def dsr_erase(
    user: dict = Depends(require_authenticated),
    body: dict = Body(default={}),
):
    """Authenticated user requests erasure (GDPR Art. 17) — legacy direct erase."""
    from gdpr_service import erase_user_data

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    confirm = body.get("confirm") in {True, "true", "1"}
    return await erase_user_data(email, confirmed=confirm)


@router.get("/gdpr/e2e")
async def gdpr_e2e(_admin: dict = Depends(require_admin)):
    from bd_platform.infrastructure_gdpr_compliance_layer import run_gdpr_compliance_e2e_1023

    return await run_gdpr_compliance_e2e_1023()
