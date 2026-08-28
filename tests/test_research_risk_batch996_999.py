"""Tests — Batch 37: #996 Market Insights, #997 Portal, #998 Research Reports, #999 Risk Assessment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import portfolio_ai_risk_assessment as risk_assess
from bd_platform import research_intelligence_portal as portal


@pytest.fixture
def portal_seed() -> dict:
    return json.loads(Path("data/research_intelligence_portal_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def risk_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_risk_assessment_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    portal.reset_research_portal_state()
    risk_assess.reset_risk_assessment_state()
    yield
    portal.reset_research_portal_state()
    risk_assess.reset_risk_assessment_state()


# --- #997 Research Intelligence Portal (master) ---


def test_997_master_status(portal_seed):
    status = portal.research_portal_status_997(seed=portal_seed)
    assert status["master_layer"] is True
    assert status["tenant_isolation"] is True
    assert status["chart_reproducibility"] is True
    assert 996 in status["merged_refs"].values()
    assert 998 in status["merged_refs"].values()
    assert "market_insights" in status["tabs"]
    assert "research_report" in status["tabs"]


# --- #996 Market Insights ---


def test_996_market_insights_weekly(portal_seed):
    report = portal.generate_market_insights_996(seed=portal_seed)
    assert report["ok"] is True
    assert len(report["sections"]) == 4
    assert report["all_claims_traceable"] is True
    assert report["publication_timestamp"] is not None
    assert report["charts_reproducible"] is True
    assert report["dataset_version"] is not None


def test_996_no_daily_duplicate(portal_seed):
    result = portal.generate_market_insights_996(frequency="daily", seed=portal_seed)
    assert result["error"] == "daily_covered_by_474_daily_brief"


def test_996_e2e(portal_seed):
    e2e = portal.run_market_insights_e2e_996(seed=portal_seed)
    assert e2e["all_passed"] is True


# --- #998 Research Reports ---


def test_998_weekly_report(portal_seed):
    report = portal.generate_research_report_998(frequency="weekly", seed=portal_seed)
    assert report["ok"] is True
    assert len(report["sections"]) == 4
    assert report["all_claims_sourced"] is True
    assert report["publication_version_archive"] is True


def test_998_on_demand_report(portal_seed):
    report = portal.generate_research_report_998(
        frequency="on_demand",
        assets=["BTC", "SOL"],
        time_range="30d",
        seed=portal_seed,
    )
    assert report["ok"] is True
    assert "BTC" in report["assets"]
    assert report["time_range"] == "30d"


def test_998_e2e(portal_seed):
    e2e = portal.run_research_report_e2e_998(seed=portal_seed)
    assert e2e["all_passed"] is True


def test_997_publication_archive(portal_seed):
    portal.generate_market_insights_996(seed=portal_seed)
    archive = portal.list_report_publication_archive_997(seed=portal_seed)
    assert archive["publication_version_archive"] is True
    assert archive["count"] >= 2


# --- #999 Risk Assessment ---


def test_999_status(risk_seed):
    status = risk_assess.risk_assessment_status_999(seed=risk_seed)
    assert status["standalone_rejected"] is True
    assert status["insight_only"] is True
    assert status["no_execution_blocking"] is True
    assert "PASS" in status["execution_terms_rejected"]
    assert status["risk_budget_visual_only"] is True


def test_999_assessment_insight_only(risk_seed):
    result = risk_assess.run_risk_assessment_999("demo_portfolio", seed=risk_seed)
    assert result["ok"] is True
    assert result["risk_label"] in ("Low Risk", "Elevated Risk", "High Risk")
    assert result["legacy_terms_rejected"]["BLOCK"] is False
    assert result["no_execution_blocking"] is True
    assert result["risk_budget"]["visual_indicator_only"] is True
    assert result["override_audit"]["override_audit"] is True


def test_999_extreme_volatility_high_risk(risk_seed):
    result = risk_assess.run_risk_assessment_999("extreme_volatility", seed=risk_seed)
    assert result["risk_level"] == "high_risk"
    assert result["risk_label"] == "High Risk"


def test_999_negative_tests(risk_seed):
    negative = risk_assess.run_negative_tests_999(seed=risk_seed)
    assert negative["ok"] is True
    assert negative["passed"] == negative["total"]


def test_999_e2e(risk_seed):
    e2e = risk_assess.run_risk_assessment_e2e_999(seed=risk_seed)
    assert e2e["all_passed"] is True


# --- Portal e2e includes new templates ---


def test_997_portal_e2e_includes_996_998(portal_seed):
    e2e = portal.run_research_portal_e2e(seed=portal_seed)
    assert e2e["all_passed"] is True
    assert 996 in e2e["feature_refs"]
    assert 998 in e2e["feature_refs"]


# --- Regression batch 36 ---


def test_batch36_query_governance_regression():
    from bd_platform.data_engine_query_performance_governance import run_query_governance_e2e_990

    e2e = run_query_governance_e2e_990()
    assert e2e["all_passed"] is True
