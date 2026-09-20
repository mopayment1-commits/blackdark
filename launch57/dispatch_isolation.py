"""Launch-57 dispatch isolation — forbid silent legacy/generic delegate for bound caps."""

from __future__ import annotations


class Launch57LegacyBypassBlocked(RuntimeError):
    """Raised when a Launch-57-bound capability would fall through to legacy handlers."""


def _compute_launch57_bound_capability_ids() -> frozenset[int]:
    from launch57.data_batch1 import LAUNCH57_BATCH1_CAP_IDS
    from launch57.data_batch2 import LAUNCH57_BATCH2_CAP_IDS
    from launch57.decision_batch1 import LAUNCH57_DECISION_BATCH1_CAP_IDS
    from launch57.decision_batch2 import LAUNCH57_DECISION_BATCH2_CAP_IDS
    from launch57.derivatives_batch1 import LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS
    from launch57.derivatives_batch2 import LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS
    from launch57.edge_ui_batch1 import LAUNCH57_EDGE_UI_BATCH1_CAP_IDS
    from launch57.explanation_ai_batch1 import LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS
    from launch57.smart_money_batch1 import LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS
    from launch57.smart_money_batch2 import LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS
    from launch57.smart_money_batch3 import LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS
    from launch57.trust_batch1 import LAUNCH57_TRUST_BATCH1_CAP_IDS

    out: set[int] = set()
    for group in (
        LAUNCH57_BATCH1_CAP_IDS,
        LAUNCH57_BATCH2_CAP_IDS,
        LAUNCH57_DECISION_BATCH1_CAP_IDS,
        LAUNCH57_DECISION_BATCH2_CAP_IDS,
        LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS,
        LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS,
        LAUNCH57_EDGE_UI_BATCH1_CAP_IDS,
        LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS,
        LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS,
        LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS,
        LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS,
        LAUNCH57_TRUST_BATCH1_CAP_IDS,
    ):
        out.update(group)
    return frozenset(out)


# Frozen at import — intercept env hacks must not reopen legacy delegate for bound caps.
LAUNCH57_DISPATCH_BOUND_CAP_IDS: frozenset[int] = _compute_launch57_bound_capability_ids()


def launch57_bound_capability_ids() -> frozenset[int]:
    return LAUNCH57_DISPATCH_BOUND_CAP_IDS


def block_legacy_delegate_for_launch57(capability_id: int) -> None:
    if capability_id in LAUNCH57_DISPATCH_BOUND_CAP_IDS:
        raise Launch57LegacyBypassBlocked(
            f"launch57_isolation: capability {capability_id} requires launch57 handler; "
            "legacy batch*_dedicated/generic delegate forbidden"
        )
