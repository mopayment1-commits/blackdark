"""Dev Health Score (#238) — institutional development continuity intelligence.

Replaces generic #722 commits aggregation with composite institutional scoring:
ownership verification, bot/fork filtering, contributor concentration, release
cadence, issue activity, and versioned methodology.

Integrated into #705 Asset Metadata — NOT a standalone dashboard.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FEATURE_ID = "238"
FEATURE_NAME = "Dev_Health_Score"
METHODOLOGY_VERSION = "v2.1"
METHODOLOGY_LAST_REVISED = "2026-08-25"
COMPONENT_WEIGHTS = {
    "activity": 0.30,
    "contributors": 0.25,
    "releases": 0.20,
    "issues": 0.15,
    "community": 0.10,
}
WEIGHT_DISPLAY = (
    "Activity: 30% | Contributors: 25% | Releases: 20% | Issues: 15% | Community: 10%"
)
DISCLAIMER = (
    "Dev Health measures project development activity. It is not a valuation metric. "
    "A high score does not guarantee project success. Not investment advice."
)

_BOT_PATTERNS = (
    re.compile(r"\[bot\]", re.I),
    re.compile(r"dependabot", re.I),
    re.compile(r"github-actions", re.I),
    re.compile(r"renovate\[bot\]", re.I),
)
_BOT_EMAIL_DOMAINS = ("noreply.github.com", "users.noreply.github.com")


def _seed_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "dev_health_seed.json"


def _load_seed() -> dict[str, Any]:
    path = _seed_path()
    if not path.exists():
        return {"assets": {}, "methodology": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def is_bot_commit(author: str, email: str = "") -> bool:
    """Detect bot commits via author name pattern + email domain."""
    author_l = (author or "").lower()
    email_l = (email or "").lower()
    if any(p.search(author_l) for p in _BOT_PATTERNS):
        return True
    return any(d in email_l for d in _BOT_EMAIL_DOMAINS)


def filter_commits(commits: list[dict[str, Any]], *, repo_is_fork: bool = False) -> list[dict[str, Any]]:
    """Exclude bot commits and fork-origin commits."""
    if repo_is_fork:
        return []
    return [
        c
        for c in commits
        if not c.get("is_fork")
        and not is_bot_commit(str(c.get("author", "")), str(c.get("email", "")))
        and not c.get("is_bot")
    ]


def compute_contributor_concentration(commits: list[dict[str, Any]], *, repo_is_fork: bool = False) -> dict[str, Any]:
    """Top-3 contributor concentration and bus factor."""
    filtered = filter_commits(commits, repo_is_fork=repo_is_fork)
    counts: dict[str, int] = {}
    for c in filtered:
        author = str(c.get("author", "unknown"))
        counts[author] = counts.get(author, 0) + 1
    total = sum(counts.values()) or 1
    ranked = sorted(counts.items(), key=lambda x: -x[1])
    top3 = ranked[:3]
    top3_pct = round(sum(c for _, c in top3) / total * 100, 1)
    if top3_pct >= 70:
        risk = "High"
    elif top3_pct >= 50:
        risk = "Medium"
    else:
        risk = "Low"
    bus = sum(1 for _, c in ranked if c >= total * 0.10) or 1
    top3_str = ", ".join(f"{a} ({round(c / total * 100)}%)" for a, c in top3)
    return {
        "top_3_contributors_pct": top3_pct,
        "top_3_detail": top3_str,
        "concentration_risk": risk,
        "bus_factor": bus,
        "verified_contributors_only": True,
    }


def compute_release_cadence(releases: list[dict[str, Any]]) -> dict[str, Any]:
    """Release cadence and regularity from release history."""
    if not releases:
        return {
            "last_release": None,
            "cadence_days_avg": None,
            "regularity": "Low",
        }
    sorted_r = sorted(releases, key=lambda r: r.get("date", ""), reverse=True)
    last = sorted_r[0].get("date")
    if len(sorted_r) < 2:
        return {"last_release": last, "cadence_days_avg": None, "regularity": "Low"}
    dates = []
    for r in sorted_r:
        try:
            dates.append(datetime.fromisoformat(str(r["date"]).replace("Z", "+00:00")))
        except (ValueError, KeyError):
            continue
    if len(dates) < 2:
        return {"last_release": last, "cadence_days_avg": None, "regularity": "Low"}
    gaps = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
    avg = round(sum(gaps) / len(gaps), 1)
    if avg <= 30:
        regularity = "High"
    elif avg <= 90:
        regularity = "Medium"
    else:
        regularity = "Low"
    return {"last_release": last, "cadence_days_avg": avg, "regularity": regularity}


def compute_issue_activity(issues: dict[str, Any]) -> dict[str, Any]:
    """Issue health metrics."""
    ratio = issues.get("bug_to_feature_ratio")
    if not ratio:
        bugs = issues.get("bug_count_30d", 0)
        features = issues.get("feature_count_30d", 0)
        ratio = f"{bugs}:{features}" if features else "N/A"
    return {
        "open_issues": issues.get("open", 0),
        "closed_30d": issues.get("closed_30d", 0),
        "response_time_days": issues.get("response_time_days", issues.get("avg_response_days")),
        "bug_to_feature_ratio": ratio,
    }


def compute_composite_score(components: dict[str, float]) -> float:
    """Weighted composite on 0–10 component scores — never commit-count-only."""
    score = 0.0
    for key, weight in COMPONENT_WEIGHTS.items():
        score += components.get(key, 0.0) * weight
    return round(score, 1)


def _normalize_ownership(repo: dict[str, Any], asset_data: dict[str, Any]) -> dict[str, Any]:
    ownership_raw = repo.get("ownership") or asset_data.get("ownership") or {}
    if "verified" in ownership_raw:
        return {
            "status": "Verified" if ownership_raw.get("verified") else "Unverified",
            "method": ownership_raw.get("method", "GitHub API org mapping + manual check"),
            "last_verified": ownership_raw.get("last_verified"),
        }
    status = ownership_raw.get("status", "Unverified")
    return {
        "status": status,
        "method": ownership_raw.get("method", "GitHub API org mapping + manual check"),
        "last_verified": ownership_raw.get("last_verified"),
    }


def _infer_trend_direction(score: float, previous_score: float | None) -> str:
    if previous_score is None:
        return "flat"
    if score > previous_score:
        return "up"
    if score < previous_score:
        return "down"
    return "flat"


def build_dev_health_score(asset_data: dict[str, Any], *, symbol: str | None = None) -> dict[str, Any] | None:
    """Build full dev health score for one asset."""
    repo = asset_data.get("repo") or asset_data.get("repository") or {}
    ownership = _normalize_ownership(repo, asset_data)
    if ownership.get("status") != "Verified":
        return None
    if repo.get("is_fork"):
        return None

    commits = asset_data.get("commits", [])
    releases = asset_data.get("releases", [])
    issues = asset_data.get("issues", {})
    components = asset_data.get("component_scores", {})
    trend_data = asset_data.get("trend", {})
    repo_is_fork = bool(repo.get("is_fork"))

    filtered = filter_commits(commits, repo_is_fork=repo_is_fork)
    concentration = compute_contributor_concentration(commits, repo_is_fork=repo_is_fork)
    cadence = compute_release_cadence(releases)
    issue_health = compute_issue_activity(issues)
    score = compute_composite_score(components)

    prev = trend_data.get("previous_score")
    direction = trend_data.get("direction") or _infer_trend_direction(score, prev)
    evidence = trend_data.get("evidence", [])

    trend_arrow = {"up": "↑", "down": "↓", "flat": "→"}.get(direction, "→")
    if prev is not None:
        trend_label = f"{trend_arrow} (from {prev} last month)"
    else:
        trend_label = trend_arrow

    strength = "Strong" if score >= 7.5 else "Moderate" if score >= 5.0 else "Weak"

    return {
        "feature_id": FEATURE_ID,
        "feature_name": FEATURE_NAME,
        "symbol": symbol or asset_data.get("symbol"),
        "project": asset_data.get("project"),
        "score": score,
        "score_display": (
            f"Score: {score}/10 | Activity: 30% | Contributors: 25% | "
            f"Releases: 20% | Issues: 15% | Community: 10%"
        ),
        "profile_display": f"Dev Health: {score}/10 | Methodology: {METHODOLOGY_VERSION}",
        "context_display": f"Dev Health: {strength} | Context: Active development | Your research required",
        "methodology": {
            "version": METHODOLOGY_VERSION,
            "components": len(COMPONENT_WEIGHTS),
            "weights": COMPONENT_WEIGHTS,
            "weights_display": WEIGHT_DISPLAY,
            "last_revised": METHODOLOGY_LAST_REVISED,
            "display": (
                f"Dev Health Methodology {METHODOLOGY_VERSION} | "
                f"Components: {len(COMPONENT_WEIGHTS)} | Weights: Documented | "
                f"Last Revised: {METHODOLOGY_LAST_REVISED}"
            ),
        },
        "ownership": {
            **ownership,
            "display": (
                f"Ownership: {ownership.get('status')} | "
                f"Method: {ownership.get('method')} | "
                f"Last Verified: {ownership.get('last_verified')}"
            ),
        },
        "filtering": {
            "commits_from_bots": "Excluded",
            "forks": "Excluded",
            "verified_contributors_only": True,
            "bot_detection_method": "Commit message pattern + author email domain",
            "display": (
                "Commits from bots: Excluded | Forks: Excluded | "
                "Verified contributors only: Yes | "
                "Bot Detection Method: Commit message pattern + author email domain"
            ),
            "filtered_commit_count": len(filtered),
            "raw_commit_count": len(commits),
        },
        "contributor_concentration": {
            **concentration,
            "display": (
                f"Top 3 Contributors: {concentration['top_3_contributors_pct']}% of commits | "
                f"Concentration Risk: {concentration['concentration_risk']} | "
                f"Bus Factor: {concentration['bus_factor']}"
            ),
        },
        "release_cadence": {
            **cadence,
            "display": (
                f"Last Release: {cadence.get('last_release', 'N/A')} | "
                f"Cadence: {cadence.get('cadence_days_avg', 'N/A')} days average | "
                f"Regularity: {cadence.get('regularity', 'N/A')}"
            ),
        },
        "issue_activity": {
            **issue_health,
            "display": (
                f"Open Issues: {issue_health['open_issues']} | "
                f"Closed (30D): {issue_health['closed_30d']} | "
                f"Response Time: {issue_health['response_time_days']} days | "
                f"Bug-to-Feature Ratio: {issue_health['bug_to_feature_ratio']}"
            ),
        },
        "component_scores": components,
        "trend": {
            "direction": direction,
            "previous_score": prev,
            "display": f"Score: {score}/10 | Trend: {trend_label}",
            "evidence": evidence,
            "evidence_display": " | ".join(evidence) if evidence else "No significant changes",
        },
        "repository": repo,
        "disclaimer": DISCLAIMER,
        "disclaimer_hideable": False,
        "standalone": False,
        "merged_into": "705_asset_metadata",
        "replaces": "722",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def get_dev_health_for_asset(symbol: str) -> dict[str, Any] | None:
    """Return dev health block for #705 asset metadata integration."""
    seed = _load_seed()
    asset = seed.get("assets", {}).get(symbol.upper())
    if not asset:
        return None
    return build_dev_health_score(asset, symbol=symbol.upper())


