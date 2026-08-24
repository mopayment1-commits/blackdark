# Feature #108 — Best Transfer Networks (Micro-Utility)

Widget that ranks networks for asset transfers — appears when user searches for withdraw/transfer.

## Displays

| Dimension | Description |
|-----------|-------------|
| Speed | ETA minutes + speed score |
| Cost | Live gas oracle fee (USD) when available |
| Security | Stable / Standard / Experimental tier |

## Integrated with #120

User's saved network (`network_used`) shown alongside recommendations with savings hint.

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/transfer/networks?asset=USDT` | Full widget payload |
| `GET /api/platform/transfer/networks/rank` | Rankings only |
| `GET /api/platform/transfer/network-used` | #120 user preference |
| `POST /api/platform/transfer/network-used` | #120 save preference |
| `GET /api/platform/transfer/networks/status` | Module health |

## Supported assets

USDT, USDC, ETH, BTC (9+ networks each)

## Example headline

> Best for USDT transfer: TRON (TRC20) — $1.00 fee, ~2 min, stable network

## Acceptance

| Criterion | Implementation |
|-----------|----------------|
| Response ≤2s | `sla_met` on every response |
| Live fees | `gas_oracle` with static fallback |
| Accuracy | Live oracle when chain supported |
