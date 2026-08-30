# Institutional B2B Layer (#87–#94)

## #87 IC Report Export

`GET/POST /intelligence/export/ic-report` and `/portfolio/export/ic-report`

PDF + HTML + JSON. Composes: Clear Answer (#63) + Methodology (#86) + Performance (#84) + Disclaimer (#57) + Share Card (#68).

## #88 Team RBAC

Merged into Auth. Roles: Admin · Analyst · Viewer · Guest.

`GET /api/platform/team/rbac/status` · `POST /api/platform/team/rbac/check`

Export permission separate from view. Audit log for every action.

## #89 SLA — DEFERRED Wave 3

Best effort only — no guaranteed uptime. Status stub.

## #90 White-Label — DEFERRED Wave 3

Status stub — Powered by BLACKDARK required when built.

## #91 VWAP Deviation

`GET /radar/technical/vwap` — merged into TA Engine.

## #92 Counterparty Risk

Extends #80 exchange health with withdrawal latency, reserve transparency, abnormal flows.

`GET /radar/exchange-health/full`

## #93 Confidence Calibration

Merged into Discipline (#66) + Journal (#76). Formula: |declared − hit_rate|.

## #94 Audit Exports — DEFERRED Wave 3

Preview via RBAC audit export. Full activation with Institution Portal.

## E2E

```
GET /api/platform/institutional-b2b/e2e  (admin)
pytest tests/test_institutional_b2b_batch87_94.py -q
```
