"""
BLACKDARK — Telegram one-step setup.

Usage: python setup_telegram.py

Secret values are written only to a private file (mode 0600).
The project .env receives the path pointer + non-secret flags only.
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


def _write_env(lines: list[str]) -> None:
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


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — Telegram Setup")
    print("=" * 60)
    print()
    print("1) Open Telegram → @BotFather → /newbot")
    print("2) Copy the token BotFather sends")
    print("3) Paste it below")
    print("Secret values are written only to a private file (mode 0600).")
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

    secret_lines = [
        "# BLACKDARK Telegram secrets — mode 0600 — do not commit",
        f"TELEGRAM_BOT_TOKEN={token}",
    ]
    if chat:
        secret_lines.append(f"TELEGRAM_CHAT_ID={chat}")
    write_private_text(SECRET_FILE, "\n".join(secret_lines) + "\n")

    lines = _read_env()
    if not lines:
        example = ROOT / ".env.example"
        lines = example.read_text(encoding="utf-8").splitlines() if example.exists() else ["# BLACKDARK"]

    # Do not write the raw token into .env — pointer + non-secret flags only.
    secret_rel = str(SECRET_FILE.relative_to(ROOT)).replace("\\", "/")
    lines = _upsert_env("TELEGRAM_SECRETS_FILE", secret_rel, lines)
    if username:
        lines = _upsert_env("TELEGRAM_BOT_USERNAME", username, lines)
    lines = _upsert_env("TELEGRAM_FREE_ALERTS_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_POLLING_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_ALERTS_ENABLED", "true", lines)
    # Strip any prior cleartext token line from .env if present.
    lines = [ln for ln in lines if not ln.startswith("TELEGRAM_BOT_TOKEN=")]
    if chat:
        # Chat id is less sensitive but keep it with the secret file; strip from .env.
        lines = [ln for ln in lines if not ln.startswith("TELEGRAM_CHAT_ID=")]
    _write_env(lines)

    print(f"\nWrote private secrets file: {secret_rel} (mode 0600)")
    print(f"Pointer saved to: {ENV_PATH} (TELEGRAM_SECRETS_FILE)")
    print("Load secrets before start: set -a; . keys/telegram.secrets.env; set +a")
    if username:
        print(f"Open bot: https://t.me/{username} → send /start")
    print("Test: http://127.0.0.1:8080/api/alerts/telegram/status")
    print("Then restart: start_blackdark.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
