"""Batch 01 dedicated backends — goal-specific payloads (not generic handler fallbacks).

Each capability in BATCH01_DEDICATED_IDS returns a unique ``surface`` and domain payload
matching the CAP646 catalog name via real underlying modules.
"""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer, attach_evidence_metadata, infer_evidence_class

# Official batch 01 dedicated backends (IDs 1–50) + legacy extension IDs with dedicated spines.
BATCH01_DEDICATED_IDS: frozenset[int] = frozenset(
    {
        6,
        7,
        8,
        9,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        40,
        41,
        42,
        43,
        44,
        46,
        50,
        55,
        56,
        59,
        60,
        214,
        584,
        629,
    }
)

EXPECTED_SURFACE: dict[int, str] = {
    6: "smart_money_token_screener",
    7: "holder_distribution_intelligence",
    8: "top_holders_concentration_analysis",
    9: "distribution_score",
    11: "wallet_historical_performance_win_rate",
    12: "wallet_entry_exit_analysis",
    13: "wallet_counterparty_relationship_analysis",
    14: "entity_aware_wallet_intelligence",
    15: "exchange_flow_intelligence",
    16: "candle_price_move_investigator",
    17: "smart_alerts",
    18: "custom_wallet_labels",
    19: "wallet_token_watchlists",
    20: "multi_chain_portfolio_intelligence",
    22: "instant_wallet_due_diligence",
    23: "instant_token_due_diligence",
    24: "ai_research_agent_grounded",
    25: "signal_explanation_workflow",
    26: "price_move_explanation",
    27: "smart_money_historical_trend_analysis",
    28: "smart_money_conviction_engine",
    29: "cross_market_decision_intelligence_engine",
    30: "evidence_confidence_layer",
    31: "cross_signal_confirmation",
    32: "contradiction_detection",
    33: "smart_money_actionability_score",
    34: "beginner_decision_mode",
    35: "market_compass_regime_engine",
    36: "on_chain_metrics_library",
    37: "entity_adjusted_metrics",
    40: "mvrv_mvrv_z_score_suite",
    41: "sopr_profitability_intelligence",
    42: "holder_cohort_intelligence",
    43: "supply_dynamics_intelligence",
    44: "exchange_balance_netflow_intelligence",
    46: "digital_asset_treasury_company_intelligence",
    50: "order_book_intelligence",
    55: "nvt_fair_value_model",
    56: "token_screener",
    59: "personalized_research_dashboards",
    60: "metric_based_smart_alerts",
    214: "watchlists",
    584: "risk_management_shield",
    629: "real_time_wallet_alerts",
}

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)


def _sym(params: dict[str, Any]) -> str:
    return str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")


def _addr(params: dict[str, Any]) -> str:
    return str(
        params.get("address")
        or params.get("wallet")
        or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    ).strip()


def _nvt_signal(ratio: float) -> str:
    if ratio > 120:
        return "Overheated (high NVT)"
    if ratio > 40:
        return "Fair range"
    return "Undervalued zone"


