# BLACKDARK — Trust Pulse (Daily Decision Pulse)

Binding first-open surface for Trust OS.

## What it is

**One live Act / Wait decision + Why (<5s) + Verified-on-Ledger proof + freshness.**

Not a news digest. Not top movers. Not a smart-money feed clone.

## Surfaces

| Surface | Path |
|---------|------|
| Dashboard first viewport | `/dashboard#trust-pulse` |
| Landing mini pulse | `/#trust-pulse` |
| JSON | `GET /api/trust-pulse` |
| SSE live | `GET /api/trust-pulse/stream` |
| Manifest | `GET /api/trust-pulse/manifest` |

## Realtime rules

- Heartbeat every ~20s (freshness / still-live)
- `decision_changed` only when action flips
- Soft cache ~45s — stream does **not** spam `prediction_id`
- Stale after ~120s without refresh — UI must say **Stale**, never fake live

## Tiers

- **Proof Pass (Free):** decision + Why + Free Proof watermark + share Proof Card + ledger chip
- **Decision Pro+:** continuity “since your last visit” + flip detail + no watermark

## Honesty

- Not financial advice; AI cannot guarantee returns
- Ledger chip shows hits **and** misses
- Share = Proof Card only (never holdings / API keys)

## Competitive wedge

TradingView / CMC / Nansen open to charts, movers, or labeled wallets.  
BLACKDARK opens to a **reviewable decision with public proof**.
