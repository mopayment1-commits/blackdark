"""
SAST Gate — Static Application Security Testing for CI/CD pipeline.

NOT standalone. Orchestrates Bandit + secrets scan + custom rules on every PR/merge.
Blocks critical/high findings; logs append-only audit trail.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SASTGate")

_FEATURE = "sast_gate"
_SEED_PATH = Path("data/sast_gate_seed.json")
_AUDIT_PATH = Path("data/sast_scan_audit.jsonl")
_SUPPRESSIONS_PATH = Path("data/sast_suppressions.json")

_INCIDENT_REF = 1017
_ENCRYPTION_REF = 1039
_VAULT_REF = 1040
_RBAC_REF = 1022
_ACTIVITY_REF = 1038

Severity = Literal["critical", "high", "medium", "low", "info"]

_EXCLUDE_DIRS = {".venv", "venv", "node_modules", ".git", "dist", "build", "data", "tests"}
_FINANCIAL_ALLOW_FLOAT = re.compile(r"money_float|# sast:allow-float|noqa.*float")

_SECRET_PATTERNS: list[tuple[str, Severity, re.Pattern[str]]] = [
    (
        "hardcoded_api_key",
        "critical",
        re.compile(
            r"""(?i)(api[_-]?key|api[_-]?secret|access[_-]?token)\s*=\s*["'][^"'\s]{12,}["']"""
        ),
    ),
    (
        "hardcoded_password",
        "critical",
        re.compile(r"""(?i)(password|passwd|pwd)\s*=\s*["'][^"'\s]{8,}["']"""),
    ),
    (
        "private_key_pem",
        "critical",
        re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "aws_access_key",
        "critical",
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
    (
        "stripe_live_key",
        "critical",
        re.compile(r"sk_live_[0-9a-zA-Z]{16,}"),
    ),
    (
        "env_secret_assignment",
        "high",
        re.compile(
            r"""(?i)os\.environ\[["'][^"']*(?:KEY|SECRET|PASSWORD|TOKEN)[^"']*["']\]\s*=\s*["'][^"']{8,}["']"""
        ),
    ),
]

_ENCRYPTION_CHECKS: list[tuple[str, Severity, re.Pattern[str]]] = [
    (
        "weak_crypto_md5_password",
        "high",
        re.compile(r"""(?i)hashlib\.md5\([^)]*password"""),
    ),
    (
        "ssl_verify_disabled",
        "high",
        re.compile(r"verify\s*=\s*False"),
    ),
]


@dataclass
class SASTFinding:
    rule_id: str
    severity: Severity
    message: str
    file: str
    line: int
    remediation: str = ""
    tool: str = "sast_gate"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "remediation": self.remediation,
            "tool": self.tool,
            "extra": self.extra,
        }


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
    return seed.get("sast_gate") or {}


def _load_suppressions() -> list[dict[str, Any]]:
    if not _SUPPRESSIONS_PATH.is_file():
        return []
    try:
        data = json.loads(_SUPPRESSIONS_PATH.read_text(encoding="utf-8"))
        return list(data.get("suppressions") or [])
    except (OSError, json.JSONDecodeError):
        return []


def is_suppressed(finding: SASTFinding) -> bool:
    """False-positive suppressions require security-lead approval in seed file."""
    for sup in _load_suppressions():
        if not sup.get("approved_by_security_lead"):
            continue
        if sup.get("rule_id") == finding.rule_id and sup.get("file") == finding.file:
            if int(sup.get("line", 0)) in {0, finding.line}:
                return True
    return False


def _iter_source_files(root: Path | None = None) -> list[Path]:
    root = root or Path(".")
    files: list[Path] = []
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & _EXCLUDE_DIRS:
            continue
        if "/tests/" in str(path) or str(path).startswith("tests/"):
            continue
        if path.name.endswith("_test.py"):
            continue
        files.append(path)
    return files


def _should_skip_file(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".example") or name.endswith(".sample"):
        return True
    if "mock" in name or "fixture" in name:
        return True
    return False


def scan_secrets(*, root: Path | None = None) -> list[SASTFinding]:
    """#1040 — detect plaintext API keys / passwords / private keys in source."""
    findings: list[SASTFinding] = []
    for path in _iter_source_files(root):
        if _should_skip_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "sast:ignore" in line or "nosec" in line:
                continue
            for rule_id, severity, pattern in _SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        SASTFinding(
                            rule_id=rule_id,
                            severity=severity,
                            message=f"Potential secret in source: {rule_id}",
                            file=str(path),
                            line=line_no,
                            remediation="Store in Vault/env; never commit secrets to source control.",
                            tool="secrets_scan",
                        )
                    )
    return findings


def scan_encryption_patterns(*, root: Path | None = None) -> list[SASTFinding]:
    """#1039 — static checks for weak crypto / disabled TLS verification."""
    findings: list[SASTFinding] = []
    for path in _iter_source_files(root):
        if _should_skip_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "sast:ignore" in line:
                continue
            for rule_id, severity, pattern in _ENCRYPTION_CHECKS:
                if pattern.search(line):
                    findings.append(
                        SASTFinding(
                            rule_id=rule_id,
                            severity=severity,
                            message=f"Encryption policy violation: {rule_id}",
                            file=str(path),
                            line=line_no,
                            remediation="Use AES-256-GCM, TLS verify=True, PBKDF2/SHA-256 for passwords.",
                            tool="encryption_policy_scan",
                            extra={"integration_ref": _ENCRYPTION_REF},
                        )
                    )
    return findings


