# Strategy Lab — #716 + #712 (Sprint 2 Pro/Institution)

| Ticket | Role |
|--------|------|
| #716 | On-The-Fly Historical Backtester (user-facing Strategy Lab) |
| #712 | AI Backtesting Verification Tag (internal QA gate — badge only) |

## #712 Internal QA Gate (CI/CD)

NOT user-facing except **"✓ Model Verified"** badge.

| Criterion | Requirement |
|-----------|-------------|
| Coverage | ≥ 80% |
| Reproducible tests | Same strategy + data = same result |
| Blast radius | Sandbox before production only |
| Backtest window | ≥ 2 years for AI models |

## #716 Strategy Lab (User-Facing)

| Feature | Implementation |
|---------|----------------|
| Speed | 2-year backtest < 10 seconds |
| Isolation | Sandbox environment, no blast radius |
| Reproducible | Deterministic `backtest_hash` |
| Walk-forward | Out-of-sample folds |
| Label | "Historical simulation" — NOT future prediction |
| Anti curve-fitting | `no_curve_fitting: true` |

Example output: `Win Rate: 62% | Average Return: 8% | Max Drawdown: 12% | Backtest: 18 months`

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/strategy-lab/status` | Lab status + QA gate summary |
| `GET /api/platform/intelligence-ledger/strategy-lab` | Backtest panel |
| `GET /api/platform/intelligence-ledger/strategy-lab/strategies` | Available strategies |
| `GET /api/platform/intelligence-ledger/strategy-lab/verified-badge` | #712 user-visible badge only |
