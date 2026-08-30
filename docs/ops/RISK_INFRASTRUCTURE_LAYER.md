# Risk & Infrastructure Layer (#164–#176)

## #164 Panic Button — REJECTED

Alternative: `GET /portfolio/liquidity-impact` — liquidity impact warning only.

## #165 Hashrate Capitulation Forecast

`GET /oracle/on-chain/mining` — hashrate death cross + miner revenue vs cost analysis.

## #166 Brokerage API — REJECTED

Alternative: White-Label Insights API (#90) — insights only, Wave 3.

## #167 Time-Sync Latency Deviation

Merged into `GET /oracle/validate` (#101) — NTP-aware stale data rejection.

## #168 Whale Wallet Cluster Index

Merged into `POST /oracle/on-chain/sybil-clustering` (#129) — quantified cluster impact.

## #169 Correlation Decay Matrix

`GET /portfolio/risk/advanced/correlation-decay` — embedded in Advanced Risk (#77).

## #170 OI Momentum Delta

`GET /radar/derivatives/oi-momentum` — derivatives open interest flow analysis.

## #171 Federal Reserve M2 Macro Flow

`GET /intelligence/multi-dim/macro/m2` — extends Macro Dimension (#133).

## #172 Institutional Memory — MERGED

`GET /intelligence/institutional-memory-status` — merged into Data Flywheel (#97).

## #173 Institutional RBAC — MERGED

`GET /auth/institutional-rbac-status` — duplicate of #88.

## #174 Full White Label — DEFERRED

`GET /institution/full-white-label-status` — Wave 3, merged into #90.

## #175 Risk Intelligence — MERGED

`GET /portfolio/risk-intelligence-status` — merged into Advanced Risk (#77).

## #176 Operational Resilience Engine

`GET /infrastructure/resilience-status` (admin) — Sprint 0 infrastructure.

## E2E

```
GET /api/platform/risk-infrastructure/e2e  (admin)
pytest tests/test_risk_infrastructure_batch164_176.py -q
```
