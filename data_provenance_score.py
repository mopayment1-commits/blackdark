"""
BLACKDARK — Data Provenance Score (Coverage radical).

Every decision carries an honest score: freshness · venue depth · source diversity.
Narrow live coverage becomes a trust feature: we only decide where data is executable.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any


def _load_live_venues() -> tuple[list[dict[str, Any]], int]:
    try:
        from platform_universe import exchanges_by_status

        live_venues = exchanges_by_status("ingestion_ready")
        return live_venues, len(live_venues)
    except Exception:
        return [], 0


def _book_freshness_ms(symbol: str) -> float | None:
    try:
        from live_book_hub import get_top_of_book

        asset = symbol.upper().replace("USDT", "").replace("/", "")
        book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset) or {}
    except Exception:
        return None

    if not isinstance(book, dict):
        return None
    ms = book.get("freshness_ms") or book.get("stalest_ms")
    if ms is None and book.get("ts"):
        ms = max(0.0, (time.time() - float(book["ts"])) * 1000.0)
    return ms


def _freshness_component(ms: float | None) -> tuple[float, str]:
    if ms is None:
        return 18.0, "unknown"
    if ms <= 2000:
        return 40.0, "fresh"
    if ms <= 15000:
        return 28.0, "ok"
    return 8.0, "stale"


def _score_band(total: float) -> tuple[str, str]:
    if total >= 80:
        return "decision_grade", "Decide — live provenance sufficient for Act/Wait honesty"
    if total >= 55:
        return "caution", "Decide with caution — some inputs soft or thin"
    return "insufficient", "Prefer WAIT — provenance below decision-grade bar"


def compute_data_provenance_score(
    *,
    symbol: str = "BTC",
    freshness_ms: float | None = None,
    venue_count: int | None = None,
    source_categories: list[str] | None = None,
    executable: bool | None = None,
) -> dict[str, Any]:
    """0–100 provenance score with explicit components and honesty band."""
    cats = list(source_categories or [])
    live_venues, live_n = _load_live_venues()

    if venue_count is None:
        venue_count = live_n

    # Freshness component (0–40)
    ms = freshness_ms
    if ms is None:
        ms = _book_freshness_ms(symbol)
    fresh_score, fresh_state = _freshness_component(ms)

    # Venue depth component (0–35) — depth of LIVE venues, not planned catalog
    # Cap honesty: reward live ready venues, not target-100 vanity
    depth = min(35.0, 8.0 + float(venue_count) * 3.0)

    # Source diversity (0–15)
    if not cats:
        cats = ["prices", "derivatives"] if live_n else ["prices"]
    diversity = min(15.0, 5.0 + len(set(cats)) * 3.0)

    # Executable gate (0–10)
    if executable is None:
        executable = fresh_state in {"fresh", "ok"} and venue_count >= 1
    exec_score = 10.0 if executable else 2.0

    total = round(min(100.0, fresh_score + depth + diversity + exec_score), 1)
    band, posture = _score_band(total)

    return {
        "surface": "data_provenance_score",
        "generated_at": datetime.now(UTC).isoformat(),
        "symbol": symbol.upper(),
        "score": total,
        "band": band,
        "posture": posture,
        "components": {
            "freshness": {"score": fresh_score, "state": fresh_state, "freshness_ms": ms},
            "venue_depth": {"score": depth, "live_venues": venue_count, "max_component": 35},
            "source_diversity": {"score": diversity, "categories": sorted(set(cats))},
            "executable_gate": {"score": exec_score, "executable": bool(executable)},
        },
        "live_ingestion_ready_ids": [r.get("id") for r in live_venues][:20],
        "data_trust": {
            "aggregators_never_l2": True,
            "canonical_eligible_only": "venue_direct",
        },
        "honesty": (
            "Score uses LIVE ingestion-ready venues only — never inflates with planned/catalog rows. "
            "Breadth without freshness is not coverage. CoinGecko/synthetic books are not L2."
        ),
        "api": "/api/oracle/provenance-score",
        "disclaimer": "Provenance ≠ profit guarantee. Low score forces WAIT posture.",
    }


def attach_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    sym = str(out.get("asset") or out.get("symbol") or "BTC")
    ms = out.get("freshness_ms")
    chip = out.get("data_freshness") or {}
    if ms is None and isinstance(chip, dict):
        ms = chip.get("freshness_ms")
    prov = compute_data_provenance_score(symbol=sym, freshness_ms=ms)
    out["data_provenance"] = prov
    out["provenance_score"] = prov["score"]
    out["provenance_band"] = prov["band"]
    return out
