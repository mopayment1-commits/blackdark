#!/usr/bin/env python3
"""Patch BATCH05 acceptance rows for Wave 5 strangler IDs (242–244, 246–250)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"

WAVE5: dict[int, tuple[str, str, list[tuple[str, str, str]]]] = {
    242: (
        "build_price_prediction_multi_signal_forecast_242",
        "price_prediction_multi_signal_forecast",
        [
            ("price_prediction_multi_signal_forecast.source", "enum", "== security_trust_data_layer.attach_audit_log_id_242"),
            ("price_prediction_multi_signal_forecast.latency_ms", "numeric", "< 5000"),
        ],
    ),
    243: (
        "build_correlation_matrix_243",
        "correlation_matrix",
        [
            ("correlation_matrix.source", "enum", "== security_trust_data_layer.ingest_bybit_price_243"),
            ("correlation_matrix.latency_ms", "numeric", "< 500"),
        ],
    ),
    244: (
        "build_new_listings_intelligence_244",
        "new_listings_intelligence",
        [
            ("new_listings_intelligence.source", "enum", "== security_trust_data_layer.ingest_cointelegraph_rss_244"),
            ("new_listings_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
    246: (
        "build_coverage_metadata_registry_246",
        "coverage_metadata_registry",
        [
            ("coverage_metadata_registry.source", "enum", "== security_trust_data_layer.list_etherscan_watchlist_246"),
            ("coverage_metadata_registry.latency_ms", "numeric", "< 500"),
        ],
    ),
    247: (
        "build_public_rest_api_247",
        "public_rest_api",
        [
            ("public_rest_api.source", "enum", "== security_trust_data_layer.generate_weekly_digest_247"),
            ("public_rest_api.latency_ms", "numeric", "< 2000"),
        ],
    ),
    248: (
        "build_mcp_server_for_ai_agents_248",
        "mcp_server_for_ai_agents",
        [
            ("mcp_server_for_ai_agents.source", "enum", "== security_trust_data_layer.manual_performance_tracker_248"),
            ("mcp_server_for_ai_agents.latency_ms", "numeric", "< 5000"),
        ],
    ),
    249: (
        "build_cli_access_249",
        "cli_access",
        [
            ("cli_access.source", "enum", "== security_trust_data_layer.trad_simulator_rejected_status_249"),
            ("cli_access.latency_ms", "numeric", "< 500"),
        ],
    ),
    250: (
        "build_openapi_sdk_generation_250",
        "openapi_sdk_generation",
        [
            ("openapi_sdk_generation.source", "enum", "== security_trust_data_layer.execution_speed_rejected_status_250"),
            ("openapi_sdk_generation.latency_ms", "numeric", "< 500"),
        ],
    ),
}


def main() -> None:
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    for row in doc["rows"]:
        cid = row["capability_id"]
        if cid not in WAVE5:
            continue
        fn, root, extra_rules = WAVE5[cid]
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
    print(f"Patched acceptance for Wave 5 IDs: {sorted(WAVE5)}")


if __name__ == "__main__":
    main()
