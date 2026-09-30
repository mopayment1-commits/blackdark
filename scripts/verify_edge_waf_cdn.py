#!/usr/bin/env python3
"""Verify WAF/CDN readiness for Launch-57 (env + templates)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rules = ROOT / "deploy" / "cloudflare" / "waf-rules.json"
    checklist = ROOT / "docs" / "CDN_WAF_CHECKLIST.md"
    active = bool(os.getenv("CDN_WAF_ACTIVE", "").strip() or os.getenv("CLOUDFLARE_ZONE_ID", "").strip())
    report = {
        "edge_active": active,
        "waf_rules_template": rules.is_file(),
        "checklist": checklist.is_file(),
        "status": "ACTIVE" if active else "TEMPLATE_ONLY",
    }
    print(json.dumps(report, indent=2))
    if not rules.is_file() or not checklist.is_file():
        return 1
    if not active:
        print("NOTE: set CDN_WAF_ACTIVE=1 or CLOUDFLARE_ZONE_ID after operator activation", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
