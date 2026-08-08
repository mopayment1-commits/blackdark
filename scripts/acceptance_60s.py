#!/usr/bin/env python3
"""Run the 60-second grasp machine probe against a live base URL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    from expert_execution import run_acceptance_60s

    result = run_acceptance_60s(args.base)
    print(json.dumps(result, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result.get("machine_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
