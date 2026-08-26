# Strategy Validation & Leverage Intelligence — #350 #352 #356

## #350 Strategy Validation Engine — 🟡 Rename & Internalize (Wave 1)

Renamed from **High_Precision_Backtesting**.

| Rule | Implementation |
|------|----------------|
| No "High Precision" in name | Renamed to Strategy Validation Engine |
| Internal only | No user-facing dashboard, no equity curve for users |
| No look-ahead lock | Point-in-time replay, survivorship controlled |
| Regression fixtures | Automated — no manual validation |
| Infrastructure | Validates intelligence layer, not a product |

API (internal): `/api/platform/internal/strategy-validation/*`

## #352 Leverage Pressure Score — 🟠 Rename & Restructure (Wave 2)

Renamed to **Leverage Context Indicator**.

| Rule | Implementation |
|------|----------------|
| No "Score" in name/output | Component breakdown: OI, funding, liquidations, basis, L/S, vol |
| Formula lock | Documented + versioned + no opaque score |
| No pressure as signal | Numeric display only — no pressure alerts |
| No asset ranking | No ranking list by pressure |
| Legal review | Mandatory before release |

Merged into Derivatives Market State Module (#327).

## #356 Liquidation Cascade Model — 🟠 Rename & Restrict (Wave 2)

Renamed to **Liquidation Risk Context**.

| Rule | Implementation |
|------|----------------|
| No "Model" in name | Historical pattern analysis only |
| No probability output | No cascade probability alerts for users |
| Walk-forward validation | Mandatory — not backtest only |
| Legal review | Mandatory before release |

Merged into Liquidation Cluster Analytics (#307).
