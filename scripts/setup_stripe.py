#!/usr/bin/env python3
"""Configure Stripe keys in .env for local or production."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from path_safety import resolve_under

ENV = ROOT / ".env"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _upsert(lines: list[str], key: str, value: str) -> list[str]:
    prefix = key + "="
    out = [ln for ln in lines if not ln.startswith(prefix)]
    out.append(f"{prefix}{value}")
    return out


def main() -> None:
    print("BLACKDARK — Stripe Setup\n")
    print("Get keys from: https://dashboard.stripe.com/apikeys")
    print("Webhook: Dashboard → Developers → Webhooks → Add endpoint")
    print("  URL: https://YOUR-DOMAIN/webhook")
    print("  Event: checkout.session.completed\n")

    sk = input("STRIPE_SECRET_KEY (sk_live_ or sk_test_): ").strip()
    wh = input("STRIPE_WEBHOOK_SECRET (whsec_): ").strip()
    pro = input("STRIPE_PRICE_PRO (price_..., optional): ").strip()
    whale = input("STRIPE_PRICE_WHALE (price_..., optional): ").strip()
    base = input("APP_BASE_URL (e.g. https://blackdark.up.railway.app): ").strip() or "http://127.0.0.1:8080"
    base = base.rstrip("/")

    if not sk.startswith("sk_"):
        print("Invalid secret key")
        raise SystemExit(1)

    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    for key, val in [
        ("STRIPE_SECRET_KEY", sk),
        ("STRIPE_WEBHOOK_SECRET", wh),
        ("APP_BASE_URL", base),
        ("STRIPE_SUCCESS_URL", f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}"),
        ("STRIPE_CANCEL_URL", f"{base}/cancel"),
    ]:
        lines = _upsert(lines, key, val)
    if pro:
        lines = _upsert(lines, "STRIPE_PRICE_PRO", pro)
    if whale:
        lines = _upsert(lines, "STRIPE_PRICE_WHALE", whale)

    env_path = resolve_under(ROOT, ".env")
    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"\nSaved to {env_path}")
    print("Restart server, then test: /login → Upgrade Pro")


if __name__ == "__main__":
    main()
