#!/usr/bin/env python3
"""
Finalize BLACKDARK launch prep (code-side).

Runs constitution smoke, saves checklist, prints remaining Railway ops.
Optionally generates .env.launch.local secrets for paste into Railway.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 — intentional admin tooling
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))  # nosec B603 — fixed argv, shell=False, no user input


def main() -> int:
    os.chdir(ROOT)
    print("=" * 64)
    print("BLACKDARK — Finalize Launch (constitution path)")
    print("=" * 64)

    # 1) Secrets file for Railway paste
    gen = [
        sys.executable,
        "scripts/generate_launch_secrets.py",
        "--write",
        "--admin-email",
        os.getenv("ADMIN_EMAILS", "mopayment1@gmail.com").split(",")[0].strip()
        or "mopayment1@gmail.com",
    ]
    if os.getenv("APP_BASE_URL"):
        gen.extend(["--app-base-url", os.getenv("APP_BASE_URL", "")])
    _run(gen)

    # 2) In-process constitution smoke via checklist
    from launch_checklist import _run_pytest_quick, save_checklist

    ok, note = _run_pytest_quick()
    print(f"\nConstitution smoke: {'PASS' if ok else 'FAIL'} — {note}")

    checklist = save_checklist()
    print(
        f"Checklist: {checklist['done_count']}/{checklist['total_tasks']} "
        f"({checklist['launch_percent']}%) ready={checklist['launch_ready']}"
    )
    blocked = [r for r in checklist["items"] if r["status"] == "blocked"]
    if blocked:
        print("\nBlocked (ops — set on Railway):")
        for row in blocked:
            print(f"  • {row['id']}: {row['title']}")
            print(f"    → {row['action']}")

    # 3) Production guard snapshot (local env)
    try:
        from production_guard import evaluate_production_guard

        guard = evaluate_production_guard()
        print("\nProduction guard (current process env):")
        print(f"  required_pass={guard.get('required_pass')}")
        print(f"  failures={guard.get('required_failures')}")
        print(f"  warnings={guard.get('warnings')}")
    except Exception as exc:
        print(f"\nProduction guard unavailable: {exc}")

    # 4) Ops paste board
    print("\n" + "=" * 64)
    print("RAILWAY GO-LIVE BOARD (copy secrets from .env.launch.local)")
    print("=" * 64)
    print(
        """
1) Railway → Variables → paste keys from .env.launch.local
2) Add DATABASE_URL (Postgres plugin)
3) Confirm LEMON_SQUEEZY_CHECKOUT_PRO (already in launch file)
4) APP_BASE_URL=https://YOUR-DOMAIN
5) Optional later: TELEGRAM_* (LAUNCH_SKIP_TELEGRAM=true for soft launch)
6) python scripts/verify_constitution_live.py
7) Deploy → open /api/production/guard · /oracle/BTC?ux_mode=beginner&lang=en
8) UptimeRobot → /health/live
9) Announce → python scripts/mark_golive.py --url https://YOUR-DOMAIN
   See docs/GO_LIVE_AR.md
""".strip()
    )

    out = {
        "constitution_smoke": ok,
        "launch_percent": checklist["launch_percent"],
        "launch_ready": checklist["launch_ready"],
        "blocked": [b["id"] for b in blocked],
        "secrets_file": str(ROOT / ".env.launch.local"),
        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
        "runbook": "docs/RUNBOOK.md",
    }
    path = ROOT / "data" / "finalize_launch.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
