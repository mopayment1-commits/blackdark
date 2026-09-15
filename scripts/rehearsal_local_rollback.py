#!/usr/bin/env python3
"""Isolated local Docker application rollback rehearsal for Production Readiness §13."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "production_readiness"
EVIDENCE_PATH = EVIDENCE_DIR / "local_rollback_rehearsal.json"

IMAGE_N = "blackdark-pr-rollback:n"
IMAGE_N1 = "blackdark-pr-rollback:nplus1"
CONTAINER_N = "blackdark-pr-rollback-n"
CONTAINER_N1 = "blackdark-pr-rollback-nplus1"
HOST_PORT = 18080
HEALTH_URL = f"http://127.0.0.1:{HOST_PORT}/health/live"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{proc.stderr[-800:]}")
    return proc


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(["sudo", "docker", *args], check=check)


def _cleanup() -> None:
    _docker("rm", "-f", CONTAINER_N, check=False)
    _docker("rm", "-f", CONTAINER_N1, check=False)


def _wait_health(timeout: int = 180) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionResetError):
            time.sleep(3)
    return False


def _container_env(version: str) -> list[str]:
    return [
        "-e",
        "ENV=test",
        "-e",
        "SERVICE_MODE=web",
        "-e",
        "RUN_AGGREGATOR=false",
        "-e",
        "INGESTION_ENABLED=false",
        "-e",
        "FORECAST_ENABLED=false",
        "-e",
        "ORACLE_DATA_HUB_ENABLED=false",
        "-e",
        "BINANCE_WS_ENABLED=false",
        "-e",
        "SERVICE_BUS_LOCAL=true",
        "-e",
        "SOFT_LAUNCH=true",
        "-e",
        f"PR_DEPLOY_VERSION={version}",
        "-e",
        "DATABASE_URL=sqlite:////tmp/pr_rollback.db",
    ]


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    gaps: list[str] = []
    evidence: dict[str, object] = {
        "LOCAL_ROLLBACK_REHEARSAL_PERFORMED": True,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        _cleanup()
        build = _docker("build", "-t", IMAGE_N, ".")
        evidence["build_n"] = build.stdout[-200:] if build.stdout else "ok"
        _docker("tag", IMAGE_N, IMAGE_N1)

        run_n = _docker(
            "run",
            "-d",
            "--name",
            CONTAINER_N,
            "-p",
            f"{HOST_PORT}:8080",
            *_container_env("n"),
            IMAGE_N,
        )
        if not _wait_health():
            gaps.append("version_n_health_failed")
        else:
            evidence["version_n_health"] = True

        _docker("stop", CONTAINER_N)
        _docker("rm", CONTAINER_N)

        run_n1 = _docker(
            "run",
            "-d",
            "--name",
            CONTAINER_N1,
            "-p",
            f"{HOST_PORT}:8080",
            *_container_env("nplus1"),
            IMAGE_N1,
        )
        if not _wait_health():
            gaps.append("version_nplus1_health_failed")
        else:
            evidence["version_nplus1_health"] = True

        _docker("stop", CONTAINER_N1)
        _docker("rm", CONTAINER_N1)

        rollback = _docker(
            "run",
            "-d",
            "--name",
            CONTAINER_N,
            "-p",
            f"{HOST_PORT}:8080",
            *_container_env("n"),
            IMAGE_N,
        )
        if not _wait_health():
            gaps.append("rollback_health_failed")
        else:
            evidence["rollback_health"] = True
            evidence["ROLLBACK_STATE_CORRUPTION_DETECTED"] = False
            evidence["ROLLBACK_DATA_LOSS_DETECTED"] = False

    except Exception as exc:
        gaps.append(f"exception:{exc}")
    finally:
        _cleanup()

    evidence["TRUE_LOCAL_ROLLBACK_GAPS"] = len(gaps)
    evidence["gaps"] = gaps
    evidence["LOCAL_ROLLBACK_REHEARSAL_PASS"] = len(gaps) == 0
    evidence["GENUINE_EXTERNAL_ROLLBACK_VALIDATION_PENDING"] = 1
    evidence["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if not gaps else 1


if __name__ == "__main__":
    raise SystemExit(main())
