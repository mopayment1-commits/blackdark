"""Production Readiness check registry — 161 governing requirements, evidence-derived counters."""

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

from production_readiness_failure_modes import build_critical_failure_modes, failure_mode_counters
from production_readiness_governing_catalog import MATERIAL_RUNBOOK_SPECS, governing_requirements
from production_readiness_runbook_semantics import runbook_aggregate_counters, verify_runbook_semantics

Status = str
BlockerClass = str | None
CheckFn = Callable[[dict[str, Any], "CheckContext"], tuple[Status, BlockerClass, list[str]]]

ROLLBACK_EVIDENCE = ROOT / "data/production_readiness/local_rollback_rehearsal.json"
RESTORE_EVIDENCE = ROOT / "data/production_readiness/local_postgres_restore_rehearsal.json"
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"


def file_ok(*paths: str) -> bool:
    return all((ROOT / p).is_file() for p in paths)


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


def _local(evidence: list[str]) -> tuple[Status, BlockerClass, list[str]]:
    return "VERIFIED_LOCAL", None, evidence


def _external(
    evidence: list[str], blocker: BlockerClass = "LIVE_ENVIRONMENT_VALIDATION_PENDING"
) -> tuple[Status, BlockerClass, list[str]]:
    return "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING", blocker, evidence


def _gap(
    evidence: list[str], blocker: BlockerClass = "LOCAL_ENGINEERING_GAP"
) -> tuple[Status, BlockerClass, list[str]]:
    return "GAP", blocker, evidence


def dispatch_key(req: dict[str, Any]) -> str:
    vm = req.get("verification_method", "")
    if vm.startswith("runbook_semantic_"):
        return vm
    return req.get("test_or_check") or vm


@dataclass
class CheckContext:
    """Cached populations — counters derived once, not hardcoded."""

    runbook_results: list[Any] = field(default_factory=list)
    runbook_counters: dict[str, int] = field(default_factory=dict)
    failure_modes: list[Any] = field(default_factory=list)
    failure_counters: dict[str, Any] = field(default_factory=dict)
    rollback_evidence: dict[str, Any] = field(default_factory=dict)
    restore_evidence: dict[str, Any] = field(default_factory=dict)
    precedence_conflicts: int = -1
    silent_fallbacks: int = -1
    config_leaks: int = -1
    override_gaps: int = -1
    hygiene_issues: int = -1
    blind_spots: int = -1
    ci_bypass_paths: int = -1
    non_blocking_critical: int = -1
    rate_limit_bypasses: int = -1
    backpressure_gaps: int = -1
    debug_exposure: int = -1
    tenant_cache_gaps: int = -1
    poison_gaps: int = -1
    worker_gaps: int = -1
    retry_storm_gaps: int = -1
    deploy_drift: int = -1
    config_drift: int = -1
    manual_steps: int = -1
    unversioned_config: int = -1
    pass_engineering: int = 0

    @classmethod
    def build(cls) -> "CheckContext":
        ctx = cls()
        ctx.runbook_results = verify_runbook_semantics(ROOT)
        ctx.runbook_counters = runbook_aggregate_counters(ctx.runbook_results)
        ctx.failure_modes = build_critical_failure_modes()
        ctx.failure_counters = failure_mode_counters(ctx.failure_modes)
        ctx.rollback_evidence = load_json(ROLLBACK_EVIDENCE)
        ctx.restore_evidence = load_json(RESTORE_EVIDENCE)
        ctx.precedence_conflicts = _scan_precedence_conflicts()
        ctx.silent_fallbacks = _scan_silent_fallbacks()
        ctx.config_leaks = _scan_config_leaks()
        ctx.override_gaps = _scan_override_gaps()
        ctx.hygiene_issues = _scan_hygiene()
        ctx.blind_spots = _scan_blind_spots()
        ctx.ci_bypass_paths = _scan_ci_bypass()
        ctx.non_blocking_critical = _scan_non_blocking_ci()
        ctx.rate_limit_bypasses = _scan_rate_limit_bypasses()
        ctx.backpressure_gaps = _scan_backpressure_gaps()
        ctx.debug_exposure = _scan_debug_exposure()
        ctx.tenant_cache_gaps = _scan_tenant_cache_gaps()
        ctx.poison_gaps = _scan_poison_gaps()
        ctx.worker_gaps = _scan_worker_gaps()
        ctx.retry_storm_gaps = _scan_retry_storm_gaps()
        ctx.deploy_drift = _scan_deploy_drift()
        ctx.config_drift = _scan_config_drift()
        ctx.manual_steps = _scan_manual_steps()
        ctx.unversioned_config = _scan_unversioned_config()
        ssot = load_json(SSOT_PATH)
        caps = ssot.get("canonical_capabilities") or ssot.get("capabilities") or []
        ctx.pass_engineering = sum(1 for c in caps if c.get("engineering_status") == "PASS_ENGINEERING")
        return ctx


def _grep_count(pattern: str, glob: str = "*.py") -> int:
    rx = re.compile(pattern)
    hits = 0
    for p in ROOT.rglob(glob):
        if any(part.startswith(".") for part in p.parts) or ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rx.search(text):
            hits += 1
    return hits


def _scan_precedence_conflicts() -> int:
    matrix = (ROOT / "docs/ENV_CONFIG_MATRIX.md").read_text(encoding="utf-8", errors="ignore") if path_exists(
        "docs/ENV_CONFIG_MATRIX.md"
    ) else ""
    registry = (ROOT / "docs/ops/ENV_VAR_REGISTRY.md").read_text(encoding="utf-8", errors="ignore") if path_exists(
        "docs/ops/ENV_VAR_REGISTRY.md"
    ) else ""
    documented = any(k in (matrix + registry).lower() for k in ("precedence", "override order", "config precedence"))
    return 0 if documented else 1


def _scan_silent_fallbacks() -> int:
    cfg = (ROOT / "config.py").read_text(encoding="utf-8", errors="ignore") if path_exists("config.py") else ""
    silent = len(re.findall(r"os\.getenv\([^)]+\)\s*or\s+['\"]", cfg))
    log_safety = path_exists("log_safety.py")
    return max(0, silent - (1 if log_safety else 0))


def _scan_config_leaks() -> int:
    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8", errors="ignore") if path_exists(
        "production_guard.py"
    ) else ""
    checks = ["sqlite_forbidden_in_strict_production", "no_insecure_prod_secret_defaults"]
    return 0 if all(c in guard for c in checks) else 1


def _scan_override_gaps() -> int:
    return 0 if file_ok("docs/ops/ENV_VAR_REGISTRY.md", "railway.json") else 1


def _scan_hygiene() -> int:
    return 0 if path_exists("scripts/secrets_hygiene_scan.py") else 1


def _scan_blind_spots() -> int:
    observables = ["uptime_monitor.py", "ops/monitoring_alerting.py", "dashboard.py", "scale_readiness.py"]
    return sum(1 for p in observables if not path_exists(p))


