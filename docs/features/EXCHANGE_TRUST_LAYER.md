# Exchange Trust Layer — Features #132 + #134 (Sprint 2)

## Role

Post-FTX trust differentiator. Unified dashboard for exchange quality (#132) and platform status (#134).

## #132 — Exchange Quality Score

### Criteria (transparent, reviewable)

| Criterion | Weight | Source |
|-----------|--------|--------|
| Proof of Reserves | 25% | `dimensions.por` + on-chain attestations |
| Withdrawal history | 25% | `dimensions.withdrawal` + closure history (#123) |
| Regulatory status | 20% | `dimensions.regulatory` |
| Insurance fund | 15% | `trust_score` + `security_history` |
| Volume/liquidity ratio | 15% | `liquidity` + `wash_trading_risk` |

### Grade Scale

A+ (90+) · A (85+) · B+ (80+) · B (75+) · C (60+) · D (<60)

### Badge Examples

- 🟢 A+ — Reserves Verified
- 🔴 D — Withdrawals Suspended 3x

## #134 — Exchange Platform Status

Real-time + historical:

| Field | Values |
|-------|--------|
| `api_status` | up / degraded / down |
| `withdrawal_status` | open / partial / closed |
| `deposit_status` | open / partial / closed |
| `trading_status` | active / suspended |

Historical: "Binance: withdrawals suspended 2x in last 6 months"

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/exchange-trust/dashboard` | Unified #132 + #134 |
| `GET /api/platform/exchange-trust/quality` | Quality scores only |
| `GET /api/platform/exchange-health/status` | #110 alerts + #134 status |

## Acceptance

- Response ≤ 2 seconds
- Accuracy ≥ 95%
- Methodology transparent and reviewable
