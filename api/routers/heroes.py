"""Hero deepenings + Section Z APIs (binding Heroes Strategy)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Query

router = APIRouter(tags=["heroes"])


@router.get("/api/heroes/strategy")
async def heroes_strategy():
    from audience_routing import all_audiences

    return {
        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
        "heroes_binding": "docs/HEROES_STRATEGY_BINDING.md",
        "heroes": [
            "opportunity_score_explainability",
            "whale_intelligence_radar",
            "public_accuracy_ledger",
            "portfolio_ai",
            "single_sentence_oracle",
            "decision_certificate",
        ],
        "section_z": [
            "locked_predictions",
            "discipline_mirror",
            "signal_vs_noise_whale",
            "emerging_fund_terminal",
            "compliance_footer",
        ],
        "audiences": all_audiences(),
        "ui_language": "en",
    }


@router.get("/api/audience/entry")
async def audience_entry_api(audience: str = Query("retail")):
    from audience_routing import audience_entry

    return audience_entry(audience)


@router.post("/api/oracle/decision-certificate")
async def decision_certificate_api(payload: dict = Body(...)):
    from decision_certificate import build_decision_certificate

    return build_decision_certificate(payload)


@router.get("/api/locked-predictions")
async def list_locked(limit: int = Query(20, ge=1, le=100)):
    from locked_predictions import glass_box_status, list_locked_predictions

    return {
        "predictions": list_locked_predictions(limit=limit),
        "status": glass_box_status(),
    }


@router.post("/api/locked-predictions")
async def create_locked(body: dict = Body(...)):
    from locked_predictions import lock_prediction

    return lock_prediction(
        event_name=str(body.get("event_name") or "market_event"),
        asset=str(body.get("asset") or "BTC"),
        direction=str(body.get("direction") or "neutral"),
        rationale=str(body.get("rationale") or ""),
        unlock_at=str(body.get("unlock_at") or ""),
        opportunity_score=body.get("opportunity_score"),
        prediction_id=body.get("prediction_id"),
    )


@router.post("/api/discipline-mirror/answer")
async def discipline_answer(body: dict = Body(...)):
    from discipline_mirror import record_follow_up

    return record_follow_up(
        user_key=str(body.get("user_key") or body.get("email") or "anonymous"),
        asset=str(body.get("asset") or "BTC"),
        system_action=str(body.get("system_action") or body.get("decision_action") or "WAIT"),
        followed=bool(body.get("followed")),
        prediction_id=body.get("prediction_id"),
        opportunity_score=body.get("opportunity_score"),
        note=body.get("note"),
    )


@router.get("/api/discipline-mirror/me")
async def discipline_me(user_key: str = Query(...), limit: int = Query(100, ge=1, le=500)):
    from discipline_mirror import personal_mirror

    return personal_mirror(user_key, limit=limit)


@router.get("/api/whale/signal-vs-noise")
async def whale_signal_vs_noise(limit: int = Query(5, ge=1, le=20)):
    from whale_signal_classifier import enrich_whale_narratives

    return await enrich_whale_narratives(limit=limit)


@router.get("/api/fund/emerging-terminal")
async def emerging_fund_terminal(fund_name: str = Query("Emerging Fund")):
    from emerging_fund_terminal import build_fund_terminal_pack

    return await build_fund_terminal_pack(fund_name=fund_name)


@router.get("/api/compliance/footer")
async def compliance_footer(surface: str = Query("oracle")):
    from decision_certificate import compliance_footer_block

    return compliance_footer_block(
        surface=surface,
        trust_basis="public_accuracy_ledger + decision_certificate",
    )
