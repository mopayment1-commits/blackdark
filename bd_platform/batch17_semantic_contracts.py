"""Batch17 semantic contracts for canonical-reuse facades 801-826."""

from __future__ import annotations

from typing import Any

from bd_platform.batch17_membership import BATCH17_IDS, CANONICAL_DUPLICATE_TARGETS
from bd_platform.extension_batch_semantic_contracts import all_contracts as _all_contracts
from bd_platform.extension_batch_semantic_contracts import contract_for as _contract_for


def contract_for(capability_id: int) -> dict[str, Any]:
    return _contract_for(capability_id, canonical_targets=CANONICAL_DUPLICATE_TARGETS)


def all_contracts() -> dict[int, dict[str, Any]]:
    return _all_contracts(batch_ids=BATCH17_IDS, canonical_targets=CANONICAL_DUPLICATE_TARGETS)
