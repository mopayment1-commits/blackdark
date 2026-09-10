"""Regression: pytest must not mutate canonical production-like data files."""

from __future__ import annotations

from pathlib import Path

import oracle_audit_chain as chain


def test_oracle_chain_isolated_from_repo_data():
    repo_chain = Path("data/oracle_audit_chain.jsonl").resolve()
    active = chain.chain_path().resolve()
    assert active != repo_chain
    assert "canonical_isolation" in str(active) or "pytest" in str(active).lower()


def test_canonical_guard_paths_exist_and_are_not_test_chain():
    guarded = Path("data/oracle_audit_chain.jsonl")
    assert guarded.is_file()
    assert chain.chain_path().resolve() != guarded.resolve()
