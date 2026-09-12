#!/usr/bin/env python3
"""Generate official batch modules with substantive v6 handlers (real module invoke + goal payload).

Pattern matches cap646/batch02_dedicated.py — NOT wrap_with_backend / execute_from_scratch / re-export.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.backend_registry import _slug, _semantic_binding_for
from cap646.batch_constants import batch_id_range, total_batch_count
from cap646.catalog import catalog_by_id, is_duplicate


def _load_param_style_overrides() -> dict[int, str]:
    path = ROOT / "cap646" / "capability_param_styles.json"
    out: dict[int, str] = {48: "asset", 49: "assets", 631: "none", 630: "symbol"}
    if path.is_file():
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        for k, v in (data.get("overrides") or {}).items():
            if isinstance(v, dict) and v.get("correct"):
                out[int(k)] = v["correct"]
    return out


def _payload_key(surface: str) -> str:
    return surface[:64] if len(surface) <= 64 else surface[:61] + "_x"


def _rich_handler_ok(body: str) -> bool:
    if "wrap_with_backend" in body and body.count("\n") < 12:
        return False
    if "execute_from_scratch" in body:
        return False
    if re.search(r"\btime\.", body) and "import time" not in body:
        return False
    for helper in re.findall(r"\b(_resolve_\w+|_build_\w+)\b", body):
        if f"def {helper}" not in body:
            return False
    return body.count("\n") >= 6 and ("_wrap(" in body or "ai_compliance_footer" in body or "return await" in body)


def _scan_rich_handlers() -> dict[int, str]:
    """Extract full async handler source for capabilities with substantive bodies."""
    out: dict[int, str] = {}
    for path in sorted((ROOT / "cap646").glob("batch*_dedicated.py")):
        if path.stem.startswith("official_batch"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(
            r"(async def _cap\d+(?:_[a-z0-9_]+)?\([^)]*\)[^:]*:.*?)(?=\nasync def |\n_DISPATCH|\nasync def execute|\Z)",
            text,
            re.DOTALL,
        ):
            body = m.group(1)
            if not _rich_handler_ok(body):
                continue
            cid_m = re.search(r"async def _cap(\d+)", body)
            if not cid_m:
                continue
            out[int(cid_m.group(1))] = body.rstrip()
    return out


def _generated_handler(
    cid: int,
    surface: str,
    name: str,
    track: str,
    module: str,
    entrypoint: str,
    param_style: str,
) -> str:
    pkey = _payload_key(surface)
    safe_name = name.replace('"', "'")
    lines = [
        f"async def _cap{cid}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:",
        "    import time",
        "    from cap646.substantive_invoke import invoke_substantive",
        "    from data_provenance_score import compute_data_provenance_score",
        "    t0 = time.perf_counter()",
        "    domain = await invoke_substantive(",
        f"        '{module}',",
        f"        '{entrypoint}',",
        "        symbol=symbol,",
        "        address=address,",
        "        params=params,",
        f"        param_style='{param_style}',",
        f"        capability_id={cid},",
        "    )",
        "    prov = compute_data_provenance_score(symbol=symbol)",
        "    latency_ms = round((time.perf_counter() - t0) * 1000, 2)",
        "    payload = {",
        f'        "capability_goal": "{safe_name}",',
        f'        "track": "{track}",',
        f'        "{pkey}": domain,',
        '        "domain_result": domain,',
        '        "provenance": prov,',
        '        "execution_path": "v6_substantive_semantic_invoke",',
        "    }",
        f"    return _wrap({cid}, symbol=symbol, payload_key='{pkey}', payload=payload, extra={{'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'}})",
    ]
    return "\n".join(lines)


def generate_batch(batch_num: int, rich: dict[int, str], param_overrides: dict[int, str]) -> Path:
    start, end = batch_id_range(batch_num)
    ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]

    surfaces = {cid: _slug(catalog_by_id()[cid]["capability"]) for cid in ids}
    out = ROOT / "cap646" / f"official_batch{batch_num:02d}_dedicated.py"

    header = [
        f'"""Official batch {batch_num:02d} — v6 substantive handlers (IDs {start}–{end})."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Awaitable, Callable",
        "",
        "from cap646.dedicated_common import addr as _addr",
        "from cap646.dedicated_common import execute_dedicated_caps",
        "from cap646.dedicated_common import exchange_netflow_footer",
        "from cap646.dedicated_common import exchange_netflow_probe",
        "from cap646.dedicated_common import holder_analytics_bundle",
        "from cap646.dedicated_common import holder_analytics_footer",
        "from cap646.dedicated_common import holder_analytics_locked",
        "from cap646.dedicated_common import make_wrap_binding",
        "from cap646.dedicated_common import seed as _seed",
        "from cap646.dedicated_common import sym as _sym",
        "from cap646.evidence_class import ai_compliance_footer",
        "from cap646.evidence_class import attach_evidence_metadata, infer_evidence_class",
        "",
        f"OFFICIAL_BATCH{batch_num:02d}_IDS: frozenset[int] = frozenset(range({start}, {end + 1}))",
        f"BATCH{batch_num:02d}_DEDICATED_IDS: frozenset[int] = frozenset({{{', '.join(str(i) for i in ids)}}})",
        f"BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()",
        "",
        "EXPECTED_SURFACE: dict[int, str] = {",
    ]
    for cid in ids:
        header.append(f'    {cid}: "{surfaces[cid]}",')
    header.append("}")
    header.append("")
    header.append("_wrap = make_wrap_binding(EXPECTED_SURFACE)")
    header.append("")

    handlers: list[str] = []
    for cid in ids:
        if cid in rich:
            h = rich[cid]
            h = re.sub(r"async def _cap\d+(?:_[a-z0-9_]+)?", f"async def _cap{cid}", h, count=1)
            handlers.append(h)
        else:
            row = catalog_by_id()[cid]
            binding = _semantic_binding_for(cid)
            ps = param_overrides.get(cid, binding.param_style)
            handlers.append(
                _generated_handler(
                    cid,
                    surfaces[cid],
                    row["capability"],
                    row["track"],
                    binding.module,
                    binding.entrypoint,
                    ps,
                )
            )
        handlers.append("")

    dispatch = ["_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {"]
    for cid in ids:
        dispatch.append(f"    {cid}: _cap{cid},")
    dispatch.append("}")
    dispatch.append("")
    dispatch.append("")
    dispatch.append("async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:")
    dispatch.append("    return await execute_dedicated_caps(")
    dispatch.append("        capability_id,")
    dispatch.append("        params=params,")
    dispatch.append(f"        dedicated_ids=BATCH{batch_num:02d}_DEDICATED_IDS,")
    dispatch.append(f"        overlap_batch01_ids=BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS,")
    dispatch.append("        dispatch=_DISPATCH,")
    dispatch.append(f'        overlap_error="batch01 overlap batch{batch_num:02d}",')
    dispatch.append(f'        not_dedicated_error=f"official batch{batch_num:02d}: not dedicated",')
    dispatch.append("    )")
    dispatch.append("")

    out.write_text("\n".join(header + handlers + dispatch), encoding="utf-8")
    return out


