"""Contract tests for Batch05 Item 7 final institutional freeze."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/generate_batch05_item7_final_freeze.py"
FREEZE = ROOT / "docs/BATCH05_ITEM7_FINAL_INSTITUTIONAL_FREEZE.json"
MATRIX = ROOT / "docs/BATCH05_REMAINING_BLOCKERS_MATRIX.json"
ARABIC = (
    "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
    "لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%."
)


@pytest.fixture(scope="module")
def freeze_doc() -> dict:
    if not FREEZE.is_file():
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    return json.loads(FREEZE.read_text(encoding="utf-8"))


def test_item7_locks(freeze_doc: dict):
    assert freeze_doc["pa_elevated_count"] == 0
    assert freeze_doc["production_aligned_count"] == 0
    assert freeze_doc["batch05_independent"] == 0
    assert freeze_doc["progress_826"] == 179
    assert freeze_doc["sequence_item"] == 7
    assert "LOCAL_GOVERNANCE_COMPLETE" in freeze_doc["not_claimed"]
    assert freeze_doc["phase_statement_ar"] == ARABIC


def test_item7_stamped_artifacts(freeze_doc: dict):
    acceptance = json.loads((ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json").read_text(encoding="utf-8"))
    rtm = json.loads((ROOT / "docs/BATCH05_RTM_201_250.json").read_text(encoding="utf-8"))
    pent = json.loads((ROOT / "docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json").read_text(encoding="utf-8"))
    for doc in (acceptance, rtm, pent):
        assert doc["phase_statement_ar"] == ARABIC
        assert doc["item7_final_freeze"]["pa_elevated_count"] == 0
        assert doc["item7_final_freeze"]["items_1_6_complete"] is True


def test_blockers_matrix(freeze_doc: dict):
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert matrix["absolute_locks"]["pa_elevated_count"] == 0
    assert matrix["summary"]["strangler_pa_eligible_now"] == 0
    assert len(matrix["per_id_strangler_readiness"]) == 43
    assert all(not r["may_elevate_pa"] for r in matrix["per_id_strangler_readiness"])
    assert any(b["status"] == "AWAITING_DEPLOY" for b in matrix["hard_blockers"])
    assert any(b["status"] == "NOT_STARTED" for b in matrix["hard_blockers"])
