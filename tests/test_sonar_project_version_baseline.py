"""Guard: Sonar Previous-version baseline uses a real projectVersion."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sonar_project_version_file_matches_properties():
    ver = (ROOT / "SONAR_PROJECT_VERSION").read_text(encoding="utf-8").strip()
    assert ver, "SONAR_PROJECT_VERSION must be non-empty"
    assert ver != "not provided"
    # Do not use per-commit SHAs as projectVersion (collapses New Code).
    assert len(ver) < 40
    assert " " not in ver

    props = (ROOT / "sonar-project.properties").read_text(encoding="utf-8")
    line = next(
        (ln for ln in props.splitlines() if ln.startswith("sonar.projectVersion=")),
        "",
    )
    assert line == f"sonar.projectVersion={ver}"


def test_sonar_workflow_passes_project_version():
    wf = (ROOT / ".github/workflows/sonarcloud.yml").read_text(encoding="utf-8")
    assert "SONAR_PROJECT_VERSION" in wf
    assert "sonar.projectVersion=" in wf
    assert "sonar.buildString=" in wf
    # AA must stay disabled operating model.
    assert "AA must stay disabled" in wf
