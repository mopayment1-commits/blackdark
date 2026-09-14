"""DTS cross-cutting delivery — timezone, i18n, accessibility (P6)."""

from __future__ import annotations

from typing import Any

from decision_truth.cross_cutting.accessibility import build_dts_accessibility_envelope
from decision_truth.cross_cutting.i18n import localize_dts_payload
from decision_truth.cross_cutting.timezone import project_dts_timestamps

DISCOVERED_DTS_SURFACES = (
    "decision_truth_api",
    "dashboard",
    "six_heroes",
    "command_view",
    "decision_surface",
    "opportunity_cards",
    "rejection_surfaces",
    "why_why_not",
    "daily_evidence",
    "full_evidence_trail",
    "simulation_surfaces",
    "portfolio_pre_impact",
    "calibration_evidence",
    "thirty_second_truth",
    "no_decision",
    "reject_proof",
)


def apply_cross_cutting_delivery(
    payload: dict[str, Any],
    *,
    lang: str | None = None,
    user_timezone: str | None = None,
) -> dict[str, Any]:
    """Apply timezone, i18n, and accessibility presentation layers."""
    out = dict(payload)
    lang = lang or out.get("lang") or "en"
    tz = user_timezone or out.get("user_timezone") or (out.get("delivery_preferences") or {}).get("timezone")
    out = project_dts_timestamps(out, user_timezone=tz, lang=lang)
    out = localize_dts_payload(out, lang)
    out["dts_accessibility"] = build_dts_accessibility_envelope(out, lang=lang)
    out["dts_cross_cutting"] = {
        "timezone_authority": "governance/timezone_governance.py",
        "i18n_authority": "i18n_service.py",
        "accessibility_authority": "accessibility_audit_service.py",
        "discovered_surfaces": list(DISCOVERED_DTS_SURFACES),
        "duplicate_timezone_authority": False,
        "parallel_translation_system": False,
        "methodology_version": "dts-p6-cross-cutting-1.0",
    }
    return out


__all__ = ["apply_cross_cutting_delivery", "DISCOVERED_DTS_SURFACES"]
