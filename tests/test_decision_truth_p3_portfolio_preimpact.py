"""P3 portfolio pre-impact and risk behavior tests."""

from __future__ import annotations

from decision_truth import govern_decision_payload
from decision_truth.depeg import evaluate_depeg_risk
from decision_truth.portfolio_context import resolve_portfolio_context
from decision_truth.portfolio_risk import evaluate_portfolio_risk
from decision_truth.pre_impact import evaluate_pre_impact
from decision_truth.reverse_stress import evaluate_reverse_stress
from decision_truth.risk_envelope import build_risk_envelope
from decision_truth.venue_health import evaluate_venue_health_decision


def _arb(**overrides):
    base = {
        "kind": "cross_exchange",
        "symbol": "BTC/USDT",
        "quote_amount": 1000,
        "net_profit_usdt": 2.5,
        "total_slippage_bps": 3,
        "trading_fees_usdt": 0.2,
        "withdrawal_fee_usdt": 0.05,
        "quote_age_ms": 120,
        "depth_usd": 200000,
        "fill_probability": 0.9,
        "estimated_recipients": 5,
        "live_duration_seconds": 6,
        "data_quality_score": 80,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "liquidity_ok": True,
        "risk_ok": True,
    }
    base.update(overrides)
    return base


def _portfolio_payload(**overrides):
    base = _arb(
        user_id=42,
        portfolio_holdings=[
            {"asset": "BTC", "value_usd": 60000, "venue": "binance"},
            {"asset": "ETH", "value_usd": 20000, "venue": "okx"},
        ],
        user_risk_settings={
            "max_daily_loss_usd": 500,
            "max_concentration_pct": 70,
            "max_venue_exposure_pct": 65,
        },
    )
    if "user_risk_settings" in overrides:
        merged = dict(base.get("user_risk_settings") or {})
        merged.update(overrides.pop("user_risk_settings") or {})
        base["user_risk_settings"] = merged
    base.update(overrides)
    return base


def test_risk_envelope_within_limits():
    ctx = resolve_portfolio_context(_portfolio_payload())
    env = build_risk_envelope(_portfolio_payload(), portfolio_context=ctx)
    assert env["dimensions"]["max_tolerated_loss_usd"]["origin"] == "USER_CONFIGURED"
    assert env["current_use"]["state"] == "AVAILABLE"


def test_near_limit_behavior():
    ctx = resolve_portfolio_context(_portfolio_payload())
    env = build_risk_envelope(_portfolio_payload(), portfolio_context=ctx)
    pre = evaluate_pre_impact(_portfolio_payload(quote_amount=50000), envelope=env, portfolio_context=ctx)
    assert pre["state"] == "AVAILABLE"
    assert pre["near_limit_dimensions"] or pre["breached_dimensions"]


def test_post_decision_breach():
    ctx = resolve_portfolio_context(_portfolio_payload())
    env = build_risk_envelope(
        _portfolio_payload(user_risk_settings={"max_concentration_pct": 55, "max_daily_loss_usd": 500}),
        portfolio_context=ctx,
    )
    pre = evaluate_pre_impact(_portfolio_payload(quote_amount=120000), envelope=env, portfolio_context=ctx)
    assert pre["material_breach"] is True
    assert pre["decision_impact"] in {"reject", "abstain"}


def test_unavailable_portfolio_state():
    ctx = resolve_portfolio_context({"symbol": "BTC"})
    assert ctx["state"] == "PORTFOLIO_CONTEXT_UNAVAILABLE"
    env = build_risk_envelope({"symbol": "BTC"}, portfolio_context=ctx)
    assert env["current_use"]["state"] == "UNAVAILABLE"


def test_user_configured_vs_system_derived():
    ctx = resolve_portfolio_context(_portfolio_payload())
    env = build_risk_envelope(_portfolio_payload(), portfolio_context=ctx)
    assert env["dimensions"]["max_tolerated_loss_usd"]["origin"] == "USER_CONFIGURED"
    assert env["dimensions"]["liquidity_coverage"]["origin"] == "SYSTEM_DERIVED"


