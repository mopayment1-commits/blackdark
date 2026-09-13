# FINAL INSTITUTIONAL REPORT — Time & Timezone

## Counts

| Status | Count |
|---|---:|
| YES | 13 |
| PARTIAL | 13 |
| NO | 8 |
| BLOCKED_EXTERNAL | 2 |

## Production enforcement default

- `BLACKDARK_TIME_ENFORCE` defaults to **ON** (1).
- Production profile cannot disable time enforcement.

## Independent sample re-verification (≥12)

| Req | Status | Verified |
|---|---|---|
| TZ-004 | YES | confirmed |
| TZ-001 | YES | confirmed |
| TZ-009 | PARTIAL | demoted/honest gap |
| TZ-008 | YES | confirmed |
| TZ-020 | NO | demoted/honest gap |
| TZ-011 | BLOCKED_EXTERNAL | confirmed |
| TZ-018 | PARTIAL | demoted/honest gap |
| TZ-002 | YES | confirmed |
| TZ-005 | PARTIAL | demoted/honest gap |
| TZ-003 | PARTIAL | demoted/honest gap |
| TZ-006 | PARTIAL | demoted/honest gap |
| TZ-007 | YES | confirmed |

## Non-YES requirements

- **TZ-003** (PARTIAL): Browser detection is UI suggestion only; no first-session server persistence
- **TZ-005** (PARTIAL): Column exists; registration default persistence not independently tested
- **TZ-006** (PARTIAL): Manual override wired; no dedicated failing test for profile save path
- **TZ-009** (PARTIAL): No active coupling found; no negative test proving separation
- **TZ-010** (PARTIAL): No country→timezone sole mapping found; not regression-tested
- **TZ-011** (BLOCKED_EXTERNAL): Production NTP/chrony/host clock sync not verifiable in this repository
- **TZ-014** (PARTIAL): Format API exists; dashboards/charts/tables not uniformly localized
- **TZ-015** (PARTIAL): i18n locale formatters exist separately; unified locale+timezone display not proven
- **TZ-016** (NO): Decision-critical UI does not consistently show timezone labels
- **TZ-017** (NO): Chart components not bound to explicit display timezone policy
- **TZ-018** (PARTIAL): Market library UTC-stamped; not all ingestion paths audited
- **TZ-019** (NO): AI output formatters do not resolve user timezone
- **TZ-020** (NO): Notification scheduling/display not wired to user timezone resolver
- **TZ-021** (NO): Email templates do not localize times via account timezone
- **TZ-022** (NO): Reports/exports lack timezone metadata contract
- **TZ-023** (PARTIAL): Audit logs store UTC; user-visible activity UI localization incomplete
- **TZ-024** (PARTIAL): Billing ledger UTC; billing UI timezone localization not proven
- **TZ-025** (NO): No recurring schedule model with IANA zone + wall-clock rule
- **TZ-029** (PARTIAL): i18n system exists; time display not fully integrated with 38-locale formatters
- **TZ-030** (NO): Cross-surface audit incomplete — charts, emails, notifications, heroes not wired
- **TZ-034** (PARTIAL): No identity/auth decisions on detected timezone; policy not regression-tested
- **TZ-035** (PARTIAL): Engineering closure meta-requirement — mandatory items remain NO/PARTIAL
- **TZ-036** (BLOCKED_EXTERNAL): Live gate requires production browser/DST/notification/cross-device evidence

## Declarations (T5)

**IN_REPO_TIME_COMPLIANCE = NO**

**LIVE_LAUNCH_READY = NO**

### Rationale

- 8 mandatory requirement(s) remain NO.
- 2 item(s) BLOCKED_EXTERNAL (TZ-011 NTP, TZ-036 live gate).
- 13 item(s) PARTIAL — cross-surface display/notifications not fully wired.
- LIVE_LAUNCH_READY requires production evidence beyond repository tests.