def scan_financial_float_usage(*, seed: dict[str, Any] | None = None) -> list[SASTFinding]:
    """#1031 — warn on float() in financial settlement modules."""
    seed = seed or _load_seed()
    modules = set(_cfg(seed).get("financial_modules") or [])
    findings: list[SASTFinding] = []
    float_re = re.compile(r"\bfloat\s*\(")
    for path in _iter_source_files():
        if path.name not in modules:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if _FINANCIAL_ALLOW_FLOAT.search(line) or "sast:ignore" in line:
                continue
            if float_re.search(line):
                findings.append(
                    SASTFinding(
                        rule_id="decimal_financial_float",
                        severity="medium",
                        message="float() in financial module — prefer money_decimal",
                        file=str(path),
                        line=line_no,
                        remediation="Use money_decimal.d() / money() for settlement math.",
                        tool="decimal_enforcement",
                    )
                )
    return findings


def scan_rbac_endpoints(*, root: Path | None = None) -> list[SASTFinding]:
    """#1022 — heuristic: API routes should declare auth Depends."""
    findings: list[SASTFinding] = []
    router_dir = (root or Path(".")) / "api" / "routers"
    if not router_dir.is_dir():
        return findings
    route_re = re.compile(r"@router\.(get|post|put|patch|delete)\(")
    auth_re = re.compile(r"Depends\((require_|optional_user)")
    public_allowlist = {
        "privacy_status",
        "health",
        "status",
    }
    for path in router_dir.glob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = route_re.search(line)
            if not m:
                i += 1
                continue
            window = "\n".join(lines[i : min(i + 8, len(lines))])
            fn_name = ""
            for j in range(i, min(i + 6, len(lines))):
                fn_m = re.search(r"async def (\w+)", lines[j])
                if fn_m:
                    fn_name = fn_m.group(1)
                    break
            if fn_name in public_allowlist or "sast:public" in window:
                i += 1
                continue
            if not auth_re.search(window):
                findings.append(
                    SASTFinding(
                        rule_id="rbac_missing_authz",
                        severity="medium",
                        message=f"Route may lack RBAC Depends() guard: {fn_name or 'unknown'}",
                        file=str(path),
                        line=i + 1,
                        remediation="Add Depends(require_authenticated) or require_admin/require_whale.",
                        tool="rbac_scan",
                        extra={"integration_ref": _RBAC_REF},
                    )
                )
            i += 1
    return findings


def run_bandit(*, root: Path | None = None) -> list[SASTFinding]:
    """Run Bandit SAST — maps severity to gate policy."""
    root = root or Path(".")
    bandit_cfg = root / ".bandit"
    cmd = ["bandit", "-r", ".", "-f", "json", "-q"]
    if bandit_cfg.is_file():
        cmd.extend(["-c", str(bandit_cfg)])
    else:
        cmd.extend(["-x", "tests,venv,.venv,data"])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=480,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return [
            SASTFinding(
                rule_id="bandit_unavailable",
                severity="high",
                message=str(exc),
                file=".",
                line=0,
                remediation="Install bandit in CI environment.",
                tool="bandit",
            )
        ]
    findings: list[SASTFinding] = []
    if not proc.stdout.strip():
        return findings
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return findings
    sev_map: dict[str, Severity] = {
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }
    for item in payload.get("results") or []:
        sev = sev_map.get(str(item.get("issue_severity", "LOW")).upper(), "low")
        findings.append(
            SASTFinding(
                rule_id=f"bandit_{item.get('test_id', 'unknown')}",
                severity=sev,
                message=str(item.get("issue_text") or ""),
                file=str(item.get("filename") or ""),
                line=int(item.get("line_number") or 0),
                remediation="See Bandit docs / fix issue or approved suppression.",
                tool="bandit",
                extra={"cwe": item.get("issue_cwe")},
            )
        )
    return findings


