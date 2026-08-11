#!/usr/bin/env python3
"""Print Excel plan audit summary — run: python scripts/run_plan_audit.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError, ValueError):
        logger.debug("optional operation skipped", exc_info=True)

from plan_audit import plan_audit


def main() -> int:
    data = plan_audit()
    print(f"\nBLACKDARK Plan Audit — {data['overall_percent']}% overall")
    print(f"  complete: {data['complete_count']} | partial: {data['partial_count']} | planned: {data['planned_count']}")
    print("\nNext priorities:")
    for item in data.get("next_priority") or []:
        print(f"  [{item['status']}] {item['title']}")
    out = ROOT / "data" / "plan_audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")
    print("UI: http://127.0.0.1:8080/plan\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
