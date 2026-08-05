#!/usr/bin/env python3
"""Run live collect + market-replay bootstrap + train in one shot."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    from database import init_db
    from ml.labeling_pipeline import run_labeling_flywheel_cycle
    from ml.train_baseline import model_status

    await init_db()
    result = await run_labeling_flywheel_cycle(bootstrap_if_needed=True, collect_live=True)
    status = await model_status()
    payload = {"flywheel": result, "model_status": status}
    print(json.dumps(payload, indent=2, default=str))
    trained = bool((result.get("training") or {}).get("trained"))
    exported = int((result.get("export") or {}).get("exported") or 0)
    collected = int((result.get("collect") or {}).get("collected") or 0)
    bootstrapped = bool((result.get("bootstrap") or {}).get("bootstrapped"))
    print(
        f"\nSUMMARY collected={collected} bootstrapped={bootstrapped} "
        f"exported={exported} trained={trained}"
    )
    return 0 if (exported > 0 or trained or collected > 0 or bootstrapped) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
