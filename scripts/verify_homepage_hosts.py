#!/usr/bin/env python3
"""Homepage must return HTML within timeout on user-facing hosts (web.dev LCP prep)."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def probe_get(base: str, timeout: float) -> tuple[int, float, int]:
    base = base.rstrip("/")
    url = f"{base}/"
    req = urllib.request.Request(url, method="GET", headers={"Accept": "text/html"})
    import time

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(65536)
            elapsed = time.perf_counter() - t0
            return int(resp.status), elapsed, len(body)
    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - t0
        return int(exc.code), elapsed, 0
    except Exception:
        elapsed = time.perf_counter() - t0
        return 0, elapsed, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--min-bytes", type=int, default=50_000)
    parser.add_argument(
        "urls",
        nargs="*",
        default=[
            "https://blackdark.io",
            "https://blackdark-production.up.railway.app",
        ],
    )
    args = parser.parse_args()
    out = {}
    ok = True
    for base in args.urls:
        code, elapsed, nbytes = probe_get(base, args.timeout)
        out[base] = {
            "http_status": code,
            "seconds": round(elapsed, 3),
            "bytes_read": nbytes,
        }
        if code != 200 or elapsed >= args.timeout or nbytes < args.min_bytes:
            ok = False
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
