# Wave 1 Report — Close 8 NO items

**Batch:** TZ-016, TZ-017, TZ-019, TZ-020, TZ-021, TZ-022, TZ-025, TZ-030

## Outcomes

| Req | Status | Control |
|---|---|---|
| TZ-016 | YES | `format_with_label` + dashboard TZ labels |
| TZ-017 | YES | `chart_config` + `blackdark-timezone.js` |
| TZ-019 | YES | `market_context.timestamp_human` → `format_ai_output` |
| TZ-020 | YES | `in_app_alerts` → `format_notification` |
| TZ-021 | YES | `alert_service` + `identity_service` → `format_email` |
| TZ-022 | YES | `weekly_report` + `audit_registry` → `export_metadata` |
| TZ-025 | YES | `RecurringSchedule` + `/api/timezone/schedules` |
| TZ-030 | YES | `cross_surface_status` + heroes/alerts/billing wiring |

All 8 former NO items closed with live caller → control paths and failing-if-removed tests.
