"""Institutional readiness APIs — DD Reports 1+2 radical closure."""

from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import (
    optional_user_from_request,
    require_admin,
    require_authenticated,
    verify_admin_key,
)


async def require_institutional_principal(
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> dict:
    """Authenticated user OR fail-closed admin key (+ MFA when policy on)."""
    if verify_admin_key(x_admin_key):
        return await require_admin(user=user, x_admin_key=x_admin_key, x_admin_totp=x_admin_totp)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


router = APIRouter(
    prefix="/api/institutional",
    tags=["institutional"],
    responses=COMMON_ERROR_RESPONSES,
    dependencies=[Depends(require_institutional_principal)],
)

# Public OAuth/OIDC browser flow — Auth0 redirects here without prior session.
sso_router = APIRouter(
    prefix="/api/institutional",
    tags=["institutional-sso"],
    responses=COMMON_ERROR_RESPONSES,
)


def _sso_session_redirect(result: dict[str, Any]) -> RedirectResponse | JSONResponse:
    from security_middleware import attach_session_cookie

    token = result.get("token")
    base = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    if base and token:
        resp = RedirectResponse(url=f"{base}/dashboard?sso=1", status_code=302)
        attach_session_cookie(resp, str(token))
        return resp
    resp = JSONResponse(result)
    if token:
        attach_session_cookie(resp, str(token))
    return resp


class OrgCreate(BaseModel):
    name: str
    owner_email: str
    require_mfa: bool = True
    slug: str | None = None


class MemberAdd(BaseModel):
    email: str
    role: str = "analyst"


class RoleChange(BaseModel):
    email: str
    role: str
    actor_email: str


class MfaPolicy(BaseModel):
    require_mfa: bool
    actor_email: str


class SsoConfigure(BaseModel):
    org_id: str
    protocol: str = "oidc"
    issuer: str
    client_id: str
    client_secret: str = ""
    authorize_url: str = ""
    token_url: str = ""
    metadata_url: str = ""


class SsoCallback(BaseModel):
    state: str
    code: str = ""
    email: str = ""
    subject: str = ""


class InvoiceCreate(BaseModel):
    email: str
    amount_usd: float = 999.0
    plan: str = "institutional"
    method: str = "invoice"
    org_id: str | None = None


class MarkPaid(BaseModel):
    invoice_id: str
    source: str = "sandbox"
    external_ref: str = ""


class KycOpen(BaseModel):
    email: str
    legal_name: str
    country: str
    org_id: str | None = None


class KycDecide(BaseModel):
    case_id: str
    decision: str
    notes: str = ""


class CapacityPublish(BaseModel):
    environment: str = "staging"
    workers: int = 4
    postgres: bool = True
    redis: bool = True
    requests: int = 1000
    p50_ms: float = 120
    p95_ms: float = 450
    p99_ms: float = 900
    error_rate: float = 0.0
    operator: str
    notes: str = ""


class EvidenceDeposit(BaseModel):
    kind: str
    title: str
    issuer: str
    reference: str
    valid_until: str = ""
    notes: str = ""


class ContractCreate(BaseModel):
    kind: str
    counterparty: str
    org_id: str | None = None
    email: str = ""


class ContractSign(BaseModel):
    contract_id: str
    signer_name: str
    signer_email: str


class Tabletop(BaseModel):
    title: str
    outcome: str
    participants: list[str] = Field(default_factory=list)


class FailoverDrill(BaseModel):
    result: str = "success"
    duration_sec: float = 30.0
    notes: str = ""


class BackupDrill(BaseModel):
    rpo_minutes: int = 60
    rto_minutes: int = 180
    result: str = "success"


class SupportTicket(BaseModel):
    email: str
    subject: str
    body: str
    tier: str = "decision_pro"
    priority: str = "p2"


@router.get("/dd-closure")
async def dd_closure() -> dict[str, Any]:
    from dd_radical_closure import build_dd_radical_closure

    return await build_dd_radical_closure()


@router.get("/dd-closure/report1")
async def dd_report1() -> dict[str, Any]:
    from dd_radical_closure import build_report1_weaknesses_closure

    return build_report1_weaknesses_closure()


@router.get("/dd-closure/report2")
async def dd_report2() -> dict[str, Any]:
    from dd_radical_closure import build_report2_capabilities_closure

    return await build_report2_capabilities_closure()


@router.post("/orgs")
async def create_org(body: OrgCreate, user: dict = Depends(require_authenticated)) -> dict[str, Any]:
    from org_tenant import create_org

    # Owner is always the authenticated principal — never trust body spoof.
    owner = str(user.get("email") or "").strip().lower()
    if not owner:
        raise HTTPException(401, "Authenticated email required")
    return create_org(name=body.name, owner_email=owner, require_mfa=body.require_mfa, slug=body.slug)


@router.get("/orgs")
async def list_orgs(user: dict = Depends(require_authenticated)) -> dict[str, Any]:
    from org_tenant import list_orgs_for_email, org_isolation_status

    email = str(user.get("email") or "").strip().lower()
    return {"orgs": list_orgs_for_email(email), "isolation": org_isolation_status()}


@router.get("/orgs/{org_id}/members")
async def org_members(org_id: str) -> dict[str, Any]:
    from org_tenant import list_members

    return {"org_id": org_id, "members": list_members(org_id)}


@router.post("/orgs/{org_id}/members", responses=COMMON_ERROR_RESPONSES)
async def org_add_member(org_id: str, body: MemberAdd) -> dict[str, Any]:
    from org_tenant import add_member

    try:
        return add_member(org_id, body.email, body.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/orgs/{org_id}/roles", responses=COMMON_ERROR_RESPONSES)
async def org_role_change(org_id: str, body: RoleChange, user: dict = Depends(require_authenticated)) -> dict[str, Any]:
    from org_tenant import set_member_role

    actor = str(user.get("email") or "").strip().lower()
    try:
        return set_member_role(org_id, body.email, body.role, actor_email=actor)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/orgs/{org_id}/mfa-policy", responses=COMMON_ERROR_RESPONSES)
async def org_mfa_policy(org_id: str, body: MfaPolicy, user: dict = Depends(require_authenticated)) -> dict[str, Any]:
    from org_tenant import set_org_mfa_required

    actor = str(user.get("email") or "").strip().lower()
    try:
        return set_org_mfa_required(org_id, body.require_mfa, actor_email=actor)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/mfa-policy/check")
async def mfa_policy_check(
    email: Annotated[str, Query(...)],
    user: dict = Depends(require_authenticated),
) -> dict[str, Any]:
    from org_mfa_policy import mfa_policy_status, org_requires_mfa_for_email
    from security_auth import is_admin_user

    ask = email.strip().lower()
    me = str(user.get("email") or "").strip().lower()
    if ask != me and not is_admin_user(user):
        raise HTTPException(403, "Cannot inspect MFA policy for another user")
    return {**org_requires_mfa_for_email(email), **mfa_policy_status()}


@router.get("/rbac/matrix")
async def rbac_matrix() -> dict[str, Any]:
    from org_rbac import rbac_status

    return rbac_status()


@router.post("/sso/configure", responses=COMMON_ERROR_RESPONSES)
async def sso_configure(body: SsoConfigure, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from enterprise_sso import configure_provider

    try:
        return configure_provider(
            body.org_id,
            protocol=body.protocol,
            issuer=body.issuer,
            client_id=body.client_id,
            client_secret=body.client_secret,
            authorize_url=body.authorize_url,
            token_url=body.token_url,
            metadata_url=body.metadata_url,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@sso_router.get("/sso/authorize", responses=COMMON_ERROR_RESPONSES)
async def sso_authorize(
    org_id: str | None = None,
    redirect_uri: str | None = None,
    email_hint: str = "",
):
    from enterprise_sso import _default_callback_uri, build_sso_authorize_url_async

    try:
        cb = (redirect_uri or _default_callback_uri()).strip()
        result = await build_sso_authorize_url_async(
            org_id or "",
            redirect_uri=cb,
            email_hint=email_hint,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    if not result.get("ready"):
        raise HTTPException(400, detail=result)
    return RedirectResponse(url=str(result["authorize_url"]), status_code=302)


@sso_router.get("/sso/callback", responses=COMMON_ERROR_RESPONSES)
async def sso_callback_get(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    from enterprise_sso import complete_sso_login_async

    try:
        result = await complete_sso_login_async(state=state, code=code)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, detail=f"SSO provider failure: {exc}") from exc
    return _sso_session_redirect(result)


@sso_router.post("/sso/callback", responses=COMMON_ERROR_RESPONSES)
async def sso_callback_post(body: SsoCallback):
    from enterprise_sso import complete_sso_login_async

    try:
        result = await complete_sso_login_async(
            state=body.state,
            code=body.code,
            email=body.email,
            subject=body.subject,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, detail=f"SSO provider failure: {exc}") from exc
    return _sso_session_redirect(result)


@sso_router.get("/sso/status")
async def sso_status_api(org_id: str | None = None) -> dict[str, Any]:
    from enterprise_sso import sso_status

    return sso_status(org_id)


@router.post("/commerce/invoice", responses=COMMON_ERROR_RESPONSES)
async def commerce_invoice(body: InvoiceCreate, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_commerce import create_invoice

    try:
        return create_invoice(
            email=body.email,
            amount_usd=body.amount_usd,
            plan=body.plan,
            method=body.method,
            org_id=body.org_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/commerce/mark-paid", responses=COMMON_ERROR_RESPONSES)
async def commerce_mark_paid(body: MarkPaid, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_commerce import get_invoice, mark_invoice_paid
    from billing.institutional_activation import activate_institutional_from_invoice

    try:
        paid = mark_invoice_paid(body.invoice_id, source=body.source, external_ref=body.external_ref)
        inv = get_invoice(body.invoice_id)
        activation = await activate_institutional_from_invoice(
            email=str(paid["email"]),
            invoice_id=body.invoice_id,
            amount_usd=float(inv.get("amount_usd") or paid.get("amount_usd") or 999),
            plan=str(inv.get("plan") or "institutional"),
            org_id=inv.get("org_id"),
            source=body.source,
            external_ref=body.external_ref,
        )
        return {"paid": paid, "activation": activation}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/commerce/kyc")
async def commerce_kyc(body: KycOpen, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_commerce import open_kyc_case

    return open_kyc_case(
        email=body.email,
        legal_name=body.legal_name,
        country=body.country,
        org_id=body.org_id,
    )


@router.post("/commerce/kyc/didit/session", responses=COMMON_ERROR_RESPONSES)
async def commerce_kyc_didit_session(body: KycOpen, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from didit_kyc import create_verification_session
    from institutional_commerce import find_kyc_case, open_kyc_case

    case = open_kyc_case(
        email=body.email,
        legal_name=body.legal_name,
        country=body.country,
        org_id=body.org_id,
        provider="didit",
        status="pending_review",
    )
    try:
        session = await create_verification_session(
            email=body.email,
            legal_name=body.legal_name,
            country=body.country,
            case_id=case["case_id"],
            org_id=body.org_id,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, detail=f"didit_session_failed: {exc}") from exc
    stored = find_kyc_case(case["case_id"]) or case
    return {"case": stored, "didit": session}


@router.post("/commerce/kyc/decide", responses=COMMON_ERROR_RESPONSES)
async def commerce_kyc_decide(body: KycDecide, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_commerce import decide_kyc

    try:
        return decide_kyc(body.case_id, decision=body.decision, notes=body.notes)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/commerce/status")
async def commerce_status_api() -> dict[str, Any]:
    from institutional_commerce import commerce_status

    return commerce_status()


@router.post("/capacity")
async def publish_capacity(body: CapacityPublish, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_assurance import publish_signed_capacity

    return publish_signed_capacity(**body.model_dump())


@router.get("/capacity")
async def get_capacity() -> dict[str, Any]:
    from institutional_assurance import get_signed_capacity, sla_document, verify_signed_capacity

    row = get_signed_capacity()
    return {
        "signed_capacity": row,
        "verified": verify_signed_capacity(row),
        "sla": sla_document(),
    }


@router.get("/compliance")
async def compliance_api() -> dict[str, Any]:
    from institutional_assurance import compliance_status

    return compliance_status()


@router.post("/compliance/evidence", responses=COMMON_ERROR_RESPONSES)
async def compliance_deposit(body: EvidenceDeposit, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_assurance import deposit_compliance_evidence

    try:
        return deposit_compliance_evidence(**body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/contracts", responses=COMMON_ERROR_RESPONSES)
async def contracts_create(body: ContractCreate, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_assurance import create_contract

    try:
        return create_contract(**body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/contracts/sign", responses=COMMON_ERROR_RESPONSES)
async def contracts_sign(body: ContractSign, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_assurance import sign_contract

    try:
        return sign_contract(
            body.contract_id,
            signer_name=body.signer_name,
            signer_email=body.signer_email,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/contracts")
async def contracts_status_api() -> dict[str, Any]:
    from institutional_assurance import contracts_status

    return contracts_status()


@router.get("/ir")
async def ir_api() -> dict[str, Any]:
    from institutional_assurance import ir_program

    return ir_program()


@router.post("/ir/tabletop")
async def ir_tabletop(
    body: Tabletop,
    user: dict = Depends(require_institutional_principal),
) -> dict[str, Any]:
    from institutional_assurance import record_tabletop

    participants = body.participants or [str(user.get("email") or "operator")]
    return record_tabletop(title=body.title, outcome=body.outcome, participants=participants)


@router.get("/edge/waf")
async def waf_api() -> dict[str, Any]:
    from institutional_assurance import waf_cdn_status

    return waf_cdn_status()


@router.get("/ha")
async def ha_api() -> dict[str, Any]:
    from institutional_assurance import ha_activation_status

    return ha_activation_status()


@router.post("/ha/failover-drill")
async def ha_failover(body: FailoverDrill, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    from institutional_assurance import record_failover_drill

    return record_failover_drill(**body.model_dump())


@router.get("/status-page")
async def status_page_api() -> dict[str, Any]:
    from institutional_assurance import ha_activation_status, observability_status, sla_document

    return {
        "status": "operational",
        "observability": observability_status(),
        "ha": ha_activation_status(),
        "sla": sla_document()["targets"],
        "public_page": "/status",
    }


@router.get("/secrets/status")
async def secrets_api() -> dict[str, Any]:
    from institutional_assurance import secrets_manager_status

    return secrets_manager_status()


@router.get("/staging")
async def staging_api() -> dict[str, Any]:
    from institutional_assurance import staging_mirror_status

    return staging_mirror_status()


@router.get("/backup")
async def backup_api() -> dict[str, Any]:
    from institutional_assurance import backup_status

    return backup_status()


@router.post("/backup/drill")
async def backup_drill(
    body: BackupDrill,
    _user: dict = Depends(require_institutional_principal),
) -> dict[str, Any]:
    from institutional_assurance import record_backup_drill

    return record_backup_drill(**body.model_dump())


@router.post("/support/tickets")
async def support_ticket(body: SupportTicket) -> dict[str, Any]:
    from institutional_assurance import open_support_ticket

    return open_support_ticket(**body.model_dump())


@router.get("/support")
async def support_api() -> dict[str, Any]:
    from institutional_assurance import support_status

    return support_status()


@router.get("/coverage-catalog")
async def coverage_catalog_api() -> dict[str, Any]:
    from institutional_assurance import coverage_catalog

    return coverage_catalog()


@router.get("/data-qa")
async def data_qa_api() -> dict[str, Any]:
    from institutional_assurance import data_qa_slo

    return data_qa_slo()


@router.get("/model-card")
async def model_card_api() -> dict[str, Any]:
    from buyer_model_card import build_buyer_model_card

    return await build_buyer_model_card()


@router.get("/dex/status")
async def dex_status() -> dict[str, Any]:
    from jupiter_dex_adapter import adapter_status

    return adapter_status()


@router.get("/assurance")
async def assurance_api() -> dict[str, Any]:
    from institutional_assurance import assurance_bundle_status

    return assurance_bundle_status()
