"""
Dependency & SBOM Scanning Gate — CI/CD supply chain security.

NOT standalone. Third pillar: SAST (#1042) + DAST (#1043) + Dependency Scanning.
Blocks critical/high CVEs; generates CycloneDX SBOM + license inventory per release.
"""

from __future__ import annotations

import hashlib
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

logger = logging.getLogger("BLACKDARK.DependencyScanGate")

_FEATURE = "dependency_scan_gate"
_SEED_PATH = Path("data/dependency_scan_seed.json")
_AUDIT_PATH = Path("data/dependency_scan_audit.jsonl")
_SUPPRESSIONS_PATH = Path("data/dependency_scan_suppressions.json")

_SAST_REF = 1042
_DAST_REF = 1043
_INCIDENT_REF = 1017
_IMMUTABLE_REF = 1029
_ACTIVITY_REF = 1038

Severity = Literal["critical", "high", "medium", "low", "info"]

_HASH_LINE = re.compile(r"--hash\s*=\s*sha256:", re.I)
_PINNED_LINE = re.compile(r"^[A-Za-z0-9_.\-]+==[0-9]", re.M)
_SOURCE_MANIFESTS = {"requirements.txt"}


@dataclass
class DependencyFinding:
    rule_id: str
    severity: Severity
    message: str
    dependency: str
    version: str = ""
    cve_id: str = ""
    cvss_score: float | None = None
    remediation: str = ""
    tool: str = "dependency_scan_gate"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "dependency": self.dependency,
            "version": self.version,
            "cve_id": self.cve_id,
            "cvss_score": self.cvss_score,
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
    return seed.get("dependency_scan_gate") or {}


def _load_suppressions() -> list[dict[str, Any]]:
    if not _SUPPRESSIONS_PATH.is_file():
        return []
    try:
        data = json.loads(_SUPPRESSIONS_PATH.read_text(encoding="utf-8"))
        return list(data.get("suppressions") or [])
    except (OSError, json.JSONDecodeError):
        return []


def is_suppressed(finding: DependencyFinding) -> bool:
    for sup in _load_suppressions():
        if not sup.get("approved_by_security_lead"):
            continue
        if finding.cve_id and sup.get("cve_id") == finding.cve_id:
            if sup.get("dependency") in {finding.dependency, "*"}:
                return True
    return False


def _cvss_to_severity(score: float | None) -> Severity:
    if score is None:
        return "high"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def _extract_cvss(vuln: dict[str, Any]) -> float | None:
    for key in ("cvss_score", "cvss"):
        raw = vuln.get(key)
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                pass
    # OSV-style nested severity
    for sev in vuln.get("severity") or []:
        if isinstance(sev, dict) and sev.get("type") == "CVSS_V3":
            try:
                return float(sev.get("score"))
            except (TypeError, ValueError):
                pass
    return None


def _cve_id_from_vuln(vuln: dict[str, Any]) -> str:
    aliases = vuln.get("aliases") or []
    for alias in aliases:
        if str(alias).upper().startswith("CVE-"):
            return str(alias)
    vid = str(vuln.get("id") or "")
    return vid or "UNKNOWN-CVE"


