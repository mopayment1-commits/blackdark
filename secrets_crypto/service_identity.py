"""Scoped service/workload identities (FDS-13 / SDG-04)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from secrets_crypto.production_policy import is_production_crypto_env

_SERVICE_SCOPES: dict[str, set[str]] = {
    "web": {"api.read", "api.write", "billing.webhook.receive"},
    "aggregator": {"market.poll", "price.read"},
    "arbitrage": {"market.scan", "execution.submit"},
    "ingestion": {"data.ingest", "lake.write"},
    "all": {"api.read", "api.write", "market.poll", "data.ingest"},
}

_CREDENTIAL_TTL_SEC = int(os.getenv("SERVICE_CREDENTIAL_TTL_SEC", "3600"))
_CREDENTIALS: dict[str, dict[str, Any]] = {}
_REVOKED: set[str] = set()


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "service_identity_evidence.jsonl"


def _append_event(event: dict[str, Any]) -> None:
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def current_service_mode() -> str:
    return (os.getenv("SERVICE_MODE") or "all").strip().lower()


def service_identity_inventory() -> list[dict[str, Any]]:
    return [
        {
            "service_mode": mode,
            "scopes": sorted(scopes),
            "short_lived": True,
            "shared_static_credential": False,
        }
        for mode, scopes in sorted(_SERVICE_SCOPES.items())
    ]


def issue_service_credential(
    *,
    service_mode: str,
    purpose: str,
    actor: str = "system",
) -> dict[str, Any]:
    mode = service_mode.strip().lower()
    if mode not in _SERVICE_SCOPES:
        raise ValueError("unknown_service_mode")
    if is_production_crypto_env() and mode == "all":
        raise PermissionError("monolith_all_mode_forbidden_in_production")
    token = secrets.token_urlsafe(32)
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = time.time()
    rec = {
        "credential_id": secrets.token_hex(8),
        "service_mode": mode,
        "scopes": sorted(_SERVICE_SCOPES[mode]),
        "purpose": purpose,
        "issued_at": now,
        "expires_at": now + _CREDENTIAL_TTL_SEC,
        "issued_by": actor,
        "fingerprint": fingerprint,
    }
    _CREDENTIALS[fingerprint] = rec
    _append_event({"event": "service_credential_issued", **rec})
    return {**rec, "token": token}


def verify_service_credential(token: str, *, required_scope: str) -> dict[str, Any]:
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if fingerprint in _REVOKED:
        raise PermissionError("service_credential_revoked")
    rec = _CREDENTIALS.get(fingerprint)
    if not rec:
        raise PermissionError("service_credential_unknown")
    if time.time() >= float(rec.get("expires_at") or 0):
        raise PermissionError("service_credential_expired")
    scopes = set(rec.get("scopes") or [])
    if required_scope not in scopes:
        raise PermissionError("service_scope_denied")
    return rec


def revoke_service_credential(token: str, *, actor: str, reason: str = "") -> bool:
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if fingerprint not in _CREDENTIALS:
        return False
    _REVOKED.add(fingerprint)
    _append_event(
        {
            "event": "service_credential_revoked",
            "fingerprint": fingerprint,
            "service_mode": _CREDENTIALS[fingerprint].get("service_mode"),
            "actor": actor,
            "reason": reason,
        }
    )
    return True


def reject_shared_static_service_secret(secret_name: str) -> None:
    forbidden = {
        "SHARED_SERVICE_API_KEY",
        "GLOBAL_WORKER_SECRET",
        "ADMIN_API_KEY",
    }
    if secret_name in forbidden and is_production_crypto_env():
        raise PermissionError("shared_static_service_credential_forbidden")
