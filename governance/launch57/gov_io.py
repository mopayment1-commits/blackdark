"""Bounded filesystem writes for Launch-57 governance artifact generators (S2083)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from path_safety import ensure_under, write_json_artifact, write_public_text_lines

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


def write_artifact_json(path: Path, document: object) -> None:
    """Write JSON closure artifacts only under the repository root (coerced, no raw blob)."""
    write_json_artifact(path, document, base=PROJECT_ROOT)


def write_artifact_lines(path: Path, lines: Sequence[str]) -> None:
    """Write markdown/text closure artifacts from discrete public-audit lines (not a free blob)."""
    write_public_text_lines(path, lines, base=PROJECT_ROOT)
