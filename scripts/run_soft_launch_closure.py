#!/usr/bin/env python3
"""Run Soft Launch institutional closure and write readiness artifact."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, _, value = raw.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Soft Launch institutional closure")
    parser.add_argument(
        "--out",
        default=str(ROOT / "docs" / "cap978" / "SOFT_LAUNCH_READINESS.json"),
    )
    parser.add_argument("--e2e", action="store_true", help="Include platform chain E2E (slower)")
    parser.add_argument("--bootstrap", action="store_true", help="Generate .env.softlaunch.local first")
    parser.add_argument("--admin-email", default="ops@blackdark.local")
    args = parser.parse_args()

    _load_env_file(ROOT / ".env.softlaunch.local")
    _load_env_file(ROOT / ".env.launch.local")

    if args.bootstrap:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "bootstrap_free_human_ops",
            ROOT / "scripts" / "bootstrap_free_human_ops.py",
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        result = mod.write_softlaunch_env(admin_email=args.admin_email, rotate=False)
        if not result.get("ok"):
            print(json.dumps(result, indent=2))
            return 2

    import database

    await database.init_db()

    from cap978.soft_launch_closure import run_soft_launch_closure

    snap = await run_soft_launch_closure(include_platform_e2e=args.e2e)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": snap["verdict"],
                "checks_failed": snap["checks_failed"],
                "snapshot_hash": snap["snapshot_hash"],
                "path": str(out),
                "tracks": snap["tracks"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if snap["verdict"].startswith("VERIFIED") or snap["verdict"].startswith("CODE COMPLETE") else 1


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(asyncio.run(main()))
