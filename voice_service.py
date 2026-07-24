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
            "speech": "قل اسم العملة أو الأمر — مثل: حلل BTC أو امسح المراجحة",
            "speech_en": "Say a symbol or command — e.g. analyze BTC or scan arbitrage",
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
                    "speech": f"لم أجد {asset} في Binance",
                    "speech_en": f"{asset} not found on Binance",
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
            speech = payload.get("oracle") or payload.get("narrative") or f"{symbol}: {payload.get('verdict')}"
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
                    f"وجدت {active} نوع مراجحة نشط من 77. "
                    f"أفضل فرصة: {top.get('kind_label')} على {top.get('asset')} "
                    f"بربح صافي {top.get('net_profit_usdt')} دولار."
                )
            else:
                speech = f"مسح 77 نوع مراجحة — {active} نشط حالياً. لا توجد فرصة مربحة فورية."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": speech,
                "result": scan,
                "timestamp": _utcnow_iso(),
            }

        if intent == "panic":
            from execution_engine import trigger_panic

            state = await trigger_panic()
            speech = "تم تفعيل زر الطوارئ. كل التنفيذ التلقائي متوقف."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": "Panic stop activated. All auto-execution halted.",
                "result": state,
                "timestamp": _utcnow_iso(),
            }

        if intent == "resume":
            from execution_engine import resume_execution

            state = await resume_execution()
            speech = "تم استئناف التنفيذ في وضع المحاكاة."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": "Execution resumed in dry-run mode.",
                "result": state,
                "timestamp": _utcnow_iso(),
            }

        if intent == "research":
            from research_lab import build_research_lab_report

            report = await build_research_lab_report()
            moat = report.get("economic_moat") or {}
            speech = (
                f"Research Lab: Moat Score {moat.get('moat_score', 0)} من 100. "
                f"دقة Oracle {report.get('oracle_audit', {}).get('average_accuracy_percent', 0)}%."
            )
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": speech,
                "result": report,
                "timestamp": _utcnow_iso(),
            }

        if intent == "whale_scan":
            from dashboard import _fetch_cvvd_whale_context

            context = await _fetch_cvvd_whale_context(refresh=True)
            alerts = len(context.get("whale_alerts") or [])
            speech = f"مسح الحيتان: {alerts} تنبيه CVVD نشط."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": f"Whale scan complete: {alerts} CVVD alerts.",
                "result": context,
                "timestamp": _utcnow_iso(),
            }

        if intent == "market_overview":
            from dashboard import _fetch_binance_market_overview

            assets = await _fetch_binance_market_overview(limit=10)
            overview = {"assets": assets, "count": len(assets)}
            speech = f"نظرة السوق: {len(overview.get('assets') or [])} أصل متابع."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": speech,
                "result": overview,
                "timestamp": _utcnow_iso(),
            }

        if intent == "simulate":
            from trade_simulator import simulate_spot_trade

            sym = params.get("symbol", "BTC")
            sim = await simulate_spot_trade(sym, "buy", 1000.0, hold_hours=24)
            base_pnl = (sim.get("scenarios") or {}).get("base", {}).get("pnl_usd", 0)
            speech = f"محاكاة {sym}: الربح الأساسي {base_pnl} دولار."
            return {
                "success": True,
                "intent": intent,
                "speech": speech,
                "speech_en": speech,
                "result": sim,
                "timestamp": _utcnow_iso(),
            }

    except Exception as exc:
        logger.exception("Voice command failed | intent=%s", intent)
        return {
            "success": False,
            "intent": intent,
            "speech": f"حدث خطأ: {exc}",
            "speech_en": f"Error: {exc}",
            "result": None,
            "timestamp": _utcnow_iso(),
        }

    help_speech = (
        "الأوامر: حلل BTC · امسح المراجحة · حالة المحفظة · Research Lab · "
        "مسح الحيتان · زر الطوارئ · محاكاة ETH"
    )
    return {
        "success": True,
        "intent": "help",
        "speech": help_speech,
        "speech_en": "Commands: analyze BTC, scan arbitrage, portfolio, research, whale scan, panic, simulate ETH",
        "result": {"commands": ["oracle BTC", "arbitrage scan", "panic", "research", "whale", "simulate SOL"]},
        "timestamp": _utcnow_iso(),
    }
