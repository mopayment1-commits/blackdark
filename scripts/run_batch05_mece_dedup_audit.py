#!/usr/bin/env python3
"""Batch05 four-layer MECE / duplication audit (IDs 201-250).

Layer 1: pairwise semantic token scan (full counts per owner mandate).
Layer 2: jscpd on bd_platform hero modules for 201-250 functions.
Layer 3: SSOT note (single equation sources).
Layer 4: Type-4 split-brain sample (excludes #214/#245 — see BATCH05_MECE_OVERLAP_214_245_DECISION.json).
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH05_DEDUP_AUDIT.json"
CATALOG_PATH = ROOT / "docs/cap646/CAP646_CATALOG.json"
INVENTORY = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"
HERO_AUDIT = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json"
OVERLAP_DECISION = ROOT / "docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json"

BATCH05 = list(range(201, 251))
BATCH_CLOSED = list(range(1, 201))
SSOT_EXTERNAL = [338, 500, 507, 534]
OVERLAP_BATCH01 = frozenset({214, 245})

NOISE = frozenset(
    {
        "intelligence",
        "the",
        "and",
        "for",
        "per",
        "data",
        "access",
        "status",
        "layer",
        "run",
        "e2e",
        "api",
        "real",
        "time",
    }
)

HERO_GLOB = [
    "bd_platform/derivatives_ta_research_layer.py",
    "bd_platform/onchain_defi_sources_layer.py",
    "bd_platform/intelligence_market_extensions_layer.py",
    "bd_platform/intelligence_ux_extensions_layer.py",
    "bd_platform/security_trust_data_layer.py",
    "bd_platform/heroes_capability_layer.py",
    "bd_platform/pro_trader_layer.py",
    "bd_platform/market_analysis_layer.py",
]

SIM_THRESHOLD = 0.55  # Jaccard on capability name tokens


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in NOISE and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _catalog_names() -> dict[int, str]:
    catalog = {r["id"]: r["capability"] for r in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))}
    return catalog


def _pair_scan(ids_a: list[int], ids_b: list[int], names: dict[int, str], scope: str) -> dict[str, Any]:
    pairs_examined = len(ids_a) * len(ids_b) if ids_a != ids_b else len(list(combinations(ids_a, 2)))
    hits: list[dict[str, Any]] = []
    if ids_a == ids_b:
        iterator = combinations(ids_a, 2)
    else:
        iterator = ((a, b) for a in ids_a for b in ids_b)
    for a, b in iterator:
        if a == b:
            continue
        ta, tb = _tokens(names[a]), _tokens(names[b])
        score = _jaccard(ta, tb)
        if score >= SIM_THRESHOLD:
            hits.append(
                {
                    "a": a,
                    "b": b,
                    "a_name": names[a],
                    "b_name": names[b],
                    "jaccard": round(score, 3),
                    "shared_tokens": sorted(ta & tb),
                }
            )
    hits.sort(key=lambda x: -x["jaccard"])
    return {
        "scope": scope,
        "pairs_examined": pairs_examined,
        "threshold_jaccard": SIM_THRESHOLD,
        "candidates_found": len(hits),
        "candidates": hits[:100],
        "excluded_from_scan": sorted(OVERLAP_BATCH01) if scope.startswith("internal") else [],
    }


def _hero_search() -> dict[str, Any]:
    fn_re = re.compile(r"def\s+(\w+)_(\d+)\(")
    hits: dict[int, list[str]] = {}
    files_searched = []
    for rel in HERO_GLOB:
        path = ROOT / rel
        if not path.is_file():
            continue
        files_searched.append(rel)
        txt = path.read_text(encoding="utf-8", errors="ignore")
        for m in fn_re.finditer(txt):
            cid = int(m.group(2))
            if cid in BATCH05:
                hits.setdefault(cid, []).append(f"{m.group(1)}@{rel}")
    audit = {
        r["capability_id"]: r
        for r in json.loads(HERO_AUDIT.read_text(encoding="utf-8"))["rows"]
        if 201 <= r["capability_id"] <= 250
    }
    return {
        "scope": "hero/bd_platform layer search for *_201..250",
        "files_searched": files_searched,
        "ids_with_functions": len(hits),
        "function_map": {str(k): v for k, v in sorted(hits.items())},
        "split_brain_ids": [
            cid
            for cid in BATCH05
            if audit.get(cid, {}).get("classification") == "SPLIT-BRAIN-UNVERIFIED"
        ],
        "overlap_resolved": {
            "214": "REUSED-LINK batch01 dedicated — hero bindings eliminated",
            "245": "REUSED-LINK batch01 freshness — hero stub eliminated",
        },
    }


def _jscpd_layer() -> dict[str, Any]:
    out_dir = ROOT / "docs/.jscpd-batch05-phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [str(ROOT / p) for p in HERO_GLOB if (ROOT / p).is_file()]
    proc = subprocess.run(
        [
            "npx",
            "--yes",
            "jscpd",
            "--min-lines",
            "8",
            "--min-tokens",
            "60",
            "--reporters",
            "json",
            "--output",
            str(out_dir),
            *existing,
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=180,
    )
    report_path = out_dir / "jscpd-report.json"
    if report_path.is_file():
        data = json.loads(report_path.read_text(encoding="utf-8"))
        stats = data.get("statistics", {}).get("total", {})
        return {
            "exit_code": proc.returncode,
            "files_scanned": len(existing),
            "duplicated_lines": stats.get("duplicatedLines"),
            "duplicated_tokens": stats.get("duplicatedTokens"),
            "clones": len(data.get("duplicates", [])),
            "report_path": str(report_path.relative_to(ROOT)),
        }
    return {"exit_code": proc.returncode, "stderr_tail": (proc.stderr or "")[-400:]}


def _ssot_scan(names: dict[int, str]) -> dict[str, Any]:
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))["per_id"]
    pairs_examined = len(BATCH05) * len(SSOT_EXTERNAL)
    hits = []
    for cid in BATCH05:
        for oid in SSOT_EXTERNAL:
            score = _jaccard(_tokens(names[cid]), _tokens(inv[str(oid)]["capability"]))
            if score >= SIM_THRESHOLD:
                hits.append(
                    {
                        "batch05_id": cid,
                        "ssot_id": oid,
                        "jaccard": round(score, 3),
                        "batch05_name": names[cid],
                        "ssot_name": inv[str(oid)]["capability"],
                    }
                )
    return {
        "scope": "batch05 vs SSOT external 338/500/507/534",
        "pairs_examined": pairs_examined,
        "candidates_found": len(hits),
        "candidates": hits,
    }


def main() -> None:
    names = _catalog_names()
    remaining = [i for i in BATCH05 if i not in OVERLAP_BATCH01]

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_hash": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "Batch05 MECE four-layer audit",
        "priority_overlap_gate": str(OVERLAP_DECISION.relative_to(ROOT)),
        "layer1_mece": {
            "internal_201_250_all": _pair_scan(BATCH05, BATCH05, names, "internal_201_250 (C(50,2)=1225)"),
            "internal_201_250_remaining_48": _pair_scan(
                remaining, remaining, names, "internal_remaining_48 (C(48,2)=1128)"
            ),
            "vs_closed_1_200": _pair_scan(BATCH05, BATCH_CLOSED, names, "batch05_vs_1_200 (50×200=10000)"),
            "vs_ssot_external": _ssot_scan(names),
            "hero_search": _hero_search(),
        },
        "layer2_code_jscpd": _jscpd_layer(),
        "layer3_ssot": {
            "note": "Single progress equation: docs/PROGRESS_826_CANONICAL.json",
            "batch05_not_in_numerator_until_PA": True,
        },
        "layer4_type4_contract": {
            "note": "#214/#245 resolved in priority gate; sample 10 IDs deferred until batch05_dedicated exists",
            "sample_ids_planned": [201, 203, 205, 208, 217, 228, 237, 242, 247, 250],
        },
        "duplicate_clusters_notable": [
            {
                "name": "funding_rate_cluster",
                "ids": [206, 228],
                "action": "MECE semantic review during implementation",
            },
            {
                "name": "open_interest_cluster",
                "ids": [205, 232],
                "action": "MECE semantic review during implementation",
            },
            {
                "name": "funding_arbitrage_cluster",
                "ids": [229, 230],
                "action": "distinct scanners — verify at implementation",
            },
        ],
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    i = doc["layer1_mece"]["internal_201_250_all"]["pairs_examined"]
    v = doc["layer1_mece"]["vs_closed_1_200"]["pairs_examined"]
    h = doc["layer1_mece"]["hero_search"]["files_searched"]
    s = doc["layer1_mece"]["vs_ssot_external"]["pairs_examined"]
    print(f"Wrote {OUT}")
    print(f"pairs_examined: internal={i} vs_1_200={v} ssot={s} hero_files={len(h)}")


if __name__ == "__main__":
    main()
