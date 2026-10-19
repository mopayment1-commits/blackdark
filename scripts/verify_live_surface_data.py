#!/usr/bin/env python3
"""Verify user-visible counters/prices on key pages use live API endpoints (not static HTML)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from starlette.testclient import TestClient  # noqa: E402

from dashboard import app  # noqa: E402

# HTML must reference these fetch targets for dynamic user data.
REQUIRED_FETCH = {
    "/": [
        "/api/trust-pulse",
        "/api/analytics/stats",
        "/api/platform/stats",
    ],
    "/oracle-accuracy": [
        "/api/oracle/accuracy/public",
        "/api/oracle/audit-chain",
    ],
    "/login": [],  # static form only
    "/join-waitlist": ["/join-waitlist"],  # POST JSON API
}

# Placeholder-only stats are OK if paired with fetch in same file.
FORBIDDEN_STATIC_COUNTERS = re.compile(
    r"(?i)(fake|dummy)\s+(users|subscribers|price)|\b1,234,567\b"
)


def main() -> int:
    client = TestClient(app, raise_server_exceptions=False)
    failures: list[str] = []

    api_checks = [
        ("GET", "/api/analytics/stats", {200}),
        ("GET", "/api/platform/stats", {200}),
        ("GET", "/api/oracle/accuracy/public", {200}),
        ("GET", "/api/trust-pulse?symbol=BTC", {200}),
    ]
    for method, path, ok in api_checks:
        res = client.request(method, path)
        if res.status_code not in ok:
            failures.append(f"API {method} {path} -> {res.status_code}")

    for page, needles in REQUIRED_FETCH.items():
        res = client.get(page, headers={"Accept": "text/html"})
        if res.status_code not in {200, 302}:
            failures.append(f"HTML {page} -> {res.status_code}")
            continue
        html = res.text
        if FORBIDDEN_STATIC_COUNTERS.search(html):
            failures.append(f"HTML {page} contains forbidden static counter pattern")
        for needle in needles:
            if needle not in html:
                failures.append(f"HTML {page} missing live hook {needle}")

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("OK — live API hooks present and core endpoints respond")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
