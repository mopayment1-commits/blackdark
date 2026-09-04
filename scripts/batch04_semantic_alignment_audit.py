#!/usr/bin/env python3
"""Semantic Alignment Gate — Batch04 #151-#200. Audit only; no repairs."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Per-ID semantic audit based on: hero source code, transform logic, runtime payload.
# Classifications are independent of prior Gate1 semantic_miswire detector.
DOMAIN_AUDIT: dict[int, dict[str, str]] = {
    151: {
        "classification": "ALIGNED",
        "hero_domain": "quarterly_protocol_report via explain_opportunity_151 + defillama TVL",
        "actual_domain": "quarter_label, reporting_period=quarterly, protocol_tvl_usd, performance_score, dimension_breakdown",
        "reason": "Dedicated batch04_quarterly_protocol module computes genuine quarterly protocol performance semantics.",
    },
    152: {
        "classification": "MISWIRED",
        "hero_domain": "data_sources E2E integration test runner (checks 140-152)",
        "actual_domain": "governance_proposals contains e2e checks/all_passed, not governance proposals",
        "reason": "Runtime executes run_data_sources_e2e_140_152; repackages test checks as governance_proposal_intelligence.",
    },
    153: {
        "classification": "MISWIRED",
        "hero_domain": "multi-venue theoretical arbitrage with cost breakdown",
        "actual_domain": "coverage_registry maps venue prices; arbitrage_insight with net_spread_pct",
        "reason": "analyze_arbitrage_opportunity_153 performs arbitrage analysis, not project monitoring coverage.",
    },
    154: {
        "classification": "MISWIRED",
        "hero_domain": "financial_brain merged infrastructure status (activation_not_build)",
        "actual_domain": "copilot_status=merged_not_standalone; dimensions/outputs are infra metadata",
        "reason": "financial_brain_status_154 reports merge status, not an interactive AI crypto copilot.",
    },
    155: {
        "classification": "MISWIRED",
        "hero_domain": "statistical arbitrage z-score mean-reversion insight",
        "actual_domain": "research_depth=deep, z_score, historical reversion — stat arb not deep research",
        "reason": "stat_arb_insight_155 is pair correlation deviation, not AI deep research capability.",
    },
    156: {
        "classification": "MISWIRED",
        "hero_domain": "asset registry 105-coin list with selection criteria",
        "actual_domain": "graph_nodes=asset list; no edges, relationships, or graph traversal",
        "reason": "asset_registry_105_coins_156 is a coin list, not a crypto knowledge graph.",
    },
    157: {
        "classification": "MISWIRED",
        "hero_domain": "onchain advanced merged infrastructure status",
        "actual_domain": "research_items=capabilities list, routes=oracle paths — infra status not library",
        "reason": "onchain_advanced_status_157 reports merge/activation status, not a research library.",
    },
    158: {
        "classification": "MISWIRED",
        "hero_domain": "multi-venue websocket connection aggregation status",
        "actual_domain": "feed_items=venue connections with latency_ms, not research content",
        "reason": "multi_venue_websocket_status_158 is streaming infra, not institutional research feed.",
    },
    159: {
        "classification": "PARTIAL_ALIGNMENT",
        "hero_domain": "institutional API platform via batch03 #103 wrap + gas profile owner",
        "actual_domain": "institutional_api, graphql, hot_storage present; blocker BLOCKER-159-103",
        "reason": "Aligned portion: API platform endpoints. Missing: full platform maturity blocked on #103.",
    },
    160: {
        "classification": "MISWIRED",
        "hero_domain": "Bollinger/Keltner volatility squeeze detection",
        "actual_domain": "pricing_model=pay_per_request but in_squeeze from vol squeeze; metering is static stub",
        "reason": "detect_volatility_squeeze_160 is TA squeeze indicator, not pay-per-request data access.",
    },
    161: {
        "classification": "PARTIAL_ALIGNMENT",
        "hero_domain": "institutional capability handler (RBAC/isolation matrix)",
        "actual_domain": "role_matrix, entitlements, isolation from handle_institutional_capability(161)",
        "reason": "Aligned portion: entitlements/RBAC. Missing: full institutional data delivery pipeline; hero binding alert_delivery unused.",
    },
    162: {
        "classification": "PARTIAL_ALIGNMENT",
        "hero_domain": "provenance hot storage payload (REUSED_LINK #106)",
        "actual_domain": "provenance + hot_storage fields present; catalog_link in code not at top-level runtime",
        "reason": "Aligned portion: evidence/provenance data. Missing: full evidence layer; underlying is #106 reuse.",
    },
    163: {
        "classification": "MISWIRED",
        "hero_domain": "intelligence analysis E2E test runner (checks 153-163)",
        "actual_domain": "cross_domain_report with checks_passed/all_passed e2e results",
        "reason": "run_intelligence_analysis_e2e_153_163 is integration test, not research-to-decision intelligence.",
    },
    164: {
        "classification": "MISWIRED",
        "hero_domain": "liquidity impact / position slippage warning (panic button rejected)",
        "actual_domain": "actionability_score derived from estimated_slippage_pct, unlock_risk=slippage",
        "reason": "liquidity_impact_warning_164 is portfolio slippage, not token unlock actionability.",
    },
    165: {
        "classification": "MISWIRED",
        "hero_domain": "BTC hashrate capitulation / miner revenue forecast",
        "actual_domain": "momentum_score=hashrate_drop_pct, capitulation_signal from mining economics",
        "reason": "hashrate_capitulation_forecast_165 is mining hashrate, not fundraising momentum.",
    },
    166: {
        "classification": "MISWIRED",
        "hero_domain": "brokerage integration rejected status",
        "actual_domain": "confidence_score=0.0 hardcoded, research_status=rejected_brokerage",
        "reason": "brokerage_rejected_status_166 reports rejection, not research confidence scoring.",
    },
    167: {
        "classification": "MISWIRED",
        "hero_domain": "NTP/time synchronization validation",
        "actual_domain": "social_volume=deviation_sec (time sync deviation), not social metrics",
        "reason": "validate_time_sync_167 is clock sync, not social volume intelligence.",
    },
    168: {
        "classification": "MISWIRED",
        "hero_domain": "sybil cluster index attachment",
        "actual_domain": "dominance_pct=cluster_index integer, not social dominance percentage",
        "reason": "attach_cluster_index_168 is on-chain clustering, not social dominance intelligence.",
    },
    169: {
        "classification": "MISWIRED",
        "hero_domain": "asset correlation decay matrix vs BTC benchmark",
        "actual_domain": "unique_volume=oi_momentum_delta, correlation_matrix from decay matrix",
        "reason": "compute_correlation_decay_matrix_169 is portfolio correlation, not unique social volume.",
    },
    170: {
        "classification": "MISWIRED",
        "hero_domain": "open interest momentum delta on derivatives",
        "actual_domain": "trending_words=[], oi_momentum from derivatives OI delta",
        "reason": "compute_oi_momentum_delta_170 is OI derivatives flow, not trending words.",
    },
    171: {
        "classification": "MISWIRED",
        "hero_domain": "Federal Reserve M2 macro liquidity flow",
        "actual_domain": "trending_coins=[symbol], m2_flow=macro liquidity data",
        "reason": "compute_m2_macro_flow_171 is macro M2 flow, not trending coins.",
    },
    172: {
        "classification": "MISWIRED",
        "hero_domain": "institutional memory / decision replay status",
        "actual_domain": "historical_trends=memory_entries, institutional_memory status",
        "reason": "institutional_memory_status_172 is internal memory store, not historical crypto trends.",
    },
    173: {
        "classification": "MISWIRED",
        "hero_domain": "institutional RBAC role matrix status",
        "actual_domain": "key_narratives=rbac_roles list, not market narratives",
        "reason": "institutional_rbac_status_173 is access control, not key narratives intelligence.",
    },
    174: {
        "classification": "MISWIRED",
        "hero_domain": "white-label branding infrastructure status",
        "actual_domain": "alpha_narratives=white_label_features, branding_status",
        "reason": "full_white_label_status_174 is branding infra, not alpha narratives intelligence.",
    },
    175: {
        "classification": "PARTIAL_ALIGNMENT",
        "hero_domain": "batch01 sentiment_ai via compound_score from database",
        "actual_domain": "surface=sentiment_ai (not social_sentiment_intelligence); compound_score=0.0 SHADOW_LIVE_FORWARD",
        "reason": "Aligned portion: sentiment compound index. Missing: catalog surface; batch01 spine not batch04 independent.",
    },
    176: {
        "classification": "MISWIRED",
        "hero_domain": "risk infrastructure E2E test runner (checks 164-176)",
        "actual_domain": "weighted_sentiment=None, checks=e2e pass/fail list",
        "reason": "run_risk_infrastructure_e2e_164_176 is integration test, not weighted social sentiment.",
    },
    177: {
        "classification": "MISWIRED",
        "hero_domain": "arbitrage cost breakdown / net spread analysis",
        "actual_domain": "sentiment_balance=net_spread_pct from arbitrage costs",
        "reason": "analyze_arbitrage_cost_177 is trading cost analysis, not social sentiment balance.",
    },
    178: {
        "classification": "MISWIRED",
        "hero_domain": "scenario drawdown stress analysis",
        "actual_domain": "source_breakdown=scenarios list from drawdown analysis",
        "reason": "run_scenario_drawdown_analysis_178 is risk scenario, not social source breakdown.",
    },
    179: {
        "classification": "MISWIRED",
        "hero_domain": "command center dashboard widget assembly",
        "actual_domain": "dev_activity_score=widget_count, widgets=top3/health/alerts/heatmap",
        "reason": "build_command_center_dashboard_179 is general dashboard, not development activity intelligence.",
    },
    180: {
        "classification": "MISWIRED",
        "hero_domain": "whale flow SVG visualization (nodes/edges)",
        "actual_domain": "contributor_count=flow_count, whale_flows=visualization graph",
        "reason": "build_whale_flow_visualization_180 is whale flow viz, not dev activity contributors.",
    },
    181: {
        "classification": "MISWIRED",
        "hero_domain": "IC committee packets / duplicate_of #87 status",
        "actual_domain": "ecosystem_score=packet_count, committee_packets status metadata",
        "reason": "committee_packets_status_181 is IC reporting infra, not ecosystem development dashboard.",
    },
    182: {
        "classification": "MISWIRED",
        "hero_domain": "white-label infrastructure duplicate_of #90 status",
        "actual_domain": "activity_change_pct from white_label status, not dev activity delta",
        "reason": "white_label_infrastructure_status_182 is branding infra, not developer activity change detection.",
    },
    183: {
        "classification": "ALIGNED",
        "hero_domain": "whale tier classification, flow direction, concentration risk (distinct from #130 swap)",
        "actual_domain": "whale_tier=mega_whale, amount_usd, flow_direction, is_whale_event, risk_score; distinct_from_130 behavioral",
        "reason": "batch04_whale_transaction performs genuine whale transaction intelligence, not swap slippage (#130).",
    },
    184: {
        "classification": "MISWIRED",
        "hero_domain": "fund reporting IC scheduled reports status (duplicate #87)",
        "actual_domain": "cohort_type=whale_shark, holders=[], reporting_status from IC reports",
        "reason": "fund_reporting_status_184 is fund IC reporting, not whale/shark holder cohorts.",
    },
    185: {
        "classification": "MISWIRED",
        "hero_domain": "acquisition evidence package deferred assembly template",
        "actual_domain": "top_holders=evidence_items from deferred doc assembly, not on-chain holders",
        "reason": "acquisition_evidence_package_185 is M&A evidence docs, not top holders intelligence.",
    },
    186: {
        "classification": "MISWIRED",
        "hero_domain": "continuous learning / data flywheel status (duplicate #97)",
        "actual_domain": "balance_history=learning_status, wallet_tool_status — flywheel not wallet balances",
        "reason": "continuous_learning_status_186 is ML flywheel, not historical wallet balance tool.",
    },
    187: {
        "classification": "MISWIRED",
        "hero_domain": "latency monitoring p50/p99 metrics",
        "actual_domain": "inflow_usd=latency_p50_ms (milliseconds labeled as USD inflow)",
        "reason": "latency_monitoring_status_187 is API latency, not exchange inflow intelligence.",
    },
    188: {
        "classification": "MISWIRED",
        "hero_domain": "risk alert user confirmation workflow",
        "actual_domain": "outflow_usd=confirmed_alerts count, alert_confirmation boolean",
        "reason": "risk_alert_user_confirmation_188 is alert UX, not exchange outflow intelligence.",
    },
    189: {
        "classification": "MISWIRED",
        "hero_domain": "Bybit price ingest with netflow_proxy=true (not actual netflow)",
        "actual_domain": "netflow contains price_usd, role=secondary_fallback, netflow_proxy=true",
        "reason": "exchange_netflow_probe uses price oracle fallback as netflow proxy, not exchange netflow.",
    },
    190: {
        "classification": "MISWIRED",
        "hero_domain": "geographic arbitrage venue spread analysis",
        "actual_domain": "supply_on_exchanges_pct=geographic_spread_pct, exchange_supply=venues",
        "reason": "analyze_geographic_arbitrage_190 is geo arbitrage, not exchange supply/balance.",
    },
    191: {
        "classification": "MISWIRED",
        "hero_domain": "arbitrage portfolio UX E2E integration test",
        "actual_domain": "user_activity_score=activity_score from UX e2e, withdrawal_alerts",
        "reason": "run_arbitrage_portfolio_ux_e2e_177_191 is UX test runner, not exchange user activity.",
    },
    192: {
        "classification": "MISWIRED",
        "hero_domain": "perpetual funding rate analysis across venues",
        "actual_domain": "network_activity=venues dict, avg_funding_pct from derivatives funding",
        "reason": "analyze_funding_rate_192 is funding rate, not network activity intelligence.",
    },
    193: {
        "classification": "MISWIRED",
        "hero_domain": "auto-arbitrage execution rejected status",
        "actual_domain": "transaction_volume=cvd_usd from rejected status (no volume data)",
        "reason": "auto_arbitrage_rejected_status_193 is rejection notice, not transaction volume intelligence.",
    },
    194: {
        "classification": "MISWIRED",
        "hero_domain": "Cumulative Volume Delta (CVD = Σ Buy-Sell Volume)",
        "actual_domain": "nvt_ratio=cvd_usd=4900000, formula explicitly CVD not NVT",
        "reason": "compute_cvd_194 outputs CVD mislabeled as NVT ratio — confirmed metric defect.",
    },
    195: {
        "classification": "MISWIRED",
        "hero_domain": "DCA/grid strategy simulator (execution rejected)",
        "actual_domain": "mvrv_ratio=average_buy_price from DCA simulation, strategy=dca/grid",
        "reason": "strategy_simulator_195 is trading strategy sim, not MVRV on-chain valuation ratio.",
    },
    196: {
        "classification": "MISWIRED",
        "hero_domain": "Yahoo Finance macro benchmarks (SPX, VIX, DXY, GOLD, OIL)",
        "actual_domain": "realized_cap_usd=SPX value 5200, benchmarks=equity/commodity indices",
        "reason": "ingest_yahoo_finance_macro_196 is macro benchmarks, not crypto realized cap.",
    },
    197: {
        "classification": "MISWIRED",
        "hero_domain": "Alpha Vantage macro economic data ingestion",
        "actual_domain": "active_addresses=role field from macro source config, not on-chain DAA count",
        "reason": "ingest_alpha_vantage_macro_197 is macro data, not daily active addresses.",
    },
    198: {
        "classification": "MISWIRED",
        "hero_domain": "Binance research report ingestion",
        "actual_domain": "age_consumed=reports list count, dormancy_signals=len(reports)",
        "reason": "ingest_binance_research_198 is research PDF ingestion, not age consumed/dormancy metrics.",
    },
    199: {
        "classification": "MISWIRED",
        "hero_domain": "Messari research report ingestion",
        "actual_domain": "mean_dollar_invested_age=report date string, not MDIA on-chain metric",
        "reason": "ingest_messari_research_199 is research reports, not mean dollar invested age.",
    },
    200: {
        "classification": "PARTIAL_ALIGNMENT",
        "hero_domain": "CoinGecko quarterly/sector report ingestion",
        "actual_domain": "token_reports with titles/dates; circulation_rate=null, no supply/circulation metrics",
        "reason": "Aligned portion: report ingestion. Missing: token circulation rate/supply intelligence semantics.",
    },
}


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def _canonical_module(cap_id: int) -> str:
    from scripts.batch04_gate1_baseline import _canonical_module as g1_mod
    return g1_mod(cap_id)


async def _probe_payload(cap_id: int, acc_row: dict) -> tuple[dict[str, Any], str]:
    from cap646.runtime import execute_capability

    params: dict[str, Any] = {
        "symbol": "BTC",
        "tier": "pro",
        "amount_usd": 1_000_000,
        "address": "0xabc123",
    }
    result = await execute_capability(cap_id, skip_entitlement=True, params=params)
    surface = str(result.get("surface") or "")
    root = acc_row.get("payload_root") or surface

    if cap_id == 175:
        payload = {
            "surface": surface,
            "context": result.get("context"),
            "gate": result.get("gate"),
            "production_spine": result.get("production_spine"),
        }
        return payload, surface

    if cap_id == 183:
        payload = result.get("whale_transaction") or result.get(root) or {}
        return payload if isinstance(payload, dict) else {}, surface

    payload = result.get(root)
    if not isinstance(payload, dict):
        for k, v in result.items():
            if isinstance(v, dict) and k not in {"evidence_metadata", "compliance_footer", "params"}:
                payload = v
                break
    return (payload if isinstance(payload, dict) else {}), surface


def _summarize_payload(payload: dict[str, Any], max_keys: int = 10) -> str:
  parts = []
  for k, v in list(payload.items())[:max_keys]:
      if isinstance(v, (dict, list)):
          parts.append(f"{k}={type(v).__name__}")
      else:
          parts.append(f"{k}={v!r}")
  return "; ".join(parts)


async def main() -> None:
    commit = _commit()
    branch = _branch()
    acceptance = json.loads((ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json").read_text())
    acc = {r["capability_id"]: r for r in acceptance["rows"]}

    audit_rows: list[dict[str, Any]] = []
    for cap_id in range(151, 201):
        a = acc[cap_id]
        payload, surface = await _probe_payload(cap_id, a)
        audit = DOMAIN_AUDIT[cap_id]
        rc = a.get("requirement_contract") or {}
        row = {
            "id": cap_id,
            "capability_name": a["capability_name"],
            "designed_purpose": rc.get("business_objective", a["capability_name"]),
            "expected_domain_output": rc.get("expected_output") or a["expected_surface"],
            "runtime_module_function": _canonical_module(cap_id),
            "controlled_input": {"symbol": "BTC", "tier": "pro", "amount_usd": 1_000_000, "address": "0xabc123"},
            "actual_domain_output": _summarize_payload(payload),
            "semantic_comparison": f"Expected: {a['capability_name']}. Hero implements: {audit['hero_domain']}. Runtime: {audit['actual_domain']}",
            "semantic_alignment_status": audit["classification"],
            "reason": audit["reason"],
            "semantic_expected": audit.get("hero_domain", ""),
            "semantic_actual": audit["actual_domain"],
            "semantic_evidence": f"scripts/batch04_semantic_alignment_audit.py + runtime probe surface={surface}",
            "semantic_evidence_commit": commit,
            "evidence_path": f"cap646/batch04_dedicated.py + {audit['hero_domain'][:60]}",
            "evidence_commit": commit,
            "runtime_surface": surface,
            "runtime_payload_sample": {k: payload.get(k) for k in list(payload.keys())[:12]},
        }
        audit_rows.append(row)

    # Mechanical counts
    statuses = [r["semantic_alignment_status"] for r in audit_rows]
    summary = {
        "semantic_alignment": {k: statuses.count(k) for k in sorted(set(statuses))},
        "miswired_ids": [r["id"] for r in audit_rows if r["semantic_alignment_status"] == "MISWIRED"],
        "partial_alignment_ids": [r["id"] for r in audit_rows if r["semantic_alignment_status"] == "PARTIAL_ALIGNMENT"],
        "aligned_ids": [r["id"] for r in audit_rows if r["semantic_alignment_status"] == "ALIGNED"],
        "unproven_ids": [r["id"] for r in audit_rows if r["semantic_alignment_status"] == "UNPROVEN"],
        "gate1_semantic_miswire_count_prior": 16,
        "semantic_miswire_count_this_gate": statuses.count("MISWIRED"),
    }

    # Merge into existing RTM
    rtm_path = ROOT / "docs/BATCH04_RTM_151_200.json"
    rtm = json.loads(rtm_path.read_text()) if rtm_path.exists() else {}
    audit_by_id = {r["id"]: r for r in audit_rows}
    for row in rtm.get("rows", []):
        ar = audit_by_id[row["id"]]
        row["semantic_alignment_status"] = ar["semantic_alignment_status"]
        row["semantic_expected"] = ar["semantic_expected"]
        row["semantic_actual"] = ar["semantic_actual"]
        row["semantic_evidence"] = ar["semantic_evidence"]
        row["semantic_evidence_commit"] = ar["semantic_evidence_commit"]
        row["semantic_reason"] = ar["reason"]
        row["semantic_comparison"] = ar["semantic_comparison"]

    rtm["gate"] = "G1_BASELINE + SEMANTIC_ALIGNMENT_AUDIT"
    rtm["semantic_audit_generated_at"] = datetime.now(UTC).isoformat()
    rtm["semantic_audit_commit"] = commit
    rtm["semantic_audit_summary"] = summary
    rtm_path.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")

    out = ROOT / "docs/BATCH04_SEMANTIC_ALIGNMENT_AUDIT.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "branch": branch,
                "commit": commit,
                "scope": "Batch04 IDs 151-200",
                "summary": summary,
                "rows": audit_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"branch": branch, "commit": commit, "summary": summary}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
