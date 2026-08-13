"""
BLACKDARK — Canonical Market State from venue-direct observations only.

If Binance=X, Coinbase=Y, Kraken=Z, BLACKDARK does not pick at random.
It publishes a consensus value with provenance, timestamps, and quality.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from data_trust_engine import cross_source_consensus, make_observation


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _mid_from_book(row: dict[str, Any]) -> float | None:
    bids = row.get("bids") or []
    asks = row.get("asks") or []
    if not bids or not asks:
        return None
    try:
        bid = float(bids[0][0])
        ask = float(asks[0][0])
    except (TypeError, ValueError, IndexError):
        return None
    if bid <= 0 or ask <= 0:
        return None
    return (bid + ask) / 2.0


def observations_from_live_books(symbol: str) -> list[dict[str, Any]]:
    """Collect decision-grade top-of-book mids. Synthetic rows are skipped."""
    from live_book_hub import get_quote_age_ms, iter_live_book_rows

    asset = symbol.upper().replace("USDT", "").replace("/", "")
    want = {asset, f"{asset}USDT"}
    out: list[dict[str, Any]] = []
    for exchange_id, sym, row in iter_live_book_rows():
        compact = str(sym).upper().replace("/", "")
        if compact not in want and str(sym).upper() not in {asset, f"{asset}/USDT"}:
            continue
        if row.get("decision_grade") is False:
            continue
        if str(row.get("book_origin") or "venue_l2").lower() == "synthetic":
            continue
        mid = _mid_from_book(row)
        if mid is None:
            continue
        age = get_quote_age_ms(exchange_id, str(sym))
        bids = row.get("bids") or [[None]]
        asks = row.get("asks") or [[None]]
        out.append(
            make_observation(
                source=f"{exchange_id}_live_book",
                venue=exchange_id,
                instrument=asset,
                data_type="l2",
                raw_value={"bid": bids[0], "ask": asks[0]},
                normalized_value=mid,
                book_origin=str(row.get("book_origin") or "venue_l2"),
                latency_ms=age,
                event_time=str(row.get("timestamp") or ""),
            )
        )
    return out


def build_canonical_market_state(symbol: str = "BTC") -> dict[str, Any]:
    """Canonical Market State for one instrument. Quiet engine — not a retail surface."""
    asset = symbol.upper().replace("USDT", "").replace("/", "")
    observations = observations_from_live_books(asset)
    consensus = cross_source_consensus(observations)
    decision_grade = consensus["action"] == "accept" and consensus["canonical_value"] is not None
    quality = 0.0
    if decision_grade:
        quality = 70.0 + min(30.0, float(consensus.get("agreement") or 0) * 30.0)
        quality += min(10.0, (consensus.get("decision_grade_count") or 0) * 2.0)
        quality = min(100.0, quality)
    elif consensus["action"] == "penalize":
        quality = 45.0
    elif consensus["action"] == "quarantine":
        quality = 25.0

    return {
        "surface": "canonical_market_state",
        "generated_at": _utcnow_iso(),
        "instrument": asset,
        "canonical_value": consensus.get("canonical_value"),
        "action": consensus.get("action"),
        "reason": consensus.get("reason"),
        "quality_score": round(quality, 1),
        "decision_grade": bool(decision_grade),
        "agreement": consensus.get("agreement"),
        "venue_count": consensus.get("decision_grade_count"),
        "quarantined_count": len(consensus.get("quarantined") or []),
        "rejected_count": len(consensus.get("rejected") or []),
        "observations": [
            {
                "venue": o.get("venue"),
                "value": o.get("normalized_value"),
                "freshness": o.get("freshness"),
                "decision_grade": o.get("decision_grade"),
                "book_origin": o.get("book_origin"),
            }
            for o in observations
        ],
        "honesty": (
            "Canonical price uses venue-direct L2/top-of-book only. "
            "CoinGecko and synthetic books never enter this state."
        ),
        "api": "/api/public/canonical-market-state",
        "doc": "docs/DATA_TRUST_LAW_BINDING.md",
        "disclaimer": "Canonical state is a provenance snapshot — not a price guarantee.",
    }


def build_data_trust_law_manifest() -> dict[str, Any]:
    from data_source_trust import classify_registry

    registry = classify_registry()
    return {
        "surface": "data_trust_law",
        "status": "binding",
        "generated_at": _utcnow_iso(),
        "thesis": (
            "BLACKDARK converts conflicting sources into one auditable Canonical Market State, "
            "then intelligence — it does not sell API count."
        ),
        "in_scope_now": [
            "classify_existing_sources",
            "observation_envelope",
            "consensus_quarantine_single_source_penalty",
            "synthetic_l2_honesty_gate",
            "canonical_market_state_majors",
            "oracle_fail_closed_when_trust_rejects",
        ],
        "explicitly_not_building": [
            "ingest_100_new_apis",
            "kaiko_coinmetrics_amberdata_coinapi_paid_core",
            "bloomberg_lseg_reuters_ft_wsj_feeds",
            "geopolitical_price_causation_engine",
            "financial_truth_layer_as_separate_product",
        ],
        "tiers": {
            "A": "venue_direct REST/WS",
            "B": "independent aggregator/reference — verify only",
            "C": "on-chain primary",
            "D": "macro primary (vintage when available)",
            "E": "primary announcement then wire then analysis",
            "F": "geopolitics as causal chain with confidence — never price edict",
        },
        "registry_honesty": registry,
        "doc": "docs/DATA_TRUST_LAW_BINDING.md",
        "api": "/api/strategy/data-trust-law",
        "canonical_api": "/api/public/canonical-market-state",
    }
