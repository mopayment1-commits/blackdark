#!/usr/bin/env python3
"""Set ADMIN_EMAILS in .env; emit ADMIN_API_KEY once for secret-manager storage."""

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
    # Never persist ADMIN_API_KEY in clear text on disk (CodeQL / Sonar).
    lines = [ln for ln in lines if not ln.startswith("ADMIN_API_KEY=")]
    ENV.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print("Admin email saved to .env")
    print(f"  ADMIN_EMAILS={email}")
    print()
    print("Store this secret in your host secret manager / Railway Variables (not in git):")
    print(f"  ADMIN_API_KEY={api_key}")
    print("\nRestart server after setting ADMIN_API_KEY in the secret store.")


if __name__ == "__main__":
    main()
