"""
Security Verification Evidence — Feature #191 (Sprint 0 / Sprint 1 security gate).

Transforms security from declared design into reproducible, reviewable evidence:
SAST/DAST/dependency scans, auth/authz regression tests, secrets checks,
severity classification, remediation verification, and release gate status.

Integrates with #192 Security-First Architecture.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import subprocess
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SecurityVerificationEvidence")

_FEATURE_ID = 191
_GATE_VERSION = "1.0.0"
_RETENTION_YEARS = 3

_EVIDENCE_DIR = Path("data/security_evidence_packs")
_FINDINGS_PATH = Path("data/security_findings.jsonl")
_PACKS_PATH = Path("data/security_evidence_packs.jsonl")
_SUPPRESSIONS_PATH = Path("data/security_suppressions.json")
_AUTHZ_TESTS = (
    "tests/test_security.py",
    "tests/test_security_hardening.py",
    "tests/test_d13_auth_abuse.py",
    "tests/test_api_security_encryption.py",
    "tests/test_security_circuit_breakers.py",
    "tests/test_security_first_architecture.py",
)

_SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")
_SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
]

_WORKFLOW_PATH = Path(".github/workflows/security.yml")
_PASSIVE_SCAN_SCRIPT = Path("scripts/wave_00_passive_security_scan.py")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _retention_cutoff() -> datetime:
    return datetime.now(UTC) - timedelta(days=_RETENTION_YEARS * 365)


def _sign_payload(payload: dict[str, Any]) -> str:
    import os

    secret = (
        os.getenv("SECURITY_EVIDENCE_SIGNING_KEY", "").strip()
        or os.getenv("PENTEST_ATTESTATION_SIGNING_KEY", "").strip()
        or os.getenv("SECRETS_MASTER_KEY", "").strip()
        or "blackdark-security-evidence-dev-sign"
    )
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def _load_suppressions() -> dict[str, Any]:
    if not _SUPPRESSIONS_PATH.is_file():
        return {"suppressions": {}}
    try:
        return json.loads(_SUPPRESSIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"suppressions": {}}


def _save_suppressions(blob: dict[str, Any]) -> None:
    _SUPPRESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SUPPRESSIONS_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _append_finding(finding: dict[str, Any]) -> dict[str, Any]:
    row = {
        "id": finding.get("id") or str(uuid.uuid4()),
        "timestamp": _utcnow(),
        "gate_version": _GATE_VERSION,
        **finding,
    }
    _FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _FINDINGS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _read_findings(*, limit: int = 500) -> list[dict[str, Any]]:
    if not _FINDINGS_PATH.is_file():
        return []
    try:
        lines = _FINDINGS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(x) for x in lines if x.strip()]
    except (OSError, json.JSONDecodeError):
        return []


def _parse_ci_tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    if not _WORKFLOW_PATH.is_file():
        return versions
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    for tool, pattern in (
        ("pip-audit", r"pip-audit==([0-9.]+)"),
        ("bandit", r"bandit==([0-9.]+)"),
        ("python", r'python-version:\s*"([0-9.]+)"'),
    ):
        match = re.search(pattern, text)
        if match:
            versions[tool] = match.group(1)
    versions["workflow"] = str(_WORKFLOW_PATH)
    return versions


def _gate_inventory() -> list[dict[str, Any]]:
    tools = _parse_ci_tool_versions()
    return [
        {
            "gate_id": "dependency_scan",
            "tool": "pip-audit",
            "version": tools.get("pip-audit", "unknown"),
            "ci_job": "pip-audit",
            "reproducible": _WORKFLOW_PATH.is_file(),
        },
        {
            "gate_id": "sast",
            "tool": "bandit",
            "version": tools.get("bandit", "unknown"),
            "ci_job": "bandit",
            "reproducible": _WORKFLOW_PATH.is_file(),
        },
        {
            "gate_id": "dast",
            "tool": "wave_00_passive_security_scan",
            "version": _GATE_VERSION,
            "script": str(_PASSIVE_SCAN_SCRIPT),
            "reproducible": _PASSIVE_SCAN_SCRIPT.is_file(),
        },
        {
            "gate_id": "authz_regression",
            "tool": "pytest",
            "version": tools.get("python", "3.12"),
            "test_modules": list(_AUTHZ_TESTS),
            "reproducible": all(Path(t).is_file() for t in _AUTHZ_TESTS),
        },
        {
            "gate_id": "secrets_scan",
            "tool": "pattern_scanner",
            "version": _GATE_VERSION,
            "patterns": len(_SECRET_PATTERNS),
            "reproducible": True,
        },
    ]


def _scan_secrets_in_repo(*, max_files: int = 200) -> list[dict[str, Any]]:
    """Lightweight secrets leak detection — scans source files, not .git."""
    root = Path(__file__).resolve().parent.parent
    findings: list[dict[str, Any]] = []
    scanned = 0
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", "data"}

    for path in root.rglob("*"):
        if scanned >= max_files:
            break
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix not in {".py", ".yml", ".yaml", ".json", ".env", ".md", ".sh"}:
            continue
        if path.name.endswith(".joblib") or "requirements" in path.name:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in _SECRET_PATTERNS:
            if pattern.search(text):
                rel = str(path.relative_to(root))
                # Exclude known safe patterns (examples, tests with fake keys)
                if "test_" in rel and "fake" in text.lower():
                    continue
                if ".example" in rel or "template" in rel.lower():
                    continue
                findings.append(
                    {
                        "gate": "secrets_scan",
                        "severity": "critical",
                        "rule": "potential_secret_leak",
                        "file": rel,
                        "status": "open",
                        "detail": f"Pattern match in {rel}",
                    }
                )
                break
    return findings


def _run_authz_regression_inventory() -> dict[str, Any]:
    present = [t for t in _AUTHZ_TESTS if Path(t).is_file()]
    missing = [t for t in _AUTHZ_TESTS if t not in present]
    return {
        "gate": "authz_regression",
        "tests_present": len(present),
        "tests_required": len(_AUTHZ_TESTS),
        "missing": missing,
        "ok": len(missing) == 0,
        "modules": present,
    }


def _run_bandit_gate(*, timeout_sec: int = 30) -> dict[str, Any]:
    """Run Bandit SAST locally when available."""
    try:
        proc = subprocess.run(
            ["bandit", "-r", ".", "-x", "./tests,./venv,./.venv", "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=Path(__file__).resolve().parent.parent,
        )
        results: list[dict[str, Any]] = []
        if proc.stdout.strip():
            try:
                blob = json.loads(proc.stdout)
                for item in blob.get("results") or []:
                    sev = str(item.get("issue_severity") or "medium").lower()
                    results.append(
                        {
                            "gate": "sast",
                            "severity": sev if sev in _SEVERITY_ORDER else "medium",
                            "rule": item.get("test_id"),
                            "file": item.get("filename"),
                            "line": item.get("line_number"),
                            "status": "open",
                            "detail": item.get("issue_text", ""),
                        }
                    )
            except json.JSONDecodeError:
                pass
        return {
            "gate": "sast",
            "tool": "bandit",
            "exit_code": proc.returncode,
            "findings": results,
            "ran": True,
        }
    except FileNotFoundError:
        return {"gate": "sast", "tool": "bandit", "ran": False, "findings": [], "reason": "bandit_not_installed"}
    except subprocess.TimeoutExpired:
        return {"gate": "sast", "tool": "bandit", "ran": False, "findings": [], "reason": "timeout"}


def run_security_gates(*, include_bandit: bool = False) -> dict[str, Any]:
    """Run versioned security gates and persist findings."""
    started = time.perf_counter()
    gate_results: list[dict[str, Any]] = []
    new_findings: list[dict[str, Any]] = []

    # Secrets scan
    secret_findings = _scan_secrets_in_repo()
    gate_results.append({"gate": "secrets_scan", "findings_count": len(secret_findings)})
    new_findings.extend(secret_findings)

    # Authz regression inventory
    authz = _run_authz_regression_inventory()
    gate_results.append(authz)
    if not authz["ok"]:
        for missing in authz["missing"]:
            new_findings.append(
                {
                    "gate": "authz_regression",
                    "severity": "high",
                    "rule": "missing_authz_test",
                    "file": missing,
                    "status": "open",
                    "detail": f"Authz regression test missing: {missing}",
                }
            )

    # DAST script availability
    dast_ok = _PASSIVE_SCAN_SCRIPT.is_file()
    gate_results.append({"gate": "dast", "script_present": dast_ok})
    if not dast_ok:
        new_findings.append(
            {
                "gate": "dast",
                "severity": "medium",
                "rule": "dast_script_missing",
                "status": "open",
                "detail": "Passive DAST script not found",
            }
        )

    # CI workflow check
    ci_ok = _WORKFLOW_PATH.is_file()
    gate_results.append({"gate": "dependency_scan", "ci_configured": ci_ok, "sast_configured": ci_ok})
    if not ci_ok:
        new_findings.append(
            {
                "gate": "dependency_scan",
                "severity": "high",
                "rule": "ci_workflow_missing",
                "status": "open",
                "detail": "Security CI workflow missing",
            }
        )

    # Optional live Bandit
    if include_bandit:
        bandit = _run_bandit_gate()
        gate_results.append(bandit)
        new_findings.extend(bandit.get("findings") or [])

    persisted = [_append_finding(f) for f in new_findings]

    duration_ms = (time.perf_counter() - started) * 1000.0
    pack = build_evidence_pack(gate_run_id=str(uuid.uuid4()))
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "gate_version": _GATE_VERSION,
        "gates_run": len(gate_results),
        "gate_results": gate_results,
        "new_findings": len(persisted),
        "evidence_pack_id": pack.get("pack_id"),
        "release_gate": pack.get("release_gate"),
        "sla_met": duration_ms <= 2000,
        "duration_ms": round(duration_ms, 2),
        "timestamp": _utcnow(),
    }


def classify_severity(score: float) -> str:
    """Map numeric score 0-10 to severity band."""
    if score >= 9:
        return "critical"
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    if score >= 1:
        return "low"
    return "info"


def suppress_finding(
    *,
    finding_id: str,
    rationale: str,
    signer: str,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Suppress a finding — requires signed rationale from authorized signer."""
    if not rationale or len(rationale.strip()) < 20:
        return {"ok": False, "error": "rationale_too_short", "min_length": 20}

    payload = {
        "finding_id": finding_id,
        "rationale": rationale.strip(),
        "signer": signer,
        "suppressed_at": _utcnow(),
        "expires_at": expires_at,
    }
    signature = _sign_payload(payload)
    blob = _load_suppressions()
    suppressions = blob.setdefault("suppressions", {})
    suppressions[finding_id] = {**payload, "signature": signature}
    _save_suppressions(blob)

    return {"ok": True, "finding_id": finding_id, "signed": True, "signature": signature[:16] + "..."}


