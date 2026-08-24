# Network Used Widget — Feature #120 (Sprint 2)

## Purpose

Embedded micro-widget on every **transfer**, **deposit**, and **withdraw** surface — not a standalone page.

Integrated with **#108** (best transfer networks) in the same UI.

## Example

> Available networks: ERC20 ($5 gas), TRC20 ($0.5 gas), BEP20 ($0.1 gas). Cheapest: BEP20.

Arabic: الشبكات المتاحة: ERC20 ($5 gas)، TRC20 ($0.5 gas)، BEP20 ($0.1 gas). الأرخص: BEP20.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/transfer/widget` | Embedded widget payload |
| `GET /api/platform/transfer/networks` | Full ranking (#108) |
| `GET/POST /api/platform/transfer/network-prefs` | User saved network (#120) |

### Query params (`/transfer/widget`)

- `asset` — USDT, USDC, ETH, BTC
- `amount_usd` — transfer size for fee scoring
- `surface` — `transfer` | `deposit` | `withdraw`
- `user_id` — optional saved preference overlay

## Acceptance

- Response ≤ 2 seconds
- Accuracy ≥ 95% (live gas oracle + static fallback)
- Widget embeddable — no separate page required
