# Market Analysis Layer (#105–#116)

## #105 Tail Risk Alpha Multiplier

Merged into Backtest (#74) + Advanced Risk (#77) + IC Report (#87).

Sortino modified, conditional drawdown, tail alpha formula visible.

## #106 Cross-Margin Contagion Risk Vector

`GET /radar/market-health/contagion` — Pro/Institution tier.

Rule-based cascade simulation. Risk map only — no auto-action.

## #107 Whale-to-Retail Volume Ratio

Merged into Whale Narrative (#71) + Market Radar.

Whale >$1M / Retail <$10K thresholds explicit.

## #108 CEX Order Book Bid-Ask Skew

`GET /radar/technical/orderbook-skew`

Skew = (Bid − Ask) / (Bid + Ask), range [-1, +1].

## #109 Liquidation Volume Spike Anchors

Merged into #82 liquidation alerts. Historical anchor sensitivity ±3%.

## #110 Whale Wallet Age Acceleration

Merged into #71. Old wallet (>730d) + acceleration (>300%).

## #111 S&P 500 Correlation

Merged into Multi-Dim (#73) macro dimension. Pearson r, 30/90/180d windows.

## #112 Global Crypto Liquidity Index (GCLI)

`GET /radar/market-health/gcli` — Pro tier.

Composite: order book depth + stablecoin flows + on-chain velocity.

## #113 Imbalance Delta Order Flow

`GET /radar/technical/orderflow-imbalance`

Delta = Imbalance_t − Imbalance_{t−1}. Zero-crossing momentum shift.

## #114 Long/Short Ratio (Whales Filtered)

`GET /radar/market-health/ls-ratio`

Whale OI >$500K filter. Noise positions <$50K excluded.

## #115 Volume-Velocity Tracker

`GET /radar/technical/volume-velocity`

Velocity >+200% = surge, <−50% = slowdown.

## #116 Delta Hedging Flow Analysis

`GET /oracle/on-chain/derivatives/delta-flow` · `/radar/derivatives/delta-pressure`

Pro/Institution tier. Spot+futures match heuristic. Artificial pressure insight.

## E2E

```
GET /api/platform/market-analysis/e2e  (admin)
pytest tests/test_market_analysis_batch105_116.py -q
```
