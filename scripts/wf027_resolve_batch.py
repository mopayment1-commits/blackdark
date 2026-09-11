#!/usr/bin/env python3
"""Resolve WF-027 legacy IDs when their official batch spine opens (Run 021)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.batch_rbas_config import BatchRbasConfig  # noqa: E402
from scripts.rbas001_scoping import WF027_UNRESOLVED_LEGACY_IDS  # noqa: E402

BATCH01_PROD = ROOT / "cap646" / "batch01_production.py"
RBAS_SCOPING = ROOT / "scripts" / "rbas001_scoping.py"


def resolve_ids_for_batch(batch_num: int) -> list[int]:
    cfg = BatchRbasConfig(batch_num)
    to_resolve = sorted(WF027_UNRESOLVED_LEGACY_IDS & set(cfg.id_range))
    if not to_resolve:
        return []

    prod_text = BATCH01_PROD.read_text(encoding="utf-8")
    scope_text = RBAS_SCOPING.read_text(encoding="utf-8")

    for cid in to_resolve:
        # Remove ID line from LEGACY_BATCH01_EXTENSION_IDS set
        prod_text = re.sub(rf"^\s*{cid},\n", "", prod_text, flags=re.M)
        prod_text = re.sub(
            rf"(\n        # {cid} removed Run 021)",
            rf"\1",
            prod_text,
        )
        comment = f"        # {cid} removed Run 021 — official batch{batch_num:02d} ({cfg.id_start}–{cfg.id_end}); see CROSS-SPINE-001 / WF-027\n"
        if comment.strip() not in prod_text:
            prod_text = prod_text.replace(
                "LEGACY_BATCH01_EXTENSION_IDS: frozenset[int] = frozenset(\n    {",
                "LEGACY_BATCH01_EXTENSION_IDS: frozenset[int] = frozenset(\n    {\n" + comment,
            )

    remaining = sorted(WF027_UNRESOLVED_LEGACY_IDS - set(to_resolve))
    scope_text = re.sub(
        r"WF027_UNRESOLVED_LEGACY_IDS = frozenset\(\{[^}]+\}\)",
        f"WF027_UNRESOLVED_LEGACY_IDS = frozenset({{{', '.join(str(x) for x in remaining) if remaining else ''}}})",
        scope_text,
        count=1,
    )

    BATCH01_PROD.write_text(prod_text, encoding="utf-8")
    RBAS_SCOPING.write_text(scope_text, encoding="utf-8")
    return to_resolve


if __name__ == "__main__":
    n = int(sys.argv[1])
    resolved = resolve_ids_for_batch(n)
    print(f"Resolved WF-027 IDs for batch{n:02d}: {resolved}")
