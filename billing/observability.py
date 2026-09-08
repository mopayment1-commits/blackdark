"""P0 observability metrics and alerts (BILL-041, BILL-042)."""

from __future__ import annotations

from typing import Any

from billing.admin_metrics import billing_metrics
from billing.event_inbox import inbox_metrics


async def collect_p0_metrics() -> dict[str, Any]:
    base = await billing_metrics()
    inbox = await inbox_metrics()
    from database import get_connection

    async with get_connection() as db:
        webhook_sig_fail = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_fraud_events
                WHERE event_type = 'webhook_signature_failure'
                """
            )
        ).fetchone()
        paid_no_ent = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM subscription_accounts sa
                WHERE sa.plan != 'free' AND sa.payment_status = 'current'
                  AND sa.subscription_status = 'expired'
                """
            )
        ).fetchone()
        ent_no_proof = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM subscription_accounts
                WHERE plan != 'free' AND payment_status = 'none'
                  AND subscription_status IN ('active', 'trialing')
                """
            )
        ).fetchone()
        recon_mismatch = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM billing_reconciliation_runs WHERE result = 'MISMATCH'"
            )
        ).fetchone()
        tax_fail = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM billing_fraud_events WHERE event_type = 'tax_failure'"
            )
        ).fetchone()
        invoice_fail = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_payment_events
                WHERE event_type = 'invoice' AND status = 'failed'
                """
            )
        ).fetchone()
    metrics = {
        **base,
        **inbox,
        "webhook_signature_failures": int(webhook_sig_fail["c"] if webhook_sig_fail else 0),
        "paid_without_entitlement": int(paid_no_ent["c"] if paid_no_ent else 0),
        "entitlement_without_payment_proof": int(ent_no_proof["c"] if ent_no_proof else 0),
        "reconciliation_mismatch_count": int(recon_mismatch["c"] if recon_mismatch else 0),
        "tax_failures": int(tax_fail["c"] if tax_fail else 0),
        "invoice_failures": int(invoice_fail["c"] if invoice_fail else 0),
    }
    metrics["critical_alerts"] = evaluate_critical_alerts(metrics)
    return metrics


def evaluate_critical_alerts(metrics: dict[str, Any]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if metrics.get("inbox_pending", 0) > 100:
        alerts.append({"code": "inbox_backlog", "severity": "critical"})
    if metrics.get("dlq_size", 0) > 0:
        alerts.append({"code": "dlq_growth", "severity": "critical"})
    if metrics.get("paid_without_entitlement", 0) > 0:
        alerts.append({"code": "paid_no_entitlement", "severity": "critical"})
    if metrics.get("entitlement_without_payment_proof", 0) > 0:
        alerts.append({"code": "entitlement_no_proof", "severity": "critical"})
    if metrics.get("reconciliation_mismatch_count", 0) > 0:
        alerts.append({"code": "reconciliation_mismatch", "severity": "critical"})
    if metrics.get("failed_payments", 0) > 50:
        alerts.append({"code": "high_decline_velocity", "severity": "warning"})
    if metrics.get("refunds_disputes", 0) > 20:
        alerts.append({"code": "dispute_spike", "severity": "warning"})
    return alerts
