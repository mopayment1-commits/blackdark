"""Bounded filesystem writes for Launch-57 governance artifact generators (S2083)."""

from __future__ import annotations

import re
from pathlib import Path

from path_safety import ensure_under

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOV_DIR = ensure_under(PROJECT_ROOT / "governance" / "launch57", PROJECT_ROOT)

_SAFE_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(json|md|txt)$")


def artifact_path(directory: Path, filename: str) -> Path:
    """Resolve a fixed artifact filename under a known governance output directory."""
    name = str(filename).strip()
    if not _SAFE_ARTIFACT_NAME.fullmatch(name):
        raise ValueError(f"Unsafe governance artifact name: {filename!r}")
    base = ensure_under(directory.resolve(), PROJECT_ROOT)
    return ensure_under(base / name, PROJECT_ROOT)


def write_artifact(path: Path, content: str) -> None:
    """Write UTF-8 text only under the repository root."""
    safe = ensure_under(path.resolve(), PROJECT_ROOT)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(content, encoding="utf-8")
