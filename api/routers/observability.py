"""Observability + due diligence API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from security_auth import is_production_env, require_admin, require_whale, verify_admin_key

router = APIRouter(tags=["observability"])


def require_metrics_access(
    authorization: str | None = Header(default=None),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    """Fail-closed Prometheus scrape in production unless a scrape token or admin key is presented."""
    import hmac
    import os

    if os.getenv("METRICS_ALLOW_UNAUTHENTICATED", "").lower() in {"1", "true", "yes"}:
        return
    token = os.getenv("METRICS_BEARER_TOKEN", "").strip()
    presented = ""
    if authorization:
        presented = authorization.removeprefix("Bearer ").strip()
    if token and presented and hmac.compare_digest(presented, token):
        return
    if verify_admin_key(x_admin_key):
        return
    if not is_production_env():
        return
    raise HTTPException(status_code=401, detail="Metrics scrape authentication required")


@router.get("/metrics")
async def prometheus_metrics(_auth: None = Depends(require_metrics_access)):
    from observability import prometheus_metrics_text

    return Response(content=prometheus_metrics_text(), media_type="text/plain; version=0.0.4")


@router.get("/api/observability/status")
async def observability_status_api():
    from observability import observability_status

    return observability_status()


@router.get("/api/due-diligence/bundle")
async def due_diligence_bundle(_admin: dict = Depends(require_admin)):
    from due_diligence_bundle import build_full_due_diligence_bundle

    return await build_full_due_diligence_bundle()


@router.get("/api/due-diligence/technical")
async def technical_due_diligence_api(
    probe_production: bool = True,
    _admin: dict = Depends(require_admin),
):
    from technical_due_diligence import build_technical_due_diligence_report

    return await build_technical_due_diligence_report(probe_production=probe_production)


@router.get("/api/due-diligence/architecture")
async def architecture_due_diligence_api(_admin: dict = Depends(require_admin)):
    from architecture_due_diligence import evaluate_architecture_dd

    return evaluate_architecture_dd()


@router.get("/api/due-diligence/evidence-pack")
async def acquirer_evidence_pack_api(_whale: dict = Depends(require_whale)):
    """One-click Acquirer / Fund committee evidence pack (Differentiator D6). Whale/Admin only."""
    from acquirer_evidence_pack import build_acquirer_evidence_pack

    return await build_acquirer_evidence_pack()


@router.get("/api/due-diligence/evidence-pack/public-summary")
async def acquirer_evidence_public_summary():
    """Redacted public teaser — no proprietary internals."""
    return {
        "product_thesis": (
            "Decision Intelligence + Proven Predictive Accuracy + "
            "Proprietary Labeled Market Corpus"
        ),
        "differentiators": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
        "public_endpoints": {
            "accuracy": "/api/oracle/accuracy/public",
            "accuracy_page": "/oracle-accuracy",
            "persona_demo": "/api/oracle/persona-clarity/demo",
            "half_life": "/api/oracle/half-life",
            "net_edge": "/api/oracle/net-edge-truth",
            "kill_rate": "/api/public/kill-rate",
            "committee_teaser": "/b2b/committee-one-pager",
        },
        "full_pack": "/api/due-diligence/evidence-pack",
        "access": "whale_or_admin",
        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
    }


@router.get("/api/due-diligence/committee-one-pager")
async def committee_one_pager_api(_whale: dict = Depends(require_whale)):
    from committee_one_pager import build_committee_one_pager

    return await build_committee_one_pager()


@router.get("/api/due-diligence/committee-one-pager.pdf")
async def committee_one_pager_pdf(_whale: dict = Depends(require_whale)):
    from fastapi.responses import Response

    from committee_one_pager import build_committee_one_pager, render_committee_pdf

    pack = await build_committee_one_pager()
    return Response(
        content=render_committee_pdf(pack),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="blackdark-committee-one-pager.pdf"'},
    )


@router.get("/api/due-diligence/corpus-passport")
async def corpus_passport_api(_whale: dict = Depends(require_whale)):
    from corpus_passport import build_corpus_passport

    return await build_corpus_passport()


@router.get("/api/due-diligence/corpus-passport/public")
async def corpus_passport_public_api():
    from corpus_passport import build_corpus_passport_public

    return build_corpus_passport_public()


@router.get("/api/due-diligence/corpus-passport.pdf")
async def corpus_passport_pdf(_whale: dict = Depends(require_whale)):
    from fastapi.responses import Response

    from corpus_passport import build_corpus_passport, render_corpus_passport_pdf

    pack = await build_corpus_passport()
    return Response(
        content=render_corpus_passport_pdf(pack),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="blackdark-corpus-passport.pdf"'},
    )


@router.get("/api/diagnostics/price/{symbol}")
async def price_source_diagnostics(symbol: str):
    from market_context import probe_price_sources

    return await probe_price_sources(symbol)
