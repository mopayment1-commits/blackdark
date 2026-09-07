"""Batch15 DeFi/Risk/Data facade layer — capabilities #701–#750.

CAP978 extension IDs delegate to canonical Batch09 DeFi/risk/data semantics (434–483)
and hero delegate #458 for Risk-to-Decision Intelligence (#725).
No execution endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.batch15_three_spec_foundations import attach_three_spec_metadata

logger = logging.getLogger("BLACKDARK.Batch15DeFiRiskDataFacade")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_batch15_defi_risk_data_state() -> None:
    return None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("batch15 seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."
    return "Analysis only — not financial advice, guarantee, or execution."


def _facade(
    cap_id: int,
    canonical_id: int,
    mod_path: str,
    fn_name: str,
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
    extra_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import importlib
    import inspect
    mod = importlib.import_module(mod_path)
    canonical_fn = getattr(mod, fn_name)
    call_kwargs: dict[str, Any] = dict(extra_kwargs or {})
    sig = inspect.signature(canonical_fn)
    if 'symbol' in sig.parameters:
        call_kwargs.setdefault('symbol', symbol)
    if seed is not None and 'seed' in sig.parameters:
        call_kwargs['seed'] = seed
    canonical = canonical_fn(**call_kwargs)
    payload = {
        **canonical,
        "ok": canonical.get("ok", True),
        "capability_id": cap_id,
        "canonical_reuse_of": canonical_id,
        "facade_layer": "batch15_defi_risk_data_facade",
        "attribution": f"BLACKDARK batch15 facade → {mod_path}.{fn_name}",
        "analysis_only": True,
        "no_execution": True,
    }
    attach_three_spec_metadata(payload, cap_id=cap_id)
    return payload


def revenue_fees_economic_activity_701(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Revenue / Fees / Economic Activity (#701) — canonical reuse of #434."""
    return _facade(
        701,
        434,
        "bd_platform.defi_yield_intelligence_layer",
        "revenue_fees_economic_activity_434",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def cross_market_research_copilot_702(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Market Research Copilot (#702) — canonical reuse of #435."""
    return _facade(
        702,
        435,
        "bd_platform.defi_yield_intelligence_layer",
        "cross_market_research_copilot_435",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def investment_thesis_scoring_703(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Investment Thesis Scoring (#703) — canonical reuse of #436."""
    return _facade(
        703,
        436,
        "bd_platform.defi_yield_intelligence_layer",
        "investment_thesis_scoring_436",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def defi_risk_radar_704(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DeFi Risk Radar (#704) — canonical reuse of #437."""
    return _facade(
        704,
        437,
        "bd_platform.defi_yield_intelligence_layer",
        "defi_risk_radar_437",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def lending_market_risk_705(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lending Market Risk (#705) — canonical reuse of #438."""
    return _facade(
        705,
        438,
        "bd_platform.defi_yield_intelligence_layer",
        "lending_market_risk_438",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def collateral_risk_706(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collateral Risk (#706) — canonical reuse of #439."""
    return _facade(
        706,
        439,
        "bd_platform.defi_yield_intelligence_layer",
        "collateral_risk_439",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def liquidation_risk_707(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquidation Risk (#707) — canonical reuse of #440."""
    return _facade(
        707,
        440,
        "bd_platform.defi_yield_intelligence_layer",
        "liquidation_risk_440",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def oracle_risk_708(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Oracle Risk (#708) — canonical reuse of #441."""
    return _facade(
        708,
        441,
        "bd_platform.defi_yield_intelligence_layer",
        "oracle_risk_441",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def liquidity_risk_709(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquidity Risk (#709) — canonical reuse of #442."""
    return _facade(
        709,
        442,
        "bd_platform.defi_yield_intelligence_layer",
        "liquidity_risk_442",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def protocol_exploit_intelligence_710(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Exploit Intelligence (#710) — canonical reuse of #443."""
    return _facade(
        710,
        443,
        "bd_platform.defi_yield_intelligence_layer",
        "protocol_exploit_intelligence_443",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def stablecoin_risk_intelligence_711(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Risk Intelligence (#711) — canonical reuse of #444."""
    return _facade(
        711,
        444,
        "bd_platform.defi_yield_intelligence_layer",
        "stablecoin_risk_intelligence_444",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def defi_strategy_risk_712(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DeFi Strategy Risk (#712) — canonical reuse of #445."""
    return _facade(
        712,
        445,
        "bd_platform.defi_yield_intelligence_layer",
        "defi_strategy_risk_445",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def real_time_risk_alerts_713(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Real-Time Risk Alerts (#713) — canonical reuse of #446."""
    return _facade(
        713,
        446,
        "bd_platform.defi_yield_intelligence_layer",
        "real_time_risk_alerts_446",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def dao_treasury_risk_714(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DAO Treasury Risk (#714) — canonical reuse of #447."""
    return _facade(
        714,
        447,
        "bd_platform.defi_yield_intelligence_layer",
        "dao_treasury_risk_447",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def institutional_risk_api_715(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional Risk API (#715) — canonical reuse of #448."""
    return _facade(
        715,
        448,
        "bd_platform.defi_yield_intelligence_layer",
        "institutional_risk_api_448",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def curated_on_chain_dashboards_716(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Curated On-Chain Dashboards (#716) — canonical reuse of #449."""
    return _facade(
        716,
        449,
        "bd_platform.defi_yield_intelligence_layer",
        "curated_on_chain_dashboards_449",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def narrative_driven_research_717(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Narrative-Driven Research (#717) — canonical reuse of #450."""
    return _facade(
        717,
        450,
        "bd_platform.defi_yield_intelligence_layer",
        "narrative_driven_research_450",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def protocol_dominance_718(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Dominance (#718) — canonical reuse of #451."""
    return _facade(
        718,
        451,
        "bd_platform.defi_yield_intelligence_layer",
        "protocol_dominance_451",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def aave_multi_chain_analytics_719(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Aave Multi-Chain Analytics (#719) — canonical reuse of #452."""
    return _facade(
        719,
        452,
        "bd_platform.defi_yield_intelligence_layer",
        "aave_multi_chain_analytics_452",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def risk_curation_720(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Risk Curation (#720) — canonical reuse of #453."""
    return _facade(
        720,
        453,
        "bd_platform.defi_yield_intelligence_layer",
        "risk_curation_453",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def capital_protection_controls_721(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Capital Protection Controls (#721) — canonical reuse of #454."""
    return _facade(
        721,
        454,
        "bd_platform.defi_yield_intelligence_layer",
        "capital_protection_controls_454",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def stress_testing_722(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stress Testing (#722) — canonical reuse of #455."""
    return _facade(
        722,
        455,
        "bd_platform.defi_yield_intelligence_layer",
        "stress_testing_455",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def cross_protocol_contagion_723(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Protocol Contagion (#723) — canonical reuse of #456."""
    return _facade(
        723,
        456,
        "bd_platform.defi_yield_intelligence_layer",
        "cross_protocol_contagion_456",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def protocol_risk_passport_724(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Protocol Risk Passport (#724) — canonical reuse of #457."""
    return _facade(
        724,
        457,
        "bd_platform.defi_yield_intelligence_layer",
        "protocol_risk_passport_457",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def risk_to_decision_intelligence_725(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Risk-to-Decision Intelligence (#725) — canonical reuse of #458."""
    return _facade(
        725,
        458,
        "bd_platform.heroes_capability_layer",
        "metric_methodology_registry_458",
        symbol=symbol,
        seed=seed,
        extra_kwargs={'locale': 'en'},
    )


def network_data_pro_metrics_726(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Network Data Pro Metrics (#726) — canonical reuse of #459."""
    return _facade(
        726,
        459,
        "bd_platform.defi_yield_intelligence_layer",
        "network_data_pro_metrics_459",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def atlas_blockchain_search_727(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Atlas Blockchain Search (#727) — canonical reuse of #460."""
    return _facade(
        727,
        460,
        "bd_platform.defi_yield_intelligence_layer",
        "atlas_blockchain_search_460",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def address_balance_search_728(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Address/Balance Search (#728) — canonical reuse of #461."""
    return _facade(
        728,
        461,
        "bd_platform.defi_yield_intelligence_layer",
        "address_balance_search_461",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def transaction_search_729(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Transaction Search (#729) — canonical reuse of #462."""
    return _facade(
        729,
        462,
        "bd_platform.defi_yield_intelligence_layer",
        "transaction_search_462",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def block_search_730(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Block Search (#730) — canonical reuse of #463."""
    return _facade(
        730,
        463,
        "bd_platform.defi_yield_intelligence_layer",
        "block_search_463",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def balance_updates_731(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Balance Updates (#731) — canonical reuse of #464."""
    return _facade(
        731,
        464,
        "bd_platform.defi_yield_intelligence_layer",
        "balance_updates_464",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def stablecoin_network_metrics_732(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stablecoin Network Metrics (#732) — canonical reuse of #465."""
    return _facade(
        732,
        465,
        "bd_platform.defi_yield_intelligence_layer",
        "stablecoin_network_metrics_465",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def market_data_feed_733(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Data Feed (#733) — canonical reuse of #466."""
    return _facade(
        733,
        466,
        "bd_platform.defi_yield_intelligence_layer",
        "market_data_feed_466",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def market_data_pro_734(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Data Pro (#734) — canonical reuse of #467."""
    return _facade(
        734,
        467,
        "bd_platform.defi_yield_intelligence_layer",
        "market_data_pro_467",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def reference_rates_735(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reference Rates (#735) — canonical reuse of #468."""
    return _facade(
        735,
        468,
        "bd_platform.defi_yield_intelligence_layer",
        "reference_rates_468",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def indexes_736(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Indexes (#736) — canonical reuse of #469."""
    return _facade(
        736,
        469,
        "bd_platform.defi_yield_intelligence_layer",
        "indexes_469",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def realized_metrics_737(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Realized Metrics (#737) — canonical reuse of #470."""
    return _facade(
        737,
        470,
        "bd_platform.defi_yield_intelligence_layer",
        "realized_metrics_470",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def supply_metrics_738(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Supply Metrics (#738) — canonical reuse of #471."""
    return _facade(
        738,
        471,
        "bd_platform.defi_yield_intelligence_layer",
        "supply_metrics_471",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def mining_validator_metrics_739(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mining/Validator Metrics (#739) — canonical reuse of #472."""
    return _facade(
        739,
        472,
        "bd_platform.defi_yield_intelligence_layer",
        "mining_validator_metrics_472",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def fee_metrics_740(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fee Metrics (#740) — canonical reuse of #473."""
    return _facade(
        740,
        473,
        "bd_platform.defi_yield_intelligence_layer",
        "fee_metrics_473",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def activity_metrics_741(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Activity Metrics (#741) — canonical reuse of #474."""
    return _facade(
        741,
        474,
        "bd_platform.defi_yield_intelligence_layer",
        "activity_metrics_474",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def custom_metric_workbench_742(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Custom Metric Workbench (#742) — canonical reuse of #475."""
    return _facade(
        742,
        475,
        "bd_platform.defi_yield_intelligence_layer",
        "custom_metric_workbench_475",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def community_charts_api_743(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Community Charts/API (#743) — canonical reuse of #476."""
    return _facade(
        743,
        476,
        "bd_platform.defi_yield_intelligence_layer",
        "community_charts_api_476",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def market_network_join_744(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market + Network Join (#744) — canonical reuse of #477."""
    return _facade(
        744,
        477,
        "bd_platform.defi_yield_intelligence_layer",
        "market_network_join_477",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def data_quality_methodologies_745(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Data Quality Methodologies (#745) — canonical reuse of #478."""
    return _facade(
        745,
        478,
        "bd_platform.defi_yield_intelligence_layer",
        "data_quality_methodologies_478",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def historical_research_dataset_746(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Historical Research Dataset (#746) — canonical reuse of #479."""
    return _facade(
        746,
        479,
        "bd_platform.defi_yield_intelligence_layer",
        "historical_research_dataset_479",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def institutional_apis_747(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional APIs (#747) — canonical reuse of #480."""
    return _facade(
        747,
        480,
        "bd_platform.defi_yield_intelligence_layer",
        "institutional_apis_480",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def cross_network_decision_intelligence_748(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Network Decision Intelligence (#748) — canonical reuse of #481."""
    return _facade(
        748,
        481,
        "bd_platform.defi_yield_intelligence_layer",
        "cross_network_decision_intelligence_481",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def institutional_trade_data_749(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional Trade Data (#749) — canonical reuse of #482."""
    return _facade(
        749,
        482,
        "bd_platform.defi_yield_intelligence_layer",
        "institutional_trade_data_482",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )


def order_book_data_750(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Order Book Data (#750) — canonical reuse of #483."""
    return _facade(
        750,
        483,
        "bd_platform.defi_yield_intelligence_layer",
        "order_book_data_483",
        symbol=symbol,
        seed=seed,
        extra_kwargs={},
    )

