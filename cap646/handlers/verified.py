"""VERIFIED canonical capabilities — extend, never rebuild."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer
from data_provenance_score import compute_data_provenance_score
from hot_storage import get_hot_storage_stats


async def handle_verified_capability(
    capability_id: int,
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id == 49:
        from bd_platform.options_intelligence import analyze_options_intelligence

        data = await analyze_options_intelligence(symbol)
        return ai_compliance_footer(
            {
                "capability_id": 49,
                "surface": "options_intelligence_suite",
                "data": data,
                "success": bool(data.get("ok")),
            }
        )

    if capability_id == 50:
        from cap646.fallbacks import resolve_order_book
        from live_book_hub import hub_stats

        book = await resolve_order_book(symbol)
        return ai_compliance_footer(
            {"capability_id": 50, "surface": "order_book_intelligence", "book": book, "hub_stats": hub_stats(), "success": bool(book)}
        )

    if capability_id == 62:
        from ml.market_replay_bootstrap import bootstrap_market_replay_dataset

        boot = await bootstrap_market_replay_dataset(assets=[symbol], min_samples=1)
        return ai_compliance_footer({"capability_id": 62, "surface": "institutional_backtesting_data_layer", "bootstrap": boot, "success": True})

    if capability_id == 63:
        prov = compute_data_provenance_score(symbol=symbol)
        hot = get_hot_storage_stats()
        return ai_compliance_footer(
            {
                "capability_id": 63,
                "surface": "data_quality_provenance_layer",
                "provenance": prov,
                "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else str(hot),
                "success": True,
            }
        )

    if capability_id == 632:
        from data_lake import lake_status

        lake = await lake_status()
        hot = get_hot_storage_stats()
        return ai_compliance_footer(
            {"capability_id": 632, "surface": "multi_tier_data_storage", "lake": lake, "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else str(hot), "success": True}
        )

    if capability_id == 638:
        from oracle_track_record import public_track_record

        record = public_track_record()
        return ai_compliance_footer({"capability_id": 638, "surface": "claims_prediction_verification", "ledger": record, "success": True})

    if capability_id == 639:
        from net_edge_truth import compute_net_edge_truth

        sample = compute_net_edge_truth(
            {
                "symbol": f"{symbol}/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "net_profit_usdt": 2.5,
                "quote_amount": 1000.0,
                "total_slippage_bps": 3,
                "withdrawal_fee_usdt": 0.05,
                "trading_fees_usdt": 0.2,
                "quote_age_ms": 120,
                "estimated_recipients": 2,
                "flywheel_net_after_crowd_usd": 2.1,
            }
        )
        return ai_compliance_footer({"capability_id": 639, "surface": "net_edge_truth_score", "sample": sample, "success": True})

    if capability_id == 640:
        from oracle_track_record import public_track_record

        ledger = public_track_record()
        return ai_compliance_footer({"capability_id": 640, "surface": "public_accuracy_ledger", "ledger": ledger, "success": True})

    if capability_id == 641:
        from decision_certificate import build_decision_certificate

        cert = build_decision_certificate(
            {
                "symbol": symbol,
                "prediction_id": params.get("prediction_id") or "cap646-demo",
                "decision_action": params.get("decision_action") or "WAIT",
                "decision_sentence": params.get("decision_sentence") or "Evidence-first posture.",
                "tier": params.get("tier") or "pro",
            }
        )
        return ai_compliance_footer({"capability_id": 641, "surface": "decision_certificate_dd_export", "certificate": cert, "success": True})

    return ai_compliance_footer({"capability_id": capability_id, "error": "verified_handler_missing", "success": False})
