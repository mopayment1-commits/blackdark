# Commercial Security Features (Launch-57)

**CISA Secure by Demand alignment note:** This document states how security capabilities map to pricing.

| Capability | Baseline (self-serve tiers) | Institutional |
|------------|----------------------------|---------------|
| User TOTP MFA | Included | Included |
| Enterprise OIDC SSO | — | **Included in platform agreement** (not sold as a separate “SSO add-on” line item) |
| Customer security log export (180d) | Included | Included |
| Dedicated SLA / custom contract | — | Negotiated (platform fee may start at published `From $999/mo` — **not** an SSO-specific surcharge) |

Institutional `price_usd_month_from` in `billing/plan_registry.py` reflects **platform** pricing, not an incremental fee for standards-based SSO alone.
