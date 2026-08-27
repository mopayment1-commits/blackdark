"""
Options Intelligence Module (#82 IV Surface + #83 Term Structure).

Silent advanced analytics for Decision Engine (#48) volatility regime.
Uses Deribit public API — NOT a standalone product for casual users.

#82: IV by strike/expiry → surface construction + benchmark validation
#83: IV by expiry → term curve + expiry exactness
"""

from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.OptionsIntelligence")

DERIBIT_BASE = "https://www.deribit.com/api/v2/public"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=3600)
_INSTRUMENT_RE = re.compile(
    r"^(?P<asset>[A-Z]+)-(?P<expiry>\d{1,2}[A-Z]{3}\d{2})-(?P<strike>\d+(?:\.\d+)?)-(?P<kind>[CP])$"
)

# Sanity benchmark bands for ATM IV validation (annualized %)
_BENCHMARK_ATM_IV: dict[str, tuple[float, float]] = {
    "BTC": (15.0, 120.0),
    "ETH": (20.0, 150.0),
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_expiry(expiry_token: str) -> datetime | None:
    """Parse Deribit expiry token (e.g. 29MAR24) with exactness check."""
    try:
        return datetime.strptime(expiry_token.upper(), "%d%b%y").replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_instrument(name: str) -> dict[str, Any] | None:
    m = _INSTRUMENT_RE.match(name.upper())
    if not m:
        return None
    expiry_dt = _parse_expiry(m.group("expiry"))
    if expiry_dt is None:
        return None
    return {
        "asset": m.group("asset"),
        "expiry_token": m.group("expiry"),
        "expiry_iso": expiry_dt.isoformat(),
        "expiry_ts": int(expiry_dt.timestamp()),
        "strike": float(m.group("strike")),
        "kind": m.group("kind"),
    }


async def _deribit_get(path: str, *, params: dict[str, Any], cache_suffix: str) -> dict[str, Any]:
    return await _CACHE.http_get_json(
        f"{DERIBIT_BASE}/{path}",
        params=params,
        timeout_sec=3.0,
        cache_key=cache_key("deribit", cache_suffix, params),
        ttl=_CACHE.ttl("DERIBIT_CACHE_TTL_SEC", 300),
        source_slug="deribit_options",
    )


async def _fetch_book_summaries(currency: str) -> list[dict[str, Any]]:
    resp = await _deribit_get(
        "get_book_summary_by_currency",
        params={"currency": currency.upper(), "kind": "option"},
        cache_suffix=f"summary_{currency}",
    )
    if not resp.get("ok"):
        return []
    data = resp.get("data") or {}
    if isinstance(data, dict) and "result" in data:
        rows = data.get("result") or []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    return [r for r in rows if isinstance(r, dict)]


async def _fetch_index_price(currency: str) -> float | None:
    resp = await _deribit_get(
        "get_index_price",
        params={"index_name": f"{currency.lower()}_usd"},
        cache_suffix=f"index_{currency}",
    )
    if not resp.get("ok"):
        return None
    data = resp.get("data") or {}
    result = data.get("result") if isinstance(data, dict) else data
    if isinstance(result, dict):
        return float(result.get("index_price") or 0) or None
    return None


def _select_atm_strike(strikes: list[float], spot: float) -> float | None:
    if not strikes or spot <= 0:
        return None
    return min(strikes, key=lambda k: abs(k - spot))


def build_iv_surface(
    summaries: list[dict[str, Any]],
    *,
    spot: float,
    asset: str,
) -> dict[str, Any]:
    """Construct IV surface grid from Deribit book summaries."""
    points: list[dict[str, Any]] = []
    for row in summaries:
        name = str(row.get("instrument_name") or "")
        meta = _parse_instrument(name)
        if not meta or meta["asset"] != asset.upper():
            continue
        iv = row.get("mark_iv")
        if iv is None:
            continue
        try:
            iv_f = float(iv)
        except (TypeError, ValueError):
            continue
        if iv_f <= 0:
            continue
        moneyness = round((meta["strike"] / spot - 1) * 100, 2) if spot > 0 else None
        points.append(
            {
                "instrument": name,
                "expiry": meta["expiry_token"],
                "expiry_iso": meta["expiry_iso"],
                "strike": meta["strike"],
                "kind": meta["kind"],
                "mark_iv_pct": round(iv_f, 2),
                "moneyness_pct": moneyness,
                "open_interest": row.get("open_interest"),
            }
        )

    expiries = sorted({p["expiry"] for p in points})
    strikes = sorted({p["strike"] for p in points})
    call_strikes = sorted({p["strike"] for p in points if p["kind"] == "C"})
    atm_strike = _select_atm_strike(call_strikes, spot)
    atm_candidates = [p for p in points if p["kind"] == "C" and p["strike"] == atm_strike]
    if atm_candidates:
        nearest = min(atm_candidates, key=lambda p: p.get("expiry_iso") or "")
        atm_iv = nearest["mark_iv_pct"]
    else:
        atm_iv = None

    put_ivs = [p["mark_iv_pct"] for p in points if p["kind"] == "P" and (p["moneyness_pct"] or 0) < -5]
    call_ivs = [p["mark_iv_pct"] for p in points if p["kind"] == "C" and (p["moneyness_pct"] or 0) > 5]
    put_skew = round((sum(put_ivs) / len(put_ivs)) - atm_iv, 2) if put_ivs and atm_iv else None

    benchmark = _BENCHMARK_ATM_IV.get(asset.upper())
    benchmark_ok = None
    if atm_iv is not None and benchmark:
        lo, hi = benchmark
        benchmark_ok = lo <= atm_iv <= hi

    return {
        "points": points[:200],
        "grid": {"expiries": expiries[:12], "strikes": strikes[:30]},
        "atm_iv_pct": atm_iv,
        "put_skew_vs_atm": put_skew,
        "benchmark_range_pct": benchmark,
        "benchmark_validation_passed": benchmark_ok,
        "point_count": len(points),
    }


def build_term_structure(
    summaries: list[dict[str, Any]],
    *,
    spot: float,
    asset: str,
) -> dict[str, Any]:
    """IV term curve by expiry with expiry exactness validation."""
    by_expiry: dict[str, list[dict[str, Any]]] = {}
    exactness_failures: list[str] = []

    for row in summaries:
        name = str(row.get("instrument_name") or "")
        meta = _parse_instrument(name)
        if not meta or meta["asset"] != asset.upper() or meta["kind"] != "C":
            continue
        iv = row.get("mark_iv")
        if iv is None:
            continue
        try:
            iv_f = float(iv)
        except (TypeError, ValueError):
            continue
        if iv_f <= 0:
            continue
        exp = meta["expiry_token"]
        by_expiry.setdefault(exp, []).append({"strike": meta["strike"], "iv": iv_f, "expiry_iso": meta["expiry_iso"]})

        # Expiry exactness: instrument token must parse to valid future date
        exp_dt = _parse_expiry(exp)
        if exp_dt is None:
            exactness_failures.append(name)
        elif exp_dt.timestamp() <= time.time():
            exactness_failures.append(name)

    curve: list[dict[str, Any]] = []
    for exp, rows in sorted(by_expiry.items(), key=lambda x: x[1][0]["expiry_iso"]):
        atm = _select_atm_strike([r["strike"] for r in rows], spot)
        atm_row = next((r for r in rows if r["strike"] == atm), None)
        if not atm_row:
            continue
        curve.append(
            {
                "expiry": exp,
                "expiry_iso": atm_row["expiry_iso"],
                "atm_iv_pct": round(atm_row["iv"], 2),
                "contracts": len(rows),
            }
        )

    front_iv = curve[0]["atm_iv_pct"] if curve else None
    back_iv = curve[-1]["atm_iv_pct"] if len(curve) >= 2 else None
    structure = "flat"
    if front_iv is not None and back_iv is not None:
        if front_iv > back_iv * 1.08:
            structure = "backwardation"
        elif back_iv > front_iv * 1.08:
            structure = "contango"

    return {
        "curve": curve,
        "front_month_iv_pct": front_iv,
        "back_month_iv_pct": back_iv,
        "structure": structure,
        "expiry_exactness_failures": exactness_failures[:10],
        "expiry_exactness_passed": len(exactness_failures) == 0,
    }


def _surface_headline(asset: str, surface: dict[str, Any], term: dict[str, Any]) -> str | None:
    atm = surface.get("atm_iv_pct")
    skew = surface.get("put_skew_vs_atm")
    parts: list[str] = []
    if atm is not None:
        parts.append(f"ATM {atm:.0f}%")
    if skew is not None and skew >= 5:
        parts.append("Put Skew Extreme")
        parts.append("AI flags potential gamma squeeze")
    if term.get("structure") == "backwardation" and term.get("front_month_iv_pct") and term.get("back_month_iv_pct"):
        return (
            f"{asset} Term Structure: Front month IV {term['front_month_iv_pct']:.0f}% vs "
            f"Back month {term['back_month_iv_pct']:.0f}% — AI flags extreme backwardation "
            "(historically precedes elevated volatility)"
        )
    if parts:
        return f"{asset} IV Surface: {' | '.join(parts)}"
    return None


async def analyze_options_intelligence(asset: str = "BTC") -> dict[str, Any]:
    """Full options intelligence snapshot (#82 + #83)."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    summaries = await _fetch_book_summaries(sym)
    spot = await _fetch_index_price(sym) or 0.0

    if not summaries or spot <= 0:
        return {
            "ok": False,
            "feature": "#82+#83",
            "asset": sym,
            "error": "options_data_unavailable",
            "data_state": "MISSING",
            "timestamp": _utcnow(),
        }

    surface = build_iv_surface(summaries, spot=spot, asset=sym)
    term = build_term_structure(summaries, spot=spot, asset=sym)
    headline = _surface_headline(sym, surface, term)
    elapsed = time.perf_counter() - t0

    return {
        "ok": True,
        "feature": "#82+#83",
        "surface": "options_intelligence_module",
        "asset": sym,
        "spot_usd": round(spot, 2),
        "iv_surface": surface,
        "term_structure": term,
        "benchmark_validation_passed": surface.get("benchmark_validation_passed"),
        "expiry_exactness_passed": term.get("expiry_exactness_passed"),
        "headline": headline,
        "ai_context_line": headline,
        "ingestion_role": "volatility_regime",
        "provider": "deribit",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def options_intelligence_for_decision_engine(asset: str = "BTC") -> dict[str, Any]:
    """Compact payload for Decision Engine (#48)."""
    row = await analyze_options_intelligence(asset)
    if not row.get("ok"):
        return {"ok": False, "feature": "#82+#83", "error": row.get("error")}
    surface = row.get("iv_surface") or {}
    term = row.get("term_structure") or {}
    risk_delta = 0.0
    if surface.get("put_skew_vs_atm") and float(surface["put_skew_vs_atm"]) >= 8:
        risk_delta += 0.6
    if term.get("structure") == "backwardation":
        risk_delta += 0.5
    if surface.get("benchmark_validation_passed") is False:
        risk_delta += 0.3
    return {
        "ok": True,
        "feature": "#82+#83",
        "asset": row.get("asset"),
        "atm_iv_pct": surface.get("atm_iv_pct"),
        "term_structure": term.get("structure"),
        "put_skew_vs_atm": surface.get("put_skew_vs_atm"),
        "risk_score_delta": round(risk_delta, 2),
        "headline": row.get("headline"),
        "latency_ms": row.get("latency_ms"),
    }


def options_intelligence_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "feature": "#82+#83",
        "role": "volatility_regime_input",
        "provider": "deribit",
        "benchmark_assets": list(_BENCHMARK_ATM_IV.keys()),
        "circuit_open": is_open("deribit_options"),
        "cache_ttl_seconds": _CACHE.ttl("DERIBIT_CACHE_TTL_SEC", 300),
        "timestamp": _utcnow(),
    }
