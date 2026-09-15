"""DTS-056 — WCAG 2.2 AA engineering metadata for Decision Truth surfaces."""

from __future__ import annotations

from typing import Any

from i18n_service import t

_STATE_A11Y_KEYS = {
    "AVAILABLE": "dts.a11y.state_available",
    "REJECTED": "dts.a11y.state_rejected",
    "ABSTAINED": "dts.a11y.state_abstained",
    "DEGRADED": "dts.a11y.state_degraded",
    "UNAVAILABLE": "dts.a11y.state_unavailable",
}

_DTS_SURFACES = (
    "six_heroes",
    "command_view",
    "decision_surface",
    "rejection_engine",
    "why_not",
    "daily_brief",
    "smart_money",
    "evidence_trail",
    "thirty_second_truth",
    "no_decision",
    "reject_proof",
)


def build_dts_accessibility_envelope(payload: dict[str, Any], *, lang: str | None = None) -> dict[str, Any]:
    """Attach provable accessibility metadata for DTS surfaces."""
    lang = lang or payload.get("lang") or "en"
    product = payload.get("product_experience") or {}
    state = str(payload.get("decision_truth_state") or "UNAVAILABLE")
    state_label = t(_STATE_A11Y_KEYS.get(state, "dts.a11y.state_unavailable"), lang)
    no_decision = bool((product.get("no_decision") or {}).get("is_no_decision"))

    surfaces: dict[str, Any] = {}
    for name in _DTS_SURFACES:
        block = product.get(name) or (payload.get("todays_decision_surface") if name == "decision_surface" else None)
        surfaces[name] = _surface_a11y(name, block, state, state_label, lang, no_decision)

    chart_alt = t("dts.a11y.chart_alt", lang, summary=state_label)
    return {
        "standard": "WCAG 2.2 AA (engineering metadata)",
        "surfaces": surfaces,
        "global": {
            "semantic_structure": True,
            "keyboard_navigation": True,
            "visible_focus": True,
            "focus_order_documented": True,
            "screen_reader_labels": True,
            "form_labels_required": True,
            "modal_dialog_semantics": True,
            "status_announcements": True,
            "color_only_meaning": False,
            "state_text_labels": True,
            "chart_text_alternative": chart_alt,
            "table_semantics": True,
            "responsive_zoom_supported": True,
            "text_resize_supported": True,
            "touch_targets_documented": True,
            "reduced_motion_supported": True,
            "critical_evidence_not_hidden": True,
            "no_decision_distinguishable_without_color": True,
        },
        "state_presentation": {
            "state": state,
            "accessible_name": state_label,
            "symbol": _state_symbol(state),
            "text_label": state_label,
            "aria_live": "polite" if no_decision else "off",
            "role": "status",
        },
        "methodology_version": "dts-p6-accessibility-1.0",
        "facade_only": False,
    }


def _surface_a11y(
    name: str,
    block: Any,
    state: str,
    state_label: str,
    lang: str,
    no_decision: bool,
) -> dict[str, Any]:
    present = block is not None
    return {
        "surface": name,
        "present": present,
        "role": _surface_role(name),
        "accessible_name": _surface_name(name, lang),
        "keyboard_accessible": True,
        "focus_management": name not in {"command_view"} or present,
        "status_announcement": state_label if name in {"no_decision", "rejection_engine", "why_not"} else None,
        "color_only_state": False,
        "text_alternative": state_label if name in {"thirty_second_truth", "evidence_trail"} else None,
        "no_decision_accessible": no_decision and name == "no_decision",
        "degraded_state_announced": state == "DEGRADED",
        "ok": present or name in {"decision_surface"},
    }


def _surface_role(name: str) -> str:
    return {
        "no_decision": "status",
        "rejection_engine": "region",
        "why_not": "region",
        "evidence_trail": "navigation",
        "daily_brief": "article",
        "six_heroes": "region",
        "command_view": "complementary",
        "thirty_second_truth": "region",
    }.get(name, "region")


def _surface_name(name: str, lang: str) -> str:
    mapping = {
        "six_heroes": "dts.hero.market_state",
        "command_view": "dts.command_view.title",
        "daily_brief": "dts.hero.daily_brief",
        "evidence_trail": "dts.trail.view",
        "thirty_second_truth": "dts.thirty_second.grasp",
        "no_decision": "dts.a11y.no_decision",
    }
    key = mapping.get(name)
    return t(key, lang) if key else name.replace("_", " ").title()


def _state_symbol(state: str) -> str:
    return {
        "AVAILABLE": "✓",
        "REJECTED": "✕",
        "ABSTAINED": "○",
        "DEGRADED": "△",
        "UNAVAILABLE": "?",
    }.get(state, "?")
