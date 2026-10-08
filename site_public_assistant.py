"""On-page assistant — visible decision/ledger context only; no financial advice."""

from __future__ import annotations

import re
from typing import Any

REFUSAL = "Not financial advice."

_ADVICE_RE = re.compile(
    r"\b("
    r"should\s+i\s+(buy|sell|trade|invest)|"
    r"buy\s+now|sell\s+now|"
    r"financial\s+advice|"
    r"guaranteed\s+return|"
    r"what\s+should\s+i\s+do\s+with\s+my\s+money"
    r")\b",
    re.I,
)

_SYMBOL_RE = re.compile(
    r"\b(BTC|ETH|SOL|XRP|BNB|ADA|DOGE|DOT|AVAX|LINK|MATIC|LTC)\b",
    re.I,
)
_AR_ETH = re.compile(r"إيث|ايث|ايثريوم|ethereum", re.I)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_SMALL_TALK_RE = re.compile(
    r"^(hi|hello|hey|howdy|yo|sup|hola|salut|مرحبا|مرحباً|السلام|اهلا|أهلا)\b",
    re.I,
)
_PAGE_SIGNAL_RE = re.compile(
    r"trust\s*pulse|pulse|oracle|ledger|accuracy|decision|verdict|wait|symbol|"
    r"btc|eth|سعر|انتظار|قرار|شريط|ledger|seal|ختم",
    re.I,
)
_THREAD_MAX = 8


def _clip(text: str, n: int = 400) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def sanitize_assistant_thread(thread: list[Any] | None) -> list[dict[str, str]]:
    return _sanitize_thread(thread)


