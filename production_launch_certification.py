"""Production launch certification — binding machine register.

Allowed verdicts only: PASS | FAIL | NOT_TESTED | NOT_APPLICABLE.
Feature tracks only: PUBLIC-DEMO-READY | LIVE-PRODUCTION-READY | LIVE-MONEY-READY | NOT-READY.
Forbidden: looks good, mostly complete, should work, appears secure, probably ready,
PRODUCTION-READY as a paper euphemism, «Production Ready ورقيًا».

Unconditional GO requires ALL of:
  0 Critical open + 0 High open + 0 untested launch-critical + 0 unknown launch blockers
  + 0 unverified launch-critical assumptions
  + every mandatory test PASS with re-verifiable evidence
  + LIVE-PRODUCTION-READY and LIVE-MONEY-READY both true
  + live-money paths proved
  + legal/external closed or documented per launch scope

This module never claims product_complete or live_fill.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALLOWED_VERDICTS = frozenset({"PASS", "FAIL", "NOT_TESTED", "NOT_APPLICABLE"})
FEATURE_TRACKS = frozenset(
    {"PUBLIC-DEMO-READY", "LIVE-PRODUCTION-READY", "LIVE-MONEY-READY", "NOT-READY"}
)
GO_VERDICTS = frozenset({"GO", "CONDITIONAL GO", "NO-GO"})
MONEY_IDS = frozenset({"EX-LIVE", "EX-JUP", "EX-AUTO", "BIL-CHECKOUT", "FUND-HA", "B2B-WL-HOST"})

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

    from telegram_monitor import oncall_live_proved

    tg = oncall_live_proved()
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


def _dv(drills: dict[str, Any], did: str) -> str:
    row = (drills.get("by_id") or {}).get(did) or {}
    v = str(row.get("verdict") or "FAIL")
    return v if v in ALLOWED_VERDICTS else "FAIL"


def _all_pass(drills: dict[str, Any], *ids: str) -> bool:
    return all(_dv(drills, i) == "PASS" for i in ids)


def _ev(drills: dict[str, Any], *ids: str) -> str:
    parts: list[str] = []
    for i in ids:
        row = (drills.get("by_id") or {}).get(i) or {}
        parts.append(f"{i}={row.get('verdict', 'FAIL')}")
    return "; ".join(parts)


def overlay_three_am_with_drills(three_am: dict[str, Any], drills: dict[str, Any]) -> dict[str, Any]:
    """Replace 3 AM NOT_TESTED with drill PASS/FAIL. Never leave a 3 AM scenario untested."""
    mapping = {
        "database_down": "postgres_dump_restore",
        "redis_down": "redis_dead_port",
        "slow_external_api": "slow_api_timeout",
        "user_spike": "rate_limit_abuse",
        "server_crash_restart": "process_restart",
        "ai_model_stop": "ai_fallback",
    }
    for row in three_am.get("scenarios") or []:
        did = mapping.get(str(row.get("id") or ""))
        if not did:
            if row.get("verdict") == "NOT_TESTED":
                row["verdict"] = "FAIL"
                row["notes"] = (row.get("notes") or "") + " | no mapped drill → FAIL (evaluated missing)"
            continue
        v = _dv(drills, did)
        row["verdict"] = v
        row["drill_id"] = did
        row["drill_evidence"] = ((drills.get("by_id") or {}).get(did) or {}).get("evidence")
        if v == "PASS":
            row["detects"] = True
            row["recovers"] = did
        if v == "FAIL":
            row["notes"] = (row.get("notes") or "") + f" | drill {did}=FAIL"
    live = (drills.get("by_id") or {}).get("telegram_oncall_live") or {}
    tg = live.get("verdict") == "PASS"
    three_am["telegram_oncall_configured"] = tg
    for row in three_am.get("scenarios") or []:
        row["pages_human_oncall"] = tg
        if tg:
            row["alert_to_human"] = f"telegram_oncall_live message_id={live.get('message_id')}"
        else:
            row["alert_to_human"] = "FAIL_closed_unconfigured_telegram"
    return three_am


def domain_register(
    *,
    integrity: dict[str, Any],
    three_am: dict[str, Any],
    drills: dict[str, Any],
) -> list[dict[str, Any]]:
    four = _four_blockers()
    pub = _public_score()
    live_fill = bool((four.get("blocker_1_live_venue_fill") or {}).get("live_fill"))
    jup = bool((four.get("blocker_2_jupiter_live_signature") or {}).get("verified_complete"))
    l2_complete = bool((four.get("blocker_3_full_mesh_100") or {}).get("full_mesh_l2_complete"))
    cloud = bool((four.get("blocker_4_cloud_multi_az_ha") or {}).get("cloud_multi_az"))
    pub_ok = bool(pub.get("meets_public_floor"))
    integ_ok = integrity.get("verdict") == "PASS"
    tg_oncall = _dv(drills, "telegram_oncall_live") == "PASS"
    stripe_ok = _dv(drills, "stripe_sandbox") == "PASS"
    oauth_ok = _dv(drills, "oauth_google_idp") == "PASS"

    return [
        _item(
            id="D01",
            title="Architecture",
            verdict="PASS"
            if _all_pass(drills, "ha_architecture", "compose_yaml_merge", "postgres_streaming_ha", "http_load_local")
            else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "ha_architecture", "compose_yaml_merge", "postgres_streaming_ha", "http_load_local"),
            notes="HA design (Railway replicas≥2, compose HA overlay) + local PG streaming + 2-worker HTTP. Cloud multi-AZ remains D20/EXT_CLOUD_HA.",
        ),
        _item(
            id="D02",
            title="Code Quality",
            verdict="PASS" if _all_pass(drills, "bandit") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "bandit"),
            notes="In-repo Bandit HIGH/CRITICAL=0 is the unpaid SAST gate. Independent pentest is D10, not this domain.",
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
            verdict="PASS" if _all_pass(drills, "executable_l2_scope") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "executable_l2_scope") + "; CORE mesh 92/92; remainder synthetic_mid",
            notes="Live adoption rejects synthetic_mid. CORE public CEX L2 is complete. Catalog 100% venue_l2 remains EXT_L2_100 (medium) — AMM ladders were not invented.",
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
            verdict="PASS" if _all_pass(drills, "panic_freeze") else "FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence=_ev(drills, "panic_freeze") + "; tests/test_risk_manager.py",
            notes="Kill switch, poison freeze, slippage gate proved in-process. Not a licensed market-risk stack.",
        ),
        _item(
            id="D09",
            title="AI/Models",
            verdict="PASS" if _all_pass(drills, "ai_fallback") else "FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence=_ev(drills, "ai_fallback") + "; dimension_conflict_guard veto",
            notes="Uncertainty is capped to WAIT/Do Not Touch. Prompt-injection pentest of LLM providers is D10.",
        ),
        _item(
            id="D10",
            title="Security",
            verdict="PASS" if _all_pass(drills, "independent_pentest_artifact") else "FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence=_ev(drills, "independent_pentest_artifact", "adversarial_suite", "bandit"),
            notes="In-repo adversarial suite is D11. Independent firm pentest artifact missing = FAIL vs Unconditional GO. Do not treat unit hardening as pentest.",
        ),
        _item(
            id="D11",
            title="API Security",
            verdict="PASS" if _all_pass(drills, "adversarial_suite") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "adversarial_suite"),
            notes="In-repo OWASP-style pack executed. Not a substitute for D10 firm pentest.",
        ),
        _item(
            id="D12",
            title="Identity & Accounts",
            verdict="PASS",
            launch_critical=True,
            severity_if_open="high",
            evidence="api/routers/auth.py; /login /register 307; MFA on /profile; tests covering authz"
            + ("; oauth_google_idp" if oauth_ok else ""),
            notes=(
                "Local register/login/session/reset/outbox proved. "
                + (
                    "Google OAuth live IdP slice PASS (authorize+token client accepted; human callback not claimed)."
                    if oauth_ok
                    else "Live OAuth IdP is ops (D28)."
                )
            ),
        ),
        _item(
            id="D13",
            title="Payments",
            verdict="PASS" if _all_pass(drills, "stripe_sandbox") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "stripe_sandbox") + "; billing_service.unpaid_upgrade_path",
            notes="Stripe TEST cycle exercised. PASS only on sk_test_ Account.retrieve + STRIPE_PRICE_PRO recurring + BLACKDARK checkout session + TEST subscription active/trialing then cancel. Invalid/rejected keys remain FAIL. sk_live_ and hosted live-money charges stay out of this unpaid cert.",
        ),
        _item(
            id="D14",
            title="Database",
            verdict="PASS" if _all_pass(drills, "postgres_dump_restore", "alembic_rollback_semantics") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "postgres_dump_restore", "alembic_rollback_semantics", "sqlite_restore"),
            notes="SQLite soft-launch is demo-only. Production constitution requires Postgres. Local dump/restore is not cloud HA.",
        ),
        _item(
            id="D15",
            title="Caching/Queues",
            verdict="PASS" if _all_pass(drills, "redis_dead_port") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "redis_dead_port"),
            notes="Dead-port injection against cached Redis client. Duplicate/lost job across a Redis cluster failover remains unpaid.",
        ),
        _item(
            id="D16",
            title="Infrastructure",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "infra_files", "compose_config", "compose_yaml_merge"),
            notes="IaC files + YAML merge drilled. docker compose config may FAIL without docker. Operator production DNS/TLS/account of the live domain was not validated → FAIL vs live production topology.",
        ),
        _item(
            id="D17",
            title="Reliability",
            verdict="PASS" if _all_pass(drills, "process_restart") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "process_restart"),
            notes="ASGI TestClient start/stop/start /health/live. Not a SIGKILL of a Railway/Docker replica.",
        ),
        _item(
            id="D18",
            title="Performance",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "asgi_latency", "http_load_local"),
            notes="Local ASGI + 2-worker uvicorn HTTP packs executed. Neither is a production multi-AZ SLO. Evaluated missing production-like topology → FAIL, not PASS.",
        ),
        _item(
            id="D19",
            title="Load/Stress/Spike",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "rate_limit_abuse", "asgi_latency", "http_load_local"),
            notes="Shedding 429 and local 2-worker HTTP pack executed. Breaking point and safety margin on production-like workers were not measured → FAIL.",
        ),
        _item(
            id="D20",
            title="High Availability",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="critical",
            evidence=_ev(drills, "postgres_streaming_ha") + "; cloud_multi_az=" + str(cloud),
            notes="Local Postgres streaming HA may PASS as a different control. Cloud multi-AZ is unpaid external — FAIL vs live HA closure.",
        ),
        _item(
            id="D21",
            title="Backup/Restore",
            verdict="PASS" if _all_pass(drills, "sqlite_restore", "postgres_dump_restore") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "sqlite_restore", "postgres_dump_restore"),
            notes="Local dump/restore executed. Region-loss restore is D22.",
        ),
        _item(
            id="D22",
            title="Disaster Recovery",
            verdict="PASS" if _all_pass(drills, "postgres_dump_restore") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "postgres_dump_restore", "chaos_dead_postgres", "postgres_streaming_ha"),
            notes="Local probe-DB DROP + pg_restore executed (dependency-loss DR). Multi-region/AZ loss remains D20/EXT_CLOUD_HA — not this PASS.",
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
            verdict="PASS" if tg_oncall else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "telegram_oncall_live"),
            notes=(
                "PASS only on live Bot API sendMessage with telegram ok + message_id. "
                "Token presence alone is not a page. LAUNCH_SKIP_TELEGRAM ≠ done."
            ),
        ),
        _item(
            id="D25",
            title="Deployment",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "infra_files") + "; .github workflows; Dockerfile",
            notes="Reproducible artifact files exist. This run did not produce a signed production deploy of this SHA → FAIL.",
        ),
        _item(
            id="D26",
            title="Rollback",
            verdict="PASS" if _all_pass(drills, "alembic_rollback_semantics") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "alembic_rollback_semantics"),
            notes="Alembic/Postgres integrity pytest executed. Operator-environment app+DB+config rollback of a live replica was not performed.",
        ),
        _item(
            id="D27",
            title="Dependencies",
            verdict="PASS" if _all_pass(drills, "sbom", "license_inventory", "pip_audit") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "sbom", "license_inventory", "pip_audit"),
            notes="SBOM + license inventory + pip-audit must all PASS. Missing tool or CVE finding is FAIL.",
        ),
        _item(
            id="D28",
            title="Cloud/Third Parties",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "telegram_oncall_live", "stripe_sandbox", "oauth_google_idp")
            + "; Binance 451; Jupiter unfunded",
            notes=(
                ("Telegram on-call live send PASS. " if tg_oncall else "Telegram on-call live send FAIL. ")
                + ("Stripe TEST PSP cycle PASS. " if stripe_ok else "Stripe TEST PSP cycle FAIL. ")
                + ("Google OAuth live IdP PASS. " if oauth_ok else "Google OAuth live IdP FAIL. ")
                + (
                    "D28 stays FAIL while Binance 451 and unfunded Jupiter remain. "
                    if oauth_ok
                    else "D28 stays FAIL while Binance 451, unfunded Jupiter, and live OAuth IdP remain. "
                )
                + "Telegram, Stripe TEST, and Google OAuth IdP slices are independent of those remaining vendors."
            ),
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
            verdict="PASS" if _all_pass(drills, "counsel_signoff") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "counsel_signoff"),
            notes="Pages /terms /privacy /disclaimer /refund exist. Engineer is not independent counsel. Missing counsel artifact = FAIL vs Unconditional GO.",
        ),
        _item(
            id="D31",
            title="Licensing/Data Rights",
            verdict="PASS" if _all_pass(drills, "license_inventory") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "license_inventory"),
            notes="Dependency license inventory generated. Independent venue ToS / derived-data counsel remains D30.",
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
            verdict="PASS" if _all_pass(drills, "chrome_public_pages") else "FAIL",
            launch_critical=False,
            severity_if_open="medium",
            evidence=_ev(drills, "chrome_public_pages"),
            notes="Chromium dump-dom lang/title smoke. Not a WCAG 2.2 AA lab or screen-reader run.",
        ),
        _item(
            id="D34",
            title="Browser/Device",
            verdict="PASS" if _all_pass(drills, "chrome_public_pages") else "FAIL",
            launch_critical=False,
            severity_if_open="medium",
            evidence=_ev(drills, "chrome_public_pages"),
            notes="Google Chrome headless only. Firefox/Safari/mobile matrix was not run.",
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
            verdict="PASS" if _all_pass(drills, "rate_limit_abuse", "adversarial_suite") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "rate_limit_abuse", "adversarial_suite"),
            notes="Rate-limit 429 + unauth/SQLi/XSS/path-traversal pack executed. Credential-stuffing campaign against production was not run.",
        ),
        _item(
            id="D37",
            title="Operations",
            verdict="PASS" if tg_oncall else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "telegram_oncall_live") + "; docs/RUNBOOK.md",
            notes=(
                "On-call armed iff live Telegram page proved (message_id). "
                "No 24/7 staffed control room is claimed."
            ),
        ),
        _item(
            id="D38",
            title="Release Engineering",
            verdict="PASS" if _all_pass(drills, "feature_flag_soft_launch") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "feature_flag_soft_launch"),
            notes="SOFT_LAUNCH flag evaluation executed. Canary of this SHA on a production account was not demonstrated.",
        ),
        _item(
            id="D39",
            title="Launch Capacity",
            verdict="FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "asgi_latency", "rate_limit_abuse", "http_load_local") + "; viral_capacity.py model",
            notes="Local two-worker HTTP pack is not measured concurrent-user evidence on production-like workers → FAIL.",
        ),
        _item(
            id="D40",
            title="Post-launch Control",
            verdict="PASS" if tg_oncall and _all_pass(drills, "panic_freeze") else "FAIL",
            launch_critical=True,
            severity_if_open="high",
            evidence=_ev(drills, "panic_freeze", "telegram_oncall_live"),
            notes="Emergency freeze + live Telegram on-call page. Both required for unattended 3 AM control.",
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


def certify_capabilities(*, tracks: dict[str, Any]) -> list[dict[str, Any]]:
    from product_capability_inventory import capability_catalog

    live_money_track = bool(tracks.get("LIVE-MONEY-READY"))
    live_prod_track = bool(tracks.get("LIVE-PRODUCTION-READY"))
    rows = []
    for cap in capability_catalog():
        status = cap["status"]
        cid = cap["id"]
        if cid in MONEY_IDS and not live_money_track:
            cert = "NOT-READY"
            scope = "live_money_path_unproved"
        elif status == "works" and live_prod_track:
            cert = "LIVE-PRODUCTION-READY"
            scope = "live_production_track"
        elif status == "works":
            cert = "PUBLIC-DEMO-READY"
            scope = "public_demo_or_paper_advisory"
        else:
            cert = "NOT-READY"
            if status == "ops_config":
                scope = "owner_secrets_required"
            elif status == "external_block":
                scope = "external_unpaid_or_geo"
            elif status == "partial":
                scope = "depth_incomplete"
            else:
                scope = status
        if cid in MONEY_IDS and live_money_track:
            cert = "LIVE-MONEY-READY"
            scope = "live_money_paths_proved"
        rows.append(
            {
                "id": cid,
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
        if cert not in FEATURE_TRACKS:
            raise ValueError(cert)
    return rows


def red_team_axes(drills: dict[str, Any], integrity: dict[str, Any]) -> list[dict[str, Any]]:
    integ_ok = integrity.get("verdict") == "PASS"
    return [
        {
            "axis": "security",
            "verdict": "PASS" if _all_pass(drills, "independent_pentest_artifact") else "FAIL",
            "notes": "Independent pentest artifact required. In-repo adversarial pack is a different axis (apis).",
        },
        {
            "axis": "data",
            "verdict": "PASS" if integ_ok else "FAIL",
            "notes": "Integrity cases force reject/abstain on stale/missing/conflict/poison.",
        },
        {
            "axis": "financial_logic",
            "verdict": "PASS" if integ_ok else "FAIL",
            "notes": "Net-edge, fees, unknown withdrawal, indicative≠executable unit-proved.",
        },
        {
            "axis": "ai",
            "verdict": "PASS" if _all_pass(drills, "ai_fallback") else "FAIL",
            "notes": "Rules/explain fallback executed. LLM provider injection remains D10.",
        },
        {
            "axis": "apis",
            "verdict": "PASS" if _all_pass(drills, "adversarial_suite") else "FAIL",
            "notes": "In-repo unauth/SQLi/XSS/path-traversal pack. Not D10 firm pentest.",
        },
        {
            "axis": "operational_failures",
            "verdict": "FAIL",
            "notes": (
                (
                    "On-call Telegram live send PASS. "
                    if _dv(drills, "telegram_oncall_live") == "PASS"
                    else "On-call page unarmed. "
                )
                + "Cloud HA false; production replica SIGKILL not drilled."
            ),
        },
        {
            "axis": "input_manipulation",
            "verdict": "PASS" if integ_ok else "FAIL",
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


def compute_tracks(
    *,
    domains: list[dict[str, Any]],
    pub: dict[str, Any],
    four: dict[str, Any],
    integrity: dict[str, Any],
    counts: dict[str, int],
) -> dict[str, Any]:
    dmap = {d["id"]: d for d in domains}
    live_fill = bool((four.get("blocker_1_live_venue_fill") or {}).get("live_fill"))
    jup = bool((four.get("blocker_2_jupiter_live_signature") or {}).get("verified_complete"))
    cloud = bool((four.get("blocker_4_cloud_multi_az_ha") or {}).get("cloud_multi_az"))

    public_demo = bool(
        pub.get("meets_public_floor")
        and integrity.get("verdict") == "PASS"
        and (dmap.get("D35") or {}).get("verdict") == "PASS"
        and (dmap.get("D12") or {}).get("verdict") == "PASS"
        and (dmap.get("D04") or {}).get("verdict") == "PASS"
        and (dmap.get("D08") or {}).get("verdict") == "PASS"
    )
    no_open_lc = (
        counts["critical_open"] == 0
        and counts["high_open"] == 0
        and counts["untested_launch_critical"] == 0
    )
    live_production = bool(
        no_open_lc
        and (dmap.get("EXT_CLOUD_HA") or {}).get("verdict") == "PASS"
        and (dmap.get("D16") or {}).get("verdict") == "PASS"
        and (dmap.get("D20") or {}).get("verdict") == "PASS"
        and (dmap.get("D10") or {}).get("verdict") == "PASS"
        and (dmap.get("D24") or {}).get("verdict") == "PASS"
        and (dmap.get("D30") or {}).get("verdict") == "PASS"
        and cloud
    )
    live_money = bool(
        live_production
        and live_fill
        and jup
        and (dmap.get("D07") or {}).get("verdict") == "PASS"
        and (dmap.get("D13") or {}).get("verdict") == "PASS"
        and (dmap.get("EXT_LIVE_FILL") or {}).get("verdict") == "PASS"
        and (dmap.get("EXT_JUPITER_VC") or {}).get("verdict") == "PASS"
    )
    return {
        "PUBLIC-DEMO-READY": public_demo,
        "LIVE-PRODUCTION-READY": live_production,
        "LIVE-MONEY-READY": live_money,
        "notes": {
            "PUBLIC-DEMO-READY": "Visitor/paper HTTP + integrity + user-safety. Not live production. Not live money.",
            "LIVE-PRODUCTION-READY": "Requires 0 Critical/High/untested LC, cloud multi-AZ, prod DNS/TLS, pentest, on-call, counsel.",
            "LIVE-MONEY-READY": "Requires LIVE-PRODUCTION-READY plus live_fill + Jupiter VC + PSP + execution proofs.",
        },
    }


def final_verdict(
    domains: list[dict[str, Any]],
    *,
    tracks: dict[str, Any],
) -> dict[str, Any]:
    counts = _count_open(domains)
    unknown = [d["id"] for d in domains if d["verdict"] not in ALLOWED_VERDICTS]
    external = [d["id"] for d in domains if d["id"].startswith("EXT_") and d["verdict"] == "FAIL"]
    unverified_lc = []
    go_ok = (
        counts["critical_open"] == 0
        and counts["high_open"] == 0
        and counts["untested_launch_critical"] == 0
        and not unknown
        and not unverified_lc
        and bool(tracks.get("LIVE-PRODUCTION-READY"))
        and bool(tracks.get("LIVE-MONEY-READY"))
    )
    decision = "GO" if go_ok else "NO-GO"
    why = (
        "Unconditional GO requires LIVE-PRODUCTION-READY and LIVE-MONEY-READY together with "
        "0 Critical, 0 High, 0 untested launch-critical, 0 unknown blockers, 0 unverified "
        "launch-critical assumptions, every mandatory test PASS with re-verifiable evidence, "
        "proved live-money paths, and closed or in-scope-documented legal/external dependencies."
    )
    if decision == "NO-GO":
        why += (
            f" Observed: critical_open={counts['critical_open']}, high_open={counts['high_open']}, "
            f"untested_lc={counts['untested_launch_critical']}, "
            f"PUBLIC-DEMO-READY={tracks.get('PUBLIC-DEMO-READY')}, "
            f"LIVE-PRODUCTION-READY={tracks.get('LIVE-PRODUCTION-READY')}, "
            f"LIVE-MONEY-READY={tracks.get('LIVE-MONEY-READY')}."
        )
    return {
        "decision": decision,
        "product_complete": False,
        "live_money_ready": bool(tracks.get("LIVE-MONEY-READY")),
        "live_production_ready": bool(tracks.get("LIVE-PRODUCTION-READY")),
        "public_demo_ready": bool(tracks.get("PUBLIC-DEMO-READY")),
        "unconditional_go_criteria_met": go_ok,
        **counts,
        "untested_launch_critical_requirements": counts["untested_launch_critical"],
        "unverified_assumptions": [],
        "unverified_launch_critical_assumptions": unverified_lc,
        "external_blockers": external,
        "known_accepted_risks": [
            "Zero-cost constraint: no wallet funding, no paid cloud multi-AZ, no geo proxy",
            "synthetic_mid remainder (5) must stay labeled",
            "Medium/Low UX/a11y/browser matrix open — must not be hidden",
            "PUBLIC-DEMO-READY is not LIVE-PRODUCTION-READY and is not LIVE-MONEY-READY",
        ],
        "unknown_launch_blockers": unknown,
        "why_not_go": why if decision == "NO-GO" else "",
        "tracks": {
            "PUBLIC-DEMO-READY": bool(tracks.get("PUBLIC-DEMO-READY")),
            "LIVE-PRODUCTION-READY": bool(tracks.get("LIVE-PRODUCTION-READY")),
            "LIVE-MONEY-READY": bool(tracks.get("LIVE-MONEY-READY")),
        },
    }


def build_certification() -> dict[str, Any]:
    import subprocess
    import sys

    from launch_drills import run_all_drills
    from operator_go_gates import run_live_probes

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    drills = run_all_drills(include_heavy=True)
    live_gates = run_live_probes(drills=drills)
    integrity = run_financial_integrity_cases()
    three_am = overlay_three_am_with_drills(run_three_am_scenarios(), drills)
    domains = domain_register(integrity=integrity, three_am=three_am, drills=drills)
    counts = _count_open(domains)
    tracks = compute_tracks(
        domains=domains,
        pub=_public_score(),
        four=_four_blockers(),
        integrity=integrity,
        counts=counts,
    )
    caps = certify_capabilities(tracks=tracks)
    red = red_team_axes(drills, integrity)
    verdict = final_verdict(domains, tracks=tracks)
    track_counts = {
        "total": len(caps),
        "PUBLIC-DEMO-READY": sum(1 for c in caps if c["certification"] == "PUBLIC-DEMO-READY"),
        "LIVE-PRODUCTION-READY": sum(1 for c in caps if c["certification"] == "LIVE-PRODUCTION-READY"),
        "LIVE-MONEY-READY": sum(1 for c in caps if c["certification"] == "LIVE-MONEY-READY"),
        "NOT-READY": sum(1 for c in caps if c["certification"] == "NOT-READY"),
    }
    return {
        "ok": True,
        "schema": "production_launch_certification.v2",
        "sha": sha,
        "proved_at": _utcnow(),
        "python": sys.version.split()[0],
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "live_money_ready": bool(tracks.get("LIVE-MONEY-READY")),
        "live_production_ready": bool(tracks.get("LIVE-PRODUCTION-READY")),
        "public_demo_ready": bool(tracks.get("PUBLIC-DEMO-READY")),
        "tracks": tracks,
        "allowed_verdicts": sorted(ALLOWED_VERDICTS),
        "feature_tracks": sorted(FEATURE_TRACKS),
        "forbidden_phrases_not_used": [
            "looks good",
            "mostly complete",
            "should work",
            "appears secure",
            "probably production-ready",
            "Production Ready ورقيًا",
            "PRODUCTION-READY",
        ],
        "financial_decision_integrity": integrity,
        "three_am": three_am,
        "drills": {
            "pass_count": drills.get("pass_count"),
            "fail_count": drills.get("fail_count"),
            "not_tested_count": drills.get("not_tested_count"),
            "items": drills.get("drills") or [],
        },
        "red_team": red,
        "domains": domains,
        "capabilities": caps,
        "capability_counts": track_counts,
        "public_direct_use": _public_score(),
        "operator_live_probes": live_gates,
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
