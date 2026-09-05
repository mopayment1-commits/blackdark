"""
DDoS Protection Layer — Sprint 0 infrastructure (#1047).

NOT standalone. Network + transport layer protection (CDN/cloud edge) combined
with WAF + Security Rate Limiting (#1046) for layered defense.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_FEATURE = "ddos_protection_layer"
_SEED_PATH = Path("data/ddos_protection_seed.json")
_AUDIT_PATH = Path("data/ddos_attack_audit.jsonl")

_RL_REF = 1046
_INCIDENT_REF = 1017
_DR_REF = 1016


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("ddos_protection_layer") or {}


def record_ddos_event(
    *,
    attack_type: str,
    source_ips: list[str],
    mitigation: str,
    impact: str = "",
) -> dict[str, Any]:
    entry = {
        "ts": time.time(),
        "iso": _utcnow(),
        "feature": _FEATURE,
        "attack_type": attack_type,
        "source_ips": source_ips[:50],
        "mitigation": mitigation,
        "impact": impact,
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass
    trigger_ddos_incident(entry)
    return entry


def trigger_ddos_incident(event: dict[str, Any]) -> dict[str, Any]:
    try:
        from security_events import record_security_event

        record_security_event(
            "ddos_attack_detected",
            severity="critical",
            actor="ddos_protection_layer",
            detail={
                "attack_type": event.get("attack_type"),
                "mitigation": event.get("mitigation"),
                "playbook": "forensics_postmortem_source_analysis",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass
    return {"triggered": True, "integration_ref": _INCIDENT_REF}


def ddos_protection_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    edge: dict[str, Any] = {}
    try:
        from institutional_assurance import waf_cdn_status

        edge = waf_cdn_status()
    except ImportError:
        pass

    nginx_ok = Path("nginx/blackdark.conf").is_file()
    cf_rules = Path("deploy/cloudflare/waf-rules.json").is_file()
    edge_active = bool(
        edge.get("edge_active")
        or os.getenv("CDN_WAF_ACTIVE", "").lower() in {"1", "true", "yes"}
    )

    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy_version": policy.get("policy_version", "1.0.0"),
        "network_layer": policy.get("network_layer") or {},
        "application_layer": policy.get("application_layer") or {},
        "origin_hardening": policy.get("origin_hardening") or {},
        "failover": policy.get("failover") or {},
        "defense_sequence": policy.get("defense_sequence") or [],
        "integrations": policy.get("integrations") or {},
        "edge": edge,
        "edge_active": edge_active,
        "templates": {
            "cloudflare_waf": str(Path("deploy/cloudflare/waf-rules.json")),
            "nginx_origin": str(Path("nginx/blackdark.conf")),
            "checklist": "docs/CDN_WAF_CHECKLIST.md",
        },
        "templates_present": {"nginx": nginx_ok, "cloudflare_rules": cf_rules},
        "audit_path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def check_ddos_protection_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    status = ddos_protection_status(seed=seed)
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}

    checks = {
        "waf_template_present": status["templates_present"].get("cloudflare_rules", False),
        "nginx_origin_hardening": status["templates_present"].get("nginx", False),
        "network_layer_documented": bool((policy.get("network_layer") or {}).get("volumetric_absorption")),
        "waf_l7_documented": (policy.get("application_layer") or {}).get("waf_enabled") is True,
        "rate_limit_integration": (policy.get("integrations") or {}).get("rate_limiting_ref") == _RL_REF,
        "failover_documented": (policy.get("failover") or {}).get("auto_failover_secondary_region") is True,
        "dr_integration": (policy.get("integrations") or {}).get("backup_dr_ref") == _DR_REF,
        "incident_integration": (policy.get("integrations") or {}).get("incident_response_ref") == _INCIDENT_REF,
        "audit_retention": policy.get("audit_retention_days", 0) >= 90,
        # Edge activation required in strict production; templates OK for soft launch
        "edge_or_soft_launch": status["edge_active"] or soft or not _is_production(),
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "edge_active": status["edge_active"],
        "timestamp": _utcnow(),
    }


def _is_production() -> bool:
    try:
        from security_auth import is_production_env

        return is_production_env()
    except ImportError:
        return os.getenv("ENV", "").lower() in {"production", "prod"}


def run_ddos_protection_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = ddos_protection_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "defense_sequence", "passed": len(status["defense_sequence"]) >= 4})
    checks.append({"id": "rate_limit_ref", "passed": status["integrations"].get("rate_limiting_ref") == _RL_REF})
    checks.append({"id": "waf_template", "passed": status["templates_present"].get("cloudflare_rules", False)})
    checks.append({"id": "nginx_template", "passed": status["templates_present"].get("nginx", False)})
    gate = check_ddos_protection_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})
    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
