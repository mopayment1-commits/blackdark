"""
DAST Gate — Dynamic Application Security Testing on live/staging services.

NOT standalone. Complements #1042 SAST with runtime scanning (TLS, RBAC, leakage).
Periodic weekly scans + CI smoke against ASGI app. Non-destructive on production.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urljoin

logger = logging.getLogger("BLACKDARK.DASTGate")

_FEATURE = "dast_gate"
_SEED_PATH = Path("data/dast_gate_seed.json")
_AUDIT_PATH = Path("data/dast_scan_audit.jsonl")
_SUPPRESSIONS_PATH = Path("data/dast_suppressions.json")

_SAST_REF = 1042
_INCIDENT_REF = 1017
_ENCRYPTION_REF = 1039
_RBAC_REF = 1022
_VAULT_REF = 1040
_LOAD_TEST_REF = 1020

Severity = Literal["critical", "high", "medium", "low", "info"]
ScanMode = Literal["ci", "weekly", "monthly", "ad_hoc"]

_LEAK_PATTERNS: list[tuple[str, Severity, re.Pattern[str]]] = [
    ("api_key_in_response", "critical", re.compile(r"sk_live_[0-9a-zA-Z]{16,}")),
    ("stripe_secret_leak", "critical", re.compile(r"sk_(?:test|live)_[0-9a-zA-Z]{16,}")),
    ("private_key_in_response", "critical", re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----")),
    ("session_token_exposure", "high", re.compile(r"""["']?(?:bd_token|session_token)["']?\s*[:=]\s*["'][A-Za-z0-9._-]{20,}""")),
    ("password_in_response", "high", re.compile(r"""["']password["']\s*:\s*["'][^"']{8,}["']""")),
]


@dataclass
class DASTFinding:
    rule_id: str
    severity: Severity
    message: str
    endpoint: str
    method: str = "GET"
    remediation: str = ""
    tool: str = "dast_gate"
    reproduction: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "endpoint": self.endpoint,
            "method": self.method,
            "remediation": self.remediation,
            "tool": self.tool,
            "reproduction": self.reproduction,
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
    return seed.get("dast_gate") or {}


def _load_suppressions() -> list[dict[str, Any]]:
    if not _SUPPRESSIONS_PATH.is_file():
        return []
    try:
        data = json.loads(_SUPPRESSIONS_PATH.read_text(encoding="utf-8"))
        return list(data.get("suppressions") or [])
    except (OSError, json.JSONDecodeError):
        return []


def is_suppressed(finding: DASTFinding) -> bool:
    for sup in _load_suppressions():
        if not sup.get("approved_by_security_lead"):
            continue
        if sup.get("rule_id") == finding.rule_id and sup.get("endpoint") == finding.endpoint:
            return True
    return False


def _throttle_delay(seed: dict[str, Any] | None = None) -> float:
    seed = seed or _load_seed()
    rps = float((_cfg(seed).get("policy") or {}).get("throttle_rps", 2))
    return 1.0 / max(rps, 0.5)


async def _http_get(
    client: Any,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], str]:
    response = await client.get(path, headers=headers or {})
    body = response.text if hasattr(response, "text") else str(response.content[:8192])
    resp_headers = {k.lower(): v for k, v in response.headers.items()}
    return response.status_code, resp_headers, body


def scan_response_leaks(
    endpoint: str,
    body: str,
    *,
    method: str = "GET",
) -> list[DASTFinding]:
    """#1040 — detect credential/session leakage in HTTP responses."""
    findings: list[DASTFinding] = []
    for rule_id, severity, pattern in _LEAK_PATTERNS:
        if pattern.search(body):
            findings.append(
                DASTFinding(
                    rule_id=rule_id,
                    severity=severity,
                    message=f"Sensitive data pattern in response: {rule_id}",
                    endpoint=endpoint,
                    method=method,
                    remediation="Never return secrets/tokens in API responses; use vault backend-only.",
                    tool="credential_leak_scan",
                    reproduction=f"{method} {endpoint}",
                    extra={"integration_ref": _VAULT_REF},
                )
            )
    return findings


