# Market Intelligence Suite — #719 #721 #723 #724 #726 #728

## #719 Smart Anomaly Alert Engine (+ #131 + #121)

Rolling baseline (30-day) + z-score. No manual-only threshold.

| Rule | Value |
|------|-------|
| Baseline | 30-day rolling mean, version documented |
| Low-sample guard | < 7 days = no alert |
| False positives | Backtest documented (e.g. 15%) |

APIs: `/api/platform/intelligence-ledger/smart-anomaly-alerts/*`

## #721 Bot Activity Detection

Layer in Market Intelligence Engine — NOT standalone. Rule-based first.

Consumers: Market Radar, Portfolio AI, Oracle API.

API: `/api/platform/intelligence-ledger/market-intelligence/bot-activity`

## #723 Portfolio Risk Analytics (Correlation)

Widget in Portfolio AI — NOT "Correlation Matrix" only.

Missing-data: grey-out, no interpolation. Window user-selectable.

API: `/api/platform/intelligence-ledger/portfolio-risk/correlation`

## #724 Market Breadth Module

Market Radar widget. Universe versioned, survivorship controlled.

Output: Breadth Score + Regime + Confidence + non-hideable disclaimer.

API: `/api/platform/intelligence-ledger/market-breadth`

## #726 Interactive Charting Engine (+ #732)

Renamed from CryptoQuant. Drawing tools absorbed.

≥50 indicators, ≤100ms latency, save/load layouts.

API: `/api/platform/charting/*`

## #728 Dashboard Builder

Sprint 2 Platform Layer. Depends on #726 + #742.

Permissions + save + version mandatory.

API: `/api/platform/dashboard-builder/*`
