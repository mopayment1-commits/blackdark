# Feature #72 — MVRV Z-Score (Cycle Regime)

Internal on-chain cycle metric — **not a standalone product**. Feeds Decision Engine (#48).

## Formula

```
Z-Score = (Market Cap proxy - Realized Cap proxy) / StdDev
```

Realized cap proxied via SMA200 from price history (Glassnode-grade on-chain = external evidence).

## Cycle zones

| Zone | Z-Score |
|------|---------|
| Undervalued | < -0.5 |
| Fair Value | -0.5 to 3.5 |
| Overvalued | 3.5 to 7.0 |
| Bubble | > 7.0 |

## Example headline

> Market Regime: Late Bull (BTC MVRV Z-Score: 4.2 — historically 85% top probability within 60 days)

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/onchain/mvrv-realignment` | Full MVRV + realignment |
| `GET /api/platform/onchain/mvrv-cycle` | Decision Engine compact payload |
| `decision_engine_inputs.mvrv_cycle` | Regime filter + risk delta |
