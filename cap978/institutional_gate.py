"""CAP978 institutional gate — invariant checks for DD/procurement and CI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cap646.catalog import EXTERNAL_IDS as BASE_EXTERNAL_IDS
from cap646.waves import EXTERNAL_EVIDENCE_SLOTS, SIGNED_INFRA_SLOTS
from cap978.catalog import EXTENSION_EXTERNAL_IDS, catalog_by_id, load_catalog
from cap978.external_registry import external_registry_report

_ROOT = Path(__file__).resolve().parent.parent
_EVIDENCE_SNAPSHOT = _ROOT / "docs" / "cap978" / "EVIDENCE_ROOM_SNAPSHOT.json"
_EXTERNAL_REGISTRY = _ROOT / "docs" / "cap978" / "EXTERNAL_REGISTRY.json"
_COMMERCIAL_CHECKLIST = _ROOT / "docs" / "cap978" / "COMMERCIAL_LAUNCH_CHECKLIST.json"

# Frozen internal-closure baseline (cap978-closure-v1). Count drift fails the gate.
CLOSURE_BASELINE = {
    "verdict": "VERIFIED COMPLETE",
    "total": 978,
    "cap978_counts": {
        "VERIFIED_COMPLETE": 938,
        "CANONICALLY_COVERED": 37,
        "EXTERNAL_BLOCKED": 2,
        "EXTERNAL_EVIDENCE_REQUIRED": 1,
    },
    "extension_counts": {
        "VERIFIED_COMPLETE": 329,
        "CANONICALLY_COVERED": 1,
        "EXTERNAL_BLOCKED": 2,
    },
    "governing_controls": {
        "VERIFIED_COMPLETE": 38,
        "EXTERNAL_BLOCKED": 4,
    },
    "external_registry": {
        "total": 33,
        "capability_ids_blocked": 31,
        "controls_blocked": 2,
    },
    "internal_incomplete": {
        "FUNCTIONALLY_INCOMPLETE": 0,
        "INTERNAL_PARTIAL": 0,
        "INTERNAL_NOT_IMPLEMENTED": 0,
    },
}

def _fail(checks: list[dict[str, Any]], name: str, detail: str) -> None:
    checks.append({"name": name, "ok": False, "detail": detail})


def _ok(checks: list[dict[str, Any]], name: str, detail: str = "") -> None:
    checks.append({"name": name, "ok": True, "detail": detail})


def validate_catalog_integrity() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    rows = load_catalog()
    if len(rows) != 978:
        _fail(checks, "catalog_total", f"expected 978 rows, got {len(rows)}")
    else:
        _ok(checks, "catalog_total", "978 capabilities")

    ids = [int(r["id"]) for r in rows]
    if ids[0] != 1 or ids[-1] != 978:
        _fail(checks, "catalog_bounds", f"bounds {ids[0]}..{ids[-1]}")
    else:
        _ok(checks, "catalog_bounds")

    if ids != list(range(1, 979)):
        _fail(checks, "catalog_contiguous", "non-contiguous capability ids")
    else:
        _ok(checks, "catalog_contiguous")

    ext = [r for r in rows if r.get("scope") == "extension_647_978"]
    if len(ext) != 332:
        _fail(checks, "extension_total", f"expected 332 extension rows, got {len(ext)}")
    else:
        _ok(checks, "extension_total")
    return checks


def validate_external_registry_integrity() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    report = external_registry_report()
    rows = report["rows"]

    expected_cap_ids = set(BASE_EXTERNAL_IDS) | set(EXTENSION_EXTERNAL_IDS) | set(EXTERNAL_EVIDENCE_SLOTS) | set(SIGNED_INFRA_SLOTS)
    registry_cap_ids = {r["id"] for r in rows if isinstance(r.get("id"), int)}
    if registry_cap_ids != expected_cap_ids:
        missing = sorted(expected_cap_ids - registry_cap_ids)
        extra = sorted(registry_cap_ids - expected_cap_ids)
        _fail(
            checks,
            "external_registry_capability_ids",
            f"missing={missing[:10]} extra={extra[:10]}",
        )
    else:
        _ok(checks, "external_registry_capability_ids", f"{len(expected_cap_ids)} capability slots")

    control_ids = {r["id"] for r in rows if isinstance(r.get("id"), str)}
    if control_ids != {"SEC-008", "SEC-009"}:
        _fail(checks, "external_registry_controls", f"controls={sorted(control_ids)}")
    else:
        _ok(checks, "external_registry_controls")

    if report["capability_ids_blocked"] != CLOSURE_BASELINE["external_registry"]["capability_ids_blocked"]:
        _fail(checks, "external_registry_cap_count", str(report["capability_ids_blocked"]))
    else:
        _ok(checks, "external_registry_cap_count")

    if not all(str(r.get("internal_action", "")).startswith("none") for r in rows):
        _fail(checks, "external_registry_no_false_internal", "internal_action must start with none")
    else:
        _ok(checks, "external_registry_no_false_internal")

    for cid in sorted(expected_cap_ids):
        if cid not in catalog_by_id():
            _fail(checks, "external_catalog_entries", f"missing catalog row for {cid}")
            break
    else:
        _ok(checks, "external_catalog_entries")
    return checks


def validate_closure_invariants(closure: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    cap = closure.get("cap978") or {}

    for key, expected in CLOSURE_BASELINE["internal_incomplete"].items():
        actual = cap.get(key, -1)
        if actual != expected:
            _fail(checks, f"internal_{key.lower()}", f"expected {expected}, got {actual}")
        else:
            _ok(checks, f"internal_{key.lower()}")

    if closure.get("verdict") != CLOSURE_BASELINE["verdict"]:
        _fail(checks, "closure_verdict", str(closure.get("verdict")))
    else:
        _ok(checks, "closure_verdict")

    counts = cap.get("counts") or {}
    for key, expected in CLOSURE_BASELINE["cap978_counts"].items():
        if counts.get(key, 0) != expected:
            _fail(checks, f"cap978_count_{key}", f"expected {expected}, got {counts.get(key, 0)}")
        else:
            _ok(checks, f"cap978_count_{key}")

    ext = cap.get("extension_647_978") or {}
    for key, expected in CLOSURE_BASELINE["extension_counts"].items():
        if ext.get(key, 0) != expected:
            _fail(checks, f"extension_count_{key}", f"expected {expected}, got {ext.get(key, 0)}")
        else:
            _ok(checks, f"extension_count_{key}")

    controls = (closure.get("governing_controls") or {}).get("counts") or {}
    for key, expected in CLOSURE_BASELINE["governing_controls"].items():
        if controls.get(key, 0) != expected:
            _fail(checks, "governing_controls", f"{key} expected {expected}, got {controls.get(key, 0)}")
            break
    else:
        _ok(checks, "governing_controls")

    chain = closure.get("data_platform_chain") or {}
    if chain.get("verdict") != "VERIFIED_COMPLETE" or not chain.get("internal_closure"):
        _fail(checks, "platform_chain", str(chain.get("verdict")))
    else:
        _ok(checks, "platform_chain")

    incomplete = cap.get("incomplete_sample") or []
    if incomplete:
        _fail(checks, "no_internal_incomplete_ids", str(incomplete[:10]))
    else:
        _ok(checks, "no_internal_incomplete_ids")
    return checks


def validate_committed_artifacts(*, snapshot_path: Path | None = None, registry_path: Path | None = None) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    snap_path = snapshot_path or _EVIDENCE_SNAPSHOT
    reg_path = registry_path or _EXTERNAL_REGISTRY

    if not snap_path.is_file():
        _fail(checks, "evidence_snapshot_exists", str(snap_path))
    else:
        _ok(checks, "evidence_snapshot_exists")
        committed = json.loads(snap_path.read_text(encoding="utf-8"))
        live_reg = external_registry_report()

        if committed.get("verdict") != CLOSURE_BASELINE["verdict"]:
            _fail(checks, "snapshot_verdict", str(committed.get("verdict")))
        else:
            _ok(checks, "snapshot_verdict")

        for section, baseline in (
            ("internal_closure", CLOSURE_BASELINE["internal_incomplete"]),
            ("cap978_counts", CLOSURE_BASELINE["cap978_counts"]),
            ("extension_counts", CLOSURE_BASELINE["extension_counts"]),
        ):
            actual = committed.get(section) or {}
            drift = {k: actual.get(k) for k in baseline if actual.get(k) != baseline[k]}
            if drift:
                _fail(checks, f"snapshot_{section}", str(drift))
            else:
                _ok(checks, f"snapshot_{section}")

        gov = committed.get("governing_controls") or {}
        gov_counts = gov.get("counts") or {}
        if gov_counts != CLOSURE_BASELINE["governing_controls"]:
            _fail(checks, "snapshot_governing_controls", str(gov_counts))
        else:
            _ok(checks, "snapshot_governing_controls")

        ext_summary = committed.get("external_registry_summary") or {}
        expected_summary = {"total": live_reg["total"], "counts": live_reg["counts"]}
        if ext_summary != expected_summary:
            _fail(checks, "snapshot_external_summary", str(ext_summary))
        else:
            _ok(checks, "snapshot_external_summary")

    if not reg_path.is_file():
        _fail(checks, "external_registry_file_exists", str(reg_path))
    else:
        _ok(checks, "external_registry_file_exists")
        committed_reg = json.loads(reg_path.read_text(encoding="utf-8"))
        live_reg = external_registry_report()
        for key in ("total", "counts", "capability_ids_blocked", "controls_blocked", "policy"):
            if committed_reg.get(key) != live_reg.get(key):
                _fail(checks, f"registry_field_{key}", "committed artifact drift")
        if not any(c["name"].startswith("registry_field_") and not c["ok"] for c in checks):
            _ok(checks, "registry_invariants")

        committed_ids = sorted(
            [r["id"] for r in committed_reg.get("rows", [])],
            key=lambda x: (isinstance(x, str), x),
        )
        live_ids = sorted(
            [r["id"] for r in live_reg.get("rows", [])],
            key=lambda x: (isinstance(x, str), x),
        )
        if committed_ids != live_ids:
            _fail(checks, "registry_row_ids", "row id set drift")
        else:
            _ok(checks, "registry_row_ids")
    return checks


def commercial_launch_checklist() -> dict[str, Any]:
    rows = external_registry_report()["rows"]
    priority_map = {
        "SEC-006": "P0",
        "SEC-008": "P0",
        "SEC-009": "P1",
        "REL-002": "P0",
        644: "P0",
        645: "P0",
        672: "P1",
        674: "P1",
        702: "P1",
        690: "P2",
        691: "P2",
    }

    items: list[dict[str, Any]] = []
    for row in rows:
        rid = row["id"]
        items.append(
            {
                **row,
                "priority": priority_map.get(rid, "P2"),
                "owner": "external",
                "status": "open",
                "blocks_commercial_launch": priority_map.get(rid, "P2") == "P0",
            }
        )

    p0 = [i for i in items if i["priority"] == "P0"]
    return {
        "baseline_tag": "cap978-closure-v1",
        "internal_closure_complete": True,
        "commercial_launch_ready": False,
        "total_external_items": len(items),
        "p0_blockers": len(p0),
        "p0_ids": [i["id"] for i in p0],
        "policy": "Commercial launch requires closing P0 external items; P1/P2 are tiered post-pilot.",
        "items": items,
    }


async def run_institutional_gate(
    *,
    sample: bool = False,
    check_artifacts: bool = True,
    include_commercial: bool = True,
) -> dict[str, Any]:
    from cap978.closure import institutional_closure_978

    checks: list[dict[str, Any]] = []
    checks.extend(validate_catalog_integrity())
    checks.extend(validate_external_registry_integrity())
    if check_artifacts:
        checks.extend(validate_committed_artifacts())

    closure = await institutional_closure_978(sample=sample)
    if sample:
        # Sample mode validates structure, not frozen baseline counts.
        cap = closure.get("cap978") or {}
        for key in CLOSURE_BASELINE["internal_incomplete"]:
            actual = cap.get(key, -1)
            if actual != 0:
                _fail(checks, f"sample_internal_{key.lower()}", f"got {actual}")
            else:
                _ok(checks, f"sample_internal_{key.lower()}")
        if cap.get("incomplete_sample"):
            _fail(checks, "sample_incomplete_ids", str(cap["incomplete_sample"][:10]))
        else:
            _ok(checks, "sample_incomplete_ids")
    else:
        checks.extend(validate_closure_invariants(closure))

    failed = [c for c in checks if not c["ok"]]
    result: dict[str, Any] = {
        "verdict": "PASS" if not failed else "FAIL",
        "mode": "sample" if sample else "full",
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "failures": failed,
        "closure_verdict": closure.get("verdict"),
        "baseline_tag": "cap978-closure-v1",
    }
    if include_commercial:
        result["commercial_launch"] = commercial_launch_checklist()
    return result
