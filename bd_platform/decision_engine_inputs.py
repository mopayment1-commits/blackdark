"""
Decision Engine inputs (#48) — aggregates silent Data Layer metrics.

Feeds risk scoring from exchange flows (#97), research context (#95),
and Solana on-chain availability (#93). No standalone user surface.
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
    from blackdark.ingestion.solana_rpc_connector import fetch_solana_chain_health
    from blackdark.ingestion.theblock_connector import fetch_theblock_research_context

    t0 = time.perf_counter()
    sym = symbol.upper()
    flows, research, solana = await _gather(
        compute_token_exchange_flows(sym),
        fetch_theblock_research_context(limit=8),
        fetch_solana_chain_health(),
    )

    risk_delta = float(flows.get("risk_score_delta") or 0)
    headlines: list[str] = []
    if flows.get("headline"):
        headlines.append(str(flows["headline"]))
    if research.get("ai_context_line"):
        headlines.append(str(research["ai_context_line"]))

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "surface": "decision_engine_inputs",
        "feature": "#48",
        "symbol": sym,
        "exchange_flows": flows,
        "research_context": research if research.get("ok") else None,
        "solana_onchain": solana if solana.get("ok") else None,
        "risk_score_delta": risk_delta,
        "headlines": headlines,
        "internal_only": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


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
