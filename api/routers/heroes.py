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

    payload = dict(payload or {})
    payload.setdefault("tier", "free")
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

    label_by_id: dict[str, str] = {}
    try:
        from database import fetch_labeled_oracle_predictions

        labeled = await fetch_labeled_oracle_predictions(limit=500, include_synthetic=False)
        for lab in labeled or []:
            pid = lab.get("id") or lab.get("prediction_id")
            if pid is not None:
                label_by_id[str(pid)] = str(lab.get("label") or "")
    except Exception:
        label_by_id = {}
    return personal_mirror(user_key, limit=limit, label_by_id=label_by_id)


@router.get("/api/accuracy/monthly-losing-report")
async def monthly_losing_report(limit: int = Query(25, ge=1, le=100)):
    from monthly_losing_report import build_monthly_losing_report

    return await build_monthly_losing_report(limit=limit)


@router.get("/api/audit-challenge")
async def audit_challenge():
    from oracle_audit_chain import verify_chain

    verify = verify_chain()
    return {
        "title": "Audit Challenge — Prove us wrong",
        "invitation": (
            "We invite any external party to find a real break in the Public Accuracy "
            "Ledger hash chain. Symbolic recognition for a verified contradiction."
        ),
        "how": [
            "Open /oracle-accuracy and /api/oracle/audit-chain/verify",
            "Reproduce tip hash linkage across records",
            "Report a broken_at_seq with evidence to sales@blackdark.io",
        ],
        "live_verify": verify,
        "verify_endpoint": "/api/oracle/audit-chain/verify",
        "hero_deepening": "public_accuracy_ledger",
    }


@router.post("/api/whale/stealth-advisor")
async def stealth_advisor(body: dict = Body(...)):
    from stealth_execution_advisor import advise_stealth_execution

    return advise_stealth_execution(
        asset=str(body.get("asset") or "BTC"),
        notional_usd=float(body.get("notional_usd") or 10000),
        side=str(body.get("side") or "buy"),
        half_life_seconds=body.get("half_life_seconds"),
        average_daily_volume_usd=body.get("average_daily_volume_usd"),
    )


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


@router.get("/api/mev/sandwich-report")
async def mev_sandwich_report(
    asset: str = Query("ETH"),
    notional_usd: float = Query(10_000.0, ge=0, le=50_000_000),
):
    from mev_sandwich_report import build_mev_sandwich_report

    return build_mev_sandwich_report(asset=asset, notional_usd=notional_usd)


@router.get("/api/glass-box/challenge")
async def glass_box_challenge():
    from glass_box_challenge import build_glass_box_challenge_pack

    return build_glass_box_challenge_pack()


@router.get("/api/glass-box/operator")
async def glass_box_operator():
    from glass_box_challenge import build_glass_box_operator_pack

    return build_glass_box_operator_pack()


@router.get("/api/ledger/share-kit")
async def ledger_share_kit():
    """Hero #3 — shareable Public Accuracy Ledger kit (no login)."""
    from heroes_quality import build_ledger_share_kit

    accuracy_pct = None
    total = None
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        summary = await build_public_accuracy_payload(recent_limit=5)
        if isinstance(summary, dict):
            oracle = summary.get("oracle") or {}
            accuracy_pct = (
                oracle.get("average_accuracy_percent")
                or oracle.get("recent_hit_rate_percent")
                or summary.get("average_accuracy_percent")
            )
            total = (
                oracle.get("resolved_predictions")
                or oracle.get("total_predictions")
                or summary.get("total_predictions")
            )
            try:
                accuracy_pct = float(accuracy_pct) if accuracy_pct is not None else None
            except (TypeError, ValueError):
                accuracy_pct = None
            try:
                total = int(total) if total is not None else None
            except (TypeError, ValueError):
                total = None
    except Exception:
        pass
    return build_ledger_share_kit(accuracy_pct=accuracy_pct, total_predictions=total)


@router.get("/api/heroes/quality")
async def heroes_quality():
    """Six-hero quality gates — polish depth, not a seventh button."""
    from heroes_quality import heroes_quality_manifest

    return heroes_quality_manifest()


@router.get("/api/strategy/correction")
async def strategy_correction():
    """Expert correction of inflated strategy pastes — four layers, six heroes."""
    from trust_os import strategy_correction_manifest

    return strategy_correction_manifest()


@router.get("/api/intent/router")
async def intent_router_api():
    """Results-over-features intent map (display layer only)."""
    from intent_router import intent_router_manifest

    return intent_router_manifest()


@router.get("/api/intent/resolve")
async def intent_resolve(intent_id: str = Query(...)):
    from intent_router import resolve_intent

    return resolve_intent(intent_id)


@router.get("/api/execution/closure")
async def execution_closure(base_url: str | None = Query(None)):
    """Expert execution closure — canonical binding + remaining human-only gates."""
    from expert_execution import execution_closure_manifest

    return execution_closure_manifest(base_url=base_url)


@router.get("/api/acceptance/60s")
async def acceptance_60s(base_url: str = Query("http://127.0.0.1:8080")):
    """Machine probe for 60-second grasp (founder confirm still required)."""
    from expert_execution import run_acceptance_60s

    return run_acceptance_60s(base_url)


@router.get("/api/glass-box/announce-drafts")
async def glass_box_announce_drafts_api():
    from expert_execution import glass_box_announce_drafts

    return glass_box_announce_drafts()


@router.get("/api/alerts/generosity")
async def alerts_generosity_posture():
    """Competitive posture vs TradingView-style rate caps — honest tier policy."""
    return {
        "title": "Alert generosity — no 15-alerts-per-3-minutes hard cap",
        "competitor_friction": (
            "TradingView and similar charting tools throttle alerts "
            "(commonly ~15 alerts / 3 minutes), which breaks discretionary workflows."
        ),
        "blackdark": {
            "in_app_inbox": (
                "In-app Oracle + arb inbox has no TV-style 15/3min hard cap "
                "(practical retention limit applies for storage)"
            ),
            "telegram_free": "Free tier: 3 Oracle alerts/day on Telegram",
            "telegram_pro": (
                "Pro/Whale: no per-3-minute hard cap on Oracle/chat Telegram alerts when bot is configured"
            ),
            "proof_gate": "Only Net-Edge Truth + Half-Life survivors are alertable",
            "honest_policy": (
                "'Unlimited' means no TradingView-style 15/3min throttle — "
                "not an infinite infra SLA. Abuse/rate guards and proof gates still apply."
            ),
        },
        "cta": "Open the in-app inbox on /dashboard — works without Telegram",
        "endpoints": {
            "inbox": "/api/alerts/inbox",
            "telegram_status": "/api/alerts/telegram/status",
        },
        "hero_deepening": "opportunity_score_explainability",
    }
