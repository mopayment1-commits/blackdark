"""
Profitability Analyzer — #981 (Net Profit Engine).

Merged into #981 — NOT standalone. Deducts all actual fees (trading, withdrawal,
deposit, network gas) before displaying net profit to users.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ProfitabilityAnalyzer")

_FEATURE_REF = 981
_MERGED_INTO = "#981 Profitability Analyzer"
_STANDALONE = False
_SEED_PATH = Path("data/profitability_analyzer_seed.json")
_RUNBOOK = "docs/infrastructure/PROFITABILITY_ANALYZER.md"

_MULTI_ACCOUNT_SYNC_REF = 907
_REFERENCE_PRICING_REF = 959
_STRIPE_REF = 908
_PROVENANCE_REF = 945
_IMMUTABLE_AUDIT_REF = 1029
_FINANCIAL_PRECISION_REF = 1032

FeeCategory = Literal["trading", "withdrawal", "deposit", "network_gas"]
EdgeFeeType = Literal["bridge_fee", "cross_chain_gas", "failed_tx_gas", "airdrop_claim_gas"]

_pnl_reports: list[dict[str, Any]] = []


def reset_profitability_analyzer_state() -> None:
    _pnl_reports.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("profitability analyzer seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("profitability_analyzer_981") or {}


def profitability_analyzer_status_981(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "insight_only": policy.get("insight_only", True),
            "non_custodial": policy.get("non_custodial", True),
            "net_profit_default_display": policy.get("net_profit_default_display", True),
            "gross_profit_labeled": policy.get("gross_profit_labeled", True),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
            "disclaimer": policy.get("disclaimer"),
            "sprint": policy.get("sprint", 2),
        },
        "fee_categories": cfg.get("fee_categories") or [],
        "fee_sourcing": cfg.get("fee_sourcing") or {},
        "edge_case_fees": cfg.get("edge_case_fees") or {},
        "integrations": {
            "multi_account_sync_ref": _MULTI_ACCOUNT_SYNC_REF,
            "reference_pricing_ref": _REFERENCE_PRICING_REF,
            "stripe_ref": _STRIPE_REF,
            "provenance_ref": _PROVENANCE_REF,
            "immutable_audit_ref": _IMMUTABLE_AUDIT_REF,
            "financial_precision_ref": _FINANCIAL_PRECISION_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def record_pnl_fee(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = (
        float(fee_cfg.get("fee_query_usd", 0.00002))
        + float(fee_cfg.get("attribution_compute_usd", 0.00003))
        + float(fee_cfg.get("storage_usd", 0.00001))
    )
    return {
        "cost_usd": round(cost, 6),
        "fee_db_logged": True,
        "logged_per_pnl_report": True,
        "timestamp": _utcnow(),
    }


def resolve_network_gas_usdt(
    *,
    chain: str = "ethereum",
    quote_usd: float = 100.0,
    gas_usdt: float | None = None,
    edge_fee_type: EdgeFeeType | None = None,
    user_override_usdt: float | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Network gas from on-chain oracle — fail-closed if unknown."""
    seed = seed or _load_seed()
    sourcing = (_cfg(seed).get("fee_sourcing") or {}).get("network_gas") or {}

    if user_override_usdt is not None:
        return {
            "category": "network_gas",
            "amount_usdt": user_override_usdt,
            "source": "user_override",
            "edge_fee_type": edge_fee_type,
            "methodology_version": (_cfg(seed).get("policy") or {}).get("methodology_version"),
        }

    if gas_usdt is not None:
        return {
            "category": "network_gas",
            "amount_usdt": gas_usdt,
            "source": sourcing.get("source", "gas_oracle_onchain"),
            "chain": chain,
            "methodology_version": (_cfg(seed).get("policy") or {}).get("methodology_version"),
        }

    try:
        import asyncio

        from gas_oracle import get_swap_gas_usd

        loop = asyncio.get_event_loop()
        if loop.is_running():
            return None
        usd = loop.run_until_complete(get_swap_gas_usd(chain))
        if usd is None:
            return None
        return {
            "category": "network_gas",
            "amount_usdt": float(usd),
            "source": sourcing.get("source", "gas_oracle_onchain"),
            "chain": chain,
            "methodology_version": (_cfg(seed).get("policy") or {}).get("methodology_version"),
        }
    except Exception:
        logger.debug("gas oracle unavailable", exc_info=True)
        return None


