#!/usr/bin/env python3
"""Patch BATCH05 acceptance rows for Wave 4 strangler IDs (229–231, 233–241)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"

WAVE4: dict[int, tuple[str, str, list[tuple[str, str, str]]]] = {
    229: (
        "build_cross_exchange_funding_arbitrage_scanner_229",
        "cross_exchange_funding_arbitrage_scanner",
        [
            ("cross_exchange_funding_arbitrage_scanner.source", "enum", "== intelligence_ux_extensions_layer.generate_reasoning_explanation_229"),
            ("cross_exchange_funding_arbitrage_scanner.latency_ms", "numeric", "< 500"),
        ],
    ),
    230: (
        "build_spot_perp_arbitrage_scanner_230",
        "spot_perp_arbitrage_scanner",
        [
            ("spot_perp_arbitrage_scanner.source", "enum", "== intelligence_ux_extensions_layer.analyze_cross_exchange_divergence_230"),
            ("spot_perp_arbitrage_scanner.latency_ms", "numeric", "< 500"),
        ],
    ),
    231: (
        "build_futures_basis_term_structure_231",
        "futures_basis_term_structure",
        [
            ("futures_basis_term_structure.source", "enum", "== intelligence_ux_extensions_layer.triangular_arbitrage_status_231"),
            ("futures_basis_term_structure.latency_ms", "numeric", "< 500"),
        ],
    ),
    233: (
        "build_liquidation_intelligence_233",
        "liquidation_intelligence",
        [
            ("liquidation_intelligence.source", "enum", "== intelligence_ux_extensions_layer.build_heatmap_component_233"),
            ("liquidation_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
    234: (
        "build_cvd_intelligence_234",
        "cvd_intelligence",
        [
            ("cvd_intelligence.source", "enum", "== intelligence_ux_extensions_layer.live_dashboard_status_234"),
            ("cvd_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
    235: (
        "build_long_short_ratio_intelligence_235",
        "long_short_ratio_intelligence",
        [
            ("long_short_ratio_intelligence.source", "enum", "== intelligence_ux_extensions_layer.whale_intelligence_status_235"),
            ("long_short_ratio_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
    236: (
        "build_dex_screener_236",
        "dex_screener",
        [
            ("dex_screener.source", "enum", "== intelligence_ux_extensions_layer.subscription_tiers_status_236"),
            ("dex_screener.latency_ms", "numeric", "< 500"),
        ],
    ),
    237: (
        "build_token_risk_scoring_237",
        "token_risk_scoring",
        [
            ("token_risk_scoring.source", "enum", "== intelligence_ux_extensions_layer.generate_market_summary_237"),
            ("token_risk_scoring.latency_ms", "numeric", "< 500"),
        ],
    ),
    238: (
        "build_pump_dump_detection_238",
        "pump_dump_detection",
        [
            ("pump_dump_detection.source", "enum", "== intelligence_ux_extensions_layer.scan_market_opportunities_238"),
            ("pump_dump_detection.latency_ms", "numeric", "< 500"),
        ],
    ),
    239: (
        "build_narrative_tracking_239",
        "narrative_tracking",
        [
            ("narrative_tracking.source", "enum", "== intelligence_ux_extensions_layer.live_ta_status_239"),
            ("narrative_tracking.latency_ms", "numeric", "< 500"),
        ],
    ),
    240: (
        "build_sector_rotation_intelligence_240",
        "sector_rotation_intelligence",
        [
            ("sector_rotation_intelligence.source", "enum", "== intelligence_ux_extensions_layer.compute_s2f_240"),
            ("sector_rotation_intelligence.latency_ms", "numeric", "< 2000"),
        ],
    ),
    241: (
        "build_sentiment_intelligence_241",
        "sentiment_intelligence",
        [
            ("sentiment_intelligence.source", "enum", "== intelligence_ux_extensions_layer.ingest_fred_macro_241"),
            ("sentiment_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
}


def main() -> None:
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    for row in doc["rows"]:
        cid = row["capability_id"]
        if cid not in WAVE4:
            continue
        fn, root, extra_rules = WAVE4[cid]
        row["binding_file"] = "cap646/batch05_strangler_spine.py"
        row["binding_function"] = fn
        row["miswire_remediation"] = "STRANGLER_IMPLEMENTED"
        base_rules = [
            {"field": "success", "type": "boolean", "condition": "== true"},
            {"field": "surface", "type": "enum", "condition": "== expected_surface"},
            {"field": f"{root}.ok", "type": "boolean", "condition": "== true"},
            {"field": f"{root}.feature_ref", "type": "numeric", "condition": f"== {cid}"},
        ]
        row["domain_rules"] = base_rules + [
            {"field": f, "type": t, "condition": c} for f, t, c in extra_rules
        ]
    ACCEPTANCE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Patched acceptance for Wave 4 IDs: {sorted(WAVE4)}")


if __name__ == "__main__":
    main()
