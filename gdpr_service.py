"""
BLACKDARK — GDPR data subject rights (export / erasure).

Merged with #949 Data Retention Governance via data_retention_governance.py.
Article 17 erasure uses 30-day soft-delete grace → automated hard delete.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.GDPR")


async def export_user_data(email: str) -> dict[str, Any]:
    """Article 15/20 — portable export of user-linked data (no secrets)."""
    from data_retention_governance import retention_deletion_policy_status
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

    tiers = retention_deletion_policy_status().get("retention_tiers") or {}
    return {
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
        "retention_tiers": tiers,
        "contact": "support@blackdark.io",
    }


async def erase_user_data(email: str, *, confirmed: bool = False) -> dict[str, Any]:
    """
    Article 17 — erasure workflow (#1023 + #949).
    Schedules soft-delete with 30-day grace; hard delete via daily cron.
    """
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=true to schedule permanent data erasure.",
            "gdpr_article": 17,
        }

    from data_retention_governance import schedule_erasure

    result = await schedule_erasure(email, actor="user", reason="gdpr_article_17")
    logger.info(
        "GDPR erasure scheduled | email=%s status=%s",
        email.strip().lower(),
        result.get("status"),
    )
    return {
        **result,
        "gdpr_article": 17,
        "implementation": "data_retention_governance.schedule_erasure",
    }


def gdpr_compliance_status() -> dict[str, Any]:
    from data_retention_governance import (
        backup_deletion_note,
        retention_deletion_policy_status,
        stripe_billing_retention_note,
    )

    retention = retention_deletion_policy_status()
    return {
        "dsr_export_api": "/api/privacy/dsr/export",
        "dsr_erase_api": "/api/privacy/dsr/erase",
        "dsr_status_api": "/api/privacy/dsr/status",
        "retention_policy_api": "/api/platform/retention-deletion/status",
        "consent_documented_in": "legal_content.py /privacy",
        "data_room": "docs/DATA_ROOM.md",
        "implementation": "gdpr_service.py + data_retention_governance.py",
        "retention_deletion_policy": retention,
        "stripe_billing": stripe_billing_retention_note(),
        "backup_deletion": backup_deletion_note(),
        "ready_for_dd": True,
        "note": "Legal review and DPIA still required before EU user-base transfer in M&A.",
    }
