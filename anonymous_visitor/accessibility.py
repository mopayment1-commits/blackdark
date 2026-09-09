"""Accessibility baseline checks — AV §24 WCAG 2.2 AA target."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _landing_checks() -> list[dict[str, Any]]:
    path = Path("templates/landing.html")
    if not path.is_file():
        return [{"check": "landing_exists", "pass": False}]
    html = path.read_text(encoding="utf-8")
    checks = [
        ("lang_attribute", 'lang="' in html or "lang={{" in html),
        ("main_landmark", "<main" in html or 'role="main"' in html),
        ("skip_link_or_semantic_nav", "<nav" in html or "skip" in html.lower()),
        ("button_or_link_cta", "Start Free" in html or "start_free" in html or "cta" in html.lower()),
        ("trust_pulse_section", "trust-pulse" in html or "trust_pulse" in html),
        ("footer_legal_links", "privacy" in html.lower() and ("terms" in html.lower() or "risk" in html.lower())),
        ("aria_live_or_status", "aria-live" in html or "role=\"status\"" in html),
        ("focus_visible_css", ":focus" in html or "focus-visible" in html),
    ]
    return [{"check": name, "pass": bool(ok)} for name, ok in checks]


def accessibility_report() -> dict[str, Any]:
    checks = _landing_checks()
    passed = sum(1 for c in checks if c["pass"])
    return {
        "target": "WCAG_2.2_AA",
        "assessment": "local_automated_baseline",
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "external_audit_required": True,
        "status": "PARTIAL" if passed >= len(checks) - 1 else "OPEN",
    }
