#!/usr/bin/env python3
"""Generate a CycloneDX 1.5 SBOM from requirements.lock.txt (no extra deps).

Usage:
  python scripts/generate_sbom.py
  python scripts/generate_sbom.py --out docs/data-room/sbom/cyclonedx-python.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements.lock.txt"
DEFAULT_OUT = ROOT / "docs" / "data-room" / "sbom" / "cyclonedx-python.json"

_REQ_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.\-]+)\s*==\s*(?P<version>[^\s;#]+)",
)


def _parse_lock(path: Path) -> list[tuple[str, str]]:
    comps: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _REQ_RE.match(line)
        if not m:
            continue
        name = m.group("name").split("[", 1)[0]
        comps.append((name, m.group("version")))
    return comps


def build_sbom(components: list[tuple[str, str]], *, lock_sha: str) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bom_ref_components = []
    for name, version in components:
        purl = f"pkg:pypi/{name.lower()}@{version}"
        bom_ref_components.append(
            {
                "type": "library",
                "bom-ref": purl,
                "name": name,
                "version": version,
                "purl": purl,
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "blackdark-generate_sbom",
                        "version": "1.0.0",
                    }
                ]
            },
            "component": {
                "type": "application",
                "name": "blackdark",
                "version": "rc2",
                "description": f"Generated from requirements.lock.txt sha256={lock_sha}",
            },
            "properties": [
                {"name": "blackdark:lockfile", "value": "requirements.lock.txt"},
                {"name": "blackdark:lockfile_sha256", "value": lock_sha},
            ],
        },
        "components": bom_ref_components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if not LOCK.is_file():
        raise SystemExit(f"missing {LOCK}")
    raw = LOCK.read_bytes()
    lock_sha = hashlib.sha256(raw).hexdigest()
    components = _parse_lock(LOCK)
    if not components:
        raise SystemExit("no components parsed from lockfile")
    sbom = build_sbom(components, lock_sha=lock_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} components={len(components)} lock_sha256={lock_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
