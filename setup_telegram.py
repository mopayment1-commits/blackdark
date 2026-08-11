"""
BLACKDARK — Telegram one-step setup.

Usage: python setup_telegram.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")


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
        print(f"\nToken rejected ({exc.code}). Copy again from BotFather.")
        return 1
    except Exception as exc:
        print(f"\nConnection failed: {exc}")
        return 1

    username = str(bot.get("username") or "").strip()
    bot_name = str(bot.get("first_name") or "Bot")
    print(f"\nOK — Bot: {bot_name} (@{username})")

    chat = input("Your TELEGRAM_CHAT_ID (message /start to bot, optional now): ").strip()

    lines = _read_env()
    if not lines:
        example = ROOT / ".env.example"
        lines = example.read_text(encoding="utf-8").splitlines() if example.exists() else ["# BLACKDARK"]

    lines = _upsert_env("TELEGRAM_BOT_TOKEN", token, lines)
    if username:
        lines = _upsert_env("TELEGRAM_BOT_USERNAME", username, lines)
    if chat:
        lines = _upsert_env("TELEGRAM_CHAT_ID", chat, lines)
    lines = _upsert_env("TELEGRAM_FREE_ALERTS_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_POLLING_ENABLED", "true", lines)
    lines = _upsert_env("TELEGRAM_ALERTS_ENABLED", "true", lines)
    _write_env(lines)

    print(f"\nSaved to: {ENV_PATH}")
    print(f"Open bot: https://t.me/{username} → send /start")
    print("Test: http://127.0.0.1:8080/api/alerts/telegram/status")
    print("Then restart: start_blackdark.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
