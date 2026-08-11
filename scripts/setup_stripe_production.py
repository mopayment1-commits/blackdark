#!/usr/bin/env python3
"""Stripe production setup — validate keys and print Railway checklist."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD_URL = os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app").rstrip("/")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _stripe_get(path: str, secret: str) -> dict | None:
    req = urllib.request.Request(
        f"https://api.stripe.com/v1{path}",
        headers={"Authorization": f"Bearer {secret}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"  Stripe API error {exc.code}: {body[:200]}")
        return None
    except Exception as exc:
        print(f"  Stripe API unreachable: {exc}")
        return None


def _print_checklist(checklist: list[tuple[str, str, str]]) -> int:
    missing = 0
    for key, val, hint in checklist:
        ok = bool(val)
        if key.startswith("STRIPE_") and key != "STRIPE_PRICE_WHALE" and not ok:
            missing += 1
        mark = "SET" if ok else "MISSING"
        print(f"  [{mark}] {key}")
        if not ok and key != "STRIPE_PRICE_WHALE":
            print(f"         -> {hint}")
    return missing


def _validate_stripe(secret: str, price_pro: str) -> None:
    if not secret.startswith(("sk_live_", "sk_test_")):
        return
    print("\n--- Validating secret key ---")
    acct = _stripe_get("/account", secret)
    if acct:
        print(f"  Account: {acct.get('settings', {}).get('dashboard', {}).get('display_name') or acct.get('id')}")
        print(f"  Livemode: {not secret.startswith('sk_test_')}")
    if price_pro:
        price = _stripe_get(f"/prices/{price_pro}", secret)
        if price:
            amt = (price.get("unit_amount") or 0) / 100
            print(f"  Pro price: ${amt:.2f} {price.get('currency', '').upper()} active={price.get('active')}")


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — Stripe Production Setup")
    print("=" * 60)
    print(f"\nProduction URL: {PROD_URL}\n")

    secret = _env("STRIPE_SECRET_KEY")
    webhook = _env("STRIPE_WEBHOOK_SECRET")
    price_pro = _env("STRIPE_PRICE_PRO")
    price_whale = _env("STRIPE_PRICE_WHALE")

    print("--- Railway Variables ---")
    checklist = [
        ("STRIPE_SECRET_KEY", secret, "sk_live_... from Stripe Dashboard"),
        ("STRIPE_PRICE_PRO", price_pro, "price_... for $29/mo Decision Pro USD"),
        ("STRIPE_PRICE_WHALE", price_whale, "price_... for $49/mo Decision Desk USD (optional)"),
        ("STRIPE_WEBHOOK_SECRET", webhook, "whsec_... endpoint POST /webhook"),
        (
            "STRIPE_SUCCESS_URL",
            _env("STRIPE_SUCCESS_URL") or f"{PROD_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "Redirect after payment",
        ),
        ("STRIPE_CANCEL_URL", _env("STRIPE_CANCEL_URL") or f"{PROD_URL}/cancel", "Checkout cancel"),
        ("APP_BASE_URL", _env("APP_BASE_URL") or PROD_URL, "Must match Railway domain"),
    ]
    missing = _print_checklist(checklist)

    print("\n--- Stripe Dashboard steps ---")
    print("  1. Products -> create 'Decision Pro' recurring $29/mo")
    print("  2. Copy Price ID -> STRIPE_PRICE_PRO")
    print("  3. Developers -> Webhooks -> Add endpoint:")
    print(f"     URL: {PROD_URL}/webhook")
    print("     Events: checkout.session.completed, customer.subscription.*, invoice.paid, invoice.payment_failed, charge.refunded")
    print("  4. Copy signing secret -> STRIPE_WEBHOOK_SECRET")
    print(f"  5. Test checkout: {PROD_URL}/create-checkout-session?tier=pro")

    _validate_stripe(secret, price_pro)

    print("\n--- After Railway deploy ---")
    print("  curl", f"{PROD_URL}/api/gtm/status")
    print("  Expect stripe.configured=true")
    print("=" * 60)
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
