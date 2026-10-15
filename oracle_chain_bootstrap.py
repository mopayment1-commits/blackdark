"""One-shot oracle audit chain bootstrap from oracle_predictions (empty JSONL only)."""

from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import HTTPException, Request


def _bootstrap_secret() -> str:
    for key in ("ORACLE_CHAIN_BOOTSTRAP_TOKEN", "TELEGRAM_BOT_TOKEN", "ADMIN_API_KEY"):
        value = (os.getenv(key) or "").strip()
        if value:
            return value
    return ""


def _verify_bootstrap_token(request: Request) -> None:
    expected = _bootstrap_secret()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "bootstrap_unconfigured",
                "message": "Set ORACLE_CHAIN_BOOTSTRAP_TOKEN or TELEGRAM_BOT_TOKEN on the web service.",
            },
        )
    provided = (request.headers.get("X-Oracle-Chain-Bootstrap-Token") or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")


async def bootstrap_chain_from_database_if_empty(request: Request) -> dict[str, Any]:
    """Append DB predictions to the hash chain when the on-disk JSONL is empty."""
    from oracle_audit_chain import verify_chain
    from oracle_track_record import backfill_from_database

    _verify_bootstrap_token(request)
    verify = verify_chain()
    records = int(verify.get("records") or 0)
    if records > 0:
        return {
            "ok": True,
            "skipped": True,
            "reason": "chain_not_empty",
            "chain_records": records,
            "integrity_valid": verify.get("valid"),
        }
    limit = int(os.getenv("ORACLE_CHAIN_BACKFILL_LIMIT", "50000"))
    result = await backfill_from_database(limit=limit)
    result["ok"] = True
    result["skipped"] = False
    result["bootstrap_limit"] = limit
    return result
