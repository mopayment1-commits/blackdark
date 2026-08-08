# Trust OS Pricing — Depth Ladder (Binding)

**Canon:** 1 product · 4 value layers · 6 heroes.  
**Not:** multi-platform SKUs, Essential ($15), Observer ($9), or guaranteed accuracy.

## Story

Proof → daily decision habit → desk packaging → institutional trust room.

Competitors sell data, charts, alerts, or opaque scores. Trust OS sells a **reviewable decision + shareable proof**.

## Ladder

| Level | Name | Price | Auth tier | Role |
|-------|------|-------|-----------|------|
| 1 | Proof Pass | $0 | `free` | Viral Free: OQS Why + Decision Certificate; **3 certified decisions/day**; Free Proof watermark |
| 2 | Decision Pro | $29/mo | `pro` | Daily habit; unlimited Oracle; Portfolio AI; alerts; no watermark; **7-day trial** |
| 3 | Whale Desk | $199/mo | `whale` | Edge + light institutional packaging (S/N, Stealth views, B2B/API, Evidence pack) |
| 4 | Trust OS Institutional | From $3,000/mo → custom | sales-led | Data Room, SSO/MFA, SLA, roles, Integration Addendum — **Talk to us** |

## Conversion levers (Free → Pro)

1. Daily ceiling (3 certified decisions)
2. Removable **Free Proof** watermark on certificates
3. Portfolio AI / deeper habit tools on Pro
4. One-click upgrade when the Free ceiling is hit
5. Keep **7-day Pro trial** (button: open first certificate → trial)

## What we do not do

- No Essential / Observer mid-tier unless Free→$29 conversion weakens later
- Do not price the six heroes as separate products — price **depth of use**
- Do not launch Institutional as self-serve on viral day — prestige via Talk to us
- Do not promise guaranteed accuracy at any tier

## Launch success metrics (in order)

1. Proof Card shares  
2. Free → Pro trial  
3. Trial → $29 paid  
4. Only then measure $199 Whale Desk

## Code surfaces

- `pricing_catalog.py` — canonical catalog + Integration Addendum  
- `auth_service.TIER_FEATURES` — gates + labels  
- `billing_service.STRIPE_TIERS` — $29 / $199 self-serve  
- `decision_certificate.py` — Free Proof watermark  
- `GET /api/pricing` — public catalog JSON  
- Landing `#pricing` — four-card story  

## Integration Addendum (Institutional)

Negotiated as a contract annex (not a pricing-page SKU): data licensing, model/API access, audit rights (glass-box methodology, not raw weights), latency/SLA, indemnity/disclaimer, custom universe, on-prem, human-in-the-loop, logo/case study.
