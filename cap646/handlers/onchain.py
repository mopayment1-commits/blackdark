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
        from cap646.fallbacks import resolve_gas_usd

        gas_row = await resolve_gas_usd(str(params.get("chain") or "ethereum"))
        return ai_compliance_footer(
            {
                "capability_id": 615,
                "surface": "gas_cost_predictor",
                "gas_usd": gas_row.get("gas_usd"),
                "gas_source": gas_row.get("source"),
                "success": bool(gas_row.get("success")),
            }
        )

    if capability_id == 581:
        from bd_platform.onchain_hub import debank_wallet

        addr = str(params.get("address") or "")
        bal = await debank_wallet(addr) if addr else {"note": "address_required"}
        return ai_compliance_footer({"capability_id": 581, "surface": "on_chain_balance_monitor", "balance": bal, "success": bool(bal)})

    if capability_id == 36:
        from bd_platform.onchain_metrics_library import build_onchain_metrics_library_panel

        panel = build_onchain_metrics_library_panel(symbol)
        return ai_compliance_footer(
            {
                "capability_id": 36,
                "surface": "on_chain_metrics_library",
                "backend_module": "bd_platform.onchain_metrics_library",
                "backend_entrypoint": "build_onchain_metrics_library_panel",
                "metrics_library": panel,
                "success": bool(panel.get("ok")),
            }
        )

    if capability_id == 202:
        from bd_platform.onchain_metrics_library import build_supply_distribution_dashboard

        distribution = build_supply_distribution_dashboard(symbol)
        return ai_compliance_footer(
            {
                "capability_id": 202,
                "surface": "supply_distribution_intelligence",
                "backend_module": "bd_platform.onchain_metrics_library",
                "backend_entrypoint": "build_supply_distribution_dashboard",
                "merged_into": 577,
                "standalone_rejected": True,
                "supply_distribution": distribution,
                "success": bool(distribution.get("ok")),
            }
        )

    from onchain_tracker import build_onchain_context_safe
    from instant_alert_engine import engine_stats
    from cap646.catalog import catalog_by_id

    ctx = await build_onchain_context_safe()
    cap_name = catalog_by_id().get(capability_id, {}).get("capability", "")
    payload: dict[str, Any] = {
        "capability_id": capability_id,
        "surface": "onchain_intelligence",
        "context": ctx,
        "success": bool(ctx),
    }
    if "alert" in cap_name.lower():
        payload["engine"] = engine_stats()
        payload["alerts"] = payload["engine"]
    return ai_compliance_footer(payload)
