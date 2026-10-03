"""Post-baseline (827–978) semantic bindings, dispatch, and oracles."""

from __future__ import annotations

from typing import Any, Callable

from cap646.backend_registry import BackendBinding, _slug
from cap978.catalog import catalog_by_id

from cap978._post_baseline_bindings_generated import POST_BASELINE_BINDINGS

_INSTITUTIONAL_MIRROR_OFFSET = 267


def is_post_baseline(capability_id: int) -> bool:
    return 827 <= capability_id <= 978


def resolve_post_baseline_binding(capability_id: int) -> BackendBinding:
    if capability_id not in POST_BASELINE_BINDINGS:
        raise ValueError(f"no post-baseline binding for capability {capability_id}")
    mod, ep, ps, _oracle = POST_BASELINE_BINDINGS[capability_id]
    row = catalog_by_id()[capability_id]
    surface = _slug(row["capability"])
    return BackendBinding(capability_id, mod, ep, surface, ps, "post_baseline_semantic")


def _payload(result: dict[str, Any]) -> dict[str, Any]:
    inner = result.get("result")
    if isinstance(inner, dict):
        return inner
    if isinstance(inner, tuple) and inner:
        first = inner[0]
        if isinstance(first, list):
            return {
                "closes": first,
                "ohlcv": first,
                "bars": first,
                "source": inner[1] if len(inner) > 1 else None,
            }
    return result


def _has_any(data: dict[str, Any], *keys: str) -> bool:
    return any(data.get(k) is not None for k in keys)


async def execute_institutional_mirror(*, symbol: str = "BTC", params: dict[str, Any] | None = None, capability_id: int = 893) -> dict[str, Any]:
    """Delegate extension institutional mirrors (893–913) to batch26 canonical handlers."""
    from cap646.institutional_official_production import execute

    base_id = capability_id - _INSTITUTIONAL_MIRROR_OFFSET
    merged = dict(params or {})
    merged.setdefault("symbol", symbol)
    body = await execute(base_id, params=merged)
    body["extension_capability_id"] = capability_id
    body["canonical_mirror_id"] = base_id
    body["mirror_offset"] = _INSTITUTIONAL_MIRROR_OFFSET
    return body


_ORACLE_VALIDATORS: dict[str, Callable[[int, str, dict[str, Any]], tuple[bool, str]]] = {}


def _register_oracle(key: str, fn: Callable[[int, str, dict[str, Any]], tuple[bool, str]]) -> None:
    _ORACLE_VALIDATORS[key] = fn


def _check_price(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "price", "mark_price", "usd", "current_price", "price_usd", "coingecko_id") or _has_any(
        result, "price", "mark_price", "price_usd"
    ):
        return True, "price_semantics"
    return False, "missing_price_payload"


def _check_ohlcv(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "ohlcv", "bars", "closes") or _has_any(result, "ohlcv", "bars"):
        return True, "ohlcv_semantics"
    return False, "missing_ohlcv_payload"


def _check_order_book(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "book", "order_book", "depth", "bids", "asks", "liquidity") or _has_any(result, "book", "order_book", "depth"):
        return True, "order_book_semantics"
    return False, "missing_order_book_payload"


def _check_api_contract(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "status", "schema", "endpoints", "graphql") or result.get("success"):
        return True, "api_contract_semantics"
    return False, "missing_api_contract"


def _check_sentiment(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "sentiment",
        "score",
        "context",
        "classification",
        "sentiment_compound_index",
        "sentiment_score_adjustments",
    ) or _has_any(result, "sentiment", "context", "sentiment_compound_index"):
        return True, "sentiment_semantics"
    return False, "missing_sentiment_payload"


def _check_portfolio(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "holdings", "allocation", "portfolio", "positions", "snapshot") or _has_any(result, "portfolio", "holdings"):
        return True, "portfolio_semantics"
    return False, "missing_portfolio_payload"


def _check_volatility(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "drawdown",
        "volatility",
        "var",
        "risk_score",
        "drawdown_pct",
        "equity_usd",
        "peak_equity_usd",
        "max_allowed_drawdown_pct",
    ) or _has_any(result, "drawdown", "volatility", "drawdown_pct"):
        return True, "volatility_semantics"
    return False, "missing_volatility_payload"


