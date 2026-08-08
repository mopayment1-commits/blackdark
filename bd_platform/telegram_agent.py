"""Autonomous Telegram AI agent — natural language over platform APIs."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.TelegramAgent")


async def handle_agent_message(text: str, *, user_id: int | None = None) -> dict[str, Any]:
    from chat_service import process_chat

    reply = await process_chat(text)
    return {
        "agent": "BLACKDARK Telegram AI",
        "input": text[:500],
        "reply": reply.get("reply") or "",
        "source": reply.get("source", "blackdark"),
        "timestamp": datetime.now(UTC).isoformat(),
        "capabilities": [
            "oracle_accuracy",
            "arbitrage_scan",
            "whale_alerts",
            "portfolio_analysis",
            "risk_status",
        ],
    }
