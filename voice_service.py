"""
BLACKDARK — AI Voice Trading (Wave 6).

Parses spoken or typed commands (Arabic + English) and routes to Oracle,
arbitrage, portfolio, research, panic, and simulation endpoints.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("BLACKDARK.Voice")

_ASSET_ALIASES: dict[str, str] = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "بيتكوين": "BTC",
    "بيت": "BTC",
    "ethereum": "ETH",
    "eth": "ETH",
    "ايث": "ETH",
    "إيث": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "سول": "SOL",
    "bnb": "BNB",
    "xrp": "XRP",
    "ripple": "XRP",
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_symbol(text: str) -> str | None:
    cleaned = text.upper().strip()
    if cleaned.endswith("USDT"):
        cleaned = cleaned[:-4]
    if cleaned in {"BTC", "ETH", "SOL", "BNB", "XRP"}:
        return cleaned
    lower = text.lower().strip()
    for alias, sym in _ASSET_ALIASES.items():
        if alias in lower:
            return sym
    match = re.search(r"\b(BTC|ETH|SOL|BNB|XRP)\b", cleaned)
    return match.group(1) if match else None


def _detect_intent(text: str) -> tuple[str, dict[str, Any]]:
    t = text.lower().strip()
    ar = text.strip()

    panic_words = ("panic", "stop", "emergency", "طوارئ", "ايقاف", "إيقاف", "وقف", "خطر")
    if any(w in t or w in ar for w in panic_words):
        return "panic", {}

    resume_words = ("resume", "continue", "استئناف", "كمل", "تابع")
    if any(w in t or w in ar for w in resume_words) and "wave" not in t:
        return "resume", {}

    arb_words = ("arbitrage", "arb", "scan", "مراجحة", "فرص", "فرصة")
    if any(w in t or w in ar for w in arb_words):
        return "arbitrage_scan", {}

    portfolio_words = ("portfolio", "محفظة", "محفظتي", "خطر المحفظة")
    if any(w in t or w in ar for w in portfolio_words):
        return "portfolio", {}

    research_words = ("research", "moat", "lab", "تقرير", "بحث", "مؤسسي")
    if any(w in t or w in ar for w in research_words):
        return "research", {}

    whale_words = ("whale", "حوت", "حيتان", "cvvd")
    if any(w in t or w in ar for w in whale_words):
        return "whale_scan", {}

    market_words = ("market", "sector", "radar", "سوق", "قطاع", "رادار")
    if any(w in t or w in ar for w in market_words):
        return "market_overview", {}

    sim_words = ("simulate", "simulation", "paper", "محاكاة", "تجربة")
    if any(w in t or w in ar for w in sim_words):
        sym = _normalize_symbol(text) or "BTC"
        return "simulate", {"symbol": sym}

    oracle_words = ("oracle", "analyze", "analysis", "حلل", "تحليل", "اشتر", "بيع", "انتظر")
    if any(w in t or w in ar for w in oracle_words):
        sym = _normalize_symbol(text)
        if sym:
            return "oracle", {"symbol": sym}

    sym = _normalize_symbol(text)
    if sym:
        return "oracle", {"symbol": sym}

    return "help", {}


async def process_voice_command(text: str) -> dict[str, Any]:
    """Execute a voice/text command and return speech-friendly response."""
    if not text or not text.strip():
        return {
            "success": False,
            "intent": "help",
            "speech": "Say a symbol or command — e.g. analyze BTC or scan arbitrage",
            "result": None,
            "timestamp": _utcnow_iso(),
        }

    intent, params = _detect_intent(text)
    logger.info("Voice command | intent=%s | text=%s", intent, text[:80])

    try:
        if intent == "oracle":
            from dashboard import (
                _build_full_oracle_response,
                _fetch_binance_ticker,
                _fetch_cvvd_whale_alert,
                _normalize_oracle_symbol,
            )

            symbol = params["symbol"]
            asset, pair = _normalize_oracle_symbol(symbol)
            market = await _fetch_binance_ticker(pair)
            if market is None:
                return {
                    "success": False,
                    "intent": intent,
                    "speech": f"{asset} not found on Binance",
                    "result": None,
                    "timestamp": _utcnow_iso(),
                }
            whale_alert = await _fetch_cvvd_whale_alert(
                asset, pair, float(market["price"])
            )
            payload = _build_full_oracle_response(
                asset,
                float(market["price"]),
                float(market["volume"]),
                float(market.get("quote_volume") or market["volume"] * market["price"]),
                float(market["change_24h"]),
                whale_alert=whale_alert,
            )
            try:
                from decision_enrichment import enrich_oracle_decision

                payload = enrich_oracle_decision(
                    payload, ux_mode="beginner", lang="en", register_signal=True
                )
            except Exception:
                logger.debug("voice oracle enrich failed", exc_info=True)
            speech = (
                payload.get("decision_sentence")
                or payload.get("oracle")
                or payload.get("narrative")
                or f"{symbol}: {payload.get('verdict')}"
            )
            return {
                "success": True,
                "intent": intent,
                "symbol": asset,
                "speech": speech,
                "speech_en": speech,
                "result": payload,
                "timestamp": _utcnow_iso(),
            }

        if intent == "arbitrage_scan":
            from arbitrage_catalog import scan_arbitrage_catalog

            scan = await scan_arbitrage_catalog()
            active = scan.get("active_live_types", 0) + scan.get("active_proxy_types", 0)
            top = scan.get("top_live_opportunity")
            if top:
                speech = (
                    f"Found {active} active arbitrage types out of 77. "
                    f"Best opportunity: {top.get('kind_label')} on {top.get('asset')} "
                    f"with net profit ${top.get('net_profit_usdt')}."
                )
            else:
                speech = f"Scanned 77 arbitrage types — {active} active. No profitable opportunity right now."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": scan,
                "timestamp": _utcnow_iso(),
            }

        if intent == "panic":
            from execution_engine import trigger_panic

            state = await trigger_panic()
            speech = "Panic stop activated. All auto-execution halted."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": state,
                "timestamp": _utcnow_iso(),
            }

        if intent == "resume":
            from execution_engine import resume_execution

            state = await resume_execution()
            speech = "Execution resumed in dry-run mode."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": state,
                "timestamp": _utcnow_iso(),
            }

        if intent == "research":
            from research_lab import build_research_lab_report

            report = await build_research_lab_report()
            moat = report.get("economic_moat") or {}
            speech = (
                f"Research Lab: Moat Score {moat.get('moat_score', 0)} out of 100. "
                f"Oracle accuracy {report.get('oracle_audit', {}).get('average_accuracy_percent', 0)}%."
            )
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": report,
                "timestamp": _utcnow_iso(),
            }

        if intent == "whale_scan":
            from dashboard import _fetch_cvvd_whale_context

            context = await _fetch_cvvd_whale_context(refresh=True)
            alerts = len(context.get("whale_alerts") or [])
            speech = f"Whale scan complete: {alerts} CVVD alerts."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": context,
                "timestamp": _utcnow_iso(),
            }

        if intent == "market_overview":
            from dashboard import _fetch_binance_market_overview

            assets = await _fetch_binance_market_overview(limit=10)
            overview = {"assets": assets, "count": len(assets)}
            speech = f"Market overview: {len(overview.get('assets') or [])} assets tracked."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": overview,
                "timestamp": _utcnow_iso(),
            }

        if intent == "simulate":
            from trade_simulator import simulate_spot_trade

            sym = params.get("symbol", "BTC")
            sim = await simulate_spot_trade(sym, "buy", 1000.0, hold_hours=24)
            base_pnl = (sim.get("scenarios") or {}).get("base", {}).get("pnl_usd", 0)
            speech = f"Simulation {sym}: base-case P&L ${base_pnl}."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "result": sim,
                "timestamp": _utcnow_iso(),
            }

    except Exception as exc:
        logger.exception("Voice command failed | intent=%s", intent)
        return {
            "success": False,
            "intent": intent,
            "speech": f"Error: {exc}",
            "result": None,
            "timestamp": _utcnow_iso(),
        }

    help_speech = (
        "Commands: analyze BTC · scan arbitrage · portfolio status · Research Lab · "
        "whale scan · panic stop · simulate ETH"
    )
    return {
        "success": True,
        "intent": "help",
        "speech": help_speech,
        "speech_en": "Commands: analyze BTC, scan arbitrage, portfolio, research, whale scan, panic, simulate ETH",
        "result": {"commands": ["oracle BTC", "arbitrage scan", "panic", "research", "whale", "simulate SOL"]},
        "timestamp": _utcnow_iso(),
    }