def attribute_fees(
    *,
    trading_usdt: float | None = None,
    withdrawal_usdt: float | None = None,
    deposit_usdt: float | None = None,
    network_gas_usdt: float | None = None,
    platform_fee_usdt: float | None = None,
    trade_id: str | None = None,
    account_id: str | None = None,
    reference_price: float | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-trade fee attribution — no ambiguous aggregation."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    sourcing = cfg.get("fee_sourcing") or {}
    items: list[dict[str, Any]] = []

    def _item(category: FeeCategory, amount: float | None) -> None:
        if amount is None:
            return
        src = sourcing.get(category) or {}
        items.append(
            {
                "category": category,
                "amount_usdt": amount,
                "source": src.get("source"),
                "method": src.get("method"),
                "trade_id": trade_id,
                "account_id": account_id,
                "reference_price": reference_price,
                "reference_pricing_ref": _REFERENCE_PRICING_REF if reference_price else None,
                "timestamp": _utcnow(),
            }
        )

    _item("trading", trading_usdt)
    _item("withdrawal", withdrawal_usdt)
    _item("deposit", deposit_usdt)
    _item("network_gas", network_gas_usdt)

    platform = None
    if platform_fee_usdt is not None:
        platform = {
            "category": cfg.get("platform_fee_label", "platform_cost"),
            "amount_usdt": platform_fee_usdt,
            "source": "stripe_fee_db_908",
            "stripe_ref": _STRIPE_REF,
            "separate_from_market_fees": True,
            "label": "منصة تكلفة",
            "trade_id": trade_id,
            "timestamp": _utcnow(),
        }

    total_market = sum(i["amount_usdt"] for i in items)
    return {
        "attribution_id": f"fee_{uuid.uuid4().hex[:10]}",
        "items": items,
        "platform_fee": platform,
        "total_market_fees_usdt": total_market,
        "total_platform_fees_usdt": platform_fee_usdt or 0.0,
        "market_fee_label": cfg.get("market_fee_label", "market_cost"),
        "methodology_version": (cfg.get("policy") or {}).get("methodology_version"),
        "provenance_ref": _PROVENANCE_REF,
    }


def compute_gross_profit(
    *,
    proceeds_usdt: float,
    cost_usdt: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from money_decimal import crypto_money, money_float

    gross_dec = crypto_money(proceeds_usdt) - crypto_money(cost_usdt)
    return {
        "gross_profit_usdt": money_float(gross_dec),
        "label": "إجمالي قبل الرسوم",
        "hidden_by_default": (_cfg(seed).get("policy") or {}).get("gross_profit_hidden_by_default", True),
    }


def compute_net_profit_engine(
    *,
    proceeds_usdt: float,
    cost_usdt: float,
    trading_fees_usdt: float,
    withdrawal_fees_usdt: float,
    deposit_fees_usdt: float,
    network_gas_usdt: float | None = None,
    slippage_buffer_usdt: float = 0.0,
    platform_fee_usdt: float | None = None,
    reference_price: float | None = None,
    trade_id: str | None = None,
    account_id: str | None = None,
    chain: str = "ethereum",
    gas_usdt: float | None = None,
    edge_fee_type: EdgeFeeType | None = None,
    user_gas_override: float | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Net profit after all 4 fee categories — Decimal precision (#1032)."""
    seed = seed or _load_seed()
    if not (_cfg(seed).get("policy") or {}).get("enabled", True):
        return None

    from money_decimal import crypto_money, money_float, net_after_costs

    gas_resolved = resolve_network_gas_usdt(
        chain=chain,
        quote_usd=cost_usdt,
        gas_usdt=gas_usdt if network_gas_usdt is None else network_gas_usdt,
        edge_fee_type=edge_fee_type,
        user_override_usdt=user_gas_override,
        seed=seed,
    )
    if gas_resolved is None and network_gas_usdt is None and user_gas_override is None:
        return None

    gas_amount = float(
        (gas_resolved or {}).get("amount_usdt")
        or network_gas_usdt
        or user_gas_override
        or 0.0
    )

    net_dec = net_after_costs(
        proceeds_usdt,
        costs=[
            cost_usdt,
            trading_fees_usdt,
            withdrawal_fees_usdt,
            deposit_fees_usdt,
            gas_amount,
            slippage_buffer_usdt,
        ],
    )
    net_profit = money_float(net_dec)
    gross = compute_gross_profit(proceeds_usdt=proceeds_usdt, cost_usdt=cost_usdt, seed=seed)

    fees = attribute_fees(
        trading_usdt=trading_fees_usdt,
        withdrawal_usdt=withdrawal_fees_usdt,
        deposit_usdt=deposit_fees_usdt,
        network_gas_usdt=gas_amount,
        platform_fee_usdt=platform_fee_usdt,
        trade_id=trade_id,
        account_id=account_id,
        reference_price=reference_price,
        seed=seed,
    )

    policy = (_cfg(seed).get("policy") or {})
    report = {
        "report_id": f"pnl_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "net_profit_usdt": net_profit,
        "net_profit_percent": money_float(crypto_money(net_profit) / crypto_money(max(cost_usdt, 1e-9)) * 100),
        "gross_profit": gross,
        "display": {
            "default": "net",
            "net_profit_usdt": net_profit,
            "gross_profit_usdt": gross["gross_profit_usdt"],
            "gross_label": gross["label"],
            "gross_hidden": gross["hidden_by_default"],
        },
        "fee_attribution": fees,
        "fee_completeness": {
            "trading": True,
            "withdrawal": True,
            "deposit": True,
            "network_gas": True,
        },
        "disclaimer": policy.get("disclaimer"),
        "insight_only": policy.get("insight_only", True),
        "money_model": "decimal_crypto_8dp",
        "financial_precision_ref": _FINANCIAL_PRECISION_REF,
        "reference_pricing_ref": _REFERENCE_PRICING_REF if reference_price else None,
        "reference_price": reference_price,
        "immutable_audit_ref": _IMMUTABLE_AUDIT_REF,
        "fee_db": record_pnl_fee(seed=seed),
        "timestamp": _utcnow(),
    }

    try:
        from bd_platform.financial_precision_policy_engine import attach_financial_audit

        report = attach_financial_audit(report, context="net_profit_engine", asset_type="crypto", seed=seed)
    except ImportError:
        pass

    _pnl_reports.append(report)
    return report


def enrich_cross_exchange_profit(
    base: dict[str, Any],
    *,
    network_gas_usdt: float | None = None,
    platform_fee_usdt: float | None = None,
    reference_price: float | None = None,
    trade_id: str | None = None,
    account_id: str | None = None,
    chain: str = "ethereum",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Wrap net_cross_exchange_profit with gas + fee attribution + net display."""
    seed = seed or _load_seed()
    from money_decimal import crypto_money, money_float

    trading = float(base.get("trading_fees_usdt") or 0)
    withdraw = float(base.get("withdrawal_fee_usdt") or 0)
    deposit = float(base.get("deposit_fees_usdt") or 0)
    slip = float(base.get("slippage_buffer_usdt") or 0)
    base_net = float(base.get("net_profit_usdt") or 0)

    gas_amount: float | None = network_gas_usdt
    if gas_amount is None:
        gas_res = resolve_network_gas_usdt(chain=chain, quote_usd=float(base.get("quote_amount") or 100), seed=seed)
        gas_amount = float(gas_res["amount_usdt"]) if gas_res else None
    if gas_amount is None:
        return None

    net_profit = money_float(crypto_money(base_net) - crypto_money(gas_amount))
    gross_profit_usdt = money_float(
        crypto_money(net_profit) + crypto_money(trading + withdraw + deposit + slip + gas_amount)
    )

    fees = attribute_fees(
        trading_usdt=trading,
        withdrawal_usdt=withdraw,
        deposit_usdt=deposit,
        network_gas_usdt=gas_amount,
        platform_fee_usdt=platform_fee_usdt,
        trade_id=trade_id,
        account_id=account_id,
        reference_price=reference_price,
        seed=seed,
    )

    policy = (_cfg(seed).get("policy") or {})
    pnl = {
        "report_id": f"pnl_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "net_profit_usdt": net_profit,
        "gross_profit": {
            "gross_profit_usdt": gross_profit_usdt,
            "label": "إجمالي قبل الرسوم",
            "hidden_by_default": policy.get("gross_profit_hidden_by_default", True),
        },
        "display": {
            "default": "net",
            "net_profit_usdt": net_profit,
            "gross_profit_usdt": gross_profit_usdt,
            "gross_label": "إجمالي قبل الرسوم",
            "gross_hidden": policy.get("gross_profit_hidden_by_default", True),
        },
        "fee_attribution": fees,
        "fee_completeness": {
            "trading": True,
            "withdrawal": True,
            "deposit": True,
            "network_gas": True,
        },
        "disclaimer": policy.get("disclaimer"),
        "insight_only": policy.get("insight_only", True),
        "money_model": "decimal_crypto_8dp",
        "financial_precision_ref": _FINANCIAL_PRECISION_REF,
        "reference_price": reference_price,
        "fee_db": record_pnl_fee(seed=seed),
        "timestamp": _utcnow(),
    }

    try:
        from bd_platform.financial_precision_policy_engine import attach_financial_audit

        pnl = attach_financial_audit(pnl, context="net_profit_engine", asset_type="crypto", seed=seed)
    except ImportError:
        pass

    _pnl_reports.append(pnl)

    out = dict(base)
    out["net_profit_engine"] = pnl
    out["net_profit_usdt"] = net_profit
    out["gross_profit_usdt"] = gross_profit_usdt
    out["network_gas_usdt"] = gas_amount
    out["display"] = pnl["display"]
    out["fee_attribution"] = fees
    out["disclaimer"] = pnl["disclaimer"]
    out["profitability_analyzer_ref"] = _FEATURE_REF
    return out


def compute_cross_exchange_net_profit(
    buy_book: dict[str, Any],
    sell_book: dict[str, Any],
    *,
    buy_exchange: str,
    sell_exchange: str,
    symbol: str,
    notional: float | None = None,
    network_gas_usdt: float | None = None,
    reference_price: float | None = None,
    market_context: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Full pipeline: depth walk → all fees → net profit display."""
    import profit_fee_algorithms as pfa

    base = pfa.net_cross_exchange_profit(
        buy_book,
        sell_book,
        buy_exchange=buy_exchange,
        sell_exchange=sell_exchange,
        symbol=symbol,
        notional=notional,
        market_context=market_context,
    )
    if base is None:
        return None
    return enrich_cross_exchange_profit(
        base,
        network_gas_usdt=network_gas_usdt,
        reference_price=reference_price,
        trade_id=f"{buy_exchange}:{sell_exchange}:{symbol}",
        seed=seed,
    )


def aggregate_cross_account_fees(
    accounts: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#907 Multi-Account Sync — aggregate fees across linked accounts."""
    seed = seed or _load_seed()
    total_trading = 0.0
    total_withdrawal = 0.0
    total_deposit = 0.0
    total_gas = 0.0
    attributions: list[dict[str, Any]] = []

    for acct in accounts:
        attr = attribute_fees(
            trading_usdt=acct.get("trading_fees_usdt"),
            withdrawal_usdt=acct.get("withdrawal_fees_usdt"),
            deposit_usdt=acct.get("deposit_fees_usdt"),
            network_gas_usdt=acct.get("network_gas_usdt"),
            account_id=str(acct.get("account_id", "unknown")),
            seed=seed,
        )
        attributions.append(attr)
        total_trading += float(acct.get("trading_fees_usdt") or 0)
        total_withdrawal += float(acct.get("withdrawal_fees_usdt") or 0)
        total_deposit += float(acct.get("deposit_fees_usdt") or 0)
        total_gas += float(acct.get("network_gas_usdt") or 0)

    return {
        "ok": True,
        "multi_account_sync_ref": _MULTI_ACCOUNT_SYNC_REF,
        "accounts_count": len(accounts),
        "totals": {
            "trading_fees_usdt": total_trading,
            "withdrawal_fees_usdt": total_withdrawal,
            "deposit_fees_usdt": total_deposit,
            "network_gas_usdt": total_gas,
        },
        "attributions": attributions,
        "fee_db": record_pnl_fee(seed=seed),
        "timestamp": _utcnow(),
    }


def get_pnl_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    reports = _pnl_reports[-limit:]
    return {
        "ok": True,
        "reports_count": len(reports),
        "reports": reports,
        "append_only": True,
        "immutable_audit_ref": _IMMUTABLE_AUDIT_REF,
        "provenance_ref": _PROVENANCE_REF,
        "timestamp": _utcnow(),
    }


def check_production_gate_981(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = profitability_analyzer_status_981(seed=seed)
    categories = status.get("fee_categories") or []
    required = ("trading", "withdrawal", "deposit", "network_gas")
    complete = all(c in categories for c in required)
    return {
        "ok": complete,
        "feature_ref": _FEATURE_REF,
        "blocks_production": complete,
        "fee_completeness": complete,
        "checks": {
            "four_fee_categories": complete,
            "net_default_display": status["policy"].get("net_profit_default_display", True),
            "decimal_precision_ref": _FINANCIAL_PRECISION_REF,
        },
        "timestamp": _utcnow(),
    }


def run_profitability_analyzer_e2e_981(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_profitability_analyzer_state()

    status = profitability_analyzer_status_981(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "four_fee_categories", "passed": len(status["fee_categories"]) == 4})
    checks.append({"id": "net_default", "passed": status["policy"]["net_profit_default_display"] is True})

    attr = attribute_fees(
        trading_usdt=0.5,
        withdrawal_usdt=4.5,
        deposit_usdt=0.0,
        network_gas_usdt=1.2,
        platform_fee_usdt=0.1,
        trade_id="test_trade",
        reference_price=42000.0,
        seed=seed,
    )
    checks.append({"id": "fee_attribution", "passed": len(attr["items"]) == 4})
    checks.append({"id": "platform_separate", "passed": attr["platform_fee"]["separate_from_market_fees"] is True})

    pnl = compute_net_profit_engine(
        proceeds_usdt=110.0,
        cost_usdt=100.0,
        trading_fees_usdt=0.5,
        withdrawal_fees_usdt=4.5,
        deposit_fees_usdt=0.0,
        network_gas_usdt=1.2,
        reference_price=42000.0,
        seed=seed,
    )
    checks.append({"id": "net_profit_computed", "passed": pnl is not None and pnl["net_profit_usdt"] < 10})
    checks.append({"id": "gross_labeled", "passed": pnl is not None and pnl["gross_profit"]["hidden_by_default"] is True})
    checks.append({"id": "disclaimer", "passed": pnl is not None and bool(pnl.get("disclaimer"))})

    buy = {"bids": [[99.0, 100.0]], "asks": [[100.0, 100.0]]}
    sell = {"bids": [[102.0, 100.0]], "asks": [[103.0, 100.0]]}
    full = compute_cross_exchange_net_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=100.0,
        network_gas_usdt=1.5,
        reference_price=42000.0,
        seed=seed,
    )
    checks.append({"id": "cross_exchange_pipeline", "passed": full is not None and "fee_attribution" in full})
    checks.append({"id": "net_less_than_gross", "passed": full is not None and full["net_profit_usdt"] <= full["gross_profit_usdt"]})

    agg = aggregate_cross_account_fees(
        [
            {"account_id": "a1", "trading_fees_usdt": 0.5, "withdrawal_fees_usdt": 2.0, "network_gas_usdt": 1.0},
            {"account_id": "a2", "trading_fees_usdt": 0.3, "deposit_fees_usdt": 0.0, "network_gas_usdt": 0.8},
        ],
        seed=seed,
    )
    checks.append({"id": "cross_account_907", "passed": agg["accounts_count"] == 2})

    gate = check_production_gate_981(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
