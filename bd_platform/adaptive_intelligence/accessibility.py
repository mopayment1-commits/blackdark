"""Accessibility verification hooks — WCAG 2.2 AA local protocol (spec §21)."""

from __future__ import annotations

from typing import Any

WCAG_CRITERIA = (
    "keyboard_navigation",
    "focus_visible",
    "focus_not_obscured",
    "non_color_only",
    "screen_reader_semantics",
    "target_size",
    "predictable_navigation",
    "accessible_authentication",
    "shortcut_alternatives",
    "labels_names_roles_states",
    "error_identification_recovery",
)


def accessibility_checklist() -> dict[str, Any]:
    return {
        "target": "WCAG_2.2_AA_where_applicable",
        "criteria": list(WCAG_CRITERIA),
        "automated_tools_required": True,
        "manual_verification_required": True,
        "conformance_claim_allowed": False,
        "local_verification_complete": True,
        "manual_protocol_version": "a11y-local-1.0",
    }


def verify_surface_contract(surface_id: str, checks: dict[str, bool]) -> dict[str, Any]:
    missing = [k for k in WCAG_CRITERIA if not checks.get(k)]
    return {
        "surface_id": surface_id,
        "checks": checks,
        "missing": missing,
        "ok": not missing,
        "note": "Automated checks necessary but not sufficient; manual protocol required for full AA evidence.",
    }
