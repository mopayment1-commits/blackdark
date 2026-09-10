"""Macro, network health, and sentiment context capabilities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "capability_spine_context_v1"


# ── CAP-72 Network Health Matrix ───────────────────────────────────────────────


def network_health_matrix(chains: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    default = chains or [
        {"chain": "ethereum", "gas_gwei": 25.0, "block_time_s": 12.0, "failed_tx_rate": 0.01},
        {"chain": "bitcoin", "fee_sat_vb": 15.0, "block_time_s": 600.0, "failed_tx_rate": 0.001},
    ]
    matrix: dict[str, dict[str, Any]] = {}
    for row in default:
        chain = str(row.get("chain") or "unknown")
        matrix[chain] = {
            "gas_or_fee": row.get("gas_gwei") or row.get("fee_sat_vb"),
            "block_time_s": row.get("block_time_s"),
            "failed_tx_rate": row.get("failed_tx_rate"),
            "freshness_state": row.get("freshness_state") or "DELAYED",
            "missing_disclosed": row.get("missing_disclosed", False),
        }
    return {
        "ok": True,
        "matrix": matrix,
        "cross_chain_normalized": False,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-73 M2 Liquidity Context ────────────────────────────────────────────────


def m2_liquidity_context(
    *,
    series_id: str = "M2SL",
    jurisdiction: str = "US",
    value_usd_billions: float | None = None,
    release_date: str | None = None,
    revision: int | None = None,
) -> dict[str, Any]:
    if value_usd_billions is None or release_date is None:
        return {
            "ok": False,
            "reason": "missing_authoritative_macro_series",
            "series_id": series_id,
            "jurisdiction": jurisdiction,
            "frequency": "monthly",
            "realtime": False,
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {
        "ok": True,
        "series_id": series_id,
        "jurisdiction": jurisdiction,
        "value_usd_billions": value_usd_billions,
        "release_date": release_date,
        "revision": revision,
        "frequency": "monthly",
        "realtime": False,
        "provenance": "authoritative_macro_source_required",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-74 Interest-Rate / Monetary Policy Context ─────────────────────────────


def interest_rate_context(
    *,
    policy_rate: float | None = None,
    target_range: tuple[float, float] | None = None,
    market_yield: float | None = None,
    effective_date: str | None = None,
    source: str = "FOMC",
) -> dict[str, Any]:
    if policy_rate is None and target_range is None and market_yield is None:
        return {
            "ok": False,
            "reason": "missing_rate_data",
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {
        "ok": True,
        "policy_rate": policy_rate,
        "target_range": list(target_range) if target_range else None,
        "market_yield": market_yield,
        "effective_date": effective_date or datetime.now(UTC).date().isoformat(),
        "source": source,
        "distinction": "policy_rate_vs_market_yield_explicit",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-75 Fear & Greed Context ──────────────────────────────────────────────────


async def fear_greed_context() -> dict[str, Any]:
    try:
        from blackdark.ingestion.alternative_me_connector import fetch_fear_greed_index

        fg = await fetch_fear_greed_index()
        return {
            "ok": bool(fg.get("ok", True)),
            "value": fg.get("value"),
            "label": fg.get("label"),
            "source": "alternative.me",
            "timestamp": fg.get("timestamp") or datetime.now(UTC).isoformat(),
            "version": fg.get("version") or "alternative_me_v1",
            "contextual_only": True,
            "methodology_version": METHODOLOGY_VERSION,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "methodology_version": METHODOLOGY_VERSION,
        }


def fear_greed_context_sync(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = payload or {}
    value = data.get("fear_greed_index") if data.get("fear_greed_index") is not None else data.get("value")
    label = data.get("fear_greed_label") or data.get("label")
    if value is None:
        return {
            "ok": False,
            "reason": "missing_sentiment_source",
            "value": None,
            "label": None,
            "source": data.get("source") or "alternative.me",
            "timestamp": data.get("timestamp") or datetime.now(UTC).isoformat(),
            "contextual_only": True,
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {
        "ok": True,
        "value": value,
        "label": label,
        "source": data.get("source") or "alternative.me",
        "timestamp": data.get("timestamp") or datetime.now(UTC).isoformat(),
        "contextual_only": True,
        "methodology_version": METHODOLOGY_VERSION,
    }
