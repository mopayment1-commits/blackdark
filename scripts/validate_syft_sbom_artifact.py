#!/usr/bin/env python3
"""Validate CycloneDX SBOM artifact from Syft lockfile job."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "governance" / "launch57" / "evidence" / "syft-prod-lock.cyclonedx.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.is_file():
        print(f"SKIP: no artifact at {path}", file=sys.stderr)
        return 3
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("bomFormat") != "CycloneDX":
        print("FAIL: bomFormat", file=sys.stderr)
        return 1
    components = data.get("components") or []
    names = {c.get("name", "").lower() for c in components if isinstance(c, dict)}
    if "webauthn" not in names:
        print("WARN: webauthn not listed in SBOM components", file=sys.stderr)
    print(f"PASS: CycloneDX with {len(components)} components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
