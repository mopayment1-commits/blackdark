"""Tests — Security-First Architecture (#192)."""

from __future__ import annotations

import pytest

from bd_platform import security_first_architecture as sfa


def test_threat_model_documented():
    summary = sfa.threat_model_summary()
    assert summary["ok"] is True
    assert summary["documented"] is True
    assert summary["actor_count"] >= 3
    assert summary["vector_count"] >= 3
    assert summary["mitigation_count"] >= 3
    assert summary["sla_met"] is True


def test_no_secrets_in_architecture_status():
    status = sfa.security_first_architecture_status()
    assert status["secrets_exposed"] is False
    raw = str(status)
    # Ensure no actual secret material patterns
    forbidden = ["api_key=sk_", "password=secret", "Bearer eyJ", "super-secret"]
    for token in forbidden:
        assert token not in raw


def test_envelope_encryption_available():
    controls = sfa.security_controls_matrix()
    enc = controls["envelope_encryption"]
    assert enc["envelope_encryption"] is True
    assert enc["plaintext_storage"] is False
    assert enc["plaintext_logging"] is False


def test_fail_closed_controls():
    controls = sfa.security_controls_matrix()
    fc = controls["fail_closed"]
    assert fc["auth_service_failure"] == "deny_all"
    assert fc["circuit_breaker_integration"] == "#190"


def test_secret_rotation_integrated():
    controls = sfa.security_controls_matrix()
    rot = controls["secret_rotation"]
    assert rot["automatic_rotation_supported"] is True
    assert rot["immediate_revocation"] is True


def test_security_testing_evidence():
    evidence = sfa.security_testing_evidence()
    assert evidence["ok"] is True
    assert len(evidence["checks"]) >= 2
    assert evidence["sast_dast_dependency_tests"] is True


def test_incident_paths_documented():
    paths = sfa.incident_response_paths()
    assert paths["ok"] is True
    assert len(paths["paths"]) >= 3
    ids = {p["id"] for p in paths["paths"]}
    assert "circuit_breaker_trip" in ids
    assert "credential_compromise" in ids


def test_architecture_status_acceptance():
    status = sfa.security_first_architecture_status()
    assert status["ok"] is True
    assert status["feature_id"] == 192
    assert status["secrets_exposed"] is False
    assert status["acceptance_met"] is True
    assert status["sla_met"] is True
    assert "#165" in status["integrated_features"]
    assert "#190" in status["integrated_features"]
