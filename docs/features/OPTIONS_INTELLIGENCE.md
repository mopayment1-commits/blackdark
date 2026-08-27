# Features #82 + #83 — Options Intelligence Module

Advanced volatility analytics: IV surface (#82) + term structure (#83).

## Scope

**NOT a casual-user feature** — advanced analytics tab feeding #48 Decision Engine volatility regime.

## #82 IV Surface

- Data: IV by strike/expiry from Deribit `get_book_summary_by_currency`
- Surface construction: moneyness grid + ATM IV + put skew
- Benchmark validation: ATM IV vs asset-specific sanity bands (BTC 15–120%, ETH 20–150%)

## #83 Term Structure

- Data: IV by expiry → ATM term curve
- Expiry exactness: Deribit token parse (`29MAR24`) + future-date validation
- Regimes: `contango`, `backwardation`, `flat`

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/options/intelligence?asset=BTC` | Full surface + term structure |
| `GET /api/platform/options/status` | Module health |
| `decision_engine_inputs.options_intelligence` | Volatility risk delta |
| Cap646 #49 | `options_intelligence_suite` surface |

## User headline examples

- *"BTC IV Surface: ATM 45% | Put Skew Extreme | AI flags potential gamma squeeze"*
- *"BTC Term Structure: Front month IV 52% vs Back month 38% — AI flags extreme backwardation"*

## Provider

Deribit public API (no execution). `options_fetcher.py` remains for legacy overview; Cap646 #49 routes through this module.
