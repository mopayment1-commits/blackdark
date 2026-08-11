"""
BLACKDARK — Expert execution closure pack.

Closes the remaining expert recommendations that are machine-checkable:
canonical binding, FalconAI inflation rejection, 60s acceptance probes,
Glass Box announce drafts (human fills timing/channel).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from path_safety import assert_safe_http_url

CANONICAL_DOCS: list[str] = [
    "docs/PRODUCT_CONSTITUTION_AR.md",
    "docs/CANONICAL_BINDING.md",
    "docs/TRUST_OS_VALUE_LAYERS.md",
    "docs/HEROES_STRATEGY_BINDING.md",
    "docs/STRATEGIC_CORRECTION_BINDING.md",
    "docs/GLASS_BOX_OPERATOR_RUNBOOK.md",
]

SUPERSEDED_FRAMES: list[dict[str, str]] = [
    {
        "id": "falconai_16_120",
        "claim": "FalconAI = 16 institutional platforms + 120 capabilities",
        "status": "rejected_as_valuation_shape",
        "replacement": "1 product · 4 value layers · 6 heroes · quiet engines",
    },
    {
        "id": "bd_dec_0031_sole_map",
        "claim": "FalconAI BD-DEC-0031 is the sole canonical product map",
        "status": "superseded",
        "replacement": "docs/CANONICAL_BINDING.md hierarchy",
    },
    {
        "id": "blackdark_v9_25_sections",
        "claim": "Expand to 25 sections + ARENA + Neuro-Design",
        "status": "rejected",
        "replacement": "Strategic correction binding + shareable certificates",
    },
]


def _probe(url: str, *, timeout: float = 8.0) -> dict[str, Any]:
    t0 = datetime.now(UTC)
    try:
        safe_url = assert_safe_http_url(url)
        req = Request(safe_url, headers={"Accept": "application/json,text/html,*/*"})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(4000)
            ms = (datetime.now(UTC) - t0).total_seconds() * 1000
            return {
                "url": safe_url,
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "latency_ms": round(ms, 1),
                "bytes": len(body),
            }
    except ValueError:
        ms = (datetime.now(UTC) - t0).total_seconds() * 1000
        return {"url": url, "ok": False, "status": None, "latency_ms": round(ms, 1), "error": "host_not_allowed"}
    except HTTPError as exc:
        ms = (datetime.now(UTC) - t0).total_seconds() * 1000
        # Generic error codes only — never return exception/stack text to clients.
        return {
            "url": url,
            "ok": False,
            "status": exc.code,
            "latency_ms": round(ms, 1),
            "error": "http_error",
        }
    except TimeoutError:
        ms = (datetime.now(UTC) - t0).total_seconds() * 1000
        return {"url": url, "ok": False, "status": None, "latency_ms": round(ms, 1), "error": "timed out"}
    except OSError:
        ms = (datetime.now(UTC) - t0).total_seconds() * 1000
        return {"url": url, "ok": False, "status": None, "latency_ms": round(ms, 1), "error": "network_error"}


def glass_box_announce_drafts() -> dict[str, Any]:
    """Human fills datetime/channel; product copy is ready."""
    challenge = (
        "BLACKDARK Glass Box Challenge: We publish our full Public Accuracy Ledger — "
        "including misses — permanently and verifiably. Labels are not proof. "
        "We challenge every competitor to publish theirs. Prove it. "
        "https://blackdark.app/oracle-accuracy#glass-box-challenge"
    )
    return {
        "status": "copy_ready_human_schedule",
        "human_only_fields": ["exact_datetime", "timezone", "announcement_channel"],
        "drafts": {
            "x_en": challenge + " #GlassBoxChallenge #ProveIt #BLACKDARK",
            "telegram_en": challenge,
            "press_one_liner_en": (
                "BLACKDARK seals timed Decision Certificates before a public macro event, "
                "then unlocks wins and losses live on its Public Accuracy Ledger."
            ),
        },
        "operator_api": "/api/glass-box/operator",
        "runbook": "docs/GLASS_BOX_OPERATOR_RUNBOOK.md",
        "note": "Do not auto-post. Founder/ops chooses clock + channel (H2).",
    }


def run_acceptance_60s(base_url: str = "http://127.0.0.1:8080") -> dict[str, Any]:
    """
    Machine probe for the 60-second grasp bar.
    Founder still confirms cold walkthrough (human H3).
    """
    base = assert_safe_http_url(base_url.rstrip("/"))
    checks = [
        ("landing", f"{base}/"),
        ("dashboard", f"{base}/dashboard"),
        ("ledger", f"{base}/oracle-accuracy"),
        ("capabilities", f"{base}/capabilities"),
        ("trust_os", f"{base}/api/trust-os"),
        ("intent", f"{base}/api/intent/router"),
        ("correction", f"{base}/api/strategy/correction"),
        ("oracle_quick", f"{base}/oracle/BTC/quick?ux_mode=beginner&lang=en"),
        ("glass_box", f"{base}/api/glass-box/challenge"),
    ]
    results = [_probe(url) for _, url in checks]
    named = {checks[i][0]: results[i] for i in range(len(checks))}
    ok_count = sum(1 for r in results if r.get("ok"))
    # Soft content assertions where JSON
    content_notes: list[str] = []
    try:
        import json

        for key in ("trust_os", "intent", "correction"):
            url = assert_safe_http_url(named[key]["url"])
            if not named[key].get("ok"):
                continue
            with urlopen(url, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="replace"))
            if key == "trust_os":
                layers = payload.get("value_layers") or []
                if len(layers) != 4:
                    content_notes.append(f"trust_os layers={len(layers)} (want 4)")
                deny = " ".join(r.get("claim", "") for r in (payload.get("overclaim_denylist") or []))
                if "ARENA" not in deny.upper():
                    content_notes.append("denylist missing ARENA")
            if key == "intent":
                q = str(payload.get("question") or "")
                # Accept current canon ("What do you need?") and legacy phrasing.
                if "What do you need?" not in q and "What do you want to do today?" not in q:
                    content_notes.append("intent question mismatch")
            if key == "correction" and payload.get("heroes_count") != 6:
                content_notes.append("correction heroes_count != 6")
    except Exception:
        content_notes.append("content_check_error")

    passed = ok_count >= 7 and not content_notes
    return {
        "bar": "60_second_grasp",
        "definition": (
            "New user reaches Act/Wait decision path and Public Accuracy Ledger "
            "without a guided tour."
        ),
        "base_url": base,
        "probes": named,
        "ok_count": ok_count,
        "total": len(checks),
        "content_notes": content_notes,
        "machine_pass": passed,
        "human_confirm_required": True,
        "human_step": "H3 — founder cold open of live URL",
        "generated_at": datetime.now(UTC).isoformat(),
    }


def execution_closure_manifest(*, base_url: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from trust_os import OVERCLAIM_DENYLIST, VALUE_LAYERS, strategy_correction_manifest

    root = Path(__file__).resolve().parent
    docs_ok = {doc: (root / doc).is_file() for doc in CANONICAL_DOCS}
    acceptance = None
    if base_url:
        acceptance = run_acceptance_60s(base_url)

    return {
        "product": "BLACKDARK",
        "thesis": "Don't trust us. Verify us.",
        "canonical_docs": docs_ok,
        "canonical_docs_complete": all(docs_ok.values()),
        "value_layers": len(VALUE_LAYERS),
        "heroes_count": 6,
        "overclaim_denylist_count": len(OVERCLAIM_DENYLIST),
        "superseded_frames": SUPERSEDED_FRAMES,
        "strategy_correction": {
            "not_building": strategy_correction_manifest().get("not_building"),
            "five_outcomes": strategy_correction_manifest().get("five_outcomes"),
        },
        "glass_box_announce": glass_box_announce_drafts(),
        "acceptance_60s": acceptance,
        "remaining_human_only": [
            {
                "id": "H2",
                "item": "Glass Box announce exact datetime + channel",
                "unblock": "Founder picks event clock and posts draft copy",
            },
            {
                "id": "H3",
                "item": "Founder cold 60-second value confirm on live URL",
                "unblock": "Open production/staging URL without coaching",
            },
            {
                "id": "HA",
                "item": "Signed HA row on Postgres+Redis multi-worker",
                "unblock": "Fill docs/LOAD_TEST_RUN_LOG.md against staging/prod-like",
            },
        ],
        "not_executing": [
            "falconai_16_platforms_valuation",
            "blackdark_arena",
            "neuro_design_engine",
            "25_section_expansion",
            "live_money_auto_execution_as_acquisition_priority",
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }
