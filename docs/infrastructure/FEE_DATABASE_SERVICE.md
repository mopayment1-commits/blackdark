# Fee Database Internal Service — Feature #130 (Sprint 1)

## Role

**Internal service** — NOT a standalone user-facing feature. The fee database is the core engine behind every profit/cost surface on the platform.

## Coverage

| Fee Type | Source |
|----------|--------|
| Trading (maker/taker) | `fee_matrix.py` + CCXT refresh |
| Withdrawal per asset | Seeded + CCXT |
| Deposit | Seeded matrix |
| Hidden spread | Order-book bid/ask or default 5 bps |

## APIs (internal / ops)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/fees/status` | Service health |
| `GET /api/platform/infra/fees/lookup?exchange_id=binance` | Fee matrix row |
| `GET /api/platform/infra/fees/transaction-cost?exchange_id=binance&notional_usd=1000` | Full cost breakdown |

## Display Format

```
Transaction cost: $2.50 (fees) + $1.20 (spread) = $3.70
```

Arabic:
```
تكلفة هذه الصفقة: $2.50 (رسوم) + $1.20 (spread) = $3.70
```

## Integration

Embed `calculate_transaction_cost()` anywhere profit or cost is shown:
- Arbitrage net profit
- Transfer optimizer
- Portfolio analytics
- Trade simulator

## Acceptance

- Accuracy ≥ 99% for known venues
- Real-time spread when order book available
- `user_facing: false` on all responses
