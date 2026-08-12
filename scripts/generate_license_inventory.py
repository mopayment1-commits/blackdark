#!/usr/bin/env python3
"""Generate a dependency license inventory from the installed environment.

Reads package metadata via importlib.metadata for names listed in
requirements.lock.txt. Writes Markdown + JSON under docs/data-room/licenses/.

Usage:
  python scripts/generate_license_inventory.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements.lock.txt"
OUT_MD = ROOT / "docs" / "data-room" / "licenses" / "DEPENDENCY_LICENSE_INVENTORY.md"
OUT_JSON = ROOT / "docs" / "data-room" / "licenses" / "dependency_licenses.json"

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


def _license_for(dist_name: str) -> tuple[str, str, str]:
    """Return (resolved_name, version, license_str)."""
    try:
        dist = metadata.distribution(dist_name)
    except metadata.PackageNotFoundError:
        # Try normalized dash/underscore variants.
        for alt in {dist_name.replace("-", "_"), dist_name.replace("_", "-")}:
            try:
                dist = metadata.distribution(alt)
                break
            except metadata.PackageNotFoundError:
                dist = None
        if dist is None:
            return dist_name, "NOT_INSTALLED", "UNKNOWN"
    meta = dist.metadata
    lic = (
        meta.get("License")
        or meta.get("License-Expression")
        or ""
    ).strip()
    if not lic:
        classifiers = meta.get_all("Classifier") or []
        lic_bits = [
            c.split(" :: ")[-1]
            for c in classifiers
            if c.startswith("License ::") and not c.endswith("OSI Approved")
        ]
        lic = "; ".join(lic_bits) if lic_bits else "UNKNOWN"
    return dist.metadata["Name"] or dist_name, dist.version, lic


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    args = parser.parse_args()
    lock_sha = hashlib.sha256(LOCK.read_bytes()).hexdigest()
    rows = []
    for name, pinned in _parse_lock(LOCK):
        resolved, version, lic = _license_for(name)
        rows.append(
            {
                "lock_name": name,
                "lock_version": pinned,
                "installed_name": resolved,
                "installed_version": version,
                "license": lic,
                "version_match": version == pinned,
            }
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "generated_at_utc": now,
        "lockfile": "requirements.lock.txt",
        "lockfile_sha256": lock_sha,
        "component_count": len(rows),
        "unknown_license_count": sum(1 for r in rows if r["license"] == "UNKNOWN"),
        "not_installed_count": sum(1 for r in rows if r["installed_version"] == "NOT_INSTALLED"),
        "components": rows,
        "counsel_review": "EXTERNAL_EVIDENCE_REQUIRED — engineer inventory only; not a legal opinion",
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# BLACKDARK Dependency License Inventory",
        "",
        f"**Generated (UTC):** `{now}`",
        f"**Lockfile:** `requirements.lock.txt` sha256=`{lock_sha}`",
        f"**Components:** {len(rows)}",
        f"**UNKNOWN license:** {payload['unknown_license_count']}",
        f"**Not installed in generator env:** {payload['not_installed_count']}",
        "",
        "> **Not a legal opinion.** Counsel review remains EXTERNAL (`F-EXT-05`).",
        "",
        "| Package | Lock version | Installed | License |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['lock_name']}` | `{r['lock_version']}` | `{r['installed_version']}` | {r['license']} |"
        )
    lines.append("")
    args.out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out_md} and {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