def scan_tls_headers(
    endpoint: str,
    headers: dict[str, str],
    *,
    is_https: bool,
) -> list[DASTFinding]:
    """#1039 — runtime TLS/HSTS verification."""
    findings: list[DASTFinding] = []
    if is_https and "strict-transport-security" not in headers:
        findings.append(
            DASTFinding(
                rule_id="tls_hsts_missing",
                severity="medium",
                message="HTTPS endpoint missing Strict-Transport-Security",
                endpoint=endpoint,
                remediation="Enable HSTS in production via security_middleware.",
                tool="tls_scan",
                extra={"integration_ref": _ENCRYPTION_REF},
            )
        )
    proto = headers.get("x-forwarded-proto", "")
    if proto and proto != "https" and is_https:
        findings.append(
            DASTFinding(
                rule_id="tls_downgrade_header",
                severity="high",
                message="x-forwarded-proto indicates non-HTTPS on TLS endpoint",
                endpoint=endpoint,
                remediation="Enforce TLS 1.3 at edge; reject downgrade.",
                tool="tls_scan",
                extra={"integration_ref": _ENCRYPTION_REF},
            )
        )
    return findings


def scan_security_headers(endpoint: str, headers: dict[str, str]) -> list[DASTFinding]:
    findings: list[DASTFinding] = []
    for hdr, severity in (
        ("x-content-type-options", "medium"),
        ("x-frame-options", "medium"),
        ("content-security-policy", "medium"),
    ):
        if hdr not in headers:
            findings.append(
                DASTFinding(
                    rule_id=f"header_missing_{hdr.replace('-', '_')}",
                    severity=severity,
                    message=f"Missing security header: {hdr}",
                    endpoint=endpoint,
                    remediation=f"Add {hdr} via security_middleware.",
                    tool="passive_http_scan",
                )
            )
    return findings


async def scan_rbac_protected_paths(
    client: Any,
    paths: list[str],
    *,
    seed: dict[str, Any] | None = None,
) -> list[DASTFinding]:
    """#1022 — unauthenticated access to protected endpoints = critical."""
    findings: list[DASTFinding] = []
    delay = _throttle_delay(seed)
    for path in paths:
        await asyncio.sleep(delay)
        try:
            status, _, body = await _http_get(client, path)
        except Exception as exc:
            findings.append(
                DASTFinding(
                    rule_id="rbac_probe_error",
                    severity="low",
                    message=str(exc),
                    endpoint=path,
                    tool="rbac_scan",
                )
            )
            continue
        if status == 200:
            findings.append(
                DASTFinding(
                    rule_id="rbac_unauthorized_access",
                    severity="critical",
                    message="Protected endpoint returned 200 without authentication",
                    endpoint=path,
                    remediation="Add Depends(require_admin/require_authenticated).",
                    tool="rbac_scan",
                    reproduction=f"GET {path} (no auth headers)",
                    extra={"integration_ref": _RBAC_REF},
                )
            )
        elif status not in {401, 403, 404, 405, 422}:
            findings.append(
                DASTFinding(
                    rule_id="rbac_unexpected_status",
                    severity="medium",
                    message=f"Protected endpoint returned unexpected status {status}",
                    endpoint=path,
                    tool="rbac_scan",
                )
            )
        findings.extend(scan_response_leaks(path, body))
    return findings


async def scan_public_paths(
    client: Any,
    paths: list[str],
    *,
    seed: dict[str, Any] | None = None,
) -> list[DASTFinding]:
    findings: list[DASTFinding] = []
    delay = _throttle_delay(seed)
    for path in paths:
        await asyncio.sleep(delay)
        try:
            status, headers, body = await _http_get(client, path)
        except Exception as exc:
            findings.append(
                DASTFinding(
                    rule_id="public_probe_error",
                    severity="low",
                    message=str(exc),
                    endpoint=path,
                    tool="passive_http_scan",
                )
            )
            continue
        if status >= 500:
            findings.append(
                DASTFinding(
                    rule_id="server_error_disclosure",
                    severity="medium",
                    message=f"Server error {status} on public endpoint",
                    endpoint=path,
                    remediation="Avoid verbose stack traces in production responses.",
                    tool="passive_http_scan",
                )
            )
        findings.extend(scan_security_headers(path, headers))
        findings.extend(scan_tls_headers(path, headers, is_https=True))
        findings.extend(scan_response_leaks(path, body))
    return findings


