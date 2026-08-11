#!/usr/bin/env python3
"""Configure Stripe keys for local/production — secrets never printed or written to .env."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
SECRET_FILE = ROOT / "keys" / "stripe.secrets.env"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _secret_io import write_private_text  # noqa: E402


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
    print("Secret values are written only to a private file (mode 0600).")
    print("They are never printed and never stored in .env.\n")

    sk = input("STRIPE_SECRET_KEY (sk_live_ or sk_test_): ").strip()
    wh = input("STRIPE_WEBHOOK_SECRET (whsec_): ").strip()
    pro = input("STRIPE_PRICE_PRO (price_..., optional): ").strip()
    whale = input("STRIPE_PRICE_WHALE (price_..., optional): ").strip()
    base = input("APP_BASE_URL (e.g. https://blackdark.up.railway.app): ").strip() or "http://127.0.0.1:8080"
    base = base.rstrip("/")

    if not sk.startswith("sk_"):
        print("Invalid secret key prefix")
        raise SystemExit(1)

    # Private secret material only (never stdout, never .env).
    secret_block = "\n".join(
        [
            f"STRIPE_SECRET_KEY={sk}",
            f"STRIPE_WEBHOOK_SECRET={wh}",
            "",
        ]
    )
    write_private_text(SECRET_FILE, secret_block)

    # Non-secret operational URLs / price ids may live in .env.
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    # Remove any legacy clear-text secret lines from .env.
    lines = [
        ln
        for ln in lines
        if not ln.startswith("STRIPE_SECRET_KEY=") and not ln.startswith("STRIPE_WEBHOOK_SECRET=")
    ]
    for key, val in [
        ("APP_BASE_URL", base),
        ("STRIPE_SUCCESS_URL", f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}"),
        ("STRIPE_CANCEL_URL", f"{base}/cancel"),
        ("STRIPE_SECRETS_FILE", str(SECRET_FILE.relative_to(ROOT)).replace("\\", "/")),
    ]:
        lines = _upsert(lines, key, val)
    if pro:
        lines = _upsert(lines, "STRIPE_PRICE_PRO", pro)
    if whale:
        lines = _upsert(lines, "STRIPE_PRICE_WHALE", whale)

    ENV.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"\nWrote private secrets file: {SECRET_FILE.relative_to(ROOT)} (mode 0600)")
    print(f"Updated non-secret keys in {ENV.name}")
    print("Load STRIPE_* from the private file into the process env before start")
    print("(e.g. `set -a; . keys/stripe.secrets.env; set +a`), then restart.")
    print("Restart server, then test: /login → Upgrade Pro")


if __name__ == "__main__":
    main()
