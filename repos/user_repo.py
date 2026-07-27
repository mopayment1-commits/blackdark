"""Repository layer — users (thin wrapper over database)."""

from __future__ import annotations

from database import fetch_user_by_email, fetch_user_count


async def count_users() -> int:
    return await fetch_user_count()


async def get_by_email(email: str):
    return await fetch_user_by_email(email)
