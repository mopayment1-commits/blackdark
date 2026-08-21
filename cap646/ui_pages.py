"""CAP646 UI route metadata."""

from __future__ import annotations

from cap646.waves import USER_FACING, WAVE_A, WAVE_B, WAVE_C


def hub_context() -> dict:
    return {
        "waves": [
            {"id": "A", "title": "Wave A — Foundations", "capability_ids": list(WAVE_A)},
            {"id": "B", "title": "Wave B — Alerts & Domains", "capability_ids": list(WAVE_B)},
            {"id": "C", "title": "Wave C — Market Depth", "capability_ids": list(WAVE_C)},
        ],
        "user_facing_count": len(USER_FACING),
        "api_base": "/api/cap646",
        "ui_base": "/cap646",
    }
