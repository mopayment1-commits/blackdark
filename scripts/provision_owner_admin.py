#!/usr/bin/env python3
"""Provision owner admin: DB user password + print Railway env block (run on Railway: railway run …)."""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def _provision(email: str, password: str, *, create_if_missing: bool) -> dict:
    from auth_service import hash_password
    from database import create_user, fetch_user_by_email, get_connection, init_db

    email = email.strip().lower()
    await init_db()
    user = await fetch_user_by_email(email)
    pwd_hash = hash_password(password)
    if user:
        uid = int(user["id"])
        async with get_connection() as db:
            await db.execute(
                "UPDATE users SET password_hash = ?, password_is_set = 1 WHERE id = ?",
                (pwd_hash, uid),
            )
            await db.commit()
        action = "password_updated"
    elif create_if_missing:
        uid = await create_user(email, pwd_hash, "Owner Admin")
        action = "user_created"
    else:
        raise SystemExit(f"No user for {email}; pass --create")

    api_key = secrets.token_hex(24)
    return {"email": email, "user_id": uid, "action": action, "admin_api_key": api_key}


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision owner admin user + admin API key material")
    parser.add_argument("--email", required=True, help="Admin email (must match ADMIN_EMAILS on Railway)")
    parser.add_argument(
        "--password",
        help="Login password (min 12 chars). Generated if omitted.",
    )
    parser.add_argument("--create", action="store_true", help="Create user if email not in DB")
    parser.add_argument(
        "--artifact",
        default="",
        help="Write credentials to this path (default: /opt/cursor/artifacts/owner-admin-credentials.md)",
    )
    args = parser.parse_args()
    password = args.password or f"Blackdark-Owner-{secrets.token_urlsafe(12)}"
    if len(password) < 12:
        print("Password must be at least 12 characters", file=sys.stderr)
        return 1

    result = asyncio.run(_provision(args.email, password, create_if_missing=args.create))
    artifact = Path(args.artifact or "/opt/cursor/artifacts/owner-admin-credentials.md")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# Owner admin credentials (DO NOT COMMIT)

**Email:** `{result['email']}`
**Password:** `{password}`
**X-Admin-Key:** `{result['admin_api_key']}`

**Railway → Variables (web service):**
```
ADMIN_EMAILS={result['email']}
ADMIN_API_KEY={result['admin_api_key']}
ADMIN_MFA_REQUIRED=false
```

Redeploy after saving variables. Then log in at https://blackdark.io/login and open https://blackdark.io/admin .

DB action: {result['action']} (user_id={result['user_id']})
"""
    artifact.write_text(body, encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
