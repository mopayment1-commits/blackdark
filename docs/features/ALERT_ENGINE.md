# Alert Engine — #289 (Sprint 2 Intelligence Ledger)

**Renamed from** "Smart Alerts" → **Alert Engine**. Rule-based first — not AI/ML implied.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Renamed | Smart Alerts → Alert Engine |
| Backend enforcement | Server-side rule evaluation |
| Dedup | Same condition within 5 min = suppressed |
| Retry | 3 attempts |
| Logs | 90 days retained |
| Delivery | push + email + webhook |

## Scope Lock

| Phase | Alerts |
|-------|--------|
| 1 | Price |
| 2 | Indicator |
| 3 | Drawing |
| Wave 3 | ML-based (deferred) |
| #323 | Derivatives alert rules (OI / funding / liquidation) — merged, no separate engine |

## #323 Derivatives Alerts (merged)

- **No separate engine** — rules config inside Alert Engine
- **Thresholds:** OI change > X% | Funding > Y% | Liquidation > Z
- **Dedup:** same asset + condition within 5 min = suppressed
- **#282** Orderflow Anomaly = input source

API: `GET /api/platform/intelligence-ledger/alert-engine/derivatives-rules`

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/alert-engine/status` | Engine status |
| `GET /api/platform/intelligence-ledger/alert-engine` | Panel |
| `GET /api/platform/intelligence-ledger/alert-engine/rules` | Rule list |
| `GET /api/platform/intelligence-ledger/alert-engine/delivery-logs` | Audit logs |