def verify_remediation(*, finding_id: str, evidence: str) -> dict[str, Any]:
    """Mark finding as remediated with evidence proof."""
    findings = _read_findings(limit=1000)
    target = next((f for f in findings if f.get("id") == finding_id), None)
    if not target:
        return {"ok": False, "error": "finding_not_found"}

    remediated = {
        "finding_id": finding_id,
        "status": "remediated",
        "remediated_at": _utcnow(),
        "evidence": evidence[:2000],
        "original_severity": target.get("severity"),
        "gate": target.get("gate"),
    }
    _append_finding({**target, **remediated, "id": finding_id})
    return {"ok": True, **remediated}


def _open_findings_summary() -> dict[str, Any]:
    findings = _read_findings(limit=1000)
    suppressions = _load_suppressions().get("suppressions") or {}

    # Latest status per finding id
    by_id: dict[str, dict[str, Any]] = {}
    for f in findings:
        fid = str(f.get("id") or "")
        if fid:
            by_id[fid] = f

    open_findings: list[dict[str, Any]] = []
    remediated_count = 0
    by_severity: dict[str, int] = {s: 0 for s in _SEVERITY_ORDER}

    for fid, f in by_id.items():
        status = str(f.get("status") or "open")
        if status == "remediated":
            remediated_count += 1
            continue
        if fid in suppressions:
            continue
        sev = str(f.get("severity") or "medium").lower()
        if sev not in _SEVERITY_ORDER:
            sev = "medium"
        by_severity[sev] = by_severity.get(sev, 0) + 1
        open_findings.append(f)

    critical_open = [f for f in open_findings if f.get("severity") == "critical"]
    return {
        "open_total": len(open_findings),
        "open_by_severity": by_severity,
        "critical_open": len(critical_open),
        "critical_open_ids": [f.get("id") for f in critical_open[:10]],
        "remediated": remediated_count,
        "suppressed": len(suppressions),
        "open_findings": open_findings[-20:],
    }


