#!/usr/bin/env python3
"""Generate requirements.hashes.txt / requirements-prod.hashes.txt for Sonar S8544."""

from __future__ import annotations

import json
import subprocess  # nosec B404 — intentional admin tooling
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _resolve(lock_file: Path) -> list[tuple[str, str]]:
    # Private temp file (not a shared world-writable path) — Sonar python:S5443.
    with tempfile.NamedTemporaryFile(
        prefix=f"bd-{lock_file.stem}-",
        suffix=".json",
        delete=False,
    ) as handle:
        report = Path(handle.name)
    try:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--only-binary=:all:",
            "-r",
            str(lock_file),
            "--report",
            str(report),
        ]
        subprocess.check_call(cmd)  # nosec B603 — fixed argv, shell=False, no user input
        data = json.loads(report.read_text(encoding="utf-8"))
    finally:
        report.unlink(missing_ok=True)
    pkgs: list[tuple[str, str]] = []
    for item in data.get("install", []):
        meta = item.get("metadata") or {}
        name = meta.get("name")
        ver = meta.get("version")
        if name and ver:
            pkgs.append((name, ver))
    return pkgs


def _hashes(name: str, version: str) -> list[str]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    seen: set[str] = set()
    out: list[str] = []
    for file_meta in data.get("urls", []):
        if file_meta.get("packagetype") not in {"bdist_wheel", "sdist"}:
            continue
        digest = (file_meta.get("digests") or {}).get("sha256")
        if digest and digest not in seen:
            seen.add(digest)
            out.append(digest)
    if not out:
        raise RuntimeError(f"No hashes for {name}=={version}")
    return out


def _write(lock_file: Path, out_file: Path, title: str) -> None:
    pkgs = _resolve(lock_file)
    lines = [f"# {title}\n", "# Regenerate: python scripts/generate_hash_lock.py\n"]
    for name, ver in sorted(pkgs, key=lambda row: row[0].lower()):
        hashes = _hashes(name, ver)
        lines.append(f"{name}=={ver} \\\n")
        for idx, digest in enumerate(hashes):
            suffix = " \\\n" if idx < len(hashes) - 1 else "\n"
            lines.append(f"    --hash=sha256:{digest}{suffix}")
    out_file.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out_file.relative_to(ROOT)} ({len(pkgs)} packages)")


def main() -> int:
    _write(
        ROOT / "requirements.lock.txt",
        ROOT / "requirements.hashes.txt",
        "CI hash lock for Sonar S8544 / pip --require-hashes",
    )
    _write(
        ROOT / "requirements-prod.lock.txt",
        ROOT / "requirements-prod.hashes.txt",
        "Docker/prod hash lock for Sonar S8544 / pip --require-hashes",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
