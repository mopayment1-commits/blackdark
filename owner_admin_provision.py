"""Provision or reset owner admin user in the live database."""

from __future__ import annotations

import secrets
from typing import Any


async def provision_owner_admin(
    email: str,
    password: str,
    *,
    create_if_missing: bool,
) -> dict[str, Any]:
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
        raise ValueError("user_not_found")

    api_key = secrets.token_hex(24)
    return {"email": email, "user_id": uid, "action": action, "admin_api_key": api_key}
