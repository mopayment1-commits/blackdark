# Exit Strategy, DeFi Safety, Unified API — Features #156, #160, #162, #174, #176

## #156 — Exit Strategy Assistant

Recommended Exit Zone — **NOT a mandatory sell**.

```
🟡 Exit Zone: $45,000 - $48,000
Reasons: (1) historical resistance, (2) RSI > 70, (3) liquidity declining
This is a suggestion — the decision is yours.
```

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/oracle/exit-zone` | Compute exit zone |
| `POST /api/platform/oracle/exit-zone/save` | Save user-edited zone |

## #160 — DeFi Safety Layer

Passive contract risk flags — **no 100% protection guarantee**.

| Flag | Severity |
|------|----------|
| selfDestruct | critical |
| unlimited mint | critical |
| pausable | high |
| proxy upgrade | high |

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/defi/contract-safety` | Scan contract |
| `GET /api/v1/platform/contract-safety` | Unified API |

## #162 — Unified API Platform (v1)

8 core endpoints with consistent schema + freshness metadata.

| Endpoint | Metric |
|----------|--------|
| `/api/v1/platform/price` | price |
| `/api/v1/platform/oracle` | oracle |
| `/api/v1/platform/sentiment` | sentiment |
| `/api/v1/platform/liquidity` | liquidity |
| `/api/v1/platform/events` | events |
| `/api/v1/platform/exit-zone` | exit_zone |
| `/api/v1/platform/contract-safety` | contract_safety |

## #174 + #176 — Spreadsheet Integration

```
=BLACKDARK("BTC", "price")
=BLACKDARK("ETH", "sentiment")
=BLACKDARK("BTC", "exit_zone_low")
```

Errors: `#ERROR: Rate limit` | `#N/A: Invalid symbol`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/platform/sheets/BLACKDARK` | Cell value for sheets |
