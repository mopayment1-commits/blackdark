"""
BLACKDARK — Identity, profile, and account recovery (Trust OS).

Standards posture:
- NIST SP 800-63B-inspired passwords (length + blocked commons; no theater rules)
- Email as primary authenticator; optional public @username for Proof sharing
- Email verification + password reset via one-time hashed tokens
- Avatars: generated initials by default; optional constrained upload
- OAuth state CSRF binding for Google/GitHub
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BILLING_NOTE = "USD self-serve via hosted PSP — card data never stored here."

USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,23}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Compact blocklist — extend via IDENTITY_BLOCKED_PASSWORDS env (comma-separated).
_COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "12345678",
    "123456789",
    "1234567890",
    "qwerty123",
    "letmein1",
    "welcome1",
    "admin123",
    "blackdark",
    "trustos1",
    "iloveyou",
    "abc12345",
}

TOKEN_TTL_MINUTES = {
    "email_verify": int(os.getenv("IDENTITY_VERIFY_TTL_MIN", "60")),
    "password_reset": int(os.getenv("IDENTITY_RESET_TTL_MIN", "45")),
}

AVATAR_DIR = Path(os.getenv("IDENTITY_AVATAR_DIR", "data/avatars"))
AVATAR_MAX_BYTES = int(os.getenv("IDENTITY_AVATAR_MAX_BYTES", str(2 * 1024 * 1024)))
ALLOWED_AVATAR_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def hash_token(raw: str) -> str:
    pepper = os.getenv("SESSION_TOKEN_PEPPER", "blackdark-identity").encode("utf-8")
    return hashlib.sha256(pepper + raw.encode("utf-8")).hexdigest()


def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise ValueError("Valid email required")
    return email


def validate_password(password: str, *, email: str = "") -> None:
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")
    if len(password) > 128:
        raise ValueError("Password too long")
    lowered = password.lower().strip()
    blocked = set(_COMMON_PASSWORDS)
    extra = os.getenv("IDENTITY_BLOCKED_PASSWORDS", "")
    if extra:
        blocked.update(x.strip().lower() for x in extra.split(",") if x.strip())
    if lowered in blocked:
        raise ValueError("Password is too common — choose a stronger one")
    local = (email or "").split("@")[0].lower()
    if local and len(local) >= 4 and local in lowered:
        raise ValueError("Password must not contain your email local-part")
    # Reject all-numeric
    if password.isdigit():
        raise ValueError("Password must not be only numbers")


def validate_username(username: str) -> str:
    u = (username or "").strip().lower()
    if not USERNAME_RE.match(u):
        raise ValueError(
            "Username must be 3–24 chars, start with a letter, and use a-z, 0-9, underscore"
        )
    reserved = {
        "admin",
        "api",
        "support",
        "blackdark",
        "oracle",
        "whale",
        "system",
        "root",
        "null",
        "undefined",
        "login",
        "signup",
        "profile",
        "billing",
        "security",
    }
    if u in reserved:
        raise ValueError("Username is reserved")
    return u


def validate_display_name(name: str) -> str:
    name = (name or "").strip()
    if len(name) > 80:
        raise ValueError("Display name too long")
    return name


def avatar_initials(name: str, email: str) -> str:
    base = (name or "").strip() or (email or "").split("@")[0]
    parts = [p for p in re.split(r"[\s._-]+", base) if p]
    if not parts:
        return "BD"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def default_avatar_svg(name: str, email: str) -> str:
    initials = avatar_initials(name, email)
    # Deterministic hue from email
    digest = hashlib.sha256((email or initials).encode()).hexdigest()
    hue = int(digest[:2], 16) % 360
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
        f'<rect width="128" height="128" rx="64" fill="hsl({hue} 45% 28%)"/>'
        f'<text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="system-ui,sans-serif" font-size="48" font-weight="700" fill="#e4e4e7">'
        f"{initials}</text></svg>"
    )


def identity_architecture() -> dict[str, Any]:
    from oauth_service import oauth_status

    return {
        "product": "BLACKDARK Trust OS",
        "primary_authenticator": "email",
        "login_methods": ["email_password", "google_oauth", "github_oauth"],
        "phone_auth": False,
        "username": {
            "login": False,
            "public_handle": True,
            "pattern": USERNAME_RE.pattern,
        },
        "password_policy": {
            "min_length": 10,
            "max_length": 128,
            "block_common": True,
            "hash": "pbkdf2_sha256",
        },
        "email_verification": True,
        "password_reset": True,
        "mfa": "totp_optional",
        "avatar": {"default": "initials_svg", "upload": True, "max_bytes": AVATAR_MAX_BYTES},
        "oauth": oauth_status(),
        "profile_fields": [
            "email",
            "display_name",
            "username",
            "avatar",
            "ui_lang",
            "ux_mode",
            "timezone",
            "telegram_chat_id",
            "tier",
            "mfa",
            "email_verified",
        ],
        "standards": [
            "NIST SP 800-63B (password length + blocked commons)",
            "OWASP ASVS session / recovery",
            "OAuth 2.0 state CSRF",
            "GDPR export/erase (existing privacy routes)",
        ],
        "billing_note": BILLING_NOTE,
    }


async def enqueue_identity_email(to_email: str, subject: str, body: str) -> dict[str, Any]:
    from email_outbox import enqueue_email, flush_email_outbox

    row = enqueue_email(to_email, subject, body, payload={"kind": "identity"})
    try:
        flush = await flush_email_outbox(limit=20)
    except Exception:
        flush = {"status": "flush_error"}
    return {"queued": row, "flush": flush}


async def issue_auth_token(user_id: int, token_type: str) -> str:
    from database import insert_auth_token

    if token_type not in TOKEN_TTL_MINUTES:
        raise ValueError("Invalid token type")
    raw = secrets.token_urlsafe(32)
    expires = _utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES[token_type])
    await insert_auth_token(
        user_id=user_id,
        token_type=token_type,
        token_hash=hash_token(raw),
        expires_at=expires.isoformat(),
    )
    return raw


async def consume_auth_token(raw: str, token_type: str) -> int:
    """Validate and consume token; return user_id."""
    from database import consume_auth_token_row

    user_id = await consume_auth_token_row(hash_token(raw), token_type)
    if not user_id:
        raise ValueError("Invalid or expired link")
    return int(user_id)


def debug_tokens_enabled() -> bool:
    """Dev-only. Hard-off in production/prod even if env is mistakenly set."""
    env = (
        os.getenv("ENV") or os.getenv("APP_ENV") or os.getenv("RAILWAY_ENVIRONMENT") or ""
    ).strip().lower()
    if env in {"production", "prod"}:
        return False
    return os.getenv("IDENTITY_DEBUG_TOKENS", "").lower() in {"1", "true", "yes"}


async def send_verification_email(user_id: int, email: str) -> dict[str, Any]:
    raw = await issue_auth_token(user_id, "email_verify")
    base = (os.getenv("APP_BASE_URL") or "http://127.0.0.1:8080").rstrip("/")
    link = f"{base}/verify-email?token={raw}"
    body = (
        "Verify your BLACKDARK email.\n\n"
        f"Open this link within {TOKEN_TTL_MINUTES['email_verify']} minutes:\n{link}\n\n"
        "If you did not create an account, ignore this message.\n"
    )
    sent = await enqueue_identity_email(email, "Verify your BLACKDARK email", body)
    out: dict[str, Any] = {"sent": True, "channel": "email_outbox_or_smtp"}
    if debug_tokens_enabled():
        out["debug_token"] = raw
        out["debug_link"] = link
    out["delivery"] = sent.get("flush", {})
    return out


async def send_password_reset_email(user_id: int, email: str) -> dict[str, Any]:
    raw = await issue_auth_token(user_id, "password_reset")
    base = (os.getenv("APP_BASE_URL") or "http://127.0.0.1:8080").rstrip("/")
    link = f"{base}/reset-password?token={raw}"
    body = (
        "Reset your BLACKDARK password.\n\n"
        f"Open this one-time link within {TOKEN_TTL_MINUTES['password_reset']} minutes:\n{link}\n\n"
        "If you did not request this, ignore this message. "
        "Your password will not change until you open the link.\n"
    )
    sent = await enqueue_identity_email(email, "Reset your BLACKDARK password", body)
    out: dict[str, Any] = {"sent": True, "channel": "email_outbox_or_smtp"}
    if debug_tokens_enabled():
        out["debug_token"] = raw
        out["debug_link"] = link
    out["delivery"] = sent.get("flush", {})
    return out


async def store_oauth_state_async(provider: str, state: str) -> None:
    from database import insert_oauth_state

    expires = (_utcnow() + timedelta(minutes=15)).isoformat()
    await insert_oauth_state(provider=provider, state=state, expires_at=expires)


async def validate_oauth_state_async(provider: str, state: str | None) -> None:
    from database import consume_oauth_state

    if not state:
        raise ValueError("Missing OAuth state")
    ok = await consume_oauth_state(provider=provider, state=state)
    if not ok:
        raise ValueError("Invalid or expired OAuth state")


def save_avatar_bytes(user_id: int, content_type: str, data: bytes) -> str:
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise ValueError("Avatar must be JPEG, PNG, or WebP")
    if len(data) > AVATAR_MAX_BYTES:
        raise ValueError(f"Avatar must be ≤ {AVATAR_MAX_BYTES} bytes")
    # Magic-byte sniff
    if content_type == "image/jpeg" and not data.startswith(b"\xff\xd8"):
        raise ValueError("Invalid JPEG data")
    if content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid PNG data")
    if content_type == "image/webp" and data[0:4] != b"RIFF":
        raise ValueError("Invalid WebP data")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    # Remove prior extensions
    for ext in (".jpg", ".png", ".webp"):
        old = AVATAR_DIR / f"{user_id}{ext}"
        if old.exists():
            old.unlink()
    ext = ALLOWED_AVATAR_TYPES[content_type]
    path = AVATAR_DIR / f"{user_id}{ext}"
    path.write_bytes(data)
    return f"/api/auth/avatar/{user_id}{ext}"


def resolve_avatar_file(user_id: int) -> Path | None:
    for ext in (".jpg", ".png", ".webp"):
        path = AVATAR_DIR / f"{user_id}{ext}"
        if path.is_file():
            return path
    return None
