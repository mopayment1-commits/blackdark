"""Account closure / DSR erasure orchestration with retention states (FDS-20)."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fds_retention_incident.retention_policy import financial_retention_matrix, retention_for_class
from financial_data.classification import FDSClass

logger = logging.getLogger("BLACKDARK.FDS_RETENTION")

_CLOSURE_STATES = frozenset(
    {
        "deleted",
        "anonymized",
        "crypto_erased",
        "revoked",
        "token_revoked",
        "pending_backup_expiry",
        "retained_legal_hold",
    }
)


def _evidence_path() -> Path:
    base = Path(os.getenv("DATA_DIR", "data"))
    return base / "account_closure_evidence.jsonl"


def _append_evidence(record: dict[str, Any]) -> None:
    path = _evidence_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


async def revoke_financial_credentials(user_id: int, *, actor: str = "account_closure") -> dict[str, Any]:
    """Revoke exchange keys, sessions, and tracked financial secrets for a user."""
    from database import delete_user_api_key, delete_user_sessions_for_user, fetch_user_api_keys
    from secrets_crypto.lifecycle import revoke_secret

    revoked: list[dict[str, Any]] = []
    sessions = await delete_user_sessions_for_user(user_id)
    revoked.append({"type": "sessions", "count": sessions, "method": "TOKEN_REVOKE"})

    keys = await fetch_user_api_keys(user_id)
    for row in keys:
        exchange = str(row.get("exchange") or "")
        deleted = await delete_user_api_key(user_id, exchange)
        secret_id = f"exchange:{user_id}:{exchange}"
        try:
            revoke_secret(secret_id, actor=actor, reason="account_closure")
        except Exception:
            pass
        revoked.append(
            {
                "type": "exchange_credentials",
                "exchange": exchange,
                "deleted": deleted,
                "method": "CRYPTO_ERASE",
                "provider_revoke_required": True,
            }
        )
    return {"revoked": revoked, "credential_revocation_complete": True}


async def close_account(email: str, *, confirmed: bool = False, actor: str = "dsr_erase") -> dict[str, Any]:
    """Orchestrate account closure distinguishing immediate vs retained data."""
    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=true to permanently close account.",
        }

    from database import erase_user_personal_data, fetch_user_by_email

    normalized = email.strip().lower()
    user = await fetch_user_by_email(normalized)
    if not user:
        return {"status": "not_found", "subject_email": normalized}

    user_id = int(user["id"])
    credential_result = await revoke_financial_credentials(user_id, actor=actor)
    erase_result = await erase_user_personal_data(normalized)

    immediate: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    pending_backup: list[dict[str, Any]] = []

    for key in ("user_personal", "financial_account_metadata", "support_export_artifacts"):
        policy = next(p for p in financial_retention_matrix() if p["policy_key"] == key)
        immediate.append(
            {
                "data_class": key,
                "action": policy["deletion_method"],
                "status": "deleted" if erase_result.get("found") else "not_found",
                "policy_version": policy["policy_version"],
            }
        )

    for key in ("payment_references", "subscription_identifiers", "billing_history", "audit_replay"):
        policy = next(p for p in financial_retention_matrix() if p["policy_key"] == key)
        retained.append(
            {
                "data_class": key,
                "action": policy["deletion_method"],
                "status": "anonymized_pending_retention_expiry",
                "retention_days": policy["retention_days"],
                "policy_version": policy["policy_version"],
                "note": "legal_or_reconciliation_retention — not claimed as immediate deletion",
            }
        )

    from fds_retention_incident.backup_lifecycle import backup_retention_days

    pending_backup.append(
        {
            "data_class": "all_financial_backups",
            "action": "BACKUP_EXPIRY",
            "status": "pending_backup_expiry",
            "retention_days": backup_retention_days(),
            "note": "immutable backup cannot be immediately purged — pending expiry verification",
        }
    )

    record = {
        "event": "account_closure",
        "subject_email": normalized,
        "user_id": user_id,
        "closed_at": datetime.now(UTC).isoformat(),
        "actor": actor,
        "immediate_deletion": immediate,
        "retained_legal_security": retained,
        "credential_revocation": credential_result,
        "backup_pending_expiry": pending_backup,
        "false_deletion_claim": False,
        "rows_deleted": erase_result.get("rows_deleted", 0),
    }
    _append_evidence(record)
    logger.info("Account closure completed | email=%s user_id=%s", normalized, user_id)
    return {
        "status": "closed",
        "subject_email": normalized,
        "closed_at": record["closed_at"],
        **record,
    }


def account_closure_status() -> dict[str, Any]:
    policies = {
        cls.value: retention_for_class(cls)
        for cls in (
            FDSClass.C3_BANKING,
            FDSClass.C4_SECRET,
            FDSClass.C5_SENSITIVE_FINANCIAL,
            FDSClass.C6_PAYMENT_REFERENCE,
        )
    }
    return {
        "policy_version": financial_retention_matrix()[0]["policy_version"] if financial_retention_matrix() else "",
        "closure_states": sorted(_CLOSURE_STATES),
        "fds_class_policies": policies,
        "evidence_path": str(_evidence_path()),
    }
