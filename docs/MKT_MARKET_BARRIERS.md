# BLACKDARK — Market Barriers & Moat (MKT-005)

## Regulatory barrier (soft moat)

- Oracle outputs use **analytics labels** (e.g. `BULLISH_ANALYTICS`) — not “Buy Now” advice
- `regulatory_compliance_guard` + `security_sanitize` strip internal verdict leaks before API response
- GDPR DSR API (`/api/privacy/export`, `/api/privacy/erase`) — DD-ready data subject rights
- **Barrier for copycats:** naive “AI says buy” products face app-store / advertising takedowns faster

## Data moat (building)

| Asset | Status | Barrier strength |
|-------|--------|------------------|
| Labeled oracle predictions | Growing via `oracle_predictions` + resolve pipeline | Medium — needs 50+ live labels |
| Behavior events | `behavior_events` table, 90d funnel | Medium — needs volume |
| Model weights / retrain | `model_weights.json`, flywheel scheduler | Low until proprietary edge proven |
| Uptime + audit chain | `uptime_probes.jsonl`, `oracle_audit_chain.jsonl` | Operational trust signal |

## Technical barrier

- Multi-source ingestion (CEX WS, sentiment, on-chain hooks) wired into unified Oracle engine
- Fallback stack on Railway (`PRICE_FEED_WS_ONLY=false`) — production already live
- Stripe + Telegram + auth integrated — not a weekend clone of “GPT wrapper”

## Distribution barrier

- **Telegram bot** with free tier creates daily touchpoint competitors lack at $0 CAC
- Shareable Oracle cards (X, WhatsApp, Telegram) — viral loop on landing
- Promo `LAUNCHPRO` + 7-day Stripe trial lowers conversion friction

## Trust barrier (honest gaps)

- **No paid subscribers yet** — primary GTM blocker (MKT-006 FAIL until fixed)
- No public third-party accuracy audit — mitigate with `/oracle-accuracy` transparency
- Brand new domain — mitigate with live uptime monitor + open DD technical report

## 90-day moat milestones

1. 10 paid Pro → proves willingness to pay
2. 50 resolved oracle labels → retrains proprietary weights
3. 1,000 behavior events → funnel optimization data
4. Documented competitive matrix + ICP (this folder) → acquirer DD ready
