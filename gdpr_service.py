"""
BLACKDARK — GDPR data subject rights (export / erasure).

Implements technical DSR workflow for acquisition due diligence requirement #19.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.GDPR")


async def export_user_data(email: str) -> dict[str, Any]:
    """Article 15/20 — portable export of user-linked data (no secrets)."""
    from database import (
        fetch_journal_entries,
        fetch_oracle_usage_today,
        fetch_user_by_email,
        fetch_user_profile,
    )

    normalized = email.strip().lower()
    user = await fetch_user_by_email(normalized)
    profile = await fetch_user_profile(normalized) if user else None
    journal: list[dict] = []
    if user:
        journal = await fetch_journal_entries(user["email"])

    from financial_data.boundary import gate_support_export
    from financial_data.dlp import sanitize_financial_payload

    export_payload = {
        "exported_at": datetime.now(UTC).isoformat(),
        "subject_email": normalized,
        "found": user is not None,
        "profile": profile,
        "account": {
            "id": user.get("id") if user else None,
            "email": user.get("email") if user else normalized,
            "tier": user.get("tier") if user else None,
            "created_at": user.get("created_at") if user else None,
        },
        "oracle_usage_today": await fetch_oracle_usage_today(normalized) if user else 0,
        "journal_entries": journal,
        "api_keys": "redacted — use authenticated /api/user/exchange-keys",
        "legal_basis": "contract_and_legitimate_interest",
        "retention_policy_days": 365,
        "contact": "support@blackdark.io",
    }
    gate_support_export(export_payload)
    return sanitize_financial_payload(export_payload)


async def erase_user_data(email: str, *, confirmed: bool = False) -> dict[str, Any]:
    """Article 17 — erasure via FDS retention-aware account closure."""
    from fds_retention_incident.account_closure import close_account

    normalized = email.strip().lower()
    result = await close_account(normalized, confirmed=confirmed, actor="dsr_erase")
    if result.get("status") == "confirmation_required":
        return {
            "status": "confirmation_required",
            "message": "Set confirm=true to permanently erase user data.",
        }
    if result.get("status") == "not_found":
        return {"status": "not_found", "subject_email": normalized}
    logger.info(
        "GDPR erasure completed | email=%s rows=%s retained=%s",
        normalized,
        result.get("rows_deleted"),
        len(result.get("retained_legal_security", [])),
    )
    return {
        "status": "erased",
        "subject_email": normalized,
        "erased_at": result.get("closed_at", datetime.now(UTC).isoformat()),
        "retention_aware": True,
        **result,
    }


def gdpr_compliance_status() -> dict[str, Any]:
    return {
        "dsr_export_api": "/api/privacy/dsr/export",
        "dsr_erase_api": "/api/privacy/dsr/erase",
        "consent_documented_in": "legal_content.py /privacy",
        "data_room": "docs/DATA_ROOM.md",
        "implementation": "gdpr_service.py",
        "ready_for_dd": True,
        "note": "Legal review and DPIA still required before EU user-base transfer in M&A.",
    }
