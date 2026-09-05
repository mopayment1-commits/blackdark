"""Contract tests for Batch05 Items 2–6 institutional closure artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

from cap646.batch05_strangler_spine import STRANGLER_IMPLEMENTED_IDS  # noqa: E402


def _load_or_generate(script: str, json_path: Path) -> dict:
    if not json_path.is_file():
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)
    return json.loads(json_path.read_text(encoding="utf-8"))


def test_reused_link_partial_disposition():
    doc = _load_or_generate(
        "scripts/generate_batch05_reused_link_partial_disposition.py",
        ROOT / "docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.json",
    )
    assert doc["pa_elevated_count"] == 0
    assert doc["production_aligned_count"] == 0
    by_id = {r["capability_id"]: r for r in doc["rows"]}
    assert by_id[232]["disposition"] == "CLOSED"
    assert by_id[214]["disposition"] == "TOLERATE"
    assert by_id[245]["disposition"] == "TOLERATE"
    assert by_id[232]["facade_probe"]["domain_all_pass"] is True


def test_entitlement_gateway_proof_43_stranglers():
    doc = _load_or_generate(
        "scripts/verify_entitlement_batch05_gateway_proof.py",
        ROOT / "docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json",
    )
    assert doc["all_verified"] is True
    assert doc["strangler_test_case_count"] == 43
    assert set(doc["strangler_capability_ids"]) == STRANGLER_IMPLEMENTED_IDS
    assert doc["production_aligned_count"] == 0


def test_hero_six_final_freeze():
    freeze_path = ROOT / "docs/BATCH05_HERO_SIX_FINAL_FREEZE.json"
    if not freeze_path.is_file():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/generate_batch05_hero_six_final_freeze.py")],
            cwd=ROOT,
            check=True,
        )
    doc = json.loads(freeze_path.read_text(encoding="utf-8"))
    assert doc["freeze_status"] == "FINAL_FREEZE_LOCAL"
    assert doc["heroes_fed_by_batch05"]["direct_strangler_ids"] == []
    assert doc["normalization"]["frozen"] is True
    assert doc["sensitivity"]["frozen"] is True
    assert doc["explainability"]["frozen"] is True


def test_sre_prr_readiness_package_locks():
    doc = json.loads((ROOT / "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json").read_text(encoding="utf-8"))
    assert doc["batch05_independent"] == 0
    assert doc["pa_elevated_count"] == 0
    assert doc["prr_status"] == "SECOND_REVIEW_READY_LOCAL"
    assert "LIVE_READY" in doc["not_claimed"]
