#!/usr/bin/env python3
"""Set ADMIN_EMAILS + ADMIN_API_KEY in .env for production admin access."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _upsert(lines: list[str], key: str, value: str) -> list[str]:
    prefix = key + "="
    out = [ln for ln in lines if not ln.startswith(prefix)]
    out.append(f"{prefix}{value}")
    return out


def main() -> None:
    email = (sys.argv[1] if len(sys.argv) > 1 else input("Admin email: ")).strip().lower()
    if "@" not in email:
        print("Invalid email")
        raise SystemExit(1)

    api_key = secrets.token_hex(24)
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    lines = _upsert(lines, "ADMIN_EMAILS", email)
    lines = _upsert(lines, "ADMIN_API_KEY", api_key)
    ENV.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print("Admin configured in .env")
    print(f"  ADMIN_EMAILS={email}")
    print(f"  ADMIN_API_KEY={api_key}")
    print("\nRestart server: start_blackdark.bat")


if __name__ == "__main__":
    main()