def _sanitize_thread(thread: list[Any] | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not isinstance(thread, list):
        return out
    for item in thread[-_THREAD_MAX:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "bot"}:
            continue
        topic = _clip(str(item.get("topic") or item.get("summary") or ""), 200)
        topic = _EMAIL_RE.sub("[redacted]", topic)
        if not topic:
            continue
        row: dict[str, str] = {"role": role, "topic": topic}
        sym = str(item.get("symbol") or "").strip().upper()
        if sym and re.fullmatch(r"[A-Z0-9]{2,12}", sym):
            row["symbol"] = sym
        intent = str(item.get("intent") or "").strip().lower()
        if intent in {"price", "why", "explain"}:
            row["intent"] = intent
        out.append(row)
    return out


def resolve_query_symbol(message: str, thread: list[dict[str, str]] | None = None) -> str | None:
    msg = (message or "").strip()
    hit = _SYMBOL_RE.search(msg)
    if hit:
        return hit.group(1).upper()
    if _AR_ETH.search(msg):
        return "ETH"
    for turn in reversed(thread or []):
        sym = turn.get("symbol")
        if sym:
            return str(sym).upper()
    return None


def _is_follow_up(message: str) -> bool:
    msg = (message or "").strip()
    if len(msg) > 160:
        return False
    return bool(
        re.search(
            r"(^و)?ما\s|سبب|لماذا|why\b|reason|what about|and the|also\b|follow",
            msg,
            re.I,
        )
    )


def classify_intent(message: str, thread: list[dict[str, str]], follow_up: bool) -> str:
    msg = (message or "").lower()
    if follow_up and thread:
        for turn in reversed(thread):
            if turn.get("intent") in {"price", "why", "explain"}:
                if re.search(r"سبب|why|wait|انتظار|reason", message or "", re.I):
                    return "why"
                return str(turn["intent"])
    if re.search(r"price|سعر|كم\s|cost|\$|quote", msg, re.I) or "سعر" in (message or ""):
        return "price"
    if re.search(r"why|سبب|wait|انتظار|reason|لماذا", message or "", re.I):
        return "why"
    return "explain"


def message_wants_oracle(message: str, thread: list[dict[str, str]] | None) -> bool:
    intent = classify_intent(message, thread or [], _is_follow_up(message))
    return intent in {"price", "why"}


def is_small_talk(message: str) -> bool:
    msg = (message or "").strip()
    if not msg or len(msg) > 32:
        return False
    return bool(_SMALL_TALK_RE.match(msg))


def wants_trust_pulse_context(message: str, symbol: str | None, intent: str) -> bool:
    if symbol or intent in {"price", "why"}:
        return True
    if _PAGE_SIGNAL_RE.search(message or ""):
        return True
    if re.search(r"what\s+is\s+shown|this\s+page|on\s+this\s+page|visible\s+here", message or "", re.I):
        return True
    return False


def _format_oracle_line(symbol: str, oracle: dict[str, Any], intent: str) -> str:
    price = oracle.get("price")
    score = oracle.get("opportunity_score") if oracle.get("opportunity_score") is not None else oracle.get("score")
    action = oracle.get("decision_action") or oracle.get("verdict") or oracle.get("action")
    sentence = oracle.get("decision_sentence") or oracle.get("oracle") or oracle.get("narrative")
    bits: list[str] = []
    if intent == "price" and price is not None:
        try:
            p = float(price)
            bits.append(f"Public quick read for {symbol}: about ${p:,.2f}")
        except (TypeError, ValueError):
            bits.append(f"Public quick read for {symbol} is on this page’s oracle strip.")
    if score is not None:
        bits.append(f"model score {score}/100")
    if action:
        bits.append(f"state {action}")
    if intent == "why" and sentence:
        bits.append(f"stated reason: {_clip(str(sentence), 180)}")
    elif sentence and intent != "price":
        bits.append(_clip(str(sentence), 180))
    return ", ".join(bits) if bits else f"No extra oracle fields for {symbol} right now."


def reply_site_assistant(
    message: str,
    page_context: dict[str, Any] | None,
    *,
    thread: list[Any] | None = None,
    oracle_ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    msg = (message or "").strip()
    ctx = page_context or {}
    history = _sanitize_thread(thread)
    if not msg:
        return {"reply": "Ask about the decision or ledger shown on this page.", "refusal": False}

    if _ADVICE_RE.search(msg):
        return {"reply": REFUSAL, "refusal": True}

    if is_small_talk(msg):
        return {
            "reply": (
                "Hi — ask about a symbol (e.g. ETH price) or why the model shows wait on this page. "
                "Analytical context only — "
                + REFUSAL
            ),
            "refusal": False,
            "turn": {"symbol": None, "intent": "explain", "topic": _clip(msg, 120)},
        }

    follow = _is_follow_up(msg)
    symbol = resolve_query_symbol(msg, history)
    intent = classify_intent(msg, history, follow)

    pulse = ctx.get("trust_pulse") or {}
    page_sym = (pulse.get("symbol") or ctx.get("pulse_symbol") or "").strip().upper() or None
    page_action = pulse.get("action") or ctx.get("pulse_action")
    page_sentence = pulse.get("sentence") or ctx.get("pulse_sentence")

    parts: list[str] = []
    user_hook = _clip(msg, 100)

    if follow and history:
        prior = next((t for t in reversed(history) if t.get("role") == "bot"), None)
        if prior:
            parts.append(f"Continuing from your last topic ({prior.get('topic', '')[:80]}).")

    if symbol:
        if intent == "price":
            parts.append(f"You asked about {symbol} price ({user_hook}).")
        elif intent == "why":
            parts.append(f"You asked why {symbol} is in a wait/hold style state ({user_hook}).")
        else:
            parts.append(f"On your question about {symbol}: {_clip(msg, 120)}.")
    else:
        parts.append(f"On your question: {_clip(msg, 140)}.")

    oracle_sym = (oracle_ctx or {}).get("symbol") or (oracle_ctx or {}).get("asset")
    if oracle_ctx and symbol and str(oracle_sym or symbol).upper() == symbol:
        parts.append(_format_oracle_line(symbol, oracle_ctx, intent))
    elif symbol and intent in {"price", "why"}:
        parts.append(
            f"I could not refresh a live {symbol} oracle snapshot; use the oracle block on this page for that symbol."
        )

    show_pulse = wants_trust_pulse_context(msg, symbol, intent)
    if show_pulse and page_sym and symbol and page_sym != symbol:
        parts.append(
            f"The Trust Pulse strip on this page is still showing {page_action or '—'} on {page_sym}, not {symbol}."
        )
    elif show_pulse and page_sym and (not symbol or page_sym == symbol):
        if intent == "why" and page_sentence and not oracle_ctx:
            parts.append(f"Visible pulse line: {_clip(str(page_sentence), 200)}")
        elif intent == "explain" and page_action and page_sym:
            parts.append(f"On this page Trust Pulse shows {page_action} on {page_sym}.")

    ledger = ctx.get("ledger") or {}
    if ledger and re.search(r"ledger|accuracy|سجل", msg, re.I):
        bits = []
        for key in ("logged", "resolved", "pending", "accuracy_percent"):
            if key in ledger and ledger[key] is not None:
                bits.append(f"{key}={ledger[key]}")
        if bits:
            parts.append("Public ledger counters here: " + ", ".join(bits) + ".")

    seal = ctx.get("seal_hash")
    if seal and re.search(r"seal|hash|ختم", msg, re.I):
        parts.append(f"Seal hash visible: {_clip(str(seal), 32)}.")

    if len(parts) == 1 and not symbol:
        parts.append(
            "I explain what is visible here (Trust Pulse, Public Accuracy Ledger, Seal). "
            "Name a symbol (e.g. ETH) or ask about the wait reason."
        )

    reply = " ".join(parts) + " Analytical context only — " + REFUSAL
    turn = {
        "symbol": symbol,
        "intent": intent,
        "topic": _clip(msg, 120),
    }
    return {"reply": reply, "refusal": False, "turn": turn}
