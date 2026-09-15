"""161 governing Production Readiness requirements (sections 4–35). Data only — no checks."""

from __future__ import annotations

from typing import Any

# 15 material runbooks (§20) — semantic verification targets
MATERIAL_RUNBOOK_SPECS: list[dict[str, Any]] = [
    {"id": "G-20-RB-01", "name": "deployment", "path": "docs/RUNBOOK.md", "section_hint": "Deploy"},
    {"id": "G-20-RB-02", "name": "rollback", "path": "docs/RUNBOOK.md", "section_hint": "Rollback"},
    {"id": "G-20-RB-03", "name": "db_migration", "path": "docs/ops/DATABASE_PROD_STAGING_AR.md", "section_hint": "migration"},
    {"id": "G-20-RB-04", "name": "db_recovery", "path": "docs/ops/BACKUP_RESTORE.md", "section_hint": "Restore"},
    {"id": "G-20-RB-05", "name": "backup_restore", "path": "docs/ops/BACKUP_RESTORE.md", "section_hint": "Backup"},
    {"id": "G-20-RB-06", "name": "provider_outage", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "upstream"},
    {"id": "G-20-RB-07", "name": "stale_feed", "path": "docs/RUNBOOK.md", "section_hint": "stale"},
    {"id": "G-20-RB-08", "name": "queue_failure", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "Redis"},
    {"id": "G-20-RB-09", "name": "worker_restart", "path": "docs/RUNBOOK.md", "section_hint": "worker"},
    {"id": "G-20-RB-10", "name": "cache_failure", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "Redis"},
    {"id": "G-20-RB-11", "name": "auth_security_incident", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "auth"},
    {"id": "G-20-RB-12", "name": "secret_rotation", "path": "docs/ops/SECRET_ROTATION.md", "section_hint": "rotat"},
    {"id": "G-20-RB-13", "name": "billing_incident", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "webhook"},
    {"id": "G-20-RB-14", "name": "telemetry_outage", "path": "docs/ops/MONITORING_ALERTING_AR.md", "section_hint": "monitor"},
    {"id": "G-20-RB-15", "name": "service_degradation", "path": "docs/ops/INCIDENT_RESPONSE.md", "section_hint": "SEV"},
]


def _req(
    rid: str,
    section: int,
    text: str,
    owner: str,
    runtime: str,
    test: str,
    applicability: str = "required",
    check_key: str = "",
) -> dict[str, Any]:
    return {
        "requirement_id": rid,
        "source_section": section,
        "requirement_text": text,
        "applicability": applicability,
        "canonical_owner": owner,
        "verification_method": check_key or rid,
        "runtime_or_config_path": runtime,
        "test_or_check": test,
    }


