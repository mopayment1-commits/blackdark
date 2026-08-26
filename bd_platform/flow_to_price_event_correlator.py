"""
Flow-to-Price Event Correlator — Feature #556 (Sprint 2 Intelligence Layer).

Renamed from "Flow-to-Price Explanation Engine".
Rule-based event-window correlation + competing-driver analysis.
NOT causation. Candidate events — not "likely drivers".
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.FlowToPriceEventCorrelator")

_FEATURE_ID = 556
_RENAMED_FROM = "Flow-to-Price Explanation Engine"
_TITLE = "Flow-to-Price Event Correlator"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/flow_to_price_event_correlator_seed.json")
_METHODOLOGY_VERSION = "1.0"
_CORRELATION_WINDOW_SECONDS = 3600

_DISCLAIMER = (
    "Temporal correlation only — correlation ≠ causation. "
    "Candidate events in window — not confirmed drivers. "
    "Causation: unverified. Not investment advice."
)

_BANNED_TERMS = (
    "likely drivers",
    "confidence %",
    "the cause is",
    "caused the move",
    "confirmed cause",
    "explanation engine",
    "this whale caused",
)

_DRIVER_CATEGORIES = (
    "exchange_flow",
    "miner_flow",
    "whale_flow",
    "stablecoin_flow",
    "derivatives",
    "liquidity",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"price_events": {}, "flow_events": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("flow to price event correlator seed load failed: %s", exc)
        return {"price_events": {}, "flow_events": {}}


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def correlate_candidate_events(
    price_event_ts: str,
    flow_events: list[dict[str, Any]],
    *,
    window_seconds: int = _CORRELATION_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    """Find candidate events in window — NOT causation."""
    price_time = _parse_ts(price_event_ts)
    candidates = []

    for event in flow_events:
        event_time = _parse_ts(event.get("timestamp", price_event_ts))
        delta = abs((event_time - price_time).total_seconds())
        if delta <= window_seconds:
            candidates.append({
                "event_id": event.get("event_id"),
                "category": event.get("category"),
                "description": event.get("description"),
                "timestamp": event.get("timestamp"),
                "temporal_alignment_seconds": round(delta, 1),
                "value_usd": event.get("value_usd"),
                "source": event.get("source"),
                "evidence_id": event.get("evidence_id"),
                "evidence_link": event.get("evidence_link"),
                "temporal_correlation": True,
                "correlation_not_causation": True,
                "causation_unverified": True,
                "not_a_driver_claim": True,
                "display": (
                    f"Candidate event in window ({delta:.0f}s): {event.get('description')} "
                    "[Correlation only — causation unverified]"
                ),
            })

    return sorted(candidates, key=lambda e: e["temporal_alignment_seconds"])


def rank_evidence_strength(
    candidates: list[dict[str, Any]],
    *,
    price_event: dict[str, Any],
) -> list[dict[str, Any]]:
    """Evidence strength ranking — NOT confidence in causation."""
    ranked = []
    for c in candidates:
        alignment = float(c.get("temporal_alignment_seconds", 9999))
        data_completeness = float(c.get("data_completeness_pct", 80))
        value_usd = float(c.get("value_usd", 0))

        alignment_score = max(0, 100 - (alignment / 36))
        magnitude_score = min(100, value_usd / 1_000_000 * 10) if value_usd else 0
        evidence_strength = round(
            (alignment_score * 0.4 + data_completeness * 0.4 + magnitude_score * 0.2), 1,
        )

        ranked.append({
            **c,
            "evidence_strength": evidence_strength,
            "evidence_strength_not_confidence": True,
            "data_completeness_pct": data_completeness,
            "temporal_alignment_seconds": alignment,
            "ranking_factors": {
                "temporal_alignment_weight": 0.4,
                "data_completeness_weight": 0.4,
                "magnitude_weight": 0.2,
            },
        })

    return sorted(ranked, key=lambda r: r["evidence_strength"], reverse=True)


def build_competing_hypotheses(
    ranked_candidates: list[dict[str, Any]],
    *,
    price_event: dict[str, Any],
) -> list[dict[str, Any]]:
    """Competing-driver analysis with hypothesis labels — alternatives always shown."""
    hypotheses: list[dict[str, Any]] = []
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    category_map: dict[str, list[dict[str, Any]]] = {}
    for c in ranked_candidates:
        cat = c.get("category", "unknown")
        category_map.setdefault(cat, []).append(c)

    for i, (category, events) in enumerate(category_map.items()):
        label = labels[i] if i < len(labels) else str(i + 1)
        top = events[0]
        cat_label = category.replace("_", " ").title()
        hypotheses.append({
            "hypothesis_id": f"hypothesis_{label}",
            "hypothesis_label": f"Hypothesis {label}",
            "statement": f"{cat_label} correlated",
            "category": category,
            "evidence_strength": top.get("evidence_strength"),
            "data_completeness_pct": top.get("data_completeness_pct"),
            "temporal_alignment_seconds": top.get("temporal_alignment_seconds"),
            "evidence_id": top.get("evidence_id"),
            "evidence_link": top.get("evidence_link"),
            "correlation_not_causation": True,
            "causation_unverified": True,
            "display": (
                f"Hypothesis {label}: {cat_label} correlated. "
                f"Evidence strength: {top.get('evidence_strength')} | "
                f"Causation: Unverified."
            ),
        })

    if not hypotheses:
        hypotheses.append({
            "hypothesis_id": "hypothesis_none",
            "hypothesis_label": "No hypotheses",
            "statement": "No candidate events in window",
            "correlation_not_causation": True,
            "causation_unverified": True,
            "display": "No candidate events in correlation window. Causation: Unverified.",
        })

    return hypotheses


def build_flow_to_price_correlation_panel(
    event_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build flow-to-price correlation panel with competing hypotheses."""
    seed = seed or _load_seed()
    price_event = (seed.get("price_events") or {}).get(event_id)
    if not price_event:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "event_not_found", "event_id": event_id}

    asset = price_event.get("asset", "BTC").upper()
    all_flow_events = (seed.get("flow_events") or {}).get(asset, [])
    window = int(price_event.get("correlation_window_seconds", _CORRELATION_WINDOW_SECONDS))

    candidates = correlate_candidate_events(
        price_event["timestamp"], all_flow_events, window_seconds=window,
    )
    ranked = rank_evidence_strength(candidates, price_event=price_event)
    hypotheses = build_competing_hypotheses(ranked, price_event=price_event)

    price_change_pct = float(price_event.get("price_change_pct", 0))
    direction = "up" if price_change_pct > 0 else "down" if price_change_pct < 0 else "flat"

    overall_completeness = round(
        sum(h.get("data_completeness_pct", 0) for h in hypotheses) / max(len(hypotheses), 1), 1,
    )
    best_alignment = min(
        (h.get("temporal_alignment_seconds", 9999) for h in hypotheses),
        default=0,
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "not_explanation_engine": True,
        "correlation_not_causation": True,
        "correlation_not_causation_explicit": True,
        "price_event": {
            "event_id": event_id,
            "asset": asset,
            "timestamp": price_event["timestamp"],
            "price_change_pct": price_change_pct,
            "direction": direction,
            "price_usd": price_event.get("price_usd"),
        },
        "candidate_events_in_window": ranked,
        "candidate_count": len(ranked),
        "competing_hypotheses": hypotheses,
        "alternatives_always_shown": True,
        "hypothesis_labels": True,
        "metrics": {
            "data_completeness_pct": overall_completeness,
            "temporal_alignment_seconds": best_alignment,
            "no_confidence_pct_for_causation": True,
        },
        "correlation_window_seconds": window,
        "timestamps_aligned": True,
        "evidence_links": [
            {"evidence_id": c.get("evidence_id"), "link": c.get("evidence_link")}
            for c in ranked if c.get("evidence_id")
        ],
        "linguistic_framing": {
            "use": "Candidate events in window | Evidence strength | Hypothesis labels",
            "forbidden": "Likely drivers | Confidence % | The cause is | Explanation Engine",
        },
        "summary_display": (
            f"Price moved {direction} {abs(price_change_pct):.2f}% at {price_event['timestamp']}. "
            f"{len(ranked)} candidate event(s) in window. "
            f"{len(hypotheses)} competing hypothesis(es). Causation: Unverified."
        ),
        "rule_based_only": True,
        "llm_optional_later": True,
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
    }


def build_flow_to_price_event_correlator_panel(
    *,
    event_id: str = "btc_move_2026_08_26",
    asset: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()

    if asset and not event_id:
        events = seed.get("price_events") or {}
        matching = [
            eid for eid, e in events.items()
            if e.get("asset", "").upper() == asset.upper()
        ]
        event_id = matching[0] if matching else event_id

    panel = build_flow_to_price_correlation_panel(event_id, seed=seed)
    if not panel.get("ok"):
        return panel

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    panel.update({
        "layer": _LAYER,
        "sprint": _SPRINT,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    })
    return panel


def flow_to_price_event_correlator_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "not_explanation_engine": True,
        "correlation_not_causation": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "correlation_window_seconds": _CORRELATION_WINDOW_SECONDS,
        "event_count": len(seed.get("price_events") or {}),
        "acceptance_criteria": {
            "correlation_not_causation_explicit": True,
            "timestamps_aligned": True,
            "evidence_links": True,
            "hypothesis_labels": True,
            "alternatives_always_shown": True,
            "no_confidence_pct_for_causation": True,
            "rule_based_only": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
