"""Behavioral coverage for failure.injection (engineering fault paths)."""

from __future__ import annotations

import pytest

from failure.injection import FAULT_MATRIX, FaultKind, inject_fault


@pytest.mark.parametrize("kind", list(FaultKind))
def test_inject_fault_every_kind(kind: FaultKind):
    out = inject_fault(kind, correlation_id="sonar-cov")
    assert isinstance(out, dict)
    assert out


def test_fault_matrix_lists_all_kinds():
    assert set(FAULT_MATRIX) == {k.value for k in FaultKind}
