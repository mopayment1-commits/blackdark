"""Batch14 Extension Analytics Layer — capabilities #651–#700.

978 extension analytics, research, DeFi fundamentals, and agent surfaces.
No execution endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.batch14_semantic_engine import compute_semantic_extra
from bd_platform.batch14_three_spec_foundations import attach_three_spec_metadata

logger = logging.getLogger("BLACKDARK.Batch14ExtensionAnalytics")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_batch14_extension_analytics_state() -> None:
    return None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("batch14 seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."
    return "Analysis only — not financial advice, guarantee, or execution."


def _base(
    cap_id: int,
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    payload = {
        "ok": True,
        "capability_id": cap_id,
        "symbol": symbol.upper(),
        "timestamp": _utcnow(),
        "disclaimer": _disclaimer(),
        "analysis_only": True,
        "no_execution": True,
    }
    if extra:
        payload.update(extra)
    attach_three_spec_metadata(payload, cap_id=cap_id)
    return payload


def tvl_intelligence_660(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """TVL Intelligence (#660) — canonical reuse of #354."""
    from bd_platform.charting_market_intelligence_layer import tvl_intelligence_354
    canonical = tvl_intelligence_354(symbol=symbol, seed=seed)
    return {
        **canonical,
        "capability_id": 660,
        "canonical_reuse_of": 354,
        "surface": "tvl_intelligence",
        "attribution": "BLACKDARK batch14 facade → charting layer #354",
    }

def chain_tvl_comparison_661(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Chain TVL Comparison (#661) — canonical reuse of #394."""
    from bd_platform.charting_market_intelligence_layer import chain_tvl_comparison_394
    canonical = chain_tvl_comparison_394(symbol=symbol, seed=seed)
    return {
        **canonical,
        "capability_id": 661,
        "canonical_reuse_of": 394,
        "surface": "chain_tvl_comparison",
        "attribution": "BLACKDARK batch14 facade → charting layer #394",
    }

def unlocks_676(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Unlocks (#676) — facade to token unlock forecaster #604 semantics."""
    from bd_platform.batch13_operational_intelligence_layer import token_unlock_forecaster_604
    canonical = token_unlock_forecaster_604(symbol=symbol, seed=seed)
    return {
        **canonical,
        "capability_id": 676,
        "canonical_reuse_of": 604,
        "surface": "unlocks",
    }

def data_lineage_656(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Data Lineage (#656)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(656, symbol=symbol, seed=seed, score_key='lineage_graph_nodes')
    return _base(
        656,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def query_performance_governance_657(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Query Performance Governance (#657)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(657, symbol=symbol, seed=seed, score_key='governance_score')
    return _base(
        657,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def white_label_embedded_analytics_658(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """White-Label Embedded Analytics (#658)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(658, symbol=symbol, seed=seed, score_key='embed_score')
    return _base(
        658,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def cross_domain_decision_layer_659(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Domain Decision Layer (#659)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(659, symbol=symbol, seed=seed, score_key='decision_score')
    return _base(
        659,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def api_aggregation_layer_682(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """API Aggregation Layer (#682)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(682, symbol=symbol, seed=seed, score_key='aggregation_score')
    return _base(
        682,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def ai_analyst_692(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """AI Analyst (#692)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(692, symbol=symbol, seed=seed, score_key='analyst_score')
    return _base(
        692,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def excel_sheets_integration_695(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Excel / Sheets Integration (#695)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(695, symbol=symbol, seed=seed, score_key='integration_score')
    return _base(
        695,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def api_data_platform_696(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """API Data Platform (#696)."""
    seed = seed or _load_seed()
    from bd_platform.batch14_three_spec_foundations import build_special_surface
    extra = build_special_surface(696, symbol=symbol, seed=seed, score_key='platform_score')
    return _base(
        696,
        symbol=symbol,
        seed=seed,
        extra=extra,
    )

def mcp_for_ai_agents_651(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """MCP for AI Agents (#651)."""
    seed = seed or _load_seed()
    return _base(
        651,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(651, symbol=symbol, seed=seed),
    )

def prompt_to_sql_agent_652(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prompt-to-SQL Agent (#652)."""
    seed = seed or _load_seed()
    return _base(
        652,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(652, symbol=symbol, seed=seed),
    )

def dashboard_from_prompt_653(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dashboard-from-Prompt (#653)."""
    seed = seed or _load_seed()
    return _base(
        653,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(653, symbol=symbol, seed=seed),
    )

def scheduled_queries_654(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Scheduled Queries (#654)."""
    seed = seed or _load_seed()
    return _base(
        654,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(654, symbol=symbol, seed=seed),
    )

def alerts_from_query_results_655(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Alerts from Query Results (#655)."""
    seed = seed or _load_seed()
    return _base(
        655,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(655, symbol=symbol, seed=seed),
    )

def protocol_directory_662(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Directory (#662)."""
    seed = seed or _load_seed()
    return _base(
        662,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(662, symbol=symbol, seed=seed),
    )

def fees_revenue_663(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fees & Revenue (#663)."""
    seed = seed or _load_seed()
    return _base(
        663,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(663, symbol=symbol, seed=seed),
    )

def dex_volume_664(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DEX Volume (#664)."""
    seed = seed or _load_seed()
    return _base(
        664,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(664, symbol=symbol, seed=seed),
    )

def perps_volume_665(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Perps Volume (#665)."""
    seed = seed or _load_seed()
    return _base(
        665,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(665, symbol=symbol, seed=seed),
    )

def options_volume_666(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Options Volume (#666)."""
    seed = seed or _load_seed()
    return _base(
        666,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(666, symbol=symbol, seed=seed),
    )

def stablecoins_intelligence_667(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoins Intelligence (#667)."""
    seed = seed or _load_seed()
    return _base(
        667,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(667, symbol=symbol, seed=seed),
    )

def bridges_intelligence_668(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bridges Intelligence (#668)."""
    seed = seed or _load_seed()
    return _base(
        668,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(668, symbol=symbol, seed=seed),
    )

def yields_screener_669(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Yields Screener (#669)."""
    seed = seed or _load_seed()
    return _base(
        669,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(669, symbol=symbol, seed=seed),
    )

def yield_history_670(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Yield History (#670)."""
    seed = seed or _load_seed()
    return _base(
        670,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(670, symbol=symbol, seed=seed),
    )

def borrowing_rates_671(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Borrowing Rates (#671)."""
    seed = seed or _load_seed()
    return _base(
        671,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(671, symbol=symbol, seed=seed),
    )

def liquid_staking_intelligence_672(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquid Staking Intelligence (#672)."""
    seed = seed or _load_seed()
    return _base(
        672,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(672, symbol=symbol, seed=seed),
    )

def rwa_intelligence_673(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """RWA Intelligence (#673)."""
    seed = seed or _load_seed()
    return _base(
        673,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(673, symbol=symbol, seed=seed),
    )

def raises_funding_rounds_674(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Raises / Funding Rounds (#674)."""
    seed = seed or _load_seed()
    return _base(
        674,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(674, symbol=symbol, seed=seed),
    )

def investor_profiles_675(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Investor Profiles (#675)."""
    seed = seed or _load_seed()
    return _base(
        675,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(675, symbol=symbol, seed=seed),
    )

def treasury_intelligence_677(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Treasury Intelligence (#677)."""
    seed = seed or _load_seed()
    return _base(
        677,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(677, symbol=symbol, seed=seed),
    )

def airdrop_incentive_intelligence_678(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Airdrop / Incentive Intelligence (#678)."""
    seed = seed or _load_seed()
    return _base(
        678,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(678, symbol=symbol, seed=seed),
    )

def capital_formation_radar_679(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Capital Formation Radar (#679)."""
    seed = seed or _load_seed()
    return _base(
        679,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(679, symbol=symbol, seed=seed),
    )

def defi_opportunity_screener_680(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DeFi Opportunity Screener (#680)."""
    seed = seed or _load_seed()
    return _base(
        680,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(680, symbol=symbol, seed=seed),
    )

def defi_risk_passport_681(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DeFi Risk Passport (#681)."""
    seed = seed or _load_seed()
    return _base(
        681,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(681, symbol=symbol, seed=seed),
    )

def cross_defi_decision_intelligence_683(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-DeFi Decision Intelligence (#683)."""
    seed = seed or _load_seed()
    return _base(
        683,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(683, symbol=symbol, seed=seed),
    )

def cross_chain_fundamentals_684(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Chain Fundamentals (#684)."""
    seed = seed or _load_seed()
    return _base(
        684,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(684, symbol=symbol, seed=seed),
    )

def protocol_fundamentals_685(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Fundamentals (#685)."""
    seed = seed or _load_seed()
    return _base(
        685,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(685, symbol=symbol, seed=seed),
    )

def stablecoin_intelligence_686(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Intelligence (#686)."""
    seed = seed or _load_seed()
    return _base(
        686,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(686, symbol=symbol, seed=seed),
    )

def stablecoin_activity_breakdown_687(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Activity Breakdown (#687)."""
    seed = seed or _load_seed()
    return _base(
        687,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(687, symbol=symbol, seed=seed),
    )

def developer_activity_688(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Developer Activity (#688)."""
    seed = seed or _load_seed()
    return _base(
        688,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(688, symbol=symbol, seed=seed),
    )

def sector_ecosystem_comparables_689(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sector/Ecosystem Comparables (#689)."""
    seed = seed or _load_seed()
    return _base(
        689,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(689, symbol=symbol, seed=seed),
    )

def equities_crypto_research_690(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Equities + Crypto Research (#690)."""
    seed = seed or _load_seed()
    return _base(
        690,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(690, symbol=symbol, seed=seed),
    )

def consensus_estimates_691(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Consensus Estimates (#691)."""
    seed = seed or _load_seed()
    return _base(
        691,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(691, symbol=symbol, seed=seed),
    )

def thesis_research_workspace_693(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Thesis Research Workspace (#693)."""
    seed = seed or _load_seed()
    return _base(
        693,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(693, symbol=symbol, seed=seed),
    )

def comparable_company_protocol_analysis_694(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Comparable Company / Protocol Analysis (#694)."""
    seed = seed or _load_seed()
    return _base(
        694,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(694, symbol=symbol, seed=seed),
    )

def research_templates_697(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Research Templates (#697)."""
    seed = seed or _load_seed()
    return _base(
        697,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(697, symbol=symbol, seed=seed),
    )

def dashboards_698(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dashboards (#698)."""
    seed = seed or _load_seed()
    return _base(
        698,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(698, symbol=symbol, seed=seed),
    )

def stablecoin_payment_intelligence_699(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Payment Intelligence (#699)."""
    seed = seed or _load_seed()
    return _base(
        699,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(699, symbol=symbol, seed=seed),
    )

def on_chain_usage_intelligence_700(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """On-Chain Usage Intelligence (#700)."""
    seed = seed or _load_seed()
    return _base(
        700,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(700, symbol=symbol, seed=seed),
    )

