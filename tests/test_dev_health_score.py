"""Tests — #238 Dev Health Score."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import dev_health_score as dhs


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "dev_health_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 238,
            "methodology_version": "2.1",
            "assets": {
                "BTC": {
                    "project": "Bitcoin Core",
                    "repo": {
                        "url": "https://github.com/bitcoin/bitcoin",
                        "owner": "bitcoin",
                        "name": "bitcoin",
                        "is_fork": False,
                        "ownership": {
                            "verified": True,
                            "method": "GitHub API org mapping + manual check",
                            "last_verified": "2026-08-25",
                        },
                    },
                    "commits": [
                        {"author": "laanwj", "email": "laanwj@gmail.com", "is_bot": False},
                        {"author": "fanquake", "email": "fanquake@gmail.com", "is_bot": False},
                        {"author": "hebasto", "email": "hebasto@gmail.com", "is_bot": False},
                        {"author": "github-actions[bot]", "email": "noreply@github.com", "is_bot": True},
                        {"author": "dependabot[bot]", "email": "noreply@github.com", "is_bot": True},
                        {"author": "sipa", "email": "sipa@ulyssis.org", "is_bot": False},
                    ],
                    "releases": [
                        {"tag": "v28.0", "date": "2026-08-10"},
                        {"tag": "v27.2", "date": "2026-06-26"},
                        {"tag": "v27.1", "date": "2026-04-15"},
                    ],
                    "issues": {
                        "open": 142,
                        "closed_30d": 38,
                        "avg_response_days": 4.2,
                        "bug_count_30d": 12,
                        "feature_count_30d": 26,
                    },
                    "component_scores": {
                        "activity": 7.8,
                        "contributors": 6.5,
                        "releases": 8.2,
                        "issues": 7.0,
                        "community": 9.5,
                    },
                    "trend": {
                        "previous_score": 8.1,
                        "evidence": [
                            "Contributor decline (-2 active contributors)",
                            "Release delay (+15 days vs average)",
                        ],
                    },
                },
                "UNVERIFIED": {
                    "project": "Unknown Fork",
                    "repo": {
                        "url": "https://github.com/random/bitcoin-fork",
                        "is_fork": True,
                        "ownership": {"verified": False},
                    },
                    "commits": [{"author": "bot", "email": "x@y.com"}],
                    "component_scores": {"activity": 5.0, "contributors": 5.0, "releases": 5.0, "issues": 5.0, "community": 5.0},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dhs, "_seed_path", lambda: seed)
    return seed


def test_is_bot_commit_detects_patterns():
    assert dhs.is_bot_commit("github-actions[bot]", "noreply@github.com")
    assert dhs.is_bot_commit("dependabot[bot]", "noreply@github.com")
    assert not dhs.is_bot_commit("laanwj", "laanwj@gmail.com")


def test_filter_commits_excludes_bots(isolated_seed):
    commits = [
        {"author": "human", "email": "h@example.com", "is_bot": False},
        {"author": "github-actions[bot]", "email": "noreply@github.com", "is_bot": True},
    ]
    filtered = dhs.filter_commits(commits)
    assert len(filtered) == 1
    assert filtered[0]["author"] == "human"


def test_filter_commits_excludes_fork_repo():
    commits = [{"author": "human", "email": "h@example.com", "is_bot": False}]
    assert dhs.filter_commits(commits, repo_is_fork=True) == []


def test_contributor_concentration(isolated_seed):
    commits = [
        {"author": "a", "email": "a@x.com", "is_bot": False},
        {"author": "a", "email": "a@x.com", "is_bot": False},
        {"author": "b", "email": "b@x.com", "is_bot": False},
        {"author": "c", "email": "c@x.com", "is_bot": False},
    ]
    result = dhs.compute_contributor_concentration(commits)
    assert result["top_3_contributors_pct"] == 100.0
    assert result["concentration_risk"] == "High"
    assert result["bus_factor"] >= 1


def test_release_cadence():
    releases = [
        {"tag": "v3", "date": "2026-08-10"},
        {"tag": "v2", "date": "2026-06-26"},
        {"tag": "v1", "date": "2026-04-15"},
    ]
    result = dhs.compute_release_cadence(releases)
    assert result["last_release"] == "2026-08-10"
    assert result["cadence_days_avg"] is not None
    assert result["regularity"] in ("High", "Medium", "Low")


def test_issue_activity_bug_feature_ratio():
    issues = {"open": 10, "closed_30d": 5, "avg_response_days": 3.0, "bug_count_30d": 4, "feature_count_30d": 8}
    result = dhs.compute_issue_activity(issues)
    assert result["bug_to_feature_ratio"] == "4:8"
    assert result["response_time_days"] == 3.0


def test_composite_score_not_commit_count_only():
    components = {"activity": 8.0, "contributors": 7.0, "releases": 6.0, "issues": 5.0, "community": 4.0}
    score = dhs.compute_composite_score(components)
    expected = round(8.0 * 0.30 + 7.0 * 0.25 + 6.0 * 0.20 + 5.0 * 0.15 + 4.0 * 0.10, 1)
    assert score == expected
    assert score != 500  # not commit-count-based


def test_build_dev_health_score_verified(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    result = dhs.build_dev_health_score(seed["assets"]["BTC"], symbol="BTC")
    assert result is not None
    assert result["score"] > 0
    assert "Activity: 30%" in result["score_display"]
    assert "500 commits" not in result["score_display"]
    assert result["ownership"]["status"] == "Verified"
    assert "Ownership: Verified" in result["ownership"]["display"]
    assert result["filtering"]["commits_from_bots"] == "Excluded"
    assert result["disclaimer_hideable"] is False
    assert result["standalone"] is False
    assert result["replaces"] == "722"


def test_unverified_repo_returns_none(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    assert dhs.build_dev_health_score(seed["assets"]["UNVERIFIED"], symbol="UNVERIFIED") is None


def test_get_dev_health_for_asset(isolated_seed):
    result = dhs.get_dev_health_for_asset("BTC")
    assert result is not None
    assert result["symbol"] == "BTC"
    assert "Dev Health:" in result["profile_display"]
    assert "Methodology: v2.1" in result["profile_display"]


def test_trend_with_evidence(isolated_seed):
    result = dhs.get_dev_health_for_asset("BTC")
    assert result is not None
    assert result["trend"]["previous_score"] == 8.1
    assert result["trend"]["direction"] == "down"
    assert len(result["trend"]["evidence"]) >= 1
    assert "Trend:" in result["trend"]["display"]


def test_context_display_not_buy_recommendation(isolated_seed):
    result = dhs.get_dev_health_for_asset("BTC")
    assert result is not None
    assert "Your research required" in result["context_display"]
    assert "Buy" not in result["context_display"]


def test_methodology_versioned(isolated_seed):
    result = dhs.get_dev_health_for_asset("BTC")
    assert result is not None
    assert result["methodology"]["version"] == "v2.1"
    assert result["methodology"]["components"] == 5
    assert "Weights: Documented" in result["methodology"]["display"]


def test_dev_health_status(isolated_seed):
    status = dhs.dev_health_status()
    assert status["feature_id"] == "238"
    assert status["status"] == "operational"
    assert status["methodology_version"] == "v2.1"
    assert status["assets_tracked"] == 1
    assert status["disclaimer_hideable"] is False
    assert status["merged_into"] == "705_asset_metadata"


def test_list_dev_health_assets(isolated_seed):
    assets = dhs.list_dev_health_assets()
    assert len(assets) == 1
    assert assets[0]["symbol"] == "BTC"