def _check_derivatives(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "funding",
        "open_interest",
        "liquidation",
        "derivatives",
        "perp",
        "coinglass",
        "deribit_options",
        "sources",
        "primary_source",
        "asset",
    ) or _has_any(result, "funding", "derivatives", "coinglass"):
        return True, "derivatives_semantics"
    return False, "missing_derivatives_payload"


def _check_arbitrage(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "opportunities", "scan", "arbitrage", "spread") or _has_any(result, "opportunities", "scan"):
        return True, "arbitrage_semantics"
    return False, "missing_arbitrage_payload"


def _check_onchain(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "onchain",
        "wallet",
        "whale",
        "address",
        "flow",
        "clusters",
        "onchain_flows",
        "onchain_signals",
        "onchain_by_asset",
        "onchain_score_adjustments",
    ) or _has_any(result, "onchain", "wallet", "onchain_flows"):
        return True, "onchain_semantics"
    return False, "missing_onchain_payload"


def _check_security(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "posture", "controls", "gates", "attestation", "checks") or _has_any(result, "posture", "attestation"):
        return True, "security_semantics"
    return False, "missing_security_payload"


def _check_risk(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "risk",
        "exposure",
        "limits",
        "status",
        "trading_frozen",
        "max_slippage_bps",
        "poison_threshold_pct",
        "honest_scope",
        "freeze_reason",
    ) or _has_any(result, "risk", "status", "trading_frozen"):
        return True, "risk_semantics"
    return False, "missing_risk_payload"


def _check_alpha(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "alpha", "signal", "score", "factors", "ranking") or _has_any(result, "alpha", "signal"):
        return True, "alpha_semantics"
    return False, "missing_alpha_payload"


def _check_defi(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "tvl", "apy", "yield", "protocols", "raises", "pools") or _has_any(result, "tvl", "yield"):
        return True, "defi_semantics"
    return False, "missing_defi_payload"


def _check_macro(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "macro", "correlation", "index", "metrics", "live_metrics", "indicators", "source") or _has_any(
        result, "macro", "metrics", "live_metrics"
    ):
        return True, "macro_semantics"
    return False, "missing_macro_payload"


def _check_charting(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "indicators", "charts", "layouts", "library", "technical_indicator", "feature") or _has_any(
        result, "indicators", "charts", "technical_indicator"
    ):
        return True, "charting_semantics"
    return False, "missing_charting_payload"


def _check_provenance(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "provenance", "lineage", "score", "band", "sources") or _has_any(result, "provenance", "data_provenance"):
        return True, "provenance_semantics"
    return False, "missing_provenance_payload"


def _check_decision(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "ledger",
        "certificate",
        "decision",
        "trace",
        "claims",
        "total",
        "linked_outcomes",
        "linked_exposure",
        "by_evidence_class",
        "path",
    ) or _has_any(result, "ledger", "certificate", "total"):
        return True, "decision_semantics"
    return False, "missing_decision_payload"


