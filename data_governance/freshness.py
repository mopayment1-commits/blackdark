"""Freshness model with source-class SLO — delegates to failure/freshness SSOT."""

from __future__ import annotations

import time
from typing import Any

from failure.freshness import FreshnessState, attach_freshness, classify_freshness

SLO_CLASS_TARGETS = {
    "T0": {"max_live_s": 2, "max_near_live_s": 15},
    "T1": {"max_live_s": 5, "max_near_live_s": 30},
    "T2": {"max_live_s": 30, "max_near_live_s": 120},
    "T3": {"max_live_s": 120, "max_near_live_s": 600},
    "T4": {"max_live_s": 300, "max_near_live_s": 1800},
    "T5": {"max_live_s": 3600, "max_near_live_s": 86400},
    "T6": {"max_live_s": 86400, "max_near_live_s": 86400 * 7},
}


def classify_with_slo(*, age_seconds: float | None, slo_class: str = "T1") -> dict[str, Any]:
    result = classify_freshness(age_seconds=age_seconds)
    targets = SLO_CLASS_TARGETS.get(slo_class, SLO_CLASS_TARGETS["T1"])
    age = age_seconds or 999999.0
    slo_met = age <= targets["max_near_live_s"]
    return {
        "freshness_state": result.state.value,
        "age_seconds": result.age_seconds,
        "as_of": result.last_successful_update,
        "slo_class": slo_class,
        "slo_met": slo_met,
        "last_successful_update": result.last_successful_update,
    }


def attach_data_freshness(payload: dict[str, Any], *, slo_class: str = "T1") -> dict[str, Any]:
    out = attach_freshness(dict(payload))
    age_ms = out.get("quote_age_ms") or out.get("freshness_ms")
    age_sec = float(age_ms) / 1000.0 if age_ms else out.get("data_age_sec")
    fresh = classify_with_slo(age_seconds=float(age_sec) if age_sec is not None else None, slo_class=slo_class)
    out["data_governance_freshness"] = fresh
    out["freshness_state"] = fresh["freshness_state"]
    out["age_seconds"] = fresh.get("age_seconds")
    if fresh["freshness_state"] == FreshnessState.UNKNOWN.value:
        out["freshness_disclosure"] = "UNKNOWN — not presented as LIVE"
    return out


def freshness_from_live_book(symbol: str) -> dict[str, Any]:
    try:
        from live_book_hub import get_quote_age_ms, get_top_of_book

        asset = symbol.upper().replace("USDT", "")
        book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
        age_ms = get_quote_age_ms(f"{asset}USDT") if book else None
        return classify_with_slo(age_seconds=float(age_ms) / 1000.0 if age_ms else None, slo_class="T0")
    except Exception:
        return classify_with_slo(age_seconds=None, slo_class="T0")
