"""
Decision Engine inputs (#48) — aggregates silent Data Layer metrics.

Feeds risk scoring from exchange flows (#97), netflow (#54), CVD (#59),
research (#95), news (#68), Solana RPC (#93), and flat archive (#66).
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
    from blackdark.ingestion.solana_rpc_connector import fetch_solana_chain_health
    from blackdark.ingestion.theblock_connector import fetch_theblock_research_context

    t0 = time.perf_counter()
    sym = symbol.upper()
    flows, netflow, cvd, research, news, solana, archive, lending = await _gather(
        compute_token_exchange_flows(sym),
        compute_exchange_netflow(sym),
        compute_futures_cvd(sym),
        fetch_theblock_research_context(limit=8),
        fetch_investing_news_context(limit=50),
        fetch_solana_chain_health(),
        _async_archive(sym),
        fetch_lending_markets(limit=25),
    )

    risk_delta = float(flows.get("risk_score_delta") or 0)
    if netflow.get("risk_score_delta") is not None:
        risk_delta = max(risk_delta, float(netflow.get("risk_score_delta") or 0))

    headlines: list[str] = []
    for row in (flows, netflow, cvd, research, news):
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
        "research_context": research if research.get("ok") else None,
        "news_context": news if news.get("ok") else None,
        "solana_onchain": solana if solana.get("ok") else None,
        "backtest_archive": archive,
        "lending_markets": lending if lending.get("ok") else None,
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
