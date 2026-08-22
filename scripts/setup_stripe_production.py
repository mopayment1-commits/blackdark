#!/usr/bin/env python3
"""Stripe production setup — validate keys and print Railway checklist (no secret values)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD_URL = os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app").rstrip("/")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _is_set(name: str) -> bool:
    return bool(_env(name))


def _stripe_get(path: str, secret: str) -> dict | None:
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
        print(f"  Stripe API error HTTP {exc.code}")
        return None
    except Exception:
        print("  Stripe API unreachable")
        return None


def main() -> int:
    from billing.ops_readiness import billing_ops_readiness

    print("=" * 60)
    print("BLACKDARK — Stripe Production Setup")
    print("=" * 60)
    print(f"\nProduction URL: {PROD_URL}\n")

    readiness = billing_ops_readiness(base_url=PROD_URL)
    print("--- Official prices ---")
    for tier, row in readiness["skus"].items():
        print(f"  {row['display']:8} ${row['price_usd']:.2f}/mo")

    print("\n--- Railway Variables ---")
    missing = 0
    for key, ok in readiness["env"].items():
        print(f"  [{'SET' if ok else 'MISSING'}] {key}")
        if key.startswith("STRIPE_") and not ok and key not in {"STRIPE_SUCCESS_URL", "STRIPE_CANCEL_URL"}:
            missing += 1

    print("\n--- Stripe Dashboard steps ---")
    print("  1. Products -> PRO $19.99 / ELITE $49.99 / QUANT $149.99 monthly USD")
    print("  2. Copy Price IDs -> STRIPE_PRICE_PRO / ELITE / QUANT")
    print("     (legacy STRIPE_PRICE_WHALE aliases to ELITE)")
    print("  3. Developers -> Webhooks -> POST", f"{PROD_URL}/webhook")
    print("     Events: checkout.session.completed, customer.subscription.*,")
    print("             invoice.paid, invoice.payment_failed, charge.refunded, charge.dispute.created")
    print("  4. Or run: BILLING_CREATE_STRIPE_PRICES=true python3 scripts/setup_billing_production.py")

    secret = _env("STRIPE_SECRET_KEY")
    if secret:
        print("\n--- Validating secret key ---")
        is_live = secret.startswith("sk_live_")
        print(f"  Livemode: {'yes' if is_live else 'no'}")
        acct = _stripe_get("/account", secret)
        if acct:
            dash = (acct.get("settings") or {}).get("dashboard") or {}
            print(f"  Account: {dash.get('display_name') or acct.get('id') or 'ok'}")
        for tier, env_name in (("pro", "STRIPE_PRICE_PRO"), ("elite", "STRIPE_PRICE_ELITE"), ("quant", "STRIPE_PRICE_QUANT")):
            pid = _env(env_name) or (_env("STRIPE_PRICE_WHALE") if tier == "elite" else "")
            if pid:
                price = _stripe_get(f"/prices/{pid}", secret)
                if price:
                    amt = (price.get("unit_amount") or 0) / 100
                    print(f"  {tier} price: ${amt:.2f} active={bool(price.get('active'))}")

    print(f"\n--- Launch ready: {readiness['launch_ready']} ---")
    print("=" * 60)
    return 0 if readiness["launch_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
