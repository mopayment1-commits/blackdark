# Correlation & Lead-Lag Module — #271 (Sprint 2 Intelligence Ledger)

**NOT standalone** — merged into **Intelligence Ledger / Analyst Suite**.

Exploration tool for metric correlation and lead-lag analysis. Dashboard UI deferred — backend module only.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Dependency gate | Sprint 1 Data Engine + 30 day stability |
| No causation language | Correlation values only — banned: causes/drives/predicts |
| Significance visible | p-value displayed, p < 0.05 highlighted |
| Window visible | 7/30/90/365 days |
| Missing data | > 20% in window = correlation blocked |
| Scope Phase 1 | Price vs on-chain metrics only |
| Update mode | Daily batch — no real-time |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/correlation/status` | Module status |
| `GET /api/platform/intelligence-ledger/correlation` | Correlation + lead-lag panel |

## Disclaimer

"Correlation does not imply causation" — non-hideable.
