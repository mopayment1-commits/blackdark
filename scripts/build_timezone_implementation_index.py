#!/usr/bin/env python3
"""Build TIMEZONE implementation index bindings TZ-001 → TZ-036."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINDINGS = {
    "TZ-001": {"reuse": "BUILD", "module_paths": ["timezone/canonical.py", "database.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Canonical internal time"},
    "TZ-002": {"reuse": "BUILD", "module_paths": ["timezone/iana.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "IANA time zones"},
    "TZ-003": {"reuse": "BUILD", "module_paths": ["static/js/bd_time.js", "api/routers/auth.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Automatic detection"},
    "TZ-004": {"reuse": "BUILD", "module_paths": ["timezone/resolver.py", "timezone/request_context.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Preference precedence"},
    "TZ-005": {"reuse": "REUSE", "module_paths": ["database.py", "auth_service.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Persistence"},
    "TZ-006": {"reuse": "IMPROVE", "module_paths": ["templates/profile.html", "api/routers/auth.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Manual override"},
    "TZ-007": {"reuse": "BUILD", "module_paths": ["timezone/resolver.py", "templates/profile.html"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Travel/device mismatch"},
    "TZ-008": {"reuse": "BUILD", "module_paths": ["timezone/format.py", "timezone/dst.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "DST correctness"},
    "TZ-009": {"reuse": "BUILD", "module_paths": ["timezone/resolver.py", "i18n_enforcement.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Language separation"},
    "TZ-010": {"reuse": "BUILD", "module_paths": ["timezone/resolver.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Country separation"},
    "TZ-011": {"reuse": "BUILD", "module_paths": ["timezone/server_discipline.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Server clock discipline", "notes": "Production NTP sync is LIVE_GATED"},
    "TZ-012": {"reuse": "IMPROVE", "module_paths": ["timezone/canonical.py", "database.py", "blackdark/data/models.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Database semantics"},
    "TZ-013": {"reuse": "BUILD", "module_paths": ["timezone/canonical.py", "api/routers/timezone.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "API contract"},
    "TZ-014": {"reuse": "BUILD", "module_paths": ["timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "User-facing rendering"},
    "TZ-015": {"reuse": "IMPROVE", "module_paths": ["i18n_enforcement.py", "timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Locale formatting"},
    "TZ-016": {"reuse": "BUILD", "module_paths": ["timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Timezone clarity"},
    "TZ-017": {"reuse": "IMPROVE", "module_paths": ["static/js/bd_time.js", "templates/dashboard.html"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Charts"},
    "TZ-018": {"reuse": "BUILD", "module_paths": ["timezone/market.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Market/source timestamps"},
    "TZ-019": {"reuse": "IMPROVE", "module_paths": ["timezone/format.py", "i18n_enforcement.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "AI outputs"},
    "TZ-020": {"reuse": "IMPROVE", "module_paths": ["timezone/format.py", "alert_service.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Notifications"},
    "TZ-021": {"reuse": "IMPROVE", "module_paths": ["identity/security_notifications.py", "timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Email"},
    "TZ-022": {"reuse": "IMPROVE", "module_paths": ["gdpr_service.py", "timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Reports and exports"},
    "TZ-023": {"reuse": "IMPROVE", "module_paths": ["api/routers/auth.py", "timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Activity/security logs"},
    "TZ-024": {"reuse": "IMPROVE", "module_paths": ["timezone/format.py", "billing/subscription_engine.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Billing"},
    "TZ-025": {"reuse": "BUILD", "module_paths": ["timezone/schedule.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Recurring schedules"},
    "TZ-026": {"reuse": "BUILD", "module_paths": ["timezone/dst.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "DST fold/gap handling"},
    "TZ-027": {"reuse": "BUILD", "module_paths": ["timezone/format.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Historical integrity"},
    "TZ-028": {"reuse": "BUILD", "module_paths": ["timezone/audit.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Auditability"},
    "TZ-029": {"reuse": "REUSE", "module_paths": ["i18n_enforcement.py", "timezone/format.py"], "test_paths": ["tests/test_i18n_38_locales.py", "tests/test_timezone_p0_test_matrix.py"], "title": "I18N integration"},
    "TZ-030": {"reuse": "BUILD", "module_paths": ["timezone/surface_registry.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Cross-surface coverage"},
    "TZ-031": {"reuse": "BUILD", "module_paths": ["timezone/canonical.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "No naive datetime policy"},
    "TZ-032": {"reuse": "REUSE", "module_paths": ["timezone/iana.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Timezone data updates"},
    "TZ-033": {"reuse": "BUILD", "module_paths": ["timezone/iana.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Fallback behavior"},
    "TZ-034": {"reuse": "BUILD", "module_paths": ["timezone/resolver.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Privacy"},
    "TZ-035": {"reuse": "BUILD", "module_paths": ["bd_platform/timezone_source_driven_engineering.py"], "test_paths": ["tests/test_timezone_p0_test_matrix.py"], "title": "Engineering acceptance"},
    "TZ-036": {"reuse": "BUILD", "module_paths": ["timezone/server_discipline.py"], "test_paths": [], "title": "Live gate", "notes": "Requires live production evidence"},
}


def main() -> None:
    payload = {
        "schema_version": "1.0",
        "spec_file": "docs/BLACKDARK_GLOBAL_TIME_TIMEZONE_SPEC_v1.md",
        "bindings": BINDINGS,
    }
    out = ROOT / "docs" / "TIMEZONE_IMPLEMENTATION_INDEX.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
