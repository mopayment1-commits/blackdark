#!/usr/bin/env python3
"""Close all 34 official batches under mandatory v6 §2.1 strict institutional gates."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.v6_strict_closure import close_all_batches_strict


async def main() -> int:
    report = await close_all_batches_strict()
    summary = report["summary"]
    print(json.dumps(summary, indent=2))
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
