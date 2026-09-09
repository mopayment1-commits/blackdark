"""Daily Evidence Autopsy — WHAT CHANGED / WHY / RISKS (DTS-034–036)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_daily_autopsy(report: dict[str, Any], *, lang: str = "en") -> dict[str, Any]:
    from i18n_service import t

    bullets = []
    for key in ("what_changed", "why_it_matters", "risks_invalidation"):
        val = report.get(key)
        if val:
            bullets.append(
                {
                    "section": key,
                    "text": val if isinstance(val, str) else str(val),
                    "source": report.get(f"{key}_source") or report.get("source") or "daily_brief",
                    "timestamp": report.get(f"{key}_at") or report.get("generated_at") or datetime.now(UTC).isoformat(),
                    "freshness": report.get("freshness") or "NEAR_LIVE",
                    "evidence_class": report.get("evidence_class") or "SHADOW_LIVE_FORWARD",
                }
            )
    return {
        "title": t("dts.daily_autopsy.title", lang),
        "bullets": bullets,
        "delivery": {
            "timezone_aware": True,
            "fixed_0800_global": False,
            "user_preference_supported": True,
        },
    }
