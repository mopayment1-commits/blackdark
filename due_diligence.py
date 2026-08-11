"""
BLACKDARK — Due diligence bundle (uptime + latency + test coverage).
"""

from __future__ import annotations

import subprocess  # nosec B404 — intentional admin tooling
import sys
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent


def run_profit_fee_coverage() -> dict[str, Any]:
    cfg = ROOT / ".coveragerc-profit-fee"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_fee_matrix.py",
        "tests/test_slippage_guard.py",
        "tests/test_profit_fee_algorithms.py",
        "tests/test_fast_scan_profit.py",
        "-q",
        "--tb=no",
        f"--cov-config={cfg}",
        "--cov=fee_matrix",
        "--cov=slippage_guard",
        "--cov=fast_scan_engine",
        "--cov=profit_fee_algorithms",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300, check=False)  # nosec B603 — fixed argv, shell=False, no user input
    lines = (proc.stdout or "").splitlines()
    total_line = next((line for line in lines if "TOTAL" in line), "")
    pct = 0.0
    if total_line:
        for part in total_line.split():
            if part.endswith("%"):
                try:
                    pct = float(part.strip("%"))
                except ValueError:
                    logger.debug("optional operation skipped", exc_info=True)
    return {
        "gate_percent": 90,
        "coverage_percent": pct,
        "passed": proc.returncode == 0,
        "modules": ["fee_matrix", "slippage_guard", "fast_scan_engine", "profit_fee_algorithms"],
        "summary_tail": lines[-12:],
        "stderr_tail": (proc.stderr or "").splitlines()[-5:],
    }


def due_diligence_report() -> dict[str, Any]:
    from latency_audit import latency_status
    from uptime_monitor import ha_architecture_status, uptime_stats

    coverage = run_profit_fee_coverage()
    latency = latency_status()
    uptime = uptime_stats(window_hours=24)
    ha = ha_architecture_status()

    probes_total = int(uptime.get("probes_total") or 0)
    meets_sla = uptime.get("meets_sla")
    uptime_ok = meets_sla is True if probes_total >= 10 else False

    checks = {
        "uptime_sla_99_99": uptime_ok,
        "uptime_probes_sufficient": probes_total >= 10,
        "latency_p99_le_50ms": bool(latency.get("meets_target_p99")),
        "profit_fee_coverage_ge_90": coverage.get("passed", False),
        "ha_architecture_ready": ha.get("high_availability_ready", False),
    }
    all_pass = all(checks.values())

    return {
        "status": "pass" if all_pass else "partial",
        "checks": checks,
        "uptime": uptime,
        "ha": ha,
        "latency": latency,
        "coverage": coverage,
        "buyer_script": "python scripts/due_diligence_verify.py",
    }
