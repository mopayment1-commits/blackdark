"""Generate institutional module map for CAP646 Wave D capabilities."""

from __future__ import annotations

import json
from pathlib import Path

from cap646.backend_registry import resolve_binding
from cap646.catalog import catalog_by_id, is_duplicate, is_external
from cap646.waves import WAVE_D


def build_module_map() -> list[dict]:
    rows = []
    for cid in WAVE_D:
        if is_external(cid) or is_duplicate(cid):
            continue
        b = resolve_binding(cid)
        cat = catalog_by_id()[cid]
        rows.append(
            {
                "id": cid,
                "capability": cat["capability"],
                "track": cat["track"],
                "backend_module": b.module,
                "backend_entrypoint": b.entrypoint,
                "surface": b.surface,
                "binding_source": b.source,
            }
        )
    return rows


def write_module_map(path: Path | None = None) -> Path:
    path = path or Path(__file__).resolve().parent.parent / "docs" / "cap646" / "CAP646_MODULE_MAP.json"
    payload = {
        "generated_by": "cap646.generate_module_map",
        "wave": "D",
        "count": len(WAVE_D),
        "rows": build_module_map(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    out = write_module_map()
    print(f"wrote {out}")
