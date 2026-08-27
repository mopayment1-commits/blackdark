"""
Decision Engine inputs (#48) — aggregates silent Data Layer metrics.

Feeds risk scoring from exchange flows (#97), netflow (#54), CVD (#59),
order flow (#85), macro (#86), Polygon on-chain (#87), Gate.io (#60), KuCoin (#69),
MarketWatch (#75), research (#95), news (#68), Solana RPC (#93), and flat archive (#66).
No standalone user surface.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def gather_decision_inputs(symbol: str = "ETH") -> dict[str, Any]:
    """Collect internal metrics that adjust decision/risk scores."""
    from blackdark.ingestion.exchange_flow_metric import compute_token_exchange_flows
    from blackdark.ingestion.exchange_netflow_intelligence import compute_exchange_netflow
    from blackdark.ingestion.futures_cvd_metric import compute_futures_cvd
    from blackdark.ingestion.historical_flat_archive import backtest_coverage_years
    from blackdark.ingestion.investing_com_connector import fetch_investing_news_context
    from blackdark.ingestion.lending_markets_connector import fetch_lending_markets
    from blackdark.ingestion.gateio_connector import fetch_gateio_listing_intelligence
    from blackdark.ingestion.kucoin_connector import fetch_kucoin_listing_intelligence
    from blackdark.ingestion.marketwatch_connector import fetch_marketwatch_macro_context
    from blackdark.ingestion.order_flow_intelligence import compute_order_flow_intelligence
    from blackdark.ingestion.polygon_io_connector import fetch_polygon_macro_context
    from blackdark.ingestion.polygonscan_connector import fetch_polygon_onchain_health
    from blackdark.ingestion.twelvedata_connector import fetch_twelvedata_macro_context
    from blackdark.ingestion.solana_rpc_connector import fetch_solana_chain_health
    from blackdark.ingestion.theblock_connector import fetch_theblock_research_context
    from bd_platform.execution_optimizer import execution_cost_for_decision_engine
    from bd_platform.flash_crash_protection import flash_protection_for_decision_engine
    from bd_platform.mvrv_realignment import mvrv_cycle_context_for_decision_engine
    from bd_platform.market_microstructure import microstructure_for_decision_engine
    from bd_platform.network_growth_intelligence import network_growth_for_decision_engine
    from bd_platform.options_intelligence import options_intelligence_for_decision_engine
    from bd_platform.puell_multiple import puell_for_decision_engine
    from blackdark.ingestion.okx_connector import okx_for_decision_engine

    t0 = time.perf_counter()
    sym = symbol.upper()
    mvrv_asset = "BTC" if sym not in {"BTC", "ETH"} else sym
    growth_asset = sym if sym in {"BTC", "ETH", "SOL", "BNB", "MATIC", "AVAX", "TRX"} else "SOL"
    options_asset = sym if sym in {"BTC", "ETH"} else "BTC"
    flows, netflow, cvd, order_flow, macro, twelvedata, polygon, gateio, kucoin, marketwatch, research, news, solana, archive, lending, execution_cost, flash_protection, mvrv_cycle, microstructure, network_growth, okx_market, options_intel, puell = await _gather(
        compute_token_exchange_flows(sym),
        compute_exchange_netflow(sym),
        compute_futures_cvd(sym),
        compute_order_flow_intelligence(sym),
        fetch_polygon_macro_context(),
        fetch_twelvedata_macro_context(),
        fetch_polygon_onchain_health(),
        fetch_gateio_listing_intelligence(),
        fetch_kucoin_listing_intelligence(),
        fetch_marketwatch_macro_context(),
        fetch_theblock_research_context(limit=8),
        fetch_investing_news_context(limit=50),
        fetch_solana_chain_health(),
        _async_archive(sym),
        fetch_lending_markets(limit=25),
        execution_cost_for_decision_engine(sym),
        flash_protection_for_decision_engine(sym),
        mvrv_cycle_context_for_decision_engine(mvrv_asset),
        microstructure_for_decision_engine(sym),
        network_growth_for_decision_engine(growth_asset),
        okx_for_decision_engine(sym),
        options_intelligence_for_decision_engine(options_asset),
        puell_for_decision_engine("BTC"),
    )

    risk_delta = float(flows.get("risk_score_delta") or 0)
    if netflow.get("risk_score_delta") is not None:
        risk_delta = max(risk_delta, float(netflow.get("risk_score_delta") or 0))
    if execution_cost.get("confidence_penalty"):
        risk_delta = round(risk_delta + float(execution_cost["confidence_penalty"]), 2)
    if flash_protection.get("pause_signals"):
        risk_delta = round(risk_delta + 1.5, 2)
    if mvrv_cycle.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(mvrv_cycle["risk_score_delta"]), 2)
    if microstructure.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(microstructure["risk_score_delta"]), 2)
    if network_growth.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(network_growth["risk_score_delta"]), 2)
    if okx_market.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(okx_market["risk_score_delta"]), 2)
    if options_intel.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(options_intel["risk_score_delta"]), 2)
    if puell.get("risk_score_delta"):
        risk_delta = round(risk_delta + float(puell["risk_score_delta"]), 2)

    headlines: list[str] = []
    for row in (flows, netflow, cvd, order_flow, macro, twelvedata, polygon, gateio, kucoin, marketwatch, research, news, execution_cost, flash_protection, mvrv_cycle, microstructure, network_growth, okx_market, options_intel, puell):
        if isinstance(row, dict) and row.get("headline"):
            headlines.append(str(row["headline"]))
        elif isinstance(row, dict) and row.get("ai_context_line"):
            headlines.append(str(row["ai_context_line"]))

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "surface": "decision_engine_inputs",
        "feature": "#48",
        "symbol": sym,
        "exchange_flows": flows,
        "exchange_netflow": netflow,
        "futures_cvd": cvd,
        "order_flow_intelligence": order_flow,
        "macro_context": macro if macro.get("ok") else None,
        "twelvedata_macro": twelvedata if twelvedata.get("ok") else None,
        "polygon_onchain": polygon if polygon.get("ok") else None,
        "gateio_listings": gateio if gateio.get("ok") else None,
        "kucoin_listings": kucoin if kucoin.get("ok") else None,
        "marketwatch_macro": marketwatch if marketwatch.get("ok") else None,
        "research_context": research if research.get("ok") else None,
        "news_context": news if news.get("ok") else None,
        "solana_onchain": solana if solana.get("ok") else None,
        "backtest_archive": archive,
        "lending_markets": lending if lending.get("ok") else None,
        "execution_optimizer": execution_cost if execution_cost.get("ok") else None,
        "flash_crash_protection": flash_protection if flash_protection.get("ok") else None,
        "mvrv_cycle": mvrv_cycle if mvrv_cycle.get("ok") else None,
        "market_microstructure": microstructure if microstructure.get("ok") else None,
        "network_growth": network_growth if network_growth.get("ok") else None,
        "okx_market": okx_market if okx_market.get("ok") else None,
        "options_intelligence": options_intel if options_intel.get("ok") else None,
        "puell_multiple": puell if puell.get("ok") else None,
        "risk_score_delta": round(risk_delta, 2),
        "headlines": headlines[:5],
        "internal_only": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def _async_archive(sym: str) -> dict[str, Any]:
    from blackdark.ingestion.historical_flat_archive import backtest_coverage_years

    return backtest_coverage_years(symbol=sym)


async def _gather(*coros):
    import asyncio

    results = await asyncio.gather(*coros, return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, BaseException):
            out.append({"ok": False, "error": str(r)})
        else:
            out.append(r if isinstance(r, dict) else {})
    return out
