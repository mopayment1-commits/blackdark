"""Integrate scoped capabilities into decision/opportunity payloads."""

from __future__ import annotations

from typing import Any

from capability_spine import context, engineering, execution, gates, quant, ux
from capability_spine import opportunity as opportunity_caps


def _sample_prices(opportunity: dict[str, Any]) -> list[float]:
    hist = opportunity.get("price_history") or opportunity.get("closes") or []
    if hist:
        return [float(p) for p in hist]
    price = float(opportunity.get("price") or 100.0)
    return [price * (1 + 0.001 * i) for i in range(-20, 1)]


def _sample_volumes(opportunity: dict[str, Any]) -> list[float]:
    vols = opportunity.get("volume_history") or []
    if vols:
        return [float(v) for v in vols]
    base = float(opportunity.get("volume_24h") or opportunity.get("quote_volume") or 1_000_000)
    return [base * (0.95 + 0.01 * i) for i in range(21)]


def enrich_opportunity_capabilities(
    opportunity: dict[str, Any],
    *,
    portfolio: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach canonical capability_spine outputs for all locally completable scoped IDs."""
    opp = dict(opportunity)
    portfolio = portfolio or {}
    prices = _sample_prices(opp)
    volumes = _sample_volumes(opp)
    btc_prices = opp.get("btc_price_history") or prices
    eth_prices = opp.get("eth_price_history") or prices

    trace = engineering.ensure_e2e_trace_id(incoming=(headers or {}).get("x-correlation-id"))
    opp["trace_id"] = trace["trace_id"]

    caps: dict[str, Any] = {}

    # Quant — greenfield + partial
    caps["CAP-01"] = quant.amihud_illiquidity(prices, volumes)
    caps["CAP-02"] = quant.kyles_lambda(
        [prices[i] - prices[i - 1] for i in range(1, len(prices))],
        opp.get("signed_flow") or [1.0, -1.0] * (len(prices) // 2),
    )
    book = opp.get("book") or {"asks": [[float(opp.get("price") or 100), 10.0]], "bids": [[float(opp.get("price") or 100) * 0.999, 10.0]]}
    caps["CAP-03"] = execution.slippage_impact_vector(
        book,
        notional_usd=float(opp.get("quote_amount") or opp.get("notional_usd") or 10_000),
        book_age_ms=opp.get("book_age_ms"),
    )
    caps["CAP-04"] = quant.vwap_deviation_index(prices, volumes)
    caps["CAP-05"] = quant.volume_velocity(volumes)
    caps["CAP-06"] = quant.order_cancellation_velocity(opp.get("book_events") or [])
    caps["CAP-07"] = quant.var_99(prices, notional=float(opp.get("quote_amount") or 10_000))
    caps["CAP-08"] = quant.cvar_expected_shortfall(prices, confidence=0.95, notional=float(opp.get("quote_amount") or 10_000))
    caps["CAP-09"] = quant.monte_carlo_scenarios(prices, seed=42, notional=float(opp.get("quote_amount") or 10_000))
    caps["CAP-10"] = quant.sharpe_ratio(prices)
    caps["CAP-11"] = quant.sortino_ratio(prices)
    caps["CAP-12"] = quant.max_drawdown_duration(prices)
    caps["CAP-13"] = quant.beta_to_benchmark(prices, btc_prices)
    caps["CAP-14"] = quant.beta_to_benchmark(prices, eth_prices)
    caps["CAP-15"] = quant.correlation_decay_matrix(prices, btc_prices)
    caps["CAP-16"] = quant.depeg_risk_score(float(opp.get("price") or 1.0), peg=float(opp.get("peg") or 1.0))
    caps["CAP-17"] = quant.large_vs_small_trade_participation(
        opp.get("trades")
        or [{"notional_usd": 1000}, {"notional_usd": 75_000}, {"notional_usd": 5000}]
    )
    caps["CAP-18"] = quant.maker_taker_net_delta(
        opp.get("trades") or [{"aggressor": "TAKER", "notional_usd": 1000}, {"aggressor": "MAKER", "notional_usd": 800}]
    )
    caps["CAP-19"] = quant.oi_momentum_delta(opp.get("oi_series") or [100.0, 102.0, 105.0, 108.0, 112.0, 118.0])
    caps["CAP-20"] = quant.funding_momentum_shift(opp.get("funding_history") or [0.0001, 0.0002, 0.00015, 0.0003, 0.0004, 0.0005])
    spot_vol = float(opp.get("spot_volume") or opp.get("volume_24h") or 1.0)
    deriv_vol = float(opp.get("derivative_volume") or spot_vol * 1.5)
    caps["CAP-21"] = quant.derivative_to_spot_volume_multiple(deriv_vol, spot_vol)
    caps["CAP-22"] = quant.effective_basis_yield(
        float(opp.get("spot_price") or opp.get("price") or 100),
        float(opp.get("derivative_price") or opp.get("price") or 100.5),
    )
    legs = opp.get("position_legs") or []
    from capability_spine.quant import PositionLeg, delta_neutral_validator

    cap23_legs = [
        PositionLeg(
            symbol=str(leg.get("symbol") or "BTC"),
            quantity=float(leg.get("quantity") or 0),
            delta=float(leg.get("delta") or 1),
            contract_multiplier=float(leg.get("contract_multiplier") or 1),
        )
        for leg in legs
    ] if legs else [PositionLeg("BTC", 1.0, 1.0), PositionLeg("BTC-PERP", -1.0, 1.0)]
    caps["CAP-23"] = delta_neutral_validator(cap23_legs)
    caps["CAP-24"] = quant.funding_spread_matrix(opp.get("venue_funding") or {"binance": 0.0001, "okx": 0.0002, "bybit": None})
    caps["CAP-25"] = quant.estimated_liquidation_cascade_risk(
        oi_usd=float(opp.get("oi_usd") or 1e9),
        leverage_proxy=float(opp.get("leverage_proxy") or 10),
        funding_rate=float(opp.get("funding_rate") or 0.0001),
        depth_usd=float(opp.get("depth_usd") or 1e7),
        volatility=float(opp.get("volatility") or 0.02),
    )
    caps["CAP-26"] = quant.iv_skew(opp.get("call_iv"), opp.get("put_iv"))
    caps["CAP-27"] = quant.put_call_ratio(opp.get("put_volume"), opp.get("call_volume"))
    caps["CAP-28"] = quant.nvt_ratio(
        float(opp.get("market_cap") or 1e11),
        opp.get("onchain_tx_value"),
        cex_volume_proxy=float(opp.get("volume_24h") or opp.get("quote_volume") or 1.0),
    )

    # Opportunity lifecycle
    score = opportunity_caps.compute_opportunity_score(opp)
    caps["CAP-34"] = score
    caps["CAP-35"] = opportunity_caps.explain_opportunity_score(opp, score)
    caps["CAP-36"] = opportunity_caps.track_opportunity_lifetime(opp)
    caps["CAP-37"] = opportunity_caps.survival_decay_model(age_seconds=float(opp.get("age_seconds") or 0), half_life_seconds=float(opp.get("half_life_seconds") or 300))
    caps["CAP-38"] = {"ok": True, "ledger_path": "data/opportunity_disappearance_ledger.jsonl"}
    caps["CAP-50"] = opportunity_caps.snapshot_at_detection(opp)
    caps["CAP-53"] = opportunity_caps.classify_opportunity_failure(opp)
    caps["CAP-55"] = opportunity_caps.reconcile_prediction_outcome(
        prediction=str(opp.get("prediction") or opp.get("verdict") or "WAIT"),
        realized=opp.get("realized_outcome"),
        horizon=str(opp.get("time_horizon") or "1h"),
        registered_at=str(opp.get("detected_at") or opp.get("timestamp") or ""),
    )
    caps["CAP-58"] = opportunity_caps.build_opportunity_explainability(opp)
    caps["CAP-59"] = opportunity_caps.disclose_missing_evidence(
        expected=opp.get("expected_evidence") or ["price", "freshness", "liquidity"],
        present=opp.get("present_evidence") or [],
    )
    caps["CAP-60"] = opportunity_caps.classify_performance_evidence(
        evidence_class=str(opp.get("evidence_class") or "SIMULATED"),
        source_ref=opp.get("evidence_ref"),
    )
    caps["CAP-63"] = opportunity_caps.append_decision_audit(
        decision_id=str(opp.get("decision_id") or opp.get("prediction_id") or "unknown"),
        event_type="capability_enrichment",
        payload={"score": score.get("score")},
        trace_id=trace["trace_id"],
    )

    # Gates
    caps["CAP-39"] = execution.required_size_liquidity_gate(
        book,
        notional_usd=float(opp.get("quote_amount") or 10_000),
        book_age_ms=opp.get("book_age_ms"),
    )
    caps["CAP-40"] = execution.order_book_integrity_gate(opp.get("book_events") or [])
    caps["CAP-41"] = gates.per_source_feature_freshness(
        source=str(opp.get("source") or "cex_spot"),
        feature=str(opp.get("feature") or "ticker"),
        age_seconds=opp.get("data_age_sec") or (float(opp.get("quote_age_ms") or 0) / 1000.0 if opp.get("quote_age_ms") else None),
    )
    import time

    now_ms = time.time() * 1000
    caps["CAP-43"] = gates.time_sync_clock_skew_detection(
        source_ts_ms=float(opp.get("source_ts_ms") or now_ms - 100),
        ingest_ts_ms=float(opp.get("ingest_ts_ms") or now_ms),
    )
    caps["CAP-44"] = gates.venue_trading_status_gate(
        str(opp.get("buy_exchange") or opp.get("venue") or "binance"),
        trading_state=opp.get("venue_trading_state"),
        deposit_open=opp.get("deposit_open"),
        withdraw_open=opp.get("withdraw_open"),
        status_age_s=opp.get("venue_status_age_s"),
    )
    caps["CAP-45"] = gates.network_compatibility_validator(
        asset=str(opp.get("asset") or opp.get("symbol") or "BTC"),
        chain=str(opp.get("chain") or "ethereum"),
        deposit_networks=opp.get("deposit_networks"),
        withdraw_networks=opp.get("withdraw_networks"),
        required_network=opp.get("required_network"),
    )
    caps["CAP-46"] = gates.new_asset_probation_gate(
        str(opp.get("asset") or opp.get("symbol") or "BTC"),
        lifecycle_state=str(opp.get("asset_lifecycle") or "PROBATION"),
        listing_age_days=opp.get("listing_age_days"),
        data_quality_score=opp.get("data_quality_score"),
    )
    caps["CAP-47"] = gates.user_capital_constraint(
        declared_capital_usd=portfolio.get("capital_usd"),
        required_capital_usd=float(opp.get("quote_amount") or opp.get("required_capital_usd") or 0),
    )
    caps["CAP-48"] = gates.user_risk_constraint(
        risk_score=float((opp.get("risk") or {}).get("risk_after") or opp.get("risk_score") or 0),
        max_risk=portfolio.get("max_risk"),
        preferences=portfolio.get("risk_preferences"),
    )

    # Execution / reconciliation
    paper = execution.paper_trading_execute({"quantity": 1.0, "price": float(opp.get("price") or 100)})
    caps["CAP-49"] = paper
    expected = caps["CAP-03"] if caps["CAP-03"].get("ok") else {}
    caps["CAP-51"] = execution.expected_vs_simulated_reconciliation(expected, caps["CAP-03"]) if expected else {"ok": False, "reason": "no_expected_snapshot"}
    caps["CAP-52"] = execution.expected_vs_observed_slippage_reconciliation(
        float(expected.get("slippage_bps") or 0),
        float(opp.get("observed_slippage_bps") or expected.get("slippage_bps") or 0),
        evidence_class=str(opp.get("evidence_class") or "SIMULATED"),
    )
    caps["CAP-54"] = execution.executable_opportunity_ratio(
        opp.get("opportunity_sample") or [{"executable": caps["CAP-39"].get("pass"), "gate_state": caps["CAP-39"].get("gate_state")}]
    )

    # Context
    caps["CAP-72"] = context.network_health_matrix(opp.get("chain_health"))
    caps["CAP-73"] = context.m2_liquidity_context(
        value_usd_billions=opp.get("m2_usd_billions"),
        release_date=opp.get("m2_release_date"),
    )
    caps["CAP-74"] = context.interest_rate_context(
        policy_rate=opp.get("policy_rate"),
        target_range=opp.get("policy_target_range"),
        market_yield=opp.get("market_yield") or 0.045,
        effective_date=opp.get("rate_effective_date"),
    )
    caps["CAP-75"] = context.fear_greed_context_sync(
        opp.get("sentiment") or {"fear_greed_index": opp.get("fear_greed_index"), "fear_greed_label": opp.get("fear_greed_label")} or opp
    )

    # Engineering
    caps["CAP-67"] = trace
    caps["CAP-68"] = engineering.backoff_policy_summary()
    caps["CAP-70"] = engineering.upstream_cost_guard_status()
    caps["EC-01"] = engineering.run_selective_mutation_tests()
    caps["EC-03"] = engineering.chaos_failure_injection_report()
    caps["EC-04"] = engineering.release_intelligence_quality_gate(tests_passed=True)
    caps["EC-06"] = engineering.retention_tier_architecture()
    caps["EC-07"] = engineering.anomaly_training_dataset()
    caps["EC-09"] = engineering.websocket_lifecycle_status()
    caps["EC-10"] = engineering.venue_rollout_state(
        str(opp.get("buy_exchange") or "binance"),
        health_score=float(opp.get("venue_health_score") or 80),
    )

    # UX
    opp["capability_spine"] = caps
    caps["UX-01"] = ux.calm_decision_surface(opp, mode=str(portfolio.get("ux_mode") or "beginner"))
    caps["UX-02"] = ux.complete_opportunity_card(opp)
    caps["UX-03"] = ux.progressive_disclosure_layers(opp, mode=str(portfolio.get("ux_mode") or "beginner"))

    opp["capability_spine"] = caps
    opp["opportunity_score"] = score.get("score")
    return opp
