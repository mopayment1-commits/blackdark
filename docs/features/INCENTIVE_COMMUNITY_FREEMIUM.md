# Incentive Tracker & Community Freemium — #203, #205

## #203 — Incentive Tracker Module (Sprint 2)

Tracks airdrop and incentive programs — **not** displayed as opportunities.

| Rule | Implementation |
|------|----------------|
| Source/status | `Source: Protocol Docs \| Status: Active/Ended/Upcoming` |
| Format | `Incentive Program: X \| APY: Y% \| Risk: Z/10` |
| Fee DB (#130) | `fee_context` on every program |
| Disclaimer | Non-hideable: "Incentives subject to change. Impermanent loss possible." |
| Timeline | `Start: YYYY-MM-DD \| End: YYYY-MM-DD \| Cliff: N days` |
| Coverage | ≥50 protocols in seed data |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/incentives` | List programs (filter by status/protocol/chain) |
| `GET /api/platform/incentives/{id}` | Program detail |
| `GET /api/platform/incentives/status` | Module status |

---

## #205 — Community Freemium Layer (merged #162)

**Not standalone** — freemium tier on Unified API.

| Limit | Value |
|-------|-------|
| Daily calls | 100 |
| Assets | BTC, ETH, SOL, BNB, XRP |
| Resolution | 1D only |
| Watermark | Powered by BLACKDARK |
| Upsell | Upgrade for real-time + sub-second |

### APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/platform/community/status` | Tier limits |
| `GET /api/v1/platform/community/chart?asset=BTC` | Chart + watermark |
| `GET /api/v1/platform/community/oracle?asset=BTC` | Oracle (same engine) |

Same chart/oracle engine as Pro — limits only, no separate charts engine.
