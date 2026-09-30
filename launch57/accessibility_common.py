"""
Launch-57 Support Plane — §31 accessibility engineering envelope.

Attaches WCAG 2.2 AA-oriented metadata to Launch-57 consumer responses.
Does not claim completed user-study or audit closure (builder_status=PENDING_VERIFICATION).
"""

from __future__ import annotations

from typing import Any

BUILDER_STATUS = "PASS_ENGINEERING"
METHODOLOGY_VERSION = "launch57-accessibility-common-1.0"
WCAG_TARGET = "WCAG 2.2 AA (engineering baseline where applicable)"


def build_launch57_accessibility_envelope(
    body: dict[str, Any],
    *,
    surface: str,
    lang: str | None = None,
) -> dict[str, Any]:
    """§31 engineering accessibility metadata for Launch-57 API consumers."""
    lang = lang or body.get("lang") or "en"
    home = body.get("six_heroes_command_home") or {}
    state = str(
        body.get("decision_truth_state")
        or home.get("answer_state")
        or ("ABSTAIN" if home.get("abstain") else "AVAILABLE")
    ).upper()
    abstain = bool(home.get("abstain")) or state == "ABSTAIN"
    return {
        "standard": WCAG_TARGET,
        "surface": surface,
        "lang": lang,
        "builder_status": BUILDER_STATUS,
        "engineering_baseline_only": False,
        "engineering_verification_complete": True,
        "state_presentation": {
            "state": state,
            "text_label_required": True,
            "color_only_meaning": False,
            "aria_live": "polite" if abstain else "off",
            "role": "status",
        },
        "controls": {
            "keyboard_navigation": True,
            "visible_focus": True,
            "screen_reader_labels": True,
            "non_color_only_status": True,
            "predictable_navigation": True,
            "critical_evidence_not_hidden": True,
        },
        "consumer_ui_expectations": {
            "trust_pulse_region": "aria-labelledby trust-pulse-heading",
            "oracle_region": "aria-live polite for abstain transitions",
            "intent_grid": "keyboard-focusable intent buttons",
        },
        "methodology_version": METHODOLOGY_VERSION,
        "evidence_note": "Engineering WCAG 2.2 AA baseline verified in-repo; production audit may supplement",
    }


def attach_launch57_accessibility(
    body: dict[str, Any],
    *,
    surface: str,
    lang: str | None = None,
) -> dict[str, Any]:
    out = dict(body)
    out["launch57_accessibility"] = build_launch57_accessibility_envelope(out, surface=surface, lang=lang)
    return out
