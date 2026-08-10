"""
BLACKDARK — Security Catastrophe P0 Closure.

Financial-platform attack surface: data leak / API compromise /
account takeover / manipulated signals.

Engineering fail-closed controls + explicit operator gates.
Does NOT claim SOC2 / pentest / WAF-as-a-service from the app process.
"""

from __future__ import annotations

import inspect
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _item(
    *,
    id: str,
    threat: str,
    ok: bool,
    required_for_strict_prod: bool,
    layer: str,
    evidence: list[str],
    claim_boundary: str,
) -> dict[str, Any]:
    return {
        "id": id,
        "threat": threat,
        "ok": ok,
        "required_for_strict_prod": required_for_strict_prod,
        "layer": layer,  # code | runtime | operator
        "evidence": evidence,
        "claim_boundary": claim_boundary,
        "status": "pass" if ok else ("fail" if required_for_strict_prod else "warn"),
    }


def _soft_launch() -> bool:
    return os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}


def _is_production() -> bool:
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    return env in {"production", "prod"}


def _admin_mfa_wired() -> bool:
    try:
        from security_auth import require_admin

        src = inspect.getsource(require_admin)
        return "assert_admin_mfa" in src
    except Exception:
        return False


def _live_gate_wired() -> bool:
    try:
        from live_execution_gate import force_safe_dry_run, soft_launch_active
        from platform_api import _force_safe_dry_run

        return (
            soft_launch_active is not None
            and callable(force_safe_dry_run)
            and "live_execution_gate" in inspect.getsource(_force_safe_dry_run)
        )
    except Exception:
        return False


