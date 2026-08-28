# Profitability Analyzer / Net Profit Engine (#981)

Insight-only, non-custodial. Merged into **#981 Profitability Analyzer** — NOT standalone.

Deducts all actual fees before displaying net profit: Trading · Withdrawal · Deposit · Network Gas.

## Fee completeness (4 categories)

| Category | Source |
|----------|--------|
| Trading | #907 Exchange Sync (read-only APIs) |
| Withdrawal | Exchange docs + fee_matrix |
| Deposit | Exchange docs + fee_matrix |
| Network Gas | On-chain gas oracle |

## Gross vs Net display

- **Net Profit** = default UI display
- **Gross Profit** = hidden by default, labeled "إجمالي قبل الرسوم"

## Disclaimer

> الربح الصافي = تقدير بناءً على الرسوم المعروفة — Risk Insight لا Protection

## Precision

Financial Precision Policy #1032: 8dp crypto · 2dp fiat · Decimal only in settlement.

## Integrations

| Ref | Role |
|-----|------|
| #907 | Cross-account fee aggregation |
| #959 | Reference price at execution time |
| #908 | Platform fees (Stripe) separate from market fees |
| #945 | Provenance audit per fee |
| #1029 | Immutable PnL inputs |
| #1032 | Decimal precision |

## Edge cases

Bridge fees · cross-chain gas · failed tx gas · airdrop claim gas — classified as `network_gas`, user override allowed.

## API

```
GET /api/platform/profitability-analyzer/status
GET /api/platform/profitability-analyzer/production-gate
GET /api/platform/profitability-analyzer/audit-trail
GET /api/platform/profitability-analyzer/e2e
POST /api/platform/profitability-analyzer/net-profit
```

## Module

- `profitability_analyzer.py`
- `data/profitability_analyzer_seed.json`
