#!/usr/bin/env python3
"""USD payments readiness checklist — official FREE/PRO/ELITE/QUANT tiers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from billing.ops_readiness import billing_ops_readiness

    readiness = billing_ops_readiness()
    print("=" * 60)
    print("BLACKDARK — USD Payments Setup")
    print("=" * 60)
    print("\nCurrency: USD | PCI: SAQ_A | Stores PAN: false")
    print("\n--- Official self-serve SKUs ---")
    for tier, row in readiness["skus"].items():
        print(f"  {row['display']:8} ${row['price_usd']:.2f}/mo  trial={row['trial_days']}d")

    print("\n--- Environment ---")
    for key, ok in readiness["env"].items():
        print(f"  [{'SET' if ok else 'MISSING'}] {key}")

    print("\n--- Webhooks ---")
    print(f"  Stripe: {readiness['webhooks']['stripe_url']}")
    print(f"  Lemon:  {readiness['webhooks']['lemon_url']}")

    print(f"\n--- Launch ready: {readiness['launch_ready']} ---")
    print("  Run: python3 scripts/setup_billing_production.py")
    print("  API: GET /api/billing/readiness")
    print("=" * 60)
    return 0 if readiness["launch_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
