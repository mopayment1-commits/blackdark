"""
BLACKDARK — Model Weights Encryption Guard (Point 49).

Lightweight XOR obfuscation for oracle dimension weights stored on disk.
Not military-grade — prevents casual copy of tuned weights from data/.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ModelWeightsGuard")

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "data" / "model_weights.json"


def _derive_key(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def weights_secret() -> str:
    return (
        os.getenv("MODEL_WEIGHTS_KEY")
        or os.getenv("BLACKDARK_B2B_API_KEY")
        or "blackdark-local-dev-weights"
    )


def encrypt_weights_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    key = _derive_key(weights_secret())
    return base64.urlsafe_b64encode(_xor_bytes(raw, key)).decode("ascii")


def decrypt_weights_payload(token: str) -> dict[str, Any]:
    key = _derive_key(weights_secret())
    raw = _xor_bytes(base64.urlsafe_b64decode(token.encode("ascii")), key)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Decrypted weights payload is not a dict")
    return data


def save_weights(payload: dict[str, Any], path: Path | None = None) -> Path:
    target = path or DEFAULT_WEIGHTS_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    encrypted = encrypt_weights_payload(payload)
    target.write_text(
        json.dumps({"encrypted": True, "payload": encrypted}, indent=2),
        encoding="utf-8",
    )
    logger.info("Model weights saved | path=%s", target.name)
    return target


def load_weights(path: Path | None = None) -> dict[str, Any] | None:
    target = path or DEFAULT_WEIGHTS_PATH
    if not target.exists():
        return None
    try:
        wrapper = json.loads(target.read_text(encoding="utf-8"))
        if wrapper.get("encrypted") and wrapper.get("payload"):
            return decrypt_weights_payload(str(wrapper["payload"]))
        if isinstance(wrapper, dict) and "dimensions" in wrapper:
            return wrapper
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        logger.warning("Unable to load model weights | reason=%s", exc)
    return None