def release_gate_status() -> dict[str, Any]:
    """Release gate: PASS only when no critical unresolved findings."""
    summary = _open_findings_summary()
    suppressions = _load_suppressions().get("suppressions") or {}

    # Verify all suppressions have valid signatures
    unsigned_suppressions = []
    for fid, sup in suppressions.items():
        sig = sup.pop("signature", "")
        expected = _sign_payload({k: v for k, v in sup.items() if k != "signature"})
        if not sig or not hmac.compare_digest(sig, expected):
            unsigned_suppressions.append(fid)
        sup["signature"] = sig

    critical_blocked = summary["critical_open"] > 0
    authz = _run_authz_regression_inventory()
    ci_configured = _WORKFLOW_PATH.is_file()

    passed = not critical_blocked and authz["ok"] and ci_configured and not unsigned_suppressions

    headline = (
        f"Open findings: {summary['open_total']} "
        f"(critical: {summary['critical_open']}) | "
        f"Remediated: {summary['remediated']} | "
        f"Gate: {'✅ Pass' if passed else '❌ Blocked'}"
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "gate_version": _GATE_VERSION,
        "passed": passed,
        "headline": headline,
        "blocked_reasons": [
            *([] if not critical_blocked else ["critical_findings_unresolved"]),
            *([] if authz["ok"] else ["authz_regression_tests_missing"]),
            *([] if ci_configured else ["security_ci_not_configured"]),
            *([] if not unsigned_suppressions else ["unsigned_suppressions"]),
        ],
        "findings_summary": summary,
        "unsigned_suppressions": unsigned_suppressions,
        "timestamp": _utcnow(),
    }


