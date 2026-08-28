# Portfolio Concentration Risk Alert

**Sprint 2 · Portfolio AI Risk Tab · Insight-only · Non-custodial**

User-configurable position concentration warnings — NOT trade blocks.

## Formula

`concentration % = (position_value / total_portfolio_value) × 100`

## Default threshold

30% per asset (user-configurable).

## Output

> "تعرضك لـ BTC = 85% من المحفظة = تركيز مرتفع"

NOT: "تم حظر الشراء"

## API

- `GET /api/platform/concentration-risk/{status,e2e}`
- `POST /api/platform/concentration-risk/thresholds` (user auth)
- `POST /portfolio/analyze` includes `concentration_risk`

## Integrations

- #907 positions · #959 pricing · #1049 correlation escalation · #1021/#1022 VaR/CVaR