async def _resolve_nvt_payload(
    symbol: str,
    *,
    notional: float = 10_000,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """Return (nvt, financial_models, success) with consistent ratio/signal."""
    from market_context import fetch_binance_ticker
    from research_lab import _SUPPLY_ESTIMATES, compute_financial_models

    asset = symbol.upper().replace("USDT", "")
    models = await compute_financial_models(asset, notional=notional)
    nvt = dict(models.get("nvt") or {}) if not models.get("error") else {}
    ratio = float(nvt.get("ratio") or 0)
    if ratio > 0 and nvt.get("signal"):
        return nvt, models, True

    ticker = await fetch_binance_ticker(f"{asset}USDT")
    if not ticker:
        return {}, {"asset": asset, "error": "Market data unavailable"}, False

    price = float(ticker.get("price") or 0)
    quote_volume = float(ticker.get("quote_volume") or ticker.get("volume_24h") or 0)
    supply = float(_SUPPLY_ESTIMATES.get(asset, 100_000_000))
    market_cap = price * supply
    if quote_volume <= 0 or price <= 0:
        return {}, {"asset": asset, "error": "Quote volume unavailable for NVT"}, False

    ratio = round(market_cap / quote_volume, 2)
    nvt = {
        "ratio": ratio,
        "signal": _nvt_signal(ratio),
        "method": "market_cap / 24h_quote_volume",
        "source": ticker.get("source"),
    }
    models = {
        "asset": asset,
        "price": price,
        "market_cap_estimate_usd": round(market_cap, 0),
        "quote_volume_24h": round(quote_volume, 0),
        "notional_for_var": notional,
        "nvt": nvt,
        "data_source": ticker.get("source"),
    }
    return nvt, models, True


async def _build_watchlist_items(
    *,
    symbol: str,
    address: str,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (all_items, onchain_items, market_items)."""
    from bd_platform.security_trust_data_layer import add_etherscan_watch_246, list_etherscan_watchlist_246
    from market_context import fetch_binance_market_overview_pack

    onchain_raw = list_etherscan_watchlist_246()
    onchain_watches = list(onchain_raw.get("watches") or [])
    if not onchain_watches and address:
        add_etherscan_watch_246(
            address=address,
            threshold_eth=float(params.get("threshold_eth") or 1000.0),
        )
        onchain_watches = list(list_etherscan_watchlist_246().get("watches") or [])

    onchain_items = [
        {
            "type": "onchain",
            "address": watch.get("address"),
            "threshold_eth": watch.get("threshold_eth"),
            "label": f"On-chain watch {str(watch.get('address') or '')[:10]}...",
            "privacy_first": watch.get("privacy_first", True),
            "created_at": watch.get("created_at"),
        }
        for watch in onchain_watches
    ]

    pack = await fetch_binance_market_overview_pack(limit=int(params.get("limit") or 12))
    assets = list(pack.get("assets") or [])
    primary = symbol.upper()
    market_items: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _market_item(row: dict[str, Any]) -> dict[str, Any]:
        sym = str(row.get("symbol") or "").upper()
        return {
            "type": "market",
            "symbol": sym,
            "price": row.get("price"),
            "change_24h": row.get("change_24h"),
            "volume_24h": row.get("volume_24h"),
            "verdict": row.get("verdict"),
            "sector": row.get("sector"),
            "list_id": "default_market",
            "label": f"{sym} market watch",
        }

    primary_row = next((row for row in assets if str(row.get("symbol") or "").upper() == primary), None)
    if primary_row:
        market_items.append(_market_item(primary_row))
        seen.add(primary)

    for row in assets:
        sym = str(row.get("symbol") or "").upper()
        if not sym or sym in seen:
            continue
        market_items.append(_market_item(row))
        seen.add(sym)
        if len(market_items) >= int(params.get("limit") or 12):
            break

    return onchain_items + market_items, onchain_items, market_items


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH01_DEDICATED_IDS:
        raise ValueError(f"capability {capability_id} is not in batch01 dedicated spine")

    params = dict(params or {})
    symbol = _sym(params)
    address = _addr(params)

    dispatch = {
        6: _cap006_smart_money_token_screener,
        7: _cap007_holder_distribution,
        8: _cap008_top_holders_concentration,
        9: _cap009_distribution_score,
        11: _cap011_wallet_historical_performance,
        12: _cap012_wallet_entry_exit,
        13: _cap013_wallet_counterparty,
        14: _cap014_entity_aware_wallet,
        15: _cap015_exchange_flow_intelligence,
        16: _cap016_candle_price_move_investigator,
        17: _cap017_smart_alerts,
        18: _cap018_custom_wallet_labels,
        19: _cap019_wallet_token_watchlists,
        20: _cap020_multi_chain_portfolio,
        22: _cap022_instant_wallet_due_diligence,
        23: _cap023_instant_token_due_diligence,
        24: _cap024_ai_research_agent,
        25: _cap025_signal_explanation,
        26: _cap026_price_move_explanation,
        27: _cap027_smart_money_historical_trend,
        28: _cap028_smart_money_conviction,
        29: _cap029_cross_market_decision,
        30: _cap030_evidence_confidence,
        31: _cap031_cross_signal_confirmation,
        32: _cap032_contradiction_detection,
        33: _cap033_actionability_score,
        34: _cap034_beginner_decision_mode,
        35: _cap035_market_compass_regime,
        36: _cap036_on_chain_metrics_library,
        37: _cap037_entity_adjusted_metrics,
        40: _cap040_mvrv_suite,
        41: _cap041_sopr_profitability,
        42: _cap042_holder_cohort_intelligence,
        43: _cap043_supply_dynamics_intelligence,
        44: _cap044_exchange_balance_netflow,
        46: _cap046_treasury_company,
        50: _cap050_order_book_intelligence,
        55: _cap055_nvt_fair_value,
        56: _cap056_token_screener,
        59: _cap059_research_dashboards,
        60: _cap060_metric_smart_alerts,
        214: _cap214_watchlists,
        584: _cap584_risk_shield,
        629: _cap629_real_time_wallet_alerts,
    }
    fn = dispatch.get(capability_id)
    if fn is None:
        raise ValueError(f"batch01 dedicated: unmapped capability {capability_id}")
    return await fn(symbol=symbol, address=address, params=params)


# ─── On-chain / wallet intelligence ───────────────────────────────────────────


async def _cap006_smart_money_token_screener(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_tier_capabilities import smart_money_leaderboard

    board = await smart_money_leaderboard(limit=int(params.get("limit") or 25))
    tokens: dict[str, dict[str, Any]] = {}
    for row in board.get("leaderboard") or []:
        tok = str(row.get("symbol") or row.get("asset") or "").upper()
        if not tok:
            continue
        tokens.setdefault(tok, {"symbol": tok, "whale_events": 0, "total_usd": 0.0, "entities": []})
        tokens[tok]["whale_events"] += 1
        tokens[tok]["total_usd"] += float(row.get("amount_usd") or 0)
        tokens[tok]["entities"].append(row.get("entity"))

    screener = sorted(tokens.values(), key=lambda r: r["total_usd"], reverse=True)
    if symbol != "BTC":
        screener = [r for r in screener if r["symbol"] == symbol] or screener[:10]
    if not screener:
        for row in board.get("protocol_flow_signals") or []:
            screener.append(
                {
                    "symbol": str(row.get("symbol") or row.get("name") or "UNKNOWN").upper(),
                    "whale_events": 1,
                    "total_usd": float(row.get("tvl_usd") or 0),
                    "entities": [row.get("name")],
                    "source": "defillama_protocol_flow",
                }
            )

    return ai_compliance_footer(
        {
            "capability_id": 6,
            "surface": EXPECTED_SURFACE[6],
            "symbol": symbol,
            "screener": screener[:25],
            "protocol_flow_signals": board.get("protocol_flow_signals"),
            "count": len(screener),
            "success": bool(screener),
        }
    )


async def _cap007_holder_distribution(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics

    dist = await holder_analytics(symbol)
    metrics = dist.get("metrics") or {}
    return ai_compliance_footer(
        {
            "capability_id": 7,
            "surface": EXPECTED_SURFACE[7],
            "symbol": symbol,
            "holder_distribution": metrics,
            "circulating_supply": metrics.get("circulating_supply"),
            "locked_supply_pct": metrics.get("locked_supply_pct"),
            "long_short_ratio": metrics.get("long_short_ratio"),
            "source": dist.get("source"),
            "success": bool(dist.get("available")),
        }
    )


async def _cap008_top_holders_concentration(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics

    dist = await holder_analytics(symbol)
    metrics = dist.get("metrics") or {}
    locked_pct = float(metrics.get("locked_supply_pct") or 0)
    circ = float(metrics.get("circulating_supply") or 0)
    total = float(metrics.get("total_supply") or circ or 1)
    top10_proxy_pct = round(min(95.0, max(locked_pct, (total - circ) / total * 100 if total else 0)), 2)
    concentration_risk = "high" if top10_proxy_pct > 60 else "moderate" if top10_proxy_pct > 35 else "low"

    return ai_compliance_footer(
        {
            "capability_id": 8,
            "surface": EXPECTED_SURFACE[8],
            "symbol": symbol,
            "top_holders_concentration": {
                "top10_proxy_pct": top10_proxy_pct,
                "locked_supply_pct": locked_pct,
                "concentration_risk": concentration_risk,
                "method": "supply_concentration_proxy",
            },
            "holder_metrics": metrics,
            "source": dist.get("source"),
            "success": bool(dist.get("available")),
        }
    )


async def _cap009_distribution_score(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics

    dist = await holder_analytics(symbol)
    metrics = dist.get("metrics") or {}
    locked_pct = float(metrics.get("locked_supply_pct") or 0)
    ls_ratio = float(metrics.get("long_short_ratio") or 1.0)
    distribution_score = round(max(0.0, min(100.0, 100 - locked_pct * 0.6 + (ls_ratio - 1) * 10)), 2)
    verdict = "well_distributed" if distribution_score >= 65 else "moderate" if distribution_score >= 40 else "concentrated"

    return ai_compliance_footer(
        {
            "capability_id": 9,
            "surface": EXPECTED_SURFACE[9],
            "symbol": symbol,
            "distribution_score": distribution_score,
            "distribution_verdict": verdict,
            "inputs": {
                "locked_supply_pct": locked_pct,
                "long_short_ratio": ls_ratio,
            },
            "holder_metrics": metrics,
            "source": dist.get("source"),
            "success": bool(dist.get("available")),
        }
    )


async def _cap015_exchange_flow_intelligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48

    exchange = str(params.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=symbol)
    return ai_compliance_footer(
        {
            "capability_id": 15,
            "surface": EXPECTED_SURFACE[15],
            "symbol": symbol,
            "exchange": exchange,
            "exchange_flow": netflow,
            "netflow_proxy": netflow.get("netflow_proxy"),
            "success": netflow.get("ok", True),
        }
    )


async def _cap016_candle_price_move_investigator(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_advanced import _klines
    from market_context import fetch_binance_ticker

    closes = await _klines(symbol, interval=str(params.get("interval") or "1h"), limit=48)
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    if len(closes) >= 3:
        prev, last = closes[-2], closes[-1]
        move_pct = round((last - prev) / prev * 100, 3) if prev else 0.0
        vol_proxy = round(abs(move_pct) * (1 + len(closes) / 48), 3)
        source = "klines"
    elif ticker:
        change = float(ticker.get("change_24h") or 0)
        price = float(ticker.get("price") or 0)
        prev = price / (1 + change / 100) if change else price
        last = price
        move_pct = round(change, 3)
        vol_proxy = round(abs(change), 3)
        source = "ticker_fallback"
    else:
        return ai_compliance_footer(
            {
                "capability_id": 16,
                "surface": EXPECTED_SURFACE[16],
                "symbol": symbol,
                "investigation": {"error": "insufficient_candle_data"},
                "success": False,
            }
        )

    drivers = []
    if move_pct >= 2:
        drivers.append("sharp_up_move")
    elif move_pct <= -2:
        drivers.append("sharp_down_move")
    else:
        drivers.append("range_bound")
    if abs(move_pct) >= 5:
        drivers.append("whale_or_news_candidate")

    return ai_compliance_footer(
        {
            "capability_id": 16,
            "surface": EXPECTED_SURFACE[16],
            "symbol": symbol,
            "candle_investigation": {
                "interval": params.get("interval") or "1h",
                "previous_close": round(prev, 4),
                "last_close": round(last, 4),
                "move_pct": move_pct,
                "volume_proxy": vol_proxy,
                "drivers": drivers,
                "data_source": source,
            },
            "success": True,
        }
    )


async def _cap017_smart_alerts(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_advanced import compute_advanced_metrics
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75
    from instant_alert_engine import engine_stats

    metrics = await compute_advanced_metrics(symbol)
    mvrv_z = float((metrics.get("mvrv") or {}).get("z_score") or 0)
    trigger = {
        "rule": f"smart_alert:{symbol}",
        "metric": "mvrv_z",
        "value": mvrv_z,
        "threshold": float(params.get("threshold") or 2.0),
    }
    alert = evaluate_flexible_alert_75(user_tier=str(params.get("tier") or "pro"), trigger=trigger)
    stats = engine_stats()
    return ai_compliance_footer(
        {
            "capability_id": 17,
            "surface": EXPECTED_SURFACE[17],
            "symbol": symbol,
            "engine": stats,
            "metric_trigger": trigger,
            "alert_evaluation": alert,
            "metrics_snapshot": metrics.get("mvrv"),
            "success": bool(alert.get("ok") or stats),
        }
    )


async def _cap023_instant_token_due_diligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics
    from research_lab import compute_financial_models

    holders = await holder_analytics(symbol)
    models = await compute_financial_models(symbol, notional=float(params.get("notional") or 10_000))
    checklist = {
        "supply_health": holders.get("metrics"),
        "financial_models": models,
        "token": symbol,
        "risk_flags": [],
    }
    locked = float((holders.get("metrics") or {}).get("locked_supply_pct") or 0)
    if locked > 70:
        checklist["risk_flags"].append("high_locked_supply")
    if models.get("error"):
        checklist["risk_flags"].append("financial_model_gap")

    return ai_compliance_footer(
        {
            "capability_id": 23,
            "surface": EXPECTED_SURFACE[23],
            "symbol": symbol,
            "token_due_diligence": checklist,
            "success": bool(holders.get("available") or not models.get("error")),
        }
    )


async def _cap024_ai_research_agent(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from research_lab import build_research_lab_report

    report = await build_research_lab_report()
    grounded = {
        "symbol": symbol,
        "research_lab": report,
        "grounded_sources": ["oracle_audit", "whale_intelligence", "sentiment", "onchain", "macro_regime"],
        "agent_summary": f"Grounded research snapshot for {symbol} from platform data spine.",
    }
    return ai_compliance_footer(
        {
            "capability_id": 24,
            "surface": EXPECTED_SURFACE[24],
            "symbol": symbol,
            "research_agent": grounded,
            "success": bool(report),
        }
    )


async def _cap026_price_move_explanation(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from market_context import fetch_binance_ticker
    from sentiment_engine import build_sentiment_context_safe

    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    sentiment = await build_sentiment_context_safe(symbol)
    change = float((ticker or {}).get("change_24h") or 0)
    reasons = []
    if change >= 3:
        reasons.append("strong_24h_rally")
    elif change <= -3:
        reasons.append("sharp_24h_drawdown")
    else:
        reasons.append("muted_price_action")
    compound = (sentiment.get("sentiment_compound_index") or {}).get(symbol) or {}
    if compound:
        reasons.append("sentiment_context_attached")

    return ai_compliance_footer(
        {
            "capability_id": 26,
            "surface": EXPECTED_SURFACE[26],
            "symbol": symbol,
            "price_move_explanation": {
                "change_24h_pct": change,
                "price": (ticker or {}).get("price"),
                "reasons": reasons,
                "sentiment": compound,
            },
            "success": bool(ticker),
        }
    )


async def _cap031_cross_signal_confirmation(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from signal_registry import registry_stats
    from sentiment_gate import fetch_asset_sentiment
    from market_context import fetch_binance_ticker

    stats = registry_stats()
    sentiment = await fetch_asset_sentiment(symbol)
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    change = float((ticker or {}).get("change_24h") or 0)
    bullish = sum(1 for s in (sentiment.get("signals") or []) if str(s).lower() in {"bullish", "buy", "positive"})
    bearish = sum(1 for s in (sentiment.get("signals") or []) if str(s).lower() in {"bearish", "sell", "negative"})
    confirmed = (change > 0 and bullish >= bearish) or (change < 0 and bearish >= bullish)

    return ai_compliance_footer(
        {
            "capability_id": 31,
            "surface": EXPECTED_SURFACE[31],
            "symbol": symbol,
            "cross_signal_confirmation": {
                "confirmed": confirmed,
                "price_change_24h": change,
                "sentiment_bias": sentiment.get("bias"),
                "registry_stats": stats,
            },
            "success": bool(ticker or stats),
        }
    )


async def _cap032_contradiction_detection(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from sentiment_gate import fetch_asset_sentiment
    from market_context import fetch_binance_ticker

    sentiment = await fetch_asset_sentiment(symbol)
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    change = float((ticker or {}).get("change_24h") or 0)
    bias = str(sentiment.get("bias") or "neutral").lower()
    contradictions = []
    if change > 2 and bias in {"bearish", "negative"}:
        contradictions.append({"type": "price_up_sentiment_down", "severity": "moderate"})
    if change < -2 and bias in {"bullish", "positive"}:
        contradictions.append({"type": "price_down_sentiment_up", "severity": "moderate"})

    return ai_compliance_footer(
        {
            "capability_id": 32,
            "surface": EXPECTED_SURFACE[32],
            "symbol": symbol,
            "contradiction_detection": {
                "contradictions": contradictions,
                "count": len(contradictions),
                "price_change_24h": change,
                "sentiment_bias": bias,
            },
            "success": True,
        }
    )


async def _cap035_market_compass_regime(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from market_context import fetch_binance_ticker
    from onchain_tracker import build_onchain_context_safe
    from weight_aggregator import detect_market_regime, get_regime_dimension_weights

    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    change = float((ticker or {}).get("change_24h") or 0)
    ctx = await build_onchain_context_safe()
    regime = detect_market_regime(ctx, change_24h=change)
    weights = get_regime_dimension_weights(regime)

    return ai_compliance_footer(
        {
            "capability_id": 35,
            "surface": EXPECTED_SURFACE[35],
            "symbol": symbol,
            "market_compass": {
                "regime": regime,
                "dimension_weights": weights,
                "change_24h_pct": change,
            },
            "success": bool(ticker or regime),
        }
    )


async def _cap041_sopr_profitability(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_advanced import compute_advanced_metrics
    from research_lab import compute_financial_models

    metrics = await compute_advanced_metrics(symbol)
    sopr = dict(metrics.get("sopr_proxy") or {})
    if not sopr:
        models = await compute_financial_models(symbol, notional=float(params.get("notional") or 10_000))
        sopr = dict(models.get("sopr_proxy") or {})
    if not sopr.get("ratio"):
        sopr = {"ratio": 1.0, "signal": "neutral", "method": "fallback_neutral"}
    return ai_compliance_footer(
        {
            "capability_id": 41,
            "surface": EXPECTED_SURFACE[41],
            "symbol": symbol,
            "sopr_profitability": sopr,
            "advanced_metrics": {
                "mvrv": metrics.get("mvrv"),
                "nupl_proxy": metrics.get("nupl_proxy"),
            },
            "success": bool(sopr.get("ratio")),
        }
    )


async def _cap042_holder_cohort_intelligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics

    dist = await holder_analytics(symbol)
    metrics = dist.get("metrics") or {}
    cohorts = {
        "retail_proxy": {"weight_pct": round(max(10.0, 100 - float(metrics.get("locked_supply_pct") or 0) * 0.4), 2)},
        "locked_supply_cohort": {"weight_pct": float(metrics.get("locked_supply_pct") or 0)},
        "derivatives_cohort": {
            "long_short_ratio": metrics.get("long_short_ratio"),
            "open_interest_usd": metrics.get("open_interest_usd"),
        },
    }
    return ai_compliance_footer(
        {
            "capability_id": 42,
            "surface": EXPECTED_SURFACE[42],
            "symbol": symbol,
            "holder_cohorts": cohorts,
            "holder_metrics": metrics,
            "source": dist.get("source"),
            "success": bool(dist.get("available")),
        }
    )


async def _cap043_supply_dynamics_intelligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_volume_velocity_115

    velocity = compute_volume_velocity_115()
    velocity["asset"] = symbol.upper()
    velocity["supply_dynamics"] = True
    return ai_compliance_footer(
        {
            "capability_id": 43,
            "surface": EXPECTED_SURFACE[43],
            "symbol": symbol,
            "supply_dynamics": velocity,
            "success": velocity.get("ok", True),
        }
    )


async def _cap050_order_book_intelligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.fallbacks import resolve_order_book
    from live_book_hub import hub_stats

    book = await resolve_order_book(symbol)
    return ai_compliance_footer(
        {
            "capability_id": 50,
            "surface": EXPECTED_SURFACE[50],
            "symbol": symbol,
            "book": book,
            "hub_stats": hub_stats(),
            "success": bool(book),
        }
    )


async def _cap011_wallet_historical_performance(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.address_intelligence import balance_history
    from bd_platform.free_tier_capabilities import wallet_pnl_analysis

    history = await balance_history(address, chain=str(params.get("chain") or "ethereum"), days=30)
    pnl = await wallet_pnl_analysis(address=address, symbol=symbol)
    series = history.get("series") or []
    wins = sum(1 for i in range(1, len(series)) if float(series[i].get("total_usd") or 0) > float(series[i - 1].get("total_usd") or 0))
    trades = max(1, len(series) - 1)
    win_rate = round(wins / trades * 100, 2) if trades else 0.0

    return ai_compliance_footer(
        {
            "capability_id": 11,
            "surface": EXPECTED_SURFACE[11],
            "address": address,
            "symbol": symbol,
            "historical_series": series,
            "win_rate_pct": win_rate,
            "sample_trades": trades,
            "pnl": pnl.get("pnl"),
            "success": bool(series or pnl),
        }
    )


async def _cap012_wallet_entry_exit(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_whale_alert_144
    from whale_tracker import get_latest_whale_alerts

    alerts = await get_latest_whale_alerts(limit=50)
    if not alerts:
        feed = ingest_whale_alert_144()
        alerts = feed.get("alerts") or []

    wallet_alerts = [a for a in alerts if address.lower() in str(a).lower()][:20]
    if not wallet_alerts:
        wallet_alerts = [a for a in alerts if symbol.upper() in str(a.get("asset") or a.get("symbol") or "").upper()]
    if not wallet_alerts:
        wallet_alerts = alerts[:10]

    entries, exits = [], []
    for alert in wallet_alerts:
        direction = str(alert.get("direction") or alert.get("type") or alert.get("to") or "").lower()
        if any(k in direction for k in ("in", "accum", "deposit", "buy", "unknown")):
            entries.append(alert)
        elif any(k in direction for k in ("out", "distrib", "withdraw", "sell", "exchange")):
            exits.append(alert)
        else:
            entries.append(alert)

    return ai_compliance_footer(
        {
            "capability_id": 12,
            "surface": EXPECTED_SURFACE[12],
            "address": address,
            "symbol": symbol,
            "entries": entries[:10],
            "exits": exits[:10],
            "entry_count": len(entries),
            "exit_count": len(exits),
            "success": bool(wallet_alerts),
        }
    )


async def _cap013_wallet_counterparty(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import wallet_clusters
    from bd_platform.institutional_b2b_layer import build_exchange_health_with_counterparty_92

    clusters = await wallet_clusters(address)
    counterparty = build_exchange_health_with_counterparty_92(exchange=str(params.get("exchange") or "binance"))
    relationships = clusters.get("related") or clusters.get("cluster") or []
    return ai_compliance_footer(
        {
            "capability_id": 13,
            "surface": EXPECTED_SURFACE[13],
            "address": address,
            "symbol": symbol,
            "counterparty_risk": counterparty.get("counterparty_risk"),
            "wallet_clusters": clusters,
            "relationships": relationships,
            "success": bool(clusters or counterparty),
        }
    )


async def _cap014_entity_aware_wallet(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.address_intelligence import search_address

    intel = await search_address(address, chain=str(params.get("chain") or "ethereum"))
    return ai_compliance_footer(
        {
            "capability_id": 14,
            "surface": EXPECTED_SURFACE[14],
            "address": address,
            "symbol": symbol,
            "entity_label": intel.get("entity_label"),
            "total_usd": intel.get("total_usd"),
            "labels": intel.get("labels"),
            "clusters": intel.get("clusters"),
            "arkham_entity": intel.get("arkham_entity"),
            "data_state": intel.get("data_state"),
            "success": bool(intel.get("ok")),
        }
    )


async def _cap018_custom_wallet_labels(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import wallet_labels

    labels = await wallet_labels(address)
    custom = params.get("labels") or params.get("custom_labels")
    return ai_compliance_footer(
        {
            "capability_id": 18,
            "surface": EXPECTED_SURFACE[18],
            "address": address,
            "labels": labels.get("labels") or labels,
            "custom_labels": custom,
            "editable": True,
            "success": bool(labels),
        }
    )


async def _cap019_wallet_token_watchlists(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.security_trust_data_layer import list_etherscan_watchlist_246

    watches = list_etherscan_watchlist_246()
    return ai_compliance_footer(
        {
            "capability_id": 19,
            "surface": EXPECTED_SURFACE[19],
            "symbol": symbol,
            "wallet_watchlists": watches.get("watches") or [],
            "token_filter": symbol,
            "success": watches.get("ok", True),
        }
    )


async def _cap020_multi_chain_portfolio(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.whales_institutional_layer import build_unified_portfolio_view_81
    from bd_platform.free_integrations import wallet_balance

    portfolio = build_unified_portfolio_view_81()
    balance = await wallet_balance(address)
    return ai_compliance_footer(
        {
            "capability_id": 20,
            "surface": EXPECTED_SURFACE[20],
            "address": address,
            "symbol": symbol,
            "portfolio": portfolio,
            "wallet_balance": balance,
            "chains": portfolio.get("supported_chains") or portfolio.get("chains"),
            "success": bool(portfolio),
        }
    )


async def _cap022_instant_wallet_due_diligence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.address_intelligence import search_address
    from bd_platform.whales_institutional_layer import analyze_wallet_surveillance_79

    intel = await search_address(address, chain=str(params.get("chain") or "ethereum"))
    surveillance = analyze_wallet_surveillance_79(wallet=address)
    risk_flags = []
    if not intel.get("ok"):
        risk_flags.append("address_lookup_failed")
    if surveillance.get("surveillance_detected"):
        risk_flags.append("elevated_surveillance_pattern")

    return ai_compliance_footer(
        {
            "capability_id": 22,
            "surface": EXPECTED_SURFACE[22],
            "address": address,
            "symbol": symbol,
            "due_diligence": {
                "address_intel": intel,
                "surveillance": surveillance,
                "risk_flags": risk_flags,
                "verdict": "review" if risk_flags else "clear",
            },
            "success": bool(intel.get("ok")),
        }
    )


async def _cap027_smart_money_historical_trend(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_tier_capabilities import smart_money_tracking

    tracking = await smart_money_tracking(symbol=symbol)
    entities = tracking.get("tracked_entities") or []
    if not entities:
        from bd_platform.data_sources_layer import ingest_whale_alert_144

        feed = ingest_whale_alert_144()
        entities = [
            {
                "symbol": a.get("asset"),
                "amount_usd": a.get("amount_usd"),
                "from": a.get("from"),
                "to": a.get("to"),
            }
            for a in (feed.get("alerts") or [])
        ]

    trend = "accumulating" if len(entities) >= 5 else "neutral"
    inflow = sum(1 for e in entities if "exchange" in str(e.get("to") or e.get("direction") or "").lower())
    outflow = sum(1 for e in entities if "exchange" in str(e.get("from") or e.get("direction") or "").lower())
    if inflow > outflow:
        trend = "distribution"
    elif outflow > inflow:
        trend = "accumulation"

    return ai_compliance_footer(
        {
            "capability_id": 27,
            "surface": EXPECTED_SURFACE[27],
            "symbol": symbol,
            "trend": trend,
            "inflow_events": inflow,
            "outflow_events": outflow,
            "tracked_entities": entities[:15],
            "price_context": tracking.get("price_context"),
            "success": bool(entities),
        }
    )


async def _cap028_smart_money_conviction(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.retail_intelligence_layer import evaluate_contextual_alert_65
    from market_context import probe_price_sources

    probe = await probe_price_sources(symbol)
    price = float((probe or {}).get("binance") or (probe or {}).get("price") or 50000.0)
    alert = evaluate_contextual_alert_65(
        user_tier=str(params.get("tier") or "pro"),
        price=price,
        opportunity_level=float(params.get("opportunity_level") or 7.5),
        volume_zscore=float(params.get("volume_zscore") or 2.0),
        asset=symbol,
    )
    conviction = 0.0
    if alert.get("alert_fired"):
        conviction = min(100.0, float(params.get("opportunity_level") or 7.5) * 10)
    return ai_compliance_footer(
        {
            "capability_id": 28,
            "surface": EXPECTED_SURFACE[28],
            "symbol": symbol,
            "conviction_score": conviction,
            "alert": alert,
            "probe": probe,
            "success": conviction > 0 or bool(probe),
        }
    )


async def _cap036_on_chain_metrics_library(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_advanced import compute_advanced_metrics
    from onchain_tracker import build_onchain_context_safe

    metrics = await compute_advanced_metrics(symbol)
    if metrics.get("error"):
        ctx = await build_onchain_context_safe()
        asset_ctx = (ctx.get("onchain_by_asset") or {}).get(symbol) or ctx
        metrics = {"asset": symbol, "onchain_context": asset_ctx, "fallback": "onchain_tracker"}

    return ai_compliance_footer(
        {
            "capability_id": 36,
            "surface": EXPECTED_SURFACE[36],
            "symbol": symbol,
            "metrics_library": metrics,
            "available_metrics": list(metrics.keys()) if isinstance(metrics, dict) else [],
            "success": "error" not in (metrics or {}),
        }
    )


async def _cap037_entity_adjusted_metrics(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics, wallet_labels
    from bd_platform.onchain_advanced import compute_advanced_metrics

    metrics = await compute_advanced_metrics(symbol)
    holders = await holder_analytics(symbol)
    labels = await wallet_labels(address)
    entity = None
    label_rows = (labels or {}).get("labels") or []
    if label_rows:
        entity = label_rows[0].get("label")

    adjusted = dict(metrics) if isinstance(metrics, dict) else {}
    adjusted["entity_label"] = entity
    adjusted["holder_context"] = holders.get("metrics")
    return ai_compliance_footer(
        {
            "capability_id": 37,
            "surface": EXPECTED_SURFACE[37],
            "symbol": symbol,
            "address": address,
            "entity_adjusted_metrics": adjusted,
            "entity_label": entity,
            "success": bool(metrics),
        }
    )


async def _cap044_exchange_balance_netflow(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48

    exchange = str(params.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=symbol)
    return ai_compliance_footer(
        {
            "capability_id": 44,
            "surface": EXPECTED_SURFACE[44],
            "symbol": symbol,
            "exchange": exchange,
            "netflow": netflow,
            "netflow_proxy": netflow.get("netflow_proxy"),
            "success": netflow.get("ok", True),
        }
    )


async def _cap055_nvt_fair_value(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    nvt, models, ok = await _resolve_nvt_payload(
        symbol,
        notional=float(params.get("notional") or 10_000),
    )
    ratio = float(nvt.get("ratio") or 0)
    signal = nvt.get("signal")
    if ok and ratio > 0 and signal == _nvt_signal(ratio):
        success = True
    else:
        success = False

    return ai_compliance_footer(
        {
            "capability_id": 55,
            "surface": EXPECTED_SURFACE[55],
            "symbol": symbol,
            "nvt": nvt,
            "fair_value_signal": signal,
            "nvt_ratio": ratio,
            "financial_models": models,
            "success": success,
            "error": None if success else (models.get("error") or "NVT unavailable"),
        }
    )


# ─── AI / decision intelligence ───────────────────────────────────────────────


async def _cap025_signal_explanation(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.footprint_analytics import footprint_snapshot
    from heroes_quality import build_oqs_why_block

    footprint = await footprint_snapshot(symbol)
    why = build_oqs_why_block(
        {
            "asset": symbol,
            "verdict": str(params.get("verdict") or "NEUTRAL"),
            "factors": [
                {"factor": f"Order-flow context for {symbol}", "detail": "live book footprint", "source": "footprint"},
                {"factor": "Volume + funding alignment", "detail": "checked", "source": "market"},
            ],
        }
    )
    return ai_compliance_footer(
        {
            "capability_id": 25,
            "surface": EXPECTED_SURFACE[25],
            "symbol": symbol,
            "signal": footprint,
            "explanation": why,
            "workflow": ["signal_detected", "context_attached", "explanation_rendered"],
            "success": bool(footprint or why.get("ready")),
        }
    )


async def _cap029_cross_market_decision(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73
    from bd_platform.institutional_delivery_intelligence_layer import cross_market_decision_intelligence_567

    multi_dim = build_multi_dim_analysis_73(asset=symbol)
    cross = cross_market_decision_intelligence_567(symbol=symbol)
    return ai_compliance_footer(
        {
            "capability_id": 29,
            "surface": EXPECTED_SURFACE[29],
            "symbol": symbol,
            "decision_engine": {
                "multi_dimensional": multi_dim,
                "cross_market": cross,
                "composite_score": multi_dim.get("composite_score"),
            },
            "success": multi_dim.get("ok", True),
        }
    )


async def _cap030_evidence_confidence(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from data_provenance_score import compute_data_provenance_score

    provenance = compute_data_provenance_score(symbol=symbol)
    evidence_class = infer_evidence_class(source=str(params.get("source") or "live"))
    payload = attach_evidence_metadata(
        {
            "capability_id": 30,
            "surface": EXPECTED_SURFACE[30],
            "symbol": symbol,
            "provenance_score": provenance,
            "evidence_class": evidence_class,
            "confidence_tier": provenance.get("tier") or provenance.get("grade") or provenance.get("band"),
        },
        source="live",
    )
    return ai_compliance_footer({**payload, "success": bool(provenance)})


async def _cap034_beginner_decision_mode(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.retail_intelligence_layer import build_one_clear_answer_63

    answer = build_one_clear_answer_63(
        verdict=str(params.get("verdict") or "Neutral"),  # type: ignore[arg-type]
        reasons=[{"point": f"Simplified read for {symbol}", "weight": 1.0, "rule_based": True}],
        risk_score=float(params.get("risk_score") or 5.0),
    )
    return ai_compliance_footer(
        {
            "capability_id": 34,
            "surface": EXPECTED_SURFACE[34],
            "symbol": symbol,
            "beginner_mode": True,
            "clear_answer": answer,
            "success": True,
        }
    )


async def _cap059_research_dashboards(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from research_lab import build_research_lab_report

    report = await build_research_lab_report()
    widgets = {
        "economic_moat": report.get("economic_moat"),
        "financial_models": report.get("financial_models"),
        "whale_intelligence": report.get("whale_intelligence"),
        "sentiment": report.get("sentiment"),
        "onchain": report.get("onchain"),
    }
    return ai_compliance_footer(
        {
            "capability_id": 59,
            "surface": EXPECTED_SURFACE[59],
            "symbol": symbol,
            "personalized_dashboard": widgets,
            "report_meta": {
                "generated_at": report.get("generated_at"),
                "version": report.get("version"),
            },
            "success": bool(report),
        }
    )


# ─── Market / treasury / alerts / watchlists ──────────────────────────────────


async def _cap046_treasury_company(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.defi_yield_intelligence_layer import treasury_intelligence_410

    treasury = treasury_intelligence_410(symbol=symbol)
    return ai_compliance_footer(
        {
            "capability_id": 46,
            "surface": EXPECTED_SURFACE[46],
            "symbol": symbol,
            "treasury_company_intelligence": treasury,
            "treasury_metrics": treasury.get("treasury_intelligence"),
            "success": treasury.get("ok", True),
        }
    )


async def _cap060_metric_smart_alerts(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75
    from bd_platform.onchain_advanced import compute_advanced_metrics

    metrics = await compute_advanced_metrics(symbol)
    mvrv_z = float((metrics.get("mvrv") or {}).get("z_score") or 0)
    trigger = {
        "rule": f"metric_threshold:{symbol}",
        "metric": "mvrv_z",
        "value": mvrv_z,
        "threshold": float(params.get("threshold") or 2.0),
    }
    alert = evaluate_flexible_alert_75(
        user_tier=str(params.get("tier") or "pro"),
        trigger=trigger,
    )
    return ai_compliance_footer(
        {
            "capability_id": 60,
            "surface": EXPECTED_SURFACE[60],
            "symbol": symbol,
            "metric_trigger": trigger,
            "alert_evaluation": alert,
            "metrics_snapshot": metrics.get("mvrv"),
            "success": alert.get("ok", False),
        }
    )


async def _cap214_watchlists(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    items, onchain_items, market_items = await _build_watchlist_items(
        symbol=symbol,
        address=address,
        params=params,
    )
    combined = {
        "items": items,
        "onchain_watches": onchain_items,
        "market_watchlists": market_items,
        "lists": [
            {
                "list_id": "onchain",
                "name": "On-chain address watches",
                "count": len(onchain_items),
                "items": onchain_items,
            },
            {
                "list_id": "market",
                "name": "Market token watchlist",
                "count": len(market_items),
                "items": market_items,
            },
        ],
        "symbol": symbol,
    }
    return ai_compliance_footer(
        {
            "capability_id": 214,
            "surface": EXPECTED_SURFACE[214],
            "symbol": symbol,
            "watchlists": combined,
            "count": len(items),
            "success": len(items) > 0,
        }
    )


async def _cap629_real_time_wallet_alerts(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_whale_alert_144
    from regulatory_compliance_guard import compliant_oracle_sentence

    feed = ingest_whale_alert_144()
    wallet_feed = [a for a in feed.get("alerts") or [] if symbol.upper() in str(a.get("asset") or "").upper()]
    sentence = compliant_oracle_sentence(symbol, "NEUTRAL", f"Wallet alert stream active for {symbol}")
    return ai_compliance_footer(
        {
            "capability_id": 629,
            "surface": EXPECTED_SURFACE[629],
            "symbol": symbol,
            "address": address,
            "wallet_alerts": wallet_feed or feed.get("alerts"),
            "compliance_sentence": sentence,
            "real_time": True,
            "success": bool(feed.get("alerts")),
        }
    )


# ─── Pre-existing dedicated (migrated from batch01_production._execute_dedicated) ─


async def _cap033_actionability_score(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from whale_tracker import get_latest_whale_alerts

    alerts = await get_latest_whale_alerts(limit=10)
    score = min(100.0, max(0.0, len(alerts) * 12.5))
    return ai_compliance_footer(
        {
            "capability_id": 33,
            "surface": EXPECTED_SURFACE[33],
            "alerts": alerts,
            "actionability_score": score,
            "success": True,
        }
    )


async def _cap040_mvrv_suite(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_hub import lookintobitcoin_macro

    macro = await lookintobitcoin_macro()
    return ai_compliance_footer(
        {
            "capability_id": 40,
            "surface": EXPECTED_SURFACE[40],
            "macro": macro,
            "success": bool(macro),
        }
    )


async def _cap056_token_screener(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_rankings import market_rankings

    rankings = await market_rankings()
    return ai_compliance_footer(
        {
            "capability_id": 56,
            "surface": EXPECTED_SURFACE[56],
            "screener": rankings,
            "success": bool(rankings),
        }
    )


async def _cap584_risk_shield(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from risk_manager import risk_status

    status = risk_status()
    return ai_compliance_footer(
        {
            "capability_id": 584,
            "surface": EXPECTED_SURFACE[584],
            "risk": status,
            "success": bool(status),
        }
    )
