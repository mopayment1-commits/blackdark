"""Tests for signed load evidence resolution across capability response shapes."""

from __future__ import annotations

from scale_readiness import signed_load_evidence_from_capability_result


def test_signed_from_report_key():
    result = {"report": {"signed_load_evidence": {"present": True}}}
    assert signed_load_evidence_from_capability_result(result) is True


def test_signed_from_capacity_load_evidence_wrapper(monkeypatch):
    monkeypatch.setattr(
        "scale_readiness._signed_load_evidence_present",
        lambda: False,
    )
    result = {
        "capacity_load_evidence": {
            "domain_result": {
                "report": {"signed_load_evidence": {"present": True}},
            }
        }
    }
    assert signed_load_evidence_from_capability_result(result) is True
