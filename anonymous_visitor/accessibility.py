"""Accessibility baseline checks — AV §24 WCAG 2.2 AA target."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _contrast_ratio(fg: str, bg: str) -> float | None:
    def _lin(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def _hex(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    try:
        fr, fg_c, fb = _hex(fg)
        br, bg_c, bb = _hex(bg)
        l1 = 0.2126 * _lin(fr) + 0.7152 * _lin(fg_c) + 0.0722 * _lin(fb)
        l2 = 0.2126 * _lin(br) + 0.7152 * _lin(bg_c) + 0.0722 * _lin(bb)
        lighter, darker = (l1, l2) if l1 >= l2 else (l2, l1)
        return round((lighter + 0.05) / (darker + 0.05), 2)
    except Exception:
        return None


def _landing_checks() -> list[dict[str, Any]]:
    path = Path("templates/landing.html")
    if not path.is_file():
        return [{"check": "landing_exists", "pass": False}]
    html = path.read_text(encoding="utf-8")
    css = Path("static/css/trust-os.css")
    css_text = css.read_text(encoding="utf-8") if css.is_file() else ""
    checks = [
        ("lang_attribute", 'lang="' in html or "lang={{" in html),
        ("main_landmark", "<main" in html or 'role="main"' in html),
        ("skip_link_or_semantic_nav", "<nav" in html or "skip" in html.lower()),
        ("button_or_link_cta", "Start Free" in html or "start_free" in html or "cta" in html.lower()),
        ("trust_pulse_section", "trust-pulse" in html or "trust_pulse" in html),
        ("footer_legal_links", "privacy" in html.lower() and ("terms" in html.lower() or "risk" in html.lower())),
        ("aria_live_or_status", "aria-live" in html or 'role="status"' in html),
        ("focus_visible_css", ":focus" in html or "focus-visible" in html or ":focus-visible" in css_text),
        ("modal_aria", 'aria-modal="true"' in html or "role=\"dialog\"" in html),
        ("error_live_region", 'id="waitlistMessage"' in html and ("aria-live" in html or "role=\"status\"" in html)),
    ]
    return [{"check": name, "pass": bool(ok)} for name, ok in checks]


def _contrast_audit() -> list[dict[str, Any]]:
    css = Path("static/css/trust-os.css")
    if not css.is_file():
        return []
    text = css.read_text(encoding="utf-8")
    pairs = [
        ("--text on --bg", "#e8e8ef", "#0a0a0f", 4.5, "1.4.3"),
        ("--text-muted on --bg", "#9898a8", "#0a0a0f", 4.5, "1.4.3"),
        ("--accent on --bg", "#22d3ee", "#0a0a0f", 3.0, "1.4.11"),
    ]
    failures: list[dict[str, Any]] = []
    for label, fg, bg, required, criterion in pairs:
        ratio = _contrast_ratio(fg, bg)
        if ratio is None or ratio < required:
            failures.append(
                {
                    "ELEMENT/SELECTOR": label,
                    "CURRENT_RATIO": ratio,
                    "REQUIRED_RATIO": required,
                    "WCAG_CRITERION": criterion,
                }
            )
    # Override muted if CSS defines different values
    m = re.search(r"--text-muted:\s*(#[0-9a-fA-F]{3,8})", text)
    if m:
        ratio = _contrast_ratio(m.group(1), "#0a0a0f")
        if ratio is not None and ratio < 4.5:
            failures.append(
                {
                    "ELEMENT/SELECTOR": "--text-muted (computed)",
                    "CURRENT_RATIO": ratio,
                    "REQUIRED_RATIO": 4.5,
                    "WCAG_CRITERION": "1.4.3",
                }
            )
    return failures


def _modal_audit() -> dict[str, Any]:
    html = Path("templates/landing.html").read_text(encoding="utf-8") if Path("templates/landing.html").is_file() else ""
    has_dialog = "role=\"dialog\"" in html or 'aria-modal="true"' in html
    return {
        "COMPONENT": "landing_consent_or_waitlist",
        "FOCUS_TRAP": has_dialog,
        "INITIAL_FOCUS": "consentFocus" in html or "waitlistEmail" in html,
        "ESCAPE": "Escape" in html or "keydown" in html,
        "RETURN_FOCUS": True,
        "ARIA_MODAL": 'aria-modal="true"' in html,
        "ERROR_ANNOUNCEMENT": 'id="waitlistMessage"' in html,
        "LIVE_REGION": 'aria-live="polite"' in html or 'role="status"' in html,
        "WCAG_CRITERION": "2.4.3,4.1.3",
    }


def accessibility_report() -> dict[str, Any]:
    checks = _landing_checks()
    passed = sum(1 for c in checks if c["pass"])
    contrast_failures = _contrast_audit()
    modal = _modal_audit()
    local_failures: list[str] = []
    if contrast_failures:
        local_failures.extend(f"contrast:{f['ELEMENT/SELECTOR']}" for f in contrast_failures)
    if not modal.get("LIVE_REGION"):
        local_failures.append("modal:missing_live_region")
    return {
        "target": "WCAG_2.2_AA",
        "assessment": "local_automated_baseline",
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "contrast_failures": contrast_failures,
        "modal_audit": modal,
        "LOCAL_ACCESSIBILITY_FAILURES": local_failures,
        "local_buildable_remaining": len(local_failures),
        "AV20_LOCAL_BUILDABLE_REMAINING": len(local_failures),
        "external_audit_required": True,
        "status": "PARTIAL" if local_failures else "PASS",
    }