def run_pip_audit(
    *,
    requirements_path: Path | None = None,
) -> list[DependencyFinding]:
    """pip-audit on hash-locked requirements tree."""
    req = requirements_path or Path("requirements.hashes.txt")
    if not req.is_file():
        return [
            DependencyFinding(
                rule_id="missing_requirements_file",
                severity="critical",
                message=f"Missing requirements file: {req}",
                dependency="*",
                remediation="Maintain requirements.hashes.txt with pinned hashes.",
                tool="pip_audit",
            )
        ]
    try:
        proc = subprocess.run(
            ["pip-audit", "-r", str(req), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return [
            DependencyFinding(
                rule_id="pip_audit_unavailable",
                severity="high",
                message=str(exc),
                dependency="*",
                remediation="Install pip-audit in CI.",
                tool="pip_audit",
            )
        ]
    if proc.returncode not in {0, 1} and not proc.stdout.strip():
        return [
            DependencyFinding(
                rule_id="pip_audit_failed",
                severity="high",
                message=(proc.stderr or "pip-audit failed")[:500],
                dependency="*",
                tool="pip_audit",
            )
        ]
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return [
            DependencyFinding(
                rule_id="pip_audit_parse_error",
                severity="high",
                message="Could not parse pip-audit JSON output",
                dependency="*",
                tool="pip_audit",
            )
        ]

    findings: list[DependencyFinding] = []
    for dep in payload.get("dependencies") or []:
        name = str(dep.get("name") or "")
        version = str(dep.get("version") or "")
        for vuln in dep.get("vulns") or []:
            cvss = _extract_cvss(vuln)
            cve = _cve_id_from_vuln(vuln)
            severity = _cvss_to_severity(cvss)
            fix_versions = vuln.get("fix_versions") or []
            remediation = (
                f"Upgrade {name} to {fix_versions[0]}" if fix_versions else f"Review advisory for {name}"
            )
            findings.append(
                DependencyFinding(
                    rule_id="cve_detected",
                    severity=severity,
                    message=str(vuln.get("description") or f"CVE in {name}")[:300],
                    dependency=name,
                    version=version,
                    cve_id=cve,
                    cvss_score=cvss,
                    remediation=remediation,
                    tool="pip_audit",
                    extra={"aliases": vuln.get("aliases"), "fix_versions": fix_versions},
                )
            )
    return findings


def verify_lockfile_pinning(*, seed: dict[str, Any] | None = None) -> list[DependencyFinding]:
    """Supply chain — pinned versions + hash verification required."""
    seed = seed or _load_seed()
    lockfiles = (_cfg(seed).get("lockfiles") or ["requirements.hashes.txt"])
    findings: list[DependencyFinding] = []
    hashes_file = Path("requirements.hashes.txt")
    if not hashes_file.is_file():
        findings.append(
            DependencyFinding(
                rule_id="unpinned_dependencies",
                severity="critical",
                message="requirements.hashes.txt missing — unpinned dependencies forbidden",
                dependency="*",
                remediation="Generate hash-locked requirements via pip hash.",
                tool="supply_chain",
            )
        )
        return findings

    text = hashes_file.read_text(encoding="utf-8")
    if not _HASH_LINE.search(text):
        findings.append(
            DependencyFinding(
                rule_id="hash_verification_missing",
                severity="critical",
                message="requirements.hashes.txt has no sha256 hashes",
                dependency="*",
                remediation="Use pip install --require-hashes.",
                tool="supply_chain",
            )
        )
    unpinned = [
        lf
        for lf in lockfiles
        if lf.endswith(".txt") and Path(lf).is_file() and lf not in _SOURCE_MANIFESTS
    ]
    for lf in unpinned:
        content = Path(lf).read_text(encoding="utf-8")
        lines = [ln for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        for ln in lines:
            stripped = ln.strip()
            if stripped.startswith("--hash") or stripped.endswith("\\"):
                continue
            if "==" not in ln:
                findings.append(
                    DependencyFinding(
                        rule_id="unpinned_package_line",
                        severity="high",
                        message=f"Unpinned dependency line in {lf}: {ln[:60]}",
                        dependency=ln.split()[0] if ln.split() else "*",
                        remediation="Pin all direct dependencies with ==version.",
                        tool="supply_chain",
                    )
                )
    return findings


def generate_sbom_artifact(*, out: Path | None = None) -> dict[str, Any]:
    """CycloneDX SBOM per release — locked with lockfile hash (#1029)."""
    out = out or Path("docs/data-room/sbom/cyclonedx-python.json")
    lock = Path("requirements.lock.txt")
    lock_sha = hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else ""
    try:
        proc = subprocess.run(
            ["python", "scripts/generate_sbom.py", "--out", str(out)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        ok = proc.returncode == 0 and out.is_file()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        ok = False
    sbom_version = None
    if out.is_file():
        try:
            sbom = json.loads(out.read_text(encoding="utf-8"))
            sbom_version = sbom.get("version")
            # Immutable release binding
            props = (sbom.get("metadata") or {}).get("properties") or []
            props.append({"name": "blackdark:release_scan_at", "value": _utcnow()})
            out.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": ok,
        "path": str(out),
        "format": "CycloneDX",
        "lockfile_sha256": lock_sha,
        "sbom_version": sbom_version,
        "integration_ref": _IMMUTABLE_REF,
    }


def scan_license_compliance(*, seed: dict[str, Any] | None = None) -> tuple[list[DependencyFinding], dict[str, Any]]:
    """License conflict detection — copyleft flags trigger legal review."""
    seed = seed or _load_seed()
    copyleft_tokens = tuple(_cfg(seed).get("copyleft_licenses") or ["GPL", "AGPL"])
    findings: list[DependencyFinding] = []
    lic_json = Path("docs/data-room/licenses/dependency_licenses.json")
    try:
        subprocess.run(
            ["python", "scripts/generate_license_inventory.py"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    summary: dict[str, Any] = {"ok": False, "copyleft_flags": [], "unknown_count": 0}
    if not lic_json.is_file():
        findings.append(
            DependencyFinding(
                rule_id="license_inventory_missing",
                severity="medium",
                message="License inventory not generated",
                dependency="*",
                remediation="Run scripts/generate_license_inventory.py",
                tool="license_scan",
            )
        )
        return findings, summary

    data = json.loads(lic_json.read_text(encoding="utf-8"))
    summary = {
        "ok": True,
        "component_count": data.get("component_count", 0),
        "unknown_count": data.get("unknown_license_count", 0),
        "copyleft_flags": [],
        "counsel_review": data.get("counsel_review"),
    }
    for comp in data.get("components") or []:
        lic = str(comp.get("license") or "")
        name = str(comp.get("lock_name") or "")
        if any(token in lic.upper() for token in copyleft_tokens):
            summary["copyleft_flags"].append({"package": name, "license": lic})
            findings.append(
                DependencyFinding(
                    rule_id="license_copyleft_conflict",
                    severity="medium",
                    message=f"Copyleft license may require legal review: {name} ({lic})",
                    dependency=name,
                    remediation="Trigger legal review for commercial/copyleft conflict.",
                    tool="license_scan",
                )
            )
        if lic == "UNKNOWN":
            findings.append(
                DependencyFinding(
                    rule_id="license_unknown",
                    severity="low",
                    message=f"Unknown license for {name}",
                    dependency=name,
                    tool="license_scan",
                )
            )
    return findings, summary


def record_dependency_scan_audit(
    *,
    actor: str,
    result: dict[str, Any],
    duration_seconds: float,
) -> dict[str, Any]:
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
        "sbom": result.get("sbom"),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("dependency scan audit persist failed", exc_info=True)
    return entry


def run_dependency_scan_gate(
    *,
    actor: str = "ci",
    seed: dict[str, Any] | None = None,
    skip_sbom: bool = False,
) -> dict[str, Any]:
    """Full dependency + SBOM + license gate."""
    started = time.time()
    seed = seed or _load_seed()
    scan_id = f"depscan-{int(started)}"

    all_findings: list[DependencyFinding] = []
    all_findings.extend(run_pip_audit())
    all_findings.extend(verify_lockfile_pinning(seed=seed))
    license_findings, license_summary = scan_license_compliance(seed=seed)
    all_findings.extend(license_findings)

    sbom_result: dict[str, Any] = {"ok": True, "skipped": True}
    if not skip_sbom:
        sbom_result = generate_sbom_artifact()

    active = [f for f in all_findings if not is_suppressed(f)]
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in active:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    policy = (_cfg(seed).get("policy") or {})
    blocked = policy.get("block_critical_cve", True) and (
        counts["critical"] > 0 or counts["high"] > 0
    )

    duration = time.time() - started
    result = {
        "ok": not blocked and sbom_result.get("ok", True),
        "blocked": blocked,
        "feature": _FEATURE,
        "scan_id": scan_id,
        "actor": actor,
        "duration_seconds": round(duration, 2),
        "finding_counts": counts,
        "findings": [f.to_dict() for f in active[:200]],
        "total_findings": len(active),
        "suppressed": len(all_findings) - len(active),
        "sbom": sbom_result,
        "license_summary": license_summary,
        "security_trilogy": {"sast_ref": _SAST_REF, "dast_ref": _DAST_REF, "dependency_ref": 1044},
        "timestamp": _utcnow(),
    }
    record_dependency_scan_audit(actor=actor, result=result, duration_seconds=duration)

    if blocked:
        trigger_dependency_cve_incident(result)

    return result


def dependency_scan_gate_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "lockfiles": _cfg(seed).get("lockfiles") or [],
        "integrations": _cfg(seed).get("integrations") or {},
        "audit_path": str(_AUDIT_PATH),
        "sbom_path": "docs/data-room/sbom/cyclonedx-python.json",
        "license_path": "docs/data-room/licenses/dependency_licenses.json",
        "ci_workflow": ".github/workflows/security.yml",
        "timestamp": _utcnow(),
    }


def check_dependency_scan_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = dependency_scan_gate_status(seed=seed)
    policy = status["policy"]
    last = _last_audit_entry()
    checks = {
        "scan_enabled": policy.get("enabled") is True,
        "pip_audit": "pip_audit" in (policy.get("tools") or []),
        "sbom_generation": policy.get("sbom_per_release") is True,
        "license_compliance": policy.get("license_compliance_scan") is True,
        "dependency_pinning": policy.get("dependency_pinning_required") is True,
        "hash_verification": policy.get("hash_verification_required") is True,
        "block_critical_cve": policy.get("block_critical_cve") is True,
        "audit_retention": policy.get("audit_retention_days", 0) >= 730,
        "last_scan_passed": last.get("ok", True) if last else True,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "last_scan": last,
        "timestamp": _utcnow(),
    }


def _last_audit_entry() -> dict[str, Any] | None:
    if not _AUDIT_PATH.is_file():
        return None
    try:
        lines = [ln for ln in _AUDIT_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return json.loads(lines[-1]) if lines else None
    except (OSError, json.JSONDecodeError):
        return None


def run_dependency_scan_gate_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = dependency_scan_gate_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "sbom_cyclonedx", "passed": status["policy"]["sbom_format"] == "CycloneDX"})
    checks.append({"id": "block_critical", "passed": status["policy"]["block_critical_cve"] is True})
    checks.append({"id": "pinning_required", "passed": status["policy"]["dependency_pinning_required"] is True})
    checks.append({"id": "sast_cross_ref", "passed": status["integrations"].get("sast_gate_ref") == _SAST_REF})
    checks.append({"id": "dast_cross_ref", "passed": status["integrations"].get("dast_gate_ref") == _DAST_REF})

    gate = check_dependency_scan_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }


def trigger_dependency_cve_incident(scan_result: dict[str, Any]) -> dict[str, Any]:
    """#1017 — critical CVE in production dependency → incident playbook."""
    counts = scan_result.get("finding_counts") or {}
    if not counts.get("critical") and not counts.get("high"):
        return {"triggered": False, "reason": "no_critical_high"}
    try:
        from security_events import record_security_event

        record_security_event(
            "dependency_cve_incident",
            severity="critical",
            actor="dependency_scan_gate",
            detail={
                "scan_id": scan_result.get("scan_id"),
                "counts": counts,
                "playbook": "emergency_patch_rollback_forensics",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass
    return {
        "triggered": True,
        "integration_ref": _INCIDENT_REF,
        "action": "emergency_patch_rollback_forensics",
        "scan_id": scan_result.get("scan_id"),
    }
