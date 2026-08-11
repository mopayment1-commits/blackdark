#!/usr/bin/env python3
"""Telegram production setup — validate token, set webhook or enable polling."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

PROD_URL = os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app").rstrip("/")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _tg(method: str, token: str, payload: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload or {}).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def _validate_bot(token: str) -> dict | None:
    print("--- Validating bot token ---")
    try:
        me = _tg("getMe", token)
    except urllib.error.HTTPError as exc:
        print(f"  Invalid token (HTTP {exc.code})")
        return None
    except Exception:
        print("  Telegram unreachable")
        return None
    if not me.get("ok"):
        print("  Error: bot validation failed")
        return None
    return me


def _print_variables(vars_: list[tuple[str, str, str]]) -> None:
    print("\n--- Railway Variables (secrets masked) ---")
    for key, val, _hint in vars_:
        # Never interpolate env values into prints (CodeQL clear-text logging).
        print(f"  {key}: {'present' if bool(val) else 'missing'}")


def _configure_polling(token: str) -> None:
    print("\n--- Mode: long polling (dev/single-instance) ---")
    print("  Set TELEGRAM_POLLING_ENABLED=true on Railway")
    print("  Do NOT set webhook when using polling")
    try:
        _tg("deleteWebhook", token, {"drop_pending_updates": False})
        print("  Cleared any existing webhook.")
    except Exception:
        pass


def _configure_webhook(token: str, webhook_url: str, webhook_secret: str) -> None:
    print("\n--- Setting webhook (recommended for Railway) ---")
    payload: dict = {"url": webhook_url, "allowed_updates": ["message", "edited_message"]}
    if webhook_secret:
        payload["secret_token"] = webhook_secret
    try:
        wh = _tg("setWebhook", token, payload)
        if wh.get("ok"):
            print("  Webhook set successfully (URL not printed)")
        else:
            print("  setWebhook failed — check bot token and webhook URL in secret store")
    except Exception:
        print("  Could not set webhook (run from machine with network)")
        print("  Manual: use BotFather/API with token from your secret store (do not paste tokens into logs)")


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — Telegram Production Setup")
    print("=" * 60)
    print(f"\nProduction URL: {PROD_URL}\n")

    token = _env("TELEGRAM_BOT_TOKEN")
    webhook_url = _env("TELEGRAM_WEBHOOK_URL") or f"{PROD_URL}/api/telegram/webhook"
    webhook_secret = _env("TELEGRAM_WEBHOOK_SECRET")
    use_polling = _env("TELEGRAM_POLLING_ENABLED").lower() in {"1", "true", "yes"}

    if not token:
        print("MISSING: TELEGRAM_BOT_TOKEN")
        print("  1. Telegram -> @BotFather -> /newbot")
        print("  2. Set token in Railway Variables")
        print("  3. Re-run this script locally with token exported")
        return 1

    me = _validate_bot(token)
    if me is None:
        return 1

    bot = me["result"]
    username = bot.get("username", "")
    print(f"  OK — @{username} ({bot.get('first_name')})")

    vars_ = [
        ("TELEGRAM_BOT_TOKEN", token, "from @BotFather"),
        ("TELEGRAM_BOT_USERNAME", username, "auto"),
        ("TELEGRAM_FREE_ALERTS_ENABLED", "true", "3 free alerts/day"),
        ("TELEGRAM_WEBHOOK_URL", webhook_url, "production webhook"),
        ("TELEGRAM_WEBHOOK_SECRET", webhook_secret or "", "random string (recommended)"),
        ("TELEGRAM_POLLING_ENABLED", "false" if not use_polling else "true", "use webhook on Railway"),
    ]
    _print_variables(vars_)

    if use_polling:
        _configure_polling(token)
    else:
        _configure_webhook(token, webhook_url, webhook_secret)

    print("\n--- Test ---")
    print("  1. Open the bot in Telegram -> send /start")
    print("  2. Check /api/telegram/free/status on your APP_BASE_URL")
    print("  3. Check /api/gtm/status on your APP_BASE_URL")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
