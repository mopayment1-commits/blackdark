#!/usr/bin/env python3
"""Generate parametrized pytest for batch04–17 dedicated modules."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "cap646" / "test_batch_range_dedicated.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _collect_ids() -> list[int]:
    ids: list[int] = []
    from cap646.batch_constants import batch_number, total_batch_count

    first_batch = batch_number(151)
    for batch_num in range(first_batch, total_batch_count() + 1):
        mod_name = f"cap646.batch{batch_num:02d}_dedicated"
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        dedicated = getattr(mod, f"BATCH{batch_num:02d}_DEDICATED_IDS", frozenset())
        ids.extend(sorted(dedicated))
    return ids


def main() -> int:
    ids = _collect_ids()
    lines = [
        '"""v6 institutional tests — batch04–17 dedicated goal-specific payloads."""',
        "",
        "from __future__ import annotations",
        "",
        "import pytest",
        "",
        "from cap646.batch_range_production import execute",
        "from cap646.backend_registry import resolve_binding",
        "",
        f"DEDICATED_IDS = {ids!r}",
        "",
        "GENERIC_SURFACES = frozenset(",
        '    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}',
        ")",
        "",
        "",
        "@pytest.mark.parametrize('capability_id', DEDICATED_IDS)",
        "@pytest.mark.asyncio",
        "async def test_batch_range_dedicated_surface_and_binding(capability_id: int):",
        "    binding = resolve_binding(capability_id)",
        "    assert binding.source == 'explicit_option_a'",
        "    result = await execute(capability_id, params={'symbol': 'BTC', 'tier': 'whale'})",
        "    assert result.get('success') is True, result",
        "    assert result.get('binding_source') == 'explicit_option_a'",
        "    surface = result.get('surface')",
        "    assert surface and surface not in GENERIC_SURFACES",
        "    assert result.get('latency_ms') is not None or result.get('performance_gate')",
        "    assert result.get('data_provenance') or any(",
        "        k in str(result) for k in ('provenance', 'freshness', 'data_provenance')",
        "    )",
        "",
        "",
        "@pytest.mark.parametrize('capability_id', DEDICATED_IDS)",
        "@pytest.mark.asyncio",
        "async def test_batch_range_dedicated_goal_payload_key(capability_id: int):",
        "    from cap646.batch_constants import batch_number",
        "    batch_num = batch_number(capability_id)",
        "    mod = __import__(f'cap646.batch{batch_num:02d}_dedicated', fromlist=['EXPECTED_SURFACE'])",
        "    expected_surface = mod.EXPECTED_SURFACE[capability_id]",
        "    result = await execute(capability_id, params={'symbol': 'ETH'})",
        "    assert result.get('surface') == expected_surface",
        "    # goal-specific payload key must exist (not bare generic result wrapper)",
        "    payload_keys = [k for k in result.keys() if k not in {",
        "        'capability_id', 'surface', 'symbol', 'success', 'compliance_footer',",
        "        'evidence_metadata', 'classification', 'evidence_class', 'backend_module',",
        "        'backend_entrypoint', 'binding_source', 'production_spine', 'official_batch',",
        "        'capability', 'track', 'latency_ms', 'performance_gate', 'data_provenance',",
        "        'binding_path',",
        "    }]",
        "    assert payload_keys, result",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} with {len(ids)} IDs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