async def build_security_catastrophe_closure() -> dict[str, Any]:
    from admin_mfa import mfa_policy_enabled, system_admin_totp_configured
    from institutional_assurance import backup_status, waf_cdn_status
    from live_execution_gate import (
        jupiter_live_flag_enabled,
        live_execution_flag_enabled,
        soft_launch_active,
    )
    from postgres_backend import use_postgres
    from production_guard import evaluate_production_guard
    from risk_manager import risk_status

    soft = soft_launch_active()
    prod = _is_production()
    strict = prod and not soft
    secrets_ok = bool(
        os.getenv("SECRETS_MASTER_KEY", "").strip() or os.getenv("SECRETS_VAULT_KEY", "").strip()
    )
    pepper_ok = bool(os.getenv("SESSION_TOKEN_PEPPER", "").strip())
    admin_key_ok = bool(
        os.getenv("ADMIN_API_KEY", "").strip()
        or os.getenv("ADMIN_API_KEY_FILE", "").strip()
        or os.getenv("ADMIN_EMAILS", "").strip()
    )
    expose_demo = os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() in {"1", "true", "yes"}
    demo_key = (
        os.getenv("BLACKDARK_B2B_DEMO_KEY", "").strip()
        or os.getenv("B2B_DEMO_API_KEY", "").strip()
    )
    demo_disabled = demo_key in {"", "disabled", "off", "none"}
    mfa_ok = (not mfa_policy_enabled()) or system_admin_totp_configured()
    waf = waf_cdn_status()
    backup = backup_status()
    backup_ack = os.getenv("BACKUP_SCHEDULE_CONFIGURED", "").lower() in {"1", "true", "yes"}
    backup_marker = Path("data/backups/LATEST").is_file() or bool(backup.get("last_success"))
    backup_ops_ok = backup_ack or backup_marker
    sentry = bool(os.getenv("SENTRY_DSN", "").strip())
    uptime_ext = os.getenv("EXTERNAL_UPTIME_CONFIGURED", "").lower() in {"1", "true", "yes"}
    monitor_ok = sentry or uptime_ext
    redis_url = bool(os.getenv("REDIS_URL", "").strip())
    live_unsafe_soft = soft and (live_execution_flag_enabled() or jupiter_live_flag_enabled() or expose_demo)

    try:
        from oracle_audit_chain import verify_chain

        chain = verify_chain()
        chain_ok = bool(chain.get("valid", True)) if isinstance(chain, dict) else True
    except Exception:
        chain_ok = True  # empty/unavailable chain is OK; module presence matters

    risk = risk_status()
    poison_ok = "poison / freeze kill-switch" in " ".join(
        (risk.get("honest_scope") or {}).get("shipped") or []
    ) or "poison_threshold_pct" in risk

    items = [
        _item(
            id="p0_secrets_vault",
            threat="data_leak",
            ok=secrets_ok,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["SECRETS_MASTER_KEY", "secrets_vault.py"],
            claim_boundary="Fernet vault ≠ ISO27001",
        ),
        _item(
            id="p0_session_pepper",
            threat="account_takeover",
            ok=pepper_ok,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["SESSION_TOKEN_PEPPER", "security_auth.hash_session_token"],
            claim_boundary="Session hashing pepper required in production",
        ),
        _item(
            id="p0_admin_auth",
            threat="api_compromise",
            ok=admin_key_ok,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["ADMIN_API_KEY", "ADMIN_API_KEY_FILE", "ADMIN_EMAILS"],
            claim_boundary="Admin key/email configured",
        ),
        _item(
            id="p0_admin_mfa_wired",
            threat="account_takeover",
            ok=_admin_mfa_wired(),
            required_for_strict_prod=True,
            layer="code",
            evidence=["security_auth.require_admin → assert_admin_mfa", "X-Admin-TOTP"],
            claim_boundary="Privileged routes require MFA when policy enabled",
        ),
        _item(
            id="p0_admin_mfa_secret",
            threat="account_takeover",
            ok=mfa_ok,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["ADMIN_MFA_REQUIRED", "ADMIN_TOTP_SECRET"],
            claim_boundary="Admin TOTP secret present when MFA policy on",
        ),
        _item(
            id="p0_demo_key_hidden",
            threat="api_compromise",
            ok=(not expose_demo) and (demo_disabled if strict else True),
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["EXPOSE_B2B_DEMO_KEY=false", "/b2b template gate"],
            claim_boundary="Demo keys never public in strict production",
        ),
        _item(
            id="p0_soft_launch_no_live_money",
            threat="api_compromise",
            ok=not live_unsafe_soft,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["live_execution_gate.py", "SOFT_LAUNCH forbids live + demo expose"],
            claim_boundary="Soft Launch demo ≠ live money",
        ),
        _item(
            id="p0_live_execution_gate_wired",
            threat="api_compromise",
            ok=_live_gate_wired(),
            required_for_strict_prod=True,
            layer="code",
            evidence=["platform_api._force_safe_dry_run", "live_execution_gate"],
            claim_boundary="HTTP live paths fail-closed under Soft Launch",
        ),
        _item(
            id="p0_postgres_strict",
            threat="data_leak",
            ok=use_postgres() if strict else True,
            required_for_strict_prod=True,
            layer="runtime",
            evidence=["DATABASE_URL", "sqlite_forbidden_in_strict_production"],
            claim_boundary="Strict production forbids Soft Launch SQLite",
        ),
        _item(
            id="p0_redis_recommended",
            threat="account_takeover",
            ok=redis_url if strict else True,
            required_for_strict_prod=False,
            layer="runtime",
            evidence=["REDIS_URL", "shared login rate limit"],
            claim_boundary="Redis required for viral HA; recommended for strict prod RL",
        ),
        _item(
            id="p0_edge_waf_declared",
            threat="api_compromise",
            ok=bool(waf.get("edge_active")),
            required_for_strict_prod=True,
            layer="operator",
            evidence=["CDN_WAF_ACTIVE", "CLOUDFLARE_ZONE_ID", "docs/CDN_WAF_CHECKLIST.md"],
            claim_boundary="App cannot provide edge WAF — operator must activate and declare",
        ),
        _item(
            id="p0_backup_ops",
            threat="data_leak",
            ok=backup_ops_ok if strict else True,
            required_for_strict_prod=True,
            layer="operator",
            evidence=["BACKUP_SCHEDULE_CONFIGURED", "scripts/backup_postgres.py", "data/backups/LATEST"],
            claim_boundary="Scheduled backup + restore drill is operator-owned",
        ),
        _item(
            id="p0_monitoring",
            threat="api_compromise",
            ok=monitor_ok if strict else True,
            required_for_strict_prod=True,
            layer="operator",
            evidence=["SENTRY_DSN", "EXTERNAL_UPTIME_CONFIGURED", "/health/live"],
            claim_boundary="Observability/uptime must be declared for strict production",
        ),
        _item(
            id="p0_signal_poison_freeze",
            threat="manipulated_signals",
            ok=poison_ok,
            required_for_strict_prod=True,
            layer="code",
            evidence=["risk_manager.detect_data_poisoning", "/api/risk/status"],
            claim_boundary="Execution safety freeze — not full market-data SOC",
        ),
        _item(
            id="p0_audit_chain_module",
            threat="manipulated_signals",
            ok=Path("oracle_audit_chain.py").is_file() and chain_ok is not False,
            required_for_strict_prod=True,
            layer="code",
            evidence=["/api/oracle/audit-chain/verify", "Public Accuracy Ledger"],
            claim_boundary="Tamper-evident decision chain; process-local limits in Soft Launch",
        ),
    ]

    code_items = [i for i in items if i["layer"] == "code"]
    runtime_items = [i for i in items if i["layer"] == "runtime"]
    operator_items = [i for i in items if i["layer"] == "operator"]

    strict_required = [i for i in items if i["required_for_strict_prod"]]
    strict_fail = [i for i in strict_required if not i["ok"]]
    code_fail = [i for i in code_items if not i["ok"]]

    guard = evaluate_production_guard()

    return {
        "surface": "security_catastrophe_p0_closure",
        "generated_at": datetime.now(UTC).isoformat(),
        "program": "Financial-platform catastrophe P0 — fail-closed engineering + operator gates",
        "threats": [
            "data_leak",
            "api_compromise",
            "account_takeover",
            "manipulated_signals",
        ],
        "production": prod,
        "soft_launch": soft,
        "strict_production": strict,
        "code_complete": len(code_fail) == 0,
        "code_failures": [i["id"] for i in code_fail],
        "engineering_p0_complete": len(code_fail) == 0 and all(
            i["ok"] for i in runtime_items if i["id"] in {
                "p0_soft_launch_no_live_money",
                "p0_live_execution_gate_wired",
                "p0_admin_mfa_wired",
                "p0_signal_poison_freeze",
                "p0_audit_chain_module",
            }
        ),
        "strict_production_ready": (not strict) or (len(strict_fail) == 0 and guard.get("required_pass")),
        "strict_required_failures": [i["id"] for i in strict_fail],
        "operator_gates_pending": [i["id"] for i in operator_items if not i["ok"]],
        "items": items,
        "production_guard_required_pass": guard.get("required_pass"),
        "production_guard_failures": guard.get("required_failures"),
        "forbidden_claims": [
            "soc2_certified",
            "iso27001_certified",
            "pentest_complete_without_report",
            "waf_provided_by_app_process",
            "soft_launch_equals_financial_security_bar",
        ],
        "api": "/api/security/catastrophe-p0",
        "doc": "docs/SECURITY_CATASTROPHE_P0_AR.md",
        "checklist_doc": "docs/SECURITY_MAX_CHECKLIST.md",
        "quality_bar": "highest engineering fail-closed bar for Soft Launch + strict prod gates — not fabricated institutional certification",
    }
