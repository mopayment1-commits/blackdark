#!/usr/bin/env python3
"""
Rotate SECRETS_MASTER_KEY and re-encrypt user_api_keys vault rows.

Usage:
  export OLD_SECRETS_MASTER_KEY=...   # current key (or SECRETS_MASTER_KEY)
  python scripts/rotate_vault_key.py --dry-run
  python scripts/rotate_vault_key.py --apply

Writes: data/vault_key_rotation_report.json
Prints new env lines to set in production after apply.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def rotate(*, apply: bool) -> dict:
    from database import (
        fetch_all_user_api_key_secrets,
        init_db,
        update_user_api_key_ciphertexts,
    )
    from secrets_vault import reencrypt_ciphertext

    old = (
        os.getenv("OLD_SECRETS_MASTER_KEY", "").strip()
        or os.getenv("SECRETS_MASTER_KEY", "").strip()
    )
    if not old:
        raise SystemExit("Set OLD_SECRETS_MASTER_KEY or SECRETS_MASTER_KEY")

    new_key = os.getenv("NEW_SECRETS_MASTER_KEY", "").strip() or secrets.token_hex(32)
    await init_db()
    rows = await fetch_all_user_api_key_secrets()

    updated = 0
    errors: list[dict] = []
    for row in rows:
        try:
            new_key_ct = reencrypt_ciphertext(
                str(row["api_key_encrypted"]),
                old_master=old,
                new_master=new_key,
            )
            new_secret_ct = reencrypt_ciphertext(
                str(row["api_secret_encrypted"]),
                old_master=old,
                new_master=new_key,
            )
            if apply:
                await update_user_api_key_ciphertexts(
                    int(row["id"]),
                    new_key_ct,
                    new_secret_ct,
                )
            updated += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": row.get("id"), "error": str(exc)})

    today = datetime.now(timezone.utc).date().isoformat()
    report = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "rows_seen": len(rows),
        "rows_ok": updated,
        "errors": errors,
        "new_env": {
            "SECRETS_MASTER_KEY": new_key if apply else "<hidden until --apply>",
            "VAULT_KEY_LAST_ROTATED_AT": today,
            "VAULT_KEY_ROTATION_DAYS": os.getenv("VAULT_KEY_ROTATION_DAYS", "90"),
        },
        "next_steps": [
            "Set SECRETS_MASTER_KEY to the new value in the secret store",
            "Set VAULT_KEY_LAST_ROTATED_AT to today (UTC)",
            "Restart web pods / compose services",
            "Destroy the old master key after validation",
        ],
    }
    if apply:
        report["new_env"]["SECRETS_MASTER_KEY"] = new_key

    out = ROOT / "data" / "vault_key_rotation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Never persist the raw new key in the report file for safety
    safe = dict(report)
    safe_env = dict(report["new_env"])
    if apply:
        safe_env["SECRETS_MASTER_KEY"] = "<written to stdout only>"
    safe["new_env"] = safe_env
    out.write_text(json.dumps(safe, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate BLACKDARK vault master key")
    parser.add_argument("--apply", action="store_true", help="Persist re-encrypted rows")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only (default)")
    args = parser.parse_args()
    apply = bool(args.apply)
    report = asyncio.run(rotate(apply=apply))
    print(json.dumps({k: v for k, v in report.items() if k != "new_env"}, indent=2))
    print("\n# Set these in production after a successful --apply:")
    for k, v in report["new_env"].items():
        print(f"export {k}={v}")
    print(f"\nReport: data/vault_key_rotation_report.json (key redacted on disk)")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
