#!/usr/bin/env python3
"""Generate institutional Evidence Room snapshot (reproducible DD artifact)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


async def main() -> int:
    parser = argparse.ArgumentParser(description="Build CAP978 institutional evidence room snapshot")
    parser.add_argument("--out", default=str(ROOT / "docs" / "cap978" / "EVIDENCE_ROOM_SNAPSHOT.json"))
    parser.add_argument(
        "--external-out",
        default=str(ROOT / "docs" / "cap978" / "EXTERNAL_REGISTRY.json"),
        help="Write machine-readable external registry JSON",
    )
    parser.add_argument("--full", action="store_true", help="Include external registry rows and full closure detail")
    args = parser.parse_args()

    import database

    await database.init_db()

    from cap978.evidence_room import build_evidence_room_snapshot
    from cap978.external_registry import external_registry_report

    snapshot = await build_evidence_room_snapshot(include_rows=args.full)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    external = external_registry_report()
    ext_out = Path(args.external_out)
    ext_out.write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": snapshot["verdict"],
                "snapshot_hash": snapshot["snapshot_hash"],
                "path": str(out),
                "external_registry_path": str(ext_out),
            },
            indent=2,
        )
    )
    return 0 if snapshot["verdict"] == "VERIFIED COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