def test_reverse_stress_identifies_scenario():
    ctx = resolve_portfolio_context(_portfolio_payload())
    env = build_risk_envelope(_portfolio_payload(), portfolio_context=ctx)
    stress = evaluate_reverse_stress(_portfolio_payload(buy_exchange="binance"), envelope=env, portfolio_context=ctx)
    assert stress["state"] == "AVAILABLE"
    assert len(stress["scenarios"]) >= 1


def test_reverse_stress_insufficient_data():
    ctx = resolve_portfolio_context({"symbol": "BTC"})
    env = build_risk_envelope({"symbol": "BTC"}, portfolio_context=ctx)
    stress = evaluate_reverse_stress({"symbol": "BTC"}, envelope=env, portfolio_context=ctx)
    assert stress["state"] == "UNAVAILABLE"


def test_venue_healthy():
    out = evaluate_venue_health_decision(_portfolio_payload(buy_exchange="binance", sell_exchange="okx"))
    assert out["state"] == "AVAILABLE"
    assert out["aggregate_health_state"] in {"healthy", "warning", "degraded"}


def test_venue_degraded():
    out = evaluate_venue_health_decision(
        _portfolio_payload(
            buy_exchange="okx",
            venue_health={"venue": "okx", "health_score": 48, "indicators": {"withdrawal_velocity": {"value": "elevated"}}},
        )
    )
    assert out["decision_impact"] in {"degrade", "abstain", "reject"}


def test_venue_unavailable_no_fabrication():
    out = evaluate_venue_health_decision(_portfolio_payload())
    assert out["state"] in {"AVAILABLE", "NOT_APPLICABLE"}


def test_critical_venue_rejects_in_govern():
    out = govern_decision_payload(
        _portfolio_payload(buy_exchange="ftx", sell_exchange="ftx"),
        run_data_governance=False,
    )
    assert out["decision_truth_state"] == "REJECTED"


def test_stablecoin_normal():
    out = evaluate_depeg_risk(
        _portfolio_payload(
            stablecoin_quotes={
                "USDT": [
                    {"source": "a", "price": 1.0001},
                    {"source": "b", "price": 1.0002},
                ]
            }
        )
    )
    assert out["aggregate_risk_band"] == "normal"


def test_depeg_warning_state():
    out = evaluate_depeg_risk(
        _portfolio_payload(
            stablecoin_quotes={
                "USDT": [
                    {"source": "a", "price": 0.9955},
                    {"source": "b", "price": 0.9958},
                ]
            }
        )
    )
    assert out["aggregate_risk_band"] in {"warning", "material"}


def test_material_depeg_abstain_or_reject():
    out = govern_decision_payload(
        _portfolio_payload(
            stablecoin_quotes={
                "USDT": [
                    {"source": "a", "price": 0.985},
                    {"source": "b", "price": 0.984},
                ]
            }
        ),
        run_data_governance=False,
    )
    assert out["decision_truth_state"] in {"REJECTED", "ABSTAINED", "UNAVAILABLE", "DEGRADED"}


def test_conflicting_depeg_sources():
    out = evaluate_depeg_risk(
        _portfolio_payload(
            stablecoin_quotes={
                "USDT": [
                    {"source": "a", "price": 1.0},
                    {"source": "b", "price": 0.992},
                ]
            }
        )
    )
    assert out["tokens"][0].get("reason_codes") == ["conflicting_depeg_sources"] or out["aggregate_risk_band"] == "warning"


def test_no_false_portfolio_personalization():
    ctx = resolve_portfolio_context({"symbol": "BTC"})
    assert ctx["state"] == "PORTFOLIO_CONTEXT_UNAVAILABLE"
    assert ctx["holdings"] == []


def test_decision_contract_integration():
    out = govern_decision_payload(_portfolio_payload(), run_data_governance=False)
    contract = (out.get("decision_truth") or {}).get("contract") or {}
    risk = contract.get("risk") or {}
    assert risk.get("risk_envelope")
    assert risk.get("portfolio_pre_impact") or risk.get("pre_impact")


def test_portfolio_risk_orchestrator():
    pack = evaluate_portfolio_risk(_portfolio_payload())
    assert pack["state"] == "AVAILABLE"
    assert pack["risk_envelope"]
    assert pack["reverse_stress"]
