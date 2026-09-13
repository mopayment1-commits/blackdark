#!/usr/bin/env python3
"""Close official batch01 (IDs 1–25) under strict v6 §2.1 institutional gates."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch_institutional_closure import close_batch01_institutional


async def main() -> int:
    report = await close_batch01_institutional()
    summary = report["summary"]
    print(json.dumps(summary, indent=2))
    return 0 if summary["pass_institutional"] == 25 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
