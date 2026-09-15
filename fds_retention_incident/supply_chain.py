"""Supply-chain security controls — SCA/SBOM/waiver/release policy (SDG-17)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

SUPPLY_CHAIN_VERSION = "fds-supply-chain-v1"
ROOT = Path(__file__).resolve().parents[1]

Severity = Literal["critical", "high", "medium", "low"]


def _waiver_path() -> Path:
    base = Path(os.getenv("DATA_DIR", "data"))
    return base / "dependency_waivers.json"


def _load_waivers() -> list[dict[str, Any]]:
    path = _waiver_path()
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_waivers(waivers: list[dict[str, Any]]) -> None:
    path = _waiver_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(waivers, indent=2), encoding="utf-8")


def register_waiver(
    *,
    package: str,
    vulnerability_id: str,
    severity: Severity,
    owner: str,
    reason: str,
    expires_at: str,
) -> dict[str, Any]:
    """Explicit waiver with owner, reason, and expiry — no permanent silent allowlist."""
    if not owner or not reason or not expires_at:
        raise ValueError("waiver_requires_owner_reason_expiry")
    waiver = {
        "package": package,
        "vulnerability_id": vulnerability_id,
        "severity": severity,
        "owner": owner,
        "reason": reason,
        "expires_at": expires_at,
        "registered_at": datetime.now(UTC).isoformat(),
        "remediation_status": "waived",
    }
    waivers = _load_waivers()
    waivers = [w for w in waivers if not (w["package"] == package and w["vulnerability_id"] == vulnerability_id)]
    waivers.append(waiver)
    _save_waivers(waivers)
    return waiver


def evaluate_waivers() -> dict[str, Any]:
    now = datetime.now(UTC)
    active: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    uncontrolled: list[dict[str, Any]] = []
    for w in _load_waivers():
        missing = [k for k in ("owner", "reason", "expires_at") if not w.get(k)]
        if missing:
            uncontrolled.append({**w, "gap": f"missing:{','.join(missing)}"})
            continue
        try:
            exp = datetime.fromisoformat(str(w["expires_at"]).replace("Z", "+00:00"))
        except ValueError:
            uncontrolled.append({**w, "gap": "invalid_expiry"})
            continue
        if exp < now:
            expired.append(w)
        else:
            active.append(w)
    return {"active": active, "expired": expired, "uncontrolled": uncontrolled}


def sca_status() -> dict[str, Any]:
    """Verify pip-audit is runnable against hash-locked requirements."""
    req = ROOT / "requirements.hashes.txt"
    if not req.is_file():
        return {"available": False, "error": "requirements.hashes.txt missing"}
    proc = subprocess.run(
        [sys.executable, "-m", "pip_audit", "-r", str(req), "--desc", "--format", "json"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    findings: list[dict[str, Any]] = []
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            if isinstance(parsed, list):
                for dep in parsed:
                    for vuln in dep.get("vulns", []):
                        findings.append(
                            {
                                "package": dep.get("name"),
                                "version": dep.get("version"),
                                "vulnerability_id": vuln.get("id"),
                                "severity": _map_severity(vuln),
                                "description": vuln.get("description", "")[:200],
                            }
                        )
        except json.JSONDecodeError:
            pass
    return {
        "tool": "pip-audit",
        "requirements_file": str(req.relative_to(ROOT)),
        "exit_code": proc.returncode,
        "finding_count": len(findings),
        "findings": findings,
        "ci_workflow": ".github/workflows/security.yml",
    }


def _map_severity(vuln: dict[str, Any]) -> str:
    for key in ("severity", "cvss_score"):
        if vuln.get(key):
            return str(vuln[key])
    return "unknown"


def sbom_status() -> dict[str, Any]:
    """Generate or verify CycloneDX SBOM."""
    script = ROOT / "scripts" / "generate_sbom.py"
    out = ROOT / "docs" / "data-room" / "sbom" / "cyclonedx-python.json"
    if not script.is_file():
        return {"available": False, "error": "generate_sbom.py missing"}
    proc = subprocess.run([sys.executable, str(script), "--out", str(out)], capture_output=True, text=True, cwd=ROOT)
    if not out.is_file():
        return {"available": False, "exit_code": proc.returncode, "error": proc.stderr[-500:]}
    data = json.loads(out.read_text(encoding="utf-8"))
    return {
        "format": data.get("bomFormat"),
        "spec_version": data.get("specVersion"),
        "component_count": len(data.get("components", [])),
        "output_path": str(out.relative_to(ROOT)),
        "machine_readable": True,
        "generated": proc.returncode == 0,
    }


def evaluate_release_policy(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Critical findings block release unless explicit active waiver."""
    waivers = evaluate_waivers()
    active_waiver_keys = {(w["package"], w["vulnerability_id"]) for w in waivers["active"]}
    blocked: list[dict[str, Any]] = []
    waived: list[dict[str, Any]] = []
    for f in findings:
        sev = str(f.get("severity", "")).lower()
        if "critical" not in sev and sev not in {"9", "9.0", "10", "10.0"}:
            continue
        key = (f.get("package"), f.get("vulnerability_id"))
        entry = {
            "package": f.get("package"),
            "vulnerability_id": f.get("vulnerability_id"),
            "severity": f.get("severity"),
            "remediation_status": "blocked",
        }
        if key in active_waiver_keys:
            entry["remediation_status"] = "waived"
            waived.append(entry)
        else:
            blocked.append(entry)
    return {
        "release_blocked": len(blocked) > 0,
        "blocked_findings": blocked,
        "waived_findings": waived,
        "policy": "critical_vulnerabilities_block_release_without_explicit_waiver",
    }


def supply_chain_status() -> dict[str, Any]:
    sca = sca_status()
    sbom = sbom_status()
    waivers = evaluate_waivers()
    release = evaluate_release_policy(sca.get("findings", []))
    return {
        "version": SUPPLY_CHAIN_VERSION,
        "sca": {"tool": sca.get("tool"), "finding_count": sca.get("finding_count")},
        "sbom": {"format": sbom.get("format"), "component_count": sbom.get("component_count")},
        "waivers": {"active": len(waivers["active"]), "uncontrolled": len(waivers["uncontrolled"])},
        "release_policy": release,
        "dependency_monitoring_contract": "pip-audit weekly CI + SBOM on security workflow",
        "controlled_update_path": "requirements.lock.txt hash-pinned PR review",
    }
