#!/usr/bin/env python3
"""Stripe production setup — validate keys and print Railway checklist (no secret values)."""
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


def _is_set(name: str) -> bool:
    return bool(_env(name))


def _stripe_get(path: str, secret: str) -> dict | None:
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from path_safety import open_http_url

    try:
        with open_http_url(
            f"https://api.stripe.com/v1{path}",
            timeout=20,
            headers={"Authorization": f"Bearer {secret}"},
            allowed_hosts={"api.stripe.com"},
        ) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        # Never print response bodies (may include account/secret-adjacent payloads).
        print(f"  Stripe API error HTTP {exc.code}")
        return None
    except Exception:
        print("  Stripe API unreachable")
        return None


def _print_checklist(keys: list[tuple[str, bool, str]]) -> int:
    missing = 0
    for key, ok, hint in keys:
        if key.startswith("STRIPE_") and key != "STRIPE_PRICE_WHALE" and not ok:
            missing += 1
        mark = "SET" if ok else "MISSING"
        print(f"  [{mark}] {key}")
        if not ok and key != "STRIPE_PRICE_WHALE":
            print(f"         -> {hint}")
    return missing


def _validate_stripe() -> None:
    secret = _env("STRIPE_SECRET_KEY")
    price_pro = _env("STRIPE_PRICE_PRO")
    if not secret:
        return
    # Derive livemode WITHOUT embedding the secret variable in a print expression.
    is_test = secret.startswith("sk_test_")
    is_live = secret.startswith("sk_live_")
    live_label = "yes" if is_live else "no"
    print("\n--- Validating secret key ---")
    if not (is_test or is_live):
        print("  Invalid STRIPE_SECRET_KEY prefix (expected sk_live_ or sk_test_)")
        return
    print(f"  Livemode: {live_label}")
    acct = _stripe_get("/account", secret)
    if acct:
        dash = (acct.get("settings") or {}).get("dashboard") or {}
        name = dash.get("display_name") or acct.get("id") or "ok"
        # Account display name / id only — never dump the full account object.
        print(f"  Account: {name}")
    if price_pro:
        price = _stripe_get(f"/prices/{price_pro}", secret)
        if price:
            amt = (price.get("unit_amount") or 0) / 100
            cur = str(price.get("currency") or "").upper()
            active = bool(price.get("active"))
            print(f"  Pro price: ${amt:.2f} {cur} active={active}")


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — Stripe Production Setup")
    print("=" * 60)
    print(f"\nProduction URL: {PROD_URL}\n")

    print("--- Railway Variables ---")
    checklist = [
        ("STRIPE_SECRET_KEY", _is_set("STRIPE_SECRET_KEY"), "sk_live_... from Stripe Dashboard"),
        ("STRIPE_PRICE_PRO", _is_set("STRIPE_PRICE_PRO"), "price_... for $29/mo Decision Pro USD"),
        ("STRIPE_PRICE_WHALE", _is_set("STRIPE_PRICE_WHALE"), "price_... for $49/mo Decision Desk USD (optional)"),
        ("STRIPE_WEBHOOK_SECRET", _is_set("STRIPE_WEBHOOK_SECRET"), "whsec_... endpoint POST /webhook"),
        ("STRIPE_SUCCESS_URL", _is_set("STRIPE_SUCCESS_URL"), "Redirect after payment"),
        ("STRIPE_CANCEL_URL", _is_set("STRIPE_CANCEL_URL"), "Checkout cancel"),
        ("APP_BASE_URL", _is_set("APP_BASE_URL"), "Must match Railway domain"),
    ]
    missing = _print_checklist(checklist)

    print("\n--- Stripe Dashboard steps ---")
    print("  1. Products -> create 'Decision Pro' recurring $29/mo")
    print("  2. Copy Price ID -> STRIPE_PRICE_PRO")
    print("  3. Developers -> Webhooks -> Add endpoint:")
    print(f"     URL: {PROD_URL}/webhook")
    print(
        "     Events: checkout.session.completed, customer.subscription.*, "
        "invoice.paid, invoice.payment_failed, charge.refunded"
    )
    print("  4. Copy signing secret -> STRIPE_WEBHOOK_SECRET")
    print(f"  5. Test checkout: {PROD_URL}/create-checkout-session?tier=pro")

    _validate_stripe()

    print("\n--- After Railway deploy ---")
    print("  curl", f"{PROD_URL}/api/gtm/status")
    print("  Expect stripe.configured=true")
    print("=" * 60)
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