async def scan_authenticated_paths(
    client: Any,
    paths: list[str],
    *,
    auth_headers: dict[str, str],
    seed: dict[str, Any] | None = None,
) -> list[DASTFinding]:
    """Authenticated DAST — not anonymous-only."""
    findings: list[DASTFinding] = []
    delay = _throttle_delay(seed)
    for path in paths:
        await asyncio.sleep(delay)
        try:
            status, _, body = await _http_get(client, path, headers=auth_headers)
        except Exception as exc:
            findings.append(
                DASTFinding(
                    rule_id="auth_probe_error",
                    severity="low",
                    message=str(exc),
                    endpoint=path,
                    tool="authenticated_scan",
                )
            )
            continue
        if status == 403:
            continue  # expected for non-admin test user on admin paths
        findings.extend(scan_response_leaks(path, body))
    return findings


def _default_paths(seed: dict[str, Any] | None = None) -> tuple[list[str], list[str]]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    protected = list(cfg.get("protected_endpoints_sample") or [])
    public = list(cfg.get("public_read_only_paths") or [])
    public.extend(
        [
            "/api/security/status",
            "/api/privacy/status",
            "/api/platform/features",
        ]
    )
    return protected, public


async def run_dast_scan_asgi(
    *,
    mode: ScanMode = "ci",
    actor: str = "ci",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CI smoke — dynamic scan against local ASGI app (non-destructive)."""
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    started = time.time()
    seed = seed or _load_seed()
    scan_id = f"dast-{int(started)}"
    protected, public = _default_paths(seed)

    transport = ASGITransport(app=app)
    findings: list[DASTFinding] = []
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        findings.extend(await scan_public_paths(client, public, seed=seed))
        findings.extend(await scan_rbac_protected_paths(client, protected, seed=seed))

        admin_key = os.getenv("DAST_ADMIN_API_KEY") or os.getenv("ADMIN_API_KEY", "")
        if admin_key and mode in {"monthly", "ad_hoc"}:
            findings.extend(
                await scan_authenticated_paths(
                    client,
                    ["/api/platform/keys/status"],
                    auth_headers={"X-Admin-Key": admin_key},
                    seed=seed,
                )
            )

    return _finalize_scan(findings, scan_id=scan_id, actor=actor, mode=mode, started=started, seed=seed)


async def run_dast_scan_url(
    base_url: str,
    *,
    mode: ScanMode = "weekly",
    actor: str = "scheduler",
    read_only: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Runtime scan against staging/production URL — read-only paths only by default."""
    import httpx

    started = time.time()
    seed = seed or _load_seed()
    scan_id = f"dast-{int(started)}"
    protected, public = _default_paths(seed)
    if read_only:
        protected = []  # never probe protected paths on production without explicit flag

    base = base_url.rstrip("/")
    findings: list[DASTFinding] = []
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(base_url=base, timeout=timeout, follow_redirects=True) as client:
        findings.extend(await scan_public_paths(client, public, seed=seed))
        if not read_only:
            findings.extend(await scan_rbac_protected_paths(client, protected, seed=seed))

        # Passive ZAP-equivalent baseline
        try:
            from scripts.wave_00_passive_security_scan import run_passive_scan

            passive = run_passive_scan(base)
            for f in passive.get("findings") or []:
                if not f.get("ok") and f.get("risk") in {"high", "medium"}:
                    findings.append(
                        DASTFinding(
                            rule_id=f"passive_{f.get('rule', 'unknown')}",
                            severity="high" if f.get("risk") == "high" else "medium",
                            message=str(f.get("detail") or ""),
                            endpoint=base,
                            tool="passive_http_scan",
                        )
                    )
        except Exception:
            logger.debug("passive scan hook failed", exc_info=True)

    return _finalize_scan(
        findings,
        scan_id=scan_id,
        actor=actor,
        mode=mode,
        started=started,
        seed=seed,
        target=base,
    )


def _finalize_scan(
    all_findings: list[DASTFinding],
    *,
    scan_id: str,
    actor: str,
    mode: ScanMode,
    started: float,
    seed: dict[str, Any],
    target: str | None = None,
) -> dict[str, Any]:
    active = [f for f in all_findings if not is_suppressed(f)]
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in active:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    policy = (_cfg(seed).get("policy") or {})
    is_prod = _is_production_target(target)
    blocked = False
    if is_prod and policy.get("block_critical_high_production", True):
        blocked = counts["critical"] > 0 or counts["high"] > 0
    elif mode == "ci":
        blocked = counts["critical"] > 0 or counts["high"] > 0

    duration = time.time() - started
    result = {
        "ok": not blocked,
        "blocked": blocked,
        "feature": _FEATURE,
        "scan_id": scan_id,
        "mode": mode,
        "actor": actor,
        "target": target or "asgi_local",
        "duration_seconds": round(duration, 2),
        "finding_counts": counts,
        "findings": [f.to_dict() for f in active[:200]],
        "total_findings": len(active),
        "suppressed": len(all_findings) - len(active),
        "read_only": target is None or policy.get("production_read_only", True),
        "timestamp": _utcnow(),
    }
    record_dast_audit(actor=actor, result=result, duration_seconds=duration)

    if blocked or (is_prod and (counts["critical"] or counts["high"])):
        trigger_dast_incident(result)

    return result


def _is_production_target(target: str | None) -> bool:
    if not target:
        return False
    t = target.lower()
    return "production" in t or os.getenv("DAST_TARGET_ENV", "").lower() in {"production", "prod"}


def record_dast_audit(
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
        "mode": result.get("mode"),
        "target": result.get("target"),
        "finding_counts": result.get("finding_counts"),
        "scan_id": result.get("scan_id"),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("dast audit persist failed", exc_info=True)
    return entry


def dast_gate_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "scan_modes": _cfg(seed).get("scan_modes") or {},
        "integrations": _cfg(seed).get("integrations") or {},
        "sast_cross_ref": _SAST_REF,
        "audit_path": str(_AUDIT_PATH),
        "zap_wrapper": "scripts/run_wave_00_zap.sh",
        "ci_workflow": ".github/workflows/security.yml",
        "timestamp": _utcnow(),
    }


def check_dast_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = dast_gate_status(seed=seed)
    policy = status["policy"]
    last = _last_audit_entry()
    checks = {
        "dast_enabled": policy.get("enabled") is True,
        "weekly_scan": policy.get("weekly_automated_scan") is True,
        "production_read_only": policy.get("production_read_only") is True,
        "no_destructive_prod": policy.get("no_destructive_on_production") is True,
        "throttle_configured": float(policy.get("throttle_rps", 0)) > 0,
        "audit_retention": policy.get("audit_retention_days", 0) >= 730,
        "sast_complement": status["integrations"].get("sast_gate_ref") == _SAST_REF,
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


def run_dast_gate_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = dast_gate_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "weekly_scan", "passed": status["policy"]["weekly_automated_scan"] is True})
    checks.append({"id": "prod_read_only", "passed": status["policy"]["production_read_only"] is True})
    checks.append({"id": "sast_cross_ref", "passed": status["sast_cross_ref"] == _SAST_REF})

    sample = DASTFinding(
        rule_id="test",
        severity="low",
        message="test",
        endpoint="/test",
    )
    checks.append({"id": "suppression_api", "passed": isinstance(is_suppressed(sample), bool)})

    gate = check_dast_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }


