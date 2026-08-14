"""Launch drills — re-verifiable in-process tests. Never invent PASS.

Each drill returns verdict PASS|FAIL|NOT_TESTED plus evidence.
NOT_TESTED only when the drill could not execute (missing binary), not when
the control is absent — absent required controls are FAIL.
"""

from __future__ import annotations

import json
import os
import shutil
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

    old_env = os.environ.get("REDIS_URL")
    old_cfg = getattr(config, "REDIS_URL", "")
    live_url = (old_env or old_cfg or "redis://127.0.0.1:6379/0").strip() or "redis://127.0.0.1:6379/0"
    os.environ["REDIS_URL"] = live_url
    config.REDIS_URL = live_url
    reset_redis_client()
    before = bool(redis_live())
    os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
    config.REDIS_URL = "redis://127.0.0.1:1/0"
    reset_redis_client()
    try:
        after = bool(redis_live())
    finally:
        os.environ["REDIS_URL"] = live_url
        config.REDIS_URL = live_url
        reset_redis_client()
        restored = bool(redis_live())
        if old_env is None:
            os.environ.pop("REDIS_URL", None)
        else:
            os.environ["REDIS_URL"] = old_env
        config.REDIS_URL = old_cfg
        reset_redis_client()
    ok = before and (after is False) and restored
    return _drill(
        "redis_dead_port",
        "PASS" if ok else "FAIL",
        "viral_capacity.reset_redis_client + live URL then 127.0.0.1:1",
        before_live=before,
        after_dead_live=after,
        restored_live=restored,
        live_url_used=live_url.split("@")[-1],
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


TELEGRAM_ONCALL_EVIDENCE = ROOT / "docs" / "dd" / "BLACKDARK_TELEGRAM_ONCALL_EVIDENCE.json"


def _telegram_oncall_stamp(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a secret-free on-call receipt. Never writes token or chat_id."""
    from telegram_monitor import oncall_evidence_path

    safe = {
        "verdict": payload.get("verdict"),
        "ok": bool(payload.get("ok")),
        "reason": payload.get("reason"),
        "bot_token_present": bool(payload.get("bot_token_present")),
        "chat_id_present": bool(payload.get("chat_id_present")),
        "bot_username": payload.get("bot_username"),
        "message_id": payload.get("message_id"),
        "chat_type": payload.get("chat_type"),
        "http_status": payload.get("http_status"),
        "telegram_ok": payload.get("telegram_ok"),
        "error_code": payload.get("error_code"),
        "proved_at": payload.get("proved_at") or _utcnow(),
        "sha": payload.get("sha"),
        "path": "telegram_monitor.prove_telegram_oncall_page",
    }
    dest = oncall_evidence_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")
    return safe


def telegram_oncall_live_proved() -> bool:
    from telegram_monitor import oncall_live_proved

    return oncall_live_proved()


def drill_telegram_oncall_live() -> dict[str, Any]:
    """Real Bot API page. PASS only with telegram ok + message_id. Never logs secrets."""
    import asyncio
    import subprocess

    from telegram_monitor import prove_telegram_oncall_page

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    text = (
        "BLACKDARK on-call test Alert\n"
        f"SHA: {sha[:12]}\n"
        f"UTC: {_utcnow()}\n"
        "This is a real Alert from BLACKDARK. Receipt requires Telegram ok + message_id."
    )
    try:
        receipt = asyncio.run(prove_telegram_oncall_page(text=text))
    except Exception:
        receipt = {
            "ok": False,
            "reason": "exception",
            "bot_token_present": False,
            "chat_id_present": False,
            "message_id": None,
            "bot_username": None,
            "chat_type": None,
            "http_status": 0,
            "telegram_ok": None,
        }
    ok = bool(
        receipt.get("ok")
        and receipt.get("telegram_ok") is True
        and isinstance(receipt.get("message_id"), int)
        and receipt.get("message_id") > 0
        and receipt.get("bot_username")
    )
    verdict = "PASS" if ok else "FAIL"
    stamped = _telegram_oncall_stamp(
        {
            "verdict": verdict,
            "ok": ok,
            "reason": receipt.get("reason"),
            "bot_token_present": receipt.get("bot_token_present"),
            "chat_id_present": receipt.get("chat_id_present"),
            "bot_username": receipt.get("bot_username"),
            "message_id": receipt.get("message_id"),
            "chat_type": receipt.get("chat_type"),
            "http_status": receipt.get("http_status"),
            "telegram_ok": receipt.get("telegram_ok"),
            "error_code": receipt.get("error_code"),
            "proved_at": _utcnow(),
            "sha": sha,
        }
    )
    return _drill(
        "telegram_oncall_live",
        verdict,
        "telegram_monitor.prove_telegram_oncall_page getMe+sendMessage; message_id required",
        bot_token_present=stamped["bot_token_present"],
        chat_id_present=stamped["chat_id_present"],
        bot_username=stamped["bot_username"],
        message_id=stamped["message_id"],
        chat_type=stamped["chat_type"],
        http_status=stamped["http_status"],
        telegram_ok=stamped["telegram_ok"],
        reason=stamped["reason"],
        notes=(
            "Live Telegram on-call page. Token presence alone is not PASS. "
            "Secrets are never written to evidence."
        ),
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
    env = {**os.environ, "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD") or "compose-config-probe"}
    try:
        proc = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.ha.yml", "config"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        return _drill(
            "compose_config",
            "FAIL",
            "docker binary not found",
            notes="Cannot validate compose HA overlay without docker. Evaluated missing → FAIL.",
        )
    if proc.returncode != 0:
        return _drill(
            "compose_config",
            "FAIL",
            "docker compose -f docker-compose.yml -f docker-compose.ha.yml config",
            returncode=proc.returncode,
            stderr=(proc.stderr or proc.stdout)[-400:],
        )
    merged = proc.stdout or ""
    ok = "WEB_REPLICAS" in merged and "postgres:" in merged
    return _drill(
        "compose_config",
        "PASS" if ok else "FAIL",
        "docker compose config merged HA overlay",
        stdout_chars=len(merged),
        notes="Client-side compose interpolation. Does not start a production cluster.",
    )


def drill_executable_l2_scope() -> dict[str, Any]:
    """Executable books must be venue_l2. Remainder stays labeled. Do not invent AMM ladders."""
    from l2_remainder import catalog_l2_remainder
    from live_data_truth_probe import _adopt_mesh_l2_probe

    rem = catalog_l2_remainder()
    remainder = rem.get("remainder") or []
    labeled = bool(remainder) and all(v.get("depth_class") == "synthetic_mid" for v in remainder)
    rejected = _adopt_mesh_l2_probe(
        {
            "ok": True,
            "live": True,
            "bids": [[1.0, 1.0]],
            "asks": [[1.1, 1.0]],
            "bid": 1.0,
            "ask": 1.1,
            "fabricated_depth": False,
            "depth_source": "synthetic_mid",
            "venue": "orca",
            "symbol": "SOL/USDC",
            "source": "drill",
        }
    )
    four_p = ROOT / "docs" / "dd" / "BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json"
    four = json.loads(four_p.read_text(encoding="utf-8")) if four_p.is_file() else {}
    b3 = four.get("blocker_3_full_mesh_100") or {}
    core_ok = int(b3.get("mesh_live_count") or 0) == int(b3.get("core_mesh_target") or -1)
    core_ok = core_ok and int(b3.get("mesh_l2_count") or 0) == int(b3.get("core_mesh_target") or -1)
    ok = labeled and (rejected is False) and core_ok and rem.get("full_mesh_l2_complete") is False
    return _drill(
        "executable_l2_scope",
        "PASS" if ok else "FAIL",
        "l2_remainder + _adopt_mesh_l2_probe rejects synthetic_mid + CORE mesh 92/92",
        remainder_count=len(remainder),
        synthetic_rejected=rejected is False,
        core_mesh=f"{b3.get('mesh_l2_count')}/{b3.get('core_mesh_target')}",
        notes="Catalog 100% venue_l2 remains EXT_L2_100. This drill proves live adoption cannot ingest synthetic_mid.",
    )


def drill_ha_architecture() -> dict[str, Any]:
    """HA *design* locally: replicas in Railway+compose, local PG streaming, 2-worker HTTP."""
    railway = ROOT / "railway.json"
    replicas = 0
    try:
        body = json.loads(railway.read_text(encoding="utf-8"))
        replicas = int((body.get("deploy") or {}).get("numReplicas") or 0)
    except Exception:
        replicas = 0
    overlay = (ROOT / "docker-compose.ha.yml").read_text(encoding="utf-8")
    has_overlay = "WEB_REPLICAS" in overlay and "WEB_CONCURRENCY" in overlay
    ok = replicas >= 2 and has_overlay
    return _drill(
        "ha_architecture",
        "PASS" if ok else "FAIL",
        "railway.json numReplicas + docker-compose.ha.yml WEB_REPLICAS",
        railway_replicas=replicas,
        compose_ha_overlay=has_overlay,
        notes="Architecture design. Cloud multi-AZ deploy is D20/EXT_CLOUD_HA, not this drill.",
    )


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

    def _run(cmd: list[str]) -> subprocess.CompletedProcess[str] | None:
        try:
            return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180, check=False)
        except FileNotFoundError:
            return None

    proc = _run(["python", "-m", "pip_audit", "-r", str(req), "--desc"])
    missing = proc is None or (
        proc.returncode == 127
        or "No module named pip_audit" in (proc.stderr or "") + (proc.stdout or "")
        or "No module named 'pip_audit'" in (proc.stderr or "") + (proc.stdout or "")
    )
    if missing:
        proc = _run(["pip-audit", "-r", str(req), "--desc"])
        missing = proc is None or proc.returncode == 127 or "not found" in (proc.stderr or "").lower()
    if missing:
        inst = _run(["python", "-m", "pip", "install", "pip-audit", "-q"])
        if inst is not None and inst.returncode == 0:
            proc = _run(["python", "-m", "pip_audit", "-r", str(req), "--desc"])
        else:
            return _drill(
                "pip_audit",
                "FAIL",
                "pip-audit missing and pip install pip-audit failed",
                returncode=None if inst is None else inst.returncode,
                tail="" if inst is None else (inst.stderr or inst.stdout or "")[-400:],
            )
    if proc is None:
        return _drill("pip_audit", "FAIL", "pip-audit binary missing after install attempt")
    return _drill(
        "pip_audit",
        "PASS" if proc.returncode == 0 else "FAIL",
        f"pip-audit -r {req.name}",
        returncode=proc.returncode,
        tail=(proc.stdout or proc.stderr or "")[-400:],
    )


def drill_compose_yaml_merge() -> dict[str, Any]:
    """Parse and merge compose files without docker. Not a substitute for `docker compose config`."""
    try:
        import yaml
    except Exception as exc:
        return _drill("compose_yaml_merge", "FAIL", "PyYAML missing", error=type(exc).__name__)
    base_p = ROOT / "docker-compose.yml"
    overlay_p = ROOT / "docker-compose.ha.yml"
    try:
        base = yaml.safe_load(base_p.read_text(encoding="utf-8")) or {}
        overlay = yaml.safe_load(overlay_p.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return _drill("compose_yaml_merge", "FAIL", "compose YAML parse", error=type(exc).__name__)
    services = dict(base.get("services") or {})
    for name, spec in (overlay.get("services") or {}).items():
        if name in services and isinstance(services[name], dict) and isinstance(spec, dict):
            services[name] = {**services[name], **spec}
        else:
            services[name] = spec
    ok = "web" in services and "postgres" in services and "redis" in services
    return _drill(
        "compose_yaml_merge",
        "PASS" if ok else "FAIL",
        "PyYAML merge docker-compose.yml + docker-compose.ha.yml",
        services=sorted(services),
        notes="Valid YAML merge. docker compose config remains a separate drill.",
    )


def drill_stripe_sandbox() -> dict[str, Any]:
    """Stripe TEST API only. Invalid/live keys must FAIL. Never logs secrets."""
    import stripe

    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        return _drill(
            "stripe_sandbox",
            "FAIL",
            "STRIPE_SECRET_KEY unset",
            notes="No sandbox charge. Unconditional GO still requires a proved PSP path.",
        )
    if key.startswith("sk_live_"):
        return _drill(
            "stripe_sandbox",
            "FAIL",
            "sk_live_ refused in unpaid cert",
            notes="Live Stripe keys are not exercised on this zero-cost cert.",
        )
    stripe.api_key = key
    try:
        stripe.Account.retrieve()
    except Exception as exc:
        return _drill(
            "stripe_sandbox",
            "FAIL",
            "stripe.Account.retrieve",
            error=type(exc).__name__,
            notes="TEST key present but Stripe API rejected it. Not a sandbox charge.",
        )
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "BLACKDARK cert probe"},
                        "unit_amount": 2900,
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            success_url="http://127.0.0.1/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://127.0.0.1/cancel",
            payment_method_types=["card"],
        )
        sid = str(getattr(session, "id", "") or "")
        url = str(getattr(session, "url", "") or "")
        ok = sid.startswith("cs_") and url.startswith("https://")
        if sid:
            try:
                stripe.checkout.Session.expire(sid)
            except Exception:
                pass
        return _drill(
            "stripe_sandbox",
            "PASS" if ok else "FAIL",
            "stripe.checkout.Session.create TEST mode",
            session_id_prefix=sid[:8],
            notes="Checkout session created in TEST mode. Completing a card charge was not required for this drill.",
        )
    except Exception as exc:
        return _drill(
            "stripe_sandbox",
            "FAIL",
            "stripe.checkout.Session.create",
            error=type(exc).__name__,
        )


def _wait_http_ok(url: str, timeout_sec: float = 45.0) -> bool:
    import urllib.error
    import urllib.request

    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if int(resp.status) == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def _chrome_dump(url: str) -> tuple[int, str]:
    import tempfile

    profile = tempfile.mkdtemp(prefix="bd-chrome-")
    proc = subprocess.Popen(
        [
            "google-chrome",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-extensions",
            "--disable-default-apps",
            "--no-first-run",
            "--metrics-recording-only",
            "--remote-debugging-port=0",
            f"--user-data-dir={profile}",
            "--virtual-time-budget=4000",
            "--dump-dom",
            url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, _stderr = proc.communicate(timeout=8)
        return proc.returncode or 0, stdout or ""
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, 15)
        except Exception:
            proc.kill()
        stdout, _stderr = proc.communicate(timeout=5)
        return 124, stdout or ""
    finally:
        try:
            shutil.rmtree(profile, ignore_errors=True)
        except Exception:
            pass


def drill_chrome_public_pages() -> dict[str, Any]:
    """Chromium headless against a local uvicorn — not Safari/Firefox/mobile."""
    import signal
    import sys
    import urllib.request

    port = 18099
    base = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "dashboard:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pages = ["/login", "/privacy", "/terms", "/disclaimer", "/refund"]
    rows: list[dict[str, Any]] = []
    try:
        if not _wait_http_ok(f"{base}/health/live", timeout_sec=60):
            return _drill(
                "chrome_public_pages",
                "FAIL",
                f"uvicorn :{port} did not become live",
                pid=proc.pid,
            )
        for path in pages:
            url = base + path
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    http_status = int(resp.status)
            except Exception:
                http_status = 0
            rc, dom = _chrome_dump(url)
            low = dom.lower()
            # Chrome may hang after dump-dom; rc 124 with HTML is still a rendered page.
            rows.append(
                {
                    "path": path,
                    "http_status": http_status,
                    "chrome_rc": rc,
                    "has_html_lang": "lang=" in low[:4000],
                    "has_title": "<title>" in low and "</title>" in low,
                    "has_viewport": "viewport" in low,
                    "dom_chars": len(dom),
                }
            )
        ok_pages = [
            r
            for r in rows
            if r["http_status"] == 200 and r["has_title"] and r["dom_chars"] > 200
        ]
        a11y_ok = all(r["has_html_lang"] and r["has_title"] for r in ok_pages) and len(ok_pages) >= 4
        browser_ok = len(ok_pages) >= 4
        verdict = "PASS" if browser_ok and a11y_ok else "FAIL"
        return _drill(
            "chrome_public_pages",
            verdict,
            "google-chrome --headless=new --dump-dom against local uvicorn",
            pages=rows,
            ok_page_count=len(ok_pages),
            a11y_lang_title=a11y_ok,
            notes="Chromium-only. Not Firefox/Safari/mobile. Automated lang/title ≠ WCAG 2.2 lab.",
        )
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=8)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


def drill_http_load_local() -> dict[str, Any]:
    """Concurrent HTTP against local uvicorn /health/live. Not a production SLO."""
    import signal
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import urllib.request

    port = 18100
    base = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "dashboard:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "2",
            "--log-level",
            "warning",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    times: list[float] = []
    statuses: list[int] = []
    try:
        if not _wait_http_ok(f"{base}/health/live", timeout_sec=60):
            return _drill("http_load_local", "FAIL", f"uvicorn :{port} did not become live", pid=proc.pid)

        def _one() -> tuple[int, float]:
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(f"{base}/health/live", timeout=5) as resp:
                    return int(resp.status), (time.perf_counter() - t0) * 1000
            except Exception:
                return 0, (time.perf_counter() - t0) * 1000

        with ThreadPoolExecutor(max_workers=16) as pool:
            futs = [pool.submit(_one) for _ in range(80)]
            for fut in as_completed(futs):
                st, ms = fut.result()
                statuses.append(st)
                times.append(ms)
        times_sorted = sorted(times)
        p95 = times_sorted[int(0.95 * (len(times_sorted) - 1))]
        ok_n = sum(1 for s in statuses if s == 200)
        local_ok = ok_n >= 76 and p95 < 2000
        return _drill(
            "http_load_local",
            "PASS" if local_ok else "FAIL",
            "80 GETs /health/live via 2-worker uvicorn + 16 threads",
            ok=ok_n,
            n=80,
            p50_ms=round(statistics.median(times_sorted), 2),
            p95_ms=round(p95, 2),
            max_ms=round(max(times), 2),
            notes="Local two-worker HTTP pack. Not multi-AZ production SLO/soak.",
        )
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=8)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


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
        drill_compose_yaml_merge(),
        drill_ha_architecture(),
        drill_executable_l2_scope(),
        drill_stripe_sandbox(),
        drill_counsel_artifacts(),
        drill_independent_pentest_artifact(),
        drill_rate_limit_abuse(),
        drill_panic_freeze(),
        drill_feature_flag(),
        drill_alembic_rollback_semantics(),
        drill_chaos_dead_postgres(),
        drill_slow_api_timeout(),
        drill_telegram_oncall_live(),
        drill_redis_dead_port(),
        drill_ai_fallback(),
        drill_pip_audit(),
    ]
    if include_heavy:
        drills.append(drill_postgres_streaming_ha())
        drills.append(drill_process_restart())
        drills.append(drill_asgi_latency())
        drills.append(drill_adversarial_suite())
        drills.append(drill_chrome_public_pages())
        drills.append(drill_http_load_local())
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
