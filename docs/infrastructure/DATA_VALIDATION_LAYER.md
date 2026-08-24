# Data Validation Layer — Feature #147 (Sprint 0)

## Role

**Internal protection** — NOT a user-facing feature. Integrated with #133 price aggregation.

Automatic pipeline:
1. Detect outlier >5% from weighted reference
2. Flag event
3. Select fallback source
4. Log to `data/data_validation_events.jsonl`

## User Surface

Only badge when verified:
```
✓ Price Verified
```

No "sniping glitches" marketing — this is infrastructure protection.

## API (ops)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/validation/status` | Layer health |

Validation runs automatically inside `aggregate_prices()` (#133).

## Acceptance

- Response ≤ 2 seconds
- Accuracy ≥ 95%
- Fallback when outlier detected
- Events logged for audit
