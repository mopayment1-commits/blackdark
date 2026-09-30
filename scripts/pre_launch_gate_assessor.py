#!/usr/bin/env python3
"""Assess pre-launch institutional gates (G1–G10) — honest status before Railway."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "PRE_LAUNCH_GATE_ASSESSMENT.json"


def main() -> int:
    from governance.assessor import assess_pre_launch_gates

    from governance.public_report import coerce_bool, pre_launch_stdout_lines, pre_launch_summary_sink

    report = assess_pre_launch_gates()
    summary_payload = pre_launch_summary_sink(report)
    OUT.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for line in pre_launch_stdout_lines(summary_payload):
        print(line)
    return 0 if coerce_bool(report.get("pre_launch_ready")) else 1


if __name__ == "__main__":
    sys.exit(main())
