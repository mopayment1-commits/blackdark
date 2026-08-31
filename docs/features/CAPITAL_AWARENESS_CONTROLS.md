# Capital Awareness Controls — Feature #410

## Decision

**Sprint 2 Risk Module — High priority, NOT standalone.**

Legal name: **Risk Awareness Layer** / **Capital Awareness Controls**  
Forbidden: "insurance", "guarantee", "protection" as capital insurance.

| Scope | Status |
|-------|--------|
| Non-executive (alerts only) | ✅ Mandatory |
| No automatic fund movement | ✅ SLA + ToS |
| Risk Score per position (0–100) | ✅ |
| Scenario Stress Testing | ✅ MDD, correlation shock, liquidity freeze |
| Risk Budget | ✅ User max loss % with proximity warnings |
| Portfolio AI alerts | ✅ Concentration, drawdown, sector correlation |
| Intelligence Ledger Risk Assessment | ✅ Mandatory on every signal |
| Standalone module | ❌ Cancelled |

## API

```
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/status
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness
GET /api/platform/intelligence-ledger/portfolio-ai/capital-awareness/reconciliation-tests
GET /api/platform/intelligence-ledger/intelligence-layer/capital-awareness/risk-assessment?signal_id=sig_btc_momentum
GET /api/platform/intelligence-ledger/portfolio-ai/capital-protection/breakeven-alerts
```

## SLA

> BLACKDARK never moves funds automatically. No stop-loss execution, no auto-rebalance, no order placement without explicit user action. Risk Awareness alerts are informational only.

## Competitive Differentiator

Non-executive model — unlike 3Commas, Alphio, Stoic which require API keys for auto-execution.
