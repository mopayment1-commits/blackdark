"""Batch13 Operational Intelligence Layer — capabilities #601–#650.

Insight-only operational, on-chain, derivatives, and trust surfaces.
No execution endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.batch13_semantic_engine import compute_semantic_extra

logger = logging.getLogger("BLACKDARK.Batch13OperationalIntel")

_EXTERNAL_DEPENDENCY_DEFAULT = "External dependency"
_EXTERNAL_INTERNAL_ACTION = "none — requires external provisioning"

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_batch13_operational_intelligence_state() -> None:
    return None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("batch13 seed load failed: %s", exc)
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
    return payload


def visual_transaction_graph_601(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Visual_Transaction_Graph (#601)."""
    seed = seed or _load_seed()
    return _base(
        601,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(601, symbol=symbol, seed=seed),
    )

def developer_wallet_tracker_602(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Developer_Wallet_Tracker (#602)."""
    seed = seed or _load_seed()
    return _base(
        602,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(602, symbol=symbol, seed=seed),
    )

def miner_flow_monitor_603(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Miner_Flow_Monitor (#603)."""
    seed = seed or _load_seed()
    return _base(
        603,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(603, symbol=symbol, seed=seed),
    )

def token_unlock_forecaster_604(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Token_Unlock_Forecaster (#604)."""
    seed = seed or _load_seed()
    return _base(
        604,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(604, symbol=symbol, seed=seed),
    )

def governance_sentiment_monitor_605(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Governance_Sentiment_Monitor (#605)."""
    seed = seed or _load_seed()
    return _base(
        605,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(605, symbol=symbol, seed=seed),
    )

def dev_health_score_606(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dev_Health_Score (#606)."""
    seed = seed or _load_seed()
    return _base(
        606,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(606, symbol=symbol, seed=seed),
    )

def financial_health_scoring_607(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Financial_Health_Scoring (#607)."""
    seed = seed or _load_seed()
    return _base(
        607,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(607, symbol=symbol, seed=seed),
    )

def custom_ratio_engine_608(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Custom_Ratio_Engine (#608)."""
    seed = seed or _load_seed()
    return _base(
        608,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(608, symbol=symbol, seed=seed),
    )

def funding_rate_listener_609(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Funding_Rate_Listener (#609)."""
    seed = seed or _load_seed()
    return _base(
        609,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(609, symbol=symbol, seed=seed),
    )

def funding_arbitrage_engine_610(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Funding_Arbitrage_Engine (#610)."""
    seed = seed or _load_seed()
    return _base(
        610,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(610, symbol=symbol, seed=seed),
    )

def funding_rate_heatmap_engine_611(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Funding_Rate_Heatmap_Engine (#611)."""
    seed = seed or _load_seed()
    return _base(
        611,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(611, symbol=symbol, seed=seed),
    )

def spread_calculation_engine_612(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Spread_Calculation_Engine (#612)."""
    seed = seed or _load_seed()
    return _base(
        612,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(612, symbol=symbol, seed=seed),
    )

async def liquidation_screener_613(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquidation_Screener (#613) — facade delegating to canonical #88 semantics."""
    from cap646.batch02_production import cap_088

    seed = seed or _load_seed()
    canonical = await cap_088(symbol=symbol, params={"symbol": symbol})
    semantic = compute_semantic_extra(613, symbol=symbol, seed=seed)
    return _base(
        613,
        symbol=symbol,
        seed=seed,
        extra={
            "canonical_reuse_of": 88,
            "surface": canonical.get("surface"),
            "liquidation": canonical.get("liquidation"),
            "underlying": canonical,
            "screener_semantic": semantic,
            **semantic,
        },
    )

def dex_liquidity_listener_614(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """DEX_Liquidity_Listener (#614)."""
    seed = seed or _load_seed()
    return _base(
        614,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(614, symbol=symbol, seed=seed),
    )

def gas_cost_predictor_615(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Gas_Cost_Predictor (#615)."""
    seed = seed or _load_seed()
    return _base(
        615,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(615, symbol=symbol, seed=seed),
    )

def yield_delta_listener_616(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Yield_Delta_Listener (#616)."""
    seed = seed or _load_seed()
    return _base(
        616,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(616, symbol=symbol, seed=seed),
    )

def yield_arbitrage_engine_617(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Yield_Arbitrage_Engine (#617)."""
    seed = seed or _load_seed()
    return _base(
        617,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(617, symbol=symbol, seed=seed),
    )

def yield_optimization_module_618(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Yield_Optimization_Module (#618)."""
    seed = seed or _load_seed()
    return _base(
        618,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(618, symbol=symbol, seed=seed),
    )

def trend_metric_collector_619(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Trend_Metric_Collector (#619)."""
    seed = seed or _load_seed()
    return _base(
        619,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(619, symbol=symbol, seed=seed),
    )

def mtf_core_logic_620(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """MTF_Core_Logic (#620)."""
    seed = seed or _load_seed()
    return _base(
        620,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(620, symbol=symbol, seed=seed),
    )

def pattern_recognition_engine_621(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pattern_Recognition_Engine (#621)."""
    seed = seed or _load_seed()
    return _base(
        621,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(621, symbol=symbol, seed=seed),
    )

def prediction_trend_analyzer_622(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prediction_Trend_Analyzer (#622)."""
    seed = seed or _load_seed()
    return _base(
        622,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(622, symbol=symbol, seed=seed),
    )

def execution_latency_monitor_623(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execution_Latency_Monitor (#623)."""
    seed = seed or _load_seed()
    return _base(
        623,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(623, symbol=symbol, seed=seed),
    )

def low_latency_execution_node_624(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Low_Latency_Execution_Node (#624)."""
    seed = seed or _load_seed()
    return _base(
        624,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(624, symbol=symbol, seed=seed),
    )

def rust_execution_module_625(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Rust_Execution_Module (#625)."""
    seed = seed or _load_seed()
    return _base(
        625,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(625, symbol=symbol, seed=seed),
    )

def institutional_dashboard_626(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional_Dashboard (#626)."""
    seed = seed or _load_seed()
    return _base(
        626,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(626, symbol=symbol, seed=seed),
    )

def viral_intelligence_distribution_loop_628(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Viral_Intelligence_Distribution_Loop (#628)."""
    seed = seed or _load_seed()
    return _base(
        628,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(628, symbol=symbol, seed=seed),
    )

def multi_tier_data_storage_632(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Multi-Tier Data Storage (#632)."""
    seed = seed or _load_seed()
    return _base(
        632,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(632, symbol=symbol, seed=seed),
    )

def cross_chain_liquidity_flow_633(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-Chain Liquidity Flow (#633)."""
    seed = seed or _load_seed()
    return _base(
        633,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(633, symbol=symbol, seed=seed),
    )

def liquidity_full_fill_feasibility_634(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquidity/Full-Fill Feasibility (#634)."""
    seed = seed or _load_seed()
    return _base(
        634,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(634, symbol=symbol, seed=seed),
    )

def unified_arbitrage_opportunity_engine_635(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Unified Arbitrage Opportunity Engine (#635)."""
    seed = seed or _load_seed()
    return _base(
        635,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(635, symbol=symbol, seed=seed),
    )

def market_data_drift_monitoring_636(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market/Data Drift Monitoring (#636)."""
    seed = seed or _load_seed()
    return _base(
        636,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(636, symbol=symbol, seed=seed),
    )

def end_to_end_decision_traceability_643(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """End-to-End Decision Traceability (#643)."""
    seed = seed or _load_seed()
    return _base(
        643,
        symbol=symbol,
        seed=seed,
        extra=compute_semantic_extra(643, symbol=symbol, seed=seed),
    )

async def scenario_engine_637(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Scenario Engine (#637) — catalog-aligned semantics."""
    from trust_pulse import build_trust_pulse

    seed = seed or _load_seed()
    underlying = await build_trust_pulse(symbol=symbol)
    return _base(
        637,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "scenario_engine",
            "feature": "Scenario Engine",
            "attribution": "trust_pulse.build_trust_pulse",
            "formula_visible": True,
            "scenario_engine": underlying,
            "underlying": underlying,
        },
    )

def claims_prediction_verification_638(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Claims/Prediction Verification Engine (#638) — catalog-aligned semantics."""
    from oracle_track_record import public_track_record
    seed = seed or _load_seed()
    underlying = public_track_record()
    return _base(
        638,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "claims_prediction_verification_engine",
            "feature": "Claims/Prediction Verification Engine",
            "attribution": "oracle_track_record.public_track_record",
            "formula_visible": True,
            "claims_prediction_verification_engine": underlying,
            "underlying": underlying,
        },
    )

def net_edge_truth_score_639(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Net-Edge Truth Score (#639) — catalog-aligned semantics."""
    from net_edge_truth import compute_net_edge_truth
    seed = seed or _load_seed()
    underlying = compute_net_edge_truth()
    return _base(
        639,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "net_edge_truth_score",
            "feature": "Net-Edge Truth Score",
            "attribution": "net_edge_truth.compute_net_edge_truth",
            "formula_visible": True,
            "net_edge_truth_score": underlying,
            "underlying": underlying,
        },
    )

def public_accuracy_ledger_640(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Public Accuracy Ledger (#640) — catalog-aligned semantics."""
    from oracle_track_record import public_track_record
    seed = seed or _load_seed()
    underlying = public_track_record()
    return _base(
        640,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "public_accuracy_ledger",
            "feature": "Public Accuracy Ledger",
            "attribution": "oracle_track_record.public_track_record",
            "formula_visible": True,
            "public_accuracy_ledger": underlying,
            "underlying": underlying,
        },
    )

def decision_certificate_export_641(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decision Certificate + Institutional DD Export (#641) — catalog-aligned semantics."""
    from decision_certificate import build_decision_certificate
    seed = seed or _load_seed()
    underlying = build_decision_certificate({"symbol": symbol.upper(), "tier": "institutional"})
    return _base(
        641,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "decision_certificate_institutional_dd_export",
            "feature": "Decision Certificate + Institutional DD Export",
            "attribution": "decision_certificate.build_decision_certificate",
            "formula_visible": True,
            "decision_certificate_institutional_dd_export": underlying,
            "underlying": underlying,
        },
    )

def security_verification_evidence_645(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Security Verification Evidence (#645) — catalog-aligned semantics."""
    from security_posture import security_posture_report
    seed = seed or _load_seed()
    underlying = security_posture_report()
    return _base(
        645,
        symbol=symbol,
        seed=seed,
        extra={
            "surface": "security_verification_evidence",
            "feature": "Security Verification Evidence",
            "attribution": "security_posture.security_posture_report",
            "formula_visible": True,
            "security_verification_evidence": underlying,
            "underlying": underlying,
        },
    )

def _external_provider_contract(
    cap_id: int,
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
    contract_fn: Any,
) -> dict[str, Any]:
    from cap978.external_registry import external_registry_rows

    seed = seed or _load_seed()
    reason = next(
        (r["reason"] for r in external_registry_rows() if r.get("id") == cap_id),
        _EXTERNAL_DEPENDENCY_DEFAULT,
    )
    contract = contract_fn(symbol=symbol, external_reason=reason)
    payload = _base(cap_id, symbol=symbol, seed=seed, extra=contract)
    if not contract.get("ok"):
        payload["ok"] = False
    return payload


def real_time_feed_647(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Real-Time Feed (#647) — local provider contract; live vendor blocked."""
    from bd_platform.extension_providers.real_time_feed import execute_local_contract

    return _external_provider_contract(647, symbol=symbol, seed=seed, contract_fn=execute_local_contract)


def datashare_648(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Datashare (#648) — local provider contract; warehouse agreement blocked."""
    from bd_platform.extension_providers.datashare import execute_local_contract

    return _external_provider_contract(648, symbol=symbol, seed=seed, contract_fn=execute_local_contract)


def dbt_connector_649(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """dbt Connector (#649) — local provider contract; external deployment blocked."""
    from bd_platform.extension_providers.dbt_connector import execute_local_contract

    return _external_provider_contract(649, symbol=symbol, seed=seed, contract_fn=execute_local_contract)


def bi_connectors_650(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """BI Connectors (#650) — local provider contract; connector licenses blocked."""
    from bd_platform.extension_providers.bi_connectors import execute_local_contract

    return _external_provider_contract(650, symbol=symbol, seed=seed, contract_fn=execute_local_contract)
