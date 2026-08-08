#!/usr/bin/env python3
"""Run the 60-second grasp machine probe against a live base URL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SAFE_REL = re.compile(r"^[A-Za-z0-9._\-]+(?:/[A-Za-z0-9._\-]+)*$")


def _validated_json_out(raw: str) -> Path:
    """Allow only relative paths under the repo (no traversal)."""
    text = (raw or "").strip().replace("\\", "/")
    if not text or text.startswith("/") or ".." in Path(text).parts or not _SAFE_REL.match(text):
        raise SystemExit("Invalid --json-out path (relative repo path required)")
    out = (ROOT / text).resolve()
    if not str(out).startswith(str(ROOT.resolve())):
        raise SystemExit("Invalid --json-out path (escaped repository root)")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    from expert_execution import run_acceptance_60s

    result = run_acceptance_60s(args.base)
    print(json.dumps(result, indent=2))
    if args.json_out:
        out = _validated_json_out(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result.get("machine_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
