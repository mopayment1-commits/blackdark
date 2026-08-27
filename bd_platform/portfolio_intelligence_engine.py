"""
Portfolio Intelligence Engine — Feature #449 (Sprint-1 Existing).

Renamed from "Portfolio AI" — quantitative portfolio analytics, not a new module.
Integrates existing Sprint-1 Portfolio AI surfaces with mandatory risk integrations.

Merged: #448, #450, #483 into same ticket.
Cancelled: Sharpe ≥1.5, Max Drawdown ≤15%, Win Rate ≥55% acceptance SLAs.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PortfolioIntelligenceEngine")

_FEATURE_ID = 449
_ROI_ATH_REF = 483
_MANDATORY_ROI_WINDOWS = ("24h", "7d", "30d", "90d", "1Y", "YTD", "all_time")
_TITLE = "Portfolio Intelligence Engine"
_LEGAL_NAME = "Portfolio Intelligence Engine"
_RENAMED_FROM = "Portfolio AI"
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Sprint-1 Existing"
_SPRINT = 1
_PRIORITY = "medium"
_SEED_PATH = Path("data/portfolio_intelligence_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Portfolio Intelligence — quantitative analytics across existing Portfolio AI modules. "
    "Not investment advice. No automatic execution."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"existing_module": True}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio intelligence engine seed load failed: %s", exc)
        return {"existing_module": True}


def apply_corporate_token_events(
    price_series: list[dict[str, Any]],
    events: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """#483 — adjust price history for splits, airdrops, burns where relevant."""
    if not events:
        return price_series
    adjusted = [dict(p) for p in price_series]
    for event in sorted(events, key=lambda e: e.get("date", "")):
        event_type = event.get("type")
        event_date = event.get("date")
        if event_type == "split":
            ratio = float(event.get("ratio", 1))
            if ratio <= 0:
                continue
            for p in adjusted:
                if p.get("date", "") < event_date:
                    p["price"] = round(float(p["price"]) / ratio, 8)
        elif event_type == "airdrop":
            factor = float(event.get("dilution_factor", 1))
            for p in adjusted:
                if p.get("date", "") < event_date:
                    p["price"] = round(float(p["price"]) / factor, 8)
        elif event_type == "burn":
            factor = float(event.get("supply_reduction_factor", 1))
            for p in adjusted:
                if p.get("date", "") >= event_date:
                    p["price"] = round(float(p["price"]) * factor, 8)
    return adjusted


def _compute_roi_pct(current: float, reference: float) -> float:
    if reference <= 0:
        return 0.0
    return round((current / reference - 1) * 100, 4)


def compute_roi_matrix(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
    use_breakeven: bool = True,
) -> dict[str, Any]:
    """#483 — 7 mandatory ROI windows with deterministic calculations."""
    seed = seed or _load_seed()
    cfg = seed.get("roi_ath_483") or {}
    assets = seed.get("assets") or {}
    data = assets.get(asset.upper())
    if not data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    price_history = apply_corporate_token_events(
        data.get("price_history") or [],
        data.get("corporate_events"),
    )
    if not price_history:
        return {"ok": False, "asset": asset, "error": "no_price_history"}

    current_price = float(price_history[-1]["price"])
    reference_prices = data.get("reference_prices") or {}
    windows: dict[str, Any] = {}

    for window in _MANDATORY_ROI_WINDOWS:
        ref_price = float(reference_prices.get(window, current_price))
        windows[window] = {
            "reference_price": ref_price,
            "roi_pct": _compute_roi_pct(current_price, ref_price),
        }

    breakeven_roi = None
    if use_breakeven:
        position_id = data.get("breakeven_position_id")
        if position_id:
            try:
                from bd_platform.live_breakeven_tracker import build_live_breakeven_panel

                breakeven = build_live_breakeven_panel(position_id)
                be_block = breakeven.get("breakeven") or breakeven.get("dynamic_breakeven") or {}
                be_price = float(be_block.get("price") or be_block.get("breakeven_price") or 0)
                if be_price > 0:
                    breakeven_roi = {
                        "reference_price": be_price,
                        "roi_pct": _compute_roi_pct(current_price, be_price),
                        "source": "live_breakeven_404",
                    }
            except Exception:
                logger.debug("breakeven ROI skipped for %s", asset, exc_info=True)

    return {
        "ok": True,
        "feature_ref": _ROI_ATH_REF,
        "asset": asset.upper(),
        "current_price": current_price,
        "roi_windows": windows,
        "mandatory_windows": list(_MANDATORY_ROI_WINDOWS),
        "breakeven_roi_404": breakeven_roi,
        "corporate_events_applied": bool(data.get("corporate_events")),
        "deterministic": True,
        "methodology_version": cfg.get("methodology_version", _METHODOLOGY_VERSION),
        "timestamp": _utcnow(),
    }


