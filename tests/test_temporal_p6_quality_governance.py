"""P6 Quality Governance tests — TEMP-AR-0361..0372, 0455."""

from __future__ import annotations

from blackdark.temporal.quality_governance import (
    EXTERNAL_STANDARDS_GUIDANCE_ONLY,
    FALSE_EXTERNAL_ATTRIBUTION_PROHIBITED,
    InstitutionalReference,
    QualityCharacteristic,
    assess_quality_governance,
    validate_external_attribution_claim,
)


def test_temp_ar_0361_no_false_external_attribution() -> None:
    assert FALSE_EXTERNAL_ATTRIBUTION_PROHIBITED is True
    bad = validate_external_attribution_claim(
        "NIST SP 800-218 SSDF v1.1 certifies our Failure Corpus"
    )
    assert bad["accepted"] is False


def test_temp_ar_0362_functional_correctness() -> None:
    report = assess_quality_governance()
    fc = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.FUNCTIONAL_CORRECTNESS)
    assert fc.supported is True


def test_temp_ar_0363_reliability() -> None:
    report = assess_quality_governance()
    rel = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.RELIABILITY)
    assert rel.supported is True


def test_temp_ar_0364_security() -> None:
    report = assess_quality_governance(runtime_signals={"api_admin_gated": True})
    sec = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.SECURITY)
    assert sec.supported is True
    assert sec.institutional_reference == InstitutionalReference.OWASP_API_2023


def test_temp_ar_0365_maintainability() -> None:
    report = assess_quality_governance()
    maint = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.MAINTAINABILITY)
    assert maint.supported is True


def test_temp_ar_0366_performance_efficiency() -> None:
    report = assess_quality_governance()
    perf = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.PERFORMANCE_EFFICIENCY)
    assert perf.supported is True


def test_temp_ar_0367_traceability() -> None:
    report = assess_quality_governance()
    trace = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.TRACEABILITY)
    assert trace.supported is True


def test_temp_ar_0368_reproducibility() -> None:
    report = assess_quality_governance(runtime_signals={"deterministic_replay": True})
    repro = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.REPRODUCIBILITY)
    assert repro.supported is True


def test_temp_ar_0369_testability() -> None:
    report = assess_quality_governance()
    test = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.TESTABILITY)
    assert test.supported is True


def test_temp_ar_0370_auditability() -> None:
    report = assess_quality_governance()
    audit = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.AUDITABILITY)
    assert audit.supported is True


def test_temp_ar_0371_quality_in_use() -> None:
    report = assess_quality_governance()
    qiu = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.QUALITY_IN_USE)
    assert qiu.supported is True


def test_temp_ar_0372_risk_based_monitoring() -> None:
    report = assess_quality_governance()
    risk = next(a for a in report.assessments if a.characteristic == QualityCharacteristic.RISK_BASED_MONITORING)
    assert risk.supported is True


def test_temp_ar_0455_external_standards_guidance_only() -> None:
    assert EXTERNAL_STANDARDS_GUIDANCE_ONLY is True
    good = validate_external_attribution_claim(
        "OWASP API Security Top 10 2023 guides API security design"
    )
    assert good["guidance_only"] is True
    assert good["accepted"] is True
