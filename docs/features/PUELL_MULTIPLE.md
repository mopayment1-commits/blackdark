# Feature #89 — Puell Multiple (Miner Profitability)

Silent on-chain cycle metric — **not a standalone chart**. Feeds Decision Engine (#48) with **≥12% weight**.

## Formula

```
Puell Multiple = Daily Miner Revenue (USD) / 365-Day MA of Daily Miner Revenue (USD)
```

Daily miner revenue:
```
(block_subsidy_btc × 144 blocks/day + daily_fees_btc) × BTC_price_usd
```

## Zone classification

| Zone | Puell Range | Signal |
|------|-------------|--------|
| Deep Capitulation | < 0.4 | Strong Buy |
| Capitulation | 0.4 – 0.8 | Buy |
| Healthy | 0.8 – 2.0 | Hold |
| Euphoria | 2.0 – 4.0 | Sell |
| Deep Euphoria | > 4.0 | Strong Sell |

## Advanced signals

- **Capitulation confirmed**: Puell < 0.5 + hash rate drop > 5% (14d)
- **Hash Ribbon Buy**: Puell recovery + hash rate recovery
- **Miner outflow correlation**: Puell < 0.6 + exchange inflow spike
- **Cycle comparison**: normalized by days-from-halving (≥3 cycles)

## Data sources

1. **Primary**: mempool.space (hash rate, fee aggregates) + block subsidy schedule + CoinGecko price history
2. **Benchmark**: Glassnode API (`GLASSNODE_API_KEY`) — Puell + miner revenue endpoints
3. **Persisted cache**: `data/puell_miner_revenue.jsonl`

## Example headline

> Puell entered Capitulation Zone (0.42). Historically, BTC bottomed within 14-45 days in prior cycles (2015, 2019, 2022).

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/onchain/puell` | Full Puell analysis + miner stress dashboard |
| `GET /api/platform/onchain/puell-cycle` | Decision Engine compact payload |
| `GET /api/platform/onchain/puell/status` | Module health |
| `decision_engine_inputs.puell_multiple` | Risk delta + headline (weight 12%) |

## Acceptance mapping

| Criterion | Implementation |
|-----------|----------------|
| Puell accuracy ≥99% vs Glassnode | `benchmark_validation` when `GLASSNODE_API_KEY` set |
| Daily update ≤2h from UTC close | TTL cache + daily revenue append |
| Historical ≥10 years | CoinGecko `days=max` backfill + persisted series |
| Zone transition alerts | `data/puell_zone_alerts.jsonl` |
| Decision Engine weight ≥12% | `decision_weight: 0.12` |