def compute_ath_statistics(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#483 — ATH drawdown and recovery days."""
    seed = seed or _load_seed()
    assets = seed.get("assets") or {}
    data = assets.get(asset.upper())
    if not data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    price_history = apply_corporate_token_events(
        data.get("price_history") or [],
        data.get("corporate_events"),
    )
    if not price_history:
        return {"ok": False, "asset": asset, "error": "no_price_history"}

    prices = [float(p["price"]) for p in price_history]
    dates = [p["date"] for p in price_history]
    ath_price = max(prices)
    ath_idx = prices.index(ath_price)
    ath_date = dates[ath_idx]
    current_price = prices[-1]
    drawdown_pct = round((current_price / ath_price - 1) * 100, 4) if ath_price > 0 else 0.0

    recovery_days = None
    if ath_idx < len(prices) - 1:
        trough_idx = ath_idx + prices[ath_idx + 1:].index(min(prices[ath_idx + 1:])) + ath_idx + 1
        if current_price >= ath_price * 0.99:
            recovery_days = len(prices) - 1 - trough_idx

    return {
        "ok": True,
        "feature_ref": _ROI_ATH_REF,
        "asset": asset.upper(),
        "ath_price": ath_price,
        "ath_date": ath_date,
        "current_price": current_price,
        "ath_drawdown_pct": drawdown_pct,
        "recovery_days": recovery_days,
        "deterministic": True,
        "timestamp": _utcnow(),
    }


def build_roi_ath_asset_card(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#483 asset card — ROI matrix + ATH statistics."""
    roi = compute_roi_matrix(asset, seed=seed)
    ath = compute_ath_statistics(asset, seed=seed)
    if not roi.get("ok"):
        return roi

    return {
        "ok": True,
        "feature_ref": _ROI_ATH_REF,
        "asset": asset.upper(),
        "roi_matrix": roi,
        "ath_statistics": ath if ath.get("ok") else None,
        "display": (
            f"{asset.upper()}: ROI 30d {roi['roi_windows']['30d']['roi_pct']:+.2f}% | "
            f"ATH drawdown {ath.get('ath_drawdown_pct', 0):+.2f}%"
        ),
        "timestamp": _utcnow(),
    }


def build_roi_ath_panel(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#483 full ROI & ATH panel for portfolio assets."""
    seed = seed or _load_seed()
    cfg = seed.get("roi_ath_483") or {}
    portfolio_assets = (seed.get("portfolio_assets") or {}).get(portfolio_id) or list((seed.get("assets") or {}).keys())
    cards = [build_roi_ath_asset_card(a, seed=seed) for a in portfolio_assets]

    return {
        "ok": True,
        "feature_ref": _ROI_ATH_REF,
        "title": "ROI & ATH Intelligence",
        "portfolio_id": portfolio_id,
        "asset_cards": [c for c in cards if c.get("ok")],
        "count": sum(1 for c in cards if c.get("ok")),
        "mandatory_roi_windows": list(_MANDATORY_ROI_WINDOWS),
        "breakeven_integration_404": cfg.get("breakeven_integration", True),
        "deterministic": True,
        "timestamp": _utcnow(),
    }


def build_integrated_panel(portfolio_id: str = "demo_portfolio") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()

    from bd_platform.capital_protection_controls import build_capital_awareness_panel
    from bd_platform.live_breakeven_tracker import build_live_breakeven_panel
    from bd_platform.strategy_simulator import build_strategy_simulator_panel

    capital = build_capital_awareness_panel(portfolio_id)
    stress_test = None
    try:
        from bd_platform.capital_protection_controls import build_portfolio_stress_test_result

        stress_test = build_portfolio_stress_test_result(portfolio_id)
    except Exception:
        logger.debug("portfolio stress test skipped", exc_info=True)
    breakeven = build_live_breakeven_panel("pos_btc_001")
    simulator = build_strategy_simulator_panel()

    net_edge_sample = None
    portfolio_net_edge = None
    try:
        from bd_platform.net_edge_truth_layer import build_portfolio_net_edge_scores

        portfolio_net_edge = build_portfolio_net_edge_scores(portfolio_id)
        if portfolio_net_edge.get("opportunities"):
            net_edge_sample = portfolio_net_edge["opportunities"][0]
        elif portfolio_net_edge.get("holdings"):
            net_edge_sample = portfolio_net_edge["holdings"][0]
    except Exception:
        logger.debug("net edge sample skipped", exc_info=True)

    fill_risk_sample = None
    try:
        from bd_platform.fill_risk_assessment import build_fill_risk_panel

        fill_risk_sample = build_fill_risk_panel()
    except Exception:
        logger.debug("fill risk sample skipped", exc_info=True)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "existing_module": True,
        "no_new_module_built": seed.get("no_new_module_built", True),
        "portfolio_id": portfolio_id,
        "capital_protection_410": capital,
        "portfolio_stress_test_453": stress_test,
        "live_breakeven_404": breakeven,
        "strategy_simulator_411": simulator,
        "net_edge_truth_417_sample": net_edge_sample,
        "net_edge_truth_417_portfolio": portfolio_net_edge,
        "fill_risk_assessment_433_sample": fill_risk_sample,
        "roi_ath_intelligence_483": build_roi_ath_panel(portfolio_id, seed=seed),
        "merged_features": seed.get("merged_features") or [448, 450, 483],
        "performance_sla_cancelled": seed.get("sharpe_drawdown_winrate_sla_cancelled", True),
        "risk_adjusted_metrics": {
            "drawdown_pct": (capital.get("portfolio_summary") or {}).get("current_drawdown_pct"),
            "risk_budget_used_pct": (capital.get("risk_budget") or {}).get("budget_used_pct"),
            "breakeven_distance": (breakeven.get("dynamic_breakeven") or {}).get("distance_to_breakeven_pct"),
        },
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def portfolio_intelligence_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "existing_module": True,
        "no_new_module_built": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "merged_features": seed.get("merged_features") or [448, 450, 483],
        "integrations": seed.get("integrations") or {},
        "performance_sla_cancelled": seed.get("sharpe_drawdown_winrate_sla_cancelled", True),
        "surface": "portfolio_ai",
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "existing_module", "passed": seed.get("existing_module") is True, "detail": "sprint-1"})
    checks.append({"id": "no_new_module", "passed": seed.get("no_new_module_built") is True, "detail": "reuse"})
    checks.append({"id": "renamed_portfolio_intelligence", "passed": seed.get("legal_name") == "Portfolio Intelligence Engine", "detail": "renamed"})
    checks.append({"id": "sla_cancelled", "passed": seed.get("sharpe_drawdown_winrate_sla_cancelled") is True, "detail": "SLA"})

    panel = build_integrated_panel()
    checks.append({"id": "capital_protection_410", "passed": panel.get("capital_protection_410", {}).get("ok") is True, "detail": "410"})
    checks.append({"id": "live_breakeven_404", "passed": panel.get("live_breakeven_404", {}).get("ok") is True, "detail": "404"})
    checks.append({"id": "merged_448_450", "passed": 448 in (seed.get("merged_features") or []) and 450 in (seed.get("merged_features") or []), "detail": "merged"})

    roi_panel = build_roi_ath_panel(seed=seed)
    checks.append({"id": "roi_ath_483", "passed": roi_panel.get("ok") is True and roi_panel.get("count", 0) >= 1, "detail": "483"})
    checks.append({"id": "roi_7_windows", "passed": roi_panel.get("mandatory_roi_windows") == list(_MANDATORY_ROI_WINDOWS), "detail": "7 windows"})
    btc_card = build_roi_ath_asset_card("BTC", seed=seed)
    checks.append({"id": "ath_drawdown", "passed": (btc_card.get("ath_statistics") or {}).get("ath_drawdown_pct") is not None, "detail": "ATH"})
    checks.append({"id": "deterministic_roi", "passed": (
        {k: v for k, v in compute_roi_matrix("BTC", seed=seed).items() if k != "timestamp"}
        == {k: v for k, v in compute_roi_matrix("BTC", seed=seed).items() if k != "timestamp"}
    ), "detail": "deterministic"})
    checks.append({"id": "breakeven_roi_404", "passed": (compute_roi_matrix("BTC", seed=seed).get("breakeven_roi_404") or {}).get("source") == "live_breakeven_404", "detail": "404"})

    checks.append({"id": "net_edge_truth_417", "passed": panel.get("net_edge_truth_417_portfolio", {}).get("ok") is True, "detail": "417"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