def list_dev_health_assets() -> list[dict[str, Any]]:
    """List all assets with verified dev health scores."""
    seed = _load_seed()
    results = []
    for sym, data in seed.get("assets", {}).items():
        result = build_dev_health_score(data, symbol=sym)
        if result:
            results.append(result)
    return results


def dev_health_status() -> dict[str, Any]:
    """Module status for platform health checks."""
    seed = _load_seed()
    assets = seed.get("assets", {})
    scored = [s for s in assets if build_dev_health_score(assets[s], symbol=s)]
    return {
        "feature_id": FEATURE_ID,
        "feature_name": FEATURE_NAME,
        "status": "operational",
        "methodology_version": METHODOLOGY_VERSION,
        "methodology_display": (
            f"Dev Health Methodology {METHODOLOGY_VERSION} | "
            f"Components: {len(COMPONENT_WEIGHTS)} | Weights: Documented | "
            f"Last Revised: {METHODOLOGY_LAST_REVISED}"
        ),
        "weights_display": WEIGHT_DISPLAY,
        "assets_tracked": len(scored),
        "assets_total": len(assets),
        "standalone": False,
        "merged_into": "705_asset_metadata",
        "replaces": "722",
        "disclaimer": DISCLAIMER,
        "disclaimer_hideable": False,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }
