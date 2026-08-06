"""
BLACKDARK — TODAY command-center feed (Master Dashboard Spec).

Composes: Since You Left · Market Pulse · Needs Your Attention · Ask hints.
English payloads only. Fail-soft: never break the dashboard shell.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("BLACKDARK.TodayFeed")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _greeting_name(user: dict | None) -> str:
    if not user:
        return "there"
    email = str(user.get("email") or "").strip()
    if email and "@" in email:
        return email.split("@", 1)[0].replace(".", " ").title()[:24] or "there"
    name = str(user.get("name") or "").strip()
    return name[:24] if name else "there"


def _hour_greeting() -> str:
    hour = datetime.now(timezone.utc).hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


async def _safe_market_assets(limit: int = 8) -> list[dict[str, Any]]:
    try:
        from dashboard import _fetch_binance_market_overview

        rows = await _fetch_binance_market_overview(limit=limit)
        return list(rows or [])
    except Exception:
        logger.debug("today market overview failed", exc_info=True)
        return []


async def _safe_inbox(user: dict | None, limit: int = 8) -> list[dict[str, Any]]:
    try:
        from in_app_alerts import list_in_app_alerts

        email = (user or {}).get("email")
        return list_in_app_alerts(limit=limit, user_email=email, unread_only=False) or []
    except Exception:
        logger.debug("today inbox failed", exc_info=True)
        return []


async def _safe_accuracy() -> dict[str, Any]:
    try:
        from oracle_track_record import public_track_record

        summary = public_track_record()
        if isinstance(summary, dict):
            live = summary.get("cumulative") or {}
            return {
                "accuracy_pct": live.get("hit_rate_percent"),
                "hit_rate": live.get("hit_rate_percent"),
                **summary,
            }
    except Exception:
        logger.debug("today accuracy failed", exc_info=True)
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        payload = await build_public_accuracy_payload()
        if isinstance(payload, dict):
            return {
                "accuracy_pct": payload.get("recent_hit_rate_percent"),
                "hit_rate": payload.get("recent_hit_rate_percent"),
                **payload,
            }
    except Exception:
        logger.debug("today public_accuracy failed", exc_info=True)
    return {}


def _importance_from_change(change: float) -> str:
    abs_c = abs(change)
    if abs_c >= 5:
        return "High Importance"
    if abs_c >= 2:
        return "Medium Risk"
    return "Watch"


def _build_since_you_left(assets: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    for a in assets[:6]:
        sym = str(a.get("symbol") or a.get("asset") or "").upper()
        if not sym:
            continue
        change = float(a.get("change_24h") or 0)
        verdict = str(a.get("verdict") or "WAIT").upper()
        if abs(change) < 1.2 and verdict in {"WAIT", "NEUTRAL", ""}:
            continue
        direction = "broke higher" if change > 0 else "under pressure"
        if "BUY" in verdict or verdict == "BULLISH":
            title = f"{sym} structure leaning ACT"
        elif "SELL" in verdict or "BEAR" in verdict:
            title = f"{sym} caution — prefer WAIT"
        else:
            title = f"{sym} {direction}"
        changes.append(
            {
                "asset": sym,
                "title": title,
                "detail": f"24h {change:+.2f}% · score {a.get('opportunity_score', '—')}",
                "importance": _importance_from_change(change),
                "change_24h": round(change, 2),
                "action_hint": "WAIT" if change < 0 or "SELL" in verdict else ("ACT" if "BUY" in verdict else "WAIT"),
            }
        )

    for alert in alerts[:4]:
        title = str(alert.get("title") or alert.get("message") or "").strip()
        if not title:
            continue
        changes.append(
            {
                "asset": str(alert.get("asset") or "SYS").upper(),
                "title": title[:96],
                "detail": str(alert.get("body") or alert.get("channel") or "In-app alert")[:120],
                "importance": "High Interest" if not alert.get("read") else "Noted",
                "change_24h": None,
                "action_hint": "WAIT",
                "alert_id": alert.get("id"),
            }
        )

    # Dedupe by title, keep top 7 then surface AI top 3
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in changes:
        key = f"{row.get('asset')}:{row.get('title')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    ranked = sorted(
        unique,
        key=lambda r: (
            0 if "High" in str(r.get("importance")) else 1,
            -abs(float(r.get("change_24h") or 0)),
        ),
    )
    top3 = ranked[:3]
    return {
        "detected_count": len(ranked),
        "items": top3,
        "all_items": ranked[:7],
        "empty_message": "Quiet since your last visit — ask BLACKDARK or open Oracle on BTC.",
    }


def _build_market_pulse(assets: list[dict[str, Any]], accuracy: dict[str, Any]) -> dict[str, Any]:
    if not assets:
        return {
            "states": [
                {"label": "Trend", "value": "Unknown"},
                {"label": "Risk", "value": "Unknown"},
                {"label": "Liquidity", "value": "Unknown"},
                {"label": "Volatility", "value": "Unknown"},
                {"label": "Sentiment", "value": "Unknown"},
                {"label": "Smart Money", "value": "Unknown"},
            ],
            "summary": "Market pulse unavailable — data feed delayed or offline.",
            "data_delayed": True,
        }

    ups = sum(1 for a in assets if float(a.get("change_24h") or 0) > 0)
    downs = sum(1 for a in assets if float(a.get("change_24h") or 0) < 0)
    avg_abs = sum(abs(float(a.get("change_24h") or 0)) for a in assets) / max(len(assets), 1)
    bullish = ups > downs + 1
    bearish = downs > ups + 1

    trend = "Neutral → Bullish" if bullish else ("Neutral → Bearish" if bearish else "Neutral")
    risk = "Elevated" if avg_abs >= 3 else ("Contained" if avg_abs < 1.5 else "Moderate")
    vol = "Expanding" if avg_abs >= 3.5 else ("Contracting" if avg_abs < 1.2 else "Steady")
    sentiment = "Optimistic" if bullish else ("Cautious" if bearish else "Balanced")
    smart = "Accumulating" if bullish and avg_abs < 4 else ("Distributing" if bearish else "Mixed")
    liquidity = "Improving" if ups >= downs else "Mixed"

    hit = accuracy.get("accuracy_pct") or accuracy.get("hit_rate") or accuracy.get("accuracy")
    summary_bits = [
        f"Breadth {ups} up / {downs} down across watched majors.",
        f"Average |move| ~{avg_abs:.1f}%.",
    ]
    if hit is not None:
        try:
            summary_bits.append(f"Public ledger accuracy ~{float(hit):.1f}%.")
        except (TypeError, ValueError):
            pass

    return {
        "states": [
            {"label": "Trend", "value": trend},
            {"label": "Risk", "value": risk},
            {"label": "Liquidity", "value": liquidity},
            {"label": "Volatility", "value": vol},
            {"label": "Sentiment", "value": sentiment},
            {"label": "Smart Money", "value": smart},
        ],
        "summary": " ".join(summary_bits),
        "data_delayed": False,
        "explain_seed": (
            f"Three drivers today: breadth is {ups} up vs {downs} down; "
            f"volatility looks {vol.lower()}; posture leans {sentiment.lower()}. "
            "Open Evidence on any asset for source weights."
        ),
    }


def _build_attention(
    since_items: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in since_items[:3]:
        out.append(
            {
                "title": row.get("title"),
                "reason": row.get("detail"),
                "asset": row.get("asset"),
                "priority": row.get("importance") or "Attention",
                "cta": "Open Analysis",
            }
        )
    if len(out) < 3:
        for alert in alerts:
            if len(out) >= 3:
                break
            title = str(alert.get("title") or "").strip()
            if not title:
                continue
            out.append(
                {
                    "title": title[:96],
                    "reason": "Survived Truth + Half-Life gates — worth a look.",
                    "asset": alert.get("asset") or "ALERT",
                    "priority": "Inbox",
                    "cta": "Open Inbox",
                }
            )
    while len(out) < 3:
        defaults = [
            {
                "title": "Run Oracle on BTC",
                "reason": "Anchor the session with one ACT/WAIT sentence.",
                "asset": "BTC",
                "priority": "Ritual",
                "cta": "Get Decision",
            },
            {
                "title": "Check Public Accuracy Ledger",
                "reason": "Trust is proof — review hits and misses.",
                "asset": "LEDGER",
                "priority": "Trust",
                "cta": "Open Ledger",
            },
            {
                "title": "Ask what changed in your watchlist",
                "reason": "Use Ask BLACKDARK instead of scanning 50 charts.",
                "asset": "ASK",
                "priority": "Focus",
                "cta": "Ask",
            },
        ]
        out.append(defaults[len(out)])
    return out[:3]


def _ask_suggestions(pulse: dict[str, Any]) -> list[str]:
    states = {s["label"]: s["value"] for s in pulse.get("states") or []}
    trend = str(states.get("Trend") or "")
    suggestions = [
        "What matters most since I left?",
        "Explain the market in 30 seconds",
        "Why is BTC moving today?",
        "Find unusual activity",
        "What's the biggest risk today?",
    ]
    if "Bullish" in trend:
        suggestions.insert(1, "Which majors still look WAIT despite the bounce?")
    if "Bearish" in trend:
        suggestions.insert(1, "Where is WAIT stronger than chasing a bounce?")
    return suggestions[:6]


async def build_today_feed(user: dict | None = None) -> dict[str, Any]:
    assets = await _safe_market_assets(limit=10)
    alerts = await _safe_inbox(user, limit=8)
    accuracy = await _safe_accuracy()
    since = _build_since_you_left(assets, alerts)
    pulse = _build_market_pulse(assets, accuracy)
    attention = _build_attention(since.get("items") or [], alerts)

    hit = accuracy.get("accuracy_pct") or accuracy.get("hit_rate") or accuracy.get("accuracy")
    accuracy_display = None
    try:
        if hit is not None:
            accuracy_display = round(float(hit), 1)
    except (TypeError, ValueError):
        accuracy_display = None

    return {
        "generated_at": _utcnow_iso(),
        "greeting": f"{_hour_greeting()}, {_greeting_name(user)}",
        "tagline": "Here's what changed since you left.",
        "since_you_left": since,
        "market_pulse": pulse,
        "needs_your_attention": attention,
        "ask_suggestions": _ask_suggestions(pulse),
        "ai_accuracy_pct": accuracy_display,
        "data_status": "delayed" if pulse.get("data_delayed") else "live",
        "compliance": {
            "disclaimer": "Not financial advice. Decisions are ACT/WAIT analytics — verify on the Public Accuracy Ledger.",
            "trust_basis": "public_accuracy_ledger + decision_certificate",
        },
    }
