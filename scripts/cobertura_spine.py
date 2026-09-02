"""Parse trusted local Cobertura XML for spine coverage (Bandit-safe: defusedxml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET


def spine_module_rows(root: ET.Element, modules: list[str]) -> tuple[list[dict[str, Any]], int, int]:
    """Return per-module rows plus total stmts/miss for weighted spine coverage."""
    rows: list[dict[str, Any]] = []
    total_stmts = total_miss = 0
    for rel in modules:
        cls = root.find(f".//class[@filename='{rel.split('/')[-1]}']")
        if cls is None:
            rows.append({"module": rel, "stmts": 0, "miss": 0, "coverage_pct": None})
            continue
        line_nodes = cls.findall("lines/line")
        if line_nodes:
            stmts = len(line_nodes)
            miss = sum(1 for ln in line_nodes if int(ln.get("hits", 0)) == 0)
        else:
            rate = float(cls.get("line-rate", 0))
            stmts = max(1, int(round(1 / rate))) if rate else 0
            miss = int(round(stmts * (1 - rate)))
        total_stmts += stmts
        total_miss += miss
        rows.append(
            {
                "module": rel,
                "stmts": stmts,
                "miss": miss,
                "coverage_pct": round(100 * (stmts - miss) / stmts, 2) if stmts else None,
            }
        )
    return rows, total_stmts, total_miss


def parse_spine_coverage(cov_path: Path, modules: list[str]) -> dict[str, Any]:
    root = ET.parse(cov_path).getroot()
    rows, total_stmts, total_miss = spine_module_rows(root, modules)
    weighted = round(100 * (total_stmts - total_miss) / total_stmts, 2) if total_stmts else 0
    return {
        "spine_modules": rows,
        "combined_spine": {
            "total_stmts": total_stmts,
            "total_miss": total_miss,
            "weighted_statement_coverage_pct": weighted,
            "metric": "statement_coverage_not_branch",
        },
    }
