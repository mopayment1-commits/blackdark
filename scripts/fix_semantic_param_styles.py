#!/usr/bin/env python3
"""Derive correct param_style per capability from actual function signatures."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.backend_registry import _semantic_binding_for
from cap646.catalog import catalog_by_id, is_duplicate


def infer_param_style(fn) -> str:
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    if not params:
        return "none"
    if "opportunity" in params:
        return "opportunity"
    if "exchange" in params and "asset" in params:
        return "exchange_asset"
    if "amount_usd" in params and "asset" in params:
        return "execution_intelligence"
    if "text" in params:
        return "message"
    if "query" in params:
        return "query"
    if "raw" in params:
        return "raw"
    if "assets" in params:
        return "assets"
    if "user_email" in params:
        return "email"
    if "address" in params and "symbol" not in params and "asset" not in params:
        return "address"
    if "asset" in params and "symbol" not in params:
        return "asset"
    if "symbol" in params:
        return "symbol"
    if "limit" in params:
        return "limit"
    if "chain" in params and len(params) == 1:
        return "chain"
    if "quote_amount" in params or "quote_usd" in params:
        return "quote"
    if len(params) == 1 and params[0] in {"pair", "symbol_or_pair"}:
        return "pair"
    if fn.__name__ in {"hub_stats"}:
        return "none"
    if fn.__name__ in {"compute_net_edge_truth"}:
        return "edge"
    if fn.__name__ in {"build_decision_certificate"}:
        return "cert"
    if fn.__name__ in {"compute_data_provenance_score"}:
        return "provenance"
    return "symbol"


def main() -> int:
    out: dict[str, dict] = {}
    for cid in range(1, 827):
        if not catalog_by_id().get(cid) or is_duplicate(cid):
            continue
        binding = _semantic_binding_for(cid)
        try:
            mod = importlib.import_module(binding.module)
            fn = getattr(mod, binding.entrypoint)
            ps = infer_param_style(fn)
            if ps != binding.param_style:
                out[str(cid)] = {
                    "module": binding.module,
                    "entrypoint": binding.entrypoint,
                    "was": binding.param_style,
                    "correct": ps,
                }
        except Exception as exc:
            out[str(cid)] = {"error": str(exc), "was": binding.param_style}
    path = ROOT / "cap646" / "capability_param_styles.json"
    path.write_text(json.dumps({"overrides": out}, indent=2), encoding="utf-8")
    print(f"wrote {path} — {len(out)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
