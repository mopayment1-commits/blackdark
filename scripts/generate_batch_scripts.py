#!/usr/bin/env python3
"""Generate per-batch RBAS scripts from Batch06 templates (Run 021)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.batch_rbas_config import BatchRbasConfig, batch_id_range  # noqa: E402


def _replace_batch(text: str, cfg: BatchRbasConfig) -> str:
    n = cfg.batch_num
    prev = n - 1
    prev_cfg = BatchRbasConfig(prev) if n > 1 else None
    bn = f"batch{n:02d}"
    prev_bn = f"batch{prev:02d}" if prev >= 1 else "batch06"
    text = text.replace("batch06", bn)
    text = text.replace("Batch06", f"Batch{n:02d}")
    text = text.replace("Batch 06", f"Batch {n:02d}")
    text = text.replace("BATCH06", f"BATCH{n:02d}")
    text = text.replace("Run 016", f"Run 0{20+n}" if n < 10 else f"Run {20+n}")
    text = text.replace("Run 015", f"Run 0{19+n}" if n < 10 else f"Run {19+n}")
    text = text.replace("Master Contract 016", f"Master Contract {20+n}")
    text = text.replace("Master Contract 015", f"Master Contract {19+n}")
    text = text.replace("Run 016", f"Run {20+n}")
    text = text.replace("Run 015", f"Run {19+n}")
    if prev_cfg:
        text = text.replace(f"range({prev_cfg.id_start}, {prev_cfg.id_end + 1})", f"range({cfg.id_start}, {cfg.id_end + 1})")
        text = text.replace(f"{prev_cfg.id_start}–{prev_cfg.id_end}", f"{cfg.id_start}–{cfg.id_end}")
        text = text.replace(f"{prev_cfg.id_start}-{prev_cfg.id_end}", f"{cfg.id_start}-{cfg.id_end}")
        text = text.replace(f"IDs {prev_cfg.id_start}–{prev_cfg.id_end}", f"IDs {cfg.id_start}–{cfg.id_end}")
        text = text.replace(f"({prev_cfg.id_start}–{prev_cfg.id_end})", f"({cfg.id_start}–{cfg.id_end})")
    text = text.replace(f"batch{prev:02d}_tier_map", f"batch_tier_map({n})")
    text = text.replace(f"write_batch{prev:02d}_tier_table", f"write_batch_tier_table({n},")
    text = text.replace(f"WF027_IN_BATCH{prev:02d}", f"WF027_IN_BATCH{n:02d}")
    # Fix tier map import
    text = re.sub(
        rf"from scripts\.rbas001_scoping import \(\n    WF027_DORMANT_LEGACY_IDS,\n    WF027_IN_BATCH{n:02d},\n    batch_tier_map\({n}\),\n\)",
        f"from scripts.rbas001_scoping import (\n    WF027_DORMANT_LEGACY_IDS,\n    batch_tier_map,\n)\n\n"
        f"WF027_IN_BATCH{n:02d} = frozenset()  # populated at runtime\n\n"
        f"def batch{n:02d}_tier_map():\n    return batch_tier_map({n})\n",
        text,
        count=1,
    )
    text = text.replace(f"BATCH{n:02d}_RANGE = range({cfg.id_start}, {cfg.id_end + 1})", f"BATCH{n:02d}_RANGE = range({cfg.id_start}, {cfg.id_end + 1})")
    # Remove batch-specific ID constants from closure (277, tier2 lists) — generic closure needed
    return text


def _fix_audit_imports(text: str, cfg: BatchRbasConfig) -> str:
    n = cfg.batch_num
    import_block = f'''from scripts.rbas001_scoping import (
    WF027_DORMANT_LEGACY_IDS,
    WF027_UNRESOLVED_LEGACY_IDS,
    batch_tier_map,
)

def batch{n:02d}_tier_map():
    return batch_tier_map({n})


WF027_IN_BATCH{n:02d} = WF027_UNRESOLVED_LEGACY_IDS & set(range({cfg.id_start}, {cfg.id_end + 1}))
'''
    text = re.sub(
        r"from scripts\.rbas001_scoping import \(.*?\)\n",
        import_block,
        text,
        count=1,
        flags=re.S,
    )
    text = text.replace("batch06_tier_map()", f"batch{n:02d}_tier_map()")
    text = text.replace("batch07_tier_map()", f"batch{n:02d}_tier_map()")
    # Remove stale batch06 decision cap constants — derive from tier map at runtime
    text = re.sub(
        r"DECISION_CAP_IDS = \{.*?\}\nAI_CAP_IDS = \{.*?\}\nWALLET_CAP_IDS.*?\n",
        "DECISION_CAP_IDS: frozenset[int] = frozenset()\nAI_CAP_IDS: frozenset[int] = frozenset()\nWALLET_CAP_IDS: frozenset[int] = frozenset()\n",
        text,
        count=1,
        flags=re.S,
    )
    return text


def generate_audit(cfg: BatchRbasConfig) -> Path:
    src = (ROOT / "scripts/independent_batch06_rbas_audit.py").read_text(encoding="utf-8")
    out = ROOT / f"scripts/independent_batch{cfg.batch_num:02d}_rbas_audit.py"
    text = _replace_batch(src, cfg)
    text = text.replace("range(251, 301)", f"range({cfg.id_start}, {cfg.id_end + 1})")
    text = _fix_audit_imports(text, cfg)
    registry_block = '''def routing_overlap_map() -> dict[int, list[str]]:
    from cap646.batch_registry import routing_overlap_map as _map
    return _map()
'''
    text = re.sub(
        r"def routing_overlap_map\(\).*?return _routing_overlap_cache\n",
        registry_block,
        text,
        count=1,
        flags=re.S,
    )
    # routing overlap - import all batches via registry
    registry_block = '''def routing_overlap_map() -> dict[int, list[str]]:
    from cap646.batch_registry import routing_overlap_map as _map
    return _map()
'''
    text = re.sub(r"def routing_overlap_map\(\).*?return _routing_overlap_cache\n", registry_block, text, count=1, flags=re.S)
    out.write_text(text, encoding="utf-8")
    return out


def generate_opening(cfg: BatchRbasConfig) -> Path:
    src = (ROOT / "scripts/run015_batch06_rbas_opening.py").read_text(encoding="utf-8")
    out = ROOT / f"scripts/run_batch{cfg.batch_num:02d}_rbas_opening.py"
    text = _replace_batch(src, cfg)
    text = text.replace("independent_batch06_rbas_audit", f"independent_batch{cfg.batch_num:02d}_rbas_audit")
    text = text.replace("write_batch06_tier_table", f"write_batch_tier_table({cfg.batch_num},")
    out.write_text(text, encoding="utf-8")
    return out


def generate_closure(cfg: BatchRbasConfig) -> Path:
    src = (ROOT / "scripts/run016_batch06_final_closure.py").read_text(encoding="utf-8")
    out = ROOT / f"scripts/run_batch{cfg.batch_num:02d}_final_closure.py"
    text = _replace_batch(src, cfg)
    text = text.replace("independent_batch06_rbas_audit", f"independent_batch{cfg.batch_num:02d}_rbas_audit")
    text = text.replace("BATCH06_OFFICIAL_RTM_251_300", f"BATCH{cfg.batch_num:02d}_OFFICIAL_RTM_{cfg.id_start}_{cfg.id_end}")
    # Strip ID277-specific block for generic batches — replace with no-op stub
    text = re.sub(
        r"async def id277_fatf_phase6_analysis\(\).*?return \{",
        "async def id277_fatf_phase6_analysis() -> dict[str, Any]:\n    return {",
        text,
        count=1,
        flags=re.S,
    )
    if cfg.batch_num != 6:
        text = re.sub(
            r"async def id277_fatf_phase6_analysis\(\) -> dict\[str, Any\]:\n    return \{.*?\n    \}\n",
            "async def batch_special_analysis() -> dict[str, Any] | None:\n    return None\n\n",
            text,
            count=1,
            flags=re.S,
        )
        text = text.replace("id277_fatf_analysis", "batch_special_analysis")
        text = text.replace("id277_fatf_disambiguation_required", "special_disambiguation_required")
        text = text.replace('"id277_disambiguation_complete": true', '"special_disambiguation_complete": true')
        text = text.replace("id277_fatf_disambiguation", "special_disambiguation")
    # Generic non-regression: all prior closed batches
    prior_scripts = []
    for p in range(1, cfg.batch_num):
        prior_scripts.append(f'        ("run_batch{p:02d}_final_closure.py", "batch{p:02d}"),')
    if cfg.batch_num <= 6:
        prior_scripts = [
            '        ("run005_batch01_final_closure.py", "batch01"),',
            '        ("run007_batch02_final_closure.py", "batch02"),',
            '        ("run010_batch03_final_closure.py", "batch03"),',
            '        ("run012_batch04_final_closure.py", "batch04"),',
            '        ("run014_batch05_final_closure.py", "batch05"),',
        ]
        if cfg.batch_num >= 6:
            prior_scripts.append('        ("run016_batch06_final_closure.py", "batch06"),')
    nr_block = "    scripts = [\n" + "\n".join(prior_scripts) + "\n    ]"
    text = re.sub(r"    scripts = \[.*?\]", nr_block, text, count=1, flags=re.S)
    out.write_text(text, encoding="utf-8")
    return out


def generate_all(batch_num: int) -> dict[str, Path]:
    cfg = BatchRbasConfig(batch_num)
    return {
        "audit": generate_audit(cfg),
        "opening": generate_opening(cfg),
        "closure": generate_closure(cfg),
    }


def main() -> None:
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(7, 18))
    for n in nums:
        paths = generate_all(n)
        print(f"Generated batch{n:02d}: {', '.join(p.name for p in paths.values())}")


if __name__ == "__main__":
    main()
