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



def _tier_by_thresholds(value: int, high: int, mid: int) -> Verdict:
    if value >= high:
        return "PASS"
    if value >= mid:
        return STR_PARTIALLY_PASS
    return "FAIL"


def _req_uptime(probes_total: int, checks: dict[str, Any], uptime: dict[str, Any]) -> RequirementAssessment:
    if probes_total >= 10 and checks.get("uptime_sla_99_99"):
        v1: Verdict = "PASS"
    elif probes_total >= 10:
        v1 = STR_PARTIALLY_PASS
    else:
        v1 = "FAIL"
    return RequirementAssessment(
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


def _req_latency(checks: dict[str, Any], latency: dict[str, Any]) -> RequirementAssessment:
    v2: Verdict = "PASS" if checks.get("latency_p99_le_50ms") else STR_PARTIALLY_PASS
    return RequirementAssessment(
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


def _req_coverage(checks: dict[str, Any], coverage: dict[str, Any], coverage_pct: float) -> RequirementAssessment:
    v3: Verdict = "PASS" if checks.get("profit_fee_coverage_ge_90") else "FAIL"
    return RequirementAssessment(
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


def _req_ha(checks: dict[str, Any], prod_ok: bool) -> RequirementAssessment:
    v4: Verdict = "PASS" if checks.get("ha_architecture_ready") and prod_ok else STR_PARTIALLY_PASS
    return RequirementAssessment(
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


def _req_prod(prod_ok: bool, prod_oracle: dict[str, Any]) -> RequirementAssessment:
    v5: Verdict = "PASS" if prod_ok else "FAIL"
    return RequirementAssessment(
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


def _req_oracle_ingest(prod_ok: bool, prod_oracle: dict[str, Any]) -> RequirementAssessment:
    v6: Verdict = "PASS" if prod_ok else "FAIL"
    return RequirementAssessment(
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


def _req_moat(moat: dict[str, Any]) -> RequirementAssessment:
    dataset = moat.get("dataset") if isinstance(moat.get("dataset"), dict) else {}
    live_labeled = int(
        moat.get("live_labeled")
        or moat.get("live_labeled_oracle")
        or dataset.get("live_labeled")
        or dataset.get("live_labeled_oracle")
        or 0
    )
    v7 = _tier_by_thresholds(live_labeled, 50, 1)
    return RequirementAssessment(
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


def _req_ml(model_verdict: str) -> RequirementAssessment:
    v8: Verdict = "PASS" if model_verdict in {"moderate", "strong"} else "FAIL"
    return RequirementAssessment(
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


def _req_behavior(behavior_events: int) -> RequirementAssessment:
    v9 = _tier_by_thresholds(behavior_events, 1000, 100)
    return RequirementAssessment(
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


def _req_paid(paid: int) -> RequirementAssessment:
    v10 = _tier_by_thresholds(paid, 10, 1)
    return RequirementAssessment(
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


def _req_api_keys() -> RequirementAssessment:
    audit_persist = (ROOT / "data" / "api_key_access_audit.jsonl").exists() or (
        ROOT / "api_key_security_guard.py"
    ).exists()
    v11: Verdict = STR_PARTIALLY_PASS if audit_persist else "FAIL"
    return RequirementAssessment(
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


def _req_secrets(has_cryptography: bool) -> RequirementAssessment:
    v12: Verdict = "PASS" if has_cryptography else "FAIL"
    return RequirementAssessment(
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


def _req_regulatory() -> RequirementAssessment:
    return RequirementAssessment(
        13,
        "Regulatory compliance (investment advice)",
        STR_PARTIALLY_PASS,
        "regulatory_compliance_guard maps verdicts to analytics labels; all public routes must sanitize.",
        "regulatory_compliance_guard.py; security_sanitize.py; dashboard.py oracle routes",
        "Unlicensed investment advice → regulatory enforcement.",
        "Inconsistent sanitization across endpoints.",
        "Good intent; legal review required.",
        "Legal escrow $50k–$200k.",
        "Apply guard on all public Oracle outputs; geo-fencing.",
        None,
    )


def _req_auth() -> RequirementAssessment:
    return RequirementAssessment(
        14,
        "Authentication & session security",
        STR_PARTIALLY_PASS,
        "PBKDF2-SHA256 sessions; no MFA/SSO in DD scope.",
        "auth_service.py; security_auth.py",
        "Account takeover high impact on crypto platform.",
        "Consumer MVP auth; not enterprise SSO.",
        "OK for SMB; insufficient for B2B exchange.",
        "Blocks enterprise upsell.",
        "MFA; OAuth2/OIDC; WAF rate limits.",
        None,
    )


def _req_architecture(dashboard_lines: int) -> RequirementAssessment:
    v15: Verdict = STR_PARTIALLY_PASS if dashboard_lines < 3000 else "FAIL"
    return RequirementAssessment(
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


def _req_observability(sentry_configured: bool) -> RequirementAssessment:
    return RequirementAssessment(
        16,
        "Observability",
        STR_PARTIALLY_PASS,
        f"Prometheus /metrics + DD endpoints; Sentry configured={sentry_configured}.",
        "observability.py; api/routers/observability.py",
        "Cannot diagnose prod incidents without tracing/logs.",
        "Blind spots in production failures.",
        "MVP observability only.",
        "Standard ops cost post-acquisition.",
        "Datadog/Grafana; OpenTelemetry; structured JSON logs.",
        {"sentry_configured": sentry_configured},
    )


def _req_cicd(ci_has_cov_gate: bool, ci_has_dd_verify: bool, ci_has_docker: bool) -> RequirementAssessment:
    if ci_has_cov_gate and ci_has_dd_verify and ci_has_docker:
        v17: Verdict = "PASS"
    elif ci_has_cov_gate and ci_has_dd_verify:
        v17 = STR_PARTIALLY_PASS
    else:
        v17 = "FAIL"
    return RequirementAssessment(
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


def _req_docs() -> RequirementAssessment:
    docs_ok = all((ROOT / p).exists() for p in ("docs/ARCHITECTURE.md", "docs/DATA_ROOM.md", "docs/RUNBOOK.md"))
    v18: Verdict = "PASS" if docs_ok else STR_PARTIALLY_PASS
    return RequirementAssessment(
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


def _req_gdpr(gdpr_module: bool) -> RequirementAssessment:
    v19: Verdict = "PASS" if gdpr_module else "FAIL"
    return RequirementAssessment(
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


def _req_ma(deal_verdict: str, prod_ok: bool) -> RequirementAssessment:
    if deal_verdict in {"consider_strategic_acquisition", "conditional_acquisition"}:
        v20: Verdict = STR_PARTIALLY_PASS
    elif deal_verdict == "pass_build_instead":
        v20 = "FAIL"
    else:
        v20 = STR_PARTIALLY_PASS if prod_ok else "FAIL"
    return RequirementAssessment(
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


async def _load_acquisition_and_moat() -> tuple[dict[str, Any], dict[str, Any]]:
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
    return acquisition, moat


def _read_ci_flags() -> tuple[bool, bool, bool]:
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    ci_text = ci_path.read_text(encoding="utf-8") if ci_path.exists() else ""
    return (
        "cov-fail-under=90" in ci_text,
        "due_diligence_verify.py" in ci_text,
        "docker build" in ci_text.lower(),
    )


def _scorecard(requirements: list[RequirementAssessment]) -> tuple[dict[str, int], str]:
    counts = dict.fromkeys(("PASS", "FAIL", STR_PARTIALLY_PASS, "NOT APPLICABLE"), 0)
    for r in requirements:
        counts[r.verdict] += 1
    overall = "pass" if counts["FAIL"] == 0 and counts[STR_PARTIALLY_PASS] <= 5 else "partial"
    if counts["FAIL"] >= 5:
        overall = "fail"
    return counts, overall

def _tech_sections(tech: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "checks": tech.get("checks") or {},
        "coverage": tech.get("coverage") or {},
        "uptime": tech.get("uptime") or {},
        "latency": tech.get("latency") or {},
    }


async def _production_probe(probe_production: bool) -> dict[str, Any]:
    if probe_production:
        return await _probe_production_oracle()
    return {}


def _pillar_stats(acquisition: dict[str, Any]) -> dict[str, Any]:
    pillars = acquisition.get("pillars") or {}
    if not isinstance(pillars, dict):
        pillars = {}
    community = pillars.get("community") or {}
    behavior = pillars.get("behavior") or {}
    models = pillars.get("models") or {}
    return {
        "paid": int((community.get("evidence") or {}).get("paid_subscribers") or 0),
        "behavior_events": int((behavior.get("evidence") or {}).get("total_events") or 0),
        "model_verdict": str(models.get("verdict") or "none"),
        "deal_verdict": str(acquisition.get("deal_verdict") or "unknown"),
    }


def _static_due_diligence_inputs() -> dict[str, Any]:
    prod_path = ROOT / "requirements-prod.txt"
    prod_req = prod_path.read_text(encoding="utf-8") if prod_path.exists() else ""
    ci_has_cov_gate, ci_has_dd_verify, ci_has_docker = _read_ci_flags()
    return {
        "has_cryptography": "cryptography" in prod_req,
        "ci_has_cov_gate": ci_has_cov_gate,
        "ci_has_dd_verify": ci_has_dd_verify,
        "ci_has_docker": ci_has_docker,
        "gdpr_module": (ROOT / "gdpr_service.py").exists(),
        "sentry_configured": bool(os.getenv("SENTRY_DSN", "").strip()),
        "dashboard_lines": _count_lines(ROOT / "dashboard.py"),
    }


async def _technical_report_inputs(probe_production: bool) -> dict[str, Any]:
    from due_diligence import due_diligence_report

    tech = due_diligence_report()
    sections = _tech_sections(tech)
    prod_oracle = await _production_probe(probe_production)
    acquisition, moat = await _load_acquisition_and_moat()
    return {
        "tech": tech,
        "prod_oracle": prod_oracle,
        "prod_ok": bool(prod_oracle.get("ok")),
        "moat": moat,
        "probes_total": int(sections["uptime"].get("probes_total") or 0),
        "coverage_pct": float(sections["coverage"].get("coverage_percent") or 0),
        **sections,
        **_pillar_stats(acquisition),
        **_static_due_diligence_inputs(),
    }


def _technical_requirements(data: dict[str, Any]) -> list[RequirementAssessment]:
    return [
        _req_uptime(data["probes_total"], data["checks"], data["uptime"]),
        _req_latency(data["checks"], data["latency"]),
        _req_coverage(data["checks"], data["coverage"], data["coverage_pct"]),
        _req_ha(data["checks"], data["prod_ok"]),
        _req_prod(data["prod_ok"], data["prod_oracle"]),
        _req_oracle_ingest(data["prod_ok"], data["prod_oracle"]),
        _req_moat(data["moat"]),
        _req_ml(data["model_verdict"]),
        _req_behavior(data["behavior_events"]),
        _req_paid(data["paid"]),
        _req_api_keys(),
        _req_secrets(data["has_cryptography"]),
        _req_regulatory(),
        _req_auth(),
        _req_architecture(data["dashboard_lines"]),
        _req_observability(data["sentry_configured"]),
        _req_cicd(data["ci_has_cov_gate"], data["ci_has_dd_verify"], data["ci_has_docker"]),
        _req_docs(),
        _req_gdpr(data["gdpr_module"]),
        _req_ma(data["deal_verdict"], data["prod_ok"]),
    ]


def _technical_report_payload(
    data: dict[str, Any],
    requirements: list[RequirementAssessment],
    counts: dict[str, int],
    overall: str,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_verdict": overall,
        "committee_statement": (
            "Salvageable engineering with honest documentation. "
            "Production Oracle must stay live; close FAIL gaps (ML, subscribers, GDPR proof) for LOI."
        ),
        "scorecard": counts,
        "requirements": [asdict(r) for r in requirements],
        "automated_checks": data["tech"],
        "production_probe": data["prod_oracle"],
    }


def _has_prod_cryptography() -> bool:
    req_path = ROOT / "requirements-prod.txt"
    prod_req = req_path.read_text(encoding="utf-8") if req_path.exists() else ""
    return "cryptography" in prod_req


def _static_readiness_flags() -> tuple[bool, bool, int]:
    return (
        (ROOT / "gdpr_service.py").exists(),
        bool(os.getenv("SENTRY_DSN", "").strip()),
        _count_lines(ROOT / "dashboard.py"),
    )


def _acquisition_metrics(acquisition: dict[str, Any]) -> tuple[int, int, str, str]:
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
    return paid, behavior_events, model_verdict, deal_verdict



async def build_technical_due_diligence_report(*, probe_production: bool = True) -> dict[str, Any]:
    data = await _technical_report_inputs(probe_production)
    requirements = _technical_requirements(data)
    counts, overall = _scorecard(requirements)
    return _technical_report_payload(data, requirements, counts, overall)


def run_sync_report(*, probe_production: bool = True) -> dict[str, Any]:
    import asyncio

    return asyncio.run(build_technical_due_diligence_report(probe_production=probe_production))
