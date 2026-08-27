# Feature #99 — AI Trading Journal & Performance Coach

Encrypted trade journal with rule-based performance coaching. Distinct from Trade Simulator (#94).

## Capabilities

- **Manual entry** + batch import from 5 exchanges (Binance, Bybit, OKX, KuCoin, Gate.io)
- **Performance metrics**: P&L, win rate, profit factor, expectancy, max drawdown, R:R
- **AI compliance**: win rate when following vs ignoring #48 signals
- **Psychology**: mood correlation, trader profile hints
- **Mistake detection**: poor R:R, oversized positions, revenge trading, AI ignore pattern
- **Weekly report card** with grade + coach tips

## Privacy

All trades encrypted at rest (Fernet via `secrets_vault`). Team cannot read raw trade payloads.

## APIs

| Method | Endpoint |
|--------|----------|
| POST | `/api/platform/trading-journal/trades` |
| POST | `/api/platform/trading-journal/import` |
| GET | `/api/platform/trading-journal/dashboard` |
| GET | `/api/platform/trading-journal/coach-report` |
| GET | `/api/platform/trading-journal/mistakes` |
| GET | `/api/platform/trading-journal/status` |

## vs #94 Trade Simulator

| | #94 Simulator | #99 Journal |
|--|---------------|-------------|
| Focus | Paper trades on AI signals | Real/manual trade analysis |
| Goal | Test AI before committing | Improve personal performance |
| Data | Virtual portfolio | Encrypted actual trades + mood |
