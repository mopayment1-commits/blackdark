#!/usr/bin/env python3
"""Set ADMIN_EMAILS + private admin key file for production admin access.

The raw ADMIN_API_KEY is written only to keys/admin_api_key.secret (mode 0600),
never printed, and never stored clear-text in .env.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
SECRET_FILE = ROOT / "keys" / "admin_api_key.secret"
sys.path.insert(0, str(ROOT / "scripts"))
from _secret_io import mask_secret, write_private_text

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
    write_private_text(SECRET_FILE, api_key + "\n")

    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    lines = _upsert(lines, "ADMIN_EMAILS", email)
    # Path reference only — secret bytes live in the 0600 file
    lines = _upsert(lines, "ADMIN_API_KEY_FILE", str(SECRET_FILE.relative_to(ROOT)).replace("\\", "/"))
    # Remove any prior clear-text key from .env
    lines = [ln for ln in lines if not ln.startswith("ADMIN_API_KEY=")]
    write_private_text(ENV, "\n".join(lines).rstrip() + "\n")

    print("Admin configured")
    print(f"  ADMIN_EMAILS={email}")
    print(f"  ADMIN_API_KEY_FILE={SECRET_FILE.relative_to(ROOT)} (mode 0600)")
    print(f"  key fingerprint={mask_secret(api_key)}")
    print("  Raw key is not printed and not stored in .env")
    print("\nRestart server: start_blackdark.bat")


if __name__ == "__main__":
    main()
