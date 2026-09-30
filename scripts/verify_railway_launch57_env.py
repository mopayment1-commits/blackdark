#!/usr/bin/env python3
"""Validate Railway Launch-57 CISA env vars (process environment, read-only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "governance" / "launch57" / "RAILWAY_CISA_ENV_EXPECTATIONS.json"


def _is_production(env: dict[str, str]) -> bool:
    return env.get("ENV", "").strip().lower() == "production"


def _check_var(rule: dict, env: dict[str, str]) -> list[str]:
    name = rule["name"]
    val = env.get(name, "").strip()
    errors: list[str] = []
    required = rule.get("required_in_production", False)
    if not val:
        if required:
            errors.append(f"{name}: missing")
        return errors
    if "equals" in rule and val.lower() != str(rule["equals"]).lower():
        errors.append(f"{name}: expected {rule['equals']}, got {val!r}")
    if rule.get("https_url") and not val.startswith("https://"):
        errors.append(f"{name}: must be https URL")
    if rule.get("min_int") is not None:
        try:
            if int(val) < int(rule["min_int"]):
                errors.append(f"{name}: must be >= {rule['min_int']}")
        except ValueError:
            errors.append(f"{name}: must be integer >= {rule['min_int']}")
    if rule.get("min_length") is not None and len(val) < int(rule["min_length"]):
        errors.append(f"{name}: length must be >= {rule['min_length']}")
    host_ref = rule.get("matches_hostname_of")
    if host_ref:
        base = env.get(host_ref, "").strip()
        if base:
            expected = urlparse(base).hostname or ""
            if val != expected:
                errors.append(f"{name}: must match hostname of {host_ref} ({expected!r})")
    return errors


def evaluate(env: dict[str, str], *, include_waf: bool) -> dict:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if not _is_production(env):
        return {
            "mode": "skipped",
            "reason": "ENV is not production",
            "ok": True,
            "errors": [],
        }
    errors: list[str] = []
    for rule in spec.get("variables", []):
        if not include_waf and rule.get("name") in {"CDN_WAF_ACTIVE", "CLOUDFLARE_ZONE_ID"}:
            continue
        errors.extend(_check_var(rule, env))
    return {"mode": "production", "ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-waf",
        action="store_true",
        help="Also require CDN_WAF_ACTIVE=1 (FINDING-19 strict)",
    )
    parser.add_argument("--json", action="store_true", help="Print report JSON only")
    args = parser.parse_args()
    if not SPEC.is_file():
        print(f"MISSING spec: {SPEC}", file=sys.stderr)
        return 1
    env = {k: v for k, v in os.environ.items()}
    report = evaluate(env, include_waf=args.include_waf)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    if report.get("mode") == "skipped":
        return 3
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
