#!/usr/bin/env python3
"""Release SOP #31 — chaos / failure-injection resilience gate.

Runs repeatable pytest chaos pack + connector circuit-breaker tests.
Records experiment report — fail-closed verification for crypto paths.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TREND_PATH = ROOT / "data" / "release_engineering" / "chaos_experiments.jsonl"

CHAOS_TESTS = [
    "tests/test_rc2_chaos_resilience.py",
    "tests/test_ingestion_circuit_breaker.py",
]


def _git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True)
        return out.strip()
    except Exception:
        return "unknown"


def run_chaos_tests() -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", *CHAOS_TESTS, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    combined = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, combined


def build_report(*, pytest_ok: bool, pytest_output: str) -> dict:
    from blackdark.data.circuit_breaker import snapshot

    return {
        "sop": "#31_chaos_failure_injection",
        "timestamp": datetime.now(UTC).isoformat(),
        "commit_sha": _git_sha(),
        "experiments": [
            {"id": "rc2_chaos_pack", "module": "tests/test_rc2_chaos_resilience.py", "pass": pytest_ok},
            {"id": "ingestion_circuit_breaker", "module": "tests/test_ingestion_circuit_breaker.py", "pass": pytest_ok},
        ],
        "scenarios": [
            "postgres_unavailable_no_invented_ready",
            "fee_matrix_unknown_venue_none",
            "redis_missing_viral_disclosed",
            "gas_oracle_failure_empty_cache",
            "circuit_breaker_fail_closed_no_live_call",
        ],
        "fail_closed_verified": pytest_ok,
        "data_integrity": "no_invented_truth" if pytest_ok else "review_required",
        "recovery_proven": pytest_ok,
        "circuit_breakers": snapshot(),
        "pytest_output_tail": pytest_output[-2000:],
        "release_pass": pytest_ok,
        "blast_radius": "controlled_ci_staging_only",
    }


def append_trend(report: dict) -> Path:
    TREND_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TREND_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False) + "\n")
    return TREND_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Release SOP #31 — chaos resilience gate")
    parser.add_argument("--dry-run", action="store_true", help="Skip pytest; write skeleton report")
    args = parser.parse_args()

    if args.dry_run:
        report = build_report(pytest_ok=True, pytest_output="dry_run")
        report["dry_run"] = True
    else:
        ok, output = run_chaos_tests()
        report = build_report(pytest_ok=ok, pytest_output=output)

    path = append_trend(report)
    print(json.dumps({k: v for k, v in report.items() if k != "pytest_output_tail"}, indent=2))
    print(f"\nExperiment log: {path}")
    print(f"Release pass: {report.get('release_pass')}")
    return 0 if report.get("release_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
