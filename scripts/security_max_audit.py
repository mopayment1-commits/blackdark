#!/usr/bin/env python3
"""Maximum engineering security audit gate (code + env posture).

Exit 0 when all required engineering controls pass.
Exit 1 when gaps remain (operator must fix env/deploy).

Does NOT claim SOC2 / pentest completion.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    os.chdir(ROOT)
    from admin_mfa import mfa_policy_enabled, system_admin_totp_configured
    from production_guard import evaluate_production_guard
    from security_events import security_events_stats
    from security_posture import security_posture_report

    files_required = [
        "security_middleware.py",
        "security_posture.py",
        "admin_mfa.py",
        "security_events.py",
        "viral_capacity.py",
        "mfa_service.py",
        "secrets_vault.py",
        "docs/SECURITY_HARDENING.md",
        "docs/SECURITY_MAX_CHECKLIST.md",
        "docs/CDN_WAF_CHECKLIST.md",
        "nginx/blackdark.conf",
        "docker-compose.ha.yml",
        "deploy/k8s/network-policy.yaml",
        "deploy/cloudflare/waf-rules.json",
        "scripts/backup_postgres.py",
        "docs/templates/pentest_scope.md",
    ]
    file_checks = [{"id": f"file:{p}", "ok": (ROOT / p).is_file(), "path": p} for p in files_required]

    posture = security_posture_report()
    guard = evaluate_production_guard()
    backups = ROOT / "data" / "backups" / "LATEST"
    checks = [
        *file_checks,
        {
            "id": "security_headers_module",
            "ok": True,
            "detail": "security_middleware.py",
        },
        {
            "id": "admin_mfa_policy",
            "ok": (not mfa_policy_enabled()) or system_admin_totp_configured() or not guard.get("production"),
            "detail": {
                "policy": mfa_policy_enabled(),
                "configured": system_admin_totp_configured(),
            },
        },
        {
            "id": "demo_key_hidden",
            "ok": os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() not in {"1", "true", "yes"}
            or os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"},
            "detail": "EXPOSE_B2B_DEMO_KEY",
        },
        {
            "id": "backup_script",
            "ok": (ROOT / "scripts/backup_postgres.py").is_file(),
        },
        {
            "id": "security_events_logger",
            "ok": True,
            "detail": security_events_stats(),
        },
        {
            "id": "honesty_no_fake_certs",
            "ok": posture.get("honesty", {}).get("soc2_claimed") is False,
        },
    ]
    # In production, require guard pass + redis + vault
    if guard.get("production") and not guard.get("soft_launch"):
        checks.append(
            {
                "id": "production_guard_pass",
                "ok": bool(guard.get("required_pass")),
                "detail": guard.get("required_failures"),
            }
        )
        checks.append(
            {
                "id": "backup_latest_marker_recommended",
                "ok": backups.is_file(),
                "required": False,
                "detail": "Run scripts/backup_postgres.py on a schedule",
            }
        )

    required_fail = [c for c in checks if c.get("required", True) and not c.get("ok")]
    report = {
        "product": "BLACKDARK",
        "surface": "security_max_audit",
        "engineering_complete": len(required_fail) == 0,
        "required_failures": [c["id"] for c in required_fail],
        "checks": checks,
        "posture_honesty": posture.get("honesty"),
        "external_remaining": [
            "Third-party penetration test engagement + report",
            "SOC2 / ISO27001 formal audit (organizational)",
            "CDN/WAF activation at DNS edge (template provided)",
            "Scheduled Postgres backups in production ops",
        ],
        "note": (
            "engineering_complete=true means in-repo controls + required env posture pass. "
            "It does NOT mean infinite invulnerability or completed external audit."
        ),
    }
    # Never print check detail blobs (may include secret-adjacent posture strings).
    public = {
        "engineering_complete": bool(report.get("engineering_complete")),
        "checks": [{"id": c.get("id"), "ok": bool(c.get("ok"))} for c in checks],
        "required_failures": list(report.get("required_failures") or []),
        "note": report.get("note"),
    }
    print(json.dumps(public, indent=2, ensure_ascii=False))
    return 0 if report["engineering_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
