#!/usr/bin/env python3
"""Measure /login Google button presence and OAuth start redirect latency."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
    rows: list[str] = []

    t0 = time.perf_counter()
    login = httpx.get(f"{base}/login", timeout=30.0, follow_redirects=True)
    login_ms = (time.perf_counter() - t0) * 1000
    rows.append(f"GET /login: {login_ms:.0f}ms status={login.status_code}")
    has_btn = 'id="googleSignInBtn"' in login.text
    rows.append(f"googleSignInBtn in HTML: {has_btn}")
    if has_btn:
        idx = login.text.find('id="googleSignInBtn"')
        rows.append(f"googleSignInBtn offset in HTML: {idx} bytes")

    t0 = time.perf_counter()
    oauth = httpx.get(
        f"{base}/api/auth/oauth/google/start",
        timeout=30.0,
        follow_redirects=False,
    )
    oauth_ms = (time.perf_counter() - t0) * 1000
    loc = oauth.headers.get("location") or ""
    rows.append(f"GET /api/auth/oauth/google/start: {oauth_ms:.0f}ms status={oauth.status_code}")
    rows.append(f"redirect: {loc[:80]}...")

    out = "\n".join(rows)
    print(out)
    artifact = Path("/opt/cursor/artifacts/login-google-perf.txt")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(out + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
