"""Static WCAG accessibility audit for HTML templates (PDF checklist closure)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
_STANDARD = "WCAG 2.1 AA (static template scan)"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _scan_template(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    issues: list[str] = []
    if "<html" in lower and 'lang="' not in lower and "lang='" not in lower:
        issues.append("missing_html_lang")
    if "<img" in lower and 'alt="' not in lower and "alt='" not in lower:
        issues.append("img_missing_alt")
    if "<input" in lower and 'aria-label="' not in lower and "<label" not in lower:
        issues.append("input_missing_label")
    return {
        "path": str(path.relative_to(_TEMPLATE_ROOT.parent)),
        "issues": issues,
        "ok": not issues,
    }


def run_static_wcag_audit(*, template_root: Path | None = None) -> dict[str, Any]:
    root = template_root or _TEMPLATE_ROOT
    templates = sorted(root.rglob("*.html"))
    rows = [_scan_template(p) for p in templates]
    issue_count = sum(len(r["issues"]) for r in rows)
    return {
        "standard": _STANDARD,
        "templates_scanned": len(rows),
        "issue_count": issue_count,
        "templates": rows,
        "ok": len(templates) >= 10 and issue_count == 0,
        "generated_at": _utcnow(),
    }


async def build_accessibility_audit_report() -> dict[str, Any]:
    audit = run_static_wcag_audit()
    return {
        "feature_ref": "accessibility_audit#wcag",
        "capability_id": None,
        "generated_at": audit["generated_at"],
        "standard": audit["standard"],
        "templates_scanned": audit["templates_scanned"],
        "issue_count": audit["issue_count"],
        "ok": audit["ok"],
        "no_execution": True,
    }


def run_accessibility_audit() -> dict[str, Any]:
    return run_static_wcag_audit()
