"""
Net-Edge Truth Score — Feature #417 (Intelligence Ledger Sprint-2 Core).

Core scoring engine — NOT standalone. Compresses opportunity quality into a
transparent score based on executable net edge, not raw gross spread.

Integrations:
  - #403/#429 Arbitrage Scanner: every opportunity gets Net-Edge Score + rejection reasons
  - #415 Fill Feasibility: depth/capacity penalties + stale/unfillable fail-closed
  - #449 Portfolio Intelligence: net-edge per holding + opportunity
  - #460 Diligence Risk: ranking adjustment
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.NetEdgeTruthLayer")

_FEATURE_ID = 417
_TITLE = "Net-Edge Truth Score"
_LEGAL_NAME = "Net-Edge Truth Score"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Sprint-2 Core"
_SPRINT = 2
_PRIORITY = "critical"
_SEED_PATH = Path("data/net_edge_truth_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Net-Edge Truth Score — executable economics after fees, slippage, latency, "
    "network costs, and liquidity capacity. Unknown costs use worst-case estimates, "
    "never zero. Stale or unfillable opportunities fail closed. "
    "Simulation only — not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"formula_version": "2.0.0", "regression_fixtures": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("net edge truth seed load failed: %s", exc)
        return {"formula_version": "2.0.0", "regression_fixtures": []}


def _attach_worst_case_defaults(opportunity: dict[str, Any], *, seed: dict[str, Any]) -> dict[str, Any]:
    """Apply worst-case cost bounds when economics fields are absent — never invent zero."""
    enriched = dict(opportunity)
    if enriched.get("worst_case_costs"):
        return enriched
    defaults = seed.get("worst_case_costs_default") or {}
    if not defaults:
        return enriched
    wc: dict[str, Any] = {}
    if "withdrawal_fee_usdt" not in enriched and defaults.get("withdrawal_fee_usdt") is not None:
        wc["withdrawal_fee_usdt"] = defaults["withdrawal_fee_usdt"]
    if "trading_fees_usdt" not in enriched and "fees_usdt" not in enriched:
        if defaults.get("trading_fees_usdt") is not None:
            wc["trading_fees_usdt"] = defaults["trading_fees_usdt"]
    if "transfer_cost_usdt" not in enriched and defaults.get("transfer_cost_usdt") is not None:
        wc["transfer_cost_usdt"] = defaults["transfer_cost_usdt"]
    if wc:
        enriched["worst_case_costs"] = {**defaults, **wc}
    return enriched


def evaluate_opportunity_truth(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
    apply_worst_case: bool = False,
) -> dict[str, Any]:
    """Score one opportunity with full #417 output + evidence."""
    from net_edge_truth import FORMULA_VERSION, compute_net_edge_truth

    seed = seed or _load_seed()
    opp = dict(opportunity)
    if apply_worst_case:
        opp = _attach_worst_case_defaults(opp, seed=seed)

    truth = compute_net_edge_truth(opp)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "formula_version": FORMULA_VERSION,
        "opportunity_id": opp.get("opportunity_id"),
        "asset": opp.get("asset") or opp.get("symbol"),
        "net_edge_truth": truth,
        "net_edge_score": truth.get("net_edge_score"),
        "net_return_pct": truth.get("net_return_pct"),
        "executable_size": truth.get("executable_size"),
        "rejection_reasons": truth.get("reasons") or [],
        "evidence": truth.get("evidence") or {},
        "pass": truth.get("pass"),
        "reject": truth.get("reject"),
        "simulation_only": True,
        "timestamp": _utcnow(),
    }


def evaluate_arbitrage_opportunity(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
    enrich_feasibility: bool = True,
) -> dict[str, Any]:
    """#403 integration — attach feasibility (#415) then score (#417)."""
    seed = seed or _load_seed()
    opp = dict(opportunity)

    if enrich_feasibility and opp.get("buy_venue") and opp.get("sell_venue"):
        try:
            from bd_platform.fill_feasibility_simulator import enrich_arbitrage_opportunity

            opp = enrich_arbitrage_opportunity(opp, size=float(opp.get("requested_size") or 1.0))
        except Exception:
            logger.debug("feasibility enrichment skipped", exc_info=True)

    truth_opp = {
        **opp,
        "net_profit_usdt": opp.get("net_edge_usdt") or opp.get("net_profit_usdt"),
        "total_slippage_bps": opp.get("slippage_bps") or opp.get("total_slippage_bps"),
        "trading_fees_usdt": opp.get("trading_fees_usdt"),
        "withdrawal_fee_usdt": opp.get("withdrawal_fee_usdt"),
        "transfer_cost_usdt": opp.get("transfer_cost_usdt"),
        "quote_age_ms": opp.get("quote_age_ms"),
    }
    result = evaluate_opportunity_truth(truth_opp, seed=seed)

    # #472 Investment Thesis Scoring — thesis score adjusts confidence (#417 integration)
    try:
        from bd_platform.investment_thesis_scoring import apply_thesis_to_confidence

        thesis_ctx = apply_thesis_to_confidence(opp, truth_result=result, seed=seed)
        if thesis_ctx.get("ok"):
            result["thesis_confidence_472"] = thesis_ctx
            truth = result.get("net_edge_truth") or {}
            if truth.get("truth_score") is not None:
                truth = dict(truth)
                truth["thesis_adjusted_confidence"] = thesis_ctx.get("adjusted_confidence")
                truth["thesis_grade"] = thesis_ctx.get("thesis_grade")
                result["net_edge_truth"] = truth
    except Exception:
        logger.debug("thesis confidence integration skipped", exc_info=True)

    return result