def _check_capacity(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    report = data.get("report") if isinstance(data.get("report"), dict) else data
    sle = (report or {}).get("signed_load_evidence") or data.get("signed_load_evidence") or {}
    if sle.get("present") and (report or {}).get("checks"):
        return True, "capacity_semantics"
    return False, "missing_capacity_evidence"


def _check_alert(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "engine", "alerts", "inbox", "stats") or _has_any(result, "engine", "alerts"):
        return True, "alert_semantics"
    return False, "missing_alert_payload"


def _check_usage(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "events",
        "analytics",
        "dashboard",
        "by_endpoint",
        "summary",
        "async_ingestion",
        "privacy_first",
        "admin_mfa_required",
    ) or _has_any(result, "analytics", "summary"):
        return True, "usage_analytics_semantics"
    return False, "missing_usage_analytics"


def _check_signal_registry(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "signals",
        "registry",
        "definitions",
        "canonical",
        "registry_stats",
        "unified_definitions",
        "sovereign",
        "ci_validation",
    ) or _has_any(result, "registry", "registry_stats"):
        return True, "signal_registry_semantics"
    return False, "missing_signal_registry"


def _check_exchange_health(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "exchanges",
        "health",
        "certification",
        "counterparty",
        "counterparty_risk",
        "withdrawal_latency_hours",
        "reserve_transparency_score",
        "exchange",
    ) or _has_any(result, "health", "counterparty"):
        return True, "exchange_health_semantics"
    return False, "missing_exchange_health"


def _check_infra(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(
        data,
        "postgresql",
        "microservices",
        "kafka",
        "vault",
        "matrix",
        "unified_exchange",
        "feature",
        "components",
        "status",
    ) or _has_any(result, "postgresql", "microservices", "unified_exchange"):
        return True, "infra_semantics"
    return False, "missing_infra_payload"


def _check_institutional(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "delivery", "institutional", "terminal", "dashboard", "surface") or result.get("surface"):
        return True, "institutional_semantics"
    return False, "missing_institutional_payload"


def _check_market_structure(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "coordinates", "squeeze", "volume", "clusters", "liquidation") or _has_any(result, "coordinates"):
        return True, "market_structure_semantics"
    return False, "missing_market_structure"


def _check_trust(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "trust", "pulse", "confidence", "calibration", "score") or _has_any(result, "trust_pulse"):
        return True, "trust_semantics"
    return False, "missing_trust_payload"


def _check_liquidity(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    if _has_any(data, "liquidity", "flow", "projects", "book", "feasibility") or _has_any(result, "liquidity"):
        return True, "liquidity_semantics"
    return False, "missing_liquidity_payload"


def _check_institutional_mirror(cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    data = _payload(result)
    base = cid - _INSTITUTIONAL_MIRROR_OFFSET
    if data.get("canonical_mirror_id") == base and (data.get("success") or result.get("success")):
        return True, "institutional_mirror_semantics"
    if data.get("extension_capability_id") == cid and data.get("surface"):
        return True, "institutional_mirror_semantics"
    if data.get("handler_module") and data.get("surface"):
        return True, "institutional_mirror_semantics"
    if result.get("success") and data.get("surface"):
        return True, "institutional_mirror_semantics"
    return False, "institutional_mirror_failed"


def _check_stablecoin(_cid: int, _name: str, result: dict[str, Any]) -> tuple[bool, str]:
    return _check_macro(_cid, _name, result)


# register oracles
for _key, _fn in [
    ("price", _check_price),
    ("ohlcv", _check_ohlcv),
    ("order_book", _check_order_book),
    ("api_contract", _check_api_contract),
    ("sentiment", _check_sentiment),
    ("portfolio", _check_portfolio),
    ("volatility", _check_volatility),
    ("derivatives", _check_derivatives),
    ("arbitrage", _check_arbitrage),
    ("onchain", _check_onchain),
    ("security", _check_security),
    ("risk", _check_risk),
    ("alpha", _check_alpha),
    ("defi", _check_defi),
    ("macro", _check_macro),
    ("charting", _check_charting),
    ("provenance", _check_provenance),
    ("decision", _check_decision),
    ("capacity", _check_capacity),
    ("alert", _check_alert),
    ("usage_analytics", _check_usage),
    ("signal_registry", _check_signal_registry),
    ("exchange_health", _check_exchange_health),
    ("infra", _check_infra),
    ("institutional", _check_institutional),
    ("market_structure", _check_market_structure),
    ("trust", _check_trust),
    ("liquidity", _check_liquidity),
    ("institutional_mirror", _check_institutional_mirror),
    ("stablecoin", _check_stablecoin),
]:
    _register_oracle(_key, _fn)


def validate_semantic_oracle(capability_id: int, result: dict[str, Any]) -> tuple[bool, str, str]:
    """Return (ok, oracle_key, detail)."""
    if not is_post_baseline(capability_id):
        return True, "not_post_baseline", "n/a"
    binding = POST_BASELINE_BINDINGS.get(capability_id)
    if not binding:
        return False, "missing_binding", "no_post_baseline_binding"
    oracle_key = binding[3]
    validator = _ORACLE_VALIDATORS.get(oracle_key)
    if not validator:
        return False, oracle_key, "missing_oracle_validator"
    name = catalog_by_id()[capability_id].get("capability", "")
    ok, detail = validator(capability_id, name, result)
    return ok, oracle_key, detail


def oracle_for(capability_id: int) -> str:
    return POST_BASELINE_BINDINGS[capability_id][3]
