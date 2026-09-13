# FULL TRUTH TABLE — Time & Timezone Compliance

**Governing file:** `docs/BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1.md`
**Mandatory requirements:** 36

## Arabic owner summary

- إجمالي المتطلبات الإلزامية: **36**
- YES: **13**
- PARTIAL: **13**
- NO: **8**
- BLOCKED_EXTERNAL: **2**

## Status matrix

| Req | Category | Status | Caller → Control | Test | Gap |
|---|---|---|---|---|---|
| TZ-001 | canonical_utc | YES | decision_ledger._utcnow → blackdark.timezone.utc_now_iso | tests/test_timezone_runtime_enforcement.py::test_decision_ledger_uses_canonical_iso | — |
| TZ-002 | parsing | YES | api/routers/auth.py:_profile_update_fields → validate_iana_timezone | tests/test_timezone_runtime_enforcement.py::test_validate_iana_timezone_rejects_invalid | — |
| TZ-003 | ui | PARTIAL | templates/profile.html:Intl.DateTimeFormat().resolvedOptions().timeZone | — | Browser detection is UI suggestion only; no first-session server persistence |
| TZ-004 | api | YES | blackdark/timezone.py:resolve_timezone → api/routers/timezone.py:/api/timezone/resolve | tests/test_timezone_runtime_enforcement.py::test_resolve_timezone_precedence | — |
| TZ-005 | storage | PARTIAL | database.py:users.timezone column → update_user_profile_fields | — | Column exists; registration default persistence not independently tested |
| TZ-006 | ui | PARTIAL | templates/profile.html + api/routers/auth.py PATCH /profile | — | Manual override wired; no dedicated failing test for profile save path |
| TZ-007 | api | YES | blackdark/timezone.py:resolve_timezone (account > detected) | tests/test_timezone_runtime_enforcement.py::test_resolve_preserves_account_over_detected | — |
| TZ-008 | dst | YES | blackdark/timezone.py:to_display_tz → ZoneInfo | tests/test_timezone_runtime_enforcement.py::test_dst_conversion_new_york | — |
| TZ-009 | display | PARTIAL | — | — | No active coupling found; no negative test proving separation |
| TZ-010 | display | PARTIAL | — | — | No country→timezone sole mapping found; not regression-tested |
| TZ-011 | jobs | BLOCKED_EXTERNAL | — | — | Production NTP/chrony/host clock sync not verifiable in this repository |
| TZ-012 | storage | YES | blackdark/data/models.py:DateTime(timezone=True), default=utc_now | tests/test_timezone_runtime_enforcement.py::test_models_use_timezone_aware_columns | — |
| TZ-013 | api | YES | blackdark/timezone.py:format_iso_z | tests/test_timezone_runtime_enforcement.py::test_format_iso_z_uses_z_suffix | — |
| TZ-014 | display | PARTIAL | api/routers/timezone.py:/api/timezone/format → to_display_tz | — | Format API exists; dashboards/charts/tables not uniformly localized |
| TZ-015 | display | PARTIAL | — | — | i18n locale formatters exist separately; unified locale+timezone display not proven |
| TZ-016 | display | NO | — | — | Decision-critical UI does not consistently show timezone labels |
| TZ-017 | display | NO | — | — | Chart components not bound to explicit display timezone policy |
| TZ-018 | ordering | PARTIAL | market_event_library.py → utc_now_iso | — | Market library UTC-stamped; not all ingestion paths audited |
| TZ-019 | display | NO | — | — | AI output formatters do not resolve user timezone |
| TZ-020 | integration | NO | — | — | Notification scheduling/display not wired to user timezone resolver |
| TZ-021 | integration | NO | — | — | Email templates do not localize times via account timezone |
| TZ-022 | display | NO | — | — | Reports/exports lack timezone metadata contract |
| TZ-023 | display | PARTIAL | — | — | Audit logs store UTC; user-visible activity UI localization incomplete |
| TZ-024 | display | PARTIAL | — | — | Billing ledger UTC; billing UI timezone localization not proven |
| TZ-025 | storage | NO | — | — | No recurring schedule model with IANA zone + wall-clock rule |
| TZ-026 | dst | YES | blackdark/timezone.py:resolve_local_to_utc | tests/test_timezone_runtime_enforcement.py::test_dst_fold_ambiguous_local | — |
| TZ-027 | storage | YES | blackdark/timezone.py:preference change does not rewrite stored instants | tests/test_timezone_runtime_enforcement.py::test_historical_integrity_unchanged_on_tz_change | — |
| TZ-028 | storage | YES | api/routers/auth.py → persist_timezone_audit | tests/test_timezone_runtime_enforcement.py::test_persist_timezone_audit | — |
| TZ-029 | display | PARTIAL | — | — | i18n system exists; time display not fully integrated with 38-locale formatters |
| TZ-030 | api | NO | — | — | Cross-surface audit incomplete — charts, emails, notifications, heroes not wired |
| TZ-031 | canonical_utc | YES | blackdark/timezone.py:ensure_aware_utc + time_enforce_enabled | tests/test_timezone_runtime_enforcement.py::test_ensure_aware_utc_rejects_naive_when_enforced | — |
| TZ-032 | parsing | YES | blackdark/timezone.py:zoneinfo.available_timezones / ZoneInfo | tests/test_timezone_runtime_enforcement.py::test_iana_tzdb_available | — |
| TZ-033 | parsing | YES | blackdark/timezone.py:safe_timezone → logger.warning | tests/test_timezone_runtime_enforcement.py::test_safe_timezone_fallback_invalid | — |
| TZ-034 | api | PARTIAL | — | — | No identity/auth decisions on detected timezone; policy not regression-tested |
| TZ-035 | api | PARTIAL | — | — | Engineering closure meta-requirement — mandatory items remain NO/PARTIAL |
| TZ-036 | integration | BLOCKED_EXTERNAL | — | — | Live gate requires production browser/DST/notification/cross-device evidence |
