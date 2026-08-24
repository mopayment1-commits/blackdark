"""Backend bindings for CAP978 extension IDs 647–978."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from cap646.backend_registry import BackendBinding, _KEYWORD_RULES, _TRACK_DEFAULTS, _slug
from cap978.catalog import catalog_by_id

_EXTENSION_ID_BINDINGS: dict[int, tuple[str, str, str]] = {
    658: ("bigquery_export", "warehouse_analytics_status", "none"),
    649: ("dbt_connector", "dbt_connector_status", "none"),
    647: ("bd_platform.free_tier_capabilities", "pyth_realtime_feed", "symbol"),
    648: ("bd_platform.free_tier_capabilities", "datashare_connector", "none"),
    652: ("bd_platform.free_tier_capabilities", "prompt_to_sql_agent", "none"),
    672: ("bd_platform.free_tier_capabilities", "liquid_staking_intelligence", "none"),
    673: ("bd_platform.free_tier_capabilities", "rwa_intelligence", "none"),
    674: ("bd_platform.free_tier_capabilities", "raises_funding_rounds", "none"),
    675: ("bd_platform.free_tier_capabilities", "investor_profiles", "none"),
    676: ("bd_platform.free_tier_capabilities", "unlocks_intelligence", "none"),
    690: ("bd_platform.free_tier_capabilities", "bloomberg_bridge_proxy", "symbol"),
    691: ("bd_platform.free_tier_capabilities", "refinitiv_bridge_proxy", "symbol"),
    702: ("bd_platform.free_tier_capabilities", "kaiko_institutional_proxy", "symbol"),
    703: ("bd_platform.free_tier_capabilities", "amberdata_institutional_proxy", "symbol"),
    704: ("bd_platform.free_tier_capabilities", "defi_risk_radar", "none"),
    705: ("bd_platform.free_tier_capabilities", "lending_market_risk", "none"),
    934: ("lp_il_simulator", "il_vulnerability_score", "symbol"),
    954: ("lp_il_simulator", "simulate_lp_live", "symbol"),
    975: ("lp_il_simulator", "lp_front_payload", "symbol"),
}

_EXTENSION_KEYWORD_RULES: tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...] = (
    (("real-time feed", "websocket", "stream"), ("b2b_websocket_hub", "get_b2b_ws_hub", "hub")),
    (("datashare", "warehouse", "snowflake", "bigquery"), ("data_lake", "lake_status", "none")),
    (("dbt", "pipeline"), ("ingestion_scheduler", "scheduler_running", "none")),
    (("bi connector", "tableau", "looker", "power bi"), ("product_honesty_api", "build_public_readiness", "none")),
    (("mcp", "ai agent", "prompt-to-sql", "prompt to sql"), ("graphql_schema", "graphql_health", "none")),
    (("dashboard-from-prompt", "dashboard from prompt"), ("bd_platform.tradingview_bridge", "chart_config", "none")),
    (("scheduled quer", "query result"), ("bd_platform.ifttt_rules", "list_rules", "none")),
    (("stablecoin", "stable coin"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("bridge", "cross-chain"), ("bd_platform.onchain_hub", "l2beat_security", "none")),
    (("yield", "apy", "lending", "borrow"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("liquid staking", "lst", "lsd"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("rwa", "real world asset", "tokenized"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("raise", "funding round", "investor profile"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("unlock", "vesting", "emission"), ("bd_platform.token_unlocks", "unlock_calendar", "none")),
    (("treasury intel", "treasury"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("etf flow", "etf"), ("bd_platform.onchain_hub", "lookintobitcoin_macro", "none")),
    (("digital asset treasury", "dat company"), ("bd_platform.market_rankings", "market_rankings", "none")),
    (("sopr", "mvrv", "realized cap", "cost basis", "holder cohort", "supply dynamic"), ("bd_platform.onchain_hub", "lookintobitcoin_macro", "none")),
    (("exchange balance", "netflow", "exchange flow"), ("onchain_tracker", "build_onchain_context_safe", "none")),
    (("entity-adjusted", "entity aware"), ("onchain_tracker", "build_onchain_context_safe", "none")),
    (("transaction decoder", "tx decoder"), ("onchain_tracker", "build_onchain_context_safe", "none")),
    (("wallet due diligence", "token due diligence", "due diligence"), ("due_diligence_bundle", "build_full_due_diligence_bundle", "none")),
    (("research copilot", "research agent", "ai research"), ("bd_platform.trulens_eval", "explain_prediction", "symbol")),
    (("thesis scor", "investment thesis"), ("trust_pulse", "build_trust_pulse", "symbol_tier")),
    (("risk radar", "defi risk"), ("risk_manager", "risk_status", "none")),
    (("methodology registry", "metric methodology", "data quality", "lineage", "normalization"), ("data_provenance_score", "compute_data_provenance_score", "provenance")),
    (("asset metadata", "canonical id", "canonical asset", "stable mapping"), ("blackdark.canonical.resolver", "resolve_asset", "symbol")),
    (("canonical data layer", "canonical data", "reference data"), ("blackdark.canonical.layer", "get_canonical_layer", "none")),
    (("coingecko", "coin gecko"), ("blackdark.ingestion.coingecko_connector", "fetch_coingecko_price", "symbol")),
    (("alternative.me", "fear greed"), ("blackdark.ingestion.alternative_me_connector", "fetch_fear_greed_index", "none")),
    (("arkham", "entity intelligence"), ("blackdark.ingestion.arkham_connector", "fetch_entity_intelligence_input", "symbol")),
    (("alpha engine", "multi-factor alpha"), ("bd_platform.alpha_engine", "compute_alpha_signal", "symbol")),
    (("data ingestion", "primary source"), ("blackdark.ingestion.coingecko_connector", "run_coingecko_primary_ingest", "none")),
    (("api export", "data export"), ("acquirer_evidence_pack", "build_acquirer_evidence_pack", "none")),
    (("event library", "market event"), ("market_event_library", "event_library_stats", "none")),
    (("failure", "kill rate"), ("failure_corpus", "corpus_stats", "none")),
    (("decision ledger", "outcome ledger"), ("decision_ledger", "ledger_stats", "none")),
    (("user exposure", "exposure log"), ("user_exposure_log", "exposure_stats", "none")),
    (("model version", "experiment registry"), ("ml.experience_log", "load_experience_summary", "none")),
    (("replay", "backfill"), ("ml.market_replay_bootstrap", "bootstrap_market_replay_dataset", "assets")),
    (("portfolio", "holding", "balance", "rebalance", "allocation"), ("bd_platform.portfolio_rebalancer", "portfolio_snapshot", "symbol")),
    (("fundamental screener", "financial statement"), ("bd_platform.market_rankings", "coin_detail", "coin_id")),
    (("sector comparable", "project comparable"), ("bd_platform.market_rankings", "market_rankings", "none")),
    (("coverage", "tokenized asset"), ("coverage_honesty", "build_coverage_honesty_board", "none")),
    (("exploiter", "attacker", "mev"), ("bd_platform.cex_dex_arbitrage", "scan_cex_dex_opportunities", "quote")),
    (("lunarcrush", "mindshare"), ("bd_platform.onchain_hub", "lunarcrush_metrics", "symbol")),
    (("coinmarketcal", "event calendar"), ("bd_platform.onchain_hub", "coinmarketcal_events", "none")),
    (("wallet cluster", "label", "scopescan"), ("bd_platform.onchain_hub", "wallet_clusters", "address")),
    (("intotheblock", "on-chain usage"), ("bd_platform.onchain_hub", "intotheblock_metrics", "symbol")),
    (("blockpour", "flow intelligence"), ("bd_platform.onchain_hub", "blockpour_flows", "none")),
    (("geckoterminal", "dex pair"), ("bd_platform.onchain_hub", "geckoterminal_pairs", "symbol")),
    (("vault", "secret", "key management"), ("bd_platform.vault_client", "vault_status", "none")),
    (("auto key", "api key import"), ("bd_platform.auto_keys", "auto_import_keys", "none")),
    (("roadmap audit", "feature audit"), ("bd_platform.roadmap_audit", "run_roadmap_audit", "none")),
    (("impermanent loss", "liquidity pool", "lp "), ("lp_il_simulator", "simulate_lp_live", "symbol")),
    (("strategy marketplace",), ("bd_platform.strategy_marketplace", "list_strategies", "none")),
)


def _keyword_binding(name: str) -> tuple[str, str, str] | None:
    nl = name.lower()
    for keys, binding in _EXTENSION_KEYWORD_RULES:
        if any(k in nl for k in keys):
            return binding
    for keys, binding in _KEYWORD_RULES:
        if any(k in nl for k in keys):
            return binding
    return None


@lru_cache(maxsize=332)
def resolve_extension_binding(capability_id: int) -> BackendBinding:
    row = catalog_by_id()[capability_id]
    name = row["capability"]
    track = row.get("track", "T19")
    surface = _slug(name)
    explicit = _EXTENSION_ID_BINDINGS.get(capability_id)
    if explicit:
        mod, ep, ps = explicit
        return BackendBinding(capability_id, mod, ep, surface, ps, "extension_id")
    kw = _keyword_binding(name)
    if kw:
        mod, ep, ps = kw
        return BackendBinding(capability_id, mod, ep, surface, ps, "extension_keyword")
    mod, ep, ps = _TRACK_DEFAULTS.get(track, ("bd_platform.infra_status", "infra_matrix", "none"))
    return BackendBinding(capability_id, mod, ep, surface, ps, "extension_track_default")


def binding_for(capability_id: int) -> dict[str, Any]:
    b = resolve_extension_binding(capability_id)
    return {
        "capability_id": b.capability_id,
        "backend_module": b.module,
        "backend_entrypoint": b.entrypoint,
        "surface": b.surface,
        "param_style": b.param_style,
        "binding_source": b.source,
    }
