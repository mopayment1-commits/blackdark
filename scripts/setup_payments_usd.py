#!/usr/bin/env python3
"""USD payments readiness checklist — Lemon + Stripe (no secrets printed)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _set(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def main() -> int:
    print("=" * 60)
    print("BLACKDARK — USD Payments Setup")
    print("=" * 60)

    from payments_usd import BILLING_CURRENCY_DISPLAY, SELF_SERVE_SKUS, payments_architecture

    arch = payments_architecture()
    print(f"\nCurrency: {BILLING_CURRENCY_DISPLAY}")
    print(f"Active provider: {arch.get('active_provider')}")
    sec = arch.get("security") or {}
    print(f"PCI target: {sec.get('pci_target')}")
    print(f"Stores PAN: {sec.get('stores_pan')}")

    print("\n--- Self-serve SKUs ---")
    for sku, info in SELF_SERVE_SKUS.items():
        print(f"  {info['name']}: ${info['amount_usd']}/mo USD (tier={sku})")

    checks = [
        ("LEMON_SQUEEZY_CHECKOUT_PRO", _set("LEMON_SQUEEZY_CHECKOUT_PRO"), "Decision Pro $29 checkout URL"),
        ("LEMON_SQUEEZY_CHECKOUT_WHALE", _set("LEMON_SQUEEZY_CHECKOUT_WHALE"), "Whale Desk $199 checkout URL"),
        ("LEMON_SQUEEZY_WEBHOOK_SECRET", _set("LEMON_SQUEEZY_WEBHOOK_SECRET"), "POST /webhook/lemon"),
        ("LEMON_SQUEEZY_CUSTOMER_PORTAL_URL", _set("LEMON_SQUEEZY_CUSTOMER_PORTAL_URL"), "optional portal"),
        ("STRIPE_SECRET_KEY", _set("STRIPE_SECRET_KEY"), "optional if Lemon complete"),
        ("STRIPE_WEBHOOK_SECRET", _set("STRIPE_WEBHOOK_SECRET"), "POST /webhook"),
        ("STRIPE_PRICE_PRO", _set("STRIPE_PRICE_PRO"), "USD price id $29"),
        ("STRIPE_PRICE_WHALE", _set("STRIPE_PRICE_WHALE"), "USD price id $199"),
        ("APP_BASE_URL", _set("APP_BASE_URL"), "public HTTPS origin"),
    ]
    print("\n--- Environment ---")
    for key, ok, hint in checks:
        print(f"  [{'SET' if ok else 'MISSING'}] {key} — {hint}")

    ready = arch["ops_readiness"]["launch_ready"]
    whale = arch["ops_readiness"]["whale_ready"]
    print("\n--- Readiness ---")
    print(f"  Launch (Pro path + webhook): {'READY' if ready else 'BLOCKED'}")
    print(f"  Whale Desk checkout: {'READY' if whale else 'MISSING — set Lemon Whale or Stripe price'}")
    print("\n--- Bank payout ---")
    print("  Complete PSP KYC and attach your USD bank account in Lemon/Stripe dashboard.")
    print("  Customers never send card data to BLACKDARK servers.")
    print("\n--- Verify ---")
    base = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
    print(f"  GET  {base}/api/billing/payments")
    print(f"  GET  {base}/api/billing/refund-policy")
    print(f"  POST {base}/api/billing/checkout  {{\"tier\":\"pro\"}}")
    print("  Docs: docs/PAYMENTS_USD_SECURITY.md")
    print("=" * 60)
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
