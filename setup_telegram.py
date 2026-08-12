"""
BLACKDARK — Telegram one-step setup.

Usage: python setup_telegram.py

Secret values are written only to a private file (mode 0600).
No secret values and no secret-file path pointers are written to .env.
Runtime loads `keys/telegram.secrets.env` by default (see env_secrets_loader).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
SECRET_FILE = ROOT / "keys" / "telegram.secrets.env"

TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")

sys.path.insert(0, str(ROOT / "scripts"))
from _secret_io import write_private_text  # noqa: E402


def _read_env() -> list[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def _write_env_flags(lines: list[str]) -> None:
    """Persist non-secret boolean/username flags only."""
    # Constant project .env path — not user-controlled.
    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")  # NOSONAR pythonsecurity:S2083,pythonsecurity:S8707


def _upsert_env(key: str, value: str, lines: list[str]) -> list[str]:
    prefix = f"{key}="
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = f"{prefix}{value}"
            return lines
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(f"{key}={value}")
    return lines


def _validate_token(token: str) -> dict:
    from path_safety import open_http_url

    url = f"https://api.telegram.org/bot{token}/getMe"
    with open_http_url(url, timeout=15, allowed_hosts={"api.telegram.org"}) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise ValueError(payload.get("description") or "Invalid token")
    return payload["result"]


def _persist_telegram_secrets(token: str, chat: str) -> None:
    """Write token/chat only to the private 0600 file (never to .env, never printed)."""
    secret_lines = [
        "# BLACKDARK Telegram secrets — mode 0600 — do not commit",
        f"TELEGRAM_BOT_TOKEN={token}",
    ]
    if chat:
        secret_lines.append(f"TELEGRAM_CHAT_ID={chat}")
    write_private_text(SECRET_FILE, "\n".join(secret_lines) + "\n")


def _persist_nonsecret_flags(username: str) -> None:
    lines = _read_env()
    if not lines:
        example = ROOT / ".env.example"
        lines = example.read_text(encoding="utf-8").splitlines() if example.exists() else ["# BLACKDARK"]

    if username:
        lines = _upsert_env("TELEGRAM_BOT_USERNAME", username, lines)
    lines = _upsert_env("TELEGRAM_FREE_ALERTS_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_POLLING_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_ALERTS_ENABLED", "true", lines)
    # Strip any prior cleartext token/chat/pointer lines from .env if present.
    strip_prefixes = (
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "TELEGRAM_SECRETS_FILE=",
    )
    lines = [ln for ln in lines if not ln.startswith(strip_prefixes)]
    _write_env_flags(lines)


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — Telegram Setup")
    print("=" * 60)
    print()
    print("1) Open Telegram → @BotFather → /newbot")
    print("2) Copy the token BotFather sends")
    print("3) Paste it below")
    print("Secret values are written only to a private file (mode 0600).")
    print("They are never printed and never stored in .env.")
    print()

    token = input("TELEGRAM_BOT_TOKEN: ").strip()
    if not token:
        print("\nNo token provided.")
        return 1
    if not TOKEN_RE.match(token):
        print("\nInvalid token format. Expected: 7123456789:AAHxxxx...")
        return 1

    print("\nValidating with Telegram API...")
    try:
        bot = _validate_token(token)
    except urllib.error.HTTPError as exc:
        print(f"\nToken rejected (HTTP {exc.code}). Copy again from BotFather.")
        return 1
    except Exception:
        print("\nConnection failed (network or API unavailable).")
        return 1

    username = str(bot.get("username") or "").strip()
    bot_name = str(bot.get("first_name") or "Bot")
    print(f"\nOK — Bot: {bot_name} (@{username})")

    chat = input("Your TELEGRAM_CHAT_ID (message /start to bot, optional now): ").strip()

    _persist_telegram_secrets(token, chat)
    del token
    del chat
    _persist_nonsecret_flags(username)

    print("\nWrote private secrets file (mode 0600).")
    print("Runtime loads keys/telegram.secrets.env by default (no .env secret pointer).")
    print("Optional override: TELEGRAM_SECRETS_FILE=<path> in process env only.")
    if username:
        print(f"Open bot: https://t.me/{username} → send /start")
    print("Test: http://127.0.0.1:8080/api/alerts/telegram/status")
    print("Then restart: start_blackdark.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
