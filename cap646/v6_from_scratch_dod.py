"""From-scratch institutional DoD — deepest v6 meaning (§2.1 + §3 + §4).

Rejects thin dedicated wrappers (wrap_with_backend-only) and requires:
- Per-capability dedicated handler in the official batch module
- Real domain payload (not generic domain_result shell)
- Per-capability regression test reference
- All thirteen §2.1 gates (delegates to v6_true_institutional_dod)
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from cap646.batch_constants import batch_number, official_batch_name
from cap646.catalog import catalog_by_id
from cap646.v6_true_institutional_dod import verify_v6_true_institutional

ROOT = Path(__file__).resolve().parent.parent

_THIN_WRAPPER_MARKERS = (
    "wrap_with_backend",
    "binding_path': 'dedicated_semantic_wrapper'",
    'binding_path": "dedicated_semantic_wrapper"',
    "invoke_semantic_backend",
)


@lru_cache(maxsize=1)
def _batch_dedicated_sources() -> dict[int, tuple[str, str]]:
    """capability_id -> (module_name, handler_name)."""
    out: dict[int, tuple[str, str]] = {}
    for path in sorted((ROOT / "cap646").glob("batch*_dedicated.py")):
        mod = f"cap646.{path.stem}"
        text = path.read_text(encoding="utf-8", errors="ignore")
        # dispatch tables: { 6: _cap006_..., 151: _cap151, ... }
        for m in re.finditer(r"^\s*(\d+):\s*(_cap\d+[_a-z0-9]*)", text, re.MULTILINE):
            cid = int(m.group(1))
            out[cid] = (mod, m.group(2))
        for m in re.finditer(r"async def (_cap\d+(?:_[a-z0-9_]+)?)\(", text):
            handler = m.group(1)
            cid_m = re.match(r"_cap(\d+)", handler)
            if cid_m:
                out.setdefault(int(cid_m.group(1)), (mod, handler))
    return out


@lru_cache(maxsize=1)
def _per_cap_test_ids() -> frozenset[int]:
    ids: set[int] = set()
    tests_root = ROOT / "tests" / "cap646"
    if not tests_root.is_dir():
        return frozenset()
    for path in tests_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(
            r"test_cap_?(\d{1,3})|capability_id[\"']?\s*[:=]\s*(\d+)|execute\((\d+),",
            text,
        ):
            for g in m.groups():
                if g and 1 <= int(g) <= 826:
                    ids.add(int(g))
        for m in re.finditer(r"range\((\d+),\s*(\d+)\)", text):
            start, end = int(m.group(1)), int(m.group(2))
            for cid in range(start, end):
                if 1 <= cid <= 826:
                    ids.add(cid)
    return frozenset(ids)


def _handler_is_thin_wrapper(capability_id: int) -> tuple[bool, str]:
    src = _batch_dedicated_sources().get(capability_id)
    if not src:
        return True, "no_dedicated_handler"
    mod_name, handler = src
    path = ROOT / "cap646" / f"{mod_name.split('.')[-1]}.py"
    if not path.is_file():
        return True, "dedicated_module_missing"
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Extract handler body (rough slice between def and next async def)
    pattern = rf"async def {handler}\([^)]*\)[^:]*:(.*?)(?=\nasync def _cap|\nasync def execute|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    body = m.group(1) if m else ""
    if "return await wrap_with_backend(" in body and body.count("\n") < 12:
        return True, "thin_wrap_with_backend_only"
    if any(marker in body for marker in _THIN_WRAPPER_MARKERS) and "ingestion_architecture_report" not in body:
        if body.strip().count("\n") < 8:
            return True, "thin_semantic_wrapper"
    return False, "dedicated_domain_handler"


def _classify_prebuild_state(capability_id: int, true_result: dict[str, Any]) -> str:
    if true_result.get("verdict") == "CANONICALLY_COVERED":
        return "DUPLICATE_ALIAS"
    if true_result.get("verdict") == "EXTERNAL_BLOCKED":
        return "EXTERNAL_BLOCKED"
    thin, _ = _handler_is_thin_wrapper(capability_id)
    if thin and capability_id not in _per_cap_test_ids():
        return "STUB_TEMPLATE"
    if true_result.get("PASS_ENGINEERING") and not thin:
        return "EXISTING_VERIFIED"
    if true_result.get("PASS_ENGINEERING") and thin:
        return "PARTIAL_CANONICAL"
    return "GREENFIELD"


async def verify_from_scratch(capability_id: int, *, user: dict[str, Any] | None = None) -> dict[str, Any]:
    """Full from-scratch verification for one capability."""
    true = await verify_v6_true_institutional(capability_id, user=user)
    row = catalog_by_id().get(capability_id, {})
    batch = official_batch_name(capability_id)
    thin, thin_reason = _handler_is_thin_wrapper(capability_id)
    has_dedicated = capability_id in _batch_dedicated_sources()
    has_test = capability_id in _per_cap_test_ids()
    prebuild = _classify_prebuild_state(capability_id, true)

    from_scratch_gates = {
        "FS01_official_batch_module": batch_number(capability_id) >= 1,
        "FS02_dedicated_handler": has_dedicated,
        "FS03_not_thin_wrapper": not thin,
        "FS04_per_capability_test": has_test,
        "FS05_v6_thirteen_gates": bool(true.get("PASS_ENGINEERING")),
    }
    fs_failed = [k for k, v in from_scratch_gates.items() if not v]
    pass_from_scratch = len(fs_failed) == 0 and prebuild in {
        "EXISTING_VERIFIED",
        "PARTIAL_CANONICAL",
    }

    return {
        "capability_id": capability_id,
        "capability": row.get("capability", ""),
        "official_batch": batch,
        "prebuild_state": prebuild,
        "PASS_FROM_SCRATCH": pass_from_scratch,
        "verdict": "PASS_FROM_SCRATCH" if pass_from_scratch else "NOT_FROM_SCRATCH",
        "from_scratch_gates": from_scratch_gates,
        "from_scratch_failed": fs_failed,
        "thin_wrapper": thin,
        "thin_wrapper_reason": thin_reason,
        "dedicated_handler": _batch_dedicated_sources().get(capability_id),
        "v6_true": true,
    }
