"""Load private KEY=VALUE secret files into os.environ when pointer vars are set.

Used so setup scripts can keep raw secrets out of the project .env while runtime
still resolves TELEGRAM_BOT_TOKEN / similar once TELEGRAM_SECRETS_FILE is set.
Never logs secret values.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("BLACKDARK.EnvSecretsLoader")

_ROOT = Path(__file__).resolve().parent
_LOADED: set[str] = set()


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("secrets_file_unreadable path=%s", path.name)
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        out[key] = value.strip().strip('"').strip("'")
    return out


def load_secrets_file(env_pointer: str, *, override: bool = False) -> bool:
    """Load file pointed to by env_pointer into os.environ.

    Returns True when a file was loaded (or already loaded this process).
    Existing non-empty env values are preserved unless override=True.
    """
    pointer = os.getenv(env_pointer, "").strip()
    if not pointer:
        return False
    if pointer in _LOADED and not override:
        return True
    path = Path(pointer)
    if not path.is_absolute():
        path = _ROOT / path
    if not path.is_file():
        logger.warning("secrets_file_missing pointer=%s", env_pointer)
        return False
    for key, value in _parse_env_file(path).items():
        if override or not os.getenv(key, "").strip():
            os.environ[key] = value
    _LOADED.add(pointer)
    logger.info("secrets_file_loaded pointer=%s keys=%s", env_pointer, "present")
    return True


_DEFAULT_TELEGRAM_SECRETS = _ROOT / "keys" / "telegram.secrets.env"


def ensure_telegram_env() -> None:
    """Load Telegram secrets from TELEGRAM_SECRETS_FILE or the default 0600 path."""
    if load_secrets_file("TELEGRAM_SECRETS_FILE"):
        return
    if not os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and _DEFAULT_TELEGRAM_SECRETS.is_file():
        # Default private file — no .env pointer required (CodeQL: avoid storing
        # secret-path pointers next to cleartext project .env).
        pointer = str(_DEFAULT_TELEGRAM_SECRETS)
        if pointer in _LOADED:
            return
        for key, value in _parse_env_file(_DEFAULT_TELEGRAM_SECRETS).items():
            if not os.getenv(key, "").strip():
                os.environ[key] = value
        _LOADED.add(pointer)
        logger.info("secrets_file_loaded pointer=default_telegram keys=present")
