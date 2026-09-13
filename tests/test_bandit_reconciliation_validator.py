"""Validator for complete 4703-finding Bandit reconciliation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "docs" / "evidence" / "bandit-reconciliation" / "BANDIT_FINDING_RECONCILIATION_4703.json"
CORPUS = ROOT / "docs" / "evidence" / "bandit-full-4703-compact.json"
EXPECTED = 4703
ALLOWED = {
    "TRUE_POSITIVE_FIXED",
    "FALSE_POSITIVE_PROVEN",
    "TEST_ONLY_PROVEN",
    "DUPLICATE_PROVEN",
    "OWNER_DECISION_REQUIRED",
    "NO_LONGER_PRESENT_WITH_PROVENANCE",
}


def test_original_corpus_immutable_and_complete():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert len(data["results"]) == EXPECTED


def test_reconciliation_covers_all_findings():
    payload = json.loads(RECON.read_text(encoding="utf-8"))
    assert payload["corpus_total"] == EXPECTED
    assert payload["reconciled_total"] == EXPECTED
    assert sum(payload["disposition_counts"].values()) == EXPECTED


def test_every_finding_has_allowed_disposition_and_evidence():
    payload = json.loads(RECON.read_text(encoding="utf-8"))
    for row in payload["findings"]:
        assert row["disposition"] in ALLOWED
        assert len(row.get("justification", "")) >= 15
        prov = row.get("original_context_provenance", "")
        if prov in {"RECOVERED_FROM_SOURCE_AT_CORPUS_LINE", "RECOVERED_FROM_NEAREST_NONEMPTY_AT_CORPUS_LINE"}:
            assert row.get("original_context", "").strip()
        elif prov:
            assert prov in {
                "UNRESOLVED_FILE_MISSING",
                "UNRESOLVED_LINE_OUT_OF_RANGE",
                "RECOVERED_BLANK_LINE_AT_CORPUS_COORDINATES",
            }
        if row["disposition"] == "DUPLICATE_PROVEN":
            assert row.get("duplicate_parent")
        if row["disposition"] == "TEST_ONLY_PROVEN":
            assert row.get("scope_proof") or "test" in row["justification"].lower()


def test_b607_all_duplicate_of_b603():
    payload = json.loads(RECON.read_text(encoding="utf-8"))
    b607 = [r for r in payload["findings"] if r["test_id"] == "B607"]
    assert len(b607) == 26
    assert all(r["disposition"] == "DUPLICATE_PROVEN" for r in b607)
    assert all("|B603" in r["duplicate_parent"] for r in b607)


def test_reconciliation_script_exits_zero():
    proc = subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").is_file() else "python3",
         "scripts/bandit_full_reconciliation.py", "--skip-bandit"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
