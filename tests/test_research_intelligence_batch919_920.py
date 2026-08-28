"""Tests — #919 AI Analyst + #920 AI Deep Research (merged into #997)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import research_intelligence_portal as rip


@pytest.fixture
def rip_seed() -> dict:
    return json.loads(Path("data/research_intelligence_portal_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    rip.reset_research_portal_state()
    yield
    rip.reset_research_portal_state()


def test_997_status(rip_seed):
    status = rip.research_portal_status_997(seed=rip_seed)
    assert status["standalone_rejected"] is True
    assert "nl_query_interface" in status["tabs"]
    assert "deep_research_job" in status["tabs"]
    assert status["insight_only"] is True
    assert status["no_execution"] is True


def test_919_tool_grounded_answer(rip_seed):
    result = rip.ask_ai_analyst_919(
        "What is Bitcoin NVT and on-chain activity?",
        seed=rip_seed,
    )
    assert result["tool_grounded"] is True
    assert result["citations_traceable"] is True
    assert len(result["citations"]) >= 1
    assert result["confidence"] in ("high", "medium", "low")
    assert "not financial advice" in result["disclaimer"].lower()


def test_919_deterministic(rip_seed):
    q = "Bitcoin funding rates and market volume"
    a1 = rip.ask_ai_analyst_919(q, seed=rip_seed)
    a2 = rip.ask_ai_analyst_919(q, seed=rip_seed)
    assert a1["answer_hash"] == a2["answer_hash"]
    assert a2.get("cache_hit") is True


def test_919_insufficient_data(rip_seed):
    result = rip.ask_ai_analyst_919("xyzzy unknown quantum flux", seed=rip_seed)
    assert result["insufficient_data"] is True
    assert result["no_unsupported_inference"] is True


def test_919_advisory_blocked(rip_seed):
    result = rip.ask_ai_analyst_919("Should I buy Bitcoin now?", seed=rip_seed)
    assert result["error"] == "advisory_blocked"


def test_919_fee_db(rip_seed):
    result = rip.ask_ai_analyst_919("BTC on-chain NVT metrics", seed=rip_seed)
    assert result["fee_db"]["total_usd"] > 0


def test_920_plan_and_approval(rip_seed):
    plan = rip.create_deep_research_plan_920(
        "Bitcoin on-chain metrics and funding rates",
        user_id="u1",
        seed=rip_seed,
    )
    assert plan["ok"] is True
    assert plan["job"]["status"] == "awaiting_approval"

    job_id = plan["job"]["job_id"]
    approved = rip.approve_deep_research_plan_920(job_id, user_id="u1", approved=True)
    assert approved["status"] == "queued"


def test_920_execute_report(rip_seed):
    plan = rip.create_deep_research_plan_920(
        "Bitcoin on-chain metrics and funding rates",
        user_id="u1",
        seed=rip_seed,
    )
    job_id = plan["job"]["job_id"]
    rip.approve_deep_research_plan_920(job_id, user_id="u1")

    result = rip.execute_deep_research_job_920(job_id, seed=rip_seed)
    assert result["ok"] is True
    assert result["status"] == "completed"
    report = result["report"]
    assert report["every_material_claim_cited"] is True
    assert report["no_fabricated_source"] is True
    assert report["source_diversity_met"] is True
    assert "summary" in report["sections"]


def test_920_retry_and_manual(rip_seed):
    plan = rip.create_deep_research_plan_920("retry test topic", user_id="u2", seed=rip_seed)
    job_id = plan["job"]["job_id"]
    rip.approve_deep_research_plan_920(job_id, user_id="u2")

    for _ in range(3):
        rip.execute_deep_research_job_920(job_id, simulate_failure=True, seed=rip_seed)

    final = rip.get_deep_research_job_920(job_id)
    assert final["job"]["manual_intervention_required"] is True
    assert final["job"]["status"] == "failed"


def test_997_e2e(rip_seed):
    e2e = rip.run_research_portal_e2e(seed=rip_seed)
    assert e2e["all_passed"] is True
