# Portfolio AI Risk Tab — VaR + CVaR + Correlation + Stress

**Sprint 2 · Insight-only · Non-custodial · NOT standalone**

Unified risk metrics sharing one holdings ingest path (#907).

## Risk Tab Quartet

| Metric | Ref | What it measures |
|--------|-----|------------------|
| **VaR** | #1021 | Percentile loss bound |
| **CVaR** | #1022 | Average tail loss beyond VaR |
| **Correlation** | #1049 | Asset co-movement (Pearson) |
| **Stress** | #1006 | Historical extreme scenarios |

## CVaR (#1022)

Historical expected shortfall — average of worst 5% daily losses (at 95% confidence).

> "In the worst 5% of days, average loss was $X" — NOT a catastrophe guarantee.

## Correlation (#1049)

Pearson correlation matrix (-1 to +1). High correlation (+0.85) = false diversification warning.

Insight-only — no forced rebalancing.

## Stress Testing (#1006)

Three predefined scenarios:
1. **Flash Crash** — 30%+ single-day drop
2. **Liquidity Freeze** — 80% volume drop amplifies worst move
3. **Correlation Breakdown** — correlations → 1 under stress

Plus historical worst 5 consecutive days.

## API

| Endpoint | Description |
|----------|-------------|
| `POST /portfolio/analyze` | Full `risk_tab` block |
| `GET /api/platform/portfolio-risk-tab/{status,e2e}` | Unified status |
| `GET /api/platform/portfolio-{var,cvar,correlation,stress}/status` | Per-metric |

## Shared data path

`portfolio_risk_shared.py` → single returns series for VaR, CVaR, Correlation, Stress.

## Disclaimer

Low VaR/CVaR/stress loss ≠ safe portfolio. Risk Tab warns — does not protect.
