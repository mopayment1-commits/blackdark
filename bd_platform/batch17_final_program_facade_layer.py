"""Batch17 final-program facade layer — capabilities #801–#826."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from bd_platform.batch17_three_spec_foundations import attach_three_spec_metadata
from bd_platform.extension_facade_dispatcher import execute_extension_facade, load_canonical_map

logger = logging.getLogger("BLACKDARK.Batch17FinalProgramFacade")

_MAP_PATH = Path(__file__).resolve().parents[1] / "scripts/partial_batches/batch_17_canonical_map.json"
_CANONICAL_MAP = load_canonical_map(_MAP_PATH)


def reset_batch17_final_program_state() -> None:
    return None


def execute_batch17_facade(
    *,
    capability_id: int,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return execute_extension_facade(
        capability_id=capability_id,
        canonical_map=_CANONICAL_MAP,
        facade_layer="batch17_final_program_facade",
        attach_metadata=attach_three_spec_metadata,
        symbol=symbol,
        seed=seed,
    )
