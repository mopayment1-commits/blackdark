"""Governing source registry — mandatory baseline documents with integrity hashes."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_UPLOADS = Path("/home/ubuntu/.cursor/projects/workspace/uploads")
_OUT = _ROOT / "docs" / "rvm" / "GOVERNING_SOURCES.json"

GOVERNING_FILES: list[dict[str, str]] = [
    {
        "id": "GOV-SRC-001",
        "role": "capabilities_978",
        "title": "Project 978 Capabilities Grouped Execution Tracks (REVIEWED RECONCILED PLUS 332 EXACT)",
        "filename": "Project_978_Capabilities_Grouped_Execution_Tracks_REVIEWED_RECONCILED_PLUS_332_EXACT_4453.pdf",
        "sha256": "723c1c0a92fbb05624e9626e38f9a94ed24e679f7a283b8661fce6582de75c69",
    },
    {
        "id": "GOV-SRC-002",
        "role": "institutional_merged_spec",
        "title": "BLACKDARK Final Institutional Merged Specification (Five-Layer Verified)",
        "filename": "BLACKDARK_FINAL_INSTITUTIONAL_MERGED_SPECIFICATION_FIVE_LAYER_VERIFIED_3108.pdf",
        "sha256": "a21ba1c81972b0125331ee7378f480b720ab62f68761e799d975bc22a5cea4b8",
    },
    {
        "id": "GOV-SRC-003",
        "role": "governing_reference",
        "title": "Governing Reference Document (48 pages)",
        "filename": "______________2d4e.pdf",
        "sha256": "f276563a37156e9054b36f4b5d335e18272b833f39fc070930c54d5896233c7c",
    },
    {
        "id": "GOV-SRC-004",
        "role": "governing_reference",
        "title": "Governing Reference Document (69 pages)",
        "filename": "____________________________________5b38.pdf",
        "sha256": "16bbf10aeefdf27db427a234abfb66ef98af0bbe9904b877010c1d021875d073",
    },
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_governing_sources() -> dict[str, Any]:
    """Confirm all mandatory governing PDFs are present and match expected hashes."""
    rows: list[dict[str, Any]] = []
    all_ok = True
    for spec in GOVERNING_FILES:
        path = _UPLOADS / spec["filename"]
        present = path.is_file()
        actual_hash = _sha256(path) if present else None
        hash_ok = present and actual_hash == spec["sha256"]
        if not hash_ok:
            all_ok = False
        rows.append(
            {
                **spec,
                "path": str(path),
                "present": present,
                "hash_ok": hash_ok,
                "actual_sha256": actual_hash,
            }
        )
    return {
        "baseline_version": "blackdark-rvm-v1",
        "all_present": all(p["present"] for p in rows),
        "all_hashes_ok": all_ok,
        "sources": rows,
        "adopted_reference": "docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md",
    }


@lru_cache(maxsize=1)
def load_governing_sources() -> dict[str, Any]:
    if _OUT.is_file():
        return json.loads(_OUT.read_text(encoding="utf-8"))
    return verify_governing_sources()


def write_governing_sources() -> dict[str, Any]:
    data = verify_governing_sources()
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    load_governing_sources.cache_clear()
    return data
