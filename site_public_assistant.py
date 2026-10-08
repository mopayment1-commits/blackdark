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


def _clip(text: str, n: int = 400) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def reply_site_assistant(message: str, page_context: dict[str, Any] | None) -> dict[str, Any]:
    msg = (message or "").strip()
    ctx = page_context or {}
    if not msg:
        return {"reply": "Ask about the decision or ledger shown on this page.", "refusal": False}
    if _ADVICE_RE.search(msg):
        return {"reply": REFUSAL, "refusal": True}

    pulse = ctx.get("trust_pulse") or {}
    action = pulse.get("action") or ctx.get("pulse_action")
    symbol = pulse.get("symbol") or ctx.get("pulse_symbol")
    sentence = pulse.get("sentence") or ctx.get("pulse_sentence")
    ledger = ctx.get("ledger") or {}
    parts: list[str] = []
    if action and symbol:
        parts.append(f"On this page Trust Pulse shows {action} on {symbol}.")
    if sentence:
        parts.append(f"Summary: {_clip(str(sentence), 220)}")
    if ledger:
        bits = []
        for key in ("logged", "resolved", "pending", "accuracy_percent"):
            if key in ledger and ledger[key] is not None:
                bits.append(f"{key}={ledger[key]}")
        if bits:
            parts.append("Public ledger counters here: " + ", ".join(bits) + ".")
    seal = ctx.get("seal_hash")
    if seal:
        parts.append(f"Seal hash visible: {_clip(str(seal), 32)}.")
    if not parts:
        parts.append(
            "I only explain what is visible on this page (Trust Pulse, Public Accuracy Ledger, Seal). "
            "Open /oracle-accuracy to verify outcomes."
        )
    parts.append("Analytical context only — " + REFUSAL)
    return {"reply": " ".join(parts), "refusal": False}
