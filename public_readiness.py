"""Public direct-use readiness — HTTP-proved catalog, never institutional COMPLETE.

Binding rules:
- Green tests ≠ COMPLETE.
- Public ≥95% is visitor/unpaid-paper readiness, not live_fill / Jupiter VC / L2-100 / cloud multi-AZ.
- Skip flags (LAUNCH_SKIP_TELEGRAM) ≠ live delivery.
- Silent False on unconfigured Telegram is a product defect; fail-closed 503 is honesty.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

PUBLIC_FLOOR_PCT = 95.0

# Expected statuses: 200 render, 3xx advertised alias, 401/403 auth gate, 503 fail-closed ops.
_OK_HTML = frozenset({200})
_OK_REDIR = frozenset({301, 302, 303, 307, 308})
_OK_JSON = frozenset({200})
_OK_AUTH_GATE = frozenset({401, 403})
_OK_OPS_CLOSED = frozenset({401, 403, 503})


def _row(
    *,
    id: str,
    path: str,
    kind: str,
    bucket: str,
    expect: frozenset[int],
    method: str = "GET",
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": id,
        "path": path,
        "method": method,
        "kind": kind,
        "bucket": bucket,
        "expect": sorted(expect),
        "note": note,
    }


def advertised_public_surfaces() -> list[dict[str, Any]]:
    """Every visitor-facing HTML page + public JSON + fail-closed ops gates.

    bucket=public_direct counts toward the public score.
    bucket=ops_fail_closed counts if the path fail-closes (401/503), not if it silently succeeds.
    bucket=excluded_external is disclosed and omitted from the public denominator.
    """
    html = [
        ("home", "/", "landing"),
        ("landing_alias", "/landing", "landing alias"),
        ("dashboard", "/dashboard", "Trust OS dashboard"),
        ("login", "/login", "login + register tabs"),
        ("profile", "/profile", "profile + MFA"),
        ("reset_password", "/reset-password", "password reset form"),
        ("verify_email", "/verify-email", "verify without token still renders"),
        ("success", "/success", "checkout success"),
        ("cancel", "/cancel", "checkout cancel"),
        ("docs", "/docs", "developer docs"),
        ("docs_public", "/docs/public", "public docs"),
        ("contact", "/contact", "contact"),
        ("complaints", "/complaints", "complaints"),
        ("faq", "/faq", "faq"),
        ("how_it_works", "/how-it-works", "how it works"),
        ("about", "/about", "about"),
        ("status_page", "/status", "status"),
        ("changelog", "/changelog", "changelog"),
        ("feedback", "/feedback", "feedback"),
        ("legal", "/legal", "legal hub"),
        ("terms", "/terms", "terms"),
        ("privacy", "/privacy", "privacy"),
        ("disclaimer", "/disclaimer", "disclaimer"),
        ("refund", "/refund", "refund"),
        ("cookies", "/cookies", "cookies"),
        ("compliance", "/compliance", "compliance"),
        ("data_room", "/data-room", "data room"),
        ("capabilities", "/capabilities", "capabilities"),
        ("platform", "/platform", "platform hub"),
        ("b2b", "/b2b", "b2b / fund terminal"),
        ("oracle_accuracy", "/oracle-accuracy", "public accuracy ledger"),
        ("errors", "/errors", "errors / misses"),
        ("plan", "/plan", "plan audit"),
        ("admin_launch", "/admin/launch", "launch checklist"),
        ("admin_plan", "/admin/plan", "admin plan"),
        ("admin_roadmap", "/admin/roadmap", "admin roadmap"),
        ("discipline", "/discipline-mirror", "discipline mirror"),
        ("kill_rate", "/kill-rate", "kill-rate"),
        ("contradiction", "/contradiction-replay", "contradiction replay"),
        ("proof_arena", "/proof-arena", "proof arena"),
        ("committee", "/b2b/committee-one-pager", "committee one-pager"),
        ("since_left", "/since-you-left", "since you left"),
        ("anti_hype", "/anti-hype", "anti-hype"),
        ("corpus", "/corpus-passport", "corpus passport"),
        ("miss_feed", "/miss-feed", "miss feed"),
        ("coverage", "/coverage-honesty", "coverage honesty"),
        ("priority", "/priority-chain", "priority chain"),
        ("zero_tol", "/zero-tolerance", "zero tolerance"),
        ("emotion", "/emotion-tax", "emotion tax"),
        ("allocator", "/allocator-receipt", "allocator receipt"),
        ("transfer", "/transfer-intent", "transfer intent"),
        ("silence", "/silence-index", "silence index"),
        ("alert_pass", "/alert-passport", "alert passport"),
        ("visibility", "/visibility-cost", "visibility cost"),
        ("validity", "/validity-decay", "validity decay"),
        ("desk_duel", "/desk-duel", "desk duel"),
        ("trust_debt", "/trust-debt", "trust debt"),
        ("unique_ten", "/unique-ten", "unique ten"),
        ("institutional", "/institutional", "institutional"),
        ("model_card", "/model-card", "model card"),
        ("d5", "/d5-honesty", "d5 honesty"),
        ("my_discipline", "/my/discipline-mirror", "my discipline"),
        ("robots", "/robots.txt", "robots"),
        ("sitemap", "/sitemap.xml", "sitemap"),
        ("manifest", "/manifest.json", "PWA manifest"),
        ("sw", "/sw.js", "service worker"),
        ("favicon", "/favicon.ico", "favicon"),
    ]
    redir = [
        ("app_alias", "/app", "dashboard alias"),
        ("register_alias", "/register", "login alias — must not 404"),
        ("settings_security", "/settings/security", "profile MFA alias"),
        ("public_ledger_alias", "/public/accuracy-ledger", "oracle-accuracy alias"),
        ("oracle_accuracy_alias", "/oracle/accuracy", "oracle-accuracy alias"),
    ]
    json_ok = [
        ("health", "/health", "process health"),
        ("health_live", "/health/live", "liveness"),
        ("api_status", "/api/status", "site status"),
        ("api_faq", "/api/faq", "faq json"),
        ("api_changelog", "/api/changelog", "changelog json"),
        ("api_site", "/api/site-services", "footer/site catalog"),
        ("i18n_locales", "/api/i18n/locales", "locales"),
        ("i18n_catalog", "/api/i18n/catalog", "i18n catalog"),
        ("inv", "/api/product/capability-inventory", "binding inventory"),
        ("l2rem", "/api/product/l2-remainder", "L2 remainder honesty"),
        ("unpaid", "/api/product/unpaid-closure", "unpaid closure"),
        ("persona", "/api/trial/persona-readiness", "six personas"),
        ("billing_unpaid", "/api/billing/unpaid-upgrade", "unpaid upgrade path"),
        ("billing_status", "/api/billing/status", "billing status"),
        ("pricing", "/api/pricing", "pricing catalog"),
        ("oauth_status", "/api/auth/oauth/status", "oauth honesty"),
        ("tg_status", "/api/alerts/telegram/status", "telegram config honesty"),
        ("tg_free", "/api/telegram/free/status", "free telegram status"),
        ("b2b_info", "/api/b2b/info", "b2b info"),
        ("trust_os", "/api/trust-os", "trust os"),
        ("lenses", "/api/lenses", "four lenses"),
        ("audience", "/api/audience/entry", "audience routing"),
        ("openapi_public", "/api/docs/public-openapi.json", "public openapi"),
        ("docs_manifest", "/api/docs/public-manifest", "docs manifest"),
        ("build_info", "/api/build-info", "build info"),
        ("universe", "/api/universe/status", "catalog health"),
        ("launch", "/api/launch/readiness", "launch board"),
        ("gtm", "/api/gtm/status", "gtm"),
        ("d5_api", "/api/public/d5-honesty", "d5 api"),
        ("wow", "/api/wow/surfaces", "wow surfaces"),
        ("f1f10", "/api/public/f1-f10-closure", "f1-f10"),
        ("plan_audit", "/api/plan/audit", "plan audit"),
        ("roadmap_audit", "/api/roadmap/audit", "roadmap audit"),
        ("metrics", "/metrics", "prometheus"),
        ("observability", "/api/observability/status", "observability"),
        ("privacy_status", "/api/privacy/status", "privacy status"),
        ("regulatory", "/api/regulatory/compliance", "regulatory"),
        ("services", "/api/services/status", "services"),
        ("trust_pulse", "/api/trust-pulse", "trust pulse"),
        ("trust_pulse_manifest", "/api/trust-pulse/manifest", "trust pulse manifest"),
        ("scale", "/api/scale/readiness", "scale readiness"),
        ("viral", "/api/viral/readiness", "viral readiness"),
        ("db_health", "/api/database/health", "db health"),
        ("feed_engine", "/api/feed/engine/status", "feed engine"),
        ("ingestion", "/api/ingestion/status", "ingestion"),
        ("public_readiness", "/api/product/public-readiness", "this catalog"),
    ]
    gated_json = [
        ("inbox", "/api/alerts/inbox", "in-app inbox"),
        ("locked", "/api/locked-predictions", "locked predictions"),
        ("dd_status", "/api/due-diligence/status", "dd status"),
        ("sec_status", "/api/security/status", "security status"),
        ("exec_status", "/api/execution/status", "execution dry-run status"),
        ("risk_status", "/api/risk/status", "risk status"),
        ("options", "/api/options/overview", "options overview"),
        ("arb_cat", "/api/arbitrage/catalog", "arb catalog"),
        ("sentiment", "/api/sentiment/overview", "sentiment"),
        ("onchain", "/api/onchain/overview", "onchain"),
        ("macro", "/api/macro/overview", "macro"),
    ]
    health_json = [
        ("health_ready", "/health/ready", "readiness (503 starting is honest)"),
        ("health_viral", "/health/viral", "viral posture (503 without redis is honest)"),
    ]
    rows: list[dict[str, Any]] = []
    for sid, path, note in html:
        rows.append(
            _row(id=sid, path=path, kind="html", bucket="public_direct", expect=_OK_HTML, note=note)
        )
    for sid, path, note in redir:
        rows.append(
            _row(
                id=sid,
                path=path,
                kind="redirect",
                bucket="public_direct",
                expect=_OK_REDIR,
                note=note,
            )
        )
    for sid, path, note in json_ok:
        rows.append(
            _row(id=sid, path=path, kind="json", bucket="public_direct", expect=_OK_JSON, note=note)
        )
    health_ok = _OK_JSON | frozenset({503})
    for sid, path, note in health_json:
        rows.append(
            _row(id=sid, path=path, kind="json", bucket="public_direct", expect=health_ok, note=note)
        )
    gated_ok = _OK_JSON | _OK_AUTH_GATE
    for sid, path, note in gated_json:
        rows.append(
            _row(
                id=sid,
                path=path,
                kind="gated_json",
                bucket="public_direct",
                expect=gated_ok,
                note=note + " — 401/403 is a working gate, not a missing page",
            )
        )
    rows.extend(
        [
            _row(
                id="tg_test_unauth",
                path="/api/alerts/telegram/test",
                method="POST",
                kind="ops_fail_closed",
                bucket="ops_fail_closed",
                expect=_OK_AUTH_GATE,
                note="unauthenticated test must 401, never silent success",
            ),
            _row(
                id="oauth_start_unconfigured",
                path="/api/auth/oauth/google/start",
                kind="ops_fail_closed",
                bucket="ops_fail_closed",
                expect=_OK_OPS_CLOSED | _OK_JSON,
                note="503 if no client id; 200 only when live IdP configured",
            ),
            _row(
                id="checkout_unconfigured",
                path="/create-checkout-session",
                kind="ops_fail_closed",
                bucket="ops_fail_closed",
                expect=_OK_OPS_CLOSED | frozenset({400, 422}),
                note="must not pretend a live charge succeeded",
            ),
            _row(
                id="ex_live_order_unauth",
                path="/api/execution/order",
                method="POST",
                kind="auth_gate",
                bucket="excluded_external",
                expect=_OK_AUTH_GATE,
                note="live fill remains EXTERNAL; path must not 404",
            ),
        ]
    )
    return rows


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def classify_probe(row: dict[str, Any], status_code: int) -> str:
    expect = set(row["expect"])
    if status_code in expect:
        return "pass"
    if status_code == 404:
        return "missing"
    if status_code >= 500:
        return "error"
    return "unexpected"


def score_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    counted = [r for r in results if r.get("bucket") in {"public_direct", "ops_fail_closed"}]
    excluded = [r for r in results if r.get("bucket") == "excluded_external"]
    passed = [r for r in counted if r.get("outcome") == "pass"]
    failed = [r for r in counted if r.get("outcome") != "pass"]
    total = len(counted)
    pct = round((100.0 * len(passed) / total), 2) if total else 0.0
    return {
        "public_direct_use_percent": pct,
        "floor_percent": PUBLIC_FLOOR_PCT,
        "meets_public_floor": pct >= PUBLIC_FLOOR_PCT,
        "counted_total": total,
        "counted_pass": len(passed),
        "counted_fail": len(failed),
        "excluded_external_probes": len(excluded),
        "failures": [
            {"id": r["id"], "path": r["path"], "status": r.get("status"), "outcome": r.get("outcome")}
            for r in failed
        ],
        "institutional_complete": False,
        "live_money_ready": False,
        "product_complete": False,
        "denominator_excludes": [
            "live_fill (Binance geo 451)",
            "jupiter on-chain VC (unfunded wallet)",
            "catalog L2 100% (5 synthetic_mid remain)",
            "cloud multi-AZ (zero-cost)",
            "hosted custom-domain white-label",
            "live PSP charge",
            "live OAuth IdP (unless owner secrets present)",
            "live Telegram send (unless TELEGRAM_BOT_TOKEN present)",
        ],
        "honesty": (
            "Public ≥95% means visitor/paper surfaces HTTP-prove. "
            "It is not institutional COMPLETE and not live money."
        ),
    }


def probe_with_client(client: Any) -> dict[str, Any]:
    """Hit every advertised surface. `client` is FastAPI TestClient (no follow redirects)."""
    results: list[dict[str, Any]] = []
    for row in advertised_public_surfaces():
        method = str(row["method"]).upper()
        path = row["path"]
        try:
            if method == "POST":
                resp = client.post(path, json={})
            else:
                resp = client.get(path)
            status = int(resp.status_code)
        except Exception as exc:  # noqa: BLE001 — probe must never crash the score
            status = 0
            outcome = "error"
            err = str(exc)[:240]
        else:
            outcome = classify_probe(row, status)
            err = ""
        results.append(
            {
                **{k: v for k, v in row.items() if k != "expect"},
                "expect": list(row["expect"]),
                "status": status,
                "outcome": outcome,
                "error": err,
            }
        )
    scored = score_results(results)
    return {
        "ok": True,
        "surface": "public_direct_use_readiness",
        "proved_at": _utcnow(),
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "trial_ready_unpaid": True,
        "live_money_ready": False,
        "score": scored,
        "probes": results,
        "review_gap_closed": [
            "AL-TG live Telegram reclassified ops_config; unconfigured test is HTTP 503",
            "LAUNCH_SKIP_TELEGRAM no longer marks telegram done",
            "SMTP optional no longer auto-done without SMTP_HOST",
            "/register alias so signup URL does not 404",
            "sitemap includes legal pages advertised in footer",
        ],
        "report": "docs/dd/BLACKDARK_PUBLIC_DIRECT_USE_INSTITUTIONAL_REVIEW.md",
    }


def catalog_without_probe() -> dict[str, Any]:
    rows = advertised_public_surfaces()
    return {
        "ok": True,
        "surface": "public_direct_use_readiness_catalog",
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "live_money_ready": False,
        "floor_percent": PUBLIC_FLOOR_PCT,
        "advertised_count": len(rows),
        "public_direct_count": sum(1 for r in rows if r["bucket"] == "public_direct"),
        "ops_fail_closed_count": sum(1 for r in rows if r["bucket"] == "ops_fail_closed"),
        "excluded_external_count": sum(1 for r in rows if r["bucket"] == "excluded_external"),
        "surfaces": [
            {k: v for k, v in r.items() if k != "expect"} | {"expect": list(r["expect"])}
            for r in rows
        ],
        "honesty": (
            "Call GET /api/product/public-readiness?probe=1 (tests) or "
            "scripts/prove_public_readiness.py for HTTP evidence. "
            "Catalog alone is not a score."
        ),
        "report": "docs/dd/BLACKDARK_PUBLIC_DIRECT_USE_INSTITUTIONAL_REVIEW.md",
    }
