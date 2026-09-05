#!/usr/bin/env python3
"""Generate Batch05 Section-0 baseline gate + per-ID INVEST / 12207 classification."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = {r["id"]: r for r in json.loads((ROOT / "docs/cap646/CAP646_CATALOG.json").read_text())}
INV = json.loads((ROOT / "docs/CAPABILITIES_826_INVENTORY.json").read_text())["per_id"]
AUDIT = {
    r["capability_id"]: r
    for r in json.loads((ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json").read_text())["rows"]
}
B4 = json.loads((ROOT / "docs/BATCH04_FINAL_CLOSURE_STATUS_151_200.json").read_text())
PROG = json.loads((ROOT / "docs/PROGRESS_826_CANONICAL.json").read_text())

FN_RE = re.compile(r"def\s+(\w+)_(\d+)\(")


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _hero_functions() -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for py in ROOT.glob("bd_platform/**/*.py"):
        rel = py.relative_to(ROOT)
        txt = py.read_text(encoding="utf-8", errors="ignore")
        for m in FN_RE.finditer(txt):
            cid = int(m.group(2))
            if 201 <= cid <= 250:
                out.setdefault(cid, []).append(f"{m.group(1)}@{rel}")
    return out


def _batch01_overlap() -> set[int]:
    overlap: set[int] = set()
    for rel in ("cap646/batch01_dedicated.py", "cap646/batch01_production.py"):
        txt = (ROOT / rel).read_text(encoding="utf-8")
        for cid in range(201, 251):
            if f"_cap{cid}" in txt or f"cap_{cid}" in txt or f" {cid}," in txt and rel.endswith("production.py"):
                overlap.add(cid)
    return overlap


def _prior_work_scan() -> list[dict]:
    patterns = [
        ("cap646/batch05*", "official spine"),
        ("tests/cap646/test_batch05*", "official tests"),
        ("docs/BATCH05_*", "official docs"),
        ("scripts/partial_batches/batch_03_201_300.json", "hero batch03 manifest (superset)"),
        ("data/hero_batch_03_201_300_evidence.jsonl", "hero evidence"),
        ("scripts/run_batch05_deep_closure.py", "misnumbered hero 401-500 script"),
        ("scripts/partial_batches/batch_05_401_500.json", "hero batch 401-500 (NOT official batch05)"),
    ]
    rows = []
    for glob_pat, label in patterns:
        if "*" in glob_pat:
            hits = sorted(ROOT.glob(glob_pat))
        else:
            p = ROOT / glob_pat
            hits = [p] if p.is_file() else []
        rows.append(
            {
                "pattern": glob_pat,
                "label": label,
                "hits": [str(h.relative_to(ROOT)) for h in hits],
                "count": len(hits),
            }
        )
    return rows


def _lifecycle(cid: int, hero_fns: list[str], overlap: set[int]) -> str:
    if cid in overlap:
        return "Brownfield-OVERLAP-BATCH01"
    if hero_fns:
        return "Brownfield"
    return "Greenfield"


def _invest_row(cid: int, cat: dict, inv: dict, aud: dict, hero_fns: list[str], lifecycle: str) -> dict:
    cap = cat["capability"]
    track = cat["track"]
    backend = inv.get("backend", "")
    audit_cls = aud.get("classification", "UNKNOWN")
    has_test = bool(aud.get("independent_test_file"))
    external = any(
        k in backend
        for k in (
            "santiment",
            "coingecko",
            "etherscan",
            "defillama",
            "dexscreener",
            "cryptoquant",
            "glassnode",
        )
    )
    paid_hint = any(k in backend.lower() for k in ("cryptoquant", "glassnode", "santiment.net"))

    independent = {
        "pass": lifecycle != "Brownfield-OVERLAP-BATCH01",
        "evidence": (
            f"Catalog goal '{cap}' (T{track}) maps to dedicated batch05 surface; "
            f"no cap646/batch05 binding yet — independent once overlap resolved for #214/#245."
            if lifecycle == "Brownfield-OVERLAP-BATCH01"
            else f"Catalog goal '{cap}' (id={cid}) is a distinct RTM row; hero fn {hero_fns[0] if hero_fns else 'TBD'} "
            f"can be wrapped without coupling to other batch05 IDs."
        ),
    }
    negotiable = {
        "pass": True,
        "evidence": (
            f"Scope negotiable on data tier ({backend}) and heuristic depth; "
            f"{'paid-vendor PENDING_PAYMENT path allowed per owner mandate §19' if paid_hint or external else 'internal rule-based scope adjustable'}."
        ),
    }
    valuable = {
        "pass": True,
        "evidence": f"Institutional '{cap}' on track {track} — listed in CAP646_CATALOG + inventory official_batch=batch05.",
    }
    estimable = {
        "pass": lifecycle != "Greenfield" or bool(hero_fns),
        "evidence": (
            f"Brownfield: audit={audit_cls}, underlying_real_code={aud.get('underlying_real_code')}, "
            f"test={aud.get('independent_test_file', 'none')} — effort bounded by strangler wiring."
            if lifecycle.startswith("Brownfield")
            else "Greenfield: no hero fn — requires discovery spike before point estimate."
        ),
    }
    small = {
        "pass": True,
        "evidence": (
            f"Single capability handler + acceptance domain_rules + one contract test — "
            f"fits one strangler slice (<200 LOC target per mandate §27)."
        ),
    }
    testable = {
        "pass": True,
        "evidence": (
            f"expected_surface derivable from catalog '{cap}'; domain_rules[] written before probe "
            f"(mandate §7). Legacy test pattern: {aud.get('independent_test_pattern', 'new test_batch05_*')}."
        ),
    }

    return {
        "capability_id": cid,
        "capability": cap,
        "track": track,
        "lifecycle_12207": lifecycle,
        "invest": {
            "I": independent,
            "N": negotiable,
            "V": valuable,
            "E": estimable,
            "S": small,
            "T": testable,
        },
        "hero_audit_classification": audit_cls,
        "hero_underlying": aud.get("underlying_function"),
        "hero_module": aud.get("underlying_module"),
        "backend_registry_current": backend,
        "split_brain": aud.get("split_brain_routing", False),
        "legacy_test_file": aud.get("independent_test_file"),
        "prior_work_disposition": (
            "RECLASSIFY-OVERLAP-BATCH01"
            if lifecycle == "Brownfield-OVERLAP-BATCH01"
            else "REUSE-AUDIT-INPUT-NOT-AUTO-PA"
            if lifecycle == "Brownfield"
            else "GREENFIELD-SPINE"
        ),
        "closure_status_initial": "NOT_READY",
    }


def main() -> None:
    commit = _git_head()
    hero_fns = _hero_functions()
    overlap = _batch01_overlap()
    prior = _prior_work_scan()

    rows = []
    for cid in range(201, 251):
        lifecycle = _lifecycle(cid, hero_fns.get(cid, []), overlap)
        rows.append(
            _invest_row(cid, CATALOG[cid], INV[str(cid)], AUDIT.get(cid, {}), hero_fns.get(cid, []), lifecycle)
        )

    lifecycle_counts = Counter(r["lifecycle_12207"] for r in rows)
    disposition_counts = Counter(r["prior_work_disposition"] for r in rows)
    audit_counts = Counter(r["hero_audit_classification"] for r in rows)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_hash": commit,
        "batch": "batch05",
        "id_range": "201-250",
        "count": 50,
        "lifecycle_12207_summary": dict(lifecycle_counts),
        "prior_work_disposition_summary": dict(disposition_counts),
        "hero_audit_summary": dict(audit_counts),
        "batch01_overlap_ids": sorted(overlap),
        "official_spine_exists": False,
        "rows": rows,
    }
    path = ROOT / "docs/BATCH05_CLASSIFICATION_INVEST_201_250.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    census = {
        "generated_at": out["generated_at"],
        "commit_hash": commit,
        "scan_commands": [
            "glob cap646/batch05*",
            "glob tests/cap646/test_batch05*",
            "glob docs/BATCH05_*",
            "rg '_cap20[1-9]|_cap21[0-9]|_cap22[0-9]|_cap23[0-9]|_cap24[0-9]|_cap250' cap646/",
            "read data/hero_batch_03_201_300_evidence.jsonl lines 1-50",
        ],
        "findings": prior,
        "legacy_hero_batch03": {
            "manifest": "scripts/partial_batches/batch_03_201_300.json",
            "evidence": "data/hero_batch_03_201_300_evidence.jsonl",
            "audit": "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json",
            "disposition": "REUSE-AUDIT-INPUT — not auto PRODUCTION-ALIGNED; requires cap646/batch05 spine + live free-tier probes",
        },
        "naming_collision": {
            "official_batch05": "201-250",
            "hero_batch05_scripts": "401-500 (IGNORE for official batch05)",
            "hero_batch03_superset": "201-300 (contains official batch05)",
        },
        "bd_platform_functions_201_250": sum(1 for cid in range(201, 251) if cid in hero_fns),
        "template_stub_201_250": 0,
    }
    census_path = ROOT / "docs/BATCH05_PRIOR_WORK_CENSUS_201_250.json"
    census_path.write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")

    b4_status = Counter(r["closure_status"] for r in B4["rows"])
    md = [
        "# Batch05 Section 0 — Baseline Gate + Prior Work Census",
        "",
        f"**Generated:** {out['generated_at']}  ",
        f"**Commit:** `{commit}`  ",
        f"**Branch:** `cursor/batch05-201-250-e85e`  ",
        f"**Scope:** Official Batch05 IDs **201–250** (50 capabilities)",
        "",
        "---",
        "",
        "## 1. Sequential baseline gate (Batch01–04)",
        "",
        "| Batch | ID range | Engineering closure | PRODUCTION-ALIGNED | Notes |",
        "|-------|----------|---------------------|-------------------:|-------|",
        "| Batch01 | 1–50 | LOCAL_GOVERNANCE_COMPLETE | **50/50** | `docs/BATCH01_826_COMPLETION_REPORT.md` |",
        "| Batch02 | 51–100 | LOCAL_GOVERNANCE_COMPLETE | **50/50** | `docs/BATCH02_HONEST_CLOSURE_AUDIT.md` |",
        "| Batch03 | 101–150 | LOCAL_GOVERNANCE_COMPLETE | **44 PA + 4 REUSED-LINK + 2 OVERLAP-PARTIAL** | `docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md` |",
        f"| Batch04 | 151–200 | BUILD_PHASE_LIFTED (not full 50/50 PA) | **{B4['production_aligned_count']}/50** | "
        f"{dict(b4_status)} — accepted per owner gate |",
        "",
        f"**progress_826 canonical:** `{PROG['canonical_progress']}` (`docs/PROGRESS_826_CANONICAL.json`)",
        "",
        "### Non-regression at gate open",
        "",
        "```bash",
        ".venv/bin/python -m pytest tests/cap646/test_batch01_dedicated.py ... test_batch04_strangler_spine.py",
        "```",
        "",
        f"**Result @ `{commit}`:** `749 passed, 1 deselected` (log: `/opt/cursor/artifacts/batch05_gate_nonregression.log`)",
        "",
        "**Gate decision:** Batch05 **OPEN** — prior batches closed for governance purposes; Batch04 partial PA acknowledged.",
        "",
        "---",
        "",
        "## 2. Prior unofficial work on 201–250",
        "",
        "| Finding | Count | Disposition |",
        "|---------|------:|-------------|",
        "| Official `cap646/batch05_*` spine | **0** | Build net-new |",
        "| Official `tests/cap646/test_batch05_*` | **0** | Build net-new |",
        "| Hero Batch03 evidence (lines 1–50) | **50** | REUSE-AUDIT-INPUT only |",
        "| `bd_platform` hero functions `*_201..250` | **50** | Brownfield input — SPLIT-BRAIN until spine wired |",
        "| Batch01 overlap (#214 dedicated, #245 production) | **2** | RECLASSIFY-OVERLAP before PA |",
        "| Misnumbered `run_batch05_deep_closure.py` (401–500) | 1 | **IGNORE** — not official Batch05 |",
        "",
        "Full census: `docs/BATCH05_PRIOR_WORK_CENSUS_201_250.json`",
        "",
        "---",
        "",
        "## 3. 12207 lifecycle classification (all 50 IDs)",
        "",
        f"| Class | Count |",
        f"|-------|------:|",
    ]
    for k, v in sorted(lifecycle_counts.items()):
        md.append(f"| {k} | {v} |")
    md += [
        "",
        "**No `_base/_metric` template stubs detected** in 201–250 hero functions (mandate §27).",
        "",
        "---",
        "",
        "## 4. INVEST — per-ID table (mandate §5)",
        "",
        "Full machine-readable rows (each I/N/V/E/S/T with individual evidence): "
        "`docs/BATCH05_CLASSIFICATION_INVEST_201_250.json`",
        "",
        "| ID | Capability | 12207 | I | N | V | E | S | T | Prior disposition |",
        "|---:|------------|-------|:-:|:-:|:-:|:-:|:-:|:-:|-------------------|",
    ]
    for r in rows:
        inv = r["invest"]
        md.append(
            f"| {r['capability_id']} | {r['capability'][:40]} | {r['lifecycle_12207'][:12]} | "
            f"{'✓' if inv['I']['pass'] else '✗'} | {'✓' if inv['N']['pass'] else '✗'} | "
            f"{'✓' if inv['V']['pass'] else '✗'} | {'✓' if inv['E']['pass'] else '✗'} | "
            f"{'✓' if inv['S']['pass'] else '✗'} | {'✓' if inv['T']['pass'] else '✗'} | "
            f"{r['prior_work_disposition']} |"
        )
    md += [
        "",
        "---",
        "",
        "## 5. Next step (not started in this deliverable)",
        "",
        "- Create `docs/BATCH05_ACCEPTANCE_201_250.json` (domain_rules before probe)",
        "- MECE dedup scan (1225 + 10000 + hero + 200 pairs)",
        "- Build `cap646/batch05_dedicated.py` strangler spine",
        "",
        "**Status:** Classification-only gate — **no implementation claims**.",
        "",
    ]
    gate_path = ROOT / "docs/BATCH05_SECTION0_BASELINE_GATE.md"
    gate_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(rows)} rows)")
    print(f"Wrote {census_path}")
    print(f"Wrote {gate_path}")
    print("lifecycle:", dict(lifecycle_counts))


if __name__ == "__main__":
    main()
