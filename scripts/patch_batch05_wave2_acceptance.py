#!/usr/bin/env python3
"""Patch BATCH05 acceptance rows for Wave 2 strangler IDs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"

WAVE2: dict[int, tuple[str, str, list[tuple[str, str, str]]]] = {
    205: (
        "build_open_interest_205",
        "open_interest_intelligence",
        [
            ("open_interest_intelligence.source", "enum", "== free_market_data.binance_futures_snapshot"),
            ("open_interest_intelligence.latency_ms", "numeric", "< 500"),
        ],
    ),
    207: (
        "build_price_volume_market_metrics_207",
        "price_volume_market_metrics",
        [
            ("price_volume_market_metrics.source", "enum", "== market_context.probe_price_sources+free_market_data.binance_futures_snapshot"),
            ("price_volume_market_metrics.latency_ms", "numeric", "< 2000"),
        ],
    ),
    208: (
        "build_metric_correlation_workbench_208",
        "metric_correlation_workbench",
        [
            ("metric_correlation_workbench.source", "enum", "== free_market_data.binance_futures_snapshot"),
            ("metric_correlation_workbench.latency_ms", "numeric", "< 500"),
        ],
    ),
    209: (
        "build_custom_chart_builder_209",
        "custom_chart_builder",
        [
            ("custom_chart_builder.source", "enum", "== cap646.fallbacks.resolve_ohlcv_closes"),
            ("custom_chart_builder.latency_ms", "numeric", "< 2000"),
        ],
    ),
    210: (
        "build_custom_dashboards_layouts_210",
        "custom_dashboards_layouts",
        [
            ("custom_dashboards_layouts.source", "enum", "== bd_platform.market_rankings.market_rankings"),
            ("custom_dashboards_layouts.latency_ms", "numeric", "< 1000"),
        ],
    ),
    211: (
        "build_screener_211",
        "screener",
        [
            ("screener.source", "enum", "== bd_platform.market_rankings.market_rankings"),
            ("screener.latency_ms", "numeric", "< 500"),
        ],
    ),
    213: (
        "build_anomaly_detection_alerts_213",
        "anomaly_detection_alerts",
        [
            ("anomaly_detection_alerts.source", "enum", "== footprint_analytics.footprint_snapshot"),
            ("anomaly_detection_alerts.latency_ms", "numeric", "< 500"),
        ],
    ),
    215: (
        "build_community_explorer_215",
        "community_explorer",
        [
            ("community_explorer.source", "enum", "== onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
            ("community_explorer.latency_ms", "numeric", "< 500"),
        ],
    ),
    216: (
        "build_research_market_insights_216",
        "research_market_insights",
        [
            ("research_market_insights.source", "enum", "== market_rankings+onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
            ("research_market_insights.latency_ms", "numeric", "< 500"),
        ],
    ),
}


def main() -> None:
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    for row in doc["rows"]:
        cid = row["capability_id"]
        if cid not in WAVE2:
            continue
        fn, root, extra_rules = WAVE2[cid]
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
    print(f"Patched acceptance for Wave 2 IDs: {sorted(WAVE2)}")


if __name__ == "__main__":
    main()
