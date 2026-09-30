"""Map security events to customer-exportable CISA-aligned categories."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from security_events import fetch_security_events, security_log_retention_days

_CISA_KINDS = frozenset(
    {
        "login_success",
        "login_failure",
        "logout",
        "mfa_enroll",
        "mfa_disable",
        "sso_login",
        "config_change",
        "admin_policy_update",
        "sso_configure",
        "session_revoke",
        "audit_export",
    }
)


def export_customer_logs(
    *,
    actor_email: str,
    org_id: str | None,
    format: str,
    limit: int,
) -> tuple[str, str, str]:
    rows = fetch_security_events(limit=limit, kinds=_CISA_KINDS)
    # Tenant filter: actor match or org metadata when present
    filtered: list[dict[str, Any]] = []
    for row in rows:
        actor = str(row.get("actor") or "")
        detail = row.get("detail") or {}
        if actor and actor_email and actor.lower() == actor_email.lower():
            filtered.append(row)
            continue
        if org_id and str(detail.get("org_id") or "") == org_id:
            filtered.append(row)
    payload = {
        "retention_days": security_log_retention_days(),
        "count": len(filtered),
        "items": filtered,
    }
    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["iso", "kind", "severity", "actor", "ip"])
        writer.writeheader()
        for r in filtered:
            writer.writerow(
                {
                    "iso": r.get("iso"),
                    "kind": r.get("kind"),
                    "severity": r.get("severity"),
                    "actor": r.get("actor"),
                    "ip": r.get("ip"),
                }
            )
        return buf.getvalue(), "text/csv; charset=utf-8", "customer_security_logs.csv"
    return (
        json.dumps(payload, ensure_ascii=False, indent=2),
        "application/json; charset=utf-8",
        "customer_security_logs.json",
    )
