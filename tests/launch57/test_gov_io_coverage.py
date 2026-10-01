"""Behavioral coverage for governance.launch57.gov_io."""

from __future__ import annotations

import json
from pathlib import Path

from governance.launch57.gov_io import GOV_DIR, artifact_path, write_artifact_json, write_artifact_lines


def test_gov_io_write_helpers():
    json_path = artifact_path(GOV_DIR, "test-gov-io-artifact.json")
    md_path = artifact_path(GOV_DIR, "test-gov-io-report.md")
    try:
        write_artifact_json(json_path, {"ok": True})
        assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
        write_artifact_lines(md_path, ["# title", "", "body"])
        assert "# title" in md_path.read_text(encoding="utf-8")
    finally:
        json_path.unlink(missing_ok=True)
        md_path.unlink(missing_ok=True)


def test_artifact_path_rejects_unsafe_name():
    try:
        artifact_path(GOV_DIR, "../escape.json")
    except ValueError as exc:
        assert "Unsafe" in str(exc)
    else:
        raise AssertionError("expected ValueError")
