# Price Spread Calculator — Feature #136 (Internal Function)

## Role

**Internal function** — NOT a standalone user-facing feature.

Centralizes gross → net spread math so gross-only numbers are never shown alone.

## Consumers

| Consumer | Usage |
|----------|-------|
| **#112** Arbitrage Scanner | Net spread after fees |
| **#155** Market Radar | Sample spread in narrative |
| **#119** Transfer Optimizer | Transfer cost as % of amount |

## Integrations

- **#130** Fee Database — trading + transfer fees
- **#113** Net profit algorithms — `profit_fee_algorithms.py`

## Display Format

```
Spread: 2.3% → after fees: 0.8% → not profitable
```

Arabic:
```
الفرق: 2.3% → بعد الرسوم: 0.8% → غير مربح
```

When gross is positive but net is negative, `gross_only_misleading: true`.

## API (internal / ops)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/spread/status` | Health |
| `GET /api/platform/infra/spread/calculate?buy_price=100&sell_price=102.3` | Calculate spread |

## Acceptance

- Response ≤ 2 seconds
- Always includes net after fees
- Accuracy ≥ 95%
