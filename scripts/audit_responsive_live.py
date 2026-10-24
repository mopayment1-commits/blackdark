#!/usr/bin/env python3
"""Audit live HTML for responsive viewport + overflow hints (desktop/Android/iOS baseline)."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from path_safety import assert_safe_http_url, safe_urlopen

PAGES = ("/", "/login", "/pricing", "/oracle-accuracy")
VIEWPORT_OK = re.compile(r"width=device-width", re.I)


def _fetch(base: str, path: str) -> tuple[int, str]:
    url = assert_safe_http_url(f"{base.rstrip('/')}{path}")
    with safe_urlopen(url, timeout=25) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def main() -> int:
    base = assert_safe_http_url(sys.argv[1] if len(sys.argv) > 1 else "https://blackdark.io")
    rows: list[dict] = []
    ok_all = True
    for path in PAGES:
        status, html = _fetch(base, path)
        has_vp = bool(VIEWPORT_OK.search(html))
        has_fit = "viewport-fit=cover" in html
        wide_fixed = bool(re.search(r"width:\s*1[0-9]{3,}px", html[:8000]))
        row = {
            "path": path,
            "status": status,
            "viewport_device_width": has_vp,
            "viewport_fit_cover": has_fit,
            "suspicious_fixed_width_inline": wide_fixed,
        }
        rows.append(row)
        if status != 200 or not has_vp:
            ok_all = False
    out = {"base": base, "ok": ok_all, "pages": rows}
    dest = ROOT / "artifacts" / "responsive_live_audit.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
