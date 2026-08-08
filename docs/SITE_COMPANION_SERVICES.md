# BLACKDARK — Site companion services (trust rail)

Binding catalog for the **trust rail around Trust OS** — not a second product.

## Canon

- **1 product · 4 lenses · 6 heroes**
- **Share** = Proof Cards / Ledger snapshots (user content)
- **Follow us** = brand social profiles (footer / About / Contact) — never hero clutter
- **Phone** = institutional / optional (`INSTITUTIONAL_PHONE`) — not viral-launch hero auth
- **AI Chat** = Operate+ (Decision Pro / Whale Desk) on `/dashboard#ai-chat`

## Surfaces (HTML)

| Path | Purpose |
|------|---------|
| `/legal` | Legal hub (fixes prior 404 from footer links) |
| `/cookies` | Cookies & local storage policy |
| `/faq` | FAQ |
| `/how-it-works` | Decide → Prove → Verify |
| `/about` | About + Follow us |
| `/status` | Public status (no secrets) |
| `/changelog` | Product changelog |
| `/feedback` | Suggestions form |
| `/contact` | Support / sales / WhatsApp when configured |
| `/complaints` | Escalations |

## APIs

- `GET /api/site-services` — full manifest
- `GET /api/status` — public status JSON
- `GET /api/faq` · `GET /api/changelog`
- `POST /api/feedback` — store + email outbox
- `POST /api/chat` — existing; gated by `ai_chat` feature

## Env

```
BRAND_SOCIAL_X=
BRAND_SOCIAL_TELEGRAM=
BRAND_SOCIAL_LINKEDIN=
SUPPORT_EMAIL=support@blackdark.app
COMPLAINTS_EMAIL=complaints@blackdark.app
SALES_EMAIL=sales@blackdark.io
WHATSAPP_BUSINESS_E164=          # digits only, e.g. 15551234567
INSTITUTIONAL_PHONE=             # Room only — optional
```

## Footer

Unified partial: `templates/partials/site_footer.html` — wired on landing, dashboard, utility, legal.

## Honesty

- Not financial advice; AI Chat does not guarantee outcomes
- Status page is engineering posture, not a contractual SLA unless contracted
- Never ask for card PAN/CVV in contact/feedback
