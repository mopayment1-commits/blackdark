"""Batch11 #525 canonical reuse proof against #74."""

from __future__ import annotations

import pytest

from bd_platform.heroes_capability_layer import strategy_backtesting_525
from bd_platform.pro_trader_layer import run_backtest_74
from pdf_capability_registry import discover_bindings, execute_capability


def test_binding_is_hero_facade_not_shared_core():
    mod, fn = discover_bindings()[525]
    assert mod == "bd_platform.heroes_capability_layer"
    assert fn == "strategy_backtesting_525"


def test_semantic_equivalence_facade_vs_canonical():
    facade = strategy_backtesting_525(symbol="ETH")
    canonical = run_backtest_74(asset="ETH")
    assert facade.get("ok") is True
    assert canonical.get("ok") is True
    assert facade.get("performance") == canonical.get("performance")
    assert facade.get("rules") == canonical.get("rules")


@pytest.mark.asyncio
async def test_cap646_runtime_path_resolves_hero_facade():
    from cap646.runtime import execute_capability as cap646_execute

    result = await cap646_execute(525, skip_entitlement=True, params={"symbol": "BTC"})
    assert result.get("success") is True, result
    assert result.get("backend_module") == "bd_platform.heroes_capability_layer"
    assert result.get("backend_entrypoint") == "strategy_backtesting_525"


def test_no_batch11_semantic_rule_for_525():
    from bd_platform.batch11_semantic_engine import CAPABILITY_SEMANTIC_SPECS

    assert 525 not in CAPABILITY_SEMANTIC_SPECS
