#!/usr/bin/env python3
"""Verify POST /api/auth/logout on the public domain returns HTTP < 8s (like Railway origin)."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def probe_post_logout(base: str, timeout: float) -> tuple[int, float, str]:
    base = base.rstrip("/")
    url = f"{base}/api/auth/logout"
    origin = base if base.startswith("http") else f"https://{base}"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Accept": "application/json",
            "Origin": origin,
            "Content-Type": "application/json",
        },
        data=b"{}",
    )
    import time

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - t0
            return int(resp.status), elapsed, body
    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - t0
        body = exc.read(4096).decode("utf-8", errors="replace") if exc.fp else ""
        return int(exc.code), elapsed, body
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        return 0, elapsed, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canonical",
        default="https://blackdark.io",
        help="User-facing domain (must answer POST logout)",
    )
    parser.add_argument(
        "--origin",
        default="https://blackdark-production.up.railway.app",
        help="Known-good Railway host for comparison",
    )
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    results = {}
    ok = True
    for label, base in (("canonical", args.canonical), ("origin", args.origin)):
        code, elapsed, body = probe_post_logout(base, args.timeout)
        results[label] = {
            "url": f"{base.rstrip('/')}/api/auth/logout",
            "http_status": code,
            "seconds": round(elapsed, 3),
            "body_excerpt": body[:200],
        }
        if label == "canonical" and (code != 200 or elapsed >= args.timeout):
            ok = False
        if label == "origin" and code != 200:
            print(f"warning: origin probe returned {code}", file=sys.stderr)

    print(json.dumps(results, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
