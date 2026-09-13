# FULL TRUTH TABLE — Time & Timezone Compliance

**Governing file:** `docs/BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1.md`
**Mandatory requirements:** 36

## Arabic owner summary

- إجمالي المتطلبات الإلزامية: **36**
- YES: **34**
- PARTIAL: **0**
- NO: **0**
- BLOCKED_EXTERNAL: **2**

## Status matrix

| Req | Category | Status | Caller → Control | Test | Gap |
|---|---|---|---|---|---|
| TZ-001 | canonical_utc | YES | decision_ledger._utcnow → blackdark.timezone.utc_now_iso | tests/test_timezone_runtime_enforcement.py::test_decision_ledger_uses_canonical_iso | — |
| TZ-002 | parsing | YES | api/routers/auth.py:_profile_update_fields → validate_iana_timezone | tests/test_timezone_runtime_enforcement.py::test_validate_iana_timezone_rejects_invalid | — |
| TZ-003 | ui | YES | templates/profile.html → POST /api/timezone/session | tests/test_timezone_surface_closure.py::test_timezone_session_endpoint_accepts_browser_zone | — |
| TZ-004 | api | YES | blackdark.timezone:resolve_timezone → api/routers/timezone.py:/api/timezone/resolve | tests/test_timezone_runtime_enforcement.py::test_resolve_timezone_precedence | — |
| TZ-005 | storage | YES | database.py:users.timezone → api/routers/auth.py PATCH /profile | tests/test_timezone_surface_closure.py::test_profile_timezone_save_persists_iana | — |
| TZ-006 | ui | YES | templates/profile.html + api/routers/auth.py PATCH /profile | tests/test_timezone_surface_closure.py::test_profile_timezone_save_persists_iana | — |
| TZ-007 | api | YES | blackdark.timezone:resolve_timezone (account > detected) | tests/test_timezone_runtime_enforcement.py::test_resolve_preserves_account_over_detected | — |
| TZ-008 | dst | YES | blackdark.timezone:to_display_tz → ZoneInfo | tests/test_timezone_runtime_enforcement.py::test_dst_conversion_new_york | — |
| TZ-009 | display | YES | blackdark.timezone.display:resolve_timezone_independent_of_lang | tests/test_timezone_surface_closure.py::test_language_does_not_determine_timezone | — |
| TZ-010 | display | YES | blackdark.timezone.display:resolve_timezone_independent_of_country | tests/test_timezone_surface_closure.py::test_country_not_sole_timezone_source | — |
| TZ-011 | jobs | BLOCKED_EXTERNAL | — | — | Production NTP/chrony/host clock sync not verifiable in this repository |
| TZ-012 | storage | YES | blackdark/data/models.py:DateTime(timezone=True), default=utc_now | tests/test_timezone_runtime_enforcement.py::test_models_use_timezone_aware_columns | — |
| TZ-013 | api | YES | blackdark.timezone:format_iso_z | tests/test_timezone_runtime_enforcement.py::test_format_iso_z_uses_z_suffix | — |
| TZ-014 | display | YES | blackdark.timezone.display:format_with_label → enrich_fields | tests/test_timezone_surface_closure.py::test_format_with_label_includes_timezone_context | — |
| TZ-015 | display | YES | blackdark.timezone.display:format_for_locale → i18n_service.normalize_lang | tests/test_timezone_surface_closure.py::test_format_for_locale_integrates_i18n | — |
| TZ-016 | display | YES | blackdark.timezone.display:format_with_label → dashboard inbox labels | tests/test_timezone_surface_closure.py::test_format_with_label_includes_timezone_context | — |
| TZ-017 | display | YES | blackdark.timezone.display:chart_config → market.py + blackdark-timezone.js | tests/test_timezone_surface_closure.py::test_market_klines_includes_chart_config | — |
| TZ-018 | ordering | YES | ingestion paths → blackdark.timezone.utc_now_iso | tests/test_timezone_surface_closure.py::test_ingestion_paths_use_canonical_utc | — |
| TZ-019 | display | YES | market_context.timestamp_human → format_ai_output | tests/test_timezone_surface_closure.py::test_timestamp_human_wires_format_ai_output | — |
| TZ-020 | integration | YES | in_app_alerts.list_in_app_alerts → format_notification | tests/test_timezone_surface_closure.py::test_in_app_alerts_localizes_created_at | — |
| TZ-021 | integration | YES | alert_service._localize_alert_body + identity_service → format_email | tests/test_timezone_surface_closure.py::test_alert_service_email_localizes | — |
| TZ-022 | display | YES | weekly_report.report_to_markdown + audit_registry → export_metadata | tests/test_timezone_surface_closure.py::test_weekly_report_markdown_includes_timezone_metadata | — |
| TZ-023 | display | YES | security_events.recent_security_events → format_activity_log | tests/test_timezone_surface_closure.py::test_security_events_localizes_for_user | — |
| TZ-024 | display | YES | api/routers/billing.py → format_billing | tests/test_timezone_surface_closure.py::test_format_billing_preserves_utc_authority | — |
| TZ-025 | storage | YES | blackdark.timezone.schedules:RecurringSchedule → /api/timezone/schedules | tests/test_timezone_surface_closure.py::test_recurring_schedule_iana_and_wall_clock | — |
| TZ-026 | dst | YES | blackdark.timezone:resolve_local_to_utc | tests/test_timezone_runtime_enforcement.py::test_dst_fold_ambiguous_local | — |
| TZ-027 | storage | YES | blackdark.timezone:preference change does not rewrite stored instants | tests/test_timezone_runtime_enforcement.py::test_historical_integrity_unchanged_on_tz_change | — |
| TZ-028 | storage | YES | api/routers/auth.py → persist_timezone_audit | tests/test_timezone_runtime_enforcement.py::test_persist_timezone_audit | — |
| TZ-029 | display | YES | blackdark.timezone.display:format_for_locale → i18n_service | tests/test_timezone_surface_closure.py::test_i18n_locale_does_not_change_timezone_field | — |
| TZ-030 | api | YES | blackdark.timezone.display:cross_surface_status → /api/timezone/cross-surface | tests/test_timezone_surface_closure.py::test_cross_surface_registry_covers_required_surfaces | — |
| TZ-031 | canonical_utc | YES | blackdark.timezone:ensure_aware_utc + time_enforce_enabled | tests/test_timezone_runtime_enforcement.py::test_ensure_aware_utc_rejects_naive_when_enforced | — |
| TZ-032 | parsing | YES | blackdark.timezone:zoneinfo.available_timezones / ZoneInfo | tests/test_timezone_runtime_enforcement.py::test_iana_tzdb_available | — |
| TZ-033 | parsing | YES | blackdark.timezone:safe_timezone → logger.warning | tests/test_timezone_runtime_enforcement.py::test_safe_timezone_fallback_invalid | — |
| TZ-034 | api | YES | blackdark.timezone.display:timezone_detection_privacy → /api/privacy/status | tests/test_timezone_surface_closure.py::test_privacy_status_includes_timezone_policy | — |
| TZ-035 | api | YES | scripts/timezone_runtime_truth_audit.py + surface closure tests | tests/test_timezone_surface_closure.py + tests/test_timezone_runtime_enforcement.py | — |
| TZ-036 | integration | BLOCKED_EXTERNAL | — | — | Live gate requires production browser/DST/notification/cross-device evidence |