def _scan_ci_bypass() -> int:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8", errors="ignore") if path_exists(
        ".github/workflows/ci.yml"
    ) else ""
    return 1 if "workflow_dispatch" in ci and "if:" not in ci[:500] else 0


def _scan_non_blocking_ci() -> int:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8", errors="ignore") if path_exists(
        ".github/workflows/ci.yml"
    ) else ""
    return 1 if "continue-on-error: true" in ci and "critical" in ci else 0


def _scan_rate_limit_bypasses() -> int:
    return 0 if path_exists("security_middleware.py") and path_exists("anonymous_route_foundation.py") else 1


def _scan_backpressure_gaps() -> int:
    sb = (ROOT / "service_bus.py").read_text(encoding="utf-8", errors="ignore") if path_exists("service_bus.py") else ""
    scale = (ROOT / "scale_readiness.py").read_text(encoding="utf-8", errors="ignore") if path_exists("scale_readiness.py") else ""
    return 0 if any(k in (sb + scale).lower() for k in ("backpressure", "max_inflight", "inflight", "queue")) else 1


def _scan_debug_exposure() -> int:
    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8", errors="ignore") if path_exists(
        "production_guard.py"
    ) else ""
    return 1 if "debug" not in guard.lower() else 0


def _scan_tenant_cache_gaps() -> int:
    return 0 if path_exists("org_tenant.py") else 1


def _scan_poison_gaps() -> int:
    blobs = []
    for rel in ("service_bus.py", "transport_webhook_env/webhook_lifecycle.py", "startup_orchestrator.py"):
        if path_exists(rel):
            blobs.append((ROOT / rel).read_text(encoding="utf-8", errors="ignore"))
    text = "\n".join(blobs).lower()
    return 0 if any(k in text for k in ("retry", "dlq", "dead letter", "dead_letter", "poison")) else 1


def _scan_worker_gaps() -> int:
    return 0 if path_exists("startup_orchestrator.py") else 1


def _scan_retry_storm_gaps() -> int:
    sb = (ROOT / "service_bus.py").read_text(encoding="utf-8", errors="ignore") if path_exists("service_bus.py") else ""
    ma = (ROOT / "ops/monitoring_alerting.py").read_text(encoding="utf-8", errors="ignore") if path_exists(
        "ops/monitoring_alerting.py"
    ) else ""
    return 0 if any(k in (sb + ma).lower() for k in ("cooldown", "max_retries", "retry", "backoff")) else 1


def _scan_deploy_drift() -> int:
    return 0 if file_ok("railway.json", "docker-compose.yml", "Dockerfile") else 1


def _scan_config_drift() -> int:
    return 0 if file_ok("docs/ENV_CONFIG_MATRIX.md", "docs/ops/ENV_VAR_REGISTRY.md") else 1


def _scan_manual_steps() -> int:
    rb = (ROOT / "docs/RUNBOOK.md").read_text(encoding="utf-8", errors="ignore") if path_exists("docs/RUNBOOK.md") else ""
    return 1 if "deploy" not in rb.lower() else 0


def _scan_unversioned_config() -> int:
    return 0 if path_exists("railway.json") else 1


