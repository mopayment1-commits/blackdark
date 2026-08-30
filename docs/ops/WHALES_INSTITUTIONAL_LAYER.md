# Whales & Institutional Layer (#77–#86)

## #77 Advanced Risk Tab (Portfolio AI)

Exposure + 30d correlation + stress scenarios. Risk Insight not Protection.

## #78 Smart Execution — REJECTED

Execution routing rejected. Alternative: `GET /api/platform/intelligence/impact-analysis` (slippage insight only).

## #79 Wallet Surveillance Insight

Merged into On-Chain + Unified View (#81). Educational insight only — no auto protection.

## #80 Exchange Health (Market Radar)

`GET /radar/exchange-health` — reserves, withdrawal velocity, sentiment, flows.

## #81 Unified Portfolio View

Multi-chain manual input + Health Score (#67) + Advanced Risk (#77).

## #82 Liquidation Cascade Alerts

`POST /api/platform/radar/alerts/liquidation` — proactive, no auto-action.

## #83 SMB Institution — DEFERRED Wave 3

Status only — no build until 500+ active Pro users.

## #84 Public Performance Ledger

`GET /transparency/performance` — auditable hit rate for due diligence.

## #85 OpenAPI Documentation

OpenAPI 3.0+ with fee metadata on `/api/docs/openapi.json`.

## #86 Methodology Documentation

`GET /transparency/methodology` — rule-based formulas, limitations, quarterly review.

## E2E

```
GET /api/platform/whales-institutional/e2e  (admin)
pytest tests/test_whales_institutional_batch77_86.py -q
```
