#!/usr/bin/env python3
"""Run all automatable pre-launch steps and write PRE_LAUNCH_EXECUTION_REPORT.json."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "PRE_LAUNCH_EXECUTION_REPORT.json"


def _run(cmd: list[str], *, timeout: int | None = None) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-40:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]),
    }


def _load_hosts_for_url(url: str) -> None:
    hosts: set[str] = set()
    for part in os.getenv("BLACKDARK_HTTP_HOST_ALLOWLIST", "").split(","):
        if part.strip():
            hosts.add(part.strip().lower())
    parsed = urlparse(url)
    if parsed.hostname:
        hosts.add(parsed.hostname.lower())
    for h in ("blackdark.io", "www.blackdark.io", "blackdark-production.up.railway.app"):
        hosts.add(h)
    os.environ["BLACKDARK_HTTP_HOST_ALLOWLIST"] = ",".join(sorted(hosts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute pre-launch closure (automated slice)")
    parser.add_argument(
        "--url",
        default=os.getenv("APP_BASE_URL", "https://blackdark-production.up.railway.app"),
        help="Production/staging base URL for live probes",
    )
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-live", action="store_true")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    report: dict = {
        "generated_at": datetime.now(UTC).isoformat(),
        "base_url": base,
        "steps": {},
        "owner_manual_remaining": [
            "Paste .env.launch.local into Railway Variables (never commit)",
            "Set DATABASE_URL (+ DATABASE_PUBLIC_URL if private DNS fails)",
            "Confirm custom domain DNS per deploy/dns/blackdark-io-railway.md",
            "UptimeRobot on /health/live",
            "Optional: mark_golive.py after public announcement",
        ],
    }

    report["steps"]["finalize_launch"] = _run(
        [sys.executable, "scripts/finalize_launch.py"],
        timeout=120,
    )

    report["steps"]["pre_launch_gate_assessor"] = _run(
        [sys.executable, "scripts/pre_launch_gate_assessor.py"],
        timeout=180,
    )

    report["steps"]["verify_constitution_live"] = _run(
        [sys.executable, "scripts/verify_constitution_live.py"],
        timeout=120,
    )

    report["steps"]["audit_visitor_nav"] = _run(
        [sys.executable, "scripts/audit_visitor_nav_links.py"],
        timeout=300,
    )

    if not args.skip_pytest:
        report["steps"]["pytest_launch57_smoke"] = _run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/launch57/test_phase8_e2e_acceptance.py",
                "tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py",
                "tests/test_public_pages_closure.py",
                "tests/test_p0_anonymous_route_foundation.py",
                "-q",
                "--tb=no",
            ],
            timeout=600,
        )

    if not args.skip_live:
        _load_hosts_for_url(base)
        report["steps"]["launch_verify"] = _run(
            [sys.executable, "scripts/launch_verify.py", base],
            timeout=600,
        )

    try:
        from launch_checklist import launch_checklist

        report["launch_checklist"] = launch_checklist()
    except Exception as exc:
        report["launch_checklist_error"] = type(exc).__name__

    assess_path = ROOT / "PRE_LAUNCH_GATE_ASSESSMENT.json"
    if assess_path.is_file():
        report["pre_launch_gate"] = json.loads(assess_path.read_text(encoding="utf-8"))

    constitution_path = ROOT / "data" / "constitution_live_verify.json"
    if constitution_path.is_file():
        report["constitution_live"] = json.loads(constitution_path.read_text(encoding="utf-8"))

    automated_ok = all(
        step.get("exit_code") == 0
        for key, step in report["steps"].items()
        if key != "pre_launch_gate_assessor"  # institutional bar; informational
    )
    lc = report.get("launch_checklist") or {}
    report["verdict"] = {
        "automated_steps_green": automated_ok,
        "launch_checklist_ready": bool(lc.get("launch_ready")),
        "code_ready_for_railway_paste": bool(lc.get("launch_ready")),
        "institutional_pre_launch_ready": bool(
            (report.get("pre_launch_gate") or {}).get("pre_launch_ready")
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["verdict"], indent=2, ensure_ascii=False))
    print(f"\nWrote {OUT}")
    return 0 if automated_ok and report["verdict"]["launch_checklist_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
