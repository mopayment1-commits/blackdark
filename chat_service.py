"""
BLACKDARK — AI Chat (Week 2).

Interactive market assistant: Oracle context + whale + sectors + optional OpenAI.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.Chat")

_ASSET_ALIASES: dict[str, str] = {
    "bitcoin": "BTC", "btc": "BTC", "بيتكوين": "BTC", "بيت": "BTC",
    "ethereum": "ETH", "eth": "ETH", "ايث": "ETH", "إيث": "ETH",
    "solana": "SOL", "sol": "SOL", "سول": "SOL",
    "bnb": "BNB", "xrp": "XRP",
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _extract_symbol(text: str) -> str | None:
    upper = text.upper()
    for sym in ("BTC", "ETH", "SOL", "BNB", "XRP"):
        if sym in upper:
            return sym
    lower = text.lower()
    for alias, sym in _ASSET_ALIASES.items():
        if alias in lower:
            return sym
    return None


async def _gather_market_context(symbol: str | None) -> dict[str, Any]:
    from dashboard import (
        _build_full_oracle_response,
        _fetch_binance_market_overview,
        _fetch_binance_ticker,
        _fetch_cvvd_whale_alert,
        _normalize_oracle_symbol,
    )

    ctx: dict[str, Any] = {"symbol": symbol, "timestamp": _utcnow_iso()}
    overview = await _fetch_binance_market_overview(limit=5)
    ctx["top_assets"] = overview[:3]

    if symbol:
        asset, pair = _normalize_oracle_symbol(symbol)
        ticker = await _fetch_binance_ticker(pair)
        if ticker:
            whale = await _fetch_cvvd_whale_alert(asset, pair, float(ticker["price"]))
            oracle = _build_full_oracle_response(
                asset,
                float(ticker["price"]),
                float(ticker["volume"]),
                float(ticker.get("quote_volume") or ticker["volume"] * ticker["price"]),
                float(ticker["change_24h"]),
                whale_alert=whale,
            )
            ctx["oracle"] = {
                "symbol": asset,
                "verdict": oracle.get("verdict"),
                "score": oracle.get("opportunity_score"),
                "oracle": oracle.get("oracle"),
                "action": oracle.get("action"),
                "confidence": oracle.get("confidence"),
                "risk_level": oracle.get("risk_level"),
                "whale_alert": oracle.get("whale_alert"),
                "change_24h": oracle.get("change_24h"),
                "price": oracle.get("price"),
            }

    try:
        from whale_tracker import get_latest_institutional_context

        inst = await get_latest_institutional_context()
        ctx["whale_alerts"] = len(inst.get("whale_alerts") or [])
        ctx["sector_flows"] = (inst.get("sector_flows") or [])[:3]
    except Exception:
        ctx["whale_alerts"] = 0

    return ctx


def _rule_based_reply(_message: str, context: dict[str, Any]) -> str:
    symbol = context.get("symbol")
    oracle = context.get("oracle") or {}

    if symbol and oracle:
        verdict = oracle.get("verdict", "WAIT")
        score = oracle.get("score") or oracle.get("opportunity_score", 0)
        action = oracle.get("action") or oracle.get("oracle") or ""
        whale = oracle.get("whale_alert") or "—"
        change = oracle.get("change_24h", 0)
        price = oracle.get("price", 0)

        return (
            f"📊 **{symbol}** @ ${price:,.2f} ({change:+.2f}% 24h)\n\n"
            f"**Verdict:** {verdict} · Score {score}/100\n"
            f"**Action:** {action}\n"
            f"**Whales:** {whale}\n\n"
            f"Confidence: {oracle.get('confidence', '—')}% · Risk: {oracle.get('risk_level', '—')}"
        )

    whales = context.get("whale_alerts", 0)
    tops = context.get("top_assets") or []
    top_line = ", ".join(
        f"{a.get('symbol')} {a.get('change_24h', 0):+.1f}%"
        for a in tops[:3]
    )

    return (
        "Hi! I'm the BLACKDARK AI assistant.\n\n"
        f"🔥 Top movers: {top_line or '—'}\n"
        f"🐋 Active CVVD alerts: {whales}\n\n"
        "Ask: «What should I do with BTC?» or «Analyze ETH»"
    )


async def _openai_reply(message: str, context: dict[str, Any], history: list[dict]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    system = (
        "You are BLACKDARK AI Chat on Trust OS — you explain the current decision context "
        "(Oracle verdict, why factors, risk). You do NOT replace the Oracle certificate. "
        "Answer in the user's language (Arabic or English). "
        "Be clear: Act / Wait / Caution with reasons from live context. "
        "Never guarantee profits, accuracy, or returns. Not financial advice. "
        "Point users to the Public Accuracy Ledger when relevant. Max 180 words."
    )
    messages = [{"role": "system", "content": system}]
    messages.append(
        {
            "role": "system",
            "content": f"Live context JSON:\n{json.dumps(context, default=str)[:3000]}",
        }
    )
    for turn in history[-6:]:
        role = turn.get("role", "user")
        if role in {"user", "assistant"}:
            messages.append({"role": role, "content": str(turn.get("content", ""))[:500]})
    messages.append({"role": "user", "content": message[:800]})

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "max_tokens": 350,
        "temperature": 0.4,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (aiohttp.ClientError, KeyError, TypeError, ValueError):
        logger.exception("OpenAI chat failed")
        return None


async def process_chat(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Main chat handler."""
    text = (message or "").strip()
    if not text:
        return {
            "reply": "Ask about any asset — e.g. What should I do with BTC?",
            "symbol": None,
            "source": "system",
            "timestamp": _utcnow_iso(),
        }

    symbol = _extract_symbol(text)
    context = await _gather_market_context(symbol)
    hist = history or []

    reply = await _openai_reply(text, context, hist)
    source = "openai" if reply else "blackdark"
    if not reply:
        reply = _rule_based_reply(text, context)

    from decision_certificate import compliance_footer_block

    return {
        "reply": reply,
        "symbol": symbol,
        "context_summary": {
            "oracle_verdict": (context.get("oracle") or {}).get("verdict"),
            "oracle_score": (context.get("oracle") or {}).get("score"),
            "whale_alerts": context.get("whale_alerts"),
        },
        "source": source,
        "timestamp": _utcnow_iso(),
        "compliance_footer": compliance_footer_block(
            surface="ai_chat",
            trust_basis="oracle_context + public_accuracy_ledger",
        ),
    }
