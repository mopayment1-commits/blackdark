"""Launch-57 B1 isolation closure — zero legacy freshness/evidence runtime deps."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROHIBITED_IMPORT_ROOTS = frozenset(
    {
        "failure.freshness",
        "cap646.evidence_class",
        "data_governance.freshness",
    }
)

B1_MODULE_PATH = Path(__file__).resolve().parents[2] / "launch57" / "data_batch1.py"


def _import_roots_for_module(module_name: str) -> set[str]:
    source = B1_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(B1_MODULE_PATH))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name)
    return roots


def test_b1_source_has_zero_prohibited_imports():
    roots = _import_roots_for_module("launch57.data_batch1")
    leaked = sorted(roots.intersection(PROHIBITED_IMPORT_ROOTS))
    assert leaked == [], f"prohibited legacy imports remain: {leaked}"


def test_b1_source_text_has_no_prohibited_dependency_tokens():
    text = B1_MODULE_PATH.read_text(encoding="utf-8")
    for token in (
        "from failure.freshness",
        "from cap646.evidence_class",
        "from data_governance.freshness",
        "import failure.freshness",
        "classify_freshness",
        "ai_compliance_footer",
        "attach_data_freshness",
        "reject_if_stale",
    ):
        assert token not in text, f"prohibited legacy token found: {token}"


@pytest.mark.asyncio
async def test_real_time_prices_fails_closed_on_freshness_without_legacy(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 1.0, "source": "binance:api.binance.com", "age_sec": 1.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["legacy_runtime_dependencies"] == 0
    assert out["b1_isolation_leakage"] == 0
    assert out["presented_as_live"] is False
    assert "freshness_state" not in out
    assert any(p["launch_number"] == 41 for p in out["temporal_dependency_pending"])
    assert any(p["launch_number"] == 6 for p in out["temporal_dependency_pending"])


def _assert_no_prohibited_legacy_tokens(text: str) -> None:
    for token in (
        "from failure.freshness",
        "from cap646.evidence_class",
        "from data_governance.freshness",
        "classify_freshness",
        "ai_compliance_footer",
        "attach_data_freshness",
    ):
        if token in text:
            raise AssertionError(f"prohibited legacy token found: {token}")


def test_isolation_guard_fails_when_legacy_dependency_reintroduced():
    clean = B1_MODULE_PATH.read_text(encoding="utf-8")
    _assert_no_prohibited_legacy_tokens(clean)
    poisoned = "from failure.freshness import classify_freshness\n" + clean
    with pytest.raises(AssertionError, match="failure.freshness"):
        _assert_no_prohibited_legacy_tokens(poisoned)
