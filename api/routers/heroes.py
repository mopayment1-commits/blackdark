"""Hero deepenings + Section Z APIs (binding Heroes Strategy)."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Body, HTTPException, Query

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["heroes"], responses=COMMON_ERROR_RESPONSES)
logger = logging.getLogger("BLACKDARK.HeroesAPI")


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


@router.get("/api/trial/persona-readiness")
async def trial_persona_readiness_api():
    from persona_capability_matrix import persona_capability_matrix

    return persona_capability_matrix()


@router.get("/api/product/capability-inventory")
async def product_capability_inventory_api():
    """Binding full-product inventory. Never claims COMPLETE."""
    from product_capability_inventory import build_full_capability_inventory

    return build_full_capability_inventory()


@router.get("/api/product/l2-remainder")
async def product_l2_remainder_api():
    from l2_remainder import catalog_l2_remainder

    return catalog_l2_remainder()


@router.get("/api/product/unpaid-closure")
async def product_unpaid_closure_api():
    from unpaid_institutional_closure import prove_unpaid_institutional_closure

    return prove_unpaid_institutional_closure()


@router.get("/api/product/public-readiness")
async def product_public_readiness_api():
    """Visitor/paper HTTP catalog. Score comes from prove script / tests, not self-grade."""
    from pathlib import Path

    from public_readiness import catalog_without_probe

    out = catalog_without_probe()
    evidence = Path("docs/dd/BLACKDARK_PUBLIC_READINESS_EVIDENCE.json")
    if evidence.is_file():
        try:
            import json

            last = json.loads(evidence.read_text(encoding="utf-8"))
            score = last.get("score") or {}
            out["last_probe"] = {
                "proved_at": last.get("proved_at"),
                "public_direct_use_percent": score.get("public_direct_use_percent"),
                "meets_public_floor": score.get("meets_public_floor"),
                "counted_pass": score.get("counted_pass"),
                "counted_total": score.get("counted_total"),
                "failures": score.get("failures") or [],
            }
        except Exception:
            out["last_probe"] = None
    else:
        out["last_probe"] = None
    out["product_complete"] = False
    out["institutional_verdict"] = "NOT_COMPLETE"
    return out


@router.get("/api/product/production-launch-cert")
async def production_launch_cert_api():
    """Binding live-launch verdict. Missing evidence is NO-GO, not implied GO."""
    import json
    from pathlib import Path

    evidence = Path("docs/dd/BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json")
    if not evidence.is_file():
        return {
            "ok": False,
            "product_complete": False,
            "public_demo_ready": False,
            "live_production_ready": False,
            "live_money_ready": False,
            "PUBLIC-DEMO-READY": False,
            "LIVE-PRODUCTION-READY": False,
            "LIVE-MONEY-READY": False,
            "decision": "NO-GO",
            "reason": "evidence_missing",
            "hint": "python scripts/prove_production_launch_cert.py",
        }
    body = json.loads(evidence.read_text(encoding="utf-8"))
    v = body.get("final_production_verdict") or {}
    tracks = body.get("tracks") or v.get("tracks") or {}
    return {
        "ok": True,
        "sha": body.get("sha"),
        "proved_at": body.get("proved_at"),
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "public_demo_ready": bool(tracks.get("PUBLIC-DEMO-READY")),
        "live_production_ready": bool(tracks.get("LIVE-PRODUCTION-READY")),
        "live_money_ready": bool(tracks.get("LIVE-MONEY-READY")),
        "PUBLIC-DEMO-READY": bool(tracks.get("PUBLIC-DEMO-READY")),
        "LIVE-PRODUCTION-READY": bool(tracks.get("LIVE-PRODUCTION-READY")),
        "LIVE-MONEY-READY": bool(tracks.get("LIVE-MONEY-READY")),
        "tracks": {
            "PUBLIC-DEMO-READY": bool(tracks.get("PUBLIC-DEMO-READY")),
            "LIVE-PRODUCTION-READY": bool(tracks.get("LIVE-PRODUCTION-READY")),
            "LIVE-MONEY-READY": bool(tracks.get("LIVE-MONEY-READY")),
        },
        "decision": v.get("decision"),
        "unconditional_go_criteria_met": v.get("unconditional_go_criteria_met"),
        "critical_open": v.get("critical_open"),
        "high_open": v.get("high_open"),
        "medium_open": v.get("medium_open"),
        "untested_launch_critical": v.get("untested_launch_critical_requirements"),
        "unverified_launch_critical_assumptions": v.get("unverified_launch_critical_assumptions") or [],
        "unknown_launch_blockers": v.get("unknown_launch_blockers") or [],
        "external_blockers": v.get("external_blockers"),
        "integrity": (body.get("financial_decision_integrity") or {}).get("verdict"),
        "report": "docs/dd/BLACKDARK_FINAL_PRODUCTION_VERDICT.md",
    }


@router.get("/api/lenses")
async def lenses_api():
    """Trust OS UX lenses — Prove / Operate / Desk / Room."""
    from trust_os_lenses import lenses_manifest

    return lenses_manifest()


@router.get("/api/lenses/{lens_id}")
async def lens_detail_api(lens_id: str, audience: str | None = Query(None)):
    from trust_os_lenses import lens_payload

    return lens_payload(lens_id, audience=audience)


@router.get("/api/lenses/{lens_id}/entries")
async def lens_entries_api(lens_id: str):
    from trust_os_lenses import primary_entries_for_lens

    return {"lens": lens_id, "entries": primary_entries_for_lens(lens_id)}


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


@router.get("/api/strategy/priority-chain")
async def strategy_priority_chain():
    """CSO priority chain binding — Product Excellence before feature inflation."""
    from cso_priority_chain import build_cso_priority_chain

    return build_cso_priority_chain()


@router.get("/api/strategy/priority-chain/evaluate")
async def strategy_priority_chain_evaluate(
    title: str = Query("untitled"),
    lever: list[str] | None = Query(None),
    raises_habit: bool = Query(False),
    raises_distribution: bool = Query(False),
    raises_revenue: bool = Query(False),
    raises_live_flywheel: bool = Query(False),
    raises_unique_intelligence: bool = Query(False),
    notes: str = Query(""),
):
    """Gate a proposed feature against the CSO binding rule."""
    from cso_priority_chain import evaluate_feature_proposal

    return evaluate_feature_proposal(
        title=title,
        levers=list(lever or []),
        raises_habit=raises_habit,
        raises_distribution=raises_distribution,
        raises_revenue=raises_revenue,
        raises_live_flywheel=raises_live_flywheel,
        raises_unique_intelligence=raises_unique_intelligence,
        notes=notes,
    )


@router.get("/api/public/cso-priority-closure")
async def cso_priority_closure_api():
    """Public closure — CSO chain shipped with zero deferred code."""
    from cso_priority_chain import build_cso_priority_closure

    return build_cso_priority_closure()


@router.get("/api/strategy/zero-tolerance")
async def strategy_zero_tolerance():
    """Zero-Tolerance defect binding — trust-destroying failure modes."""
    from zero_tolerance import build_zero_tolerance_manifest

    return build_zero_tolerance_manifest()


@router.get("/api/public/zero-tolerance-closure")
async def zero_tolerance_closure_api():
    """Public closure — Zero-Tolerance helpers wired with zero deferred code."""
    from zero_tolerance import build_zero_tolerance_closure

    return build_zero_tolerance_closure()


@router.get("/api/intent/router")
async def intent_router_api():
    """Results-over-features intent map (display layer only)."""
    from intent_router import intent_router_manifest

    return intent_router_manifest()


@router.get("/api/intent/resolve")
async def intent_resolve(intent_id: str = Query(...)):
    from intent_router import resolve_intent

    return resolve_intent(intent_id)


@router.get("/api/execution/closure", responses=COMMON_ERROR_RESPONSES)
async def execution_closure(base_url: str | None = Query(None)):
    """Expert execution closure — canonical binding + remaining human-only gates."""
    from expert_execution import execution_closure_manifest

    try:
        return await asyncio.to_thread(execution_closure_manifest, base_url=base_url)
    except Exception:
        logger.exception("execution_closure failed")
        raise HTTPException(status_code=500, detail="execution_closure_unavailable") from None


@router.get("/api/acceptance/60s", responses=COMMON_ERROR_RESPONSES)
async def acceptance_60s(base_url: str = Query("http://127.0.0.1:8080")):
    """Machine probe for 60-second grasp (founder confirm still required).

    Runs off the event loop so single-worker Soft Launch does not deadlock on
    self-HTTP probes. Exception details are never returned to clients.
    """
    from expert_execution import run_acceptance_60s

    try:
        return await asyncio.to_thread(run_acceptance_60s, base_url)
    except Exception:
        logger.exception("acceptance_60s failed")
        raise HTTPException(status_code=500, detail="acceptance_probe_unavailable") from None


@router.get("/api/glass-box/announce-drafts")
async def glass_box_announce_drafts_api():
    from expert_execution import glass_box_announce_drafts

    return glass_box_announce_drafts()


@router.get("/api/public/kill-rate")
async def public_kill_rate_board():
    from kill_rate_board import build_kill_rate_board

    return build_kill_rate_board()


@router.get("/api/public/miss-feed")
async def public_miss_feed_api(limit: int = Query(40, ge=1, le=100)):
    from public_miss_feed import build_public_miss_feed

    return await build_public_miss_feed(limit=limit)


@router.get("/api/public/coverage-honesty")
async def coverage_honesty_api():
    from coverage_honesty import build_coverage_honesty_board

    return await build_coverage_honesty_board()


@router.get("/api/oracle/provenance-score")
async def provenance_score_api(symbol: str = Query("BTC")):
    from data_provenance_score import compute_data_provenance_score

    return compute_data_provenance_score(symbol=symbol)


@router.get("/api/emotion-tax/receipt")
async def emotion_tax_receipt_api(
    user_key: str = Query("anon"),
    notional_usd: float = Query(1000.0, ge=10, le=10_000_000),
):
    from emotion_tax_receipt import build_emotion_tax_receipt

    return build_emotion_tax_receipt(user_key=user_key, notional_usd=notional_usd)


@router.get("/api/public/brand-coverage-closure")
async def brand_coverage_closure_api():
    from brand_proof_engine import build_brand_coverage_radical_closure

    return await build_brand_coverage_radical_closure()


@router.get("/api/public/f1-f10-closure")
async def f1_f10_closure_api():
    from f1_f10_unique_closure import build_f1_f10_unique_closure

    return await build_f1_f10_unique_closure()


@router.get("/api/allocator-receipt")
async def allocator_receipt_api(
    limit: int = Query(12, ge=1, le=50),
    fund_name: str = Query("Emerging Desk"),
):
    from allocator_decision_receipt import build_allocator_decision_receipt

    return await build_allocator_decision_receipt(limit=limit, fund_name=fund_name)


@router.get("/api/allocator-receipt/pdf")
async def allocator_receipt_pdf_api(
    limit: int = Query(12, ge=1, le=50),
    fund_name: str = Query("Emerging Desk"),
):
    from fastapi.responses import Response

    from allocator_decision_receipt import (
        build_allocator_decision_receipt,
        render_allocator_receipt_pdf,
    )

    receipt = await build_allocator_decision_receipt(limit=limit, fund_name=fund_name)
    pdf = render_allocator_receipt_pdf(receipt)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="allocator-receipt.pdf"'},
    )


@router.get("/api/transfer-intent")
async def transfer_intent_api(asset: str = Query("BTC")):
    from transfer_intent_probability import build_transfer_intent_board

    return await build_transfer_intent_board(asset=asset)


@router.post("/api/transfer-intent")
async def transfer_intent_compute(payload: dict = Body(default={})):
    from transfer_intent_probability import compute_transfer_intent

    body = payload or {}
    return compute_transfer_intent(
        asset=str(body.get("asset") or "BTC"),
        amount_usd=float(body.get("amount_usd") or 5_000_000),
        from_label=str(body.get("from_label") or "unknown"),
        to_label=str(body.get("to_label") or "unknown"),
        funding_z=body.get("funding_z"),
        oi_change_percent=body.get("oi_change_percent"),
    )


@router.get("/api/silence-index")
async def silence_index_api():
    from industry_silence_index import build_industry_silence_index

    return build_industry_silence_index()


@router.post("/api/silence-index/event")
async def silence_index_event(payload: dict = Body(default={})):
    from datetime import UTC, datetime

    from industry_silence_index import register_event

    body = payload or {}
    return register_event(
        event_name=str(body.get("event_name") or "Untitled event"),
        event_at=str(body.get("event_at") or datetime.now(UTC).isoformat()),
        category=str(body.get("category") or "macro"),
        sealed_by_blackdark=bool(body.get("sealed_by_blackdark", True)),
        peer_seals=body.get("peer_seals"),
    )


@router.get("/api/alert-passport")
async def alert_passport_api(user_key: str = Query("anon")):
    from proof_gated_alert_passport import build_alert_passport

    return build_alert_passport(user_key=user_key)


@router.post("/api/alert-passport/evaluate")
async def alert_passport_evaluate(payload: dict = Body(default={})):
    from proof_gated_alert_passport import evaluate_alert_gate

    body = payload or {}
    return evaluate_alert_gate(
        user_key=str(body.get("user_key") or "anon"),
        asset=str(body.get("asset") or "BTC"),
        net_edge_pass=body.get("net_edge_pass"),
        veto_clear=body.get("veto_clear"),
        freshness_ok=body.get("freshness_ok"),
        truth_score=body.get("truth_score"),
        freshness_ms=body.get("freshness_ms"),
    )


@router.get("/api/visibility-cost")
async def visibility_cost_api(
    asset: str = Query("ETH"),
    notional_usd: float = Query(250_000.0, ge=100, le=50_000_000),
    venue: str = Query("public_memepool"),
):
    from whale_visibility_cost import build_visibility_cost_meter

    return build_visibility_cost_meter(asset=asset, notional_usd=notional_usd, venue=venue)


@router.get("/api/validity-decay")
async def validity_decay_api(
    limit: int = Query(40, ge=1, le=200),
    asset: str | None = Query(None),
):
    from decision_validity_decay import build_validity_decay_map

    return await build_validity_decay_map(limit=limit, asset=asset)


@router.get("/api/desk-duel")
async def desk_duel_board_api(limit: int = Query(20, ge=1, le=100)):
    from sealed_desk_duel import build_duel_board

    return build_duel_board(limit=limit)


@router.post("/api/desk-duel")
async def desk_duel_create(payload: dict = Body(default={})):
    from sealed_desk_duel import create_duel

    body = payload or {}
    return create_duel(
        asset=str(body.get("asset") or "BTC"),
        window_minutes=int(body.get("window_minutes") or 60),
        host_desk=str(body.get("host_desk") or "Desk A"),
        host_verdict=str(body.get("host_verdict") or "WAIT"),
        invitee_desk=str(body.get("invitee_desk") or "Desk B"),
    )


@router.post("/api/desk-duel/accept", responses=COMMON_ERROR_RESPONSES)
async def desk_duel_accept(payload: dict = Body(default={})):
    from sealed_desk_duel import accept_duel

    body = payload or {}
    try:
        return accept_duel(
            str(body.get("duel_id") or ""),
            desk=str(body.get("desk") or "Challenger"),
            verdict=str(body.get("verdict") or "WAIT"),
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_duel_accept") from None


@router.post("/api/desk-duel/reveal", responses=COMMON_ERROR_RESPONSES)
async def desk_duel_reveal(payload: dict = Body(default={})):
    from sealed_desk_duel import reveal_duel

    body = payload or {}
    try:
        return reveal_duel(str(body.get("duel_id") or ""), force=bool(body.get("force", True)))
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_duel_reveal") from None


@router.get("/api/trust-debt")
async def trust_debt_api(
    user_key: str = Query("anon"),
    window_days: int = Query(7, ge=1, le=90),
):
    from trust_debt_score import build_trust_debt_score

    return build_trust_debt_score(user_key=user_key, window_days=window_days)


@router.post("/api/trust-debt/event")
async def trust_debt_event(payload: dict = Body(default={})):
    from trust_debt_score import record_trust_event

    body = payload or {}
    return record_trust_event(
        user_key=str(body.get("user_key") or "anon"),
        kind=str(body.get("kind") or "ledger_decision"),
        weight=float(body.get("weight") or 1.0),
        note=str(body.get("note") or ""),
    )


@router.get("/api/contradiction-replay")
async def contradiction_replay_api(
    symbol: str = Query("BTC"),
    clip_id: str | None = Query(None),
):
    from contradiction_replay import build_contradiction_replay, get_replay, list_recent_replays

    if clip_id:
        found = get_replay(clip_id)
        if found:
            return found
    card = build_contradiction_replay(symbol=symbol)
    return {"card": card, "recent": list_recent_replays(12)}


@router.post("/api/contradiction-replay")
async def contradiction_replay_create(payload: dict = Body(default={})):
    from contradiction_replay import build_contradiction_replay

    body = payload or {}
    return build_contradiction_replay(
        symbol=str(body.get("symbol") or "BTC"),
        conflict=body.get("conflict"),
        score=body.get("score"),
        persist=True,
    )


@router.get("/api/oracle/half-life/heat")
async def half_life_heat_clock_api(board: bool = Query(False)):
    from half_life_heat_clock import build_heat_clock, build_heat_clock_board

    if board:
        return build_heat_clock_board()
    return build_heat_clock()


@router.get("/api/proof-arena/week")
async def proof_arena_week(week_id: str | None = Query(None)):
    from proof_arena import build_week_board

    return build_week_board(week_id)


@router.post("/api/proof-arena/pick")
async def proof_arena_pick(payload: dict = Body(...)):
    from proof_arena import submit_pick

    return submit_pick(
        user_key=str(payload.get("user_key") or "anon"),
        symbol=str(payload.get("symbol") or "BTC"),
        direction=str(payload.get("direction") or "wait"),
        note=str(payload.get("note") or ""),
    )


@router.get("/api/glass-box/announce-schedule")
async def glass_box_announce_schedule_get():
    from glass_box_announce_schedule import schedule_status

    return schedule_status()


@router.post("/api/glass-box/announce-schedule")
async def glass_box_announce_schedule_set(payload: dict = Body(...)):
    from glass_box_announce_schedule import set_schedule

    return set_schedule(
        announce_at=str(payload.get("announce_at") or ""),
        channel=str(payload.get("channel") or "x_linkedin_telegram"),
        note=str(payload.get("note") or ""),
    )


@router.get("/api/since-you-left")
async def since_you_left_api(
    user_key: str = Query("anon"),
    touch: bool = Query(True),
):
    from since_you_left import build_since_you_left

    return build_since_you_left(user_key=user_key, touch=touch)


@router.get("/api/anti-hype/mode")
async def anti_hype_mode_get(user_key: str = Query("anon")):
    from anti_hype_mode import build_anti_hype_mode

    return build_anti_hype_mode(user_key=user_key)


@router.post("/api/anti-hype/mode")
async def anti_hype_mode_set(payload: dict = Body(...)):
    from anti_hype_mode import set_mode

    return set_mode(
        bool(payload.get("enabled")),
        user_key=str(payload.get("user_key") or "anon"),
    )


@router.get("/api/wow/surfaces")
async def wow_surfaces_manifest():
    """Unique wow surfaces by tier — product-complete registry (100%)."""
    return {
        "product_complete": False,
        "proof_pass": [
            {"id": "oracle", "href": "/", "label": "Single-Sentence Oracle"},
            {"id": "certificate", "href": "/dashboard?lens=prove#decide", "label": "Decision Certificate"},
            {"id": "ledger", "href": "/oracle-accuracy", "label": "Public Accuracy Ledger"},
            {"id": "kill_rate", "href": "/kill-rate"},
            {"id": "contradiction_replay", "href": "/contradiction-replay"},
            {"id": "proof_arena", "href": "/proof-arena"},
            {"id": "since_you_left", "href": "/since-you-left"},
            {"id": "anti_hype", "href": "/anti-hype"},
        ],
        "decision_pro": [
            {"id": "unlimited_oracle", "href": "/dashboard?lens=operate#decide", "label": "Unlimited decisions"},
            {"id": "radar", "href": "/dashboard?lens=operate#radar", "label": "Market Radar"},
            {"id": "alerts", "href": "/dashboard#alerts", "label": "Alerts"},
            {"id": "net_edge", "href": "/api/oracle/net-edge-truth", "label": "Net-Edge Truth"},
            {"id": "since_you_left", "href": "/since-you-left"},
        ],
        "decision_desk": [
            {"id": "signal_vs_noise", "href": "/dashboard?lens=desk#whales", "label": "Signal vs Noise"},
            {"id": "stealth", "href": "/dashboard?lens=desk#stealth", "label": "Stealth Advisor"},
            {"id": "api", "href": "/b2b", "label": "B2B / API"},
            {"id": "evidence", "href": "/b2b#evidence", "label": "Evidence Pack"},
            {"id": "half_life_heat_clock", "href": "/dashboard?lens=desk#half-life-clock"},
            {"id": "committee_one_pager", "href": "/b2b/committee-one-pager"},
            {"id": "corpus_passport", "href": "/corpus-passport"},
        ],
        "institutional": [
            {"id": "data_room", "href": "/data-room", "label": "Data Room"},
            {"id": "sla_sso", "href": "/data-room", "label": "SLA / SSO path"},
            {"id": "committee_pdf", "href": "/api/due-diligence/committee-one-pager.pdf"},
            {"id": "corpus_passport", "href": "/corpus-passport"},
            {"id": "anti_hype_mode", "href": "/anti-hype"},
            {"id": "evidence_pack", "href": "/api/due-diligence/evidence-pack"},
        ],
        "wow_eight_shipped": [
            "kill_rate_board",
            "contradiction_replay_clip",
            "committee_one_pager",
            "half_life_heat_clock",
            "proof_arena_lite",
            "since_you_left_top3",
            "anti_hype_mode",
            "corpus_passport",
        ],
        "brand_coverage_radical_closure": {
            "miss_feed": "/miss-feed",
            "coverage_honesty": "/coverage-honesty",
            "emotion_tax": "/emotion-tax",
            "provenance_score": "/api/oracle/provenance-score",
            "status_api": "/api/public/brand-coverage-closure",
            "product_complete": False,
        },
        "cso_priority_chain": {
            "page": "/priority-chain",
            "api": "/api/strategy/priority-chain",
            "evaluate": "/api/strategy/priority-chain/evaluate",
            "closure": "/api/public/cso-priority-closure",
            "doc": "docs/CSO_PRIORITY_CHAIN_BINDING_AR.md",
            "binding": True,
            "all_done_for_agreed_scope": True,
        },
        "zero_tolerance": {
            "page": "/zero-tolerance",
            "api": "/api/strategy/zero-tolerance",
            "closure": "/api/public/zero-tolerance-closure",
            "doc": "docs/ZERO_TOLERANCE_BINDING_AR.md",
            "binding": True,
            "defect_count": 7,
        },
        "f1_f10_unique_full_ship": {
            "F1": "/miss-feed",
            "F2": "/emotion-tax",
            "F3": "/allocator-receipt",
            "F4": "/transfer-intent",
            "F5": "/silence-index",
            "F6": "/alert-passport",
            "F7": "/visibility-cost",
            "F8": "/validity-decay",
            "F9": "/desk-duel",
            "F10": "/trust-debt",
            "status_api": "/api/public/f1-f10-closure",
            "product_complete": False,
        },
    }


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
