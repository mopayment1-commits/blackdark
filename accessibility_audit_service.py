"""
BLACKDARK — WCAG / accessibility audit capability (institutional testing surface).

Static HTML checks + optional axe-core when available.
"""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _has_lang_en(text: str) -> bool:
    return bool(
        re.search(r'lang\s*=\s*["\']en["\']', text)
        or 'lang|default("en")' in text
        or "lang|default('en')" in text
    )


def _scan_template(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if not _has_lang_en(text):
        issues.append("missing_html_lang_en")
    imgs = re.findall(r"<img[^>]*>", text, re.I)
    for tag in imgs:
        if 'alt=""' in tag or "alt=''" in tag:
            issues.append(f"empty_alt:{path.name}")
        elif "alt=" not in tag.lower():
            issues.append(f"missing_alt:{path.name}")
    if 'dir="rtl"' in text and 'lang|default("en")' not in text:
        issues.append("rtl_without_i18n_default")
    return {
        "file": str(path.relative_to(ROOT)),
        "issues": issues,
        "img_count": len(imgs),
        "ok": len(issues) == 0,
    }


def run_static_wcag_audit(*, template_glob: str = "*.html") -> dict[str, Any]:
    """Scan all templates for baseline WCAG signals."""
    scans = [_scan_template(p) for p in sorted(TEMPLATES.glob(template_glob))]
    failed = [s for s in scans if not s["ok"]]
    return {
        "feature_ref": "accessibility_audit#wcag",
        "generated_at": _utcnow(),
        "templates_scanned": len(scans),
        "templates_passing": len(scans) - len(failed),
        "templates_failing": len(failed),
        "scans": scans,
        "ok": len(failed) == 0,
        "standard": "WCAG 2.1 AA baseline (static HTML)",
    }


def run_axe_cli_audit(url: str | None = None) -> dict[str, Any]:
    """Optional axe-core CLI when @axe-core/cli is installed."""
    import os

    target = url or os.getenv("ACCESSIBILITY_AUDIT_URL", "")
    if not target:
        return {"ok": False, "error": "ACCESSIBILITY_AUDIT_URL not set"}
    try:
        proc = subprocess.run(
            ["npx", "--yes", "@axe-core/cli", target, "--exit"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        return {
            "url": target,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-2000:],
            "ok": proc.returncode == 0,
        }
    except FileNotFoundError:
        return {"url": url, "ok": False, "error": "npx_not_available"}
    except subprocess.TimeoutExpired:
        return {"url": url, "ok": False, "error": "axe_timeout"}


async def build_accessibility_audit_report(*, url: str | None = None) -> dict[str, Any]:
    static = run_static_wcag_audit()
    axe: dict[str, Any] | None = None
    if url:
        axe = run_axe_cli_audit(url)
    return {
        **static,
        "axe": axe,
        "disclaimer": "Automated scan supplements manual accessibility review.",
    }