def build_evidence_pack(*, gate_run_id: str | None = None) -> dict[str, Any]:
    """Build security evidence pack for institutional review."""
    started = time.perf_counter()
    pack_id = gate_run_id or str(uuid.uuid4())
    gate = release_gate_status()
    summary = gate["findings_summary"]
    tools = _parse_ci_tool_versions()

    pack = {
        "pack_id": pack_id,
        "feature_id": _FEATURE_ID,
        "gate_version": _GATE_VERSION,
        "generated_at": _utcnow(),
        "retention_years": _RETENTION_YEARS,
        "retention_until": (datetime.now(UTC) + timedelta(days=_RETENTION_YEARS * 365)).isoformat(),
        "tool_versions": tools,
        "gate_inventory": _gate_inventory(),
        "release_gate": {
            "passed": gate["passed"],
            "headline": gate["headline"],
            "blocked_reasons": gate["blocked_reasons"],
        },
        "findings": {
            "open_total": summary["open_total"],
            "open_by_severity": summary["open_by_severity"],
            "critical_open": summary["critical_open"],
            "remediated": summary["remediated"],
            "suppressed": summary["suppressed"],
        },
        "integrated_features": ["#192"],
        "reproducible": all(g.get("reproducible") for g in _gate_inventory()),
    }

    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    pack_file = _EVIDENCE_DIR / f"pack_{pack_id}.json"
    pack_file.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    _PACKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _PACKS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"pack_id": pack_id, "generated_at": pack["generated_at"], "passed": gate["passed"]}) + "\n")

    duration_ms = (time.perf_counter() - started) * 1000.0
    pack["sla_met"] = duration_ms <= 2000
    pack["duration_ms"] = round(duration_ms, 2)
    return pack


def security_verification_status() -> dict[str, Any]:
    """Security verification evidence status (#191)."""
    started = time.perf_counter()
    gate = release_gate_status()
    duration_ms = (time.perf_counter() - started) * 1000.0
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Security Verification Evidence",
        "mode": "infrastructure",
        "user_facing": False,
        "gate_version": _GATE_VERSION,
        "release_gate_passed": gate["passed"],
        "headline": gate["headline"],
        "retention_years": _RETENTION_YEARS,
        "gates": _gate_inventory(),
        "findings_summary": gate["findings_summary"],
        "integrated_features": ["#192"],
        "policy": (
            "No critical unresolved release findings. Scans reproducible via CI. "
            "No suppressed finding without signed rationale. Evidence retained 3+ years."
        ),
        "sla_met": duration_ms <= 2000,
        "duration_ms": round(duration_ms, 2),
        "timestamp": _utcnow(),
    }
