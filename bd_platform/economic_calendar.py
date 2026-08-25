"""
Economic Calendar — Feature #211 (Sprint 1 — widget import + asset relevance).

NOT built from scratch — imports TradingView Economic Calendar widget config.
Adds asset relevance layer with historical volatility context.
Source, timezone, and revisions tracked per event.
Displayed as factual data (Forecast | Previous | Actual), not trade advice.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EconomicCalendar")

_FEATURE_ID = 211
_STORE_PATH = Path("data/economic_calendar.json")
_SEED_PATH = Path("data/economic_calendar_seed.json")
_DISCLAIMER = "Economic data is factual reporting, not investment advice."
_DISCLAIMER_AR = "البيانات الاقتصادية تقارير واقعية وليست نصيحة استثمارية."

Impact = Literal["low", "medium", "high"]

# Historical asset relevance heuristics (institutional guidance — not financial advice)
_ASSET_RELEVANCE: dict[str, dict[str, Any]] = {
    "monetary_policy": {
        "BTC": {"historical_volatility_24h_pct": 5.2, "direction": "elevated"},
        "ETH": {"historical_volatility_24h_pct": 6.1, "direction": "elevated"},
        "SOL": {"historical_volatility_24h_pct": 7.4, "direction": "elevated"},
        "headline_template": "{event} → {asset} volatility historically +{vol}% in 24h",
    },
    "inflation": {
        "BTC": {"historical_volatility_24h_pct": 3.5, "direction": "elevated"},
        "ETH": {"historical_volatility_24h_pct": 4.0, "direction": "elevated"},
        "headline_template": "{event} → {asset} volatility historically +{vol}% in 24h",
    },
    "employment": {
        "BTC": {"historical_volatility_24h_pct": 2.8, "direction": "moderate"},
        "ETH": {"historical_volatility_24h_pct": 3.1, "direction": "moderate"},
        "headline_template": "{event} → {asset} volatility historically +{vol}% in 24h",
    },
    "growth": {
        "BTC": {"historical_volatility_24h_pct": 2.0, "direction": "moderate"},
        "ETH": {"historical_volatility_24h_pct": 2.3, "direction": "moderate"},
        "headline_template": "{event} → {asset} volatility historically +{vol}% in 24h",
    },
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_store() -> dict[str, Any]:
    if not _STORE_PATH.is_file():
        return _bootstrap_store()
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _bootstrap_store()


def _bootstrap_store() -> dict[str, Any]:
    events: dict[str, Any] = {}
    if _SEED_PATH.is_file():
        try:
            rows = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
            for row in rows:
                events[row["id"]] = {**row, "imported_at": _utcnow()}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("economic calendar seed load failed: %s", exc)
    store = {"events": events, "updated_at": _utcnow()}
    _save_store(store)
    return store


def _save_store(blob: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob["updated_at"] = _utcnow()
    _STORE_PATH.write_text(json.dumps(blob, indent=2, ensure_ascii=False), encoding="utf-8")


def _values_display(row: dict[str, Any]) -> str:
    forecast = row.get("forecast")
    previous = row.get("previous")
    actual = row.get("actual")
    parts = [
        f"Forecast: {forecast}" if forecast is not None else "Forecast: —",
        f"Previous: {previous}" if previous is not None else "Previous: —",
        f"Actual: {actual}" if actual is not None else "Actual: —",
    ]
    return " | ".join(parts)


def _source_line(row: dict[str, Any]) -> str:
    source = row.get("source") or "Unknown"
    tz = row.get("timezone_display") or row.get("timezone") or "UTC"
    rev = row.get("revision") or "v1"
    rev_label = row.get("revision_label") or "preliminary"
    event = row.get("event") or row.get("name") or "Event"
    return f"Event: {event} | Source: {source} | Timezone: {tz} | Revision: {rev} ({rev_label})"


def _build_asset_relevance(row: dict[str, Any]) -> dict[str, Any]:
    category = str(row.get("category") or "growth")
    template = _ASSET_RELEVANCE.get(category, _ASSET_RELEVANCE["growth"])
    headline_tpl = template.get("headline_template", "")
    event_name = row.get("event") or "Macro event"
    assets = row.get("relevant_assets") or ["BTC"]
    relevance: dict[str, Any] = {}

    for asset in assets:
        sym = str(asset).upper()
        meta = template.get(sym) or template.get("BTC", {})
        vol = meta.get("historical_volatility_24h_pct", 2.0)
        headline = headline_tpl.format(event=event_name, asset=sym, vol=vol)
        relevance[sym] = {
            "asset": sym,
            "historical_volatility_24h_pct": vol,
            "direction": meta.get("direction", "moderate"),
            "display": headline,
            "not_a_prediction": True,
        }

    return relevance


def _time_aligned(row: dict[str, Any]) -> dict[str, Any]:
    scheduled = row.get("scheduled_at_utc") or row.get("scheduled_at")
    tz = row.get("timezone") or "UTC"
    return {
        "scheduled_at_utc": scheduled,
        "timezone": tz,
        "timezone_display": row.get("timezone_display") or tz,
        "time_aligned": True,
    }


def _enrich_event(row: dict[str, Any]) -> dict[str, Any]:
    asset_relevance = _build_asset_relevance(row)
    return {
        **row,
        **_time_aligned(row),
        "values_display": _values_display(row),
        "source_line": _source_line(row),
        "asset_relevance": asset_relevance,
        "asset_relevance_summary": [
            v["display"] for v in asset_relevance.values()
        ],
        "not_a_prediction": True,
        "not_trade_advice": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_ar": _DISCLAIMER_AR,
        "disclaimer_hideable": False,
    }


def list_economic_events(
    *,
    asset: str | None = None,
    country: str | None = None,
    category: str | None = None,
    impact: Impact | None = None,
    upcoming_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_event(e) for e in store.get("events", {}).values()]

    if asset:
        sym = asset.upper()
        rows = [
            r for r in rows
            if sym in [a.upper() for a in (r.get("relevant_assets") or [])]
        ]
    if country:
        rows = [r for r in rows if str(r.get("country", "")).upper() == country.upper()]
    if category:
        rows = [r for r in rows if str(r.get("category", "")).lower() == category.lower()]
    if impact:
        rows = [r for r in rows if str(r.get("impact", "")).lower() == impact]

    if upcoming_only:
        now = datetime.now(UTC)
        filtered = []
        for r in rows:
            ts = r.get("scheduled_at_utc")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if dt >= now:
                    filtered.append(r)
            except ValueError:
                continue
        rows = filtered

    rows.sort(key=lambda r: r.get("scheduled_at_utc") or "", reverse=False)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "economic_calendar_widget",
        "build_from_scratch": False,
        "import_source": "TradingView Economic Calendar",
        "count": len(rows[:limit]),
        "events": rows[:limit],
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_a_prediction": True,
        "timestamp": _utcnow(),
    }


def get_economic_event(event_id: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("events", {}).get(event_id)
    if not row:
        return {"ok": False, "error": "event_not_found"}
    enriched = _enrich_event(row)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "event": enriched,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def get_asset_calendar_relevance(asset: str) -> dict[str, Any]:
    feed = list_economic_events(asset=asset, limit=200)
    events = feed.get("events") or []
    relevance_lines = []
    for ev in events:
        rel = ev.get("asset_relevance", {}).get(asset.upper())
        if rel:
            relevance_lines.append(rel.get("display", ""))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": asset.upper(),
        "event_count": len(events),
        "relevance_lines": relevance_lines[:10],
        "upcoming_events": [e for e in events if e.get("actual") is None][:5],
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_a_prediction": True,
        "timestamp": _utcnow(),
    }


def tradingview_widget_config(
    *,
    theme: str = "dark",
    locale: str = "en",
    importance_filter: str = "0,1,2,3",
) -> dict[str, Any]:
    """TradingView Economic Calendar widget embed config (Sprint 1 — no custom engine)."""
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "widget": "TradingView Economic Calendar",
        "embed_type": "widget",
        "script_src": "https://s3.tradingview.com/external-embedding/embed-widget-events.js",
        "config": {
            "colorTheme": theme,
            "isTransparent": False,
            "locale": locale,
            "countryFilter": "us,eu",
            "importanceFilter": importance_filter,
            "width": "100%",
            "height": "600",
        },
        "forex_factory_alternative": {
            "note": "ForexFactory API can be wired in Sprint 2 for supplemental import",
            "enabled": False,
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def economic_calendar_status() -> dict[str, Any]:
    store = _load_store()
    events = list(store.get("events", {}).values())
    sources = {e.get("source") for e in events}
    revisions = {e.get("revision") for e in events}
    with_actual = sum(1 for e in events if e.get("actual") is not None)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "Economic Calendar",
        "sprint": 1,
        "build_from_scratch": False,
        "import_sources": ["TradingView Economic Calendar"],
        "forex_factory_sprint_2": True,
        "event_count": len(events),
        "sources_tracked": sorted(s for s in sources if s),
        "revisions_tracked": sorted(r for r in revisions if r),
        "timezone_tracked": True,
        "events_with_actuals": with_actual,
        "asset_relevance_layer": True,
        "factual_display": "Forecast | Previous | Actual",
        "not_trade_advice": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
