#!/usr/bin/env python3
"""Build BILLING_IMPLEMENTATION_INDEX.json from source universe + repository bindings."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "docs/BILLING_FULL_SOURCE_UNIVERSE.json"
OUT = ROOT / "docs/BILLING_IMPLEMENTATION_INDEX.json"

# Canonical implementation bindings per BILL requirement
BINDINGS: dict[str, dict] = {
    "BILL-001": {"domain": "principles", "module_paths": ["billing/subscription_engine.py", "billing/entitlement_state.py"], "reuse": "KEEP"},
    "BILL-002": {"domain": "provider_eligibility", "module_paths": ["billing/ops_readiness.py"], "reuse": "KEEP", "gate": "LIVE_GATED"},
    "BILL-003": {"domain": "architecture", "module_paths": ["billing/event_processor.py", "billing/webhook_processor.py", "billing/subscription_engine.py"], "reuse": "REUSE"},
    "BILL-004": {"domain": "database", "module_paths": ["database.py"], "reuse": "REUSE"},
    "BILL-005": {"domain": "event_inbox", "module_paths": ["billing/event_inbox.py"], "reuse": "BUILD"},
    "BILL-006": {"domain": "webhook_security", "module_paths": ["billing_service.py", "dashboard.py"], "reuse": "REUSE"},
    "BILL-007": {"domain": "async_processing", "module_paths": ["billing/event_processor.py"], "reuse": "BUILD"},
    "BILL-008": {"domain": "out_of_order", "module_paths": ["billing/out_of_order_guard.py"], "reuse": "BUILD"},
    "BILL-009": {"domain": "billing_state", "module_paths": ["billing/billing_states.py", "billing/subscription_store.py"], "reuse": "BUILD"},
    "BILL-010": {"domain": "entitlement_state", "module_paths": ["billing/entitlement_state.py"], "reuse": "BUILD"},
    "BILL-011": {"domain": "paid_through", "module_paths": ["billing/entitlement_state.py"], "reuse": "BUILD"},
    "BILL-012": {"domain": "free_plan", "module_paths": ["billing/plan_registry.py", "billing/subscription_engine.py"], "reuse": "KEEP"},
    "BILL-013": {"domain": "price_registry", "module_paths": ["billing/plan_registry.py", "billing/price_versioning.py"], "reuse": "REUSE"},
    "BILL-014": {"domain": "price_versioning", "module_paths": ["billing/price_versioning.py"], "reuse": "BUILD"},
    "BILL-015": {"domain": "signup", "module_paths": ["billing/subscription_engine.py", "api/routers/billing.py"], "reuse": "REUSE"},
    "BILL-016": {"domain": "upgrade", "module_paths": ["billing/subscription_engine.py"], "reuse": "KEEP"},
    "BILL-017": {"domain": "downgrade", "module_paths": ["billing/subscription_engine.py", "billing/sweeper.py"], "reuse": "KEEP"},
    "BILL-018": {"domain": "proration", "module_paths": ["billing/financial_arithmetic.py"], "reuse": "BUILD"},
    "BILL-019": {"domain": "renewal", "module_paths": ["billing/subscription_engine.py"], "reuse": "KEEP"},
    "BILL-020": {"domain": "renewal_reminder", "module_paths": ["billing/renewal_reminder.py"], "reuse": "BUILD"},
    "BILL-021": {"domain": "dunning", "module_paths": ["billing/subscription_engine.py"], "reuse": "KEEP"},
    "BILL-022": {"domain": "grace", "module_paths": ["billing/subscription_engine.py", "billing/entitlement_state.py"], "reuse": "REUSE"},
    "BILL-023": {"domain": "card_declines", "module_paths": ["billing/card_declines.py"], "reuse": "BUILD"},
    "BILL-024": {"domain": "payment_methods", "module_paths": ["billing_service.py", "payments_usd.py"], "reuse": "KEEP", "gate": "LIVE_GATED"},
    "BILL-025": {"domain": "customer_portal", "module_paths": ["billing_service.py", "api/routers/billing.py"], "reuse": "REUSE"},
    "BILL-026": {"domain": "cancellation", "module_paths": ["billing/subscription_engine.py", "api/routers/billing.py"], "reuse": "KEEP"},
    "BILL-027": {"domain": "refunds", "module_paths": ["billing/webhook_resolver.py", "billing/subscription_engine.py"], "reuse": "IMPROVE"},
    "BILL-028": {"domain": "disputes", "module_paths": ["billing/webhook_resolver.py"], "reuse": "IMPROVE"},
    "BILL-029": {"domain": "reconciliation", "module_paths": ["billing/reconciliation.py", "billing/sweeper.py"], "reuse": "BUILD"},
    "BILL-030": {"domain": "invoices", "module_paths": ["billing/subscription_engine.py", "institutional_commerce.py"], "reuse": "REUSE"},
    "BILL-031": {"domain": "financial_arithmetic", "module_paths": ["billing/financial_arithmetic.py"], "reuse": "BUILD"},
    "BILL-032": {"domain": "cost_model", "module_paths": ["payments_usd.py"], "reuse": "KEEP"},
    "BILL-033": {"domain": "taxes", "module_paths": ["billing/consent_registry.py", "billing/price_versioning.py"], "reuse": "REUSE"},
    "BILL-034": {"domain": "sca", "module_paths": ["billing/entitlement_state.py"], "reuse": "REUSE"},
    "BILL-035": {"domain": "pci", "module_paths": ["payments_usd.py"], "reuse": "KEEP"},
    "BILL-036": {"domain": "secrets", "module_paths": ["production_guard.py", "config.py"], "reuse": "KEEP"},
    "BILL-037": {"domain": "audit", "module_paths": ["billing/audit_ledger.py"], "reuse": "KEEP"},
    "BILL-038": {"domain": "break_glass", "module_paths": ["billing/break_glass.py"], "reuse": "BUILD"},
    "BILL-039": {"domain": "admin_console", "module_paths": ["api/routers/admin_billing.py"], "reuse": "REUSE"},
    "BILL-040": {"domain": "fraud", "module_paths": ["billing/fraud_controls.py"], "reuse": "BUILD"},
    "BILL-041": {"domain": "observability", "module_paths": ["billing/observability.py", "billing/admin_metrics.py"], "reuse": "BUILD"},
    "BILL-042": {"domain": "alerts", "module_paths": ["billing/observability.py"], "reuse": "BUILD"},
    "BILL-043": {"domain": "b2b", "module_paths": ["billing/seat_enforcement.py"], "reuse": "BUILD"},
    "BILL-044": {"domain": "seats", "module_paths": ["billing/seat_enforcement.py"], "reuse": "BUILD"},
    "BILL-045": {
        "domain": "enterprise_terms",
        "module_paths": ["billing/seat_enforcement.py", "institutional_commerce.py", "docs/BILLING_OWNER_LAUNCH_POLICY.json"],
        "reuse": "REUSE",
        "launch_policy_notes": "DISABLED_AT_LAUNCH; PREPAID_ONLY; NET_15/NET_30 disabled; future NET via governed admin only",
    },
    "BILL-046": {
        "domain": "multi_currency",
        "module_paths": ["billing/price_versioning.py", "docs/BILLING_OWNER_LAUNCH_POLICY.json"],
        "reuse": "REUSE",
        "launch_policy_notes": "DISABLED_AT_LAUNCH; USD_ONLY; architecture preserved; future currencies require owner approval",
    },
    "BILL-047": {"domain": "legal", "module_paths": ["docs/SUBSCRIPTION_LEGAL_BASIS.md"], "reuse": "BUILD"},
    "BILL-048": {"domain": "consent", "module_paths": ["billing/consent_registry.py"], "reuse": "BUILD"},
    "BILL-049": {"domain": "privacy", "module_paths": ["docs/SUBSCRIPTION_LEGAL_BASIS.md"], "reuse": "REUSE"},
    "BILL-050": {"domain": "retention", "module_paths": ["docs/SUBSCRIPTION_LEGAL_BASIS.md"], "reuse": "BUILD"},
    "BILL-051": {"domain": "customer_ux", "module_paths": ["pricing_catalog.py", "api/routers/billing.py"], "reuse": "REUSE"},
    "BILL-052": {"domain": "capability_enforcement", "module_paths": ["cap646/entitlements.py", "billing/subscription_engine.py"], "reuse": "KEEP"},
    "BILL-053": {"domain": "tier_consistency", "module_paths": ["cap646/entitlements.py", "billing/plan_registry.py"], "reuse": "KEEP"},
    "BILL-054": {"domain": "failure_safety", "module_paths": ["billing/event_inbox.py", "billing/reconciliation.py"], "reuse": "BUILD"},
    "BILL-055": {"domain": "dlq", "module_paths": ["billing/event_inbox.py"], "reuse": "BUILD"},
    "BILL-056": {"domain": "replay", "module_paths": ["billing/event_inbox.py"], "reuse": "BUILD"},
    "BILL-057": {"domain": "concurrency", "module_paths": ["billing/out_of_order_guard.py", "database.py"], "reuse": "BUILD"},
    "BILL-058": {"domain": "reliability", "module_paths": ["billing/subscription_engine.py", "billing/event_inbox.py"], "reuse": "REUSE"},
    "BILL-059": {"domain": "p0_test_matrix", "module_paths": ["tests/test_billing_p0_test_matrix.py", "tests/test_billing_subscription_engine.py"], "reuse": "BUILD"},
    "BILL-060": {"domain": "acceptance_gates", "module_paths": ["scripts/billing_source_driven_final_closure.py"], "reuse": "BUILD"},
    "BILL-061": {"domain": "live_activation", "module_paths": ["billing/ops_readiness.py"], "reuse": "KEEP", "gate": "LIVE_GATED"},
    "BILL-062": {"domain": "implementation_phases", "module_paths": ["scripts/billing_source_driven_final_closure.py"], "reuse": "BUILD"},
}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    universe = json.loads(UNIVERSE.read_text(encoding="utf-8")) if UNIVERSE.is_file() else {"requirements": []}
    bindings_out = {}
    for req in universe.get("requirements", []):
        rid = req["requirement_id"]
        base = BINDINGS.get(rid, {"domain": "cross_cutting", "module_paths": [], "reuse": "REUSE"})
        bindings_out[rid] = {
            **base,
            "requirement_id": rid,
            "title": req.get("title"),
            "test_paths": ["tests/test_billing_p0_test_matrix.py", "tests/test_billing_subscription_engine.py"],
            "implementation_intended": base.get("gate") not in {"LIVE_GATED", "EXTERNAL_GATED"},
        }
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "bindings": bindings_out,
        "total_bindings": len(bindings_out),
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "bindings": len(bindings_out)}, indent=2))


if __name__ == "__main__":
    main()
