#!/usr/bin/env python3
"""Verify RFC 9116 security.txt (repo file + optional live URL)."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_FILE = ROOT / "static" / ".well-known" / "security.txt"


def _validate_content(text: str) -> list[str]:
    errors: list[str] = []
    if "Contact:" not in text:
        errors.append("missing Contact")
    if "Expires:" not in text:
        errors.append("missing Expires")
    if "Policy:" not in text:
        errors.append("missing Policy")
    if not re.search(r"^Expires:\s*\d{4}-\d{2}-\d{2}T", text, re.M):
        errors.append("invalid Expires format")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="", help="Production base URL to fetch /.well-known/security.txt")
    args = parser.parse_args()
    if not REPO_FILE.is_file():
        print("FAIL: repo security.txt missing", file=sys.stderr)
        return 1
    repo_text = REPO_FILE.read_text(encoding="utf-8")
    repo_err = _validate_content(repo_text)
    if repo_err:
        print("FAIL repo:", repo_err, file=sys.stderr)
        return 1
    print("PASS repo security.txt")
    if args.url:
        url = args.url.rstrip("/") + "/.well-known/security.txt"
        with urllib.request.urlopen(url, timeout=15) as resp:
            live = resp.read().decode("utf-8", errors="replace")
        live_err = _validate_content(live)
        if live_err:
            print("FAIL live:", live_err, file=sys.stderr)
            return 1
        print(f"PASS live {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
