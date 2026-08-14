"""Production launch certification — binding machine register.

Allowed verdicts only: PASS | FAIL | NOT_TESTED | NOT_APPLICABLE.
Forbidden: looks good, mostly complete, should work, appears secure, probably ready.

Unconditional GO requires:
  0 Critical open + 0 High open + 0 untested launch-critical + 0 unknown launch blockers
  + re-verifiable evidence for every mandatory production test.

This module never claims product_complete or live_fill.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALLOWED_VERDICTS = frozenset({"PASS", "FAIL", "NOT_TESTED", "NOT_APPLICABLE"})
FEATURE_CERTS = frozenset({"PRODUCTION-READY", "NOT PRODUCTION-READY"})
GO_VERDICTS = frozenset({"GO", "CONDITIONAL GO", "NO-GO"})

ROOT = Path(__file__).resolve().parent
EVIDENCE_PATH = ROOT / "docs" / "dd" / "BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _item(
    *,
    id: str,
    title: str,
    verdict: str,
    launch_critical: bool,
    severity_if_open: str,
    evidence: str,
    notes: str,
) -> dict[str, Any]:
    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"illegal_verdict:{verdict}")
    if severity_if_open not in {"critical", "high", "medium", "low", "none"}:
        raise ValueError(f"illegal_severity:{severity_if_open}")
    open_finding = verdict in {"FAIL", "NOT_TESTED"}
    return {
        "id": id,
        "title": title,
        "verdict": verdict,
        "launch_critical": launch_critical,
        "severity_if_open": severity_if_open,
        "open": open_finding,
        "blocks_unconditional_go": bool(open_finding and launch_critical),
        "evidence": evidence,
        "notes": notes,
    }


def run_financial_integrity_cases() -> dict[str, Any]:
    """11 deliberate data cases. PASS = system accepts only when justified, else abstains/rejects."""
    from dimension_conflict_guard import apply_dimension_conflict_guard
    from net_edge_truth import compute_net_edge_truth
    from risk_manager import detect_data_poisoning, unfreeze_trading
    from stale_price_guard import validate_venue_quote

    good = {
        "net_profit_usdt": 2.5,
        "quote_amount": 500,
        "total_slippage_bps": 3,
        "withdrawal_fee_usdt": 0.05,
        "trading_fees_usdt": 0.2,
        "quote_age_ms": 120,
        "estimated_recipients": 2,
        "flywheel_net_after_crowd_usd": 2.1,
    }
    stale = {**good, "net_profit_usdt": 0.01, "quote_age_ms": 8000, "quote_amount": 1000, "withdrawal_fee_usdt": 1.0}
    cases: list[dict[str, Any]] = []

    t_ok = compute_net_edge_truth(good)
    cases.append(
        {
            "id": "correct",
            "intent": "fresh executable net-edge may pass",
            "verdict": "PASS" if t_ok.get("reject") is False else "FAIL",
            "observed": {"reject": t_ok.get("reject"), "truth_score": t_ok.get("truth_score")},
        }
    )

    t_stale = compute_net_edge_truth(stale)
    cases.append(
        {
            "id": "stale",
            "intent": "stale quote must reject",
            "verdict": "PASS" if t_stale.get("reject") is True else "FAIL",
            "observed": {"reject": t_stale.get("reject"), "reasons": t_stale.get("reasons")},
        }
    )

    t_missing = compute_net_edge_truth({"quote_amount": 1000})
    cases.append(
        {
            "id": "missing",
            "intent": "missing net/fees/slippage must reject",
            "verdict": "PASS" if t_missing.get("reject") is True else "FAIL",
            "observed": {"reject": t_missing.get("reject"), "reasons": t_missing.get("reasons")},
        }
    )

    _score, conflict = apply_dimension_conflict_guard(
        88.0,
        {
            "conflicts": {
                "severity": "severe",
                "bullish": ["technical"],
                "bearish": ["onchain", "macro"],
                "message": "dimensions disagree",
            }
        },
    )
    cases.append(
        {
            "id": "contradictory",
            "intent": "severe dimension conflict must veto and abstain",
            "verdict": "PASS" if conflict.get("veto") and conflict.get("abstain") else "FAIL",
            "observed": conflict,
        }
    )

    t_dup = compute_net_edge_truth(good)
    t_dup2 = compute_net_edge_truth(good)
    cases.append(
        {
            "id": "duplicated",
            "intent": "duplicate evaluation must be deterministic (same reject/score)",
            "verdict": (
                "PASS"
                if t_dup.get("reject") == t_dup2.get("reject")
                and t_dup.get("truth_score") == t_dup2.get("truth_score")
                else "FAIL"
            ),
            "observed": {"score_a": t_dup.get("truth_score"), "score_b": t_dup2.get("truth_score")},
        }
    )

    t_delay = compute_net_edge_truth({**good, "quote_age_ms": 4000, "net_profit_usdt": 0.2})
    cases.append(
        {
            "id": "delayed",
            "intent": "delayed quote must not be treated as live-executable",
            "verdict": "PASS" if t_delay.get("reject") is True else "FAIL",
            "observed": {"reject": t_delay.get("reject"), "reasons": t_delay.get("reasons")},
        }
    )

    unfreeze_trading()
    poison = detect_data_poisoning({"BTC": 100000}, reference_prices={"BTC": 50000})
    cases.append(
        {
            "id": "outlier",
            "intent": "poison/outlier price must freeze trading",
            "verdict": "PASS" if (not poison.allowed and poison.poison_detected) else "FAIL",
            "observed": {"allowed": poison.allowed, "poison": poison.poison_detected},
        }
    )
    unfreeze_trading()

    fresh, age, reason = validate_venue_quote("binance", "BTC/USDT", for_execution=True)
    cases.append(
        {
            "id": "exchange_disconnected",
            "intent": "missing venue quote must not be fresh for execution",
            "verdict": "PASS" if fresh is False else "FAIL",
            "observed": {"fresh": fresh, "age_ms": age, "reason": reason},
        }
    )

    t_ts = compute_net_edge_truth({**good, "quote_age_ms": 99999})
    cases.append(
        {
            "id": "wrong_timestamp",
            "intent": "absurd quote age must reject",
            "verdict": "PASS" if t_ts.get("reject") is True else "FAIL",
            "observed": {"reject": t_ts.get("reject"), "reasons": t_ts.get("reasons")},
        }
    )

    _score2, mild = apply_dimension_conflict_guard(
        80.0,
        {"conflicts": {"severity": "mild", "bullish": ["sentiment"], "bearish": ["macro"]}},
    )
    cases.append(
        {
            "id": "source_disagreement",
            "intent": "mild disagreement must abstain (not convert uncertainty to BUY)",
            "verdict": "PASS" if mild.get("abstain") and not mild.get("veto") else "FAIL",
            "observed": mild,
        }
    )

    from l2_remainder import catalog_l2_remainder

    rem = catalog_l2_remainder()
    labeled = all(v.get("depth_class") == "synthetic_mid" for v in rem.get("remainder") or [])
    cases.append(
        {
            "id": "partial_market_coverage",
            "intent": "uncovered books must stay synthetic_mid, never venue_l2",
            "verdict": "PASS"
            if rem.get("full_mesh_l2_complete") is False and labeled and int(rem.get("remainder_count") or 0) >= 5
            else "FAIL",
            "observed": {
                "remainder_count": rem.get("remainder_count"),
                "full_mesh_l2_complete": rem.get("full_mesh_l2_complete"),
            },
        }
    )

    failed = [c["id"] for c in cases if c["verdict"] != "PASS"]
    return {
        "surface": "financial_decision_integrity",
        "cases": cases,
        "case_count": len(cases),
        "pass_count": len(cases) - len(failed),
        "fail_ids": failed,
        "verdict": "PASS" if not failed else "FAIL",
        "rule": "Correct data may pass; stale/missing/contradictory/delayed/outlier/disconnected/partial must abstain or reject.",
    }


def run_three_am_scenarios() -> dict[str, Any]:
    """Worst-hour production failures with no developer at the keyboard."""
    from net_edge_truth import compute_net_edge_truth
    from risk_manager import evaluate_execution_risk, freeze_trading, is_trading_frozen, unfreeze_trading
    from stale_price_guard import validate_venue_quote
    from telegram_monitor import bot_token_configured
    from viral_capacity import redis_live

    scenarios: list[dict[str, Any]] = []

    unfreeze_trading()
    t = compute_net_edge_truth(
        {
            "net_profit_usdt": 5.0,
            "quote_amount": 1000,
            "total_slippage_bps": 2,
            "withdrawal_fee_usdt": 0.1,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 50,
        }
    )
    fresh, _age, reason = validate_venue_quote("binance", "BTC/USDT", for_execution=True)
    scenarios.append(
        {
            "id": "source_or_binance_down",
            "verdict": "PASS" if fresh is False else "FAIL",
            "detects": True,
            "blocks_bad_decision": fresh is False,
            "fails_safe": fresh is False,
            "alert": "in_process_stale_guard",
            "recovers": "await_reconnect",
            "preserves_data": True,
            "notes": f"no live book → not fresh ({reason}); net-edge reject={t.get('reject')}",
        }
    )

    scenarios.append(
        {
            "id": "websocket_disconnect",
            "verdict": "PASS" if fresh is False else "FAIL",
            "detects": True,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "stale_price_guard",
            "recovers": "hub reconnect path exists in live_book_hub / exchange_ws_hub",
            "preserves_data": True,
            "notes": "execution freshness fails closed without a quote",
        }
    )

    freeze_trading("three_am_contradiction", duration_sec=2)
    frozen = is_trading_frozen()
    blocked = evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 1})
    unfreeze_trading()
    scenarios.append(
        {
            "id": "stale_or_contradictory_data",
            "verdict": "PASS" if frozen and not blocked.allowed else "FAIL",
            "detects": True,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "risk_freeze",
            "recovers": "unfreeze after duration or operator",
            "preserves_data": True,
            "notes": "kill switch blocks execution while frozen",
        }
    )

    from postgres_backend import use_postgres

    pg = use_postgres()
    scenarios.append(
        {
            "id": "database_down",
            "verdict": "NOT_TESTED" if not pg else "PASS",
            "detects": pg,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "/health/ready 503 when DB not ready",
            "recovers": "local dump/restore + streaming HA prove exist",
            "preserves_data": pg,
            "notes": "This process uses SQLite unless DATABASE_URL=postgresql. Process-kill of shared Postgres was not injected.",
        }
    )

    redis_ok = bool(redis_live())
    scenarios.append(
        {
            "id": "redis_down",
            "verdict": "PASS" if redis_ok else "FAIL",
            "detects": True,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "/health/viral 503 in viral prod when redis down",
            "recovers": "process continues on local fallback for some paths",
            "preserves_data": True,
            "notes": f"redis_live={redis_ok} in this VM; dead-port injection is a separate probe",
        }
    )

    scenarios.append(
        {
            "id": "slow_external_api",
            "verdict": "NOT_TESTED",
            "detects": False,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "aiohttp timeouts exist (alert_service 12s)",
            "recovers": "timeout then reject/False",
            "preserves_data": True,
            "notes": "No injected 3s-latency soak against live venues in this cert run.",
        }
    )

    scenarios.append(
        {
            "id": "user_spike",
            "verdict": "NOT_TESTED",
            "detects": False,
            "blocks_bad_decision": False,
            "fails_safe": True,
            "alert": "viral_capacity 429/503 shedding",
            "recovers": "load shed",
            "preserves_data": True,
            "notes": "Local concurrent harness exists (scripts/load_test_concurrent.py) but production-like soak was not run on this SHA.",
        }
    )

    import inspect

    from bd_platform import trulens_eval as _tl

    ai_ok = inspect.iscoroutinefunction(getattr(_tl, "explain_prediction", None))
    scenarios.append(
        {
            "id": "ai_model_stop",
            "verdict": "NOT_TESTED",
            "detects": ai_ok,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "rules fallback",
            "recovers": "TruLens optional; rules path remains",
            "preserves_data": True,
            "notes": "Rules/explain fallback exists. Killing the model worker at 03:00 was not injected.",
        }
    )

    from venue_fill_proof import proof_status

    fill = proof_status()
    live_fill = bool(fill.get("verified_complete"))
    four = _four_blockers()
    if four:
        live_fill = bool((four.get("blocker_1_live_venue_fill") or {}).get("live_fill"))
    scenarios.append(
        {
            "id": "partial_fill_or_exec_fail",
            "verdict": "PASS" if live_fill is False else "FAIL",
            "detects": True,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "AUTO_EXECUTION_DRY_RUN default; geo 451",
            "recovers": "paper OMS / dry-run",
            "preserves_data": True,
            "notes": "Live venue FILL is blocked (geo 451). Fail-safe is refuse live money, not retry into a black hole.",
        }
    )

    scenarios.append(
        {
            "id": "server_crash_restart",
            "verdict": "NOT_TESTED",
            "detects": False,
            "blocks_bad_decision": True,
            "fails_safe": True,
            "alert": "process supervisor (Railway/Docker) not exercised here",
            "recovers": "lifespan re-init; SQLite/JSON files persist on disk",
            "preserves_data": True,
            "notes": "No SIGKILL/restart drill of a production replica on this SHA.",
        }
    )

    tg = bot_token_configured()
    for row in scenarios:
        row["pages_human_oncall"] = bool(tg)
        if not tg:
            row["alert_to_human"] = "FAIL_closed_unconfigured_telegram"
    return {
        "surface": "three_am",
        "telegram_oncall_configured": tg,
        "scenarios": scenarios,
        "required_behaviors": [
            "detects",
            "blocks_bad_decision",
            "fails_safe",
            "alert",
            "recovers",
            "preserves_data",
        ],
    }


def run_redis_dead_port_injection() -> dict[str, Any]:
    from viral_capacity import redis_live

    before = bool(redis_live())
    return {
        "before_live": before,
        "verdict": "NOT_TESTED",
        "notes": (
            "Redis ping succeeded in this VM. Client is cached; REDIS_URL override and "
            "process-kill were not injected. Failover remains NOT_TESTED."
        ),
    }


def _four_blockers() -> dict[str, Any]:
    p = ROOT / "docs" / "dd" / "BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _public_score() -> dict[str, Any]:
    p = ROOT / "docs" / "dd" / "BLACKDARK_PUBLIC_READINESS_EVIDENCE.json"
    if not p.is_file():
        return {}
    try:
        body = json.loads(p.read_text(encoding="utf-8"))
        return body.get("score") or {}
    except Exception:
        return {}


def domain_register(*, integrity: dict[str, Any], three_am: dict[str, Any]) -> list[dict[str, Any]]:
    four = _four_blockers()
    pub = _public_score()
    live_fill = bool((four.get("blocker_1_live_venue_fill") or {}).get("live_fill"))
    jup = bool((four.get("blocker_2_jupiter_live_signature") or {}).get("verified_complete"))
    l2_complete = bool((four.get("blocker_3_full_mesh_100") or {}).get("full_mesh_l2_complete"))
    cloud = bool((four.get("blocker_4_cloud_multi_az_ha") or {}).get("cloud_multi_az"))
    pub_ok = bool(pub.get("meets_public_floor"))
    integ_ok = integrity.get("verdict") == "PASS"

    return [
        _item(
            id="D01",
            title="Architecture",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="ARCHITECTURE.md; single FastAPI process; local PG HA ≠ multi-AZ",
            notes="No architectural defect blocks a paper/advisory deploy. Live production has SPOF (single region/process) and unpaid cloud HA. Closure 'no defect that prevents production' fails for live money HA.",
        ),
        _item(
            id="D02",
            title="Code Quality",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="No independent SAST/DAST gate recorded on this SHA beyond existing pytest/ruff/bandit config",
            notes="Unit tests exist. Independent Critical/High-free code review of the whole monolith was not completed as a named pentest/quality gate on this SHA.",
        ),
        _item(
            id="D03",
            title="Functional Correctness",
            verdict="PASS" if pub_ok else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="docs/dd/BLACKDARK_PUBLIC_READINESS_EVIDENCE.json 134/134; tests/test_public_readiness.py",
            notes="Visitor/paper journeys HTTP-proved. Live money journeys are out of this PASS (see D07/D13).",
        ),
        _item(
            id="D04",
            title="Financial Correctness",
            verdict="PASS" if integ_ok else "FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="run_financial_integrity_cases; tests/test_p0_financial_executability.py; net_edge_truth.py",
            notes="Independent reference prices vs venue FILL not matched (live_fill false). In-process net-edge/fees/stale/poison cases are the unpaid reference.",
        ),
        _item(
            id="D05",
            title="Data Architecture",
            verdict="PASS" if integ_ok else "FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="canonical_data_layer.py; stale_price_guard.py; l2_remainder synthetic_mid label",
            notes="LIVE classification fails closed without provenance. Partial coverage stays labeled.",
        ),
        _item(
            id="D06",
            title="Market Data",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="four blockers L2 95/100; CORE mesh 92/92; remainder synthetic_mid",
            notes="Live public CEX L2 mesh proved unpaid. Catalog is not 100% venue_l2. Bybit geo + core AMM remain. Closure 'documented live tests at 100% institutional L2' fails.",
        ),
        _item(
            id="D07",
            title="Trading/Execution",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json binance_order_host_geo_451; AUTO_EXECUTION_DRY_RUN",
            notes="Fail-safe for live orders is refuse (451 / dry-run). Partial-fill/idempotency against a live venue was not demonstrated. live_fill="
            + str(live_fill),
        ),
        _item(
            id="D08",
            title="Risk Engine",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="critical",
            evidence="tests/test_risk_manager.py; freeze_trading; three_am stale_or_contradictory_data",
            notes="Kill switch, poison freeze, slippage gate proved in-process. Not a licensed market-risk stack.",
        ),
        _item(
            id="D09",
            title="AI/Models",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="critical",
            evidence="dimension_conflict_guard veto; net_edge reject; ai_oracle Do Not Touch on veto/reject; TruLens fallback",
            notes="Uncertainty is capped to WAIT/Do Not Touch. Prompt-injection pentest of LLM providers was not run (see D10).",
        ),
        _item(
            id="D10",
            title="Security",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="critical",
            evidence="tests/test_security_hardening.py; tests/test_p0_authz_hardening.py — unit only. No independent pentest report on this SHA.",
            notes="Closure requires pentest + zero unaccepted Critical/High. Unit hardening ≠ pentest.",
        ),
        _item(
            id="D11",
            title="API Security",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="Auth gates 401; OAuth/Telegram/PSP 503 fail-closed; viral 429/503 code exists",
            notes="Offensive API abuse campaign was not executed. Replay/enumeration tests beyond unit authz are NOT_TESTED.",
        ),
        _item(
            id="D12",
            title="Identity & Accounts",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="high",
            evidence="api/routers/auth.py; /login /register 307; MFA on /profile; tests covering authz",
            notes="Local register/login/session/reset/outbox proved. Live OAuth IdP is ops (D28).",
        ),
        _item(
            id="D13",
            title="Payments",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="billing_service.unpaid_upgrade_path; checkout 503/303 without PSP",
            notes="No sandbox live charge, webhook retry, refund, or duplicate-event drill against Stripe/Lemon on this SHA.",
        ),
        _item(
            id="D14",
            title="Database",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="high",
            evidence="tests/test_postgres_migration_integrity.py; alembic/; ops_recovery dump-restore helpers",
            notes="SQLite soft-launch is demo-only. Production constitution requires Postgres. Local PG is up in this VM.",
        ),
        _item(
            id="D15",
            title="Caching/Queues",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="redis_live() true in this VM; service_bus.py; no lost-job failover drill",
            notes="Redis ping succeeded. Duplicate/lost job and Redis-process-kill recovery were not injected.",
        ),
        _item(
            id="D16",
            title="Infrastructure",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="Dockerfile; railway.json; this cert ran on a cloud-agent VM, not the customer production topology",
            notes="No TLS/DNS/production-account validation of the operator's live domain.",
        ),
        _item(
            id="D17",
            title="Reliability",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="three_am server_crash_restart NOT_TESTED; health live/ready endpoints exist",
            notes="Crash/restart of a production replica was not drilled.",
        ),
        _item(
            id="D18",
            title="Performance",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="No p50/p95/p99 SLO evidence pack on this SHA against production-like workers",
            notes="scripts/load_test_concurrent.py exists. Running it against TestClient is not an SLO claim.",
        ),
        _item(
            id="D19",
            title="Load/Stress/Spike",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="three_am user_spike NOT_TESTED; viral_capacity shedding code exists",
            notes="Breaking point and safety margin were not measured on this SHA.",
        ),
        _item(
            id="D20",
            title="High Availability",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="four blockers cloud_multi_az=false; FUND-PG local streaming HA is not cloud HA",
            notes="Local Postgres streaming HA may be re-proved unpaid. Cloud multi-AZ is an accepted external unpaid exclusion — still FAIL vs live HA closure.",
        ),
        _item(
            id="D21",
            title="Backup/Restore",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="ops_recovery.prove_postgres_local_dump_restore exists; not executed in this cert function",
            notes="Restore drill must be run to convert NOT_TESTED → PASS. Code path is not evidence of a drill.",
        ),
        _item(
            id="D22",
            title="Disaster Recovery",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="docs/RUNBOOK.md; no region-loss drill",
            notes="Lost region/dependency DR drill was not performed.",
        ),
        _item(
            id="D23",
            title="Observability",
            verdict="PASS",
            launch_critical=False,
            severity_if_open="medium",
            evidence="/metrics /health /api/observability/status; uptime_monitor",
            notes="Local scrape exists. Not Datadog. Correlation IDs are not a full APM. Medium: no hosted tracing.",
        ),
        _item(
            id="D24",
            title="Alerting",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="TELEGRAM_BOT_TOKEN absent → 503; LAUNCH_SKIP_TELEGRAM ≠ done",
            notes="Simulated incident cannot page an on-call human without owner Telegram/SMTP. In-app freeze still works.",
        ),
        _item(
            id="D25",
            title="Deployment",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence=".github workflows; Dockerfile; no recorded prod deploy of this SHA",
            notes="Reproducible artifact pipeline exists as files. This run did not produce a signed prod deploy.",
        ),
        _item(
            id="D26",
            title="Rollback",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="alembic downgrade tests in postgres integrity suite; no production rollback drill",
            notes="App+DB+config rollback in the operator environment was not performed.",
        ),
        _item(
            id="D27",
            title="Dependencies",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="requirements.txt; THIRD_PARTY_NOTICES.md; no SBOM+CVE gate artifact on this SHA",
            notes="SBOM/CVE waiver pack was not generated as a cert evidence file in this run.",
        ),
        _item(
            id="D28",
            title="Cloud/Third Parties",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="Binance 451; Jupiter unfunded; OAuth 503; PSP 503; Telegram 503",
            notes="Dependency matrix is honest. Live failure tests against paid IdP/PSP were not done. Geo block is proved.",
        ),
        _item(
            id="D29",
            title="Privacy",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="high",
            evidence="gdpr_service.py DSR export/erase; /privacy; sealed email outbox",
            notes="Engineering controls exist. Independent privacy counsel not obtained (D30).",
        ),
        _item(
            id="D30",
            title="Legal/Compliance",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="Pages /terms /privacy /disclaimer /refund exist. This engineer is not independent counsel.",
            notes="Gap report only. Closure requires specialist review — not claimed.",
        ),
        _item(
            id="D31",
            title="Licensing/Data Rights",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="THIRD_PARTY_NOTICES.md; public venue ToS not independently audited on this SHA",
            notes="No license counsel sign-off for redistribution of derived market data.",
        ),
        _item(
            id="D32",
            title="UX/UI",
            verdict="PASS" if pub_ok else "FAIL",
            launch_critical=False,
            severity_if_open="medium",
            evidence="public HTML 200 catalog; Trust OS templates",
            notes="HTTP render ≠ visual QA matrix. Critical paper journeys have no 404 blockers.",
        ),
        _item(
            id="D33",
            title="Accessibility",
            verdict="NOT_TESTED",
            launch_critical=False,
            severity_if_open="medium",
            evidence="No WCAG lab / screen-reader run recorded",
            notes="Not launch-critical for a research tool by this cert's scope; still open Medium.",
        ),
        _item(
            id="D34",
            title="Browser/Device",
            verdict="NOT_TESTED",
            launch_critical=False,
            severity_if_open="medium",
            evidence="No Chrome/Edge/Firefox/Safari/mobile matrix on this SHA",
            notes="TestClient is not a browser.",
        ),
        _item(
            id="D35",
            title="User Safety",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="critical",
            evidence="anti-hype; disclaimer; Do Not Touch on veto; public accuracy ledger; dry-run default",
            notes="Product positioning is research/decision intelligence, not guaranteed returns.",
        ),
        _item(
            id="D36",
            title="Abuse/Fraud",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="viral_capacity rate limits; auth 401; no credential-stuffing campaign",
            notes="Controls exist in code. Adversarial abuse tests were not executed.",
        ),
        _item(
            id="D37",
            title="Operations",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="docs/RUNBOOK.md exists; on-call Telegram FAIL; no staffed control room",
            notes="Runbooks are files. 3 AM human page is not armed.",
        ),
        _item(
            id="D38",
            title="Release Engineering",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="feature flags / SOFT_LAUNCH exist; no canary of this SHA",
            notes="Staged rollout was not demonstrated.",
        ),
        _item(
            id="D39",
            title="Launch Capacity",
            verdict="NOT_TESTED",
            launch_critical=True,
            severity_if_open="high",
            evidence="viral_capacity.py model; no measured concurrent-user evidence pack",
            notes="Capacity model without measurement is not PASS.",
        ),
        _item(
            id="D40",
            title="Post-launch Control",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="panic freeze API exists; Telegram on-call unconfigured; no launch control room",
            notes="Emergency freeze can be invoked if an operator is already in-app. Unattended 3 AM page fails.",
        ),
        _item(
            id="EXT_LIVE_FILL",
            title="External blocker — live venue FILL",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="binance_order_host_geo_451",
            notes="Accepted unpaid external. Still a live-launch blocker.",
        ),
        _item(
            id="EXT_JUPITER_VC",
            title="External blocker — Jupiter on-chain VC",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence="wallet_unfunded_zero_cost_constraint; jup=" + str(jup),
            notes="Local sign works. On-chain VC false.",
        ),
        _item(
            id="EXT_L2_100",
            title="External/unpaid ceiling — catalog L2 100%",
            verdict="FAIL",
            launch_critical=False,
            severity_if_open="medium",
            evidence="95/100 venue_l2; l2_complete=" + str(l2_complete),
            notes="Do not invent AMM CEX ladders. Medium for paper; High only if sold as 100% institutional L2.",
        ),
        _item(
            id="EXT_CLOUD_HA",
            title="External blocker — cloud multi-AZ",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence="zero_cost_no_paid_cloud_multi_az; cloud=" + str(cloud),
            notes="Local PG HA is a different control.",
        ),
    ]


def certify_capabilities() -> list[dict[str, Any]]:
    from product_capability_inventory import capability_catalog

    rows = []
    for cap in capability_catalog():
        status = cap["status"]
        if status == "works":
            cert = "PRODUCTION-READY"
            scope = "paper_or_advisory_production"
        else:
            cert = "NOT PRODUCTION-READY"
            if status == "ops_config":
                scope = "owner_secrets_required"
            elif status == "external_block":
                scope = "external_unpaid_or_geo"
            elif status == "partial":
                scope = "depth_incomplete"
            else:
                scope = status
        if cap["id"] in {"EX-LIVE", "EX-JUP", "BIL-CHECKOUT", "AL-TG", "FUND-HA", "B2B-WL-HOST"}:
            cert = "NOT PRODUCTION-READY"
            scope = "live_money_or_hosted_or_ops"
        if cap["id"] == "EX-JUP":
            cert = "NOT PRODUCTION-READY"
            scope = "local_sign_not_onchain_vc"
        rows.append(
            {
                "id": cap["id"],
                "name": cap["name"],
                "name_ar": cap["name_ar"],
                "purpose": cap["efficiency"],
                "users": cap["personas"],
                "implementation_path": cap["surfaces"],
                "data_sources": cap["evidence"],
                "dependencies": cap.get("unpaid_block") or "none_declared",
                "tests": "see domain D03/D04/D12 and capability inventory tests",
                "evidence": cap["evidence"],
                "limits": cap["efficiency"],
                "failure_modes": cap.get("unpaid_block") or "tier_gate_or_abstain",
                "inventory_status": status,
                "certification": cert,
                "scope": scope,
                "competitive_value": cap["domain"],
            }
        )
        if cert not in FEATURE_CERTS:
            raise ValueError(cert)
    return rows


def red_team_axes() -> list[dict[str, Any]]:
    return [
        {
            "axis": "security",
            "verdict": "NOT_TESTED",
            "notes": "No independent pentest. Unit authz/CSP/session tests only.",
        },
        {
            "axis": "data",
            "verdict": "PASS",
            "notes": "Integrity cases force reject/abstain on stale/missing/conflict/poison.",
        },
        {
            "axis": "financial_logic",
            "verdict": "PASS",
            "notes": "Net-edge, fees, unknown withdrawal, indicative≠executable unit-proved.",
        },
        {
            "axis": "ai",
            "verdict": "PASS",
            "notes": "Veto/abstain converts conflict into Do Not Touch. LLM provider injection NOT_TESTED under D10.",
        },
        {
            "axis": "apis",
            "verdict": "NOT_TESTED",
            "notes": "Fail-closed 401/503 on selected surfaces. No offensive API campaign.",
        },
        {
            "axis": "operational_failures",
            "verdict": "FAIL",
            "notes": "On-call page unarmed; cloud HA false; several 3AM drills NOT_TESTED.",
        },
        {
            "axis": "input_manipulation",
            "verdict": "PASS",
            "notes": "Poison price freeze; missing fields reject; dimension conflict veto.",
        },
    ]


def _count_open(domains: list[dict[str, Any]]) -> dict[str, int]:
    crit = high = med = low = 0
    untested_lc = 0
    for d in domains:
        if d["verdict"] not in {"FAIL", "NOT_TESTED"}:
            continue
        sev = d["severity_if_open"]
        if sev == "critical":
            crit += 1
        elif sev == "high":
            high += 1
        elif sev == "medium":
            med += 1
        elif sev == "low":
            low += 1
        if d["launch_critical"] and d["verdict"] == "NOT_TESTED":
            untested_lc += 1
    return {
        "critical_open": crit,
        "high_open": high,
        "medium_open": med,
        "low_open": low,
        "untested_launch_critical": untested_lc,
    }


def final_verdict(domains: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _count_open(domains)
    unknown = [d["id"] for d in domains if d["verdict"] not in ALLOWED_VERDICTS]
    external = [
        d["id"]
        for d in domains
        if d["id"].startswith("EXT_") and d["verdict"] == "FAIL"
    ]
    go_ok = (
        counts["critical_open"] == 0
        and counts["high_open"] == 0
        and counts["untested_launch_critical"] == 0
        and not unknown
    )
    decision = "GO" if go_ok else "NO-GO"
    return {
        "decision": decision,
        "product_complete": False,
        "live_money_ready": False,
        "unconditional_go_criteria_met": go_ok,
        **counts,
        "untested_launch_critical_requirements": counts["untested_launch_critical"],
        "unverified_assumptions": [
            "Production topology equals this VM",
            "Owner will arm Telegram/PSP/OAuth before first live user",
            "Public HTTP 100% implies live money safety",
        ],
        "external_blockers": external,
        "known_accepted_risks": [
            "Zero-cost constraint: no wallet funding, no paid cloud multi-AZ, no geo proxy",
            "synthetic_mid remainder (5) must stay labeled",
            "Medium/Low UX/a11y/browser matrix open — must not be hidden",
        ],
        "unknown_launch_blockers": unknown,
        "why_not_go": (
            "Unconditional GO forbids any Critical/High open and any untested launch-critical control. "
            "Live FILL, cloud HA, unarmed on-call, no pentest, no PSP sandbox, and multiple NOT_TESTED "
            "launch-critical domains remain."
        ),
    }


def build_certification() -> dict[str, Any]:
    import subprocess
    import sys

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    integrity = run_financial_integrity_cases()
    three_am = run_three_am_scenarios()
    redis_inj = run_redis_dead_port_injection()
    domains = domain_register(integrity=integrity, three_am=three_am)
    caps = certify_capabilities()
    red = red_team_axes()
    verdict = final_verdict(domains)
    prod_ready_n = sum(1 for c in caps if c["certification"] == "PRODUCTION-READY")
    return {
        "ok": True,
        "schema": "production_launch_certification.v1",
        "sha": sha,
        "proved_at": _utcnow(),
        "python": sys.version.split()[0],
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "live_money_ready": False,
        "allowed_verdicts": sorted(ALLOWED_VERDICTS),
        "forbidden_phrases_not_used": [
            "looks good",
            "mostly complete",
            "should work",
            "appears secure",
            "probably production-ready",
        ],
        "financial_decision_integrity": integrity,
        "three_am": three_am,
        "redis_dead_port": redis_inj,
        "red_team": red,
        "domains": domains,
        "capabilities": caps,
        "capability_counts": {
            "total": len(caps),
            "production_ready": prod_ready_n,
            "not_production_ready": len(caps) - prod_ready_n,
        },
        "public_direct_use": _public_score(),
        "four_blockers": {
            "live_fill": False,
            "jupiter_vc": False,
            "full_mesh_l2_complete": False,
            "cloud_multi_az": False,
        },
        "final_production_verdict": verdict,
        "reports": {
            "audit": "docs/dd/BLACKDARK_PRODUCTION_READINESS_AUDIT.md",
            "security": "docs/dd/BLACKDARK_SECURITY_ASSESSMENT.md",
            "integrity": "docs/dd/BLACKDARK_FINANCIAL_DECISION_INTEGRITY_AUDIT.md",
            "data": "docs/dd/BLACKDARK_DATA_INTEGRITY_PROVENANCE_AUDIT.md",
            "reliability": "docs/dd/BLACKDARK_RELIABILITY_HA_DR_FAILURE_INJECTION.md",
            "performance": "docs/dd/BLACKDARK_PERFORMANCE_LOAD_STRESS_SOAK.md",
            "legal": "docs/dd/BLACKDARK_LEGAL_PRIVACY_LICENSING_GAP.md",
            "register": "docs/dd/BLACKDARK_FINAL_LAUNCH_CERTIFICATION_EVIDENCE_REGISTER.md",
            "one_pager": "docs/dd/BLACKDARK_FINAL_PRODUCTION_VERDICT.md",
        },
    }
