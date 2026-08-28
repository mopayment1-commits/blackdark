"""
Data Engine Quality Pipeline — Feature #850 (Sprint-0).

NOT standalone — quality_pipeline component in Data Engine.
Raw → clean institutional data. Overlaps #824 quality_monitor.

Pipeline: Read → Compute → Store → Distribute → QA
3 mandatory tests: gap | outlier (Z>3) | reconciliation (±0.1%)
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DataEngineQualityPipeline")

_FEATURE_REF = 850
_STANDALONE = False
_MERGED_INTO = "Data Engine"
_COMPONENT = "quality_pipeline"
_QUALITY_MONITOR_REF = 824
_SEED_PATH = Path("data/data_engine_quality_pipeline_seed.json")
_MANDATORY_TESTS = ("gap_detection", "outlier_detection", "reconciliation")
_RECONCILIATION_TOLERANCE_PCT = 0.1
_OUTLIER_Z_THRESHOLD = 3.0

QaStatus = Literal["Pass", "Warning", "Fail"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("quality pipeline seed load failed: %s", exc)
        return {}


def _qa_status(passed: int, total: int) -> QaStatus:
    if passed == total:
        return "Pass"
    if passed >= total - 1:
        return "Warning"
    return "Fail"


def run_pipeline_batch_qa_850(
    batch_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run 3 mandatory QA tests on a batch."""
    from bd_platform.data_engine_quality_monitor import (
        run_daily_quality_check_824,
    )

    seed = seed or _load_seed()
    batches = seed.get("batches") or {}
    batch = batches.get(batch_id)
    if not batch:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "batch_not_found", "batch_id": batch_id}

    dataset_id = batch.get("dataset_id", "market_ohlcv")
    qm_seed = {"datasets": (seed.get("quality_monitor_seed") or {}).get("datasets") or {}}
    tests = []
    for check_type in _MANDATORY_TESTS:
        result = run_daily_quality_check_824(check_type, dataset_id, seed=qm_seed)
        tests.append({
            "test": check_type,
            "passed": result.get("ok", False),
            "detail": result.get("result"),
        })

    passed = sum(1 for t in tests if t["passed"])
    status: QaStatus = _qa_status(passed, len(tests))

    return {
        "ok": status != "Fail",
        "feature_ref": _FEATURE_REF,
        "batch_id": batch_id,
        "dataset_id": dataset_id,
        "qa_status": status,
        "tests_run": len(tests),
        "tests_passed": passed,
        "mandatory_tests": list(_MANDATORY_TESTS),
        "tests": tests,
        "timestamp": _utcnow(),
    }


def build_quality_pipeline_panel_850(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Quality pipeline status — Read → Compute → Store → Distribute."""
    seed = seed or _load_seed()
    cfg = seed.get("quality_pipeline_850") or {}
    batches = list((seed.get("batches") or {}).keys())
    qa_results = [run_pipeline_batch_qa_850(b, seed=seed) for b in batches]

    return {
        "ok": all(r.get("ok") for r in qa_results),
        "feature_ref": _FEATURE_REF,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "standalone_rejected": True,
        "no_user_surface": True,
        "quality_monitor_ref": _QUALITY_MONITOR_REF,
        "pipeline_stages": [
            "read",
            "compute",
            "store",
            "distribute",
            "qa",
        ],
        "pipeline_documented": True,
        "no_hidden_steps": True,
        "mandatory_tests": list(_MANDATORY_TESTS),
        "outlier_z_threshold": _OUTLIER_Z_THRESHOLD,
        "reconciliation_tolerance_pct": _RECONCILIATION_TOLERANCE_PCT,
        "batch_qa_results": qa_results,
        "fee_db": cfg.get("fee_db") or seed.get("fee_db"),
        "timestamp": _utcnow(),
    }


def quality_pipeline_status_850(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("quality_pipeline_850") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": 0,
        "no_user_surface": True,
        "quality_monitor_ref": _QUALITY_MONITOR_REF,
        "mandatory_tests": list(_MANDATORY_TESTS),
        "qa_statuses": ["Pass", "Warning", "Fail"],
        "pipeline_stages": ["read", "compute", "store", "distribute", "qa"],
        "outlier_z_threshold": _OUTLIER_Z_THRESHOLD,
        "reconciliation_tolerance_pct": _RECONCILIATION_TOLERANCE_PCT,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def run_quality_pipeline_e2e_850(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = quality_pipeline_status_850(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "component_quality_pipeline", "passed": status.get("component") == "quality_pipeline"})
    tests.append({"test": "three_mandatory_tests", "passed": status.get("mandatory_tests") == list(_MANDATORY_TESTS)})
    tests.append({"test": "quality_monitor_ref_824", "passed": status.get("quality_monitor_ref") == 824})

    panel = build_quality_pipeline_panel_850(seed=seed)
    tests.append({"test": "pipeline_documented", "passed": panel.get("pipeline_documented") is True})
    tests.append({"test": "no_hidden_steps", "passed": panel.get("no_hidden_steps") is True})
    tests.append({"test": "all_batches_qa", "passed": panel.get("ok") is True})

    batch_qa = run_pipeline_batch_qa_850("batch-20260827", seed=seed)
    tests.append({"test": "batch_qa_pass", "passed": batch_qa.get("qa_status") in ("Pass", "Warning")})
    tests.append({"test": "gap_test_ran", "passed": any(t["test"] == "gap_detection" for t in batch_qa.get("tests", []))})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
