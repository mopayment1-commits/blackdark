# Custom Market Data Screener, DEX Intelligence & Dev-Market Divergence — #533 #535 #537

## #533 — Custom Market Data Screener (Sprint 2)

Renamed from "Custom Intelligence Screener" → **Custom Market Data Screener**.

| Rule | Implementation |
|------|----------------|
| User-controlled | User creates filters; platform applies |
| No AI ranking | No "best pick" or opportunity language |
| Explain each match | "Matched because: [criteria] = [value]" |
| Save + alert | Saved screeners with backend-enforced rate limits |
| Multi-domain | risk, whales, on-chain, derivatives, sentiment, technicals |

API: `/api/platform/intelligence-ledger/intelligence-layer/market-data-screener/*`

## #535 — DEX Intelligence Layer (Sprint 1)

Renamed from "DEX_Liquidity_Listener" → **DEX Intelligence Layer**.

| Rule | Implementation |
|------|----------------|
| Pool/token identity verified | Identity block on every pool |
| Scam/spam filters | Rug pulls excluded from results |
| Reorg handling | 12 confirmation blocks |
| Multi-pool aggregation | By DEX and token |

API: `/api/platform/intelligence-ledger/onchain-layer/dex-intelligence/*`

## #537 — Dev-Market Divergence Detector (Sprint 2)

| Rule | Implementation |
|------|----------------|
| No causal claim | "Diverged over [window]" not "buy opportunity" |
| Windows documented | 90D rolling, 14D persistence |
| Sparse data handling | Insufficient data flagged |
| Backtest | Historical divergence stats |
| Descriptive only | Not prediction, not value signal |

API: `/api/platform/intelligence-ledger/intelligence-layer/dev-market-divergence/*`
