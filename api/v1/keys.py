"""Per-tenant Decision API keys — hashed at rest, shown once at issuance."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import UTC, datetime
from typing import Any

from api.v1.contract import CUSTOMER_SCOPES, DEFAULT_CUSTOMER_SCOPES, PLAN_LIMITS

logger = logging.getLogger("BLACKDARK.DecisionAPIKeys")

KEY_LIVE_PREFIX = "bd_live_"
KEY_TEST_PREFIX = "bd_test_"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def key_pepper() -> str:
    pepper = (
        os.getenv("DECISION_API_KEY_PEPPER", "").strip()
        or os.getenv("SESSION_TOKEN_PEPPER", "").strip()
    )
    if pepper:
        return pepper
    if _is_production():
        raise RuntimeError("DECISION_API_KEY_PEPPER or SESSION_TOKEN_PEPPER must be set in production")
    logger.warning("Decision API key pepper unset — using insecure dev default")
    return "blackdark-decision-api-dev-pepper"


def hash_api_key(plaintext: str) -> str:
    return hmac.new(key_pepper().encode("utf-8"), plaintext.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_api_key(*, environment: str) -> tuple[str, str]:
    env = "test" if environment == "test" else "live"
    head = KEY_TEST_PREFIX if env == "test" else KEY_LIVE_PREFIX
    secret = secrets.token_urlsafe(32)
    plaintext = f"{head}{secret}"
    prefix = plaintext[:16]
    return plaintext, prefix


def generate_signing_secret() -> str:
    return secrets.token_urlsafe(32)


def _normalize_scopes(scopes: list[str] | None) -> list[str]:
    requested = list(scopes or DEFAULT_CUSTOMER_SCOPES)
    cleaned: list[str] = []
    for raw in requested:
        scope = str(raw).strip()
        if scope not in CUSTOMER_SCOPES:
            raise ValueError(f"unsupported_scope:{scope}")
        if scope not in cleaned:
            cleaned.append(scope)
    if not cleaned:
        raise ValueError("scopes_required")
    return cleaned


def _plan_defaults(plan: str, environment: str) -> dict[str, int]:
    if environment == "test" or plan == "sandbox":
        return dict(PLAN_LIMITS["sandbox"])
    return dict(PLAN_LIMITS.get(plan) or PLAN_LIMITS["institutional"])


def public_key_view(row: dict[str, Any]) -> dict[str, Any]:
    scopes = row.get("scopes") or []
    if isinstance(scopes, str):
        try:
            scopes = json.loads(scopes)
        except json.JSONDecodeError:
            scopes = []
    return {
        "id": row.get("public_id"),
        "org_id": row.get("org_id"),
        "name": row.get("name"),
        "environment": row.get("environment"),
        "key_prefix": row.get("key_prefix"),
        "scopes": scopes,
        "plan": row.get("plan"),
        "rpm_limit": int(row.get("rpm_limit") or 0),
        "rpd_limit": int(row.get("rpd_limit") or 0),
        "created_at": row.get("created_at"),
        "last_used_at": row.get("last_used_at"),
        "revoked_at": row.get("revoked_at"),
        "status": "revoked" if row.get("revoked_at") else "active",
    }


async def issue_decision_api_key(
    *,
    org_id: str,
    name: str,
    created_by: str,
    environment: str = "live",
    plan: str = "institutional",
    scopes: list[str] | None = None,
    rpm_limit: int | None = None,
    rpd_limit: int | None = None,
) -> dict[str, Any]:
    """Sales-led issuance. Plaintext api_key + signing_secret returned once."""
    from database import insert_decision_api_key
    from secrets_vault import encrypt_secret

    org = str(org_id or "").strip()
    label = str(name or "").strip()
    if len(org) < 3 or len(org) > 64:
        raise ValueError("org_id_invalid")
    if len(label) < 2 or len(label) > 80:
        raise ValueError("name_invalid")
    env = "test" if str(environment).strip().lower() in {"test", "sandbox"} else "live"
    plan_name = "sandbox" if env == "test" else str(plan or "institutional").strip().lower()
    if plan_name not in PLAN_LIMITS:
        plan_name = "institutional"
    limits = _plan_defaults(plan_name, env)
    cleaned_scopes = _normalize_scopes(scopes)
    plaintext, prefix = generate_api_key(environment=env)
    signing = generate_signing_secret()
    public_id = f"dak_{secrets.token_hex(8)}"
    row = await insert_decision_api_key(
        public_id=public_id,
        org_id=org,
        name=label,
        environment=env,
        key_prefix=prefix,
        key_hash=hash_api_key(plaintext),
        signing_secret_encrypted=encrypt_secret(signing),
        scopes=cleaned_scopes,
        plan=plan_name,
        rpm_limit=int(rpm_limit or limits["rpm"]),
        rpd_limit=int(rpd_limit or limits["rpd"]),
        created_by=created_by.strip() or "admin",
        created_at=_utcnow(),
    )
    view = public_key_view(row)
    view["api_key"] = plaintext
    view["signing_secret"] = signing
    view["shown_once"] = True
    view["warning"] = "Store api_key and signing_secret now. They cannot be retrieved later."
    return view


async def authenticate_decision_api_key(presented: str) -> dict[str, Any]:
    from database import fetch_decision_api_key_by_prefix, touch_decision_api_key_usage

    raw = (presented or "").strip()
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    if not raw.startswith((KEY_LIVE_PREFIX, KEY_TEST_PREFIX)):
        raise PermissionError("invalid_api_key")
    if len(raw) < 20:
        raise PermissionError("invalid_api_key")
    prefix = raw[:16]
    row = await fetch_decision_api_key_by_prefix(prefix)
    if not row or row.get("revoked_at"):
        raise PermissionError("invalid_api_key")
    if not hmac.compare_digest(str(row["key_hash"]), hash_api_key(raw)):
        raise PermissionError("invalid_api_key")
    env_ok = (raw.startswith(KEY_TEST_PREFIX) and row["environment"] == "test") or (
        raw.startswith(KEY_LIVE_PREFIX) and row["environment"] == "live"
    )
    if not env_ok:
        raise PermissionError("invalid_api_key")
    await touch_decision_api_key_usage(str(row["public_id"]))
    scopes = row.get("scopes") or []
    if isinstance(scopes, str):
        try:
            scopes = json.loads(scopes)
        except json.JSONDecodeError:
            scopes = []
    row = dict(row)
    row["scopes"] = scopes
    return row


def principal_has_scope(row: dict[str, Any], scope: str) -> bool:
    scopes = row.get("scopes") or []
    return scope in scopes


async def revoke_decision_api_key(public_id: str, *, revoked_by: str) -> dict[str, Any] | None:
    from database import revoke_decision_api_key_row

    row = await revoke_decision_api_key_row(public_id, revoked_by=revoked_by, revoked_at=_utcnow())
    return public_key_view(row) if row else None
