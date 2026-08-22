#!/usr/bin/env python3
"""Billing production setup — official tiers, Stripe prices, webhook checklist."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OFFICIAL_SKUS = {
    "pro": {"name": "BLACKDARK PRO", "amount_cents": 1999},
    "elite": {"name": "BLACKDARK ELITE", "amount_cents": 4999},
    "quant": {"name": "BLACKDARK QUANT", "amount_cents": 14999},
}


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _stripe_create_prices(secret: str) -> dict[str, str]:
    import stripe

    stripe.api_key = secret
    out: dict[str, str] = {}
    for tier, spec in OFFICIAL_SKUS.items():
        product = stripe.Product.create(name=spec["name"], metadata={"tier": tier, "product": "trust_os"})
        price = stripe.Price.create(
            product=product.id,
            unit_amount=spec["amount_cents"],
            currency="usd",
            recurring={"interval": "month"},
            metadata={"tier": tier},
        )
        out[tier] = price.id
    return out


def main() -> int:
    from billing.ops_readiness import billing_ops_readiness

    print("=" * 70)
    print("BLACKDARK — Billing Production Setup (FREE/PRO/ELITE/QUANT/INSTITUTIONAL)")
    print("=" * 70)

    readiness = billing_ops_readiness()
    print("\n--- Official SKUs ---")
    for tier, row in readiness["skus"].items():
        print(f"  {row['display']:12} ${row['price_usd']:.2f}/mo  trial={row['trial_days']}d")

    print("\n--- Webhook endpoints ---")
    for k, url in readiness["webhooks"].items():
        if k.endswith("_url"):
            print(f"  {k}: {url}")

    print("\n--- Environment status ---")
    for key, ok in readiness["env"].items():
        print(f"  [{'SET' if ok else 'MISSING'}] {key}")

    secret = _env("STRIPE_SECRET_KEY")
    create = os.getenv("BILLING_CREATE_STRIPE_PRICES", "").lower() in {"1", "true", "yes"}
    if create and secret:
        print("\n--- Creating Stripe products/prices ---")
        try:
            ids = _stripe_create_prices(secret)
            print(json.dumps({f"STRIPE_PRICE_{k.upper()}": v for k, v in ids.items()}, indent=2))
            print("Copy these into Railway/environment secrets.")
        except Exception as exc:
            print(f"  Stripe create failed: {exc}")
            return 1
    elif create and not secret:
        print("\n  BILLING_CREATE_STRIPE_PRICES=true but STRIPE_SECRET_KEY missing")
        return 1

    print(f"\n--- Launch ready: {readiness['launch_ready']} ---")
    if readiness["next_steps"]:
        print("Next steps:")
        for step in readiness["next_steps"]:
            print(f"  - {step}")
    print("=" * 70)
    return 0 if readiness["launch_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
