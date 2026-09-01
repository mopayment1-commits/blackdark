"""Institutional backend bindings — one semantic module per CAP646 capability."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from cap646.catalog import catalog_by_id, matrix_by_id

_GENERIC_SURFACES = frozenset({"platform_codepath", "generic", "unknown"})


@dataclass(frozen=True)
class BackendBinding:
    capability_id: int
    module: str
    entrypoint: str
    surface: str
    param_style: str = "symbol"  # symbol | none | address | quote
    source: str = "track_default"


# Option A — explicit production bindings (not pdf_registry / audit layer)
_EXPLICIT_BINDINGS: dict[int, BackendBinding] = {
    338: BackendBinding(
        338,
        "cap646.data_spine",
        "data_quality_pipeline_report",
        "data_quality_pipeline",
        "none",
        "explicit_option_a",
    ),
    500: BackendBinding(
        500,
        "cap646.data_spine",
        "normalization_report",
        "data_quality_normalization",
        "symbol",
        "explicit_option_a",
    ),
    507: BackendBinding(
        507,
        "cap646.fallbacks",
        "resolve_ohlcv_closes",
        "ohlcv",
        "symbol",
        "explicit_option_a",
    ),
    534: BackendBinding(
        534,
        "cap646.data_spine",
        "bucketed_cvd_report",
        "bucketed_cvd",
        "symbol",
        "explicit_option_a",
    ),
    69: BackendBinding(
        69,
        "cap646.handlers.onchain",
        "handle_onchain_capability",
        "cross_domain_decision_intelligence_layer",
        "symbol",
        "canonical_handler_post_batch02_merge",
    ),
}


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "capability"


def _register_batch01_bindings() -> None:
    from cap646.batch01_production import BATCH01_IDS, batch01_entrypoint

    for cid in BATCH01_IDS:
        if cid in _EXPLICIT_BINDINGS:
            continue
        row = catalog_by_id().get(cid, {})
        surface = _slug(row.get("capability", f"cap_{cid}"))
        _EXPLICIT_BINDINGS[cid] = BackendBinding(
            cid,
            "cap646.batch01_production",
            batch01_entrypoint(cid),
            surface,
            "symbol",
            "explicit_option_a",
        )


_register_batch01_bindings()


def _register_batch02_bindings() -> None:
    from cap646.batch02_production import BATCH02_IDS, batch02_entrypoint

    for cid in BATCH02_IDS:
        if cid in _EXPLICIT_BINDINGS:
            continue
        row = catalog_by_id().get(cid, {})
        surface = _slug(row.get("capability", f"cap_{cid}"))
        _EXPLICIT_BINDINGS[cid] = BackendBinding(
            cid,
            "cap646.batch02_production",
            batch02_entrypoint(cid),
            surface,
            "symbol",
            "explicit_option_a",
        )


_register_batch02_bindings()


# Map gap-matrix component stems → canonical import path + entrypoint
_COMPONENT_BINDINGS: dict[str, tuple[str, str, str]] = {
    "market_context.py": ("market_context", "probe_price_sources", "symbol"),
    "live_book_hub.py": ("live_book_hub", "hub_stats", "none"),
    "ccxt_market_fetcher.py": ("market_context", "fetch_binance_ticker", "pair"),
    "market_cache.py": ("market_cache", "cache_stats", "none"),
    "whale_tracker.py": ("whale_tracker", "get_latest_whale_alerts", "limit"),
    "onchain_tracker.py": ("onchain_tracker", "build_onchain_context_safe", "none"),
    "gas_oracle.py": ("cap646.fallbacks", "resolve_gas_usd", "chain"),
    "data_provenance_score.py": ("data_provenance_score", "compute_data_provenance_score", "symbol"),
    "data_lake.py": ("data_lake", "lake_status", "none"),
    "hot_storage.py": ("hot_storage", "get_hot_storage_stats", "none"),
    "arbitrage_service.py": ("arbitrage_service", "scan_arbitrage_opportunities", "quote"),
    "arbitrage_engine.py": ("arbitrage_service", "scan_arbitrage_opportunities", "quote"),
    "execution_engine.py": ("execution_engine", "get_execution_status", "none"),
    "risk_manager.py": ("risk_manager", "risk_status", "none"),
    "options_fetcher.py": ("options_fetcher", "fetch_options_overview", "symbols"),
    "perp_dex_fetcher.py": ("cap646.fallbacks", "resolve_dex_volume_snapshot", "symbol"),
    "trust_pulse.py": ("trust_pulse", "build_trust_pulse", "symbol_tier"),
    "sentiment_engine.py": ("sentiment_engine", "build_sentiment_context_safe", "symbol"),
    "sentiment_gate.py": ("sentiment_gate", "fetch_asset_sentiment", "symbol"),
    "instant_alert_engine.py": ("instant_alert_engine", "engine_stats", "none"),
    "in_app_alerts.py": ("in_app_alerts", "inbox_stats", "email"),
    "ai_oracle.py": ("ai_oracle", "evaluate_opportunity", "opportunity"),
    "decision_certificate.py": ("decision_certificate", "build_decision_certificate", "cert"),
    "oracle_track_record.py": ("oracle_track_record", "public_track_record", "none"),
    "oracle_integrity.py": ("oracle_audit_chain", "verify_chain", "none"),
    "product_honesty_api.py": ("product_honesty_api", "build_public_readiness", "none"),
    "graphql_schema.py": ("graphql_schema", "graphql_health", "none"),
    "scale_readiness.py": ("scale_readiness", "scale_readiness_report", "none"),
    "security_posture.py": ("security_posture", "security_posture_report", "none"),
    "org_rbac.py": ("org_rbac", "role_matrix", "none"),
    "org_tenant.py": ("org_tenant", "org_isolation_status", "none"),
    "bd_platform/derivatives_hub.py": ("bd_platform.derivatives_hub", "derivatives_overview", "symbol"),
    "bd_platform/onchain_hub.py": ("bd_platform.onchain_hub", "dexscreener_pairs", "symbol"),
    "bd_platform/liquidation_radar.py": ("bd_platform.liquidation_radar", "liquidation_radar", "symbol"),
    "bd_platform/market_rankings.py": ("bd_platform.market_rankings", "market_rankings", "none"),
    "bd_platform/news_classifier.py": ("bd_platform.news_classifier", "coindesk_feed", "none"),
    "bd_platform/footprint_analytics.py": ("bd_platform.footprint_analytics", "footprint_snapshot", "symbol"),
    "bd_platform/portfolio_rebalancer.py": ("bd_platform.portfolio_rebalancer", "suggest_rebalance", "none"),
    "bd_platform/grid_bot.py": ("bd_platform.grid_bot", "list_grids", "none"),
    "bd_platform/whale_story.py": ("bd_platform.whale_story", "whale_narrative", "symbol"),
    "bd_platform/token_unlocks.py": ("bd_platform.token_unlocks", "unlock_calendar", "none"),
    "bd_platform/public_proof.py": ("bd_platform.public_proof", "build_public_proof", "none"),
    "bd_platform/tradingview_bridge.py": ("bd_platform.tradingview_bridge", "chart_config", "none"),
    "bd_platform/trulens_eval.py": ("bd_platform.trulens_eval", "explain_prediction", "symbol"),
    "bd_platform/ifttt_rules.py": ("bd_platform.ifttt_rules", "list_rules", "none"),
    "bd_platform/telegram_agent.py": ("bd_platform.telegram_agent", "handle_agent_message", "message"),
    "bd_platform/infra_status.py": ("bd_platform.infra_status", "infra_matrix", "none"),
    "ml/market_replay_bootstrap.py": ("ml.market_replay_bootstrap", "bootstrap_market_replay_dataset", "assets"),
    "due_diligence_bundle.py": ("due_diligence_bundle", "build_full_due_diligence_bundle", "none"),
    "acquirer_evidence_pack.py": ("acquirer_evidence_pack", "build_acquirer_evidence_pack", "none"),
    "signal_registry.py": ("signal_registry", "registry_stats", "none"),
    "decision_ledger.py": ("decision_ledger", "ledger_stats", "none"),
    "user_exposure_log.py": ("user_exposure_log", "exposure_stats", "none"),
    "market_event_library.py": ("market_event_library", "event_library_stats", "none"),
    "failure_corpus.py": ("failure_corpus", "corpus_stats", "none"),
    "platform_chain_e2e.py": ("platform_chain_e2e", "run_platform_compounding_e2e", "symbol"),
    "fee_matrix.py": ("fee_matrix", "matrix_stats", "none"),
    "net_edge_truth.py": ("net_edge_truth", "compute_net_edge_truth", "edge"),
    "production_guard.py": ("production_guard", "evaluate_production_guard", "none"),
    "ingestion_scheduler.py": ("ingestion_scheduler", "scheduler_running", "none"),
    "feed_lag_scanner.py": ("feed_lag_scanner", "scan_feed_lag_from_books", "books"),
    "stale_price_guard.py": ("stale_price_guard", "guard_enabled", "none"),
    "parquet_compactor.py": ("data_lake", "lake_status", "none"),
    "binance_ws_ingest.py": ("ingestion_scheduler", "scheduler_running", "none"),
    "storage_tier_manager.py": ("hot_storage", "get_hot_storage_stats", "none"),
    "defi_arbitrage_engine.py": ("defi_arbitrage_engine", "defi_engine_stats", "none"),
    "b2b_websocket_hub.py": ("b2b_websocket_hub", "get_b2b_ws_hub", "hub"),
    "billing_service.py": ("billing_service", "billing_configured", "none"),
    "user_keys_service.py": ("product_honesty_api", "build_public_readiness", "none"),
    "auth_service.py": ("security_posture", "security_posture_report", "none"),
    "graphql_schema.py": ("product_honesty_api", "build_public_readiness", "none"),
}


_TRACK_DEFAULTS: dict[str, tuple[str, str, str]] = {
    "T01": ("scale_readiness", "scale_readiness_report", "none"),
    "T02": ("security_posture", "security_posture_report", "none"),
    "T03": ("data_provenance_score", "compute_data_provenance_score", "symbol"),
    "T04": ("market_context", "probe_price_sources", "symbol"),
    "T05": ("bd_platform.derivatives_hub", "derivatives_overview", "symbol"),
    "T06": ("arbitrage_service", "scan_arbitrage_opportunities", "quote"),
    "T07": ("bd_platform.portfolio_rebalancer", "portfolio_snapshot", "symbol"),
    "T08": ("bd_platform.derivatives_hub", "derivatives_overview", "symbol"),
    "T09": ("onchain_tracker", "build_onchain_context_safe", "none"),
    "T10": ("bd_platform.onchain_hub", "defillama_raises", "none"),
    "T11": ("blackdark.canonical.layer", "get_canonical_layer", "none"),
    "T12": ("trust_pulse", "build_trust_pulse", "symbol_tier"),
    "T13": ("instant_alert_engine", "engine_stats", "none"),
    "T14": ("product_honesty_api", "build_public_readiness", "none"),
    "T15": ("product_honesty_api", "build_public_readiness", "none"),
    "T16": ("org_tenant", "org_isolation_status", "none"),
    "T17": ("oracle_track_record", "public_track_record", "none"),
    "T18": ("product_honesty_api", "build_capability_inventory", "none"),
}


_KEYWORD_RULES: tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...] = (
    (("whale", "smart money"), ("whale_tracker", "get_latest_whale_alerts", "limit")),
    (("narrative", "story"), ("bd_platform.whale_story", "whale_narrative", "symbol")),
    (("sentiment", "social"), ("sentiment_engine", "build_sentiment_context_safe", "symbol")),
    (("news", "headline"), ("bd_platform.news_classifier", "coindesk_feed", "none")),
    (("arbitrage", "arb"), ("arbitrage_service", "scan_arbitrage_opportunities", "quote")),
    (("liquidation", "cascade"), ("bd_platform.liquidation_radar", "liquidation_radar", "symbol")),
    (("funding", "perp", "futures", "open interest"), ("bd_platform.derivatives_hub", "derivatives_overview", "symbol")),
    (("options", "deribit"), ("options_fetcher", "fetch_options_overview", "symbols")),
    (("portfolio", "rebalance", "allocation", "holding", "balance"), ("bd_platform.portfolio_rebalancer", "portfolio_snapshot", "symbol")),
    (("grid bot", "grid trading"), ("bd_platform.grid_bot", "list_grids", "none")),
    (("alert", "notification"), ("instant_alert_engine", "engine_stats", "none")),
    (("gas", "fee"), ("cap646.fallbacks", "resolve_gas_usd", "chain")),
    (("wallet", "debank"), ("bd_platform.onchain_hub", "debank_wallet", "address")),
    (("tvl", "defi", "yield", "stablecoin"), ("bd_platform.onchain_hub", "defillama_raises", "none")),
    (("dex", "gecko", "pair"), ("bd_platform.onchain_hub", "dexscreener_pairs", "symbol")),
    (("macro", "mvrv", "sopr", "cycle"), ("bd_platform.onchain_hub", "lookintobitcoin_macro", "none")),
    (("asset metadata", "canonical id", "canonical asset"), ("blackdark.canonical.resolver", "resolve_asset", "symbol")),
    (("canonical data", "data normalization", "reference data"), ("blackdark.canonical.layer", "get_canonical_layer", "none")),
    (("coingecko", "coin gecko"), ("blackdark.ingestion.coingecko_connector", "fetch_coingecko_price", "symbol")),
    (("alternative.me", "fear greed", "fear & greed"), ("blackdark.ingestion.alternative_me_connector", "fetch_fear_greed_index", "none")),
    (("arkham", "entity intelligence"), ("blackdark.ingestion.arkham_connector", "fetch_entity_intelligence_input", "symbol")),
    (("alpha engine", "multi-factor alpha"), ("bd_platform.alpha_engine", "compute_alpha_signal", "symbol")),
    (("data ingestion", "ingestion layer"), ("blackdark.ingestion.coingecko_connector", "run_coingecko_primary_ingest", "none")),
    (("mvrv", "realignment", "z-score"), ("bd_platform.mvrv_realignment", "compute_mvrv_realignment", "symbol")),
    (("multi-factor", "alpha rank", "alpha ranking"), ("bd_platform.alpha_factor_ranking", "rank_assets_by_alpha_factors", "none")),
    (("squeeze", "trigger", "liquidation cluster"), ("bd_platform.squeeze_trigger_engine", "squeeze_trigger_coordinates", "symbol")),
    (("slippage tolerance", "self-optimization", "slippage optimize", "slippage intelligence"), ("bd_platform.slippage_tolerance_optimizer", "optimize_slippage_tolerance", "symbol")),
    (("asymmetric slippage", "directional slippage", "buy sell slippage"), ("bd_platform.slippage_tolerance_optimizer", "compute_asymmetric_slippage_cost", "symbol")),
    (("intelligence ledger", "execution intelligence", "best execution"), ("bd_platform.intelligence_ledger", "build_execution_intelligence", "symbol")),
    (("address intelligence", "address search", "wallet search", "balance history", "balance updates"), ("bd_platform.address_intelligence", "address_intelligence_overview", "address")),
    (("1inch", "dex aggregator"), ("bd_platform.oneinch_connector", "fetch_oneinch_quote", "symbol")),
    (("ranking", "marketcap"), ("bd_platform.market_rankings", "market_rankings", "none")),
    (("footprint", "order flow"), ("bd_platform.footprint_analytics", "footprint_snapshot", "symbol")),
    (("chart", "tradingview"), ("bd_platform.tradingview_bridge", "chart_config", "none")),
    (("proof", "merkle", "audit chain"), ("bd_platform.public_proof", "build_public_proof", "none")),
    (("tax", "due diligence", "report pack"), ("due_diligence_bundle", "build_full_due_diligence_bundle", "none")),
    (("prediction", "oracle", "decision"), ("trust_pulse", "build_trust_pulse", "symbol_tier")),
    (("provenance", "quality", "lineage"), ("data_provenance_score", "compute_data_provenance_score", "symbol")),
    (("storage", "lake", "hot tier"), ("data_lake", "lake_status", "none")),
    (("security", "encryption", "vault"), ("security_posture", "security_posture_report", "none")),
    (("billing", "subscription"), ("billing_service", "billing_status", "none")),
    (("tenant", "rbac", "org"), ("org_tenant", "org_isolation_status", "none")),
    (("graphql", "api platform"), ("graphql_schema", "graphql_health", "none")),
    (("backtest", "replay"), ("ml.market_replay_bootstrap", "bootstrap_market_replay_dataset", "assets")),
    (("risk", "hedge", "stress"), ("risk_manager", "risk_status", "none")),
    (("unlock", "vesting"), ("bd_platform.token_unlocks", "unlock_calendar", "none")),
    (("telegram", "agent"), ("bd_platform.telegram_agent", "handle_agent_message", "message")),
    (("ifttt", "rule"), ("bd_platform.ifttt_rules", "list_rules", "none")),
    (("strategy marketplace", "marketplace"), ("bd_platform.strategy_marketplace", "list_strategies", "none")),
)


def _keyword_binding(name: str) -> tuple[str, str, str] | None:
    nl = name.lower()
    for keys, binding in _KEYWORD_RULES:
        if any(k in nl for k in keys):
            return binding
    return None


def _component_binding(components: list[str]) -> tuple[str, str, str] | None:
    for raw in components:
        stem = raw.strip()
        if stem in _COMPONENT_BINDINGS:
            return _COMPONENT_BINDINGS[stem]
        base = stem.split("/")[-1]
        if base in _COMPONENT_BINDINGS:
            return _COMPONENT_BINDINGS[base]
    return None


@lru_cache(maxsize=646)
def resolve_binding(capability_id: int) -> BackendBinding:
    explicit = _EXPLICIT_BINDINGS.get(capability_id)
    if explicit is not None:
        return explicit

    row = catalog_by_id()[capability_id]
    matrix = matrix_by_id().get(capability_id, {})
    name = row["capability"]
    track = row["track"]
    surface = _slug(name)

    comp = _component_binding(matrix.get("existing_code_components") or [])
    if comp:
        mod, ep, ps = comp
        return BackendBinding(capability_id, mod, ep, surface, ps, "gap_matrix_component")

    kw = _keyword_binding(name)
    if kw:
        mod, ep, ps = kw
        return BackendBinding(capability_id, mod, ep, surface, ps, "capability_keyword")

    mod, ep, ps = _TRACK_DEFAULTS.get(track, _TRACK_DEFAULTS["T04"])
    return BackendBinding(capability_id, mod, ep, surface, ps, "track_default")


def binding_for(capability_id: int) -> dict[str, Any]:
    b = resolve_binding(capability_id)
    return {
        "capability_id": b.capability_id,
        "backend_module": b.module,
        "backend_entrypoint": b.entrypoint,
        "surface": b.surface,
        "param_style": b.param_style,
        "binding_source": b.source,
    }


def is_generic_surface(surface: str | None) -> bool:
    return (surface or "") in _GENERIC_SURFACES