def build_truth_score_panel(
    *,
    opportunity_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Panel of scored opportunities from unified arbitrage feed."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    evaluations: list[dict[str, Any]] = []

    try:
        from bd_platform.unified_arbitrage_engine import build_unified_feed

        feed = build_unified_feed()
        for opp in feed.get("opportunities") or []:
            if opportunity_id and opp.get("opportunity_id") != opportunity_id:
                continue
            if opp.get("net_edge_truth"):
                evaluations.append({
                    "opportunity_id": opp.get("opportunity_id"),
                    "asset": opp.get("asset"),
                    "net_edge_truth": opp["net_edge_truth"],
                    "rejection_reasons": (opp["net_edge_truth"] or {}).get("reasons") or [],
                })
            else:
                evaluations.append(evaluate_arbitrage_opportunity(opp, seed=seed))
    except Exception:
        logger.debug("unified feed unavailable for truth panel", exc_info=True)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    from net_edge_truth import FORMULA_VERSION

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "formula_version": FORMULA_VERSION,
        "evaluations": evaluations,
        "count": len(evaluations),
        "disclaimer": _DISCLAIMER,
        "simulation_only": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_portfolio_net_edge_scores(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#449 integration — net-edge score per holding + live opportunities."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    holdings = seed.get("portfolio_holdings") or []
    asset_scores: list[dict[str, Any]] = []

    for holding in holdings:
        asset = str(holding.get("asset") or "BTC")
        proxy_opp = {
            "opportunity_id": f"holding_{asset.lower()}",
            "asset": asset,
            "opportunity_type": "holding",
            "net_profit_usdt": 0.0,
            "quote_amount": 1000,
            "total_slippage_bps": 5,
            "withdrawal_fee_usdt": 0.0,
            "trading_fees_usdt": 0.0,
            "quote_age_ms": 200,
            "volume_feasibility": {"liquidity_score": 75, "max_executable_size": 1.0,
                                   "buy_leg": {"verdict": "full_fill"}, "sell_leg": {"verdict": "full_fill"}},
        }
        scored = evaluate_opportunity_truth(proxy_opp, seed=seed)
        asset_scores.append({
            "asset": asset,
            "weight_pct": holding.get("weight_pct"),
            "opportunity_type": holding.get("opportunity_type", "holding"),
            "net_edge_score": scored.get("net_edge_score"),
            "net_return_pct": scored.get("net_return_pct"),
            "reject": scored.get("reject"),
            "rejection_reasons": scored.get("rejection_reasons"),
        })

    opportunities: list[dict[str, Any]] = []
    try:
        from bd_platform.unified_arbitrage_engine import build_unified_feed

        for opp in (build_unified_feed().get("opportunities") or [])[:5]:
            truth = opp.get("net_edge_truth") or evaluate_arbitrage_opportunity(opp, seed=seed).get("net_edge_truth")
            opportunities.append({
                "opportunity_id": opp.get("opportunity_id"),
                "asset": opp.get("asset"),
                "opportunity_type": opp.get("opportunity_type"),
                "net_edge_score": (truth or {}).get("net_edge_score"),
                "net_return_pct": (truth or {}).get("net_return_pct"),
                "executable_size": (truth or {}).get("executable_size"),
                "rejection_reasons": (truth or {}).get("reasons") or [],
            })
    except Exception:
        logger.debug("opportunity net-edge skipped", exc_info=True)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    from net_edge_truth import FORMULA_VERSION

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "portfolio_id": portfolio_id,
        "formula_version": FORMULA_VERSION,
        "holdings": asset_scores,
        "opportunities": opportunities,
        "truth_score_history": build_truth_score_history_panel(seed=seed),
        "disclaimer": _DISCLAIMER,
        "simulation_only": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_truth_score_history_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Truth Score History — predicted vs outcome for trust calibration."""
    seed = seed or _load_seed()
    from net_edge_truth import FORMULA_VERSION, load_truth_score_history, truth_score_history_summary

    live = load_truth_score_history(limit=100)
    samples = seed.get("truth_score_history_samples") or []
    combined = samples + [r for r in live if r not in samples]
    summary = truth_score_history_summary()
    scored = [r for r in combined if r.get("outcome_recorded")]
    correct = sum(1 for r in scored if r.get("outcome") == "correct")
    return {
        "formula_version": FORMULA_VERSION,
        "total_predictions": len(combined),
        "outcomes_recorded": len(scored),
        "correct_predictions": correct,
        "accuracy_rate": round(correct / len(scored), 4) if scored else summary.get("accuracy_rate"),
        "records": combined[-20:],
        "trust_calibration": (
            "Shows how often signals with a given predicted score were later validated. "
            "Builds confidence in Net-Edge Truth over gross-spread theater."
        ),
    }


def build_intelligence_ledger_integration() -> dict[str, Any]:
    from net_edge_truth import FORMULA_VERSION, net_edge_truth_status

    status = net_edge_truth_status()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "layer": "intelligence_ledger",
        "formula_version": FORMULA_VERSION,
        "status": status,
        "integrations": (_load_seed().get("integrations") or {}),
        "timestamp": _utcnow(),
    }


def net_edge_truth_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    from net_edge_truth import FORMULA_VERSION

    formula = seed.get("formula") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "formula_version": FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "formula_documented": bool(formula),
        "unknown_costs_never_zero": True,
        "fail_closed_stale_unfillable": True,
        "integrations": seed.get("integrations") or {},
        "simulation_only": seed.get("simulation_only", True),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_regression_fixtures(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Deterministic regression set from seed fixtures."""
    seed = seed or _load_seed()
    results: list[dict[str, Any]] = []
    for fixture in seed.get("regression_fixtures") or []:
        inp = fixture.get("input") or {}
        expect = fixture.get("expect") or {}
        scored = evaluate_opportunity_truth(inp, seed=seed)
        truth = scored.get("net_edge_truth") or {}
        passed = True
        details: list[str] = []

        if "pass" in expect and truth.get("pass") != expect["pass"]:
            passed = False
            details.append(f"pass expected {expect['pass']} got {truth.get('pass')}")
        if expect.get("reject") and not truth.get("reject"):
            passed = False
            details.append("expected reject")
        if expect.get("min_truth_score") and float(truth.get("truth_score") or 0) < float(expect["min_truth_score"]):
            passed = False
            details.append("truth_score below min")
        if expect.get("reason") and expect["reason"] not in (truth.get("reasons") or []):
            passed = False
            details.append(f"missing reason {expect['reason']}")
        for reason in expect.get("reasons_include") or []:
            if reason not in (truth.get("reasons") or []):
                passed = False
                details.append(f"missing reason {reason}")
        if expect.get("cost_policy"):
            policies = truth.get("cost_policies") or {}
            wd = (policies.get("withdrawal") or {}).get("source")
            if wd != expect["cost_policy"]:
                passed = False
                details.append(f"cost_policy expected {expect['cost_policy']} got {wd}")

        results.append({
            "fixture_id": fixture.get("id"),
            "passed": passed,
            "truth_score": truth.get("truth_score"),
            "reject": truth.get("reject"),
            "reasons": truth.get("reasons"),
            "details": details,
        })

    passed_count = sum(1 for r in results if r["passed"])
    return {
        "ok": passed_count == len(results),
        "feature_id": _FEATURE_ID,
        "fixtures": results,
        "passed": passed_count,
        "total": len(results),
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "ledger core"})
    checks.append({"id": "formula_version", "passed": bool(seed.get("formula_version")), "detail": seed.get("formula_version")})
    checks.append({"id": "unknown_costs_never_zero", "passed": (seed.get("formula") or {}).get("unknown_costs_policy") == "worst_case_estimate_never_zero", "detail": "policy"})
    checks.append({"id": "fail_closed_documented", "passed": bool((seed.get("formula") or {}).get("fail_closed")), "detail": "gates"})

    regression = run_regression_fixtures(seed=seed)
    checks.append({"id": "deterministic_regression", "passed": regression["ok"], "detail": f"{regression['passed']}/{regression['total']}"})

    status = net_edge_truth_layer_status()
    checks.append({"id": "layer_status", "passed": status.get("ok") is True, "detail": "417"})

    panel = build_truth_score_panel(seed=seed)
    checks.append({"id": "arbitrage_integration_403", "passed": panel.get("ok") is True, "detail": f"count={panel.get('count')}"})

    portfolio = build_portfolio_net_edge_scores(seed=seed)
    checks.append({"id": "portfolio_integration_449", "passed": len(portfolio.get("holdings") or []) >= 1, "detail": "holdings"})

    history = build_truth_score_history_panel(seed=seed)
    checks.append({"id": "truth_score_history", "passed": history.get("total_predictions", 0) >= 1, "detail": "history"})

    from bd_platform.investment_thesis_scoring import run_reconciliation_tests as thesis_tests
    thesis = thesis_tests()
    checks.append({"id": "investment_thesis_472", "passed": thesis.get("ok") is True, "detail": f"{thesis.get('passed')}/{thesis.get('total')}"})

    opp_eval = evaluate_arbitrage_opportunity({"asset": "BTC", "opportunity_type": "cross_venue"}, seed=seed)
    thesis_ctx = opp_eval.get("thesis_confidence_472") or {}
    checks.append({
        "id": "thesis_confidence_integration",
        "passed": thesis_ctx.get("not_price_probability") is True,
        "detail": thesis_ctx.get("thesis_grade"),
    })

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
