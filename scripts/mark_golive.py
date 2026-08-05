#!/usr/bin/env python3
"""Mark GO LIVE announced after production deploy + share."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Production APP_BASE_URL")
    parser.add_argument("--note", default="announced")
    args = parser.parse_args()

    payload = {
        "announced_at": datetime.now(timezone.utc).isoformat(),
        "url": args.url.rstrip("/"),
        "note": args.note,
        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
        "checks": [
            "/health/live",
            "/api/production/guard",
            "/oracle/BTC?ux_mode=beginner&lang=ar",
            "/oracle-accuracy",
        ],
    }
    path = ROOT / "data" / "golive_announced.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GO LIVE marked → {path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
