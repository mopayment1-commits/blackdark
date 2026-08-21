"""Execution & risk capabilities."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def handle_execution_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or "BTC").upper().replace("/USDT", "")

    if capability_id == 584:
        from risk_manager import evaluate_execution_risk, risk_status

        verdict = evaluate_execution_risk(
            {
                "symbol": f"{symbol}/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "expected_edge_bps": float(params.get("expected_edge_bps") or 12.0),
            }
        )
        return ai_compliance_footer(
            {
                "capability_id": 584,
                "surface": "risk_management_shield",
                "verdict": verdict.__dict__,
                "status": risk_status(),
                "success": verdict.allowed,
            }
        )

    if capability_id in {610, 612}:
        from arbitrage_service import scan_arbitrage_opportunities

        scan = await scan_arbitrage_opportunities(asset=symbol, limit=5)
        return ai_compliance_footer(
            {
                "capability_id": capability_id,
                "surface": "funding_arbitrage" if capability_id == 610 else "spread_calculation",
                "scan": scan,
                "success": bool(scan),
            }
        )

    if capability_id == 639:
        from cap646.handlers.verified import handle_verified_capability

        return await handle_verified_capability(639, params=params)

    from fee_matrix import taker_fee

    return ai_compliance_footer(
        {"capability_id": capability_id, "surface": "execution_trading", "fee_sample": taker_fee("binance"), "success": True}
    )
