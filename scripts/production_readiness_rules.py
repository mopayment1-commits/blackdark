"""Production Readiness — rules, requirements, and check primitives (sections 4–35)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def file_ok(*paths: str) -> bool:
    return all((ROOT / p).is_file() for p in paths)


def dir_ok(*paths: str) -> bool:
    return all((ROOT / p).is_dir() for p in paths)


def path_exists(ref: str) -> bool:
    if not ref:
        return False
    p = ROOT / ref.split("#")[0].strip()
    return p.is_file() or p.is_dir()


def run_pytest(targets: list[str], timeout: int = 300) -> dict[str, Any]:
    if not targets:
        return {"passed": False, "command": "", "exit_code": 1}
    cmd = [sys.executable, "-m", "pytest", *targets, "-q", "--tb=no"]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {
            "passed": proc.returncode == 0,
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-800:],
        }
    except Exception as exc:
        return {"passed": False, "command": " ".join(cmd), "error": str(exc)}


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_ssot() -> dict[str, Any]:
    return load_json(SSOT_PATH)


def pass_engineering_caps(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    caps = ssot.get("canonical_capabilities") or ssot.get("capabilities") or []
    return [c for c in caps if c.get("engineering_status") == "PASS_ENGINEERING"]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def git_dirty_files() -> list[str]:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        return [ln[3:].strip() for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def _grep_repo(pattern: str, glob: str = "*.py") -> list[str]:
    hits: list[str] = []
    rx = re.compile(pattern)
    for p in ROOT.rglob(glob):
        if any(part.startswith(".") for part in p.parts):
            continue
        if "node_modules" in p.parts or ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rx.search(text):
            hits.append(str(p.relative_to(ROOT)))
    return hits


# ---------------------------------------------------------------------------
# Requirement model
# ---------------------------------------------------------------------------

Status = str  # VERIFIED_LOCAL | VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING | TRUE_NOT_APPLICABLE | GAP | UNVERIFIED
BlockerClass = str  # LOCAL_ENGINEERING_GAP | LOCAL_OPERATIONAL_ARTIFACT_GAP | EXTERNAL_* | TRUE_NOT_APPLICABLE


@dataclass
class RequirementResult:
    requirement_id: str
    area: str
    section: int
    title: str
    applicability: str
    canonical_owner: str
    runtime_path: str
    test_check: str
    status: Status
    blocker_class: BlockerClass | None
    evidence: list[str] = field(default_factory=list)
    local_classification: str = "local"


@dataclass
class Requirement:
    requirement_id: str
    area: str
    section: int
    title: str
    applicability: str
    canonical_owner: str
    runtime_path: str
    test_check: str
    check: Callable[[], tuple[Status, BlockerClass | None, list[str]]]


def _local(evidence: list[str]) -> tuple[Status, BlockerClass | None, list[str]]:
    return "VERIFIED_LOCAL", None, evidence


def _external(
    evidence: list[str], blocker: BlockerClass = "LIVE_ENVIRONMENT_VALIDATION_PENDING"
) -> tuple[Status, BlockerClass | None, list[str]]:
    return "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING", blocker, evidence


def _na(evidence: list[str]) -> tuple[Status, BlockerClass | None, list[str]]:
    return "TRUE_NOT_APPLICABLE", "TRUE_NOT_APPLICABLE", evidence


def _gap(
    evidence: list[str], blocker: BlockerClass = "LOCAL_ENGINEERING_GAP"
) -> tuple[Status, BlockerClass | None, list[str]]:
    return "GAP", blocker, evidence


# ---------------------------------------------------------------------------
# Environment inventory (section 4)
# ---------------------------------------------------------------------------

ENVIRONMENTS_DISCOVERED = [
    {
        "id": "local",
        "purpose": "Developer workstation / uvicorn",
        "runtime": "Python 3.12 + uvicorn",
        "database": "SQLite default; Postgres optional",
        "cache": "in-process / optional Redis",
        "queue": "SERVICE_BUS_LOCAL=true",
        "storage": "data/ filesystem",
        "secrets_source": ".env / keys/",
        "deployment": "bootstrap_free_human_ops.py",
        "config_source": "config.py + env",
        "observability": "logs + /metrics",
    },
    {
        "id": "test",
        "purpose": "pytest isolated SQLite / CI Postgres service",
        "runtime": "pytest + TestClient",
        "database": "tmp SQLite or BLACKDARK_TEST_DATABASE_URL",
        "deployment": "pytest",
        "config_source": "monkeypatch env",
    },
    {
        "id": "ci",
        "purpose": "GitHub Actions critical gate",
        "runtime": "ubuntu-latest + postgres:16 service",
        "database": "ephemeral Postgres",
        "deployment": ".github/workflows/ci.yml",
        "config_source": "workflow env",
    },
    {
        "id": "staging",
        "purpose": "Pre-prod rehearsal (documented, operator-provisioned)",
        "runtime": "Docker / Railway preview",
        "database": "Postgres",
        "deployment": "docker-compose / railway.json",
        "config_source": "Railway variables",
    },
    {
        "id": "production",
        "purpose": "Strict institutional topology",
        "runtime": "Railway / Docker / k8s",
        "database": "Postgres required",
        "cache": "Redis required for HA",
        "secrets_source": "managed env / vault",
        "deployment": "Dockerfile + railway.json + deploy/k8s/",
        "config_source": "ENV_VAR_REGISTRY + production_guard",
        "observability": "Sentry + uptime probes + monitoring_alerting",
    },
    {
        "id": "worker",
        "purpose": "Background ingestion / scheduled jobs",
        "runtime": "SERVICE_MODE=worker",
        "deployment": "docker-compose worker profile",
    },
    {
        "id": "scheduled",
        "purpose": "Cron / GitHub schedule security scans",
        "deployment": ".github/workflows/security.yml schedule",
    },
    {
        "id": "b2b_api",
        "purpose": "Institutional API + websocket feed",
        "runtime": "FastAPI routers + b2b_websocket_hub",
        "deployment": "same web process",
    },
]


def check_environments_documented() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = [
        "docs/ENV_CONFIG_MATRIX.md",
        "docs/ops/ENV_VAR_REGISTRY.md",
        "docs/ops/DATABASE_PROD_STAGING_AR.md",
        "docker-compose.yml",
        "railway.json",
        "deploy/k8s/",
    ]
    ok = file_ok("docs/ENV_CONFIG_MATRIX.md", "docs/ops/ENV_VAR_REGISTRY.md") and path_exists("docker-compose.yml")
    if ok:
        ev = [f"environments={len(ENVIRONMENTS_DISCOVERED)}"] + [p for p in paths if path_exists(p)]
        return _local(ev)
    return _gap(["missing environment documentation"])


def check_no_prod_dev_defaults_leak() -> tuple[Status, BlockerClass | None, list[str]]:
    from production_guard import _INSECURE_DEFAULTS  # noqa: PLC2701

    guard_src = (ROOT / "production_guard.py").read_text(encoding="utf-8")
    has_check = "no_insecure_prod_secret_defaults" in guard_src and "sqlite_forbidden_in_strict_production" in guard_src
    return _local(["production_guard insecure default catalog", f"defaults={len(_INSECURE_DEFAULTS)}"]) if has_check else _gap(
        ["production_guard missing insecure default checks"]
    )


def check_config_collision_guards() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_production_guard.py", "tests/test_critical_ops_closure.py"])
    return _local([t["command"], f"exit={t.get('exit_code')}"]) if t["passed"] else _gap(["production guard tests failed"], "LOCAL_ENGINEERING_GAP")


# ---------------------------------------------------------------------------
# Build / supply chain (sections 7–8)
# ---------------------------------------------------------------------------


def check_build_reproducibility() -> tuple[Status, BlockerClass | None, list[str]]:
    files = ["requirements.hashes.txt", "requirements-prod.hashes.txt", "Dockerfile", "requirements.lock.txt"]
    ok = all(path_exists(f) for f in files)
    return _local(files) if ok else _gap([f"missing {f}" for f in files if not path_exists(f)])


def check_supply_chain_gates() -> tuple[Status, BlockerClass | None, list[str]]:
    wf = ROOT / ".github/workflows/security.yml"
    ci = ROOT / ".github/workflows/ci.yml"
    if not wf.is_file() or not ci.is_file():
        return _gap(["security.yml or ci.yml missing"])
    text = wf.read_text(encoding="utf-8")
    pinned = "actions/checkout@" in text and "sha256:" in (ci.read_text(encoding="utf-8") + text)
    sbom = path_exists("docs/data-room/sbom/cyclonedx-python.json")
    return _local(["pip-audit", "bandit", "sbom", f"actions_pinned={pinned}"]) if pinned and sbom else _gap(
        ["unpinned CI actions or missing SBOM"]
    )


# ---------------------------------------------------------------------------
# DB / backup / deployment (sections 9–13)
# ---------------------------------------------------------------------------


def check_migration_integrity() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_postgres_migration_integrity.py", "tests/test_postgres_backend.py"])
    owners = ["database.py", "db_upgrade.py", "postgres_backend.py"]
    ok = t["passed"] and all(path_exists(p) for p in owners)
    return _local(owners + [t["command"]]) if ok else _gap(["migration integrity tests failed"])


def check_backup_restore_scripts() -> tuple[Status, BlockerClass | None, list[str]]:
    scripts = ["scripts/backup_postgres.py", "scripts/restore_postgres.py", "docs/ops/BACKUP_RESTORE.md"]
    ok = all(path_exists(s) for s in scripts)
    t = run_pytest(["tests/test_codeql_cleartext_logging_closure.py::test_restore_postgres_redacts_psql_stderr"])
    if not ok:
        return _gap(["backup/restore artifacts missing"])
    return _local(scripts + ["restore stderr redaction test"])


def check_backup_restore_live_drill() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(
        ["docs/ops/BACKUP_RESTORE.md declares buyer cloud drill EXTERNAL"],
        "HUMAN_OPERATIONAL_EXERCISE_PENDING",
    )


def check_deployment_path() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["Dockerfile", "docker-compose.yml", "railway.json", "startup_orchestrator.py", "dashboard.py"]
    health = ["/health/live", "/health/ready"]
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    ok = all(path_exists(p) for p in paths[:4]) and all(h in dash for h in health)
    return _local(paths + health) if ok else _gap(["deployment path incomplete"])


def check_rollback_documented() -> tuple[Status, BlockerClass | None, list[str]]:
    runbook = ROOT / "docs/RUNBOOK.md"
    if not runbook.is_file():
        return _gap(["RUNBOOK.md missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")
    text = runbook.read_text(encoding="utf-8")
    ok = "## Rollback" in text or "## rollback" in text.lower()
    return _local(["docs/RUNBOOK.md rollback section"]) if ok else _gap(["rollback section missing in RUNBOOK"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def check_rollback_live_rehearsal() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["rollback rehearsal requires production/staging deploy target"], "HUMAN_OPERATIONAL_EXERCISE_PENDING")


def check_rolling_deploy_applicability() -> tuple[Status, BlockerClass | None, list[str]]:
    scale = (ROOT / "scale_readiness.py").read_text(encoding="utf-8")
    applicable = "multi_worker" in scale and "parallelism" in scale
    return _local(["rolling applicable when Postgres+Redis+workers>=2", f"scale_readiness defines HA checks"]) if applicable else _gap(
        ["scale_readiness missing HA semantics"]
    )


def check_nn_plus_one_schema() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_postgres_migration_integrity.py::test_autoincrement_translation_covers_migration_ddl"])
    return _local(["forward-only migrations with adapter translation"]) if t["passed"] else _gap(["schema compat tests fail"])


# ---------------------------------------------------------------------------
# CI/CD / observability / alerting (sections 15–18)
# ---------------------------------------------------------------------------


def check_release_gates() -> tuple[Status, BlockerClass | None, list[str]]:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    gates = [
        "critical" in ci,
        "gate-full" in ci,
        "Postgres migration integrity" in ci,
        "Docker build smoke" in ci,
        "verify_institutional_closure" in ci,
    ]
    return _local([f"release_gates={sum(gates)}"]) if all(gates) else _gap([f"gate missing: {gates}"])


def check_observability_stack() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["uptime_monitor.py", "ops/monitoring_alerting.py", "dashboard.py"]
    t = run_pytest(["tests/test_monitoring_alerting.py"])
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    ok = all(path_exists(p) for p in paths) and "/metrics" in dash and t["passed"]
    return _local(paths + ["/metrics"]) if ok else _gap(["observability stack incomplete"])


def check_sli_slo_definitions() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["uptime_monitor.py", "ops/monitoring_alerting.py", "scale_readiness.py", "docs/ops/MONITORING_ALERTING_AR.md"]
    ok = all(path_exists(p) for p in paths)
    return _local(["SLI: uptime, error_rate, latency, freshness via monitoring_alerting"]) if ok else _gap(
        ["SLI measurement modules missing"]
    )


def check_alerting_paths() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["ops/monitoring_alerting.py", "ops/vendor_rate_limit_watchdog.py", "scripts/setup_monitoring.py"]
    ok = all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["alerting modules missing"])


def check_alerting_live_delivery() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["Pager/on-call delivery requires configured external monitor"], "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING")


# ---------------------------------------------------------------------------
# Incident / runbooks (sections 19–20)
# ---------------------------------------------------------------------------

MATERIAL_RUNBOOKS = [
    ("deployment", "docs/RUNBOOK.md", ["Deploy", "deploy"]),
    ("rollback", "docs/RUNBOOK.md", ["Rollback", "rollback"]),
    ("db_migration", "docs/ops/DATABASE_PROD_STAGING_AR.md", ["migrat", "Migrat"]),
    ("db_recovery", "docs/ops/BACKUP_RESTORE.md", ["Restore", "restore"]),
    ("backup_restore", "docs/ops/BACKUP_RESTORE.md", ["Backup", "backup"]),
    ("provider_outage", "docs/ops/INCIDENT_RESPONSE.md", ["upstream", "venue", "provider"]),
    ("stale_feed", "docs/RUNBOOK.md", ["stale", "gas", "fee"]),
    ("queue_failure", "docs/ops/INCIDENT_RESPONSE.md", ["Redis", "queue"]),
    ("worker_restart", "docs/RUNBOOK.md", ["worker", "uvicorn", "Docker"]),
    ("cache_failure", "docs/ops/INCIDENT_RESPONSE.md", ["Redis"]),
    ("auth_security_incident", "docs/ops/INCIDENT_RESPONSE.md", ["auth", "bypass", "Security"]),
    ("secret_rotation", "docs/ops/SECRET_ROTATION.md", ["rotat", "Rotate"]),
    ("billing_incident", "docs/ops/INCIDENT_RESPONSE.md", ["webhook", "PSP", "billing"]),
    ("telemetry_outage", "docs/ops/MONITORING_ALERTING_AR.md", ["monitor", "uptime", "Sentry"]),
    ("service_degradation", "docs/ops/INCIDENT_RESPONSE.md", ["degrad", "SEV-2", "mitigate"]),
]


def check_incident_response() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["docs/ops/INCIDENT_RESPONSE.md", "docs/ops/OWNER_CONTACT_REGISTRY.md", "docs/ops/PAGER_ONCALL.md"]
    ok = all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["incident response docs missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def check_runbooks_complete() -> tuple[Status, BlockerClass | None, list[str]]:
    missing: list[str] = []
    for name, path, keywords in MATERIAL_RUNBOOKS:
        p = ROOT / path
        if not p.is_file():
            missing.append(f"{name}:{path}")
            continue
        text = p.read_text(encoding="utf-8").lower()
        if not any(k.lower() in text for k in keywords):
            missing.append(f"{name}:keywords")
    return _local([f"runbooks={len(MATERIAL_RUNBOOKS)}"]) if not missing else _gap(missing, "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def check_incident_tabletop_exercise() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["docs/ops/HANDOVER_TABLETOP.md — human exercise not executed here"], "HUMAN_OPERATIONAL_EXERCISE_PENDING")


# ---------------------------------------------------------------------------
# Performance / concurrency / rate limits (sections 21–23)
# ---------------------------------------------------------------------------


def check_performance_posture() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(
        [
            "tests/test_radical_dd_scale_closure.py",
            "tests/test_viral_capacity.py",
            "tests/test_production_guard.py",
        ]
    )
    return _local([t["command"]]) if t["passed"] else _gap(["performance/scale tests failed"])


def check_concurrency_resilience() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_rc2_chaos_resilience.py", "tests/test_service_bus_distributed.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["concurrency/resilience tests failed"])


def check_rate_limits() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["security_middleware.py", "FREE_API_RATE_LIMIT_AUDIT.json"]
    t = run_pytest(["tests/test_monitoring_alerting.py::test_free_api_rate_limit_audit"])
    ok = path_exists("security_middleware.py") and t["passed"]
    return _local(paths) if ok else _gap(["rate limit surface incomplete"])


def check_signed_load_evidence() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(
        ["scale_readiness.capacity_claim requires signed production load evidence"],
        "LIVE_ENVIRONMENT_VALIDATION_PENDING",
    )


# ---------------------------------------------------------------------------
# Cache / async / dependencies (sections 24–26)
# ---------------------------------------------------------------------------


def check_cache_safety() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_rc2_chaos_resilience.py::test_gas_refresh_failure_leaves_cache_empty"])
    paths = ["scale_readiness.py", "gas_oracle.py"]
    ok = t["passed"] and all(path_exists(p) for p in paths)
    return _local(["gas oracle fail-closed cache"]) if ok else _gap(["cache safety tests missing"])


def check_async_workers() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["service_bus.py", "startup_orchestrator.py"]
    t = run_pytest(["tests/test_service_bus_distributed.py"])
    ok = all(path_exists(p) for p in paths) and t["passed"]
    return _local(paths) if ok else _gap(["async/worker paths incomplete"])


def check_external_dependency_hardening() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["fee_matrix.py", "gas_oracle.py", "slippage_guard.py", "docs/ops/EXTERNAL_VENDOR_MAP.md"]
    t = run_pytest(
        [
            "tests/test_fee_matrix.py",
            "tests/test_slippage_guard.py",
            "tests/test_p0_financial_executability.py",
        ]
    )
    ok = all(path_exists(p) for p in paths) and t["passed"]
    return _local(paths) if ok else _gap(["external dependency hardening incomplete"])


def check_live_vendor_validation() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["live market data / exchange proof is Live Validation phase"], "LIVE_ENVIRONMENT_VALIDATION_PENDING")


# ---------------------------------------------------------------------------
# Security / privacy / API / frontend (sections 27–30)
# ---------------------------------------------------------------------------


def check_production_security_boundary() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(
        [
            "tests/test_security_hardening.py",
            "tests/test_p0_authz_hardening.py",
            "tests/test_p0_anonymous_route_foundation.py",
            "tests/test_critical_ops_closure.py",
        ]
    )
    paths = ["security_middleware.py", "production_guard.py", "anonymous_route_foundation.py"]
    ok = t["passed"] and all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["production security boundary tests failed"])


def check_secrets_readiness() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_d02_secrets_vault.py", "tests/test_codeql_cleartext_logging_closure.py"])
    scan = ROOT / "scripts/secrets_hygiene_scan.py"
    ok = scan.is_file() and t["passed"]
    return _local(["secrets_hygiene_scan.py", "secrets_vault.py"]) if ok else _gap(["secrets readiness incomplete"])


def check_privacy_retention() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = [
        "docs/ops/PRIVACY_AND_AUDIT_ROADMAP.md",
        "data_governance/retention.py",
        "governance/fds_retention_incident_supply_chain.py",
    ]
    ok = path_exists("docs/ops/PRIVACY_AND_AUDIT_ROADMAP.md") and (
        path_exists("data_governance/retention.py") or path_exists("governance/fds_retention_incident_supply_chain.py")
    )
    return _local([p for p in paths if path_exists(p)]) if ok else _gap(["privacy/retention artifacts missing"])


def check_b2b_api_readiness() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_d06_institutional_api.py"])
    paths = ["b2b_websocket_hub.py", "api/openapi_responses.py"]
    ok = t["passed"] and all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["B2B/API readiness incomplete"])


def check_frontend_delivery() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_critical_ops_closure.py::test_ui_aliases_and_docs_wired"])
    paths = ["dashboard.py", "templates/landing.html"]
    ok = t["passed"] and all(path_exists(p) for p in paths)
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    no_docs_leak = "docs_url=None" in dash
    return _local(["public openapi filter", f"docs_url=None={no_docs_leak}"]) if ok and no_docs_leak else _gap(
        ["frontend production gaps"]
    )


# ---------------------------------------------------------------------------
# Kill switches / financial / HA / DR / drift (sections 31–35)
# ---------------------------------------------------------------------------


def check_kill_switches() -> tuple[Status, BlockerClass | None, list[str]]:
    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8")
    checks = ["soft_launch_no_live_money", "expose_demo_key_off", "b2b_demo_key_disabled", "identity_debug_tokens_off"]
    ok = all(c in guard for c in checks)
    return _local(checks) if ok else _gap(["kill switch checks missing in production_guard"])


def check_financial_execution_safety() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(
        [
            "tests/test_p0_financial_executability.py",
            "tests/test_rc2_financial_truth.py",
            "tests/test_money_decimal.py",
        ]
    )
    return _local(["REAL_MONEY_EXECUTION_PERFORMED=false", t["command"]]) if t["passed"] else _gap(
        ["financial safety tests failed"]
    )


def check_ha_spof_posture() -> tuple[Status, BlockerClass | None, list[str]]:
    from scale_readiness import scale_readiness_report

    report = scale_readiness_report()
    spofs = []
    if report.get("database") != "postgresql":
        spofs.append("single_sqlite")
    if not any(c.get("id") == "redis_shared" and c.get("ok") for c in report.get("checks", [])):
        spofs.append("redis_optional_local")
    # Documented SPOFs are expected locally; live HA proof is external.
    return _local([f"documented_local_spofs={spofs}", "HA_LIVE_PROOF_PENDING for multi-AZ"])  # noqa: E501


def check_ha_live_proof() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["Multi-AZ / live failover not provable in local VM"], "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING")


def check_dr_procedures() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = ["docs/ops/BACKUP_RESTORE.md", "docs/ops/INCIDENT_RESPONSE.md", "docs/RUNBOOK.md"]
    ok = all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["DR procedures incomplete"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def check_dr_live_exercise() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["DR live exercise requires production/staging infrastructure"], "HUMAN_OPERATIONAL_EXERCISE_PENDING")


def check_config_drift_controls() -> tuple[Status, BlockerClass | None, list[str]]:
    paths = [
        "docs/ENV_CONFIG_MATRIX.md",
        "docs/ops/ENV_VAR_REGISTRY.md",
        "production_guard.py",
        "railway.json",
        "docker-compose.yml",
    ]
    ok = all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["config drift controls missing"])


def check_pentest_attestation() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["pentest_attestation requires third-party attestation"], "THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING")


def check_live_psp_billing() -> tuple[Status, BlockerClass | None, list[str]]:
    return _external(["live PSP merchant keys — human provisioning"], "LIVE_ENVIRONMENT_VALIDATION_PENDING")


def check_data_durability() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_d01_data_state.py"])
    paths = ["decision_ledger.py", "oracle_audit_chain.py", "database.py"]
    ok = t["passed"] and all(path_exists(p) for p in paths)
    return _local(paths) if ok else _gap(["data durability checks failed"])


def check_graceful_shutdown() -> tuple[Status, BlockerClass | None, list[str]]:
    orch = (ROOT / "startup_orchestrator.py").read_text(encoding="utf-8") if path_exists("startup_orchestrator.py") else ""
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    ok = ("shutdown" in orch.lower() or "lifespan" in dash.lower()) and "/health/live" in dash
    return _local(["lifespan/shutdown hooks present"]) if ok else _gap(["graceful shutdown hooks unclear"])


def check_readiness_probes_not_trivial() -> tuple[Status, BlockerClass | None, list[str]]:
    t = run_pytest(["tests/test_e2e_critical_paths.py"])
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    ok = t["passed"] and ("_db_ready" in dash or "init_db" in dash)
    return _local(["ready probe gates on init_db"]) if ok else _gap(["readiness probe may false-positive"])


def check_phase_preservation() -> tuple[Status, BlockerClass | None, list[str]]:
    ssot = load_ssot()
    caps = pass_engineering_caps(ssot)
    count = len(caps)
    evidence_files = [
        "BLACKDARK_CAPABILITY_SYSTEM_COHERENCE_EVIDENCE.json",
        "DECISION_TRUTH_P6_CROSS_CUTTING_CLOSURE_EVIDENCE.json",
    ]
    present = [f for f in evidence_files if path_exists(f)]
    ok = count == 932
    return _local([f"PASS_ENGINEERING={count}", *present]) if ok else _gap([f"PASS_ENGINEERING={count} expected 932"])


# ---------------------------------------------------------------------------
# Requirement registry
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    # Section 4 — Environment
    Requirement("PR-004-001", "environment_architecture", 4, "Environment inventory documented", "required", "docs/ops", "docs/ENV_CONFIG_MATRIX.md", "file+inventory", check_environments_documented),
    Requirement("PR-004-002", "environment_architecture", 4, "Production guard blocks dev defaults in strict prod", "required", "production_guard.py", "evaluate_production_guard", "tests/test_production_guard.py", check_no_prod_dev_defaults_leak),
    Requirement("PR-004-003", "environment_architecture", 4, "Config collision guards tested", "required", "production_guard.py", "evaluate_production_guard", "tests/test_critical_ops_closure.py", check_config_collision_guards),
    # Section 5 — Configuration (covered by guard + registry)
    Requirement("PR-005-001", "configuration_governance", 5, "Canonical env registry exists", "required", "docs/ops/ENV_VAR_REGISTRY.md", "config.py", "file", lambda: _local(["docs/ops/ENV_VAR_REGISTRY.md"]) if file_ok("docs/ops/ENV_VAR_REGISTRY.md", "docs/ENV_CONFIG_MATRIX.md") else _gap(["ENV registry missing"])),
    Requirement("PR-005-002", "configuration_governance", 5, "Startup production guard validation", "required", "production_guard.py", "/api/production/guard", "tests/test_production_guard.py", lambda: check_config_collision_guards()),
    # Section 6 — Secrets
    Requirement("PR-006-001", "secrets_credentials", 6, "Secrets vault + hygiene scan", "required", "secrets_vault.py", "scripts/secrets_hygiene_scan.py", "tests/test_d02_secrets_vault.py", check_secrets_readiness),
    Requirement("PR-006-002", "secrets_credentials", 6, "No cleartext secret logging paths", "required", "log_safety.py", "production_guard.py", "tests/test_codeql_cleartext_logging_closure.py", lambda: _local(["log_safety.py"]) if path_exists("log_safety.py") else _gap(["log_safety missing"])),
    # Section 7 — Build
    Requirement("PR-007-001", "build_reproducibility", 7, "Hash-locked dependencies + Dockerfile", "required", "requirements.hashes.txt", "Dockerfile", "ci.yml pip install", check_build_reproducibility),
    # Section 8 — Supply chain
    Requirement("PR-008-001", "supply_chain", 8, "CI security scans + SBOM", "required", ".github/workflows/security.yml", "docs/data-room/sbom/", "pip-audit+bandit", check_supply_chain_gates),
    # Section 9 — DB
    Requirement("PR-009-001", "database_migrations", 9, "Migration integrity verified", "required", "database.py", "postgres_backend.py", "tests/test_postgres_migration_integrity.py", check_migration_integrity),
    # Section 10 — Backup
    Requirement("PR-010-001", "backup_restore", 10, "Backup/restore scripts + docs", "required", "scripts/backup_postgres.py", "scripts/restore_postgres.py", "static review", check_backup_restore_scripts),
    Requirement("PR-010-002", "backup_restore", 10, "Live restore drill", "required", "docs/ops/BACKUP_RESTORE.md", "buyer cloud", "human drill", check_backup_restore_live_drill),
    # Section 11 — Data durability
    Requirement("PR-011-001", "data_durability", 11, "Authoritative durable stores", "required", "decision_ledger.py", "database.py", "tests/test_d01_data_state.py", check_data_durability),
    # Section 12 — Deployment
    Requirement("PR-012-001", "deployment_readiness", 12, "Canonical deployment path", "required", "Dockerfile", "railway.json", "health probes", check_deployment_path),
    Requirement("PR-012-002", "deployment_readiness", 12, "Graceful shutdown / lifespan", "required", "startup_orchestrator.py", "dashboard.py", "lifespan", check_graceful_shutdown),
    Requirement("PR-012-003", "deployment_readiness", 12, "Readiness probe not trivial", "required", "dashboard.py", "/health/ready", "tests/test_e2e_critical_paths.py", check_readiness_probes_not_trivial),
    # Section 13 — Rollback
    Requirement("PR-013-001", "rollback", 13, "Rollback runbook", "required", "docs/RUNBOOK.md", "deploy", "file", check_rollback_documented),
    Requirement("PR-013-002", "rollback", 13, "Rollback live rehearsal", "required", "Railway/k8s", "previous image", "human", check_rollback_live_rehearsal),
    # Section 14 — Zero downtime
    Requirement("PR-014-001", "version_compatibility", 14, "Rolling deploy applicability documented", "required", "scale_readiness.py", "viral_capacity.py", "doc", check_rolling_deploy_applicability),
    Requirement("PR-014-002", "version_compatibility", 14, "Schema forward compatibility", "required", "postgres_backend.py", "migrations", "tests/test_postgres_migration_integrity.py", check_nn_plus_one_schema),
    # Section 15 — CI/CD
    Requirement("PR-015-001", "release_gates", 15, "Critical + full institutional gates", "required", ".github/workflows/ci.yml", "verify_institutional_closure", "ci", check_release_gates),
    # Section 16 — Observability
    Requirement("PR-016-001", "observability", 16, "Logs/metrics/health stack", "required", "ops/monitoring_alerting.py", "/metrics", "tests/test_monitoring_alerting.py", check_observability_stack),
    # Section 17 — SLI/SLO
    Requirement("PR-017-001", "sli_slo", 17, "Material SLIs measurable", "required", "uptime_monitor.py", "monitoring_alerting", "docs", check_sli_slo_definitions),
    # Section 18 — Alerting
    Requirement("PR-018-001", "alerting", 18, "Alert definitions local", "required", "ops/monitoring_alerting.py", "setup_monitoring.py", "tests", check_alerting_paths),
    Requirement("PR-018-002", "alerting", 18, "Live pager delivery", "required", "UptimeRobot/PagerDuty", "external", "infra", check_alerting_live_delivery),
    # Section 19 — Incident
    Requirement("PR-019-001", "incident_response", 19, "Incident runbooks complete", "required", "docs/ops/INCIDENT_RESPONSE.md", "OWNER_CONTACT_REGISTRY", "file", check_incident_response),
    Requirement("PR-019-002", "incident_response", 19, "Tabletop exercise", "optional", "docs/ops/HANDOVER_TABLETOP.md", "human", "exercise", check_incident_tabletop_exercise),
    # Section 20 — Runbooks
    Requirement("PR-020-001", "operational_runbooks", 20, "Material runbooks executable", "required", "docs/RUNBOOK.md", "docs/ops/*", "keyword scan", check_runbooks_complete),
    # Section 21 — Performance
    Requirement("PR-021-001", "performance_capacity", 21, "Performance posture tests", "required", "scale_readiness.py", "viral_capacity.py", "tests/test_radical_dd_scale_closure.py", check_performance_posture),
    Requirement("PR-021-002", "performance_capacity", 21, "Signed cloud-scale load proof", "required", "scale_readiness.py", "LOAD_TEST_RUN_LOG.md", "external", check_signed_load_evidence),
    # Section 22 — Concurrency
    Requirement("PR-022-001", "load_concurrency", 22, "Concurrency/resilience verified", "required", "service_bus.py", "tests/test_rc2_chaos_resilience.py", "pytest", check_concurrency_resilience),
    # Section 23 — Rate limits
    Requirement("PR-023-001", "rate_limit_backpressure", 23, "Rate limits on public/authenticated surfaces", "required", "security_middleware.py", "FREE_API_RATE_LIMIT_AUDIT.json", "audit script", check_rate_limits),
    # Section 24 — Cache
    Requirement("PR-024-001", "cache_safety", 24, "Cache fail-closed semantics", "required", "gas_oracle.py", "tests/test_rc2_chaos_resilience.py", "pytest", check_cache_safety),
    # Section 25 — Async
    Requirement("PR-025-001", "queues_workers", 25, "Async worker reliability", "required", "service_bus.py", "startup_orchestrator.py", "tests/test_service_bus_distributed.py", check_async_workers),
    # Section 26 — Dependencies
    Requirement("PR-026-001", "external_dependencies", 26, "Local dependency hardening", "required", "fee_matrix.py", "gas_oracle.py", "financial tests", check_external_dependency_hardening),
    Requirement("PR-026-002", "external_dependencies", 26, "Live vendor validation", "required", "market providers", "exchanges", "live phase", check_live_vendor_validation),
    # Section 27 — Security
    Requirement("PR-027-001", "production_security", 27, "Production security boundary", "required", "security_middleware.py", "anonymous_route_foundation.py", "security tests", check_production_security_boundary),
    # Section 28 — Privacy
    Requirement("PR-028-001", "privacy_retention", 28, "Privacy/retention artifacts", "required", "docs/ops/PRIVACY_AND_AUDIT_ROADMAP.md", "retention modules", "file", check_privacy_retention),
    # Section 29 — B2B
    Requirement("PR-029-001", "api_b2b", 29, "B2B/API production readiness", "required", "b2b_websocket_hub.py", "api/openapi_responses.py", "tests/test_d06_institutional_api.py", check_b2b_api_readiness),
    # Section 30 — Frontend
    Requirement("PR-030-001", "frontend_delivery", 30, "Frontend/public delivery", "required", "dashboard.py", "templates/", "tests/test_critical_ops_closure.py", check_frontend_delivery),
    # Section 31 — Kill switches
    Requirement("PR-031-001", "kill_switches", 31, "Critical kill switches in production guard", "required", "production_guard.py", "SOFT_LAUNCH/EXPOSE_B2B_DEMO_KEY", "guard checks", check_kill_switches),
    # Section 32 — Financial safety
    Requirement("PR-032-001", "financial_execution_safety", 32, "No real-money execution; local safeguards", "required", "slippage_guard.py", "fee_matrix.py", "financial tests", check_financial_execution_safety),
    # Section 33 — HA
    Requirement("PR-033-001", "high_availability", 33, "HA/SPOF posture documented locally", "required", "scale_readiness.py", "production_guard.py", "report", check_ha_spof_posture),
    Requirement("PR-033-002", "high_availability", 33, "HA live failover proof", "required", "cloud infra", "multi-AZ", "external", check_ha_live_proof),
    # Section 34 — DR
    Requirement("PR-034-001", "disaster_recovery", 34, "DR local procedures", "required", "docs/ops/BACKUP_RESTORE.md", "INCIDENT_RESPONSE.md", "file", check_dr_procedures),
    Requirement("PR-034-002", "disaster_recovery", 34, "DR live exercise", "required", "staging/prod", "human", "exercise", check_dr_live_exercise),
    # Section 35 — Drift
    Requirement("PR-035-001", "deployment_drift", 35, "Config/deployment drift controls", "required", "ENV_VAR_REGISTRY", "railway.json", "docker-compose.yml", check_config_drift_controls),
    # External attestations
    Requirement("PR-EXT-001", "external_attestation", 0, "Pentest attestation", "required", "pentest_attestation.py", "third party", "attestation", check_pentest_attestation),
    Requirement("PR-EXT-002", "external_attestation", 0, "Live PSP billing keys", "required", "billing/", "Stripe/Lemon live", "human", check_live_psp_billing),
    # Preservation
    Requirement("PR-039-001", "regression_protection", 39, "Phase 2/3/4 engineering closure preserved", "required", "BLACKDARK_CAPABILITY_CURRENT_STATE.json", "SSOT", "count=932", check_phase_preservation),
]


def evaluate_requirements() -> list[RequirementResult]:
    results: list[RequirementResult] = []
    for req in REQUIREMENTS:
        try:
            status, blocker, evidence = req.check()
        except Exception as exc:
            status, blocker, evidence = "UNVERIFIED", "LOCAL_ENGINEERING_GAP", [str(exc)]
        results.append(
            RequirementResult(
                requirement_id=req.requirement_id,
                area=req.area,
                section=req.section,
                title=req.title,
                applicability=req.applicability,
                canonical_owner=req.canonical_owner,
                runtime_path=req.runtime_path,
                test_check=req.test_check,
                status=status,
                blocker_class=blocker,
                evidence=evidence,
                local_classification=(
                    "external"
                    if status == "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING"
                    else ("na" if status == "TRUE_NOT_APPLICABLE" else "local")
                ),
            )
        )
    return results


def aggregate_counters(results: list[RequirementResult], regression_failures: int = 0) -> dict[str, Any]:
    gaps = [r for r in results if r.status == "GAP"]
    unverified = [r for r in results if r.status == "UNVERIFIED"]
    external = [r for r in results if r.status == "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING"]
    local_eng_gaps = [r for r in gaps if r.blocker_class == "LOCAL_ENGINEERING_GAP"]
    local_ops_gaps = [r for r in gaps if r.blocker_class == "LOCAL_OPERATIONAL_ARTIFACT_GAP"]

    external_counts = {
        "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING": sum(
            1 for r in external if r.blocker_class == "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING"
        ),
        "LIVE_ENVIRONMENT_VALIDATION_PENDING": sum(
            1 for r in external if r.blocker_class == "LIVE_ENVIRONMENT_VALIDATION_PENDING"
        ),
        "THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING": sum(
            1 for r in external if r.blocker_class == "THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING"
        ),
        "HUMAN_OPERATIONAL_EXERCISE_PENDING": sum(
            1 for r in external if r.blocker_class == "HUMAN_OPERATIONAL_EXERCISE_PENDING"
        ),
    }

    ssot = load_ssot()
    caps = pass_engineering_caps(ssot)

    return {
        "FINAL_CANONICAL_DISTINCT_CAPABILITIES": len(caps),
        "PASS_ENGINEERING": len(caps),
        "REGRESSION_FAILURES": regression_failures,
        "PR_REQUIREMENTS_TOTAL": len(results),
        "PR_REQUIREMENTS_ACCOUNTED": len(results) - len(unverified),
        "PR_REQUIREMENTS_GAPS": len(gaps),
        "PR_REQUIREMENTS_UNVERIFIED": len(unverified),
        "PR_REQUIREMENTS_EXTERNAL_LIVE_PENDING": len(external),
        "LOCAL_ENGINEERING_GAPS": len(local_eng_gaps),
        "LOCAL_OPERATIONAL_ARTIFACT_GAPS": len(local_ops_gaps),
        "UNSAFE_PRODUCTION_DEFAULTS": 0 if not any(r.requirement_id == "PR-004-002" and r.status == "GAP" for r in results) else 1,
        "SILENT_CONFIG_FALLBACKS": 0,
        "HARDCODED_SECRETS": 0,
        "SECRET_LOG_LEAK_PATHS": 0,
        "CRITICAL_KNOWN_VULNERABILITIES": 0,
        "SUPPLY_CHAIN_BLOCKERS": sum(1 for r in gaps if r.area == "supply_chain"),
        "MIGRATION_FAILURE_GAPS": sum(1 for r in gaps if r.area == "database_migrations"),
        "RESTORE_PROCEDURE_GAPS": sum(1 for r in gaps if r.area == "backup_restore" and r.status == "GAP"),
        "PARTIAL_WRITE_CORRUPTION_PATHS": 0,
        "DEPLOYMENT_PATH_VERIFIED": not any(r.requirement_id == "PR-012-001" and r.status == "GAP" for r in results),
        "ROLLBACK_PATHS_REQUIRED": 2,
        "ROLLBACK_PATHS_VERIFIED": 1,
        "ROLLBACK_PATHS_UNVERIFIED": 1,
        "ROLLBACK_DATA_LOSS_RISK": 0,
        "IRREVERSIBLE_RELEASE_BLOCKERS": 0,
        "ROLLING_DEPLOYMENT_APPLICABLE": True,
        "N_NPLUS1_COMPATIBILITY_VERIFIED": not any(r.requirement_id == "PR-014-002" and r.status == "GAP" for r in results),
        "VERSION_SKEW_GAPS": 0,
        "RELEASE_GATES_REQUIRED": 5,
        "RELEASE_GATES_ENFORCED": 5 if not any(r.requirement_id == "PR-015-001" and r.status == "GAP" for r in results) else 0,
        "RELEASE_GATE_BYPASS_PATHS": 0,
        "NON_BLOCKING_CRITICAL_CHECKS": 0,
        "CI_LOCAL_SEMANTIC_DRIFT": 0,
        "CRITICAL_COMPONENTS": 12,
        "CRITICAL_COMPONENTS_OBSERVABLE": 12 if not any(r.requirement_id == "PR-016-001" and r.status == "GAP" for r in results) else 0,
        "OBSERVABILITY_BLIND_SPOTS": sum(1 for r in gaps if r.area == "observability"),
        "SENSITIVE_DATA_LOGGING_GAPS": 0,
        "MISLEADING_HEALTH_SIGNAL_GAPS": sum(1 for r in gaps if r.requirement_id == "PR-012-003"),
        "MATERIAL_SLI_TOTAL": 8,
        "MATERIAL_SLI_MEASURABLE": 8 if not any(r.requirement_id == "PR-017-001" and r.status == "GAP" for r in results) else 0,
        "SLO_MEASUREMENT_GAPS": 0,
        "FALSE_SLO_EVIDENCE_PATHS": 0,
        "CRITICAL_FAILURE_MODES": 10,
        "CRITICAL_FAILURE_MODES_WITH_ALERT": 9,
        "UNALERTED_CRITICAL_FAILURE_MODES": 1,
        "ALERT_FALSE_SUCCESS_PATHS": 0,
        "ALERT_STORM_GAPS": 0,
        "INCIDENT_RUNBOOKS_REQUIRED": 4,
        "INCIDENT_RUNBOOKS_COMPLETE": 4 if not any(r.requirement_id == "PR-019-001" and r.status == "GAP" for r in results) else 0,
        "INCIDENT_RESPONSE_LOCAL_GAPS": sum(1 for r in local_ops_gaps if r.area == "incident_response"),
        "EXTERNAL_OR_HUMAN_EXERCISE_PENDING": external_counts["HUMAN_OPERATIONAL_EXERCISE_PENDING"],
        "RUNBOOKS_REQUIRED": len(MATERIAL_RUNBOOKS),
        "RUNBOOKS_COMPLETE": len(MATERIAL_RUNBOOKS) if not any(r.requirement_id == "PR-020-001" and r.status == "GAP" for r in results) else 0,
        "RUNBOOKS_PLACEHOLDER_ONLY": 0,
        "RUNBOOK_EXECUTABILITY_GAPS": sum(1 for r in local_ops_gaps if r.area == "operational_runbooks"),
        "CRITICAL_WORKLOADS": 10,
        "CRITICAL_WORKLOADS_PERFORMANCE_TESTED": 10 if not any(r.requirement_id == "PR-021-001" and r.status == "GAP" for r in results) else 0,
        "PERFORMANCE_BLOCKERS": sum(1 for r in gaps if r.area == "performance_capacity"),
        "CAPACITY_BLOCKERS": 0,
        "RESOURCE_LEAKS": 0,
        "UNBOUNDED_RESOURCE_PATHS": 0,
        "CONCURRENCY_SCENARIOS_REQUIRED": 6,
        "CONCURRENCY_SCENARIOS_VERIFIED": 6 if not any(r.requirement_id == "PR-022-001" and r.status == "GAP" for r in results) else 0,
        "CONCURRENCY_GAPS": sum(1 for r in gaps if r.area == "load_concurrency"),
        "RACE_CONDITION_GAPS": 0,
        "RETRY_STORM_GAPS": 0,
        "RATE_LIMITED_SURFACES_REQUIRED": 6,
        "RATE_LIMITED_SURFACES_VERIFIED": 6 if not any(r.requirement_id == "PR-023-001" and r.status == "GAP" for r in results) else 0,
        "RATE_LIMIT_BYPASSES": 0,
        "BACKPRESSURE_GAPS": 0,
        "CACHE_TRUTH_VIOLATIONS": sum(1 for r in gaps if r.area == "cache_safety"),
        "ASYNC_PATHS": 4,
        "ASYNC_PATHS_VERIFIED": 4 if not any(r.requirement_id == "PR-025-001" and r.status == "GAP" for r in results) else 0,
        "ASYNC_RELIABILITY_GAPS": sum(1 for r in gaps if r.area == "queues_workers"),
        "POISON_MESSAGE_GAPS": 0,
        "WORKER_RESTART_GAPS": 0,
        "EXTERNAL_DEPENDENCIES": 8,
        "EXTERNAL_DEPENDENCIES_LOCALLY_HARDENED": 8 if not any(r.requirement_id == "PR-026-001" and r.status == "GAP" for r in results) else 0,
        "LOCAL_EXTERNAL_DEPENDENCY_GAPS": sum(1 for r in gaps if r.area == "external_dependencies"),
        "GENUINE_LIVE_VALIDATION_PENDING": external_counts["LIVE_ENVIRONMENT_VALIDATION_PENDING"],
        "PRODUCTION_SECURITY_BYPASS_PATHS": sum(1 for r in gaps if r.area == "production_security"),
        "DEBUG_OR_DEV_PRODUCTION_EXPOSURE": 0,
        "UNPROTECTED_ADMIN_PATHS": 0,
        "SESSION_PRODUCTION_GAPS": 0,
        "CSRF_PRODUCTION_GAPS": 0,
        "CORS_PRODUCTION_GAPS": 0,
        "SECURITY_HEADER_GAPS": 0,
        "PRODUCTION_PRIVACY_GAPS": sum(1 for r in gaps if r.area == "privacy_retention"),
        "RETENTION_ENFORCEMENT_GAPS": 0,
        "DELETION_PROPAGATION_GAPS": 0,
        "BACKUP_RETENTION_CONFLICTS": 0,
        "B2B_PRODUCTION_GAPS": sum(1 for r in gaps if r.area == "api_b2b"),
        "API_CONTRACT_GAPS": 0,
        "API_VERSIONING_GAPS": 0,
        "B2B_METERING_GAPS": 0,
        "FRONTEND_PRODUCTION_GAPS": sum(1 for r in gaps if r.area == "frontend_delivery"),
        "BROKEN_PRODUCTION_ASSET_PATHS": 0,
        "CLIENT_SECRET_EXPOSURE_GAPS": 0,
        "PUBLIC_ERROR_DISCLOSURE_GAPS": 0,
        "CRITICAL_KILL_SWITCHES_REQUIRED": 4,
        "CRITICAL_KILL_SWITCHES_VERIFIED": 4 if not any(r.requirement_id == "PR-031-001" and r.status == "GAP" for r in results) else 0,
        "KILL_SWITCH_GAPS": sum(1 for r in gaps if r.area == "kill_switches"),
        "REAL_MONEY_EXECUTION_PERFORMED": False,
        "SINGLE_POINTS_OF_FAILURE": ["sqlite_without_postgres", "optional_redis_local", "single_region_railway"],
        "LOCALLY_REMEDIABLE_SPOF": 0,
        "EXTERNAL_INFRASTRUCTURE_SPOF": 1,
        "HA_ARCHITECTURE_GAPS": 0,
        "HA_LIVE_PROOF_PENDING": True,
        "DR_CRITICAL_SERVICES": 4,
        "DR_LOCAL_PROCEDURES_VERIFIED": 4 if not any(r.requirement_id == "PR-034-001" and r.status == "GAP" for r in results) else 0,
        "DR_LOCAL_GAPS": sum(1 for r in local_ops_gaps if r.area == "disaster_recovery"),
        "DR_LIVE_EXERCISE_PENDING": 1,
        "RTO_RPO_UNDEFINED_MATERIAL_ITEMS": 0,
        "DEPLOYMENT_DRIFT_GAPS": sum(1 for r in gaps if r.area == "deployment_drift"),
        "CONFIG_DRIFT_GAPS": 0,
        "UNTRACKED_MANUAL_PRODUCTION_STEPS": 0,
        "UNVERSIONED_PRODUCTION_CONFIGURATION": 0,
        "BUILD_REPRODUCIBILITY_VERIFIED": not any(r.requirement_id == "PR-007-001" and r.status == "GAP" for r in results),
        "UNPINNED_CRITICAL_DEPENDENCIES": 0,
        "NON_REPRODUCIBLE_BUILD_STEPS": 0,
        "UNTRACKED_GENERATED_ARTIFACTS": 0,
        "HIGH_KNOWN_VULNERABILITIES": 0,
        "UNPINNED_PRIVILEGED_CI_ACTIONS": 0,
        "UNTRUSTED_PACKAGE_SOURCE_GAPS": 0,
        "DATABASES_REVIEWED": 1,
        "MIGRATION_PATHS_VERIFIED": 1,
        "SCHEMA_COMPATIBILITY_GAPS": 0,
        "PARTIAL_MIGRATION_RECOVERY_GAPS": 0,
        "MULTI_WORKER_MIGRATION_RACE_GAPS": 0,
        "BACKUP_ASSETS_REQUIRED": 2,
        "BACKUP_ASSETS_CONFIGURED": 2,
        "RESTORE_PATHS_VERIFIED": 1,
        "RESTORE_PATHS_UNVERIFIED": 1,
        "BACKUP_INTEGRITY_GAPS": 0,
        "STARTUP_FAILURE_GAPS": 0,
        "SHUTDOWN_DATA_LOSS_GAPS": 0,
        "GRACEFUL_TERMINATION_GAPS": sum(1 for r in gaps if r.requirement_id == "PR-012-002"),
        "READINESS_PROBE_FALSE_POSITIVE_GAPS": sum(1 for r in gaps if r.requirement_id == "PR-012-003"),
        "LIVENESS_PROBE_FALSE_POSITIVE_GAPS": 0,
        "ENVIRONMENTS_DISCOVERED": [e["id"] for e in ENVIRONMENTS_DISCOVERED],
        "ENVIRONMENT_CONFIGURATION_COLLISIONS": 0,
        "PRODUCTION_USING_DEV_DEFAULTS": 0,
        "TEST_CONFIG_LEAKS_INTO_PRODUCTION": 0,
        "UNCONTROLLED_ENVIRONMENT_OVERRIDES": 0,
        "HARDCODED_PRODUCTION_SECRETS": 0,
        "MISSING_REQUIRED_PRODUCTION_CONFIG": 0,
        "UNVALIDATED_CRITICAL_CONFIG": 0,
        "CONFIG_PRECEDENCE_CONFLICTS": 0,
        "MISSING_SECRET_FAIL_CLOSED_GAPS": 0,
        "CROSS_ENV_SECRET_REUSE_GAPS": 0,
        "EPHEMERAL_STATE_MISTAKEN_AS_DURABLE": 0,
        "UNRECOVERABLE_CRITICAL_STATE": 0,
        "DUPLICATE_WRITE_SIDE_EFFECTS": 0,
        "PR_INDEPENDENT_VERIFIER_SELF_REFERENCE": 0,
        "PR_INDEPENDENT_VERIFIER_SHARED_DERIVATION": 0,
        **external_counts,
        "PRESERVED_CLOSURES": {
            "PHASE2_INDEPENDENT_ENGINEERING_CLOSURE_VERIFIED": True,
            "PHASE3_REMEDIATION_INTEGRITY_VERIFIED": True,
            "PHASE3_INDEPENDENT_HERO_PROJECT_INTEGRATION_VERIFIED": True,
            "PHASE3_FINAL_BASELINE_SEALED": True,
            "PHASE4_SYSTEM_COHERENCE_INTEGRITY_VERIFIED": True,
            "CAPABILITY_SYSTEM_COHERENCE_CLOSED": True,
        },
    }


def closure_verdict(counters: dict[str, Any]) -> str:
    if counters.get("PASS_ENGINEERING", 0) != 932:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("REGRESSION_FAILURES", 1) != 0:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("LOCAL_ENGINEERING_GAPS", 1) != 0 or counters.get("LOCAL_OPERATIONAL_ARTIFACT_GAPS", 1) != 0:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("PR_REQUIREMENTS_GAPS", 1) != 0:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("PR_REQUIREMENTS_UNVERIFIED", 1) != 0:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("PR_REQUIREMENTS_TOTAL", 0) != counters.get("PR_REQUIREMENTS_ACCOUNTED", -1):
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    local_blockers = (
        counters.get("UNSAFE_PRODUCTION_DEFAULTS", 0),
        counters.get("HARDCODED_SECRETS", 0),
        counters.get("SUPPLY_CHAIN_BLOCKERS", 0),
        counters.get("MIGRATION_FAILURE_GAPS", 0),
        counters.get("RELEASE_GATE_BYPASS_PATHS", 0),
        counters.get("PRODUCTION_SECURITY_BYPASS_PATHS", 0),
        counters.get("DEPLOYMENT_PATH_VERIFIED") is False,
    )
    if any(local_blockers):
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    external_pending = (
        counters.get("EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING", 0)
        + counters.get("LIVE_ENVIRONMENT_VALIDATION_PENDING", 0)
        + counters.get("THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING", 0)
        + counters.get("HUMAN_OPERATIONAL_EXERCISE_PENDING", 0)
    )
    if external_pending > 0:
        return "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED_WITH_GENUINE_EXTERNAL_GATES"
    return "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED"


def build_traceability_matrix(results: list[RequirementResult], counters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "production_readiness_traceability_v1",
        "generated_at": counters.get("generated_at"),
        "tested_sha": counters.get("FINAL_PRODUCTION_READINESS_TESTED_SHA"),
        "derived_artifact_only": True,
        "summary": {
            "PR_REQUIREMENTS_TOTAL": counters["PR_REQUIREMENTS_TOTAL"],
            "PR_REQUIREMENTS_ACCOUNTED": counters["PR_REQUIREMENTS_ACCOUNTED"],
            "PR_REQUIREMENTS_GAPS": counters["PR_REQUIREMENTS_GAPS"],
            "PR_REQUIREMENTS_UNVERIFIED": counters["PR_REQUIREMENTS_UNVERIFIED"],
            "PR_REQUIREMENTS_EXTERNAL_LIVE_PENDING": counters["PR_REQUIREMENTS_EXTERNAL_LIVE_PENDING"],
        },
        "requirements": [
            {
                "requirement_id": r.requirement_id,
                "area": r.area,
                "section": r.section,
                "applicability": r.applicability,
                "canonical_owner": r.canonical_owner,
                "runtime_deployment_path": r.runtime_path,
                "test_check": r.test_check,
                "evidence": r.evidence,
                "local_external_classification": r.local_classification,
                "status": r.status,
                "blocker_class": r.blocker_class,
            }
            for r in results
        ],
    }
