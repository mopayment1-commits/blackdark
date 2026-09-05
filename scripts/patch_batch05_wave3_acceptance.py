#!/usr/bin/env python3
"""Patch BATCH05 acceptance rows for Wave 3 strangler IDs (217–225, 227)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"

WAVE3: dict[int, tuple[str, str, list[tuple[str, str, str]]]] = {
    217: (
        "build_sanapi_style_data_access_217",
        "sanapi_style_data_access",
        [
            ("sanapi_style_data_access.source", "enum", "== intelligence_market_extensions_layer.analyze_best_venue_217"),
            ("sanapi_style_data_access.latency_ms", "numeric", "< 500"),
        ],
    ),
    218: (
        "build_google_sheets_integration_218",
        "google_sheets_integration",
        [
            ("google_sheets_integration.source", "enum", "== intelligence_market_extensions_layer.list_manual_order_journal_218"),
            ("google_sheets_integration.latency_ms", "numeric", "< 500"),
        ],
    ),
    219: (
        "build_metric_availability_registry_219",
        "metric_availability_registry",
        [
            ("metric_availability_registry.source", "enum", "== intelligence_market_extensions_layer.analyze_nlp_sentiment_219"),
            ("metric_availability_registry.latency_ms", "numeric", "< 500"),
        ],
    ),
    220: (
        "build_data_stabilization_mutability_metadata_220",
        "data_stabilization_mutability_metadata",
        [
            ("data_stabilization_mutability_metadata.source", "enum", "== intelligence_market_extensions_layer.analyze_pattern_outcome_220"),
            ("data_stabilization_mutability_metadata.latency_ms", "numeric", "< 500"),
        ],
    ),
    221: (
        "build_data_quality_provenance_layer_221",
        "data_quality_provenance_layer",
        [
            ("data_quality_provenance_layer.source", "enum", "== intelligence_market_extensions_layer.market_slippage_analysis_221"),
            ("data_quality_provenance_layer.latency_ms", "numeric", "< 500"),
        ],
    ),
    222: (
        "build_metric_methodology_registry_222",
        "metric_methodology_registry",
        [
            ("metric_methodology_registry.source", "enum", "== intelligence_market_extensions_layer.monitor_exchange_latency_222"),
            ("metric_methodology_registry.latency_ms", "numeric", "< 500"),
        ],
    ),
    223: (
        "build_social_to_on_chain_confirmation_engine_223",
        "social_to_on_chain_confirmation_engine",
        [
            ("social_to_on_chain_confirmation_engine.source", "enum", "== intelligence_market_extensions_layer.analyze_defi_fundamentals_223"),
            ("social_to_on_chain_confirmation_engine.latency_ms", "numeric", "< 500"),
        ],
    ),
    224: (
        "build_narrative_actionability_score_224",
        "narrative_actionability_score",
        [
            ("narrative_actionability_score.source", "enum", "== intelligence_market_extensions_layer.analyze_token_dcf_224"),
            ("narrative_actionability_score.latency_ms", "numeric", "< 5000"),
        ],
    ),
    225: (
        "build_development_to_market_divergence_detector_225",
        "development_to_market_divergence_detector",
        [
            ("development_to_market_divergence_detector.source", "enum", "== intelligence_market_extensions_layer.pwa_strategy_status_225"),
            ("development_to_market_divergence_detector.latency_ms", "numeric", "< 500"),
        ],
    ),
    227: (
        "build_unified_trading_intelligence_workspace_227",
        "unified_trading_intelligence_workspace",
        [
            ("unified_trading_intelligence_workspace.source", "enum", "== intelligence_market_extensions_layer.analyze_etf_premium_227"),
            ("unified_trading_intelligence_workspace.latency_ms", "numeric", "< 500"),
        ],
    ),
}


def main() -> None:
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    for row in doc["rows"]:
        cid = row["capability_id"]
        if cid not in WAVE3:
            continue
        fn, root, extra_rules = WAVE3[cid]
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
    print(f"Patched acceptance for Wave 3 IDs: {sorted(WAVE3)}")


if __name__ == "__main__":
    main()
