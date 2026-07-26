"""Save roadmap audit JSON for due diligence."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from bd_platform.roadmap_audit import save_audit


def main() -> None:
    data = save_audit()
    print(f"Roadmap audit saved → {data.get('saved_to')}")
    print(f"Complete: {data['complete_count']}/{data['total_items']} ({data['complete_percent']}%)")
    print(f"Weighted: {data['weighted_percent']}%")


if __name__ == "__main__":
    main()
