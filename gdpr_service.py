"""
BLACKDARK — GDPR data subject rights (export / erasure).

Implements technical DSR workflow for acquisition due diligence requirement #19.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
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

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
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


async def erase_user_data(email: str, *, confirmed: bool = False) -> dict[str, Any]:
    """Article 17 — erasure (requires explicit confirmation)."""
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=true to permanently erase user data.",
        }

    from database import erase_user_personal_data

    normalized = email.strip().lower()
    result = await erase_user_personal_data(normalized)
    logger.info("GDPR erasure completed | email=%s rows=%s", normalized, result.get("rows_deleted"))
    return {
        "status": "erased",
        "subject_email": normalized,
        "erased_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }


def gdpr_compliance_status() -> dict[str, Any]:
    return {
        "dsr_export_api": "/api/privacy/dsr/export",
        "dsr_erase_api": "/api/privacy/dsr/erase",
        "request_deletion_page": "/request-deletion",
        "request_deletion_api": "/api/privacy/request-deletion",
        "report_issue_api": "/api/privacy/report-issue",
        "terms_accept_api": "/api/legal/accept-terms",
        "consent_documented_in": "legal_content.py /privacy + terms_consent.py",
        "data_room": "docs/DATA_ROOM.md",
        "implementation": "gdpr_service.py",
        "ready_for_dd": True,
        "note": "Legal review and DPIA still required before EU user-base transfer in M&A.",
    }