def governing_requirements() -> list[dict[str, Any]]:
    """Return exactly 161 governing requirements."""
    reqs: list[dict[str, Any]] = []

    # §4 Environment (7)
    reqs += [
        _req("G-04-001", 4, "Environment inventory discovered and documented", "docs/ops", "docs/ENV_CONFIG_MATRIX.md", "inventory"),
        _req("G-04-002", 4, "ENVIRONMENT_CONFIGURATION_COLLISIONS = 0", "production_guard.py", "config.py", "collision_scan"),
        _req("G-04-003", 4, "PRODUCTION_USING_DEV_DEFAULTS = 0", "production_guard.py", "evaluate_production_guard", "tests/test_production_guard.py"),
        _req("G-04-004", 4, "TEST_CONFIG_LEAKS_INTO_PRODUCTION = 0", "config.py", "ENV separation", "config_leak_scan"),
        _req("G-04-005", 4, "UNCONTROLLED_ENVIRONMENT_OVERRIDES = 0", "docs/ops/ENV_VAR_REGISTRY.md", "railway.json", "override_scan"),
        _req("G-04-006", 4, "HARDCODED_PRODUCTION_SECRETS = 0", "secrets_vault.py", "scripts/secrets_hygiene_scan.py", "hygiene_scan"),
        _req("G-04-007", 4, "MISSING_REQUIRED_PRODUCTION_CONFIG = 0", "production_guard.py", "/api/production/guard", "guard_required_checks"),
    ]

    # §5 Configuration (5)
    reqs += [
        _req("G-05-001", 4, "UNVALIDATED_CRITICAL_CONFIG = 0", "production_guard.py", "startup validation", "guard_startup"),
        _req("G-05-002", 5, "UNSAFE_PRODUCTION_DEFAULTS = 0", "production_guard.py", "insecure default catalog", "default_scan"),
        _req("G-05-003", 5, "CONFIG_PRECEDENCE_CONFLICTS = 0", "config.py", "docs/ENV_CONFIG_MATRIX.md", "precedence_scan"),
        _req("G-05-004", 5, "SILENT_CONFIG_FALLBACKS = 0", "config.py", "log_safety.py", "fallback_scan"),
        _req("G-05-005", 5, "Canonical env registry + startup guard", "docs/ops/ENV_VAR_REGISTRY.md", "production_guard.py", "registry_exists"),
    ]

    # Fix section numbers for G-05-001
    reqs[7]["source_section"] = 5

    # §6 Secrets (4)
    reqs += [
        _req("G-06-001", 6, "HARDCODED_SECRETS = 0", "scripts/secrets_hygiene_scan.py", "repo scan", "hygiene_scan"),
        _req("G-06-002", 6, "SECRET_LOG_LEAK_PATHS = 0", "log_safety.py", "tests/test_codeql_cleartext_logging_closure.py", "log_leak_tests"),
        _req("G-06-003", 6, "MISSING_SECRET_FAIL_CLOSED_GAPS = 0", "production_guard.py", "secrets_master_key check", "guard_secrets"),
        _req("G-06-004", 6, "CROSS_ENV_SECRET_REUSE_GAPS = 0", "secrets_vault.py", "production policy", "cross_env_scan"),
    ]

    # §7 Build (4)
    reqs += [
        _req("G-07-001", 7, "BUILD_REPRODUCIBILITY_VERIFIED", "requirements.hashes.txt", "Dockerfile", "build_files"),
        _req("G-07-002", 7, "UNPINNED_CRITICAL_DEPENDENCIES = 0", "requirements.hashes.txt", "requirements-prod.hashes.txt", "hash_lock_scan"),
        _req("G-07-003", 7, "NON_REPRODUCIBLE_BUILD_STEPS = 0", "Dockerfile", ".github/workflows/ci.yml", "build_steps"),
        _req("G-07-004", 7, "UNTRACKED_GENERATED_ARTIFACTS = 0", "docs/data-room/sbom/", "build output policy", "artifact_policy"),
    ]

    # §8 Supply chain (5)
    reqs += [
        _req("G-08-001", 8, "CRITICAL_KNOWN_VULNERABILITIES blockers = 0", ".github/workflows/security.yml", "pip-audit", "security_workflow"),
        _req("G-08-002", 8, "HIGH known vulnerabilities dispositioned", "docs/SECURITY_REMEDIATION.md", "dependency waivers", "vuln_policy"),
        _req("G-08-003", 8, "UNPINNED_PRIVILEGED_CI_ACTIONS = 0", ".github/workflows/ci.yml", "action pinning", "ci_pin_scan"),
        _req("G-08-004", 8, "UNTRUSTED_PACKAGE_SOURCE_GAPS = 0", "requirements.hashes.txt", "pip --require-hashes", "hash_only_install"),
        _req("G-08-005", 8, "SUPPLY_CHAIN_BLOCKERS = 0", "security.yml", "bandit+sbom", "supply_chain_gate"),
    ]

    # §9 DB/migrations (6)
    reqs += [
        _req("G-09-001", 9, "DATABASES_REVIEWED", "database.py", "postgres_backend.py", "migration_tests"),
        _req("G-09-002", 9, "MIGRATION_PATHS_VERIFIED", "db_upgrade.py", "tests/test_postgres_migration_integrity.py", "migration_tests"),
        _req("G-09-003", 9, "MIGRATION_FAILURE_GAPS = 0", "database.py", "init_db", "migration_tests"),
        _req("G-09-004", 9, "SCHEMA_COMPATIBILITY_GAPS = 0", "postgres_backend.py", "forward migrations", "schema_tests"),
        _req("G-09-005", 9, "PARTIAL_MIGRATION_RECOVERY_GAPS = 0", "postgres_backend.py", "transaction rollback", "migration_recovery_tests"),
        _req("G-09-006", 9, "MULTI_WORKER_MIGRATION_RACE_GAPS = 0", "startup_orchestrator.py", "init_db ordering", "startup_order"),
    ]

    # §10 Backup/restore (6)
    reqs += [
        _req("G-10-001", 10, "BACKUP_ASSETS_CONFIGURED", "scripts/backup_postgres.py", "docs/ops/BACKUP_RESTORE.md", "backup_scripts"),
        _req("G-10-002", 10, "RESTORE_PROCEDURE_GAPS = 0", "scripts/restore_postgres.py", "stderr redaction", "restore_script_tests"),
        _req("G-10-003", 10, "BACKUP_INTEGRITY_GAPS = 0", "scripts/backup_postgres.py", "sha256 sidecar", "backup_integrity"),
        _req("G-10-004", 10, "Local Postgres restore rehearsal performed", "scripts/rehearsal_local_postgres_restore.py", "isolated postgres", "restore_rehearsal"),
        _req("G-10-005", 10, "RESTORE_PATHS_VERIFIED locally", "rehearsal evidence", "data/production_readiness/", "restore_rehearsal_pass"),
        _req("G-10-006", 10, "Live/cloud restore drill", "docs/ops/BACKUP_RESTORE.md", "buyer cloud", "external_restore", applicability="external"),
    ]

    # §11 Data durability (4)
    reqs += [
        _req("G-11-001", 11, "EPHEMERAL_STATE_MISTAKEN_AS_DURABLE = 0", "decision_ledger.py", "tests/test_d01_data_state.py", "durability_tests"),
        _req("G-11-002", 11, "UNRECOVERABLE_CRITICAL_STATE = 0", "database.py", "oracle_audit_chain.py", "durability_tests"),
        _req("G-11-003", 11, "PARTIAL_WRITE_CORRUPTION_PATHS = 0", "database.py", "transaction boundaries", "durability_tests"),
        _req("G-11-004", 11, "DUPLICATE_WRITE_SIDE_EFFECTS = 0", "decision_ledger.py", "idempotency", "idempotency_tests"),
    ]

    # §12 Deployment (6)
    reqs += [
        _req("G-12-001", 12, "DEPLOYMENT_PATH_VERIFIED", "Dockerfile", "railway.json", "deploy_artifacts"),
        _req("G-12-002", 12, "STARTUP_FAILURE_GAPS = 0", "startup_orchestrator.py", "init_db", "startup_tests"),
        _req("G-12-003", 12, "SHUTDOWN_DATA_LOSS_GAPS = 0", "dashboard.py", "lifespan", "shutdown_hooks"),
        _req("G-12-004", 12, "GRACEFUL_TERMINATION_GAPS = 0", "startup_orchestrator.py", "graceful shutdown", "shutdown_hooks"),
        _req("G-12-005", 12, "READINESS_PROBE_FALSE_POSITIVE_GAPS = 0", "dashboard.py", "/health/ready", "readiness_tests"),
        _req("G-12-006", 12, "LIVENESS_PROBE_FALSE_POSITIVE_GAPS = 0", "dashboard.py", "/health/live", "liveness_tests"),
    ]

    # §13 Rollback (5)
    reqs += [
        _req("G-13-001", 13, "Rollback procedure documented", "docs/RUNBOOK.md", "rollback section", "runbook_rollback"),
        _req("G-13-002", 13, "Local Docker rollback rehearsal performed", "scripts/rehearsal_local_rollback.py", "docker", "rollback_rehearsal"),
        _req("G-13-003", 13, "ROLLBACK_DATA_LOSS_RISK = 0", "rehearsal evidence", "rollback state", "rollback_rehearsal_pass"),
        _req("G-13-004", 13, "IRREVERSIBLE_RELEASE_BLOCKERS = 0", "database.py", "forward-only migrations", "migration_policy"),
        _req("G-13-005", 13, "Live Railway rollback validation", "Railway/k8s", "production deploy", "external_rollback", applicability="external"),
    ]

    # §14 Version compatibility (3)
    reqs += [
        _req("G-14-001", 14, "ROLLING_DEPLOYMENT_APPLICABLE documented", "scale_readiness.py", "viral_capacity.py", "ha_docs"),
        _req("G-14-002", 14, "N_NPLUS1_COMPATIBILITY_VERIFIED", "postgres_backend.py", "schema forward compat", "schema_tests"),
        _req("G-14-003", 14, "VERSION_SKEW_GAPS = 0", "api/openapi_responses.py", "API contracts", "contract_tests"),
    ]

    # §15 CI/CD (5)
    reqs += [
        _req("G-15-001", 15, "RELEASE_GATES_ENFORCED", ".github/workflows/ci.yml", "gate-full", "ci_gates"),
        _req("G-15-002", 15, "RELEASE_GATE_BYPASS_PATHS = 0", ".github/workflows/ci.yml", "needs: dependencies", "ci_bypass_scan"),
        _req("G-15-003", 15, "NON_BLOCKING_CRITICAL_CHECKS = 0", ".github/workflows/ci.yml", "blocking jobs", "ci_blocking"),
        _req("G-15-004", 15, "CI_LOCAL_SEMANTIC_DRIFT = 0", "ci.yml vs local pytest", "semantic parity", "ci_parity"),
        _req("G-15-005", 15, "Artifact build + SBOM retention", "docs/data-room/sbom/", "ci sbom step", "sbom_gate"),
    ]

    # §16 Observability (5)
    reqs += [
        _req("G-16-001", 16, "CRITICAL_COMPONENTS_OBSERVABLE", "ops/monitoring_alerting.py", "/metrics", "observability_tests"),
        _req("G-16-002", 16, "OBSERVABILITY_BLIND_SPOTS = 0", "uptime_monitor.py", "observability map", "blind_spot_scan"),
        _req("G-16-003", 16, "SENSITIVE_DATA_LOGGING_GAPS = 0", "log_safety.py", "cleartext logging tests", "log_leak_tests"),
        _req("G-16-004", 16, "MISLEADING_HEALTH_SIGNAL_GAPS = 0", "dashboard.py", "/health/ready", "readiness_tests"),
        _req("G-16-005", 16, "Telemetry operational usefulness", "ops/monitoring_alerting.py", "monitoring_status", "telemetry_shape"),
    ]

    # §17 SLI/SLO (4)
    reqs += [
        _req("G-17-001", 17, "MATERIAL_SLI_MEASURABLE", "uptime_monitor.py", "monitoring_alerting", "sli_sources"),
        _req("G-17-002", 17, "SLO_MEASUREMENT_GAPS = 0", "uptime_monitor.py", "SLA thresholds", "slo_defined"),
        _req("G-17-003", 17, "FALSE_SLO_EVIDENCE_PATHS = 0", "scale_readiness.py", "honest capacity claim", "slo_honesty"),
        _req("G-17-004", 17, "SLI breach behavior defined", "ops/monitoring_alerting.py", "alert thresholds", "breach_behavior"),
    ]

    # §18 Alerting (5)
    reqs += [
        _req("G-18-001", 18, "Critical failure modes with local alert path", "ops/monitoring_alerting.py", "failure_mode_population", "failure_modes_alerted"),
        _req("G-18-002", 18, "TRUE_UNALERTED_CRITICAL_FAILURE_MODES = 0", "failure_modes.py", "derived population", "failure_modes_derived"),
        _req("G-18-003", 18, "ALERT_FALSE_SUCCESS_PATHS = 0", "ops/monitoring_alerting.py", "probe overall_ok semantics", "alert_semantics"),
        _req("G-18-004", 18, "ALERT_STORM_GAPS = 0", "ops/monitoring_alerting.py", "cooldown", "alert_cooldown"),
        _req("G-18-005", 18, "External pager delivery validation", "setup_monitoring.py", "UptimeRobot", "external_pager", applicability="external"),
    ]

    # §19 Incident (4)
    reqs += [
        _req("G-19-001", 19, "INCIDENT_RUNBOOKS_COMPLETE", "docs/ops/INCIDENT_RESPONSE.md", "OWNER_CONTACT_REGISTRY", "incident_docs"),
        _req("G-19-002", 19, "INCIDENT_RESPONSE_LOCAL_GAPS = 0", "docs/ops/INCIDENT_RESPONSE.md", "severity table", "incident_complete"),
        _req("G-19-003", 19, "Tabletop human exercise", "docs/ops/HANDOVER_TABLETOP.md", "human", "external_tabletop", applicability="external"),
        _req("G-19-004", 19, "Severity levels and escalation defined", "docs/ops/INCIDENT_RESPONSE.md", "PAGER_ONCALL.md", "severity_defined"),
    ]

    # §20 Runbooks: 2 aggregate gates (derived from 15 semantic checks) + 15 semantic
    reqs += [
        _req("G-20-003", 20, "RUNBOOKS_PLACEHOLDER_ONLY = 0", "runbook_semantics", "semantic verify", "runbook_placeholder_scan"),
        _req("G-20-004", 20, "RUNBOOK_EXECUTABILITY_GAPS = 0", "runbook_semantics", "8-part structure", "runbook_gaps"),
    ]
    for rb in MATERIAL_RUNBOOK_SPECS:
        reqs.append(
            _req(
                rb["id"],
                20,
                f"Runbook semantic completeness: {rb['name']}",
                rb["path"],
                rb["section_hint"],
                "runbook_semantic",
                check_key=f"runbook_semantic_{rb['name']}",
            )
        )

    # §21 Performance (6)
    reqs += [
        _req("G-21-001", 21, "CRITICAL_WORKLOADS_PERFORMANCE_TESTED", "scale_readiness.py", "performance tests", "perf_tests"),
        _req("G-21-002", 21, "PERFORMANCE_BLOCKERS = 0", "tests/test_radical_dd_scale_closure.py", "scale tests", "perf_tests"),
        _req("G-21-003", 21, "CAPACITY_BLOCKERS = 0", "viral_capacity.py", "parallelism", "capacity_scan"),
        _req("G-21-004", 21, "RESOURCE_LEAKS = 0", "tests/test_rc2_chaos_resilience.py", "resource tests", "resource_tests"),
        _req("G-21-005", 21, "UNBOUNDED_RESOURCE_PATHS = 0", "security_middleware.py", "rate limits", "bounded_resources"),
        _req("G-21-006", 21, "Signed cloud-scale load evidence", "scale_readiness.py", "LOAD_TEST_RUN_LOG.md", "external_load", applicability="external"),
    ]

    # §22 Concurrency (4)
    reqs += [
        _req("G-22-001", 22, "CONCURRENCY_SCENARIOS_VERIFIED", "service_bus.py", "chaos tests", "concurrency_tests"),
        _req("G-22-002", 22, "CONCURRENCY_GAPS = 0", "tests/test_service_bus_distributed.py", "concurrency", "concurrency_tests"),
        _req("G-22-003", 22, "RACE_CONDITION_GAPS = 0", "tests/test_rc2_chaos_resilience.py", "race tests", "concurrency_tests"),
        _req("G-22-004", 22, "RETRY_STORM_GAPS = 0", "service_bus.py", "retry policy", "retry_policy_scan"),
    ]

    # §23 Rate limits (4)
    reqs += [
        _req("G-23-001", 23, "RATE_LIMITED_SURFACES_VERIFIED", "security_middleware.py", "rate limiter", "rate_limit_tests"),
        _req("G-23-002", 23, "RATE_LIMIT_BYPASSES = 0", "anonymous_route_foundation.py", "public routes", "rate_limit_bypass_scan"),
        _req("G-23-003", 23, "BACKPRESSURE_GAPS = 0", "service_bus.py", "backpressure", "backpressure_scan"),
        _req("G-23-004", 23, "Rate limit audit non-mutating", "scripts/free_api_rate_limit_audit.py", "read-only audit", "rate_audit_readonly"),
    ]

    # §24 Cache (4)
    reqs += [
        _req("G-24-001", 24, "CACHE_TRUTH_VIOLATIONS = 0", "gas_oracle.py", "fail-closed cache", "cache_tests"),
        _req("G-24-002", 24, "CACHE_TENANT_ISOLATION_GAPS = 0", "org_tenant.py", "tenant cache keys", "tenant_cache_scan"),
        _req("G-24-003", 24, "CACHE_STALE_FALSE_LIVE_GAPS = 0", "gas_oracle.py", "stale → None", "cache_tests"),
        _req("G-24-004", 24, "CACHE_RECOVERY_GAPS = 0", "scale_readiness.py", "redis rebuild", "cache_recovery"),
    ]

    # §25 Async (5)
    reqs += [
        _req("G-25-001", 25, "ASYNC_PATHS_VERIFIED", "service_bus.py", "worker paths", "async_tests"),
        _req("G-25-002", 25, "ASYNC_RELIABILITY_GAPS = 0", "startup_orchestrator.py", "async reliability", "async_tests"),
        _req("G-25-003", 25, "POISON_MESSAGE_GAPS = 0", "service_bus.py", "DLQ/retry", "poison_scan"),
        _req("G-25-004", 25, "WORKER_RESTART_GAPS = 0", "startup_orchestrator.py", "worker restart", "worker_scan"),
        _req("G-25-005", 25, "Worker shutdown graceful", "startup_orchestrator.py", "shutdown", "shutdown_hooks"),
    ]

    # §26 External deps (4)
    reqs += [
        _req("G-26-001", 26, "EXTERNAL_DEPENDENCIES_LOCALLY_HARDENED", "fee_matrix.py", "gas_oracle.py", "dependency_tests"),
        _req("G-26-002", 26, "LOCAL_EXTERNAL_DEPENDENCY_GAPS = 0", "slippage_guard.py", "financial tests", "dependency_tests"),
        _req("G-26-003", 26, "GENUINE_LIVE_VALIDATION_PENDING", "market providers", "live phase", "external_vendor", applicability="external"),
        _req("G-26-004", 26, "Dependency timeout/retry/circuit breaker", "fee_matrix.py", "timeout policy", "dependency_hardening"),
    ]

    # §27 Security boundary (10)
    reqs += [
        _req("G-27-001", 27, "PRODUCTION_SECURITY_BYPASS_PATHS = 0", "security_middleware.py", "auth tests", "security_tests"),
        _req("G-27-002", 27, "DEBUG_OR_DEV_PRODUCTION_EXPOSURE = 0", "production_guard.py", "debug flags", "debug_exposure_scan"),
        _req("G-27-003", 27, "UNPROTECTED_ADMIN_PATHS = 0", "anonymous_route_foundation.py", "admin routes", "admin_route_tests"),
        _req("G-27-004", 27, "SESSION_PRODUCTION_GAPS = 0", "security_auth.py", "session tests", "session_tests"),
        _req("G-27-005", 27, "CSRF_PRODUCTION_GAPS = 0", "security_middleware.py", "CSRF checks", "csrf_tests"),
        _req("G-27-006", 27, "CORS_PRODUCTION_GAPS = 0", "security_middleware.py", "CORS policy", "cors_scan"),
        _req("G-27-007", 27, "SECURITY_HEADER_GAPS = 0", "security_middleware.py", "CSP/HSTS", "header_tests"),
        _req("G-27-008", 27, "TLS/transport security", "transport_webhook_env/transport.py", "HTTPS enforcement", "transport_tests"),
        _req("G-27-009", 27, "Webhook validation", "billing/webhook_processor.py", "webhook secrets", "webhook_tests"),
        _req("G-27-010", 27, "Tenant isolation", "org_tenant.py", "tenant tests", "tenant_tests"),
    ]

    # §28 Privacy (4)
    reqs += [
        _req("G-28-001", 28, "PRODUCTION_PRIVACY_GAPS = 0", "docs/ops/PRIVACY_AND_AUDIT_ROADMAP.md", "retention", "privacy_scan"),
        _req("G-28-002", 28, "RETENTION_ENFORCEMENT_GAPS = 0", "data_governance/retention.py", "retention policy", "retention_scan"),
        _req("G-28-003", 28, "DELETION_PROPAGATION_GAPS = 0", "governance/fds_retention_incident_supply_chain.py", "deletion paths", "deletion_scan"),
        _req("G-28-004", 28, "BACKUP_RETENTION_CONFLICTS = 0", "docs/ops/BACKUP_RESTORE.md", "retention alignment", "backup_retention"),
    ]

    # §29 B2B (4)
    reqs += [
        _req("G-29-001", 29, "B2B_PRODUCTION_GAPS = 0", "b2b_websocket_hub.py", "institutional API", "b2b_tests"),
        _req("G-29-002", 29, "API_CONTRACT_GAPS = 0", "api/openapi_responses.py", "error contract", "api_contract_tests"),
        _req("G-29-003", 29, "API_VERSIONING_GAPS = 0", "api/openapi_responses.py", "versioning", "api_version_scan"),
        _req("G-29-004", 29, "B2B_METERING_GAPS = 0", "oracle_audit_chain.py", "metering", "metering_scan"),
    ]

    # §30 Frontend (4)
    reqs += [
        _req("G-30-001", 30, "FRONTEND_PRODUCTION_GAPS = 0", "dashboard.py", "templates/", "frontend_tests"),
        _req("G-30-002", 30, "BROKEN_PRODUCTION_ASSET_PATHS = 0", "static/", "asset paths", "asset_scan"),
        _req("G-30-003", 30, "CLIENT_SECRET_EXPOSURE_GAPS = 0", "dashboard.py", "public openapi filter", "client_secret_scan"),
        _req("G-30-004", 30, "PUBLIC_ERROR_DISCLOSURE_GAPS = 0", "api/openapi_responses.py", "error pages", "error_disclosure_scan"),
    ]

    # §31 Kill switches (3)
    reqs += [
        _req("G-31-001", 31, "CRITICAL_KILL_SWITCHES_VERIFIED", "production_guard.py", "SOFT_LAUNCH guards", "kill_switch_scan"),
        _req("G-31-002", 31, "KILL_SWITCH_GAPS = 0", "production_guard.py", "demo key disabled", "kill_switch_scan"),
        _req("G-31-003", 31, "Kill switch audit trail", "data/kill_rate_events.jsonl", "audit path", "kill_switch_audit"),
    ]

    # §32 Financial safety (1)
    reqs += [
        _req("G-32-001", 32, "REAL_MONEY_EXECUTION_PERFORMED = false + local safeguards", "slippage_guard.py", "financial tests", "financial_safety_tests"),
    ]

    # §33 HA (4)
    reqs += [
        _req("G-33-001", 33, "HA_ARCHITECTURE_GAPS = 0 (local)", "scale_readiness.py", "HA checks", "ha_local"),
        _req("G-33-002", 33, "LOCALLY_REMEDIABLE_SPOF = 0", "scale_readiness.py", "SPOF doc", "spof_local"),
        _req("G-33-003", 33, "HA live failover proof", "cloud infra", "multi-AZ", "external_ha", applicability="external"),
        _req("G-33-004", 33, "SPOF documented honestly", "scale_readiness.py", "SPOF list", "spof_documented"),
    ]

    # §34 DR (5)
    reqs += [
        _req("G-34-001", 34, "DR_LOCAL_PROCEDURES_VERIFIED", "docs/ops/BACKUP_RESTORE.md", "INCIDENT_RESPONSE.md", "dr_docs"),
        _req("G-34-002", 34, "DR_LOCAL_GAPS = 0", "docs/RUNBOOK.md", "recovery sequence", "dr_complete"),
        _req("G-34-003", 34, "DR live exercise", "staging/prod", "human exercise", "external_dr", applicability="external"),
        _req("G-34-004", 34, "RTO/RPO documented", "docs/ops/BACKUP_RESTORE.md", "RPO/RTO table", "rto_rpo_docs"),
        _req("G-34-005", 34, "Recovery sequence defined", "docs/ops/INCIDENT_RESPONSE.md", "recovery steps", "recovery_sequence"),
    ]

    # §35 Drift (4)
    reqs += [
        _req("G-35-001", 35, "DEPLOYMENT_DRIFT_GAPS = 0", "railway.json", "docker-compose.yml", "deploy_drift_scan"),
        _req("G-35-002", 35, "CONFIG_DRIFT_GAPS = 0", "docs/ENV_CONFIG_MATRIX.md", "ENV_VAR_REGISTRY", "config_drift_scan"),
        _req("G-35-003", 35, "UNTRACKED_MANUAL_PRODUCTION_STEPS = 0", "docs/RUNBOOK.md", "documented deploy", "manual_steps_scan"),
        _req("G-35-004", 35, "UNVERSIONED_PRODUCTION_CONFIGURATION = 0", "railway.json", "versioned config", "unversioned_config_scan"),
    ]

    if len(reqs) != 161:
        raise RuntimeError(f"Governing catalog must have 161 requirements, got {len(reqs)}")
    return reqs