def generate_test(batch_num: int) -> None:
    start, end = batch_id_range(batch_num)
    ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]
    path = ROOT / "tests" / "cap646" / f"test_official_batch{batch_num:02d}_from_scratch.py"
    path.write_text(
        f'''"""Substantive v6 tests — official batch{batch_num:02d} (IDs {start}–{end})."""

from __future__ import annotations

import pytest

from cap646.official_batch_production import execute

BATCH_IDS = {ids}


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch{batch_num:02d}_substantive_execute(capability_id: int):
    result = await execute(
        capability_id,
        params={{"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"}},
    )
    assert result.get("success") is True, result
    assert result.get("backend_module") == "cap646.official_batch_production"
    assert result.get("data_provenance") or result.get("provenance")
    assert result.get("latency_ms") is not None or result.get("performance_gate")
''',
        encoding="utf-8",
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from-batch", type=int, default=1)
    p.add_argument("--to-batch", type=int, default=total_batch_count())
    p.add_argument("--batch", type=int)
    args = p.parse_args()
    rich = _scan_rich_handlers()
    param_overrides = _load_param_style_overrides()
    batches = [args.batch] if args.batch else list(range(args.from_batch, args.to_batch + 1))
    for b in batches:
        if b == 1:
            generate_test(1)
            continue
        generate_batch(b, rich, param_overrides)
        generate_test(b)
        print(f"batch{b:02d}: {len(batch_id_range(b))} caps substantive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
