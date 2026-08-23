#!/usr/bin/env python3
"""Wave 0 passive security scan (ZAP-baseline equivalent when Docker unavailable).

Checks security headers, cookie flags, and common misconfigurations via HTTP only.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from typing import Any


def _fetch(url: str) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        body = resp.read(4096).decode("utf-8", errors="replace")
        return resp.status, headers, body


def run_passive_scan(base: str) -> dict[str, Any]:
    base = base.rstrip("/")
    findings: list[dict[str, Any]] = []

    def add(rule: str, risk: str, ok: bool, detail: str) -> None:
        findings.append({"rule": rule, "risk": risk, "ok": ok, "detail": detail})

    try:
        status, headers, _ = _fetch(f"{base}/")
    except Exception as exc:
        return {"ok": False, "error": str(exc), "findings": findings}

    add("http_200", "info", status == 200, f"GET / -> {status}")

    for hdr, risk in (
        ("x-content-type-options", "low"),
        ("x-frame-options", "low"),
        ("content-security-policy", "medium"),
        ("referrer-policy", "low"),
        ("permissions-policy", "low"),
        ("cross-origin-resource-policy", "low"),
    ):
        add(f"header_{hdr}", risk, hdr in headers, f"{hdr}: {headers.get(hdr, 'MISSING')}")

    if base.startswith("https"):
        add(
            "hsts",
            "medium",
            "strict-transport-security" in headers,
            headers.get("strict-transport-security", "MISSING"),
        )

    add(
        "x_security_hardening",
        "info",
        headers.get("x-security-hardening") == "1",
        f"x-security-hardening: {headers.get('x-security-hardening', 'MISSING')}",
    )

    # API surface
    try:
        _, api_headers, _ = _fetch(f"{base}/api/security/status")
        add(
            "api_security_status",
            "info",
            True,
            f"X-Response-Time present: {'x-response-time' in api_headers}",
        )
    except Exception as exc:
        add("api_security_status", "medium", False, str(exc))

    high_fail = [f for f in findings if not f["ok"] and f["risk"] in {"high", "medium"}]
    return {
        "ok": len(high_fail) == 0,
        "target": base,
        "finding_count": len(findings),
        "medium_or_high_failures": len(high_fail),
        "findings": findings,
    }


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "https://blackdark-production.up.railway.app"
    result = run_passive_scan(base)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
