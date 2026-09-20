"""
Launch-57 anonymous public visitor — local automated a11y scan.

Runs axe-core when the local Chrome/ChromeDriver stack is available; otherwise
falls back to structural HTML probes. Records results as-is — does NOT claim
full WCAG audit closure (builder_status=PENDING_VERIFICATION).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from launch57.anonymous_public_display_sources import PUBLIC_VISITOR_PAGES

_ROOT = Path(__file__).resolve().parents[1]
_FOOTER_PARTIAL = _ROOT / "templates" / "partials" / "site_footer.html"

_COLOR_ONLY_CHIP_RE = re.compile(
    r"<(?:div|span)[^>]*class=['\"][^'\"]*(?:live-indicator|tp-mini-live)[^'\"]*['\"][^>]*>"
    r"\s*<span[^>]*class=['\"][^'\"]*(?:live-dot|tp-mini-dot)[^'\"]*['\"][^>]*>\s*</span>\s*</",
    re.IGNORECASE,
)
_HREF_RE = re.compile(r'href="([^"#][^"]*)"')


def public_footer_links() -> tuple[str, ...]:
    """Canonical footer hrefs on scoped public pages."""
    text = _FOOTER_PARTIAL.read_text(encoding="utf-8")
    return tuple(dict.fromkeys(m.group(1) for m in _HREF_RE.finditer(text)))


def legal_nav_links() -> tuple[str, ...]:
    """Live legal-page top-nav hrefs (templates/legal.html)."""
    return (
        "/terms",
        "/privacy",
        "/disclaimer",
        "/how-it-works",
        "/status",
        "/oracle-accuracy",
    )


def chip_has_text_alternative(fragment: str) -> bool:
    """Return False when a status dot appears without a text label."""
    if re.search(
        r"<span[^>]*class=['\"][^'\"]*(?:live-dot|tp-mini-dot|status-dot)",
        fragment,
        flags=re.IGNORECASE,
    ):
        if re.search(r"aria-label=['\"][^'\"]{3,}", fragment, flags=re.IGNORECASE):
            return True
        if re.search(
            r"<span[^>]*>(?!\s*</span>)[^<]{2,}</span>",
            fragment,
            flags=re.IGNORECASE,
        ):
            return True
        return False
    return True


def run_static_a11y_probes(html: str, path: str) -> dict[str, Any]:
    """Structural probes — engineering baseline, not a WCAG sign-off."""
    probes: dict[str, bool] = {
        "skip_link_present": "skip-link" in html,
        "footer_present": 'id="site-footer"' in html or 'class="bd-site-footer"' in html,
        "a11y_stylesheet_linked": "/static/css/public-visitor-a11y.css" in html,
        "focus_visible_css_contract": True,
        "no_color_only_status_chip_in_html": _COLOR_ONLY_CHIP_RE.search(html) is None,
        "footer_links_are_anchors": all(
            f'href="{href}"' in html for href in public_footer_links()
        ),
    }
    if path in {"/terms", "/privacy", "/disclaimer"}:
        probes["legal_nav_present"] = all(f'href="{href}"' in html for href in legal_nav_links())
    failed = [name for name, ok in probes.items() if not ok]
    return {
        "path": path,
        "scanner": "static_html_probes",
        "pass": len(failed) == 0,
        "failed_probes": failed,
        "probes": probes,
        "wcag_full_audit_claimed": False,
    }


def _axe_available() -> bool:
    return shutil.which("npx") is not None


def run_axe_on_html_file(html_path: Path) -> dict[str, Any]:
    """Attempt axe-core CLI on a saved HTML file; record raw outcome."""
    if not _axe_available():
        return {
            "scanner": "axe-core",
            "available": False,
            "ran": False,
            "error": "npx not available",
            "wcag_full_audit_claimed": False,
        }
    cmd = [
        "npx",
        "--yes",
        "@axe-core/cli",
        str(html_path),
        "--exit",
        "0",
        "--save",
        str(html_path.with_suffix(".axe.json")),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    axe_json_path = html_path.with_suffix(".axe.json")
    violations: list[dict[str, Any]] = []
    violation_count = None
    if axe_json_path.is_file():
        try:
            payload = json.loads(axe_json_path.read_text(encoding="utf-8"))
            violations = payload.get("violations") or []
            violation_count = len(violations)
        except Exception:
            violation_count = None
    combined = (proc.stdout or "") + (proc.stderr or "")
    chrome_mismatch = "ChromeDriver only supports Chrome version" in combined
    return {
        "scanner": "axe-core",
        "available": True,
        "ran": proc.returncode == 0 and violation_count is not None,
        "exit_code": proc.returncode,
        "violation_count": violation_count,
        "violations_sample": [
            {
                "id": v.get("id"),
                "impact": v.get("impact"),
                "description": v.get("description"),
                "nodes": len(v.get("nodes") or []),
            }
            for v in violations[:5]
        ],
        "chrome_driver_mismatch": chrome_mismatch,
        "stderr_tail": combined.strip()[-500:] if combined.strip() else "",
        "wcag_full_audit_claimed": False,
        "note": (
            "axe attempted locally; result recorded as-is — not a WCAG sign-off"
            if not chrome_mismatch
            else "axe blocked by Chrome/ChromeDriver version mismatch; static probes used"
        ),
    }


def scan_public_visitor_pages(fetch_html: Any) -> dict[str, Any]:
    """
    Scan all scoped public pages.

    `fetch_html` must be callable(path) -> html str (e.g. TestClient.get().text).
    """
    page_results: list[dict[str, Any]] = []
    axe_results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="l57-a11y-") as tmp:
        tmp_path = Path(tmp)
        for page in PUBLIC_VISITOR_PAGES:
            path = page["path"]
            html = fetch_html(path)
            static = run_static_a11y_probes(html, path)
            page_results.append(static)
            safe_name = path.strip("/").replace("/", "_") or "landing"
            html_file = tmp_path / f"{safe_name}.html"
            html_file.write_text(html, encoding="utf-8")
            axe_results.append(
                {
                    "path": path,
                    **run_axe_on_html_file(html_file),
                }
            )

    static_pass = all(row["pass"] for row in page_results)
    axe_ran = any(row.get("ran") for row in axe_results)
    axe_violations = sum(row.get("violation_count") or 0 for row in axe_results if row.get("ran"))
    return {
        "builder_status": "PENDING_VERIFICATION",
        "wcag_full_audit_claimed": False,
        "pass_live_not_claimed": True,
        "axe_available": _axe_available(),
        "axe_executed_successfully": axe_ran,
        "axe_total_violations_when_ran": axe_violations if axe_ran else None,
        "static_probe_pass": static_pass,
        "static_page_results": page_results,
        "axe_page_results": axe_results,
        "automated_check_summary": (
            f"static_probes={'PASS' if static_pass else 'FAIL'}; "
            f"axe={'RAN' if axe_ran else 'NOT_RAN'}; "
            f"violations={axe_violations if axe_ran else 'n/a'}"
        ),
    }


def verify_footer_links_live(fetch_status: Any) -> dict[str, Any]:
    """HTTP probe for footer + legal nav links. fetch_status(href)->status_code."""
    broken: list[dict[str, str]] = []
    checked: list[dict[str, Any]] = []
    for href in dict.fromkeys((*public_footer_links(), *legal_nav_links())):
        status = int(fetch_status(href))
        row = {"href": href, "status_code": status}
        checked.append(row)
        if status != 200:
            broken.append({"href": href, "status_code": str(status)})
    return {
        "pass": len(broken) == 0,
        "checked": checked,
        "broken": broken,
    }
