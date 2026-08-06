"""TODAY command-center API."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import optional_user

router = APIRouter(prefix="/api", tags=["today"])


@router.get("/today")
async def today_feed(user: dict | None = Depends(optional_user)):
    from today_feed import build_today_feed

    return await build_today_feed(user=user)