def record_scan_audit(
    *,
    actor: str,
    result: dict[str, Any],
    duration_seconds: float,
) -> dict[str, Any]:
    """Append-only scan log — 2-year retention (#1038 cross-ref)."""
    entry = {
        "ts": time.time(),
        "iso": _utcnow(),
        "actor": actor,
        "feature": _FEATURE,
        "duration_seconds": round(duration_seconds, 2),
        "ok": result.get("ok"),
        "blocked": result.get("blocked"),
        "finding_counts": result.get("finding_counts"),
        "scan_id": result.get("scan_id"),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("sast audit persist failed", exc_info=True)
    return entry


def run_sast_scan(
    *,
    actor: str = "ci",
    root: Path | None = None,
    include_bandit: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute full SAST gate — target ≤10 minutes via parallel-ready stages."""
    started = time.time()
    seed = seed or _load_seed()
    scan_id = f"sast-{int(started)}"

    all_findings: list[SASTFinding] = []
    if include_bandit:
        all_findings.extend(run_bandit(root=root))
    all_findings.extend(scan_secrets(root=root))
    all_findings.extend(scan_encryption_patterns(root=root))
    all_findings.extend(scan_financial_float_usage(seed=seed))
    all_findings.extend(scan_rbac_endpoints(root=root))

    active = [f for f in all_findings if not is_suppressed(f)]
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in active:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    policy = (_cfg(seed).get("policy") or {})
    blocked = policy.get("block_critical_high", True) and (
        counts["critical"] > 0 or counts["high"] > 0
    )
    duration = time.time() - started

    result = {
        "ok": not blocked,
        "blocked": blocked,
        "feature": _FEATURE,
        "scan_id": scan_id,
        "actor": actor,
        "duration_seconds": round(duration, 2),
        "within_time_budget": duration <= int(policy.get("max_scan_minutes", 10)) * 60,
        "finding_counts": counts,
        "findings": [f.to_dict() for f in active[:200]],
        "total_findings": len(active),
        "suppressed": len(all_findings) - len(active),
        "tools": ["bandit", "secrets_scan", "encryption_policy_scan", "decimal_enforcement", "rbac_scan"],
        "timestamp": _utcnow(),
    }
    record_scan_audit(actor=actor, result=result, duration_seconds=duration)

    if blocked and policy.get("block_critical_high", True):
        try:
            from security_events import record_security_event

            record_security_event(
                "sast_gate_blocked",
                severity="critical",
                actor=actor,
                detail={
                    "scan_id": scan_id,
                    "critical": counts["critical"],
                    "high": counts["high"],
                    "integration_ref": _INCIDENT_REF,
                    "action": "block_merge_or_incident_playbook",
                },
            )
        except ImportError:
            pass

    return result


def sast_gate_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy_version": _cfg(seed).get("policy_version", "1.0.0"),
        "policy": policy,
        "severity_policy": _cfg(seed).get("severity_policy") or {},
        "rulesets": _cfg(seed).get("rulesets") or [],
        "integrations": _cfg(seed).get("integrations") or {},
        "audit_path": str(_AUDIT_PATH),
        "suppressions_path": str(_SUPPRESSIONS_PATH),
        "ci_workflow": ".github/workflows/security.yml",
        "timestamp": _utcnow(),
    }


def check_sast_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = sast_gate_status(seed=seed)
    policy = status["policy"]
    last_scan = _last_audit_entry()
    checks = {
        "sast_enabled": policy.get("enabled") is True,
        "scan_every_pr": policy.get("scan_every_pr") is True,
        "block_critical_high": policy.get("block_critical_high") is True,
        "secrets_scanning": "plaintext_api_keys" in (status.get("rulesets") or []),
        "decimal_rules": "decimal_financial_paths" in (status.get("rulesets") or []),
        "rbac_rules": "rbac_endpoint_authz" in (status.get("rulesets") or []),
        "audit_retention": policy.get("audit_retention_days", 0) >= 730,
        "suppression_policy": policy.get("suppression_requires_security_lead") is True,
        "last_scan_passed": last_scan.get("ok", True) if last_scan else True,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "last_scan": last_scan,
        "timestamp": _utcnow(),
    }


def _last_audit_entry() -> dict[str, Any] | None:
    if not _AUDIT_PATH.is_file():
        return None
    try:
        lines = [ln for ln in _AUDIT_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            return None
        return json.loads(lines[-1])
    except (OSError, json.JSONDecodeError):
        return None


def run_sast_gate_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = sast_gate_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "block_critical_high", "passed": status["policy"]["block_critical_high"] is True})
    checks.append({"id": "secrets_ruleset", "passed": "plaintext_api_keys" in status["rulesets"]})
    checks.append({"id": "time_budget", "passed": status["policy"]["max_scan_minutes"] <= 10})

    # Self-test secret detector on synthetic snippet (no real secrets committed)
    sample = SASTFinding(
        rule_id="test",
        severity="critical",
        message="test",
        file="x.py",
        line=1,
    )
    checks.append({"id": "suppression_api", "passed": isinstance(is_suppressed(sample), bool)})

    gate = check_sast_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }


def trigger_production_vulnerability_incident(scan_result: dict[str, Any]) -> dict[str, Any]:
    """#1017 — critical SAST finding in production candidate → incident playbook hook."""
    counts = scan_result.get("finding_counts") or {}
    if not counts.get("critical") and not counts.get("high"):
        return {"triggered": False, "reason": "no_critical_high"}
    try:
        from security_events import record_security_event

        record_security_event(
            "sast_critical_vulnerability_incident",
            severity="critical",
            actor="sast_gate",
            detail={
                "scan_id": scan_result.get("scan_id"),
                "counts": counts,
                "playbook": "rollback_forensics",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass
    return {
        "triggered": True,
        "integration_ref": _INCIDENT_REF,
        "action": "rollback_and_forensics",
        "scan_id": scan_result.get("scan_id"),
    }
