#!/usr/bin/env python3
"""Regenerate requirements.lock.txt and requirements-prod.lock.txt from the active env."""

from __future__ import annotations

import re
import subprocess  # nosec B404 — intentional admin tooling
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _parse_names(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"([A-Za-z0-9_.-]+)(\[[^\]]+\])?", s)
        if m:
            out.append((m.group(1), m.group(2) or ""))
    return out


def _freeze_map() -> dict[str, str]:
    raw = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)  # nosec B603 — fixed argv, shell=False, no user input
    fmap: dict[str, str] = {}
    for line in raw.splitlines():
        if "==" not in line or line.startswith("-e"):
            continue
        name, ver = line.split("==", 1)
        key = name.lower().replace("_", "-")
        fmap[key] = ver
        fmap[name.lower()] = ver
    return fmap


def _write_lock(src: Path, dst: Path) -> None:
    fmap = _freeze_map()
    lines = [
        "# Locked for Sonar S8544 / reproducible CI+Docker — regenerate: python scripts/lock_requirements.py\n"
    ]
    missing: list[str] = []
    for name, extras in _parse_names(src):
        key = name.lower().replace("_", "-")
        ver = fmap.get(key) or fmap.get(name.lower())
        if not ver:
            missing.append(name)
            continue
        lines.append(f"{name}{extras}=={ver}\n")
    dst.write_text("".join(lines), encoding="utf-8")
    if missing:
        raise SystemExit(f"Missing installed versions for: {', '.join(missing)}")
    print(f"Wrote {dst.relative_to(ROOT)} ({len(lines) - 1} pins)")


def main() -> int:
    _write_lock(ROOT / "requirements.txt", ROOT / "requirements.lock.txt")
    _write_lock(ROOT / "requirements-prod.txt", ROOT / "requirements-prod.lock.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
