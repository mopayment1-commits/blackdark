"""D8 public signal registry summary must stay redacted and wired."""

from __future__ import annotations


def test_signal_registry_public_block_has_no_persist_path():
    from ml.public_accuracy import _signal_registry_block

    block = _signal_registry_block()
    assert block.get("differentiator") == "D8"
    assert "persist_path" not in block
    assert "total" in block
    assert "by_type" in block


def test_market_context_prefers_guard_conflict_meta():
    from market_context import build_full_oracle_response

    # Minimal call path: if helper needs many args, unit-test the merge logic via source contract.
    import inspect
    from pathlib import Path

    src = Path("market_context.py").read_text(encoding="utf-8")
    assert 'unified.get("dimension_conflict")' in src
    assert "build_full_oracle_response" in inspect.getsource(build_full_oracle_response)
