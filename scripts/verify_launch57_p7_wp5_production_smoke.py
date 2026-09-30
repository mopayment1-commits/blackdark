#!/usr/bin/env python3
"""Program Phase 7 L57-P7-WP5 — production smoke: headers, security.txt, SSO bootstrap, optional log export."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

REQUIRED_HEADERS = (
    "X-Content-Type-Options",
    "X-Security-Hardening",
    "X-Blackdark-Auth-Boundary",
)


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def main() -> int:
    base = (os.getenv("LAUNCH57_PROD_URL") or "").strip().rstrip("/")
    if not base:
        print("SKIP: LAUNCH57_PROD_URL required for L57-P7-WP5 production smoke", file=sys.stderr)
        return 3
    checks: dict[str, Any] = {}

    code, hdrs, body = _get(f"{base}/api/user/profile")
    missing = [h for h in REQUIRED_HEADERS if not hdrs.get(h)]
    checks["anonymous_401_security_headers"] = {
        "ok": code == 401 and not missing,
        "status": code,
        "missing_headers": missing,
        "program_ref": "§6 FINDING-17; L57-P7-WP2",
    }

    code, hdrs, body = _get(f"{base}/.well-known/security.txt")
    text = body.decode("utf-8", errors="replace")
    checks["security_txt_rfc9116"] = {
        "ok": code == 200 and "Contact:" in text and "Policy:" in text,
        "status": code,
        "program_ref": "§6 FINDING-14; L57-P7-WP5",
    }

    code, hdrs, body = _get(f"{base}/api/institutional/sso/authorize")
    body_l = body.lower()
    sso_ok = code in {302, 307} or (
        code in {400, 422} and (b"authorize" in body_l or b"ready" in body_l or b"sso" in body_l)
    )
    checks["sso_authorize_bootstrap"] = {
        "ok": code not in {401, 403} and sso_ok,
        "status": code,
        "note": "302 when IdP configured; 400 acceptable when bootstrap reachable but not ready (program §6 FINDING-03)",
        "program_ref": "L57-P3-WP2; L57-P7-WP5",
    }

    token = (os.getenv("LAUNCH57_OPS_BEARER_TOKEN") or "").strip()
    if token:
        code, hdrs, raw = _get(
            f"{base}/api/security/customer-logs/export?format=json&limit=1",
            headers={"Authorization": f"Bearer {token}"},
        )
        checks["customer_log_export_sample"] = {
            "ok": code in {200, 403},
            "status": code,
            "note": "200 or 403 proves route exists; 403 if token lacks org admin (E-RUN only)",
            "program_ref": "§6 FINDING-09; L57-P7-WP5",
        }
    else:
        checks["customer_log_export_sample"] = {
            "ok": True,
            "skipped": True,
            "note": "Set LAUNCH57_OPS_BEARER_TOKEN for authenticated export probe",
        }

    report = {
        "authority": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        "work_package": "L57-P7-WP5",
        "base_url": base,
        "cisa_certification_claimed": False,
        "checks": checks,
    }
    print(json.dumps(report, indent=2))
    required = [k for k, v in checks.items() if not v.get("skipped")]
    if all(checks[k].get("ok") for k in required):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
