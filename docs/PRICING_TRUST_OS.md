# Trust OS Pricing — Depth Ladder (Binding · Option A)

**Canon:** 1 product · 4 value layers · 6 heroes.  
**Option A (final · merged to `main`):** Proof Pass $0 · Decision Pro $29 (7-day trial) · Decision Desk $49 · Institutional From $3,000/mo → open.  
**Not:** multi-platform SKUs, Essential ($15), Observer ($9), or guaranteed accuracy.  
**Closure:** Signup plan picker + sequential upgrades shipped; no open pricing deferral for Option A.

## Story

Proof → daily decision habit → desk packaging → institutional trust room.

Competitors sell data, charts, alerts, or opaque scores. Trust OS sells a **reviewable decision + shareable proof**.

## Ladder

| Level | Name | Price | Auth tier | Role |
|-------|------|-------|-----------|------|
| 1 | Proof Pass | $0 | `free` | Viral Free: OQS Why + Decision Certificate; **3 certified decisions/day**; Free Proof watermark |
| 2 | Decision Pro | $29/mo | `pro` | Daily habit; unlimited Oracle; Portfolio AI; alerts; no watermark; **7-day trial** |
| 3 | Decision Desk | $49/mo | `whale` | Edge + serious desk tools (S/N, Stealth views, B2B/API, Evidence pack) |
| 4 | Trust OS Institutional | From $3,000/mo → **open** | sales-led | Data Room, SSO/MFA, SLA, roles, Integration Addendum — **Talk to us** |

## Signup plan picker (required)

At `/login?tab=register` the user **chooses one of the four plans** before account creation.

| Selected plan | After register |
|---------------|----------------|
| Proof Pass | Enter app on Free — **no** auto Pro trial |
| Decision Pro | Start **7-day Pro trial** → profile welcome |
| Decision Desk | Account created → redirect to Desk checkout (`tier=whale`) |
| Institutional | Account created → `/data-room` (Talk to us) |

Deep links: `/login?tab=register&plan=free|pro|whale|institutional`.

## Sequential upgrades (required)

Upgrade CTAs always point to the **next depth only**:

`Free → Pro ($29 trial/checkout) → Desk ($49) → Institutional (Talk to us)`

APIs: `GET /api/pricing/upgrade-path?tier=…` · `GET /api/pricing/signup-plans`.

## Why $29 should feel fair (value equation)

1. Free already delivers Act/Wait + Why + shareable Proof Card **before pay**.  
2. Pro removes the 3/day ceiling so the habit is not rationed.  
3. Pro removes Free Proof watermark on certificates.  
4. Pro unlocks Portfolio AI, alerts, history, Since You Left.  
5. 7-day trial lets users feel unlimited habit before charge.  
6. Framing: ~$1/day for a verified daily decision system — not a chart zoo.

**Anti-waste rules:** no charge before first Proof Card aha; no guaranteed returns; no $15 mid-tier; Institutional never fake self-serve checkout.

## Conversion levers (Free → Pro)

1. Daily ceiling (3 certified decisions)  
2. Removable **Free Proof** watermark on certificates  
3. Portfolio AI / deeper habit tools on Pro  
4. One-click upgrade when the Free ceiling is hit (next step only)  
5. Keep **7-day Pro trial** when user picks Decision Pro at signup  

## What we do not do

- No Essential / Observer / **$15** mid-tier unless Free→$29 conversion weakens later with evidence  
- Do not price the six heroes as separate products — price **depth of use**  
- Do not launch Institutional as self-serve on viral day — prestige via Talk to us  
- Do not promise guaranteed accuracy at any tier  
- Do not auto-start Pro trial on every signup (only when plan=`pro`)

## Launch success metrics (in order)

1. Proof Card shares  
2. Free → Pro trial (plan pick or upgrade)  
3. Trial → $29 paid  
4. Only then measure $49 Decision Desk conversion  

## Code surfaces

- `pricing_catalog.py` — canonical catalog, signup cards, `next_upgrade()`, value equation  
- `auth_service.register_user(plan=…)` — Option A signup branches  
- `templates/login.html` — plan picker  
- `templates/dashboard.html` / `profile.html` — sequential upgrade CTAs  
- `auth_service.TIER_FEATURES` — gates + labels  
- `billing_service.STRIPE_TIERS` — $29 / $49 self-serve **USD**  
- `payments_usd.py` + `docs/PAYMENTS_USD_SECURITY.md` — PSP architecture / PCI SAQ A  
- `decision_certificate.py` — Free Proof watermark  
- `GET /api/pricing` · `GET /api/pricing/signup-plans` · `GET /api/pricing/upgrade-path`  
- Landing `#pricing` — four-depth story · binding `docs/MORNING_SESSION_FINAL_BINDING.md`  

## Integration Addendum (Institutional)

Negotiated as a contract annex (not a pricing-page SKU): data licensing, model/API access, audit rights (glass-box methodology, not raw weights), latency/SLA, indemnity/disclaimer, custom universe, on-prem, human-in-the-loop, logo/case study.
