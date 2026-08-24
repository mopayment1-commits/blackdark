# Early Stage Scanner + Liquidity Inflow — Features #115, #116, #193, #149

## #115 Early Stage Token Scanner

Filtering tool — **not** prediction or "واعدة/promising".

| Filter | Rule |
|--------|------|
| Market cap | < $10M |
| Liquidity lock | > 6 months (label or pair age proxy) |
| Contract verified | DexScreener verified label / info |
| Holder distribution | Balanced buy/sell txn flow |

Integrates **#193 Smart Contract Scanner** — rejects critical/high risk contracts.

API: `GET /api/platform/market-radar/early-stage-scanner`

## #116 Liquidity Inflow Alert

On-chain signal alerts — **not** "فرصة/opportunity".

| Signal | Threshold |
|--------|-----------|
| Volume 3x | 1h volume ≥ 3× baseline |
| New wallets | > 100 buy txns in 1h (proxy) |
| TVL spike | Liquidity +25% vs prior snapshot |

Includes **Confidence Score (#149)** per alert.

API: `GET /api/platform/market-radar/liquidity-inflow`

## #193 Smart Contract Scanner

API: `GET /api/platform/security/contract-scan?chain=&address=`

## Market Radar

`/api/market/radar-narrative` enriched with `early_stage_scanner` and `liquidity_inflow` blocks.

## Acceptance

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Mode | `filter_only` / `alert_only` |
| Disclaimer | Required on all responses |
