#!/usr/bin/env python3
"""Verify Adaptive v4 baseline freeze integrity and detect semantic regression."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE"
BASELINE_PATH = OUT_DIR / "ADAPTIVE_V4_FINAL_LOCAL_BASELINE.json"
MANIFEST_PATH = OUT_DIR / "ADAPTIVE_V4_EVIDENCE_MANIFEST.json"
CLOSURE_PATH = ROOT / "ADAPTIVE_V4_FINAL_LOCAL_CLOSURE.md"
REOPEN_PATH = OUT_DIR / "ADAPTIVE_V4_REOPEN_CONDITIONS.md"
SPEC_PATH = ROOT / "governing-sources-population/BLACKDARK_Adaptive_Intelligence_Experience_Institutional_Final_v4_CURSOR (1).md"

EPHEMERAL_ARTIFACTS = {
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/FINAL_GATE_ASSERTIONS.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/WORKING_TREE_RECONCILIATION.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_LOCAL_PERFORMANCE_EVIDENCE.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_SECURITY_VERIFICATION_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ACCESSIBILITY_LOCAL_VERIFICATION_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ACCESSIBILITY_LOCAL_VERIFICATION_REPORT.md",
}

PARALLEL_SSOT_PATHS = (
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE_ALT",
    "bd_platform/adaptive_intelligence_ssot_parallel",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_show_blob(sha: str, rel: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{sha}:{rel}"],
        cwd=ROOT,
        capture_output=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def _verify_closure_infrastructure(errors: list[str]) -> dict:
    for path in (BASELINE_PATH, MANIFEST_PATH, CLOSURE_PATH, REOPEN_PATH, SPEC_PATH):
        if not path.is_file():
            _fail(errors, f"missing closure artifact: {path.relative_to(ROOT)}")
    if errors:
        return {}
    return _load_json(BASELINE_PATH)


def _verify_spec_identity(baseline: dict, errors: list[str]) -> None:
    expected = baseline.get("specification")
    if not SPEC_PATH.is_file():
        _fail(errors, "authoritative specification file missing")
        return
    if expected and expected not in str(SPEC_PATH):
        _fail(errors, f"spec identity mismatch: expected {expected}")


def _verify_manifest_hashes(baseline: dict, manifest: dict, errors: list[str]) -> None:
    baseline_sha = baseline.get("baseline_sha_short") or baseline.get("baseline_sha", "")[:8]
    for _name, entry in manifest.get("artifacts", {}).items():
        rel = entry["path"]
        path = ROOT / rel
        if not path.is_file():
            _fail(errors, f"evidence artifact missing: {rel}")
            continue
        if entry.get("ephemeral_regeneration_allowed") or rel in EPHEMERAL_ARTIFACTS:
            continue
        frozen = entry.get("sha256")
        if not frozen:
            continue
        blob = _git_show_blob(baseline_sha, rel)
        if blob is None:
            current = _sha256(path)
        else:
            current = hashlib.sha256(blob).hexdigest()
        if current != frozen:
            _fail(errors, f"frozen evidence hash mismatch for {rel}")


def _verify_semantic_invariants(baseline: dict, errors: list[str]) -> None:
    atomic_path = OUT_DIR / "PRIMARY_TO_ATOMIC_REQUIREMENT_MAPPING.json"
    sec_path = OUT_DIR / "ADAPTIVE_V4_SECURITY_VERIFICATION_MATRIX.json"
    a11y_path = OUT_DIR / "ACCESSIBILITY_LOCAL_VERIFICATION_MATRIX.json"
    reg_path = OUT_DIR / "ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json"
    perf_path = OUT_DIR / "ADAPTIVE_V4_LOCAL_PERFORMANCE_EVIDENCE.json"
    risk_path = OUT_DIR / "RESIDUAL_RISK_32_1.json"

    for p in (atomic_path, sec_path, a11y_path, reg_path, perf_path, risk_path):
        if not p.is_file():
            _fail(errors, f"semantic evidence missing: {p.name}")
            return

    atomic = _load_json(atomic_path)
    sec = _load_json(sec_path)
    a11y = _load_json(a11y_path)
    reg = _load_json(reg_path)
    perf = _load_json(perf_path)
    risk = _load_json(risk_path)
    cal = risk.get("calibration_semantics", {})

    min_atomic = baseline.get("atomic_requirement_count", 226)
    if atomic.get("INDEPENDENT_ATOMIC_OBLIGATIONS", 0) < min_atomic:
        _fail(errors, "atomic obligation count regressed below baseline minimum")
    if atomic.get("UNMAPPED_ATOMIC_OBLIGATIONS", 1) != 0:
        _fail(errors, "unmapped atomic obligations detected")
    if atomic.get("UNIMPLEMENTED_LOCAL_ATOMIC_OBLIGATIONS", 1) != 0:
        _fail(errors, "unimplemented local atomic obligations detected")

    if sec.get("UNRESOLVED_LOCAL_ADAPTIVE_SECURITY_FINDINGS", 1) != 0:
        _fail(errors, "unresolved local adaptive security findings")
    if sec.get("SECURITY_LOCAL_VERIFICATION_COMPLETE") is not True:
        _fail(errors, "security local verification no longer complete")
    min_sec = baseline.get("security_findings", {}).get("security_categories_verified", 34)
    if sec.get("SECURITY_CATEGORIES_VERIFIED", 0) < min_sec:
        _fail(errors, "security category verification count regressed")

    if a11y.get("UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS", 1) != 0:
        _fail(errors, "unresolved local accessibility defects")
    if a11y.get("ACCESSIBILITY_LOCAL_INTERACTION_VERIFICATION_COMPLETE") is not True:
        _fail(errors, "accessibility local verification no longer complete")

    if reg.get("FULL_RELEVANT_REGRESSION_GREEN") is not True:
        _fail(errors, "regression status no longer green")
    if reg.get("CHANGED_PRODUCTION_MODULES_WITHOUT_TEST_COVERAGE", 1) != 0:
        _fail(errors, "changed production modules without test coverage")

    if perf.get("status") != "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE":
        _fail(errors, "local performance engineering status regressed")
    if perf.get("PRODUCTION_SLO_EVIDENCE_GATED") is not True:
        _fail(errors, "production SLO gate must remain gated externally")

    if cal.get("FALSE_PRECISION_BLOCKED") is not True:
        _fail(errors, "false precision blocking weakened")
    if cal.get("UNCALIBRATED_NUMERIC_CONFIDENCE_BLOCKED") is not True:
        _fail(errors, "uncalibrated numeric confidence blocking weakened")
    if cal.get("EMPIRICAL_CALIBRATION_EVIDENCE_GATED") is not True:
        _fail(errors, "empirical calibration must remain externally gated")

    ext = baseline.get("accepted_external_gates", [])
    for gate in (
        "LIVE_DEPLOYMENT_GATED",
        "PRODUCTION_SLO_EVIDENCE_GATED",
        "EMPIRICAL_CALIBRATION_EVIDENCE_GATED",
        "EXTERNAL_HUMAN_EVIDENCE_GATED",
    ):
        if gate not in ext:
            _fail(errors, f"accepted external gate missing from baseline record: {gate}")


def _verify_entitlement_and_ssot(errors: list[str]) -> None:
    ent_path = ROOT / "bd_platform/adaptive_intelligence/entitlement_gate.py"
    if not ent_path.is_file():
        _fail(errors, "entitlement_gate.py missing")
        return
    ent_src = ent_path.read_text(encoding="utf-8")
    if "check_adaptive_entitlement" not in ent_src:
        _fail(errors, "entitlement authority entry point removed")

    for rel in PARALLEL_SSOT_PATHS:
        if (ROOT / rel).exists():
            _fail(errors, f"parallel SSOT path detected: {rel}")

    rtm = OUT_DIR / "RTM.json"
    if rtm.is_file():
        data = _load_json(rtm)
        parents = data.get("parents", []) if isinstance(data, dict) else data
        min_parents = 44
        if isinstance(parents, list) and len(parents) < min_parents:
            _fail(errors, "RTM parent control count regressed below baseline minimum")


def main() -> int:
    errors: list[str] = []
    baseline = _verify_closure_infrastructure(errors)
    if not baseline:
        result = {"BASELINE_INTEGRITY_VERIFIED": False, "errors": errors}
        print(json.dumps(result, indent=2))
        return 1

    manifest = _load_json(MANIFEST_PATH)
    _verify_spec_identity(baseline, errors)
    _verify_manifest_hashes(baseline, manifest, errors)
    _verify_semantic_invariants(baseline, errors)
    _verify_entitlement_and_ssot(errors)

    ok = len(errors) == 0
    result = {
        "BASELINE_INTEGRITY_VERIFIED": ok,
        "baseline_sha": baseline.get("baseline_sha_short", "07bb4049"),
        "specification": baseline.get("specification"),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
