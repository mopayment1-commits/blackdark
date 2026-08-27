# Impermanent Loss Live Simulator

**CAP978 ID 954** — Live LP impermanent loss vs HODL with real market data.

## Features

- Constant-product AMM (Uniswap v2 style) 50/50 full-range IL math
- Live pool prices + liquidity from **DexScreener**
- Pool fee APY from **DeFiLlama yields**
- IL vulnerability score (CAP978 ID 934)
- Alerts when IL exceeds 5% / 10% thresholds
- Simulation history in `simulation_logs` (`kind=lp_il`)

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/defi/il/live` | Live simulation |
| `GET /api/platform/defi/il/pools` | Pool search |
| `POST /api/platform/defi/il/simulate` | Custom simulation |
| `GET /api/platform/defi/il/vulnerability-score` | IL risk score |
| `GET /api/platform/defi/il/history` | Past simulations |

## UI

`/il-simulator` — dark theme interactive simulator.

## Formula

```
IL = 2√r / (1+r) − 1
r = exit_price / entry_price
```

## Tests

```bash
pytest tests/test_il_simulator.py -v
```

## Limitations

- v2 50/50 model only (not Uniswap v3 concentrated liquidity)
- Fee APY matched heuristically from DeFiLlama
- Educational — not financial advice
