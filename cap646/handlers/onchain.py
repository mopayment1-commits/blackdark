"""On-chain capabilities (non-EXTERNAL)."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def handle_onchain_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id == 5:
        from whale_signal_classifier import enrich_whale_narratives

        data = await enrich_whale_narratives(limit=5)
        return ai_compliance_footer({"capability_id": 5, "surface": "smart_money_accumulation_detection", "data": data, "success": True})

    if capability_id == 279:
        from onchain_tracker import build_onchain_context_safe

        ctx = await build_onchain_context_safe()
        return ai_compliance_footer({"capability_id": 279, "surface": "transaction_search", "context": ctx, "success": bool(ctx)})

    if capability_id == 354:
        from bd_platform.onchain_hub import intotheblock_metrics

        data = await intotheblock_metrics(symbol)
        return ai_compliance_footer({"capability_id": 354, "surface": "tvl_intelligence", "data": data, "success": bool(data)})

    if capability_id == 615:
        from gas_oracle import get_swap_gas_usd

        gas = await get_swap_gas_usd("ethereum")
        return ai_compliance_footer({"capability_id": 615, "surface": "gas_cost_predictor", "gas_usd": gas, "success": gas is not None})

    if capability_id == 581:
        from bd_platform.onchain_hub import debank_wallet

        addr = str(params.get("address") or "")
        bal = await debank_wallet(addr) if addr else {"note": "address_required"}
        return ai_compliance_footer({"capability_id": 581, "surface": "on_chain_balance_monitor", "balance": bal, "success": bool(bal)})

    from onchain_tracker import build_onchain_context_safe

    ctx = await build_onchain_context_safe()
    return ai_compliance_footer({"capability_id": capability_id, "surface": "onchain_intelligence", "context": ctx, "success": bool(ctx)})
