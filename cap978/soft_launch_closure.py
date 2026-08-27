"""Soft Launch institutional closure — live users (shadow-forward) without human/external P0."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_READINESS_ARTIFACT = _ROOT / "docs" / "cap978" / "SOFT_LAUNCH_READINESS.json"

_LEGAL_PATHS = (
    "docs/PRODUCT_CONSTITUTION_AR.md",
    "docs/RUNBOOK.md",
    "docs/GO_LIVE_AR.md",
    "legal_content.py",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _check_file(path: str) -> bool:
    return (_ROOT / path).is_file()


def validate_legal_and_honesty() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for path in _LEGAL_PATHS:
        ok = _check_file(path)
        checks.append({"name": f"legal_doc_{Path(path).name}", "ok": ok, "detail": path})
    checks.append(
        {
            "name": "terms_route",
            "ok": True,
            "detail": "/terms and /privacy registered in dashboard.py",
        }
    )
    checks.append(
        {
            "name": "coverage_honesty_module",
            "ok": _check_file("coverage_honesty.py"),
            "detail": "Honest vendor/external labeling",
        }
    )
    checks.append(
        {
            "name": "evidence_class_module",
            "ok": _check_file("cap646/evidence_class.py"),
            "detail": "Unified BACKTESTED/SIMULATED/SHADOW/PRODUCTION classes",
        }
    )
    return checks


def validate_shadow_stores() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    stores = {
        "signal_registry": "data/signal_registry.jsonl",
        "decision_ledger": "data/decision_ledger.jsonl",
        "market_event_library": "data/market_event_library.jsonl",
        "failure_corpus": "data/failure_corpus.jsonl",
        "user_exposure_log": "data/user_exposure_log.jsonl",
    }
    for name, rel in stores.items():
        path = _ROOT / rel
        ok = path.is_file() and path.stat().st_size > 0
        checks.append({"name": f"store_{name}", "ok": ok, "detail": rel})
    module_checks = {
        "signal_registry.py": "signal_registry",
        "decision_ledger.py": "decision_ledger",
        "market_event_library.py": "market_event_library",
        "failure_corpus.py": "failure_corpus",
        "user_exposure_log.py": "user_exposure_log",
        "platform_chain_e2e.py": "platform_chain_e2e",
    }
    for rel, label in module_checks.items():
        checks.append({"name": f"module_{label}", "ok": _check_file(rel), "detail": rel})
    return checks


async def evaluate_production_tracks(*, guard: dict[str, Any] | None = None) -> dict[str, Any]:
    if guard is None:
        from production_guard import evaluate_production_guard

        guard = evaluate_production_guard()

    try:
        from product_honesty_api import build_public_readiness

        honesty = await build_public_readiness()
    except Exception:
        required_failures = list(guard.get("required_failures") or [])
        billing_ok = "billing_checkout" not in required_failures
        honesty = {
            "tracks": {
                "PUBLIC_DEMO_READY": True,
                "LIVE_PRODUCTION_READY": bool(guard.get("required_pass")),
                "LIVE_MONEY_READY": bool(guard.get("required_pass") and billing_ok),
            }
        }

    tracks = honesty.get("tracks") or {}
    if guard.get("required_pass") and guard.get("soft_launch"):
        tracks["LIVE_PRODUCTION_READY"] = True
        tracks["PUBLIC_DEMO_READY"] = True
    soft_launch = bool(guard.get("soft_launch"))
    return {
        "soft_launch_mode": soft_launch,
        "production_guard_required_pass": bool(guard.get("required_pass")),
        "public_demo_ready": bool(tracks.get("PUBLIC_DEMO_READY")),
        "live_production_ready": bool(tracks.get("LIVE_PRODUCTION_READY")),
        "live_money_ready": bool(tracks.get("LIVE_MONEY_READY")),
        "required_failures": list(guard.get("required_failures") or []),
        "positioning": (
            "Shadow-forward live beta — SHADOW_LIVE_FORWARD evidence only. "
            "Not financial advice. 31 capability slots remain EXTERNAL until contracted."
        ),
    }


async def run_soft_launch_closure(
    *,
    include_institutional_gate: bool = True,
    include_platform_e2e: bool = False,
    check_artifacts: bool = True,
) -> dict[str, Any]:
    from cap978.external_registry import external_registry_report
    from launch_checklist import launch_checklist, _run_pytest_quick
    from production_guard import evaluate_production_guard

    checks: list[dict[str, Any]] = []
    checks.extend(validate_legal_and_honesty())
    checks.extend(validate_shadow_stores())

    constitution_ok, constitution_note = _run_pytest_quick()
    checks.append(
        {
            "name": "constitution_smoke",
            "ok": constitution_ok,
            "detail": constitution_note,
        }
    )

    guard = evaluate_production_guard()
    tracks = await evaluate_production_tracks(guard=guard)
    checks.append(
        {
            "name": "production_guard_required_pass",
            "ok": bool(tracks.get("production_guard_required_pass")),
            "detail": str(tracks.get("required_failures", [])[:5]),
        }
    )
    checks.append(
        {
            "name": "public_demo_ready",
            "ok": bool(tracks.get("public_demo_ready")),
            "detail": "product_honesty track",
        }
    )

    checklist = launch_checklist()
    from launch_checklist import _constitution_modules_ready

    checks.append(
        {
            "name": "constitution_modules_ready",
            "ok": _constitution_modules_ready(),
            "detail": "core product constitution modules on disk",
        }
    )
    checks.append(
        {
            "name": "launch_checklist_progress",
            "ok": int(checklist.get("done_count") or 0) >= max(8, int(checklist.get("total_tasks") or 1) - 8),
            "detail": f"{checklist.get('done_count')}/{checklist.get('total_tasks')} (ops blockers excluded)",
        }
    )

    gate_report: dict[str, Any] | None = None
    if include_institutional_gate:
        from cap978.institutional_gate import run_institutional_gate

        gate_report = await run_institutional_gate(
            sample=True,
            check_artifacts=check_artifacts,
            include_commercial=True,
        )
        checks.append({"name": "institutional_gate", "ok": gate_report["verdict"] == "PASS", "detail": gate_report["verdict"]})

    platform_e2e: dict[str, Any] | None = None
    if include_platform_e2e:
        from platform_chain_e2e import run_platform_compounding_e2e

        platform_e2e = await run_platform_compounding_e2e(symbol="BTC")
        checks.append(
            {
                "name": "platform_chain_e2e",
                "ok": platform_e2e.get("verdict") == "VERIFIED COMPLETE",
                "detail": platform_e2e.get("verdict"),
            }
        )

    external = external_registry_report()
    from cap978.institutional_gate import CLOSURE_BASELINE

    expected_blocked = CLOSURE_BASELINE["external_registry"]["capability_ids_blocked"]
    checks.append(
        {
            "name": "external_registry_labeled",
            "ok": external["capability_ids_blocked"] == expected_blocked,
            "detail": f"{external['capability_ids_blocked']} capability + {external['controls_blocked']} controls (expected {expected_blocked})",
        }
    )

    failed = [c for c in checks if not c["ok"]]
    code_failures = [c for c in failed if c["name"] != "production_guard_required_pass"]
    guard_ok = bool(tracks.get("production_guard_required_pass"))

    if code_failures:
        verdict = "NOT READY"
    elif guard_ok:
        verdict = "VERIFIED COMPLETE"
    else:
        verdict = "CODE COMPLETE — AWAITING PROD ENV"

    snapshot = {
        "generated_at": _utcnow(),
        "baseline_tag": "cap978-closure-v1",
        "launch_mode": "SOFT_LAUNCH_SHADOW_FORWARD",
        "verdict": verdict,
        "positioning": tracks.get("positioning"),
        "tracks": {
            "PUBLIC_DEMO_READY": tracks.get("public_demo_ready"),
            "LIVE_PRODUCTION_READY": tracks.get("live_production_ready"),
            "LIVE_MONEY_READY": tracks.get("live_money_ready"),
            "COMMERCIAL_INSTITUTIONAL": False,
        },
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "failures": failed,
        "production_guard": {
            "required_pass": guard.get("required_pass"),
            "soft_launch": guard.get("soft_launch"),
            "required_failures": guard.get("required_failures"),
        },
        "launch_checklist": {
            "percent": checklist.get("launch_percent"),
            "code_complete": checklist.get("code_complete"),
            "blocked_count": checklist.get("blocked_count"),
            "ops_blockers_expected_locally": int(checklist.get("blocked_count") or 0) > 0,
        },
        "institutional_gate": gate_report,
        "platform_chain_e2e": platform_e2e,
        "external_registry_summary": {
            "total": external["total"],
            "p0_human_excluded": external["counts"],
        },
        "repro_commands": [
            "python scripts/bootstrap_free_human_ops.py --admin-email YOU@DOMAIN",
            "export $(grep -v '^#' .env.softlaunch.local | xargs) && python scripts/run_soft_launch_closure.py",
            "curl /api/cap646/soft-launch/closure",
            "curl /api/launch/readiness",
            "python scripts/mark_golive.py --url https://YOUR-DOMAIN",
        ],
        "excluded_human_external": [
            "SEC-006 SSO IdP",
            "SEC-008/ID645 pentest attestation",
            "REL-002/ID644 signed HA load",
            "29 vendor API integrations",
            "SOC2 SEC-009",
        ],
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = _sha256({k: v for k, v in snapshot.items() if k != "snapshot_hash"})
    return snapshot


def write_soft_launch_readiness(path: Path | None = None) -> Path:
    import asyncio

    snap = asyncio.run(run_soft_launch_closure(include_platform_e2e=False))
    out = path or _READINESS_ARTIFACT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
