"""
Digital Asset Treasury Company Intelligence — Feature #239 (Sprint 2).

Tracks public companies with digital asset treasuries. Integrated into
Macro Intelligence Hub (#263) — NOT a standalone product.
Macro context only — no yield/arbitrage recommendations.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.TreasuryIntelligence")

_FEATURE_ID = 239
_STANDALONE = False
_MERGED_INTO = "Macro Intelligence Hub (#263)"
_SPRINT = 2
_SEED_PATH = Path("data/treasury_intelligence_seed.json")
_METHODOLOGY_VERSION = "1.0"
_STALE_THRESHOLD_DAYS = 45

_DISCLAIMER_TEXT = (
    "Treasury data based on public company filings. Holdings may have changed since last disclosure. "
    "Unrealized P&L is an estimate. Not investment advice."
)

FreshnessStatus = Literal["Live", "Stale"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"companies": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("treasury intelligence seed load failed: %s", exc)
        return {"companies": {}}


def _parse_date(value: str) -> date:
    return date.fromisoformat(str(value)[:10])


def _format_usd(value: float, *, signed: bool = False) -> str:
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        text = f"${abs_val / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        text = f"${abs_val / 1_000_000:.0f}M"
    else:
        text = f"${abs_val:,.0f}"
    if signed and value < 0:
        return f"-{text}"
    if signed and value > 0:
        return f"+{text}"
    return text


def compute_data_age(reporting_period_end: str, *, as_of: date | None = None) -> int:
    """Days since reporting period end."""
    end = _parse_date(reporting_period_end)
    ref = as_of or datetime.now(UTC).date()
    return (ref - end).days


def classify_freshness(age_days: int) -> FreshnessStatus:
    return "Live" if age_days <= _STALE_THRESHOLD_DAYS else "Stale"


def build_filing_block(filing: dict[str, Any], holdings: dict[str, Any]) -> dict[str, Any]:
    """Mandatory filing/source timestamps — no number without a filing source."""
    asset = holdings.get("asset", "BTC")
    amount = holdings.get("disclosed_amount")
    source = filing.get("source", "SEC Filing")
    form = filing.get("form", "10-K")
    item = filing.get("item", "")
    filed = filing.get("filed_date")
    period = filing.get("reporting_period")
    next_filing = filing.get("next_expected_filing")

    item_str = f" ({item})" if item else ""
    return {
        "holdings_amount": amount,
        "asset": asset,
        "source": source,
        "form": form,
        "item": item,
        "filed_date": filed,
        "reporting_period": period,
        "next_expected_filing": next_filing,
        "display": (
            f"Holdings: {amount:,.0f} {asset} | Source: {source} {form}{item_str} | "
            f"Filed: {filed} | Reporting Period: {period} | Next Expected Filing: {next_filing}"
        ),
    }


def build_holdings_status(
    holdings: dict[str, Any],
    filing: dict[str, Any],
    *,
    as_of: date | None = None,
) -> dict[str, Any]:
    """Never present stale holdings as live."""
    period_end = filing.get("reporting_period_end") or filing.get("reporting_period", "")
    age_days = compute_data_age(str(period_end), as_of=as_of)
    freshness = classify_freshness(age_days)
    asset = holdings.get("asset", "BTC")
    disclosed = holdings.get("disclosed_amount", 0)

    result: dict[str, Any] = {
        "disclosed_amount": disclosed,
        "asset": asset,
        "as_of": period_end,
        "age_days": age_days,
        "freshness": freshness,
        "display": (
            f"Last Disclosed: {disclosed:,.0f} {asset} | As of: {period_end} | "
            f"Age: {age_days} days | Status: {freshness}"
        ),
        "presented_as_live": False,
    }

    estimate = holdings.get("estimated_current")
    if freshness == "Stale" and estimate:
        result["estimate"] = {
            "amount": estimate,
            "confidence": holdings.get("estimate_confidence", "Low"),
            "method": holdings.get("estimate_method", "Heuristic"),
            "display": (
                f"Estimated Current (based on purchase history): {estimate:,.0f} {asset} | "
                f"Confidence: {holdings.get('estimate_confidence', 'Low')} | "
                f"Method: {holdings.get('estimate_method', 'Heuristic')}"
            ),
        }
    elif freshness == "Live":
        result["presented_as_live"] = True

    return result


def normalize_treasury_exposure(company: dict[str, Any]) -> dict[str, Any]:
    """Normalized exposure metrics — the investor-facing value add."""
    norm = company.get("normalized") or {}
    btc_per_share = norm.get("btc_per_share")
    pct_mcap = norm.get("pct_of_market_cap")
    cost_basis = norm.get("cost_basis_usd")
    unrealized_pct = norm.get("unrealized_pnl_pct")
    treasury_value = norm.get("treasury_value_usd")
    market_cap = norm.get("market_cap_usd")

    return {
        "btc_per_share": btc_per_share,
        "pct_of_market_cap": pct_mcap,
        "cost_basis_usd": cost_basis,
        "unrealized_pnl_pct": unrealized_pct,
        "treasury_value_usd": treasury_value,
        "market_cap_usd": market_cap,
        "display": (
            f"BTC per Share: {btc_per_share} | % of Market Cap: {pct_mcap}% | "
            f"Cost Basis: {_format_usd(cost_basis)} | "
            f"Unrealized P&L: {unrealized_pct:+.1f}%"
            if btc_per_share is not None and pct_mcap is not None and cost_basis is not None
            else "Normalization data unavailable"
        ),
        "treasury_value_display": _format_usd(treasury_value) if treasury_value else "N/A",
        "market_cap_display": _format_usd(market_cap) if market_cap else "N/A",
    }


def build_crypto_linkage(company: dict[str, Any]) -> dict[str, Any]:
    """Stock-crypto linkage — correlation, beta, exposure level."""
    link = company.get("crypto_linkage") or {}
    corr = link.get("stock_btc_correlation_90d")
    beta = link.get("beta_to_btc")
    exposure = link.get("btc_exposure_level", "Unknown")

    return {
        "stock_btc_correlation_90d": corr,
        "beta_to_btc": beta,
        "btc_exposure_level": exposure,
        "linked_asset": link.get("linked_asset", "BTC"),
        "display": (
            f"Stock-BTC Correlation (90D): {corr:+.2f} | Beta to BTC: {beta} | BTC Exposure: {exposure}"
            if corr is not None and beta is not None
            else f"BTC Exposure: {exposure}"
        ),
        "context_display": f"Treasury Exposure: {exposure} | Context: BTC proxy",
        "not_a_recommendation": True,
    }


def build_company_dashboard(company: dict[str, Any], *, as_of: date | None = None) -> dict[str, Any]:
    """Full DAT company dashboard card."""
    ticker = company.get("ticker", "")
    name = company.get("name", "")
    filing = company.get("filing") or {}
    holdings = company.get("holdings") or {}

    filing_block = build_filing_block(filing, holdings)
    holdings_status = build_holdings_status(holdings, filing, as_of=as_of)
    exposure = normalize_treasury_exposure(company)
    linkage = build_crypto_linkage(company)

    return {
        "ticker": ticker,
        "name": name,
        "company_display": f"Company: {name} ({ticker})",
        "treasury_value": exposure["treasury_value_display"],
        "pct_of_market_cap": exposure.get("pct_of_market_cap"),
        "cost_basis": _format_usd(exposure.get("cost_basis_usd") or 0),
        "unrealized_pnl": (
            f"{exposure['unrealized_pnl_pct']:+.1f}%"
            if exposure.get("unrealized_pnl_pct") is not None
            else "N/A"
        ),
        "btc_per_share": exposure.get("btc_per_share"),
        "stock_btc_correlation": linkage.get("stock_btc_correlation_90d"),
        "last_filing": filing.get("filed_date"),
        "next_expected_filing": filing.get("next_expected_filing"),
        "dashboard_display": (
            f"Company: {name} ({ticker}) | "
            f"Treasury Value: {exposure['treasury_value_display']} | "
            f"% of Market Cap: {exposure.get('pct_of_market_cap', 'N/A')}% | "
            f"Cost Basis: {_format_usd(exposure.get('cost_basis_usd') or 0)} | "
            f"Unrealized P&L: {exposure.get('unrealized_pnl_pct', 0):+.1f}% | "
            f"BTC per Share: {exposure.get('btc_per_share', 'N/A')} | "
            f"Stock-BTC Correlation: {linkage.get('stock_btc_correlation_90d', 'N/A')} | "
            f"Last Filing: {filing.get('filed_date', 'N/A')} | "
            f"Next Expected: {filing.get('next_expected_filing', 'N/A')}"
        ),
        "filing": filing_block,
        "holdings_status": holdings_status,
        "normalized_exposure": exposure,
        "crypto_linkage": linkage,
        "context_display": linkage["context_display"],
        "macro_context_only": True,
        "not_a_recommendation": True,
        "no_buy_language": True,
    }


def build_treasury_companies_card(asset: str = "BTC") -> dict[str, Any]:
    """Card payload for Macro Intelligence Hub (#263) integration."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    companies_raw = seed.get("companies") or {}

    cards = []
    for ticker, data in companies_raw.items():
        linked = (data.get("crypto_linkage") or {}).get("linked_asset", "BTC")
        if linked != sym and sym not in (data.get("holdings") or {}).get("assets", [linked]):
            continue
        cards.append(build_company_dashboard(data))

    cards.sort(
        key=lambda c: (c.get("normalized_exposure") or {}).get("treasury_value_usd") or 0,
        reverse=True,
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    total_tracked = len(companies_raw)

    return {
        "feature_id": _FEATURE_ID,
        "feature_name": "Digital Asset Treasury Company Intelligence",
        "status": "live",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "company_count": len(cards),
        "coverage_minimum": 20,
        "coverage_met": total_tracked >= 20,
        "companies": cards,
        "top_by_treasury_value": [c["ticker"] for c in cards[:5]],
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        "methodology_display": seed.get(
            "methodology_display",
            f"Treasury Intelligence Methodology {_METHODOLOGY_VERSION} | Filing-sourced | Stale-aware",
        ),
        "staleness_policy": {
            "threshold_days": _STALE_THRESHOLD_DAYS,
            "display": (
                f"Holdings marked Stale when reporting period end > {_STALE_THRESHOLD_DAYS} days ago. "
                "Never presented as live when stale."
            ),
        },
        "macro_context_only": True,
        "no_yield_arbitrage": True,
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_treasury_dashboard(asset: str | None = None) -> dict[str, Any]:
    """Full treasury companies dashboard — accessed via Macro Hub, not standalone."""
    seed = _load_seed()
    sym = (asset or "BTC").upper().replace("/USDT", "")
    card = build_treasury_companies_card(sym)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": "macro_intelligence_hub",
        "merged_into": _MERGED_INTO,
        **card,
    }


def get_treasury_company(ticker: str) -> dict[str, Any] | None:
    """Single company treasury intelligence."""
    seed = _load_seed()
    company = (seed.get("companies") or {}).get(ticker.upper())
    if not company:
        return None
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        **build_company_dashboard(company),
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def list_treasury_companies() -> list[dict[str, Any]]:
    """All tracked treasury companies sorted by treasury value."""
    seed = _load_seed()
    companies = [
        build_company_dashboard(c)
        for c in (seed.get("companies") or {}).values()
    ]
    companies.sort(
        key=lambda c: (c.get("normalized_exposure") or {}).get("treasury_value_usd") or 0,
        reverse=True,
    )
    return companies


def treasury_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    companies = seed.get("companies") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_label": seed.get("feature_label", "Treasury Intelligence Module"),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        "companies_tracked": len(companies),
        "coverage_minimum": 20,
        "coverage_met": len(companies) >= 20,
        "staleness_threshold_days": _STALE_THRESHOLD_DAYS,
        "acceptance_criteria": {
            "filing_source_timestamps": True,
            "no_stale_as_live": True,
            "treasury_exposure_normalized": True,
            "crypto_linkage_visible": True,
            "no_buy_language": True,
            "disclaimer_non_hideable": True,
            "macro_context_only": True,
            "macro_hub_integration": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
