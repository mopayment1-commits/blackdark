#!/usr/bin/env python3
"""Write ISO 29148 pre-test acceptance criteria for Batch03 IDs 101-150.

Derived from RTM + handler bindings (cap646/batch03_dedicated.py, batch01 handlers).
Does NOT read probe output — run this BEFORE any pentagonal regeneration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH03_ACCEPTANCE_101_150.json"

# Shared rule fragments
OK_BOOL = {"field": "{root}.ok", "type": "boolean", "condition": "== true"}
FEATURE_REF = {"field": "{root}.feature_ref", "type": "numeric", "condition": "> 0"}
SUCCESS_TOP = {"field": "success", "type": "boolean", "condition": "== true"}
SURFACE_MATCH = {"field": "surface", "type": "enum", "condition": "== expected_surface"}

REUSED_106 = [
    {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 63"},
    {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
    {"field": "data_quality_provenance.provenance.score", "type": "numeric", "condition": ">= 0"},
    {"field": "data_quality_provenance.provenance.score", "type": "numeric", "condition": "<= 100"},
]
REUSED_107 = [
    {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 64"},
    {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
    {"field": "metric_methodology.methodology_registry", "type": "present", "condition": "not_null"},
]
REUSED_110 = [
    {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 69"},
    {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
    {"field": "cross_domain_decision.multi_dimensional.ok", "type": "boolean", "condition": "== true"},
    {"field": "cross_domain_decision.multi_dimensional.composite_score", "type": "numeric", "condition": ">= 0"},
]
REUSED_125 = [
    {"field": "catalog_link.duplicate_of", "type": "numeric", "condition": "== 85"},
    {"field": "catalog_link.classification", "type": "enum", "condition": "== REUSED-LINK"},
    {
        "field": "futures_open_interest.open_interest_usd",
        "type": "numeric",
        "condition": ">= 0",
        "decision": "ZERO_ACCEPTABLE",
        "rationale": "open_interest_usd may be 0 when Binance public free_tier.available=false — contract passes with numeric zero; does NOT imply live OI feed failure.",
    },
    {
        "field": "futures_open_interest.derivatives_overview",
        "type": "present",
        "condition": "not_null",
        "rationale": "Overview object must exist even when OI fields are zero.",
    },
]

E2E_ALL_PASSED = [
    {"field": "{root}.ok", "type": "boolean", "condition": "== true"},
    {"field": "{root}.all_passed", "type": "boolean", "condition": "== true"},
    {"field": "{root}.checks", "type": "list_min_length", "condition": ">= 1"},
]


def _root_rules(root: str, templates: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    templates = templates or E2E_ALL_PASSED
    out = []
    for t in templates:
        row = dict(t)
        row["field"] = row["field"].replace("{root}", root)
        out.append(row)
    return out

# Per-ID: (payload_root_key, domain_rules with {root} placeholder, notes, functional_gap optional)
_SPECS: dict[int, dict[str, Any]] = {
    101: {
        "payload_root": "oracle_freshness",
        "domain_rules": [
            {"field": "oracle_freshness.ok", "type": "boolean", "condition": "== true"},
            {"field": "oracle_freshness.deviation_ms", "type": "numeric", "condition": "< 5000"},
            {"field": "oracle_freshness.status", "type": "enum", "condition": "in fresh,stale,critical_stale"},
            {"field": "oracle_freshness.accepted", "type": "boolean", "condition": "in true,false"},
            {"field": "oracle_freshness.feature_ref", "type": "numeric", "condition": "== 101"},
        ],
        "functional_gap": {
            "catalog_name": "AI Data Analyst / Ask AI",
            "implemented_scope": "Oracle timestamp freshness gate only (validate_oracle_freshness_101 → /oracle/validate)",
            "missing_scope": "No NL Ask-AI chat, analyst Q&A, or generative reporting in binding _cap101",
            "decision": "PARTIAL_MISNAMED — acceptance covers freshness sub-capability; full Ask-AI not implemented in current spine",
        },
    },
    102: {
        "payload_root": "il_vulnerability",
        "domain_rules": [
            {"field": "il_vulnerability.vulnerability_score", "type": "numeric", "condition": ">= 0"},
            {"field": "il_vulnerability.vulnerability_score", "type": "numeric", "condition": "<= 100"},
            {"field": "il_vulnerability.feature_ref", "type": "numeric", "condition": "== 102"},
        ],
    },
    103: {
        "payload_root": None,
        "spine": "batch01",
        "domain_rules": [
            {"field": "hot_storage", "type": "present", "condition": "not_null"},
            {"field": "graphql", "type": "enum", "condition": "== /graphql"},
            {"field": "institutional_api", "type": "enum", "condition": "== /api/institutional"},
        ],
        "notes": "OVERLAP-PARTIAL — batch01 spine via handle_institutional_capability",
    },
    104: {
        "payload_root": "block_level_delivery",
        "domain_rules": _root_rules("block_level_delivery"),
    },
    105: {
        "payload_root": "historical_data_layer",
        "domain_rules": [
            {"field": "historical_data_layer.tail_risk_alpha.ok", "type": "boolean", "condition": "== true"},
            {"field": "historical_data_layer.tail_risk_alpha.feature_ref", "type": "numeric", "condition": "== 105"},
            {"field": "historical_data_layer.tail_risk_alpha.tail_alpha", "type": "numeric", "condition": "present"},
        ],
    },
    106: {"payload_root": "data_quality_provenance", "domain_rules": REUSED_106, "status": "REUSED-LINK"},
    107: {"payload_root": "metric_methodology", "domain_rules": REUSED_107, "status": "REUSED-LINK"},
    108: {
        "payload_root": "institutional_data_api",
        "domain_rules": [
            {"field": "institutional_data_api.skew", "type": "numeric", "condition": ">= -1"},
            {"field": "institutional_data_api.skew", "type": "numeric", "condition": "<= 1"},
            {"field": "institutional_data_api.feature_ref", "type": "numeric", "condition": "== 108"},
        ],
    },
    109: {
        "payload_root": "white_label_research",
        "domain_rules": [
            {"field": "white_label_research.ok", "type": "boolean", "condition": "== true"},
            {"field": "white_label_research.spike_anchors", "type": "present", "condition": "not_null"},
            {"field": "white_label_research.feature_ref", "type": "enum", "condition": "in 82,100,109"},
        ],
    },
    110: {"payload_root": "cross_domain_decision", "domain_rules": REUSED_110, "status": "REUSED-LINK"},
    111: {
        "payload_root": "exchange_flow_actionability",
        "domain_rules": [
            {"field": "exchange_flow_actionability.pearson_r", "type": "numeric", "condition": ">= -1"},
            {"field": "exchange_flow_actionability.pearson_r", "type": "numeric", "condition": "<= 1"},
        ],
    },
    112: {
        "payload_root": "flow_to_price_explanation",
        "domain_rules": [
            {"field": "flow_to_price_explanation.gcli_score", "type": "numeric", "condition": ">= 0"},
        ],
    },
    113: {
        "payload_root": "asset_intelligence_profile",
        "domain_rules": [
            {"field": "asset_intelligence_profile.delta", "type": "numeric", "condition": "present"},
            {"field": "asset_intelligence_profile.feature_ref", "type": "numeric", "condition": "== 113"},
        ],
    },
    114: {
        "payload_root": "asset_classification_taxonomy",
        "domain_rules": [
            {"field": "asset_classification_taxonomy.whale_filtered_ratio", "type": "numeric", "condition": "> 0"},
            {"field": "asset_classification_taxonomy.feature_ref", "type": "numeric", "condition": "== 114"},
        ],
    },
    115: {
        "payload_root": "asset_screener",
        "domain_rules": [
            {"field": "asset_screener.velocity_pct", "type": "numeric", "condition": "> 0"},
            {"field": "asset_screener.feature_ref", "type": "numeric", "condition": "== 115"},
        ],
    },
    116: {
        "payload_root": "market_pair_intelligence",
        "domain_rules": _root_rules("market_pair_intelligence"),
    },
    117: {
        "payload_root": "real_volume_quality_adjusted",
        "domain_rules": [
            {"field": "real_volume_quality_adjusted.vacuum_pct", "type": "numeric", "condition": ">= 0"},
        ],
    },
    118: {
        "payload_root": "vwap_price_intelligence",
        "domain_rules": [
            {"field": "vwap_price_intelligence.risk_distribution", "type": "present", "condition": "not_null"},
        ],
    },
    119: {
        "payload_root": "market_cap_fdv",
        "domain_rules": [
            {"field": "market_cap_fdv.execution_rejected", "type": "boolean", "condition": "== true"},
            {"field": "market_cap_fdv.reference_price", "type": "numeric", "condition": "> 0"},
            {"field": "market_cap_fdv.feature_ref", "type": "numeric", "condition": "== 119"},
        ],
    },
    120: {
        "payload_root": "supply_intelligence",
        "domain_rules": [
            {"field": "supply_intelligence.leverage_risk_analysis.ok", "type": "boolean", "condition": "== true"},
            {"field": "supply_intelligence.leverage_risk_analysis.optimization_rejected", "type": "boolean", "condition": "== true"},
            {"field": "supply_intelligence.drawdown_lifecycle", "type": "present", "condition": "not_null"},
        ],
    },
    121: {
        "payload_root": "roi_ath_intelligence",
        "domain_rules": [
            {"field": "roi_ath_intelligence.pnl_attribution", "type": "present", "condition": "not_null"},
        ],
    },
    122: {
        "payload_root": "volatility_intelligence",
        "domain_rules": [
            {"field": "volatility_intelligence.statistical_not_ai", "type": "boolean", "condition": "== true"},
            {"field": "volatility_intelligence.chow_f_statistic", "type": "numeric", "condition": ">= 0"},
            {"field": "volatility_intelligence.feature_ref", "type": "numeric", "condition": "== 122"},
        ],
    },
    123: {
        "payload_root": "sharpe_ratio_intelligence",
        "domain_rules": [
            {"field": "sharpe_ratio_intelligence.poc_price", "type": "numeric", "condition": "> 0"},
        ],
    },
    124: {
        "payload_root": "futures_funding_rate",
        "domain_rules": [
            {"field": "futures_funding_rate.gaps", "type": "list_min_length", "condition": ">= 0"},
        ],
    },
    125: {"payload_root": "futures_open_interest", "domain_rules": REUSED_125, "status": "REUSED-LINK"},
    126: {
        "payload_root": "futures_volume",
        "domain_rules": [
            {"field": "futures_volume.no_shield_no_execution", "type": "boolean", "condition": "== true"},
        ],
    },
    127: {
        "payload_root": "multi_factor_market_overview",
        "domain_rules": [
            {"field": "multi_factor_market_overview.exploiter_naming_rejected", "type": "boolean", "condition": "== true"},
        ],
    },
    128: {
        "payload_root": "momentum_intelligence",
        "domain_rules": _root_rules("momentum_intelligence"),
    },
    129: {
        "payload_root": None,
        "spine": "batch01",
        "domain_rules": [
            {"field": "context", "type": "present", "condition": "not_null"},
            {"field": "gate", "type": "present", "condition": "not_null"},
        ],
        "notes": "OVERLAP-PARTIAL — batch01 market handler sentiment_intelligence",
    },
    130: {
        "payload_root": "mindshare_intelligence",
        "domain_rules": [
            {"field": "mindshare_intelligence.ok", "type": "boolean", "condition": "== true"},
            {"field": "mindshare_intelligence.execution_rejected", "type": "boolean", "condition": "== true"},
            {"field": "mindshare_intelligence.feature_ref", "type": "numeric", "condition": "== 130"},
        ],
    },
    131: {
        "payload_root": "narrative_sector_intelligence",
        "domain_rules": [
            {"field": "narrative_sector_intelligence.dust_asset_count", "type": "numeric", "condition": ">= 0"},
            {"field": "narrative_sector_intelligence.execution_rejected", "type": "boolean", "condition": "== true"},
            {"field": "narrative_sector_intelligence.feature_ref", "type": "numeric", "condition": "== 131"},
        ],
    },
    132: {
        "payload_root": "mindshare_gainers_losers",
        "domain_rules": [
            {"field": "mindshare_gainers_losers.risk_score", "type": "numeric", "condition": ">= 0"},
            {"field": "mindshare_gainers_losers.self_patching_rejected", "type": "boolean", "condition": "== true"},
        ],
    },
    133: {
        "payload_root": "curated_crypto_news",
        "domain_rules": [
            {"field": "curated_crypto_news.dimensions.macro.event_nexus.ok", "type": "boolean", "condition": "== true"},
            {"field": "curated_crypto_news.dimensions.macro.event_nexus.feature_ref", "type": "numeric", "condition": "== 133"},
        ],
    },
    134: {
        "payload_root": "ai_news_summaries",
        "domain_rules": [
            {"field": "ai_news_summaries.convergence_pct", "type": "numeric", "condition": ">= 0"},
            {"field": "ai_news_summaries.feature_ref", "type": "numeric", "condition": "== 134"},
        ],
    },
    135: {
        "payload_root": "industry_event_monitoring",
        "domain_rules": [
            {"field": "industry_event_monitoring.vortex_score", "type": "numeric", "condition": ">= 0"},
            {"field": "industry_event_monitoring.rule_based_only", "type": "boolean", "condition": "== true"},
        ],
    },
    136: {
        "payload_root": "agentic_monitoring_views",
        "domain_rules": [
            {"field": "agentic_monitoring_views.reply", "type": "present", "condition": "not_null"},
            {"field": "agentic_monitoring_views.rule_based_faq", "type": "boolean", "condition": "== true"},
        ],
    },
    137: {
        "payload_root": "custom_watchlists",
        "domain_rules": [
            {"field": "custom_watchlists.ok", "type": "boolean", "condition": "== true"},
            {"field": "custom_watchlists.not_a_technical_feature", "type": "boolean", "condition": "== true"},
        ],
    },
    138: {
        "payload_root": "token_unlock_calendar",
        "domain_rules": [
            {"field": "token_unlock_calendar.ok", "type": "boolean", "condition": "== true"},
            {"field": "token_unlock_calendar.bundle", "type": "present", "condition": "not_null"},
        ],
    },
    139: {
        "payload_root": "vesting_schedule_intelligence",
        "domain_rules": _root_rules("vesting_schedule_intelligence"),
    },
    140: {
        "payload_root": "token_allocation_intelligence",
        "domain_rules": [
            {"field": "token_allocation_intelligence.duplicate_of", "type": "numeric", "condition": "== 90"},
            {"field": "token_allocation_intelligence.not_standalone", "type": "boolean", "condition": "== true"},
            {"field": "token_allocation_intelligence.feature_ref", "type": "numeric", "condition": "== 140"},
        ],
    },
    141: {
        "payload_root": "unlock_impact_intelligence",
        "domain_rules": [
            {"field": "unlock_impact_intelligence.items", "type": "list_min_length", "condition": ">= 1"},
            {"field": "unlock_impact_intelligence.feature_ref", "type": "numeric", "condition": "== 141"},
        ],
    },
    142: {
        "payload_root": "fundraising_rounds",
        "domain_rules": [
            {"field": "fundraising_rounds.ok", "type": "boolean", "condition": "== true"},
            {"field": "fundraising_rounds.metrics.network_growth.value", "type": "numeric", "condition": "> 0"},
        ],
    },
    143: {
        "payload_root": "investor_intelligence",
        "domain_rules": [
            {"field": "investor_intelligence.events", "type": "list_min_length", "condition": ">= 0"},
        ],
    },
    144: {
        "payload_root": "fund_manager_intelligence",
        "domain_rules": [
            {"field": "fund_manager_intelligence.ok", "type": "boolean", "condition": "== true"},
            {"field": "fund_manager_intelligence.alerts", "type": "list_min_length", "condition": ">= 1"},
            {"field": "fund_manager_intelligence.cross_validation_on_chain", "type": "boolean", "condition": "== true"},
            {"field": "fund_manager_intelligence.feature_ref", "type": "numeric", "condition": "== 144"},
        ],
    },
    145: {
        "payload_root": "ma_intelligence",
        "domain_rules": [
            {"field": "ma_intelligence.price", "type": "numeric", "condition": "> 0"},
            {"field": "ma_intelligence.volume_24h", "type": "numeric", "condition": "> 0"},
        ],
    },
    146: {
        "payload_root": "capital_flow_funding_trends",
        "domain_rules": [
            {"field": "capital_flow_funding_trends.consensus_accepted", "type": "boolean", "condition": "in true,false"},
            {"field": "capital_flow_funding_trends.primary_price", "type": "numeric", "condition": "> 0"},
            {"field": "capital_flow_funding_trends.divergences_pct", "type": "present", "condition": "not_null"},
        ],
    },
    147: {
        "payload_root": "comparable_funding_valuation",
        "domain_rules": [
            {"field": "comparable_funding_valuation.trading_engine_rejected", "type": "boolean", "condition": "== true"},
            {"field": "comparable_funding_valuation.feature_ref", "type": "numeric", "condition": "== 147"},
            {"field": "comparable_funding_valuation.insight_only", "type": "boolean", "condition": "== true"},
        ],
    },
    148: {
        "payload_root": "due_diligence_report",
        "domain_rules": [
            {"field": "due_diligence_report.ok", "type": "boolean", "condition": "== true"},
            {"field": "due_diligence_report.block_height", "type": "numeric", "condition": "> 0"},
            {"field": "due_diligence_report.cross_validation_primary_rpc", "type": "boolean", "condition": "== true"},
        ],
    },
    149: {
        "payload_root": "automated_risk_scoring",
        "domain_rules": [
            {"field": "automated_risk_scoring.tvl_usd", "type": "numeric", "condition": "> 0"},
            {"field": "automated_risk_scoring.protocol", "type": "string_nonempty", "condition": "length >= 1"},
        ],
    },
    150: {
        "payload_root": "protocol_kpi_intelligence",
        "domain_rules": [
            {"field": "protocol_kpi_intelligence.daily_top3", "type": "present", "condition": "not_null"},
            {"field": "protocol_kpi_intelligence.opportunity_score.opportunity_score", "type": "numeric", "condition": ">= 0"},
            {"field": "protocol_kpi_intelligence.opportunity_score.opportunity_score", "type": "numeric", "condition": "<= 100"},
        ],
    },
}


def _expand_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in rules:
        row = dict(r)
        if "{root}" in row.get("field", ""):
            continue  # caller must replace
        out.append(row)
    return out


def build_acceptance() -> dict[str, Any]:
    from cap646.batch03_dedicated import EXPECTED_SURFACE

    rtm = json.loads((ROOT / "docs/BATCH03_RTM.json").read_text(encoding="utf-8"))
    rows = []
    for rtm_row in sorted(rtm["rows"], key=lambda r: r["id"]):
        cid = rtm_row["id"]
        spec = _SPECS[cid]
        rules = []
        for rule in spec["domain_rules"]:
            rules.append(dict(rule))
        rules.insert(0, dict(SUCCESS_TOP))
        rules.insert(1, dict(SURFACE_MATCH))

        entry: dict[str, Any] = {
            "capability_id": cid,
            "capability_name": rtm_row["capability"],
            "expected_surface": EXPECTED_SURFACE.get(cid, rtm_row["expected_surface"]),
            "status": spec.get("status", rtm_row["status"]),
            "production_spine": spec.get("spine", rtm_row.get("production_spine")),
            "payload_root": spec.get("payload_root"),
            "binding_file": rtm_row.get("binding_file"),
            "binding_function": rtm_row.get("binding_function"),
            "domain_rules": rules,
            "source": "catalog+handler_contract — written before probe (ISO 29148)",
        }
        if spec.get("notes"):
            entry["notes"] = spec["notes"]
        if spec.get("functional_gap"):
            entry["functional_gap"] = spec["functional_gap"]
        rows.append(entry)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "standard": "ISO/IEC/IEEE 29148",
        "scope": "Batch03 IDs 101-150 (50 rows)",
        "pre_probe": True,
        "rows": rows,
    }


def main() -> None:
    doc = build_acceptance()
    assert len(doc["rows"]) == 50, f"expected 50 acceptance rows, got {len(doc['rows'])}"
    for row in doc["rows"]:
        assert row["domain_rules"], f"ID {row['capability_id']}: domain_rules must not be empty"
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(doc['rows'])} capabilities)")


if __name__ == "__main__":
    main()
