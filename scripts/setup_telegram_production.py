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
from _secret_io import is_secret_env_key

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


def _display_val(key: str, val: str, hint: str) -> str:
    """Never return secret material — CodeQL treats masked secrets as clear-text sinks."""
    if is_secret_env_key(key):
        return "<set>" if val else f"<missing — {hint}>"
    if not val:
        return hint
    return val


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

    print("--- Validating bot token ---")
    try:
        me = _tg("getMe", token)
    except urllib.error.HTTPError as exc:
        print(f"  Invalid token (HTTP {exc.code})")
        return 1
    except Exception:
        print("  Telegram unreachable")
        return 1

    if not me.get("ok"):
        print("  Error: bot validation failed")
        return 1

    bot = me["result"]
    username = bot.get("username", "")
    print(f"  OK — @{username} ({bot.get('first_name')})")

    print("\n--- Railway Variables (secrets masked) ---")
    vars_ = [
        ("TELEGRAM_BOT_TOKEN", token, "from @BotFather"),
        ("TELEGRAM_BOT_USERNAME", username, "auto"),
        ("TELEGRAM_FREE_ALERTS_ENABLED", "true", "3 free alerts/day"),
        ("TELEGRAM_WEBHOOK_URL", webhook_url, "production webhook"),
        ("TELEGRAM_WEBHOOK_SECRET", webhook_secret or "", "random string (recommended)"),
        ("TELEGRAM_POLLING_ENABLED", "false" if not use_polling else "true", "use webhook on Railway"),
    ]
    for key, val, hint in vars_:
        # Keep secret values out of the print call entirely (CodeQL taint).
        if is_secret_env_key(key):
            print(f"  {key}=<set>" if val else f"  {key}=<missing — {hint}>")
        else:
            print(f"  {key}={val or hint}")

    if use_polling:
        print("\n--- Mode: long polling (dev/single-instance) ---")
        print("  Set TELEGRAM_POLLING_ENABLED=true on Railway")
        print("  Do NOT set webhook when using polling")
        try:
            _tg("deleteWebhook", token, {"drop_pending_updates": False})
            print("  Cleared any existing webhook.")
        except Exception:
            pass
    else:
        print("\n--- Setting webhook (recommended for Railway) ---")
        payload: dict = {"url": webhook_url, "allowed_updates": ["message", "edited_message"]}
        if webhook_secret:
            payload["secret_token"] = webhook_secret
        try:
            wh = _tg("setWebhook", token, payload)
            if wh.get("ok"):
                print(f"  Webhook set: {webhook_url}")
            else:
                print("  setWebhook failed — check bot token and webhook URL")
        except Exception:
            print("  Could not set webhook (run from machine with network)")
            print("  Manual: use BotFather/API with token from your secret store (do not paste tokens into logs)")

    print("\n--- Test ---")
    print(f"  1. Open https://t.me/{username} -> send /start")
    print(f"  2. Check {PROD_URL}/api/telegram/free/status")
    print(f"  3. GTM status: {PROD_URL}/api/gtm/status")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
