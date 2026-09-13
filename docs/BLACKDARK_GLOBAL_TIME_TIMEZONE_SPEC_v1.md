# BLACKDARK Global Time, Time Zone & Date-Time Handling Specification

**Version:** v1.0
**Status:** Governing SSOT for implementation

## Governing principles

- UTC is the canonical storage/transport instant.
- User-facing time uses the resolved user timezone.
- IANA TZDB identifiers are canonical for timezones.
- Language, country and timezone are independent.
- Explicit user choice overrides automatic detection.
- Recurring schedules retain wall-clock intent plus IANA timezone.
- No silent UTC/local mixing.
- Reuse existing BLACKDARK I18N, Identity/Profile, Billing, Audit and Notification authorities.
- No PASS_LIVE without production evidence.

---

## TZ-001 — Canonical internal time

Persist absolute timestamps as UTC-aware instants; never use local wall-clock time as the canonical event timestamp.

---


## TZ-002 — IANA time zones

Use IANA TZDB identifiers such as `Africa/Cairo` and `America/New_York`; fixed offsets are not canonical user time zones.

---


## TZ-003 — Automatic detection

On first eligible visit/session detect the browser/device time zone using a standards-based runtime API; treat detection as a suggestion, not an immutable identity fact.

---


## TZ-004 — Preference precedence

Resolve timezone as: explicit per-request override > saved account preference > saved session/browser preference > detected browser timezone > UTC default.

---


## TZ-005 — Persistence

Authenticated users must have a persisted preferred timezone.

---


## TZ-006 — Manual override

Profile → Preferences must allow manual timezone selection; an explicit user choice wins over automatic detection.

---


## TZ-007 — Travel/device mismatch

Do not silently overwrite an explicit timezone when a device reports a different zone; handle mismatch by governed policy.

---


## TZ-008 — DST correctness

All conversion must use IANA timezone rules so DST and governmental rule changes are handled correctly.

---


## TZ-009 — Language separation

Language/locale must not determine timezone.

---


## TZ-010 — Country separation

Country/region must not be the sole timezone source because countries may contain multiple zones and users may travel.

---


## TZ-011 — Server clock discipline

Production hosts/workers must use synchronized clocks (NTP/managed equivalent) and UTC as server default where practical.

---


## TZ-012 — Database semantics

Use timezone-aware database semantics where supported (`TIMESTAMPTZ` or equivalent) and avoid naive datetime ambiguity.

---


## TZ-013 — API contract

Expose absolute timestamps using unambiguous ISO-8601/RFC3339-style values with `Z` or explicit offset.

---


## TZ-014 — User-facing rendering

Convert canonical instants into the resolved user timezone before display.

---


## TZ-015 — Locale formatting

Date/time formatting follows selected locale while timezone remains an independent preference.

---


## TZ-016 — Timezone clarity

Where time affects decisions, show clear timezone context/label.

---


## TZ-017 — Charts

Chart axes, crosshairs, candles, events and tooltips must use one explicit display timezone and never silently mix zones.

---


## TZ-018 — Market/source timestamps

Preserve source provenance and canonical event ordering; timezone localization is display-only.

---


## TZ-019 — AI outputs

AI-generated user-facing times use the resolved user timezone unless the user explicitly requests another timezone.

---


## TZ-020 — Notifications

Notification scheduling and displayed timestamps honor the user timezone; canonical event times remain UTC.

---


## TZ-021 — Email

Transactional/security/product emails containing times render in the intended user/account timezone and locale.

---


## TZ-022 — Reports and exports

Reports/exports clearly state timezone; machine-readable exports preserve canonical UTC timestamps and timezone metadata where needed.

---


## TZ-023 — Activity/security logs

User-visible activity/login history renders local time while audit evidence retains canonical UTC.

---


## TZ-024 — Billing

Billing dates/times localize display without changing provider authority, event order, billing-cycle semantics, or `USD_ONLY`.

---


## TZ-025 — Recurring schedules

Recurring local schedules store the intended IANA zone plus local wall-clock rule; do not model them as fixed UTC offsets.

---


## TZ-026 — DST fold/gap handling

Ambiguous/nonexistent local times must have deterministic documented behavior and tests.

---


## TZ-027 — Historical integrity

Changing a user's preferred timezone must never mutate historical canonical instants.

---


## TZ-028 — Auditability

Material timezone/scheduling preference changes and time-sensitive security actions should be auditable.

---


## TZ-029 — I18N integration

Reuse BLACKDARK's existing 38-locale i18n system; no parallel date/time localization subsystem.

---


## TZ-030 — Cross-surface coverage

Audit dashboards, Six Heroes, alerts, charts, tables, tooltips, reports, exports, emails, notifications, billing/profile/security pages, activity logs, user-facing APIs and AI outputs.

---


## TZ-031 — No naive datetime policy

Canonical time boundaries must reject or normalize naive datetimes; tests must detect accidental naive/local-time usage.

---


## TZ-032 — Timezone data updates

Use maintained IANA TZDB data so operators do not manually edit per-country clock rules.

---


## TZ-033 — Fallback behavior

If a timezone is invalid/unavailable, safely fall back to UTC for rendering and emit observability for correction.

---


## TZ-034 — Privacy

Timezone detection is a preference/context signal only; never treat it as exact physical location or identity proof.

---


## TZ-035 — Engineering acceptance

Do not claim engineering closure without repository-wide proof of UTC canon, IANA preference handling, automatic detection, manual override, DST-aware conversion, cross-surface localization and no known naive/ambiguous timestamp defects.

---


## TZ-036 — Live gate

Live readiness requires production evidence for clock sync, real browser detection, persistence, DST-sensitive conversion, representative notification/email behavior and cross-device behavior. Do not claim PASS_LIVE from local tests alone.

---