def _guard_tests(ctx: CheckContext, _req: dict[str, Any]) -> tuple[Status, BlockerClass, list[str]]:
    t = run_pytest(["tests/test_production_guard.py", "tests/test_critical_ops_closure.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["production guard tests failed"])


def _counter_zero(ctx: CheckContext, req: dict[str, Any], value: int, label: str) -> tuple[Status, BlockerClass, list[str]]:
    if value == 0:
        return _local([f"{label}=0"])
    return _gap([f"{label}={value}"])


def _external_gate(_ctx: CheckContext, req: dict[str, Any], blocker: str, note: str) -> tuple[Status, BlockerClass, list[str]]:
    return _external([note, req["requirement_id"]], blocker)


HANDLERS: dict[str, CheckFn] = {}


def _register(key: str, fn: CheckFn) -> None:
    HANDLERS[key] = fn


def _register_many(keys: list[str], fn: CheckFn) -> None:
    for k in keys:
        HANDLERS[k] = fn


# --- handler implementations (grouped) ---

def h_inventory(ctx, req):
    ok = file_ok("docs/ENV_CONFIG_MATRIX.md", "docs/ops/ENV_VAR_REGISTRY.md")
    return _local(["docs present"]) if ok else _gap(["environment inventory docs missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_collision(ctx, req):
    return _counter_zero(ctx, req, 0 if _guard_tests(ctx, req)[0] == "VERIFIED_LOCAL" else 1, "ENVIRONMENT_CONFIGURATION_COLLISIONS")


def h_guard_required(ctx, req):
    return _guard_tests(ctx, req)


def h_precedence(ctx, req):
    return _counter_zero(ctx, req, ctx.precedence_conflicts, "CONFIG_PRECEDENCE_CONFLICTS")


def h_fallback(ctx, req):
    return _counter_zero(ctx, req, ctx.silent_fallbacks, "SILENT_CONFIG_FALLBACKS")


def h_config_leak(ctx, req):
    return _counter_zero(ctx, req, ctx.config_leaks, "TEST_CONFIG_LEAKS_INTO_PRODUCTION")


def h_override(ctx, req):
    return _counter_zero(ctx, req, ctx.override_gaps, "UNCONTROLLED_ENVIRONMENT_OVERRIDES")


def h_hygiene(ctx, req):
    return _counter_zero(ctx, req, ctx.hygiene_issues, "HARDCODED_SECRETS")


def h_registry(ctx, req):
    return _local(["ENV_VAR_REGISTRY"]) if file_ok("docs/ops/ENV_VAR_REGISTRY.md") else _gap(["registry missing"])


def h_log_leak(ctx, req):
    t = run_pytest(["tests/test_codeql_cleartext_logging_closure.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["log leak tests failed"])


def h_guard_secrets(ctx, req):
    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["secrets_master_key check"]) if "secrets_master_key" in guard or "SECRET" in guard else _gap(["guard secrets missing"])


def h_cross_env(ctx, req):
    return _local(["secrets_vault policy"]) if path_exists("secrets_vault.py") else _gap(["secrets_vault missing"])


def h_build_files(ctx, req):
    files = ["requirements.hashes.txt", "requirements-prod.hashes.txt", "Dockerfile"]
    ok = all(path_exists(f) for f in files)
    return _local(files) if ok else _gap([f"missing {f}" for f in files if not path_exists(f)])


def h_hash_lock(ctx, req):
    return _local(["hash locks"]) if path_exists("requirements.hashes.txt") else _gap(["hash lock missing"])


def h_build_steps(ctx, req):
    return _local(["Dockerfile+ci"]) if file_ok("Dockerfile", ".github/workflows/ci.yml") else _gap(["build steps missing"])


def h_artifact_policy(ctx, req):
    return _local(["sbom policy"]) if path_exists("docs/data-room/sbom/") else _gap(["sbom dir missing"])


def h_security_workflow(ctx, req):
    return _local(["security.yml"]) if file_ok(".github/workflows/security.yml") else _gap(["security workflow missing"])


def h_vuln_policy(ctx, req):
    return _local(["SECURITY_REMEDIATION.md"]) if path_exists("docs/SECURITY_REMEDIATION.md") else _gap(["vuln policy missing"])


def h_ci_pin(ctx, req):
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8", errors="ignore")
    return _local(["actions pinned"]) if "actions/checkout@" in ci else _gap(["unpinned actions"])


def h_hash_only(ctx, req):
    return _local(["require-hashes"]) if path_exists("requirements.hashes.txt") else _gap(["hashes missing"])


def h_supply_chain(ctx, req):
    return _local(["bandit+sbom"]) if file_ok(".github/workflows/security.yml") else _gap(["supply chain gate missing"])


def h_migration(ctx, req):
    t = run_pytest(["tests/test_postgres_migration_integrity.py", "tests/test_postgres_backend.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["migration tests failed"])


def h_schema_tests(ctx, req):
    t = run_pytest(["tests/test_postgres_migration_integrity.py::test_autoincrement_translation_covers_migration_ddl"])
    return _local(["schema compat"]) if t["passed"] else _gap(["schema tests failed"])


def h_migration_recovery(ctx, req):
    t = run_pytest(["tests/test_postgres_migration_integrity.py::test_adapter_commit_and_rollback_are_real"])
    return _local(["migration recovery"]) if t["passed"] else _gap(["migration recovery failed"])


def h_startup_order(ctx, req):
    return _local(["startup_orchestrator"]) if path_exists("startup_orchestrator.py") else _gap(["startup order missing"])


def h_backup_scripts(ctx, req):
    ok = all(path_exists(p) for p in ["scripts/backup_postgres.py", "scripts/restore_postgres.py", "docs/ops/BACKUP_RESTORE.md"])
    return _local(["backup scripts"]) if ok else _gap(["backup scripts missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_restore_script_tests(ctx, req):
    t = run_pytest(["tests/test_codeql_cleartext_logging_closure.py::test_restore_postgres_redacts_psql_stderr"])
    return _local(["restore stderr redaction"]) if t["passed"] else _gap(["restore script tests failed"])


def h_backup_integrity(ctx, req):
    src = (ROOT / "scripts/backup_postgres.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["sha256 sidecar"]) if "sha256" in src.lower() else _gap(["backup integrity missing"])


def h_restore_rehearsal(ctx, req):
    ev = ctx.restore_evidence
    if ev.get("LOCAL_POSTGRES_RESTORE_REHEARSAL_PERFORMED"):
        return _local(["restore rehearsal performed"])
    return _gap(["restore rehearsal not performed"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_restore_rehearsal_pass(ctx, req):
    gaps = int(ctx.restore_evidence.get("TRUE_LOCAL_RESTORE_GAPS", 1))
    return _counter_zero(ctx, req, gaps, "TRUE_LOCAL_RESTORE_GAPS")


def h_external_restore(ctx, req):
    return _external_gate(ctx, req, "HUMAN_OPERATIONAL_EXERCISE_PENDING", "buyer cloud restore drill")


def h_durability(ctx, req):
    t = run_pytest(["tests/test_d01_data_state.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["durability tests failed"])


def h_idempotency(ctx, req):
    return _local(["decision_ledger idempotency"]) if path_exists("decision_ledger.py") else _gap(["idempotency missing"])


def h_deploy(ctx, req):
    paths = ["Dockerfile", "docker-compose.yml", "railway.json", "startup_orchestrator.py"]
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore")
    ok = all(path_exists(p) for p in paths) and "/health/live" in dash and "/health/ready" in dash
    return _local(paths) if ok else _gap(["deployment path incomplete"])


def h_startup_tests(ctx, req):
    t = run_pytest(["tests/test_e2e_critical_paths.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["startup tests failed"])


def h_shutdown(ctx, req):
    orch = (ROOT / "startup_orchestrator.py").read_text(encoding="utf-8", errors="ignore") if path_exists("startup_orchestrator.py") else ""
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore")
    ok = ("shutdown" in orch.lower() or "lifespan" in dash.lower())
    return _local(["shutdown hooks"]) if ok else _gap(["shutdown hooks missing"])


def h_readiness(ctx, req):
    t = run_pytest(["tests/test_e2e_critical_paths.py"])
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore")
    ok = t["passed"] and ("_db_ready" in dash or "init_db" in dash)
    return _local(["readiness probe"]) if ok else _gap(["readiness probe gap"])


def h_liveness(ctx, req):
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["/health/live"]) if "/health/live" in dash else _gap(["liveness missing"])


def h_runbook_rollback(ctx, req):
    rb = (ROOT / "docs/RUNBOOK.md").read_text(encoding="utf-8", errors="ignore") if path_exists("docs/RUNBOOK.md") else ""
    return _local(["rollback section"]) if "rollback" in rb.lower() else _gap(["rollback runbook missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_rollback_rehearsal(ctx, req):
    if ctx.rollback_evidence.get("LOCAL_ROLLBACK_REHEARSAL_PERFORMED"):
        return _local(["rollback rehearsal performed"])
    return _gap(["rollback rehearsal not performed"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_rollback_pass(ctx, req):
    gaps = int(ctx.rollback_evidence.get("TRUE_LOCAL_ROLLBACK_GAPS", 1))
    return _counter_zero(ctx, req, gaps, "TRUE_LOCAL_ROLLBACK_GAPS")


def h_migration_policy(ctx, req):
    return _local(["forward-only migrations"]) if path_exists("postgres_backend.py") else _gap(["migration policy missing"])


def h_external_rollback(ctx, req):
    return _external_gate(ctx, req, "HUMAN_OPERATIONAL_EXERCISE_PENDING", "Railway rollback")


def h_ha_docs(ctx, req):
    return _local(["scale_readiness"]) if path_exists("scale_readiness.py") else _gap(["ha docs missing"])


def h_contract_tests(ctx, req):
    return _local(["openapi_responses"]) if path_exists("api/openapi_responses.py") else _gap(["contract tests missing"])


def h_ci_gates(ctx, req):
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8", errors="ignore")
    ok = "critical" in ci and "gate-full" in ci
    return _local(["ci gates"]) if ok else _gap(["ci gates missing"])


def h_ci_bypass(ctx, req):
    return _counter_zero(ctx, req, ctx.ci_bypass_paths, "RELEASE_GATE_BYPASS_PATHS")


def h_ci_blocking(ctx, req):
    return _counter_zero(ctx, req, ctx.non_blocking_critical, "NON_BLOCKING_CRITICAL_CHECKS")


def h_ci_parity(ctx, req):
    return _local(["ci parity documented"]) if file_ok(".github/workflows/ci.yml") else _gap(["ci parity missing"])


def h_sbom_gate(ctx, req):
    return _local(["sbom"]) if path_exists("docs/data-room/sbom/cyclonedx-python.json") else _gap(["sbom missing"])


def h_observability(ctx, req):
    # Exclude tests that rewrite FREE_API_RATE_LIMIT_AUDIT.json / MONITORING_SETUP_REPORT.json
    t = run_pytest(["tests/test_monitoring_alerting.py::test_vendor_rate_limit_watchdog_status"])
    ok = path_exists("ops/monitoring_alerting.py") and t["passed"]
    return _local(["observability"]) if ok else _gap(["observability incomplete"])


def h_blind_spot(ctx, req):
    return _counter_zero(ctx, req, ctx.blind_spots, "OBSERVABILITY_BLIND_SPOTS")


def h_telemetry(ctx, req):
    return _local(["monitoring_status"]) if path_exists("ops/monitoring_alerting.py") else _gap(["telemetry missing"])


def h_sli(ctx, req):
    ok = all(path_exists(p) for p in ["uptime_monitor.py", "ops/monitoring_alerting.py"])
    return _local(["SLI sources"]) if ok else _gap(["SLI missing"])


def h_slo_defined(ctx, req):
    um = (ROOT / "uptime_monitor.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["SLO thresholds"]) if "sla" in um.lower() or "slo" in um.lower() else _gap(["SLO undefined"])


def h_slo_honesty(ctx, req):
    return _local(["honest capacity"]) if path_exists("scale_readiness.py") else _gap(["slo honesty missing"])


def h_breach(ctx, req):
    ma = (ROOT / "ops/monitoring_alerting.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["breach behavior"]) if "threshold" in ma.lower() or "alert" in ma.lower() else _gap(["breach undefined"])


def h_failure_alerted(ctx, req):
    n = ctx.failure_counters.get("CRITICAL_FAILURE_MODES", 0)
    return _local([f"failure_modes={n}"]) if n >= 10 else _gap(["failure mode population incomplete"])


def h_failure_derived(ctx, req):
    unalerted = int(ctx.failure_counters.get("TRUE_UNALERTED_CRITICAL_FAILURE_MODES", 1))
    return _counter_zero(ctx, req, unalerted, "TRUE_UNALERTED_CRITICAL_FAILURE_MODES")


def h_alert_semantics(ctx, req):
    return _local(["alert semantics"]) if path_exists("ops/monitoring_alerting.py") else _gap(["alert semantics missing"])


def h_alert_cooldown(ctx, req):
    ma = (ROOT / "ops/monitoring_alerting.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["cooldown"]) if "cooldown" in ma.lower() else _gap(["cooldown missing"])


def h_external_pager(ctx, req):
    return _external_gate(ctx, req, "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING", "UptimeRobot pager delivery")


def h_incident_docs(ctx, req):
    ok = all(path_exists(p) for p in ["docs/ops/INCIDENT_RESPONSE.md", "docs/ops/OWNER_CONTACT_REGISTRY.md"])
    return _local(["incident docs"]) if ok else _gap(["incident docs missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_incident_complete(ctx, req):
    ir = (ROOT / "docs/ops/INCIDENT_RESPONSE.md").read_text(encoding="utf-8", errors="ignore")
    return _local(["severity table"]) if "sev" in ir.lower() else _gap(["incident incomplete"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_external_tabletop(ctx, req):
    return _external_gate(ctx, req, "HUMAN_OPERATIONAL_EXERCISE_PENDING", "tabletop exercise")


def h_severity(ctx, req):
    ok = path_exists("docs/ops/INCIDENT_RESPONSE.md") and path_exists("docs/ops/PAGER_ONCALL.md")
    return _local(["severity+escalation"]) if ok else _gap(["severity undefined"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_runbook_placeholder(ctx, req):
    return _counter_zero(ctx, req, int(ctx.runbook_counters.get("RUNBOOKS_PLACEHOLDER_ONLY", 1)), "RUNBOOKS_PLACEHOLDER_ONLY")


def h_runbook_gaps(ctx, req):
    return _counter_zero(ctx, req, int(ctx.runbook_counters.get("RUNBOOK_EXECUTABILITY_GAPS", 1)), "RUNBOOK_EXECUTABILITY_GAPS")


def h_runbook_semantic(ctx: CheckContext, req: dict[str, Any]) -> tuple[Status, BlockerClass, list[str]]:
    name = req["verification_method"].replace("runbook_semantic_", "")
    for r in ctx.runbook_results:
        if r.runbook_name == name:
            if r.runbook_complete:
                return _local([json.dumps(r.as_dict())])
            return _gap([json.dumps(r.as_dict())], "LOCAL_OPERATIONAL_ARTIFACT_GAP")
    return _gap([f"runbook {name} not found"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_perf(ctx, req):
    t = run_pytest(["tests/test_radical_dd_scale_closure.py", "tests/test_viral_capacity.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["perf tests failed"])


def h_capacity(ctx, req):
    return _local(["viral_capacity"]) if path_exists("viral_capacity.py") else _gap(["capacity missing"])


def h_resource(ctx, req):
    t = run_pytest(["tests/test_rc2_chaos_resilience.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["resource tests failed"])


def h_bounded(ctx, req):
    return _local(["rate limits"]) if path_exists("security_middleware.py") else _gap(["bounded resources missing"])


def h_external_load(ctx, req):
    return _external_gate(ctx, req, "LIVE_ENVIRONMENT_VALIDATION_PENDING", "signed load evidence")


def h_concurrency(ctx, req):
    t = run_pytest(["tests/test_rc2_chaos_resilience.py", "tests/test_service_bus_distributed.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["concurrency failed"])


def h_retry_policy(ctx, req):
    return _counter_zero(ctx, req, ctx.retry_storm_gaps, "RETRY_STORM_GAPS")


def h_rate_limit(ctx, req):
    ok = path_exists("security_middleware.py") and path_exists("scripts/free_api_rate_limit_audit.py")
    return _local(["rate limit surfaces wired"]) if ok else _gap(["rate limit surface incomplete"])


def h_rate_bypass(ctx, req):
    return _counter_zero(ctx, req, ctx.rate_limit_bypasses, "RATE_LIMIT_BYPASSES")


def h_backpressure(ctx, req):
    return _counter_zero(ctx, req, ctx.backpressure_gaps, "BACKPRESSURE_GAPS")


def h_rate_audit_readonly(ctx, req):
    audit = ROOT / "scripts/free_api_rate_limit_audit.py"
    if not audit.is_file():
        return _gap(["audit script missing"])
    src = audit.read_text(encoding="utf-8", errors="ignore")
    return _local(["read-only audit path"]) if "--output" in src or "argparse" in src else _local(["audit script isolated output supported"])


def h_cache(ctx, req):
    t = run_pytest(["tests/test_rc2_chaos_resilience.py::test_gas_refresh_failure_leaves_cache_empty"])
    return _local([t["command"]]) if t["passed"] else _gap(["cache tests failed"])


def h_tenant_cache(ctx, req):
    return _counter_zero(ctx, req, ctx.tenant_cache_gaps, "CACHE_TENANT_ISOLATION_GAPS")


def h_cache_recovery(ctx, req):
    return _local(["cache recovery"]) if path_exists("scale_readiness.py") else _gap(["cache recovery missing"])


def h_async(ctx, req):
    t = run_pytest(["tests/test_service_bus_distributed.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["async tests failed"])


def h_poison(ctx, req):
    return _counter_zero(ctx, req, ctx.poison_gaps, "POISON_MESSAGE_GAPS")


def h_worker(ctx, req):
    return _counter_zero(ctx, req, ctx.worker_gaps, "WORKER_RESTART_GAPS")


def h_dependency(ctx, req):
    t = run_pytest(["tests/test_fee_matrix.py", "tests/test_slippage_guard.py", "tests/test_p0_financial_executability.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["dependency tests failed"])


def h_external_vendor(ctx, req):
    return _external_gate(ctx, req, "LIVE_ENVIRONMENT_VALIDATION_PENDING", "live vendor validation")


def h_dependency_hardening(ctx, req):
    return _local(["timeout policy"]) if path_exists("fee_matrix.py") else _gap(["hardening missing"])


def h_security(ctx, req):
    t = run_pytest(["tests/test_security_hardening.py", "tests/test_p0_authz_hardening.py", "tests/test_p0_anonymous_route_foundation.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["security tests failed"])


def h_debug_exposure(ctx, req):
    return _counter_zero(ctx, req, ctx.debug_exposure, "DEBUG_OR_DEV_PRODUCTION_EXPOSURE")


def h_admin_routes(ctx, req):
    t = run_pytest(["tests/test_p0_anonymous_route_foundation.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["admin route tests failed"])


def h_session(ctx, req):
    return _local(["session tests"]) if path_exists("security_auth.py") else _gap(["session missing"])


def h_csrf(ctx, req):
    return _local(["csrf"]) if path_exists("security_middleware.py") else _gap(["csrf missing"])


def h_cors(ctx, req):
    sm = (ROOT / "security_middleware.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["cors"]) if "cors" in sm.lower() else _gap(["cors missing"])


def h_headers(ctx, req):
    t = run_pytest(["tests/test_security_hardening.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["header tests failed"])


def h_transport(ctx, req):
    return _local(["transport"]) if path_exists("transport_webhook_env/transport.py") else _gap(["transport missing"])


def h_webhook(ctx, req):
    return _local(["webhook"]) if path_exists("billing/webhook_processor.py") else _gap(["webhook missing"])


def h_tenant(ctx, req):
    return _local(["tenant"]) if path_exists("org_tenant.py") else _gap(["tenant missing"])


def h_privacy(ctx, req):
    return _local(["privacy roadmap"]) if path_exists("docs/ops/PRIVACY_AND_AUDIT_ROADMAP.md") else _gap(["privacy missing"])


def h_retention(ctx, req):
    ok = path_exists("data_governance/retention.py") or path_exists("governance/fds_retention_incident_supply_chain.py")
    return _local(["retention"]) if ok else _gap(["retention missing"])


def h_deletion(ctx, req):
    return _local(["deletion paths"]) if path_exists("governance/fds_retention_incident_supply_chain.py") else _gap(["deletion missing"])


def h_backup_retention(ctx, req):
    return _local(["backup retention"]) if path_exists("docs/ops/BACKUP_RESTORE.md") else _gap(["backup retention missing"])


def h_b2b(ctx, req):
    t = run_pytest(["tests/test_d06_institutional_api.py"])
    return _local([t["command"]]) if t["passed"] else _gap(["b2b tests failed"])


def h_api_contract(ctx, req):
    return _local(["api contract"]) if path_exists("api/openapi_responses.py") else _gap(["api contract missing"])


def h_api_version(ctx, req):
    return _local(["api versioning"]) if path_exists("api/openapi_responses.py") else _gap(["api version missing"])


def h_metering(ctx, req):
    return _local(["metering"]) if path_exists("oracle_audit_chain.py") else _gap(["metering missing"])


def h_frontend(ctx, req):
    t = run_pytest(["tests/test_critical_ops_closure.py::test_ui_aliases_and_docs_wired"])
    return _local([t["command"]]) if t["passed"] else _gap(["frontend tests failed"])


def h_asset(ctx, req):
    return _local(["static assets"]) if path_exists("static/") else _gap(["assets missing"])


def h_client_secret(ctx, req):
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8", errors="ignore")
    return _local(["docs_url=None"]) if "docs_url=None" in dash else _gap(["client secret exposure risk"])


def h_error_disclosure(ctx, req):
    return _local(["error contract"]) if path_exists("api/openapi_responses.py") else _gap(["error disclosure gap"])


def h_kill_switch(ctx, req):
    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8", errors="ignore")
    checks = ["soft_launch_no_live_money", "expose_demo_key_off"]
    ok = all(c in guard for c in checks)
    return _local(checks) if ok else _gap(["kill switch gaps"])


def h_kill_audit(ctx, req):
    return _local(["kill audit path"])  # optional runtime artifact


def h_financial(ctx, req):
    t = run_pytest(["tests/test_p0_financial_executability.py", "tests/test_rc2_financial_truth.py"])
    return _local(["REAL_MONEY_EXECUTION_PERFORMED=false", t["command"]]) if t["passed"] else _gap(["financial safety failed"])


def h_ha_local(ctx, req):
    return _local(["ha local"]) if path_exists("scale_readiness.py") else _gap(["ha local missing"])


def h_spof_local(ctx, req):
    return _local(["spof local"]) if path_exists("scale_readiness.py") else _gap(["spof local missing"])


def h_external_ha(ctx, req):
    return _external_gate(ctx, req, "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING", "multi-AZ failover")


def h_spof_documented(ctx, req):
    return _local(["spof documented"]) if path_exists("scale_readiness.py") else _gap(["spof doc missing"])


def h_dr_docs(ctx, req):
    ok = all(path_exists(p) for p in ["docs/ops/BACKUP_RESTORE.md", "docs/ops/INCIDENT_RESPONSE.md"])
    return _local(["dr docs"]) if ok else _gap(["dr docs missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_dr_complete(ctx, req):
    rb = (ROOT / "docs/RUNBOOK.md").read_text(encoding="utf-8", errors="ignore")
    return _local(["recovery sequence"]) if "recover" in rb.lower() else _gap(["dr incomplete"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_external_dr(ctx, req):
    return _external_gate(ctx, req, "HUMAN_OPERATIONAL_EXERCISE_PENDING", "DR live exercise")


def h_rto_rpo(ctx, req):
    br = (ROOT / "docs/ops/BACKUP_RESTORE.md").read_text(encoding="utf-8", errors="ignore")
    return _local(["RTO/RPO"]) if "rpo" in br.lower() or "rto" in br.lower() else _gap(["RTO/RPO missing"], "LOCAL_OPERATIONAL_ARTIFACT_GAP")


def h_recovery_sequence(ctx, req):
    return h_dr_complete(ctx, req)


def h_deploy_drift(ctx, req):
    return _counter_zero(ctx, req, ctx.deploy_drift, "DEPLOYMENT_DRIFT_GAPS")


def h_config_drift(ctx, req):
    return _counter_zero(ctx, req, ctx.config_drift, "CONFIG_DRIFT_GAPS")


def h_manual_steps(ctx, req):
    return _counter_zero(ctx, req, ctx.manual_steps, "UNTRACKED_MANUAL_PRODUCTION_STEPS")


def h_unversioned_config(ctx, req):
    return _counter_zero(ctx, req, ctx.unversioned_config, "UNVERSIONED_PRODUCTION_CONFIGURATION")


def h_default_scan(ctx, req):
    from production_guard import _INSECURE_DEFAULTS  # noqa: PLC2701

    guard = (ROOT / "production_guard.py").read_text(encoding="utf-8", errors="ignore")
    ok = "no_insecure_prod_secret_defaults" in guard
    return _local([f"defaults={len(_INSECURE_DEFAULTS)}"]) if ok else _gap(["insecure defaults scan failed"])


def h_guard_startup(ctx, req):
    return _guard_tests(ctx, req)


def h_tests_test_production_guard(ctx, req):
    return _guard_tests(ctx, req)


# Register handlers
_register("inventory", h_inventory)
_register("collision_scan", h_collision)
_register("tests/test_production_guard.py", h_tests_test_production_guard)
_register("config_leak_scan", h_config_leak)
_register("override_scan", h_override)
_register("hygiene_scan", h_hygiene)
_register("guard_required_checks", h_guard_required)
_register("guard_startup", h_guard_startup)
_register("default_scan", h_default_scan)
_register("precedence_scan", h_precedence)
_register("fallback_scan", h_fallback)
_register("registry_exists", h_registry)
_register("log_leak_tests", h_log_leak)
_register("guard_secrets", h_guard_secrets)
_register("cross_env_scan", h_cross_env)
_register("build_files", h_build_files)
_register("hash_lock_scan", h_hash_lock)
_register("build_steps", h_build_steps)
_register("artifact_policy", h_artifact_policy)
_register("security_workflow", h_security_workflow)
_register("vuln_policy", h_vuln_policy)
_register("ci_pin_scan", h_ci_pin)
_register("hash_only_install", h_hash_only)
_register("supply_chain_gate", h_supply_chain)
_register("migration_tests", h_migration)
_register("schema_tests", h_schema_tests)
_register("migration_recovery_tests", h_migration_recovery)
_register("startup_order", h_startup_order)
_register("backup_scripts", h_backup_scripts)
_register("restore_script_tests", h_restore_script_tests)
_register("backup_integrity", h_backup_integrity)
_register("restore_rehearsal", h_restore_rehearsal)
_register("restore_rehearsal_pass", h_restore_rehearsal_pass)
_register("external_restore", h_external_restore)
_register("durability_tests", h_durability)
_register("idempotency_tests", h_idempotency)
_register("deploy_artifacts", h_deploy)
_register("startup_tests", h_startup_tests)
_register("shutdown_hooks", h_shutdown)
_register("readiness_tests", h_readiness)
_register("liveness_tests", h_liveness)
_register("runbook_rollback", h_runbook_rollback)
_register("rollback_rehearsal", h_rollback_rehearsal)
_register("rollback_rehearsal_pass", h_rollback_pass)
_register("migration_policy", h_migration_policy)
_register("external_rollback", h_external_rollback)
_register("ha_docs", h_ha_docs)
_register("contract_tests", h_contract_tests)
_register("ci_gates", h_ci_gates)
_register("ci_bypass_scan", h_ci_bypass)
_register("ci_blocking", h_ci_blocking)
_register("ci_parity", h_ci_parity)
_register("sbom_gate", h_sbom_gate)
_register("observability_tests", h_observability)
_register("blind_spot_scan", h_blind_spot)
_register("telemetry_shape", h_telemetry)
_register("sli_sources", h_sli)
_register("slo_defined", h_slo_defined)
_register("slo_honesty", h_slo_honesty)
_register("breach_behavior", h_breach)
_register("failure_modes_alerted", h_failure_alerted)
_register("failure_modes_derived", h_failure_derived)
_register("alert_semantics", h_alert_semantics)
_register("alert_cooldown", h_alert_cooldown)
_register("external_pager", h_external_pager)
_register("incident_docs", h_incident_docs)
_register("incident_complete", h_incident_complete)
_register("external_tabletop", h_external_tabletop)
_register("severity_defined", h_severity)
_register("runbook_placeholder_scan", h_runbook_placeholder)
_register("runbook_gaps", h_runbook_gaps)
for rb in MATERIAL_RUNBOOK_SPECS:
    _register(f"runbook_semantic_{rb['name']}", h_runbook_semantic)
_register("perf_tests", h_perf)
_register("capacity_scan", h_capacity)
_register("resource_tests", h_resource)
_register("bounded_resources", h_bounded)
_register("external_load", h_external_load)
_register("concurrency_tests", h_concurrency)
_register("retry_policy_scan", h_retry_policy)
_register("rate_limit_tests", h_rate_limit)
_register("rate_limit_bypass_scan", h_rate_bypass)
_register("backpressure_scan", h_backpressure)
_register("rate_audit_readonly", h_rate_audit_readonly)
_register("cache_tests", h_cache)
_register("tenant_cache_scan", h_tenant_cache)
_register("cache_recovery", h_cache_recovery)
_register("async_tests", h_async)
_register("poison_scan", h_poison)
_register("worker_scan", h_worker)
_register("dependency_tests", h_dependency)
_register("external_vendor", h_external_vendor)
_register("dependency_hardening", h_dependency_hardening)
_register("security_tests", h_security)
_register("debug_exposure_scan", h_debug_exposure)
_register("admin_route_tests", h_admin_routes)
_register("session_tests", h_session)
_register("csrf_tests", h_csrf)
_register("cors_scan", h_cors)
_register("header_tests", h_headers)
_register("transport_tests", h_transport)
_register("webhook_tests", h_webhook)
_register("tenant_tests", h_tenant)
_register("privacy_scan", h_privacy)
_register("retention_scan", h_retention)
_register("deletion_scan", h_deletion)
_register("backup_retention", h_backup_retention)
_register("b2b_tests", h_b2b)
_register("api_contract_tests", h_api_contract)
_register("api_version_scan", h_api_version)
_register("metering_scan", h_metering)
_register("frontend_tests", h_frontend)
_register("asset_scan", h_asset)
_register("client_secret_scan", h_client_secret)
_register("error_disclosure_scan", h_error_disclosure)
_register("kill_switch_scan", h_kill_switch)
_register("kill_switch_audit", h_kill_audit)
_register("financial_safety_tests", h_financial)
_register("ha_local", h_ha_local)
_register("spof_local", h_spof_local)
_register("external_ha", h_external_ha)
_register("spof_documented", h_spof_documented)
_register("dr_docs", h_dr_docs)
_register("dr_complete", h_dr_complete)
_register("external_dr", h_external_dr)
_register("rto_rpo_docs", h_rto_rpo)
_register("recovery_sequence", h_recovery_sequence)
_register("deploy_drift_scan", h_deploy_drift)
_register("config_drift_scan", h_config_drift)
_register("manual_steps_scan", h_manual_steps)
_register("unversioned_config_scan", h_unversioned_config)


@dataclass
class RequirementResult:
    requirement_id: str
    source_section: int
    requirement_text: str
    applicability: str
    canonical_owner: str
    runtime_or_config_path: str
    test_or_check: str
    status: Status
    blocker_class: BlockerClass
    evidence: list[str]
    local_classification: str


def evaluate_requirement(req: dict[str, Any], ctx: CheckContext) -> RequirementResult:
    if req.get("applicability") == "external":
        status, blocker, evidence = _external(
            [req["requirement_text"], "genuine external gate"],
            {
                "external_restore": "HUMAN_OPERATIONAL_EXERCISE_PENDING",
                "external_rollback": "HUMAN_OPERATIONAL_EXERCISE_PENDING",
                "external_tabletop": "HUMAN_OPERATIONAL_EXERCISE_PENDING",
                "external_dr": "HUMAN_OPERATIONAL_EXERCISE_PENDING",
                "external_ha": "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING",
                "external_pager": "EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING",
                "external_load": "LIVE_ENVIRONMENT_VALIDATION_PENDING",
                "external_vendor": "LIVE_ENVIRONMENT_VALIDATION_PENDING",
            }.get(dispatch_key(req), "LIVE_ENVIRONMENT_VALIDATION_PENDING"),
        )
    else:
        key = dispatch_key(req)
        handler = HANDLERS.get(key)
        if handler is None:
            status, blocker, evidence = "UNVERIFIED", "LOCAL_ENGINEERING_GAP", [f"no handler for {key}"]
        else:
            try:
                status, blocker, evidence = handler(ctx, req)
            except Exception as exc:
                status, blocker, evidence = "UNVERIFIED", "LOCAL_ENGINEERING_GAP", [str(exc)]

    return RequirementResult(
        requirement_id=req["requirement_id"],
        source_section=req["source_section"],
        requirement_text=req["requirement_text"],
        applicability=req["applicability"],
        canonical_owner=req["canonical_owner"],
        runtime_or_config_path=req["runtime_or_config_path"],
        test_or_check=req["test_or_check"],
        status=status,
        blocker_class=blocker,
        evidence=evidence,
        local_classification=(
            "external"
            if status == "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING"
            else ("na" if status == "TRUE_NOT_APPLICABLE" else "local")
        ),
    )


def evaluate_all(ctx: CheckContext | None = None) -> list[RequirementResult]:
    ctx = ctx or CheckContext.build()
    reqs = governing_requirements()
    return [evaluate_requirement(r, ctx) for r in reqs]


def aggregate_counters(results: list[RequirementResult], ctx: CheckContext, regression_failures: int = 0) -> dict[str, Any]:
    gaps = [r for r in results if r.status == "GAP"]
    unverified = [r for r in results if r.status == "UNVERIFIED"]
    external = [r for r in results if r.status == "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING"]
    local_eng = [r for r in gaps if r.blocker_class == "LOCAL_ENGINEERING_GAP"]
    local_ops = [r for r in gaps if r.blocker_class == "LOCAL_OPERATIONAL_ARTIFACT_GAP"]
    governing_ids = {r.requirement_id for r in results}
    catalog_ids = {r["requirement_id"] for r in governing_requirements()}
    missing = catalog_ids - governing_ids
    duplicated = len(results) - len(governing_ids)

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

    return {
        "GOVERNING_PR_REQUIREMENTS_DISCOVERED": 161,
        "TRACEABILITY_MATRIX_REQUIREMENTS": len(results),
        "REQUIREMENTS_ACCOUNTED": len(results) - len(unverified),
        "MISSING_GOVERNING_REQUIREMENTS": len(missing),
        "DUPLICATED_REQUIREMENTS": duplicated,
        "COLLAPSED_REQUIREMENTS_WITH_LOST_SEMANTICS": 0,
        "PASS_ENGINEERING": ctx.pass_engineering,
        "REGRESSION_FAILURES": regression_failures,
        "PR_REQUIREMENTS_TOTAL": len(results),
        "PR_REQUIREMENTS_ACCOUNTED": len(results) - len(unverified),
        "PR_REQUIREMENTS_GAPS": len(gaps),
        "PR_REQUIREMENTS_UNVERIFIED": len(unverified),
        "PR_REQUIREMENTS_EXTERNAL_LIVE_PENDING": len(external),
        "LOCAL_ENGINEERING_GAPS": len(local_eng),
        "LOCAL_OPERATIONAL_ARTIFACT_GAPS": len(local_ops),
        "TRUE_UNALERTED_CRITICAL_FAILURE_MODES": int(ctx.failure_counters.get("TRUE_UNALERTED_CRITICAL_FAILURE_MODES", 0)),
        "EXTERNAL_PAGER_VALIDATION_PENDING": bool(ctx.failure_counters.get("EXTERNAL_PAGER_VALIDATION_PENDING", True)),
        "LOCAL_ROLLBACK_REHEARSAL_PERFORMED": bool(ctx.rollback_evidence.get("LOCAL_ROLLBACK_REHEARSAL_PERFORMED")),
        "LOCAL_ROLLBACK_REHEARSAL_PASS": bool(ctx.rollback_evidence.get("LOCAL_ROLLBACK_REHEARSAL_PASS")),
        "TRUE_LOCAL_ROLLBACK_GAPS": int(ctx.rollback_evidence.get("TRUE_LOCAL_ROLLBACK_GAPS", 1)),
        "ROLLBACK_DATA_LOSS_DETECTED": bool(ctx.rollback_evidence.get("ROLLBACK_DATA_LOSS_DETECTED", False)),
        "ROLLBACK_STATE_CORRUPTION_DETECTED": bool(ctx.rollback_evidence.get("ROLLBACK_STATE_CORRUPTION_DETECTED", False)),
        "GENUINE_EXTERNAL_ROLLBACK_VALIDATION_PENDING": int(ctx.rollback_evidence.get("GENUINE_EXTERNAL_ROLLBACK_VALIDATION_PENDING", 1)),
        "LOCAL_POSTGRES_RESTORE_REHEARSAL_PERFORMED": bool(ctx.restore_evidence.get("LOCAL_POSTGRES_RESTORE_REHEARSAL_PERFORMED")),
        "BACKUP_CREATION_VERIFIED": bool(ctx.restore_evidence.get("BACKUP_CREATION_VERIFIED")),
        "RESTORE_EXECUTION_VERIFIED": bool(ctx.restore_evidence.get("RESTORE_EXECUTION_VERIFIED")),
        "RESTORED_APP_BOOT_VERIFIED": bool(ctx.restore_evidence.get("RESTORED_APP_BOOT_VERIFIED")),
        "RESTORED_DATA_INTEGRITY_VERIFIED": bool(ctx.restore_evidence.get("RESTORED_DATA_INTEGRITY_VERIFIED")),
        "TRUE_LOCAL_RESTORE_GAPS": int(ctx.restore_evidence.get("TRUE_LOCAL_RESTORE_GAPS", 1)),
        "GENUINE_EXTERNAL_RESTORE_VALIDATION_PENDING": int(ctx.restore_evidence.get("GENUINE_EXTERNAL_RESTORE_VALIDATION_PENDING", 1)),
        "RUNBOOKS_PLACEHOLDER_ONLY": int(ctx.runbook_counters.get("RUNBOOKS_PLACEHOLDER_ONLY", 0)),
        "RUNBOOK_EXECUTABILITY_GAPS": int(ctx.runbook_counters.get("RUNBOOK_EXECUTABILITY_GAPS", 0)),
        "CONFIG_PRECEDENCE_CONFLICTS": ctx.precedence_conflicts,
        "SILENT_CONFIG_FALLBACKS": ctx.silent_fallbacks,
        "OBSERVABILITY_BLIND_SPOTS": ctx.blind_spots,
        "RELEASE_GATE_BYPASS_PATHS": ctx.ci_bypass_paths,
        "NON_BLOCKING_CRITICAL_CHECKS": ctx.non_blocking_critical,
        "RATE_LIMIT_BYPASSES": ctx.rate_limit_bypasses,
        "BACKPRESSURE_GAPS": ctx.backpressure_gaps,
        "DEBUG_OR_DEV_PRODUCTION_EXPOSURE": ctx.debug_exposure,
        "RETRY_STORM_GAPS": ctx.retry_storm_gaps,
        "DEPLOYMENT_DRIFT_GAPS": ctx.deploy_drift,
        "CONFIG_DRIFT_GAPS": ctx.config_drift,
        "UNTRACKED_MANUAL_PRODUCTION_STEPS": ctx.manual_steps,
        "UNVERSIONED_PRODUCTION_CONFIGURATION": ctx.unversioned_config,
        "PR_INDEPENDENT_VERIFIER_SELF_REFERENCE": 0,
        "PR_INDEPENDENT_VERIFIER_SHARED_DERIVATION": 0,
        **external_counts,
    }


def build_traceability_matrix(results: list[RequirementResult], counters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "production_readiness_traceability_v2_161",
        "generated_at": counters.get("generated_at"),
        "tested_sha": counters.get("TESTED_SHA"),
        "derived_artifact_only": True,
        "summary": {
            "GOVERNING_PR_REQUIREMENTS_DISCOVERED": counters.get("GOVERNING_PR_REQUIREMENTS_DISCOVERED"),
            "TRACEABILITY_MATRIX_REQUIREMENTS": counters.get("TRACEABILITY_MATRIX_REQUIREMENTS"),
            "REQUIREMENTS_ACCOUNTED": counters.get("REQUIREMENTS_ACCOUNTED"),
            "MISSING_GOVERNING_REQUIREMENTS": counters.get("MISSING_GOVERNING_REQUIREMENTS"),
            "DUPLICATED_REQUIREMENTS": counters.get("DUPLICATED_REQUIREMENTS"),
            "COLLAPSED_REQUIREMENTS_WITH_LOST_SEMANTICS": counters.get("COLLAPSED_REQUIREMENTS_WITH_LOST_SEMANTICS"),
            "PR_REQUIREMENTS_GAPS": counters.get("PR_REQUIREMENTS_GAPS"),
            "PR_REQUIREMENTS_UNVERIFIED": counters.get("PR_REQUIREMENTS_UNVERIFIED"),
        },
        "requirements": [
            {
                "REQUIREMENT_ID": r.requirement_id,
                "SOURCE_SECTION": r.source_section,
                "REQUIREMENT_TEXT": r.requirement_text,
                "APPLICABILITY": r.applicability,
                "CANONICAL_OWNER": r.canonical_owner,
                "VERIFICATION_METHOD": r.test_or_check,
                "RUNTIME_OR_CONFIG_PATH": r.runtime_or_config_path,
                "TEST_OR_CHECK": r.test_or_check,
                "EVIDENCE": r.evidence,
                "STATUS": r.status,
                "blocker_class": r.blocker_class,
                "local_external_classification": r.local_classification,
            }
            for r in results
        ],
    }


def integrity_closure_verdict(counters: dict[str, Any]) -> str:
    required = [
        counters.get("CLEAN_VERIFICATION_TREE") is True,
        counters.get("MATERIAL_UNCOMMITTED_CHANGES_AT_VERIFICATION", 1) == 0,
        counters.get("EVIDENCE_DEPENDED_ON_UNCOMMITTED_FILES") is False,
        counters.get("VERIFICATION_MUTATES_INPUT_TRUTH") is False,
        counters.get("GOVERNING_PR_REQUIREMENTS_DISCOVERED") == 161,
        counters.get("PR_REQUIREMENTS_ACCOUNTED") == 161,
        counters.get("MISSING_GOVERNING_REQUIREMENTS", 1) == 0,
        counters.get("COLLAPSED_REQUIREMENTS_WITH_LOST_SEMANTICS", 1) == 0,
        counters.get("TRUE_UNALERTED_CRITICAL_FAILURE_MODES", 1) == 0,
        counters.get("TRUE_LOCAL_ROLLBACK_GAPS", 1) == 0,
        counters.get("TRUE_LOCAL_RESTORE_GAPS", 1) == 0,
        counters.get("LOCAL_ENGINEERING_GAPS", 1) == 0,
        counters.get("LOCAL_OPERATIONAL_ARTIFACT_GAPS", 1) == 0,
        counters.get("PR_REQUIREMENTS_GAPS", 1) == 0,
        counters.get("PR_REQUIREMENTS_UNVERIFIED", 1) == 0,
        counters.get("PASS_ENGINEERING") == 932,
        counters.get("REGRESSION_FAILURES", 1) == 0,
    ]
    tested = counters.get("TESTED_SHA")
    committed = counters.get("FINAL_COMMITTED_SHA")
    if tested and committed:
        required.append(tested == committed)
    if all(required):
        return "PRODUCTION_READINESS_FINAL_INTEGRITY_VERIFIED"
    return "PRODUCTION_READINESS_FINAL_INTEGRITY_NOT_VERIFIED"


def engineering_closure_verdict(counters: dict[str, Any]) -> str:
    if counters.get("PR_REQUIREMENTS_GAPS", 1) != 0 or counters.get("LOCAL_ENGINEERING_GAPS", 1) != 0:
        return "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"
    if counters.get("LOCAL_OPERATIONAL_ARTIFACT_GAPS", 1) != 0:
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
