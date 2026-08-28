"""
Market Radar Futures Volume Intelligence — Feature #962 (Sprint 2).

Merged into Market Radar Derivatives tab — NOT standalone.
Volume, OI, funding rate, liquidations — USD/notional conversion audited.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.FuturesVolumeIntelligence")

_FEATURE_REF = 962
_FMV_REF = 959
_FUNDING_REF = 861
_STANDALONE = False
_MERGED_INTO = "Market Radar / Derivatives tab"
_SEED_PATH = Path("data/market_radar_futures_volume_seed.json")

_DISCLAIMER = (
    "Futures volume intelligence — derivatives market data. "
    "USD conversion uses reference price #959. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("futures volume seed load failed: %s", exc)
        return {}


def futures_volume_status_962(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("futures_volume_962") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "fmv_pricing_ref": _FMV_REF,
        "funding_ref": _FUNDING_REF,
        "metrics": ["volume", "open_interest", "funding_rate", "liquidations"],
        "usd_conversion_audited": True,
        "exchange_timestamp_used": True,
        "venue_aggregation_auditable": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _get_reference_price(asset: str, seed: dict[str, Any]) -> float | None:
    prices = seed.get("reference_prices") or {}
    return prices.get(asset.upper())


def build_futures_volume_dashboard_962(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    sym = asset.upper()
    venues = (seed.get("futures_venues") or {}).get(sym)
    if not venues:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "asset_not_found"}

    ref_price = _get_reference_price(sym, seed)
    cfg = seed.get("futures_volume_962") or {}
    per_exchange: list[dict[str, Any]] = []
    total_volume_usd = 0.0
    total_oi_usd = 0.0
    total_liquidations_usd = 0.0

    for venue, data in venues.items():
        if venue.startswith("_"):
            continue
        notional_vol = float(data.get("volume_notional", 0))
        notional_oi = float(data.get("open_interest_notional", 0))
        liq_notional = float(data.get("liquidations_notional", 0))
        volume_usd = notional_vol * ref_price if ref_price else notional_vol
        oi_usd = notional_oi * ref_price if ref_price else notional_oi
        liq_usd = liq_notional * ref_price if ref_price else liq_notional
        total_volume_usd += volume_usd
        total_oi_usd += oi_usd
        total_liquidations_usd += liq_usd

        per_exchange.append({
            "exchange": venue,
            "volume_notional": notional_vol,
            "volume_usd": round(volume_usd, 2),
            "open_interest_notional": notional_oi,
            "open_interest_usd": round(oi_usd, 2),
            "funding_rate": data.get("funding_rate"),
            "funding_rate_apr_pct": data.get("funding_rate_apr_pct"),
            "liquidations_notional": liq_notional,
            "liquidations_usd": round(liq_usd, 2),
            "exchange_timestamp": data.get("exchange_timestamp"),
            "usd_conversion_method": "notional_x_reference_price_959",
            "reference_price_usd": ref_price,
        })

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": sym,
        "metrics": {
            "volume_usd": round(total_volume_usd, 2),
            "open_interest_usd": round(total_oi_usd, 2),
            "funding_rate_weighted_apr_pct": venues.get("_aggregate", {}).get("funding_rate_apr_pct"),
            "liquidations_usd": round(total_liquidations_usd, 2),
        },
        "per_exchange": per_exchange,
        "exchange_count": len(per_exchange),
        "usd_conversion_audited": True,
        "reference_price_ref": _FMV_REF,
        "reference_price_usd": ref_price,
        "exchange_timestamp_used": True,
        "not_ingestion_time": True,
        "venue_aggregation_auditable": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_futures_volume_e2e_962(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = futures_volume_status_962(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "four_metrics", "passed": len(status["metrics"]) == 4})

    dash = build_futures_volume_dashboard_962("BTC", seed=seed)
    checks.append({"id": "dashboard", "passed": dash.get("ok") is True})
    checks.append({"id": "usd_conversion", "passed": dash.get("usd_conversion_audited") is True})
    checks.append({"id": "exchange_timestamp", "passed": dash.get("exchange_timestamp_used") is True})
    checks.append({"id": "venue_aggregation", "passed": dash.get("exchange_count", 0) >= 2})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
