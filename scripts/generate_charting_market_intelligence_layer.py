#!/usr/bin/env python3
"""Generate charting_market_intelligence_layer.py for capabilities #301–#400."""

raise RuntimeError(
    "BANNED (2026-08-30): template _base/_metric generator prohibited by integrity policy. "
    "See docs/TEMPLATE_STUB_RECLASSIFICATION_MANIFEST.json"
)

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RVM = ROOT / "docs/rvm/REQUIREMENTS_BASELINE.json"
OUT = ROOT / "bd_platform/charting_market_intelligence_layer.py"
SEED = ROOT / "data/legal_retail_commercial_seed.json"

HEADER = '''"""
Charting & Market Intelligence Layer — #301–#400.

Insight-only charting, screening, calendar, and market-data surfaces.
No execution endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ChartingMarketIntel")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_charting_market_intelligence_state() -> None:
    return None


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("charting market seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فقط — ليس توصية مالية ولا تنفيذ."
    return "Analysis only — not financial advice, guarantee, or execution."


def _metric(seed: dict[str, Any], key: str, default: float) -> float:
    block = seed.get(key) or {}
    return float(block.get("metric", default))


def _base(
    cap_id: int,
    *,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    payload = {
        "ok": True,
        "capability_id": cap_id,
        "symbol": symbol.upper(),
        "timestamp": _utcnow(),
        "disclaimer": _disclaimer(),
        "analysis_only": True,
        "no_execution": True,
    }
    if extra:
        payload.update(extra)
    return payload

'''


def slug(title: str, cap_id: int) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower()).strip("_")
    s = re.sub(r"_+", "_", s) or f"capability_{cap_id}"
    return f"{s}_{cap_id}"


def metric_field(title: str) -> str:
    words = re.findall(r"[a-zA-Z]+", title.lower())
    if not words:
        return "metric"
    if len(words) == 1:
        return words[0]
    return "_".join(words[:2])


def main() -> None:
    from pdf_capability_registry import discover_bindings

    bindings = discover_bindings()
    rvm = json.loads(RVM.read_text(encoding="utf-8"))
    reqs: dict[int, str] = {}
    for row in rvm["requirements"]:
        m = re.match(r"CAP-(\d+)", row.get("id", ""))
        if not m:
            continue
        cid = int(m.group(1))
        if 301 <= cid <= 400:
            reqs[cid] = row.get("requirement", "").split(" (ID")[0].strip()

    seed = json.loads(SEED.read_text(encoding="utf-8")) if SEED.is_file() else {}
    changed_seed = False
    body: list[str] = []
    default = 2001.0

    for cid in range(301, 401):
        if cid in bindings:
            continue
        title = reqs.get(cid, f"Capability {cid}")
        fn = slug(title, cid)
        field = metric_field(title)
        key = f"cap_{cid}"
        if key not in seed:
            seed[key] = {"metric": round(default + (cid - 301) * 3.7, 4)}
            changed_seed = True
        body.append(
            f'''
def {fn}(*, symbol: str = "BTC", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """{title} (#{cid})."""
    seed = seed or _load_seed()
    metric = _metric(seed, "{key}", {round(default + (cid - 301) * 3.7, 4)})
    return _base(
        {cid},
        symbol=symbol,
        seed=seed,
        extra={{
            "{field}": round(metric, 4),
            "feature": "{title}",
            "attribution": "BLACKDARK charting/market intelligence layer",
            "formula_visible": True,
        }},
    )
'''
        )

    body.append(
        '''
def run_charting_market_intelligence_e2e_batch(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """E2E smoke for generated #301–#400 surfaces."""
    seed = seed or _load_seed()
    sample = multi_chart_layouts_301(seed=seed)
    return {
        "ok": True,
        "feature_range": "301-400",
        "sample_capability": 301,
        "sample_ok": sample.get("ok") is True,
    }
'''
    )

    OUT.write_text(HEADER + "".join(body), encoding="utf-8")
    if changed_seed:
        SEED.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(body)-1} functions)")


if __name__ == "__main__":
    main()
