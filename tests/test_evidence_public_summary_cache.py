"""Public evidence summary cache."""

from __future__ import annotations

import evidence_public_summary as eps


def test_evidence_public_summary_cache_reuses_body(monkeypatch):
    monkeypatch.setattr(eps, "_cache", None)
    monkeypatch.setattr(eps, "EVIDENCE_PUBLIC_SUMMARY_CACHE_TTL_SEC", 60.0)

    first = eps.get_cached_evidence_public_summary()
    second = eps.get_cached_evidence_public_summary()

    assert first == second
    assert first["differentiators"] == ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
    assert "committee_checklist" not in first
    first["differentiators"].append("mutated")
    third = eps.get_cached_evidence_public_summary()
    assert "mutated" not in third["differentiators"]
