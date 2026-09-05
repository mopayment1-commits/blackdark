"""Batch06 acceptance contract — 50 IDs semantic rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch06_ids import BATCH06_MANIFEST_IDS  # noqa: E402


@pytest.fixture(scope="module")
def acceptance_doc() -> dict:
    path = ROOT / "docs/BATCH06_ACCEPTANCE_251_300.json"
    if not path.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts/generate_batch06_acceptance_251_300.py")], cwd=ROOT, check=True)
    return json.loads(path.read_text(encoding="utf-8"))


def test_acceptance_covers_251_300(acceptance_doc: dict):
    ids = {r["capability_id"] for r in acceptance_doc["rows"]}
    assert ids == set(range(251, 301))


@pytest.mark.parametrize("capability_id", sorted(BATCH06_MANIFEST_IDS))
def test_each_row_has_semantic_rules(acceptance_doc: dict, capability_id: int):
    row = next(r for r in acceptance_doc["rows"] if r["capability_id"] == capability_id)
    rules = row["domain_rules"]
    assert len(rules) >= 3
    fields = {r["field"] for r in rules}
    assert "success" in fields or any("ok" in f for f in fields)
    assert any(r["field"] == "surface" for r in rules)
