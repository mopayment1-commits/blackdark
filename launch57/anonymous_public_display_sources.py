"""
Launch-57 anonymous public page display source registry.

Maps every visitor-visible numeric metric on allowlisted public HTML pages to a
governed source and LICENSE_PUBLIC_DISPLAY posture. Does not claim PASS_LIVE or
external legal clearance — builder_status remains PENDING_VERIFICATION.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

BUILDER_STATUS = "PENDING_VERIFICATION"
REGISTRY_VERSION = "launch57-anonymous-public-display-sources-1.0.0"

# Public HTML pages in scope for this batch (landing + status + methodology + accuracy + legal).
PUBLIC_VISITOR_PAGES: tuple[dict[str, str], ...] = (
    {"path": "/", "page_id": "landing", "template": "templates/landing.html"},
    {"path": "/status", "page_id": "status", "template": "templates/utility.html"},
    {"path": "/how-it-works", "page_id": "how_it_works", "template": "templates/utility.html"},
    {"path": "/oracle-accuracy", "page_id": "oracle_accuracy", "template": "templates/oracle_accuracy.html"},
    {"path": "/terms", "page_id": "terms", "template": "templates/legal.html"},
    {"path": "/privacy", "page_id": "privacy", "template": "templates/legal.html"},
    {"path": "/disclaimer", "page_id": "disclaimer", "template": "templates/legal.html"},
)


class LicensePublicDisplay(str, Enum):
    """Public display licensing posture for a governed metric."""

    KNOWN = "KNOWN"
    DELAYED = "DELAYED"
    BLOCKED = "BLOCKED"


_LICENSE_ALLOWED = frozenset({LicensePublicDisplay.KNOWN, LicensePublicDisplay.DELAYED})


def _metric(
    *,
    metric_id: str,
    page_id: str,
    display_label: str,
    source_module: str,
    license_public_display: LicensePublicDisplay,
    launch_item_id: int | None = None,
    api_route: str | None = None,
    dom_selector: str | None = None,
    attribution: str | None = None,
    raw_provider_blocked_when_unlicensed: bool = True,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "page_id": page_id,
        "display_label": display_label,
        "source_module": source_module,
        "launch_item_id": launch_item_id,
        "api_route": api_route,
        "dom_selector": dom_selector,
        "license_public_display": license_public_display.value,
        "attribution": attribution or source_module,
        "raw_provider_blocked_when_unlicensed": raw_provider_blocked_when_unlicensed,
        "legal_review_open": True,
        "mica_uk_compliance_claim_forbidden": True,
    }


def build_public_page_display_registry() -> list[dict[str, Any]]:
    """Every visitor-visible number on scoped public pages → source + license posture."""
    rows: list[dict[str, Any]] = [
        # --- landing ---
        _metric(
            metric_id="landing_trust_pulse_price",
            page_id="landing",
            display_label="Trust Pulse reference price (USD)",
            source_module="launch57.data_batch1:realtime_prices",
            launch_item_id=22,
            api_route="/api/launch57/real-time-prices",
            dom_selector="#lpPriceVal",
            license_public_display=LicensePublicDisplay.KNOWN,
            attribution="Launch-57 #22 governed price spine",
        ),
        _metric(
            metric_id="landing_trust_pulse_change_24h",
            page_id="landing",
            display_label="Trust Pulse 24h change",
            source_module="launch57.data_batch1:realtime_prices",
            launch_item_id=22,
            api_route="/api/launch57/real-time-prices",
            dom_selector="#lpSym",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="landing_trust_pulse_freshness",
            page_id="landing",
            display_label="Trust Pulse freshness label",
            source_module="launch57.data_batch2:freshness_update_assurance",
            launch_item_id=41,
            api_route="/api/launch57/freshness",
            dom_selector="#lpFresh",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="landing_price_freshness_badge",
            page_id="landing",
            display_label="Price row freshness badge",
            source_module="launch57.data_batch2:freshness_update_assurance",
            launch_item_id=41,
            dom_selector="#lpPriceFresh",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="landing_oracle_freshness",
            page_id="landing",
            display_label="Oracle demo freshness label",
            source_module="launch57.data_batch2:freshness_update_assurance",
            launch_item_id=41,
            dom_selector="#oracleFreshnessLabel",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="landing_oracle_opportunity_score",
            page_id="landing",
            display_label="Oracle demo opportunity score",
            source_module="launch57.trust_batch2:guest_trust_surface",
            launch_item_id=46,
            api_route="/api/launch57/guest-trust",
            dom_selector="#resultScore",
            license_public_display=LicensePublicDisplay.DELAYED,
            attribution="Guest-trust disclosure only — not raw provider feed",
        ),
        # --- status ---
        _metric(
            metric_id="status_component_count",
            page_id="status",
            display_label="Listed system components",
            source_module="site_services:public_status_report",
            dom_selector=".channel-list",
            license_public_display=LicensePublicDisplay.KNOWN,
            attribution="Operational summary — no raw vendor telemetry",
        ),
        # --- oracle accuracy ---
        _metric(
            metric_id="accuracy_average_pct",
            page_id="oracle_accuracy",
            display_label="Average accuracy %",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            api_route="/api/launch57/public-accuracy",
            dom_selector="#stat-accuracy",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="accuracy_total_predictions",
            page_id="oracle_accuracy",
            display_label="Total predictions",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#stat-total",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="accuracy_labeled_samples",
            page_id="oracle_accuracy",
            display_label="Training samples (labeled)",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#stat-labeled",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="accuracy_training_runs",
            page_id="oracle_accuracy",
            display_label="Training runs",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#stat-training",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="accuracy_exchange_count",
            page_id="oracle_accuracy",
            display_label="Exchanges in model",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#stat-exchanges",
            license_public_display=LicensePublicDisplay.DELAYED,
            attribution="Aggregated count — delayed public disclosure",
        ),
        _metric(
            metric_id="accuracy_assets_tracked",
            page_id="oracle_accuracy",
            display_label="Assets tracked",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#stat-assets",
            license_public_display=LicensePublicDisplay.DELAYED,
        ),
        _metric(
            metric_id="accuracy_shareable_outcome",
            page_id="oracle_accuracy",
            display_label="Shareable accuracy (#45)",
            source_module="launch57.trust_batch2:shareable_accuracy",
            launch_item_id=45,
            api_route="/api/launch57/shareable-accuracy",
            dom_selector="#launch57-shareable-accuracy-detail",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
        _metric(
            metric_id="accuracy_live_ledger_sample",
            page_id="oracle_accuracy",
            display_label="Live ledger sample",
            source_module="launch57.trust_batch1:public_accuracy",
            launch_item_id=4,
            dom_selector="#launch57-ledger-detail",
            license_public_display=LicensePublicDisplay.KNOWN,
        ),
    ]
    return rows


def build_public_page_table() -> list[dict[str, Any]]:
    """Pages × governed display sources (STOP table for local closure)."""
    registry = build_public_page_display_registry()
    table: list[dict[str, Any]] = []
    for page in PUBLIC_VISITOR_PAGES:
        metrics = [m for m in registry if m["page_id"] == page["page_id"]]
        table.append(
            {
                "path": page["path"],
                "page_id": page["page_id"],
                "template": page["template"],
                "metric_count": len(metrics),
                "display_sources": [
                    {
                        "metric_id": m["metric_id"],
                        "display_label": m["display_label"],
                        "source_module": m["source_module"],
                        "license_public_display": m["license_public_display"],
                        "api_route": m.get("api_route"),
                    }
                    for m in metrics
                ],
            }
        )
    return table


def verify_registry_completeness() -> dict[str, Any]:
    """Ensure every registry row has a known license posture."""
    registry = build_public_page_display_registry()
    missing_license: list[str] = []
    blocked_without_gate: list[str] = []
    for row in registry:
        status = row.get("license_public_display")
        if status not in {s.value for s in LicensePublicDisplay}:
            missing_license.append(row["metric_id"])
        if status == LicensePublicDisplay.BLOCKED.value and not row.get("raw_provider_blocked_when_unlicensed"):
            blocked_without_gate.append(row["metric_id"])
    pages_with_metrics = {row["page_id"] for row in registry}
    static_legal_pages = {"terms", "privacy", "disclaimer", "how_it_works"}
    pages_without_metrics = [
        p["page_id"]
        for p in PUBLIC_VISITOR_PAGES
        if p["page_id"] not in pages_with_metrics and p["page_id"] not in static_legal_pages
    ]
    return {
        "registry_version": REGISTRY_VERSION,
        "builder_status": BUILDER_STATUS,
        "pass_live_not_claimed": True,
        "metric_count": len(registry),
        "page_count": len(PUBLIC_VISITOR_PAGES),
        "all_metrics_have_license_status": len(missing_license) == 0,
        "missing_license_status": missing_license,
        "blocked_gate_ok": len(blocked_without_gate) == 0,
        "pages_without_numeric_metrics": pages_without_metrics,
        "legal_review_markers_open": True,
        "mica_uk_compliance_claim_forbidden": True,
    }


def resolve_public_display(
    metric_id: str,
    raw_value: Any,
    *,
    license_public_display: str | None = None,
) -> dict[str, Any]:
    """
    Fail-closed display resolver — raw unlicensed provider values are blocked.
    """
    registry = {row["metric_id"]: row for row in build_public_page_display_registry()}
    row = registry.get(metric_id)
    if not row:
        return {
            "metric_id": metric_id,
            "display_allowed": False,
            "display_value": None,
            "reason": "unknown_metric",
            "license_public_display": None,
        }
    allowed_statuses = {s.value for s in LicensePublicDisplay}
    status = row["license_public_display"]
    if license_public_display is not None:
        if license_public_display not in allowed_statuses:
            return {
                "metric_id": metric_id,
                "display_allowed": False,
                "display_value": None,
                "reason": "missing_license_public_display",
                "license_public_display": license_public_display or None,
            }
        status = license_public_display
    if status not in allowed_statuses:
        return {
            "metric_id": metric_id,
            "display_allowed": False,
            "display_value": None,
            "reason": "missing_license_public_display",
            "license_public_display": status,
        }
    if status == LicensePublicDisplay.BLOCKED.value:
        return {
            "metric_id": metric_id,
            "display_allowed": False,
            "display_value": None,
            "reason": "blocked_unlicensed_raw_provider",
            "license_public_display": status,
            "source_module": row["source_module"],
        }
    if status == LicensePublicDisplay.DELAYED.value:
        return {
            "metric_id": metric_id,
            "display_allowed": True,
            "display_value": raw_value,
            "presented_as": "DELAYED",
            "license_public_display": status,
            "source_module": row["source_module"],
            "attribution": row.get("attribution"),
        }
    return {
        "metric_id": metric_id,
        "display_allowed": True,
        "display_value": raw_value,
        "presented_as": "KNOWN",
        "license_public_display": status,
        "source_module": row["source_module"],
        "attribution": row.get("attribution"),
    }


def gate_public_numeric_payload(payload: dict[str, Any], metric_id: str) -> dict[str, Any]:
    """Strip raw provider fields when license posture forbids public display."""
    row = next(
        (r for r in build_public_page_display_registry() if r["metric_id"] == metric_id),
        None,
    )
    if not row:
        return {"allowed": False, "payload": {}, "reason": "unknown_metric"}
    status = row["license_public_display"]
    if status == LicensePublicDisplay.BLOCKED.value:
        return {
            "allowed": False,
            "payload": {},
            "reason": "blocked_unlicensed_raw_provider",
            "license_public_display": status,
        }
    if status not in _LICENSE_ALLOWED:
        return {
            "allowed": False,
            "payload": {},
            "reason": "missing_license_public_display",
            "license_public_display": status,
        }
    return {
        "allowed": True,
        "payload": payload,
        "license_public_display": status,
        "presented_as": "DELAYED" if status == LicensePublicDisplay.DELAYED.value else "KNOWN",
    }


def build_governance_artifact(
    *,
    automated_a11y_scan: dict[str, Any] | None = None,
    footer_link_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Machine-readable closure artifact for governance/launch57/."""
    verification = verify_registry_completeness()
    return {
        "artifact": "BLACKDARK_LAUNCH57_ANONYMOUS_PUBLIC_DISPLAY_SOURCES",
        "registry_version": REGISTRY_VERSION,
        "builder_status": BUILDER_STATUS,
        "pass_live_not_claimed": True,
        "legal_review_markers_open": True,
        "legal_review_required_markers": [
            {
                "id": "uk_financial_promotion",
                "category": "LEGAL_REVIEW_REQUIRED",
                "detail": "UK financial-promotion applicability not closed",
            },
            {
                "id": "mica_casp",
                "category": "LEGAL_REVIEW_REQUIRED",
                "detail": "MiCA/CASP applicability not closed",
            },
        ],
        "mica_uk_compliance_claim_forbidden": True,
        "public_visitor_pages": list(PUBLIC_VISITOR_PAGES),
        "page_table": build_public_page_table(),
        "registry": build_public_page_display_registry(),
        "verification": verification,
        "automated_a11y_scan": automated_a11y_scan,
        "footer_link_probe": footer_link_probe,
    }
