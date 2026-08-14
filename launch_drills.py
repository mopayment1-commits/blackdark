"""Launch drills — re-verifiable in-process tests. Never invent PASS.

Each drill returns verdict PASS|FAIL|NOT_TESTED plus evidence.
NOT_TESTED only when the drill could not execute (missing binary), not when
the control is absent — absent required controls are FAIL.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ALLOWED = frozenset({"PASS", "FAIL", "NOT_TESTED", "NOT_APPLICABLE"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _drill(id: str, verdict: str, evidence: str, **extra: Any) -> dict[str, Any]:
    if verdict not in ALLOWED:
        raise ValueError(verdict)
    out = {"id": id, "verdict": verdict, "evidence": evidence, "proved_at": _utcnow()}
    out.update(extra)
    return out


def drill_sqlite_restore() -> dict[str, Any]:
    from ops_recovery import prove_sqlite_backup_restore

    r = prove_sqlite_backup_restore()
    return _drill(
        "sqlite_restore",
        "PASS" if r.get("ok") else "FAIL",
        "ops_recovery.prove_sqlite_backup_restore",
        result={k: r.get(k) for k in ("ok", "engine", "backup_bytes", "control")},
    )


def drill_postgres_dump_restore() -> dict[str, Any]:
    from ops_recovery import prove_postgres_local_dump_restore

    r = prove_postgres_local_dump_restore()
    ok = bool(r.get("ok"))
    return _drill(
        "postgres_dump_restore",
        "PASS" if ok else "FAIL",
        "ops_recovery.prove_postgres_local_dump_restore",
        result={k: r.get(k) for k in ("ok", "control", "ha_dr", "reason") if k in r or True},
        notes="LOCAL_EPHEMERAL_NOT_HA — not cloud multi-AZ",
    )


def drill_postgres_streaming_ha() -> dict[str, Any]:
    from ops_recovery import prove_postgres_streaming_ha_rpo_rto

    r = prove_postgres_streaming_ha_rpo_rto()
    ok = bool(r.get("ok"))
    return _drill(
        "postgres_streaming_ha",
        "PASS" if ok else "FAIL",
        "ops_recovery.prove_postgres_streaming_ha_rpo_rto",
        result={k: r.get(k) for k in ("ok", "ha_class", "rpo_ms", "rto_ms", "reason", "cloud_multi_az") if True},
        notes="Local streaming replication only. cloud_multi_az remains false.",
    )


def drill_redis_dead_port() -> dict[str, Any]:
    import config
    from viral_capacity import redis_live, reset_redis_client

    before = bool(redis_live())
    old_env = os.environ.get("REDIS_URL")
    old_cfg = getattr(config, "REDIS_URL", "")
    os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
    config.REDIS_URL = "redis://127.0.0.1:1/0"
    reset_redis_client()
    try:
        after = bool(redis_live())
    finally:
        if old_env is None:
            os.environ.pop("REDIS_URL", None)
        else:
            os.environ["REDIS_URL"] = old_env
        config.REDIS_URL = old_cfg
        reset_redis_client()
    restored = bool(redis_live()) if before else True
    ok = before and (after is False) and restored
    return _drill(
        "redis_dead_port",
        "PASS" if ok else "FAIL",
        "viral_capacity.reset_redis_client + REDIS_URL=127.0.0.1:1",
        before_live=before,
        after_dead_live=after,
        restored_live=bool(redis_live()) if before else restored,
    )


def drill_slow_api_timeout() -> dict[str, Any]:
    """Unreachable/invalid bot must fail closed inside the alert timeout budget."""
    import asyncio

    from alert_service import send_telegram_message

    old_tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    old_chat = os.environ.get("TELEGRAM_CHAT_ID")
    os.environ["TELEGRAM_BOT_TOKEN"] = "drill-token-not-real"
    os.environ["TELEGRAM_CHAT_ID"] = "1"
    t0 = time.perf_counter()
    try:
        ok = asyncio.run(send_telegram_message("drill", chat_id="1"))
    except Exception:
        ok = False
    finally:
        if old_tok is None:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        else:
            os.environ["TELEGRAM_BOT_TOKEN"] = old_tok
        if old_chat is None:
            os.environ.pop("TELEGRAM_CHAT_ID", None)
        else:
            os.environ["TELEGRAM_CHAT_ID"] = old_chat
    ms = (time.perf_counter() - t0) * 1000
    verdict = "PASS" if ok is False and ms < 20000 else "FAIL"
    return _drill(
        "slow_api_timeout",
        verdict,
        "alert_service.send_telegram_message with fake token",
        elapsed_ms=round(ms, 1),
        returned_ok=ok,
        notes="Fake token → delivery False (fail-closed). Hang >20s is FAIL.",
    )


def drill_sbom() -> dict[str, Any]:
    out = ROOT / "docs" / "data-room" / "sbom" / "cyclonedx-python.json"
    proc = subprocess.run(
        ["python", "scripts/generate_sbom.py", "--out", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0 or not out.is_file():
        return _drill("sbom", "FAIL", "scripts/generate_sbom.py", stderr=proc.stderr[-400:])
    body = json.loads(out.read_text(encoding="utf-8"))
    comps = body.get("components") or []
    ok = body.get("bomFormat") == "CycloneDX" and len(comps) >= 10
    return _drill("sbom", "PASS" if ok else "FAIL", str(out), component_count=len(comps))


def drill_license_inventory() -> dict[str, Any]:
    proc = subprocess.run(
        ["python", "scripts/generate_license_inventory.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    path = ROOT / "docs" / "data-room" / "licenses" / "dependency_licenses.json"
    ok = proc.returncode == 0 and path.is_file() and path.stat().st_size > 20
    return _drill(
        "license_inventory",
        "PASS" if ok else "FAIL",
        str(path),
        returncode=proc.returncode,
    )


def drill_bandit() -> dict[str, Any]:
    proc = subprocess.run(
        ["python", "-m", "bandit", "-c", ".bandit", "-f", "json", "-q", "-r", "."],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return _drill("bandit", "FAIL", "bandit json parse", stderr=proc.stderr[-400:])
    metrics = payload.get("metrics") or {}
    totals = metrics.get("_totals") or {}
    high = int(totals.get("SEVERITY.HIGH") or 0)
    crit = int(totals.get("SEVERITY.CRITICAL") or 0)
    # Bandit exits 1 when findings exist; we grade on HIGH/CRITICAL only.
    verdict = "PASS" if crit == 0 and high == 0 else "FAIL"
    return _drill(
        "bandit",
        verdict,
        ".bandit policy + python -m bandit",
        high=high,
        critical=crit,
        medium=int(totals.get("SEVERITY.MEDIUM") or 0),
    )


def drill_infra_files() -> dict[str, Any]:
    required = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.ha.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        "railway.json",
    ]
    missing = [p for p in required if not (ROOT / p).is_file()]
    return _drill(
        "infra_files",
        "PASS" if not missing else "FAIL",
        "Dockerfile + compose + HA overlay + CI/security workflows",
        missing=missing,
        notes="Files exist. Operator production DNS/TLS account was not probed — see D16 notes.",
    )


def drill_compose_config() -> dict[str, Any]:
    proc = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.ha.yml", "config"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        # docker may be absent — that is FAIL for production-like validation, not NOT_TESTED hidden.
        return _drill(
            "compose_config",
            "FAIL",
            "docker compose -f docker-compose.yml -f docker-compose.ha.yml config",
            returncode=proc.returncode,
            stderr=(proc.stderr or proc.stdout)[-400:],
        )
    return _drill("compose_config", "PASS", "docker compose config merged HA overlay")


def drill_counsel_artifacts() -> dict[str, Any]:
    """Independent counsel sign-off must be a file. Absence is FAIL, not NOT_TESTED."""
    paths = [
        ROOT / "docs" / "legal" / "COUNSEL_SIGNOFF.pdf",
        ROOT / "docs" / "legal" / "COUNSEL_SIGNOFF.md",
        ROOT / "docs" / "dd" / "INDEPENDENT_COUNSEL_SIGNOFF.md",
    ]
    found = [str(p) for p in paths if p.is_file()]
    return _drill(
        "counsel_signoff",
        "PASS" if found else "FAIL",
        "docs/legal/COUNSEL_SIGNOFF.*",
        found=found,
        notes="Engineer cannot sign legal. Missing artifact = FAIL vs Unconditional GO.",
    )


def drill_independent_pentest_artifact() -> dict[str, Any]:
    paths = [
        ROOT / "docs" / "dd" / "INDEPENDENT_PENTEST_REPORT.pdf",
        ROOT / "docs" / "dd" / "INDEPENDENT_PENTEST_REPORT.md",
    ]
    found = [str(p) for p in paths if p.is_file()]
    return _drill(
        "independent_pentest_artifact",
        "PASS" if found else "FAIL",
        "docs/dd/INDEPENDENT_PENTEST_REPORT.*",
        found=found,
        notes="In-repo adversarial suite is a different drill. Firm pentest artifact missing = FAIL.",
    )


def drill_process_restart() -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from dashboard import app

    codes: list[int] = []
    for _ in range(2):
        with TestClient(app, follow_redirects=False) as client:
            r = client.get("/health/live")
            codes.append(int(r.status_code))
    ok = codes == [200, 200]
    return _drill(
        "process_restart",
        "PASS" if ok else "FAIL",
        "TestClient lifespan start/stop/start /health/live",
        status_codes=codes,
    )


def drill_asgi_latency() -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from dashboard import app

    times: list[float] = []
    statuses: list[int] = []
    client = TestClient(app, follow_redirects=False)
    for _ in range(30):
        t0 = time.perf_counter()
        r = client.get("/health/live")
        times.append((time.perf_counter() - t0) * 1000)
        statuses.append(int(r.status_code))
    times_sorted = sorted(times)
    p95 = times_sorted[int(0.95 * (len(times_sorted) - 1))]
    p50 = statistics.median(times_sorted)
    ok_n = sum(1 for s in statuses if s == 200)
    # Local SLO for this drill only — production-like multi-worker is a separate FAIL.
    local_ok = ok_n == 30 and p95 < 2000
    return _drill(
        "asgi_latency",
        "PASS" if local_ok else "FAIL",
        "30x GET /health/live TestClient",
        p50_ms=round(p50, 2),
        p95_ms=round(p95, 2),
        max_ms=round(max(times), 2),
        ok=ok_n,
        n=30,
        local_slo="p95<2000ms /health/live ASGI",
        notes="Local ASGI pack. Not a multi-AZ production SLO.",
    )


def drill_rate_limit_abuse() -> dict[str, Any]:
    from viral_capacity import check_rate_limit, reset_redis_client

    reset_redis_client()
    tripped = False
    for _ in range(20):
        try:
            check_rate_limit("launch-drill-abuse", limit=5, window_sec=60, prefix="drill")
        except Exception as exc:
            tripped = getattr(exc, "status_code", None) == 429 or "429" in str(exc)
            if tripped:
                break
    return _drill(
        "rate_limit_abuse",
        "PASS" if tripped else "FAIL",
        "viral_capacity.check_rate_limit limit=5",
        tripped_429=tripped,
    )


def drill_panic_freeze() -> dict[str, Any]:
    from risk_manager import evaluate_execution_risk, freeze_trading, is_trading_frozen, unfreeze_trading

    unfreeze_trading()
    freeze_trading("launch_drill", duration_sec=3)
    frozen = is_trading_frozen()
    blocked = evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 1})
    unfreeze_trading()
    ok = frozen and not blocked.allowed and not is_trading_frozen()
    return _drill("panic_freeze", "PASS" if ok else "FAIL", "risk_manager freeze/evaluate/unfreeze")


def drill_feature_flag() -> dict[str, Any]:
    old = os.environ.get("SOFT_LAUNCH")
    os.environ["SOFT_LAUNCH"] = "true"
    try:
        from production_guard import evaluate_production_guard, is_production

        report = evaluate_production_guard()
        ok = isinstance(report, dict) and isinstance(report.get("checks"), list)
        prod = is_production()
        return _drill(
            "feature_flag_soft_launch",
            "PASS" if ok else "FAIL",
            "SOFT_LAUNCH=true evaluate_production_guard",
            is_production=prod,
            check_count=len(report.get("checks") or []) if isinstance(report, dict) else 0,
        )
    finally:
        if old is None:
            os.environ.pop("SOFT_LAUNCH", None)
        else:
            os.environ["SOFT_LAUNCH"] = old


def drill_alembic_rollback_semantics() -> dict[str, Any]:
    """Execute the migration integrity tests as a subprocess for re-verify."""
    proc = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/test_postgres_migration_integrity.py",
            "tests/test_postgres_backend.py",
            "-q",
            "--tb=line",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return _drill(
        "alembic_rollback_semantics",
        "PASS" if proc.returncode == 0 else "FAIL",
        "pytest tests/test_postgres_migration_integrity.py tests/test_postgres_backend.py",
        returncode=proc.returncode,
        tail=(proc.stdout or "")[-300:],
    )


def drill_adversarial_suite() -> dict[str, Any]:
    proc = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/test_adversarial_launch_redteam.py",
            "tests/test_p0_authz_hardening.py",
            "tests/test_security_hardening.py",
            "-q",
            "--tb=line",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    return _drill(
        "adversarial_suite",
        "PASS" if proc.returncode == 0 else "FAIL",
        "pytest adversarial + authz + security_hardening",
        returncode=proc.returncode,
        tail=(proc.stdout or proc.stderr or "")[-400:],
    )


def drill_chaos_dead_postgres() -> dict[str, Any]:
    proc = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/test_rc2_chaos_resilience.py",
            "-q",
            "--tb=line",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return _drill(
        "chaos_dead_postgres",
        "PASS" if proc.returncode == 0 else "FAIL",
        "pytest tests/test_rc2_chaos_resilience.py",
        returncode=proc.returncode,
        tail=(proc.stdout or "")[-300:],
    )


def drill_ai_fallback() -> dict[str, Any]:
    """Rules/explain path must survive missing TruLens and must not raise."""
    import asyncio

    from bd_platform.trulens_eval import explain_prediction

    try:
        body = asyncio.run(explain_prediction("BTC", price=50000.0))
    except Exception as exc:
        return _drill("ai_fallback", "FAIL", "explain_prediction raised", error=str(exc)[:240])
    ok = isinstance(body, dict) and "direction" in body and "reason_chain" in body
    return _drill(
        "ai_fallback",
        "PASS" if ok else "FAIL",
        "bd_platform.trulens_eval.explain_prediction",
        engine=body.get("engine") if isinstance(body, dict) else None,
        trulens_available=body.get("trulens_available") if isinstance(body, dict) else None,
        notes="TruLens optional. Missing provider must not crash or invent a live BUY.",
    )


def drill_pip_audit() -> dict[str, Any]:
    req = ROOT / "requirements.hashes.txt"
    if not req.is_file():
        req = ROOT / "requirements.lock.txt"
    if not req.is_file():
        return _drill("pip_audit", "FAIL", "requirements.hashes.txt and requirements.lock.txt missing")

    def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180, check=False)

    proc = _run(["python", "-m", "pip_audit", "-r", str(req), "--desc"])
    missing = (
        proc.returncode == 127
        or "No module named pip_audit" in (proc.stderr or "") + (proc.stdout or "")
        or "No module named 'pip_audit'" in (proc.stderr or "") + (proc.stdout or "")
    )
    if missing:
        proc = _run(["pip-audit", "-r", str(req), "--desc"])
        missing = proc.returncode == 127 or "not found" in (proc.stderr or "").lower()
    if missing:
        inst = _run(["python", "-m", "pip", "install", "pip-audit", "-q"])
        if inst.returncode == 0:
            proc = _run(["python", "-m", "pip_audit", "-r", str(req), "--desc"])
        else:
            return _drill(
                "pip_audit",
                "FAIL",
                "pip-audit missing and pip install pip-audit failed",
                returncode=inst.returncode,
                tail=(inst.stderr or inst.stdout or "")[-400:],
            )
    return _drill(
        "pip_audit",
        "PASS" if proc.returncode == 0 else "FAIL",
        f"pip-audit -r {req.name}",
        returncode=proc.returncode,
        tail=(proc.stdout or proc.stderr or "")[-400:],
    )


def run_all_drills(*, include_heavy: bool = True) -> dict[str, Any]:
    """Execute every in-repo drill. Heavy = postgres HA + dashboard TestClient packs."""
    drills: list[dict[str, Any]] = [
        drill_sqlite_restore(),
        drill_postgres_dump_restore(),
        drill_sbom(),
        drill_license_inventory(),
        drill_bandit(),
        drill_infra_files(),
        drill_compose_config(),
        drill_counsel_artifacts(),
        drill_independent_pentest_artifact(),
        drill_rate_limit_abuse(),
        drill_panic_freeze(),
        drill_feature_flag(),
        drill_alembic_rollback_semantics(),
        drill_chaos_dead_postgres(),
        drill_slow_api_timeout(),
        drill_redis_dead_port(),
        drill_ai_fallback(),
        drill_pip_audit(),
    ]
    if include_heavy:
        drills.append(drill_postgres_streaming_ha())
        drills.append(drill_process_restart())
        drills.append(drill_asgi_latency())
        drills.append(drill_adversarial_suite())
    by_id = {d["id"]: d for d in drills}
    return {
        "ok": True,
        "proved_at": _utcnow(),
        "drills": drills,
        "by_id": by_id,
        "pass_count": sum(1 for d in drills if d["verdict"] == "PASS"),
        "fail_count": sum(1 for d in drills if d["verdict"] == "FAIL"),
        "not_tested_count": sum(1 for d in drills if d["verdict"] == "NOT_TESTED"),
    }
