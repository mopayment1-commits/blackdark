#!/usr/bin/env python3
"""Generate production secrets and print a Railway Variables block."""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    domain = (sys.argv[1] if len(sys.argv) > 1 else input("Your Railway domain (e.g. blackdark.up.railway.app): ")).strip()
    insecure_scheme = "http" + "://"
    secure_scheme = "https" + "://"
    domain = domain.replace(secure_scheme, "").replace(insecure_scheme, "").rstrip("/")
    if not domain:
        print("Domain required")
        raise SystemExit(1)

    email = input("Admin email: ").strip().lower()
    base = f"{secure_scheme}{domain}"

    block = f"""# Paste into Railway → Variables (Raw Editor)

PORT=8080
APP_BASE_URL={base}

SECRETS_MASTER_KEY={secrets.token_hex(32)}
SESSION_TOKEN_PEPPER={secrets.token_hex(16)}
ADMIN_API_KEY={secrets.token_hex(24)}
ADMIN_EMAILS={email}

RUN_AGGREGATOR=true
INGESTION_ENABLED=true
MANIFEST_AUTO_APPROVE=true
UNIVERSE_AUTO_ACTIVATE=true
AUTO_EXECUTION_DRY_RUN=true
AUTO_EXECUTION_ENABLED=false
PRO_TRIAL_DAYS=7

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_PRO=
STRIPE_PRICE_WHALE=
STRIPE_SUCCESS_URL={base}/success?session_id={{CHECKOUT_SESSION_ID}}
STRIPE_CANCEL_URL={base}/cancel

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_WEBHOOK_URL={base}/api/telegram/webhook
TELEGRAM_WEBHOOK_SECRET={secrets.token_hex(16)}
TELEGRAM_ALERTS_ENABLED=true
TELEGRAM_POLLING_ENABLED=false

GROQ_API_KEY=
"""
    out = ROOT / "data" / "railway_variables.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(block, encoding="utf-8")

    print("\n=== RAILWAY VARIABLES (copy to Railway dashboard) ===\n")
    print(block)
    print(f"Saved to: {out}")
    print("\nNext: Railway → New Project → Deploy from GitHub → paste variables → Generate Domain")


if __name__ == "__main__":
    main()