def trigger_dast_incident(scan_result: dict[str, Any]) -> dict[str, Any]:
    """#1017 — critical/high DAST finding triggers incident playbook."""
    counts = scan_result.get("finding_counts") or {}
    if not counts.get("critical") and not counts.get("high"):
        return {"triggered": False, "reason": "no_critical_high"}
    try:
        from security_events import record_security_event

        record_security_event(
            "dast_critical_finding_incident",
            severity="critical",
            actor="dast_gate",
            detail={
                "scan_id": scan_result.get("scan_id"),
                "target": scan_result.get("target"),
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
        "action": "rollback_assessment_forensics",
        "scan_id": scan_result.get("scan_id"),
    }


async def run_dast_gate(
    *,
    mode: ScanMode | None = None,
    actor: str = "ci",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entry point — ASGI local (CI) or remote URL (scheduled)."""
    seed = seed or _load_seed()
    mode = mode or ("weekly" if os.getenv("DAST_TARGET_URL") else "ci")
    target = (os.getenv("DAST_TARGET_URL") or "").strip()
    if target:
        read_only = os.getenv("DAST_PRODUCTION_READ_ONLY", "true").lower() in {"1", "true", "yes"}
        return await run_dast_scan_url(target, mode=mode, actor=actor, read_only=read_only, seed=seed)
    return await run_dast_scan_asgi(mode=mode, actor=actor, seed=seed)
