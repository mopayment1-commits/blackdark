#!/usr/bin/env python3
"""HTTP smoke checks for Launch-57 public security surface (FINDING-13/14/16)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def _get_json(url: str) -> tuple[int, dict[str, Any] | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw), raw
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, None, body
    except Exception as exc:
        return -1, None, str(exc)


def _get_text(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return -1, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="", help="Production base URL (or LAUNCH57_PROD_URL)")
    args = parser.parse_args()
    import os

    base = (args.url or os.getenv("LAUNCH57_PROD_URL") or "").strip().rstrip("/")
    if not base:
        print("SKIP: set --url or LAUNCH57_PROD_URL", file=sys.stderr)
        return 3
    checks: dict[str, dict] = {}
    code, text = _get_text(f"{base}/.well-known/security.txt")
    checks["security_txt"] = {
        "ok": code == 200 and "Contact:" in text and "Policy:" in text,
        "status": code,
    }
    code, body, _ = _get_json(f"{base}/api/security/vdp")
    checks["vdp_api"] = {
        "ok": code == 200 and isinstance(body, dict) and body.get("surface") == "vulnerability_disclosure_policy",
        "status": code,
    }
    code, body, _ = _get_json(f"{base}/api/security/status")
    honest = isinstance(body, dict) and body.get("honesty", {}).get("cisa_certification_claimed") is False
    checks["security_status_public"] = {
        "ok": code == 200
        and isinstance(body, dict)
        and body.get("surface") == "security_posture_public"
        and "pentest_attestation" not in (body or {})
        and honest,
        "status": code,
    }
    report = {"base_url": base, "checks": checks}
    print(json.dumps(report, indent=2))
    if all(c.get("ok") for c in checks.values()):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
