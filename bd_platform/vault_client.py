"""HashiCorp Vault client — optional cloud secrets; local Fernet fallback."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.VaultClient")

MOUNT = os.getenv("VAULT_KV_MOUNT", "secret")
PATH_PREFIX = os.getenv("VAULT_SECRET_PATH", "blackdark")
_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_LOCAL_STORE = Path("keys") / "vault_store.json"


def _safe_secret_key(key: str) -> str:
    """Reject path traversal / absolute segments in vault key names."""
    raw = (key or "").strip()
    if not raw or ".." in raw or "/" in raw or "\\" in raw or not _SAFE_KEY.match(raw):
        raise ValueError("invalid_vault_secret_key")
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in "._-")
    if cleaned != raw or not cleaned:
        raise ValueError("invalid_vault_secret_key")
    return cleaned


def _storage_id(safe_key: str) -> str:
    """Non-path identifier for local/KV storage (hex digest only)."""
    return hashlib.sha256(f"bd-vault-key:{safe_key}".encode()).hexdigest()


def _vault_kv_path(safe_key: str) -> str:
    """KV path uses digest under a fixed prefix — no raw user path segments."""
    prefix = "".join(ch for ch in PATH_PREFIX if ch.isalnum() or ch in "._-") or "blackdark"
    return f"{prefix}/{_storage_id(safe_key)}"


def vault_addr() -> str:
    return os.getenv("VAULT_ADDR", "").strip()


def vault_configured() -> bool:
    return bool(vault_addr()) and bool(os.getenv("VAULT_TOKEN", "").strip())


def _local_fernet_ok() -> bool:
    try:
        from secrets_vault import get_vault_key

        get_vault_key()
        return True
    except Exception:
        return False


def vault_status() -> dict[str, Any]:
    hvac_ok = False
    if vault_configured():
        try:
            import hvac

            client = hvac.Client(url=vault_addr(), token=os.getenv("VAULT_TOKEN", ""))
            hvac_ok = bool(client.is_authenticated())
        except Exception:
            hvac_ok = False
    return {
        "hashicorp_configured": vault_configured(),
        "hashicorp_authenticated": hvac_ok,
        "vault_addr": vault_addr() or None,
        "kv_mount": MOUNT,
        "secret_path_prefix": PATH_PREFIX,
        "local_fernet_available": _local_fernet_ok(),
        "primary": "hashicorp" if hvac_ok else "local_fernet",
        "note": "Docker: vault service in docker-compose.yml · VAULT_ADDR=http://localhost:8200",
    }


def _hvac_client() -> Any:
    import hvac

    client = hvac.Client(url=vault_addr(), token=os.getenv("VAULT_TOKEN", ""))
    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")
    return client


def _load_local_blob() -> dict[str, str]:
    if not _LOCAL_STORE.is_file():
        return {}
    import json

    return json.loads(_LOCAL_STORE.read_text(encoding="utf-8"))


def _save_local_blob(blob: dict[str, str]) -> None:
    import json

    _LOCAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(blob, indent=2)
    # Fixed path only (module constant). Encrypted JSON payload — not a user path.
    _LOCAL_STORE.write_text(payload, encoding="utf-8")  # NOSONAR(S2083)


def read_secret(key: str) -> dict[str, Any]:
    """Read secret from Vault KV v2 or local encrypted store."""
    try:
        safe_key = _safe_secret_key(key)
        kv_path = _vault_kv_path(safe_key)
        storage_id = _storage_id(safe_key)
    except ValueError:
        return {"source": "none", "error": "invalid_vault_secret_key"}
    if vault_configured():
        try:
            client = _hvac_client()
            secret = client.secrets.kv.v2.read_secret_version(path=kv_path, mount_point=MOUNT)
            data = (secret.get("data") or {}).get("data") or {}
            return {"source": "hashicorp", "path": kv_path, "data": data}
        except Exception:
            logger.warning("Vault read failed | event=vault_read_failed")
            return {"source": "hashicorp", "error": "vault_read_failed", "stored": False}

    try:
        from secrets_vault import decrypt_secret

        blob = _load_local_blob()
        enc = blob.get(storage_id) or blob.get(safe_key)
        if enc:
            return {
                "source": "local_fernet",
                "path": safe_key,
                "data": {"value": decrypt_secret(enc)},
            }
    except Exception:
        logger.warning("Local vault read failed | event=local_vault_read_failed")
        return {"source": "local_fernet", "error": "local_vault_read_failed"}

    return {"source": "none", "note": "Secret not found — use store_secret first."}


def store_secret(key: str, value: str) -> dict[str, Any]:
    """Store secret in Vault or local encrypted JSON."""
    try:
        safe_key = _safe_secret_key(key)
        kv_path = _vault_kv_path(safe_key)
        storage_id = _storage_id(safe_key)
    except ValueError:
        return {"source": "none", "error": "invalid_vault_secret_key", "stored": False}
    if vault_configured():
        try:
            client = _hvac_client()
            client.secrets.kv.v2.create_or_update_secret(
                path=kv_path,
                mount_point=MOUNT,
                secret={"value": value},
            )
            return {"source": "hashicorp", "path": kv_path, "stored": True}
        except Exception:
            logger.warning("Vault store failed | event=vault_store_failed")
            return {"source": "hashicorp", "error": "vault_store_failed", "stored": False}

    from secrets_vault import encrypt_secret

    blob = _load_local_blob()
    blob[storage_id] = encrypt_secret(value)
    _save_local_blob(blob)
    return {"source": "local_fernet", "path": safe_key, "stored": True}
