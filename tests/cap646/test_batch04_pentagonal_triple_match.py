"""Triple-match guard and pentagonal template integrity for batch04."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PENTAGONAL = ROOT / "docs/BATCH04_PENTAGONAL_TEMPLATE_151_200.json"
ACCEPTANCE = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"
RULE_PROOF = ROOT / "docs/BATCH04_RULE_COUNT_ASSERT_PROOF.txt"


def test_pentagonal_template_exists_and_covers_50():
    assert PENTAGONAL.is_file(), "run scripts/generate_batch04_institutional_pentagonal.py"
    doc = json.loads(PENTAGONAL.read_text(encoding="utf-8"))
    assert doc["batch04_independent"] == 0
    assert doc["progress_826"] == 148
    assert doc["production_aligned_count"] == 0
    assert len(doc["rows"]) == 50


def test_triple_match_per_probe_id():
    pent = json.loads(PENTAGONAL.read_text(encoding="utf-8"))
    acc = {r["capability_id"]: r for r in json.loads(ACCEPTANCE.read_text(encoding="utf-8"))["rows"]}
    for row in pent["rows"]:
        cid = row["capability_id"]
        acceptance_count = len(acc[cid]["domain_rules"])
        er = row["pentagonal"]["external_result_iso29148"]
        assert acceptance_count == len(er["domain_rule_results"]) == er["rules_total"]
        assert er["rules_passed"] == sum(1 for r in er["domain_rule_results"] if r["pass"])
        assert row["closure_status"] != "PRODUCTION-ALIGNED"
        assert row["batch04_independent"] is False


def test_rule_count_proof_file():
    assert RULE_PROOF.is_file()
    text = RULE_PROOF.read_text(encoding="utf-8")
    assert "assert_rule_count_triple_match: end" in text
    assert text.count(" OK") >= 50


@pytest.mark.slow
def test_pentagonal_generator_exit_zero():
  result = subprocess.run(
      [sys.executable, str(ROOT / "scripts/generate_batch04_institutional_pentagonal.py")],
      cwd=ROOT,
      capture_output=True,
      text=True,
      timeout=120,
  )
  assert result.returncode == 0, result.stderr or result.stdout
