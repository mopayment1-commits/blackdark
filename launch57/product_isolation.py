"""Launch-57 product isolation — first-screen scope lock for 55 ready items."""

from __future__ import annotations

from typing import Any

from launch57.tier_distribution import BLOCKED_EXTERNAL_LAUNCH_IDS

READY_LAUNCH57_COUNT = 55
READY_LAUNCH57_IDS = frozenset(range(1, 58)) - frozenset(BLOCKED_EXTERNAL_LAUNCH_IDS)
PRODUCT_ISOLATION_ENABLED = True
OUT_OF_SCOPE_LABEL = "خارج نطاق الإطلاق"

# Legacy / non-Launch-57 surfaces hidden on first screen when isolation is active.
ISOLATED_FIRST_SCREEN_ELEMENTS: tuple[dict[str, str], ...] = (
    {"id": "toolbar-since-you-left", "surface": "toolbar", "legacy_path": "/since-you-left"},
    {"id": "toolbar-miss-feed", "surface": "toolbar", "legacy_path": "/miss-feed"},
    {"id": "toolbar-coverage-honesty", "surface": "toolbar", "legacy_path": "/coverage-honesty"},
    {"id": "toolbar-corpus-passport", "surface": "toolbar", "legacy_path": "/corpus-passport"},
    {"id": "toolbar-portfolio", "surface": "toolbar", "legacy_path": "#portfolio"},
    {"id": "toolbar-stealth", "surface": "toolbar", "legacy_path": "#stealth"},
    {"id": "section-since-you-left", "surface": "section", "legacy_path": "/since-you-left"},
    {"id": "section-market-radar", "surface": "section", "legacy_path": "/api/market/overview"},
    {"id": "section-operate-digest", "surface": "section", "legacy_path": "/api/subscriber/value"},
    {"id": "section-portfolio", "surface": "section", "legacy_path": "/portfolio/analyze"},
    {"id": "section-half-life-clock", "surface": "section", "legacy_path": "/kill-rate"},
    {"id": "section-stealth", "surface": "section", "legacy_path": "/api/whale/stealth-advisor"},
    {"id": "section-mev", "surface": "section", "legacy_path": "/api/mev/sandwich-report"},
    {"id": "section-legacy-alerts", "surface": "section", "legacy_path": "/api/alerts/telegram"},
    {"id": "lens-room", "surface": "lens", "legacy_path": "/data-room"},
    {"id": "entry-my-book", "surface": "entry-rail", "legacy_path": "#portfolio"},
    {"id": "entry-legacy-alerts", "surface": "entry-rail", "legacy_path": "#alerts"},
    {"id": "dashboard-stream", "surface": "stream", "legacy_path": "/api/dashboard/stream"},
)

BLOCKED_EXTERNAL_SURFACES: tuple[dict[str, str], ...] = (
    {
        "key": "smart_alerts",
        "label": "Smart Alerts — Telegram محجوب خارجيًا",
        "reason": BLOCKED_EXTERNAL_LAUNCH_IDS[33],
    },
    {
        "key": "mvrv_zscore",
        "label": "MVRV / Z-Score — مصدر مرخّص محجوب خارجيًا",
        "reason": BLOCKED_EXTERNAL_LAUNCH_IDS[38],
    },
)


def build_product_isolation_manifest() -> dict[str, Any]:
    return {
        "artifact": "LAUNCH57_PRODUCT_ISOLATION",
        "launch57_product_isolation": PRODUCT_ISOLATION_ENABLED,
        "ready_launch_count": READY_LAUNCH57_COUNT,
        "ready_launch_ids": sorted(READY_LAUNCH57_IDS),
        "blocked_external_launch_ids": sorted(BLOCKED_EXTERNAL_LAUNCH_IDS),
        "blocked_external_surfaces": [
            {
                "label": row["label"],
                "reason": row["reason"],
                "live_path_forbidden": True,
                "telegram_send_forbidden": row["key"] == "smart_alerts",
            }
            for row in BLOCKED_EXTERNAL_SURFACES
        ],
        "isolated_elements": list(ISOLATED_FIRST_SCREEN_ELEMENTS),
        "out_of_scope_label": OUT_OF_SCOPE_LABEL,
        "verification_status": "PENDING_VERIFICATION",
        "pass_live_claimed": False,
    }
