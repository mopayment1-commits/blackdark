"""
BLACKDARK — Senior Technical Due Diligence (requirements 1–20).

Strict acquisition-committee evaluation: PASS | FAIL | PARTIALLY PASS | NOT APPLICABLE.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import aiohttp

# Sonar S1192: duplicated string literals
STR_PARTIALLY_PASS = 'PARTIALLY PASS'

ROOT = Path(__file__).resolve().parent
Verdict = Literal["PASS", "FAIL", STR_PARTIALLY_PASS, "NOT APPLICABLE"]


@dataclass
class RequirementAssessment:
    id: int
    title: str
    verdict: Verdict
    why: str
    location: str
    business_risk: str
    technical_risk: str
    committee_view: str
    valuation_impact: str
    enterprise_solution: str
    evidence: dict[str, Any] | None = None


def _count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


async def _probe_production_oracle() -> dict[str, Any]:
    url = os.getenv(
        "DD_PRODUCTION_URL",
        "https://blackdark-production.up.railway.app/oracle/BTC",
    ).strip()
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            body = await resp.json(content_type=None)
            return {
                "url": url,
                "http_status": resp.status,
                "ok": resp.status == 200 and isinstance(body, dict) and body.get("symbol"),
                "release_hint": body.get("verdict") if isinstance(body, dict) else None,
            }
    except Exception as exc:
        return {"url": url, "http_status": None, "ok": False, "error": str(exc)[:200]}


async def build_technical_due_diligence_report(*, probe_production: bool = True) -> dict[str, Any]:
    from due_diligence import due_diligence_report

    tech = due_diligence_report()
    checks = tech.get("checks") or {}
    coverage = tech.get("coverage") or {}
    uptime = tech.get("uptime") or {}
    latency = tech.get("latency") or {}
    tech.get("ha") or {}

    prod_oracle: dict[str, Any] = {}
    if probe_production:
        prod_oracle = await _probe_production_oracle()

    # Acquisition + moat (async)
    acquisition: dict[str, Any] = {}
    moat: dict[str, Any] = {}
    try:
        from acquisition_assets_service import build_acquisition_asset_audit

        acquisition = await build_acquisition_asset_audit()
    except Exception as exc:
        acquisition = {"error": str(exc)[:200]}
    try:
        from data_moat_guard import build_moat_build_status

        moat = await build_moat_build_status()
    except Exception as exc:
        moat = {"error": str(exc)[:200]}

    # Secrets / crypto in prod requirements
    prod_req = (ROOT / "requirements-prod.txt").read_text(encoding="utf-8") if (ROOT / "requirements-prod.txt").exists() else ""
    has_cryptography = "cryptography" in prod_req

    # CI workflow
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_text = ci_path.read_text(encoding="utf-8") if ci_path.exists() else ""
    ci_has_cov_gate = "cov-fail-under=90" in ci_text
    ci_has_dd_verify = "due_diligence_verify.py" in ci_text
    ci_has_docker = "docker build" in ci_text.lower()

    # GDPR module
    gdpr_module = (ROOT / "gdpr_service.py").exists()

    # Observability
    sentry_configured = bool(os.getenv("SENTRY_DSN", "").strip())

    # Dashboard size
    dashboard_lines = _count_lines(ROOT / "dashboard.py")

    probes_total = int(uptime.get("probes_total") or 0)
    coverage_pct = float(coverage.get("coverage_percent") or 0)
    prod_ok = bool(prod_oracle.get("ok"))
    pillars = acquisition.get("pillars") or {}
    if not isinstance(pillars, dict):
        pillars = {}
    community = pillars.get("community") or {}
    behavior = pillars.get("behavior") or {}
    models = pillars.get("models") or {}
    paid = int((community.get("evidence") or {}).get("paid_subscribers") or 0)
    behavior_events = int((behavior.get("evidence") or {}).get("total_events") or 0)
    model_verdict = str(models.get("verdict") or "none")

    deal_verdict = str(acquisition.get("deal_verdict") or "unknown")

    requirements: list[RequirementAssessment] = []

    # 1 Uptime
    if probes_total >= 10 and checks.get("uptime_sla_99_99"):
        v1: Verdict = "PASS"
    elif probes_total >= 10:
        v1 = STR_PARTIALLY_PASS
    else:
        v1 = "FAIL"
    requirements.append(
        RequirementAssessment(
            1,
            "Uptime SLA 99.99%",
            v1,
            f"probes_total={probes_total}; meets_sla={checks.get('uptime_sla_99_99')}. "
            "External monitor proof still required for enterprise DD.",
            "due_diligence.py:65-74; uptime_monitor.py:57-74; /health/live records probes",
            "Unauditable SLA blocks B2B/API contracts.",
            "Single replica without external monitor export.",
            "Zero probes = automatic FAIL; ≥10 probes with SLA = credible.",
            "-15% to -25% infra multiple if probes insufficient.",
            "UptimeRobot/Datadog on /health/live; multi-replica HA deploy.",
            {"probes_total": probes_total, "uptime_percent": uptime.get("uptime_percent")},
        )
    )

    # 2 Latency
    v2: Verdict = "PASS" if checks.get("latency_p99_le_50ms") else STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            2,
            "Latency P99 ≤ 50ms (price → decision)",
            v2,
            "Benchmark applies to warm in-memory fast_scan path only, not full Oracle REST E2E.",
            "latency_audit.py:37-103; fast_scan_engine.py",
            "Marketing sub-50ms for Oracle would mislead traders.",
            "Production Oracle uses HTTP fallbacks (hundreds of ms+).",
            "Accept for arb scan engine; reject for user-facing Oracle SLA.",
            "No HFT premium without published per-endpoint latency.",
            "Separate SLAs for decision engine vs E2E API; WS+Redis colocation.",
            {"p99_ms": latency.get("p99_ms"), "meets_target": checks.get("latency_p99_le_50ms")},
        )
    )

    # 3 Coverage
    v3: Verdict = "PASS" if checks.get("profit_fee_coverage_ge_90") else "FAIL"
    requirements.append(
        RequirementAssessment(
            3,
            "Profit/fee algorithm test coverage ≥ 90%",
            v3,
            f"Coverage gate at {coverage_pct}% (target 90%).",
            "due_diligence.py:15-53; slippage_guard.py; .github/workflows/ci.yml",
            "Fee/slippage errors → wrong profit signals.",
            "Core monetization math not gate-protected below 90%.",
            "Standard merge blocker for fintech acquirers.",
            "-5% valuation; escrow/holdback if below gate.",
            "Maintain pytest --cov-fail-under=90 in CI.",
            {"coverage_percent": coverage_pct, "passed": coverage.get("passed")},
        )
    )

    # 4 HA
    v4: Verdict = "PASS" if checks.get("ha_architecture_ready") and prod_ok else STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            4,
            "High availability architecture",
            v4,
            "HA compose + nginx exist; production may still be single Railway replica.",
            "docker-compose.ha.yml; nginx/blackdark.conf; uptime_monitor.py:95+",
            "HA documentation without operational failover = credibility gap.",
            "No proven load-balanced failover in prod.",
            "HA-ready ≠ HA-deployed.",
            "Architecture option value only.",
            "Deploy docker-compose.ha.yml or K8s with 2+ web replicas.",
            {"ha_architecture_ready": checks.get("ha_architecture_ready")},
        )
    )

    # 5 Production deployment
    v5: Verdict = "PASS" if prod_ok else "FAIL"
    requirements.append(
        RequirementAssessment(
            5,
            "Production deployment reliability",
            v5,
            f"Live Oracle probe ok={prod_ok} status={prod_oracle.get('http_status')}.",
            "Dockerfile; railway.toml; dashboard.py lifespan; run_service.py",
            "Product cannot be sold if it cannot stay online.",
            "Monolith boot + deploy pipeline fragility.",
            "Deal breaker until 30-day stable prod.",
            "-30% to -50% until stable prod demonstrated.",
            "CI Docker build smoke; deferred DB boot; healthcheck 180s+.",
            prod_oracle,
        )
    )

    # 6 Oracle ingestion
    v6: Verdict = "PASS" if prod_ok else "FAIL"
    requirements.append(
        RequirementAssessment(
            6,
            "Oracle / live price ingestion (operational)",
            v6,
            "Multi-source REST fallbacks in market_context.py; prod must return price.",
            "market_context.py:385-414; dashboard.py /oracle/{symbol}",
            "Core product non-functional without live price.",
            "Binance geo-block on cloud; fallbacks required.",
            "Code shows awareness; ops must prove live.",
            "Core failure → pass or asset-only pricing.",
            "Verify /api/diagnostics/price/BTC; cache last-good price.",
            prod_oracle,
        )
    )

    # 7 Data moat
    dataset = moat.get("dataset") if isinstance(moat.get("dataset"), dict) else {}
    live_labeled = int(
        moat.get("live_labeled")
        or moat.get("live_labeled_oracle")
        or dataset.get("live_labeled")
        or dataset.get("live_labeled_oracle")
        or 0
    )
    if live_labeled >= 50:
        v7: Verdict = "PASS"
    elif live_labeled >= 1:
        v7: Verdict = STR_PARTIALLY_PASS
    else:
        v7: Verdict = "FAIL"
    requirements.append(
        RequirementAssessment(
            7,
            "Data moat — live-only oracle labels",
            v7,
            f"live_labeled={live_labeled} (LOI minimum 50).",
            "data_moat_guard.py; docs/DATA_ROOM.md",
            "Defensibility unproven at scale.",
            "Policy guards exist; volume may be insufficient.",
            "Good policy; insufficient proof.",
            "Moat at option value only.",
            "Run prod with DATA_MOAT_LIVE_ONLY=true; daily moat report.",
            {"live_labeled": live_labeled, "moat": moat},
        )
    )

    # 8 ML in production
    v8: Verdict = "PASS" if model_verdict in {"moderate", "strong"} else "FAIL"
    requirements.append(
        RequirementAssessment(
            8,
            "ML model in production",
            v8,
            f"Model pillar verdict={model_verdict}; production_engine=rules_engine.",
            "acquisition_assets_service.py _audit_models_asset; ml/",
            "AI Oracle marketing overstates capability.",
            "Flywheel not closed to production model.",
            "AI washing risk — discount AI multiple.",
            "No AI premium without deployed .joblib.",
            "Train/deploy first model at 50+ labels; MLflow registry.",
            {"model_verdict": model_verdict},
        )
    )

    # 9 Behavior data
    if behavior_events >= 1000:
        v9: Verdict = "PASS"
    elif behavior_events >= 100:
        v9: Verdict = STR_PARTIALLY_PASS
    else:
        v9: Verdict = "FAIL"
    requirements.append(
        RequirementAssessment(
            9,
            "Behavior data asset volume",
            v9,
            f"behavior_events_30d={behavior_events} (LOI target 1,000+).",
            "behavior_data_service.py; acquisition_assets_service.py",
            "No usage graph = no retention analytics.",
            "Instrumentation exists; volume may be low.",
            "Fastest moat to build — not built at scale.",
            "Zero behavior-data premium below threshold.",
            "Enable BEHAVIOR_DATA_ENABLED; warehouse export.",
            {"behavior_events_30d": behavior_events},
        )
    )

    # 10 Paying subscribers
    if paid >= 10:
        v10: Verdict = "PASS"
    elif paid >= 1:
        v10: Verdict = STR_PARTIALLY_PASS
    else:
        v10: Verdict = "FAIL"
    requirements.append(
        RequirementAssessment(
            10,
            "Community / paying subscribers",
            v10,
            f"paid_subscribers={paid} (LOI minimum 10).",
            "acquisition_assets_service.py; docs/DATA_ROOM.md",
            "No proven PMF or revenue.",
            "Stripe integrated but not proven at scale.",
            "Pass unless off-repo revenue proof.",
            "Asset purchase not revenue multiple.",
            "90-day paid pilot; MRR dashboard.",
            {"paid_subscribers": paid},
        )
    )

    # 11 API key security
    audit_persist = (ROOT / "data" / "api_key_access_audit.jsonl").exists() or (
        ROOT / "api_key_security_guard.py"
    ).exists()
    v11: Verdict = STR_PARTIALLY_PASS if audit_persist else "FAIL"
    requirements.append(
        RequirementAssessment(
            11,
            "API key security & custody",
            v11,
            "Withdraw-block + vault guards implemented; audit trail file-backed when enabled.",
            "api_key_security_guard.py; user_keys_service.py",
            "Key compromise = direct user financial loss.",
            "HSM/KMS not integrated.",
            "Acceptable pre-revenue; insufficient at custody scale.",
            "Blocks exchange-custody premium without HSM.",
            "Persist audit to DB; AWS KMS; SOC2 Type I.",
            {"audit_file": str(ROOT / "data" / "api_key_access_audit.jsonl")},
        )
    )

    # 12 Secrets
    v12: Verdict = "PASS" if has_cryptography else "FAIL"
    requirements.append(
        RequirementAssessment(
            12,
            "Secrets management",
            v12,
            f"cryptography in requirements-prod.txt={has_cryptography}.",
            "secrets_vault.py; requirements-prod.txt",
            "Vault may fail in slim Docker without cryptography.",
            "Missing prod dependency = latent crash.",
            "Day-1 security review item.",
            "-5% holdback until verified in prod.",
            "cryptography in prod reqs; HashiCorp Vault or AWS Secrets Manager.",
            {"cryptography_in_prod": has_cryptography},
        )
    )

    # 13 Regulatory
    v13: Verdict = STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            13,
            "Regulatory compliance (investment advice)",
            v13,
            "regulatory_compliance_guard maps verdicts to analytics labels; all public routes must sanitize.",
            "regulatory_compliance_guard.py; security_sanitize.py; dashboard.py oracle routes",
            "Unlicensed investment advice → regulatory enforcement.",
            "Inconsistent sanitization across endpoints.",
            "Good intent; legal review required.",
            "Legal escrow $50k–$200k.",
            "Apply guard on all public Oracle outputs; geo-fencing.",
            None,
        )
    )

    # 14 Auth
    v14: Verdict = STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            14,
            "Authentication & session security",
            v14,
            "PBKDF2-SHA256 sessions; no MFA/SSO in DD scope.",
            "auth_service.py; security_auth.py",
            "Account takeover high impact on crypto platform.",
            "Consumer MVP auth; not enterprise SSO.",
            "OK for SMB; insufficient for B2B exchange.",
            "Blocks enterprise upsell.",
            "MFA; OAuth2/OIDC; WAF rate limits.",
            None,
        )
    )

    # 15 Architecture
    v15: Verdict = STR_PARTIALLY_PASS if dashboard_lines < 3000 else "FAIL"
    requirements.append(
        RequirementAssessment(
            15,
            "Architecture modularity",
            v15,
            f"dashboard.py={dashboard_lines} lines; api/routers extraction in progress.",
            "docs/ARCHITECTURE.md; dashboard.py; api/routers/",
            "High bus factor; slow acquirer onboarding.",
            "God-module coupling increases integration cost.",
            "Acceptable with debt.",
            "+6 month integration cost post-close.",
            "Complete router extraction; import-linter.",
            {"dashboard_lines": dashboard_lines},
        )
    )

    # 16 Observability
    v16: Verdict = STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            16,
            "Observability",
            v16,
            f"Prometheus /metrics + DD endpoints; Sentry configured={sentry_configured}.",
            "observability.py; api/routers/observability.py",
            "Cannot diagnose prod incidents without tracing/logs.",
            "Blind spots in production failures.",
            "MVP observability only.",
            "Standard ops cost post-acquisition.",
            "Datadog/Grafana; OpenTelemetry; structured JSON logs.",
            {"sentry_configured": sentry_configured},
        )
    )

    # 17 CI/CD
    if ci_has_cov_gate and ci_has_dd_verify and ci_has_docker:
        v17: Verdict = "PASS"
    elif ci_has_cov_gate and ci_has_dd_verify:
        v17 = STR_PARTIALLY_PASS
    else:
        v17 = "FAIL"
    requirements.append(
        RequirementAssessment(
            17,
            "CI/CD & automated testing",
            v17,
            f"cov_gate={ci_has_cov_gate} dd_verify={ci_has_dd_verify} docker_build={ci_has_docker}.",
            ".github/workflows/ci.yml; scripts/due_diligence_verify.py",
            "Broken code can reach main without gates.",
            "Immature DevOps for acquisition target.",
            "-10% engineering risk discount.",
            "CI: pytest + cov 90% + Docker build + smoke health.",
            {"ci_has_cov_gate": ci_has_cov_gate, "ci_has_dd_verify": ci_has_dd_verify, "ci_has_docker": ci_has_docker},
        )
    )

    # 18 Documentation
    docs_ok = all((ROOT / p).exists() for p in ("docs/ARCHITECTURE.md", "docs/DATA_ROOM.md", "docs/RUNBOOK.md"))
    v18: Verdict = "PASS" if docs_ok else STR_PARTIALLY_PASS
    requirements.append(
        RequirementAssessment(
            18,
            "Documentation & data room",
            v18,
            "Architecture, data room, runbook present; label as-deployed vs target.",
            "docs/; due_diligence_bundle.py",
            "Over-documentation of aspirational architecture misleads.",
            "Low technical risk.",
            "+5% for transparency.",
            "Auto-generate DD bundle in CI artifact.",
            {"docs_present": docs_ok},
        )
    )

    # 19 GDPR
    v19: Verdict = "PASS" if gdpr_module else "FAIL"
    requirements.append(
        RequirementAssessment(
            19,
            "GDPR / data transfer readiness",
            v19,
            f"gdpr_service.py present={gdpr_module}; DSR export/erase API required.",
            "gdpr_service.py; api/routers/privacy.py; docs/DATA_ROOM.md",
            "Cannot transfer EU user base without DSR workflow.",
            "No automated access/erasure.",
            "Pass on user-data acquisition until GDPR pack.",
            "User list valued at $0 until compliant.",
            "DSR API; consent registry; DPIA template.",
            {"gdpr_module": gdpr_module},
        )
    )

    # 20 M&A
    if deal_verdict in {"consider_strategic_acquisition", "conditional_acquisition"}:
        v20: Verdict = STR_PARTIALLY_PASS
    elif deal_verdict == "pass_build_instead":
        v20 = "FAIL"
    else:
        v20 = STR_PARTIALLY_PASS if prod_ok else "FAIL"
    requirements.append(
        RequirementAssessment(
            20,
            "Non-code acquisition value / M&A verdict",
            v20,
            f"deal_verdict={deal_verdict}; prod_oracle_ok={prod_ok}.",
            "acquisition_assets_service.py; due_diligence_bundle.py",
            "Buyer pays for code that must run + unproven data.",
            "High integration/rebuild cost if moat weak.",
            "Acqui-hire or tuck-in unless metrics improve.",
            "$0–$500k pre-revenue range without paid users.",
            "90-day proof: stable prod, 50+ labels, 10+ paid, 90% coverage.",
            {"deal_verdict": deal_verdict},
        )
    )

    counts = dict.fromkeys(("PASS", "FAIL", STR_PARTIALLY_PASS, "NOT APPLICABLE"), 0)
    for r in requirements:
        counts[r.verdict] += 1

    overall = "pass" if counts["FAIL"] == 0 and counts[STR_PARTIALLY_PASS] <= 5 else "partial"
    if counts["FAIL"] >= 5:
        overall = "fail"

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_verdict": overall,
        "committee_statement": (
            "Salvageable engineering with honest documentation. "
            "Production Oracle must stay live; close FAIL gaps (ML, subscribers, GDPR proof) for LOI."
        ),
        "scorecard": counts,
        "requirements": [asdict(r) for r in requirements],
        "automated_checks": tech,
        "production_probe": prod_oracle,
    }


def run_sync_report(*, probe_production: bool = True) -> dict[str, Any]:
    import asyncio

    return asyncio.run(build_technical_due_diligence_report(probe_production=probe_production))
