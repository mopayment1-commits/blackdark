"""Formal EXTERNAL registry — machine-readable, no false INTERNAL closure."""

from __future__ import annotations

from typing import Any

from cap646.catalog import EXTERNAL_IDS as BASE_EXTERNAL_IDS
from cap646.waves import EXTERNAL_EVIDENCE_SLOTS, SIGNED_INFRA_SLOTS
from cap978.catalog import EXTENSION_EXTERNAL_IDS, catalog_by_id

_EXTERNAL_REASONS: dict[int, str] = {
    647: "Low-latency institutional feed SLA — vendor contract required",
    648: "Institutional datashare connector — external warehouse agreement",
    649: "dbt Cloud/project integration — external dbt deployment",
    652: "BI connector licenses (Tableau/Looker/Power BI)",
    658: "Snowflake/BigQuery export — external cloud infra credentials",
    672: "Chainalysis API — paid compliance vendor",
    673: "Elliptic API — paid compliance vendor",
    674: "TRM Labs API — paid compliance vendor",
    675: "Nansen full API — paid on-chain intelligence vendor",
    676: "Arkham full API — paid on-chain intelligence vendor",
    690: "Bloomberg Terminal bridge — external terminal license",
    691: "Refinitiv Eikon bridge — external terminal license",
    702: "Kaiko institutional data — paid market data vendor",
    703: "Amberdata institutional — paid market data vendor",
    704: "CryptoQuant full tier — paid analytics vendor",
    705: "Glassnode full tier — paid on-chain analytics vendor",
}

_CONTROL_EXTERNAL = [
    {"id": "SEC-008", "reason": "Third-party penetration test attestation — ID645 slot"},
    {"id": "SEC-009", "reason": "SOC2/ISO certification — external audit firm"},
]

_BASE_VENDOR_REASON = "Paid on-chain/market data vendor — API rights + contract required"


def production_signed_capacity_closes_644() -> bool:
    """True when verified production signed capacity satisfies CAP-644 closure."""
    try:
        from institutional_assurance import get_signed_capacity, verify_signed_capacity

        cap = get_signed_capacity()
        env = str((cap or {}).get("environment") or "").strip().lower()
        return bool(cap and env == "production" and verify_signed_capacity(cap))
    except Exception:
        return False


def expected_external_capability_ids() -> set[int]:
    """Capability slots represented in the external registry (env-aware for CAP-644)."""
    slots = set(BASE_EXTERNAL_IDS) | set(EXTENSION_EXTERNAL_IDS) | set(EXTERNAL_EVIDENCE_SLOTS) | set(SIGNED_INFRA_SLOTS)
    if production_signed_capacity_closes_644():
        slots.discard(644)
    return slots


def external_registry_rows() -> list[dict[str, Any]]:
    cat = catalog_by_id()
    rows: list[dict[str, Any]] = []

    for cid in sorted(BASE_EXTERNAL_IDS):
        row = cat.get(cid, {})
        rows.append(
            {
                "id": cid,
                "scope": "base_646",
                "capability": row.get("capability", f"ID{cid}"),
                "track": row.get("track"),
                "classification": "EXTERNAL_BLOCKED",
                "blocker_type": "vendor_api_rights",
                "reason": _BASE_VENDOR_REASON,
                "internal_action": "none — requires external contract or product downgrade label",
            }
        )

    for cid in sorted(EXTENSION_EXTERNAL_IDS):
        row = cat.get(cid, {})
        rows.append(
            {
                "id": cid,
                "scope": "extension_647_978",
                "capability": row.get("capability", f"ID{cid}"),
                "track": row.get("track", "T19"),
                "classification": "EXTERNAL_BLOCKED",
                "blocker_type": "vendor_license_or_infra",
                "reason": _EXTERNAL_REASONS.get(cid, "External vendor or infrastructure dependency"),
                "internal_action": "none — requires external provisioning",
            }
        )

    for cid in EXTERNAL_EVIDENCE_SLOTS:
        row = cat.get(cid, {})
        rows.append(
            {
                "id": cid,
                "scope": "base_646",
                "capability": row.get("capability", f"ID{cid}"),
                "track": row.get("track"),
                "classification": "EXTERNAL_EVIDENCE_REQUIRED",
                "blocker_type": "independent_attestation",
                "reason": "ID645 pentest attestation" if cid == 645 else "Third-party security verification attestation",
                "internal_action": "none — requires external auditor attestation",
            }
        )

    for cid in SIGNED_INFRA_SLOTS:
        if cid in EXTERNAL_EVIDENCE_SLOTS:
            continue
        if cid == 644 and production_signed_capacity_closes_644():
            continue
        row = cat.get(cid, {})
        rows.append(
            {
                "id": cid,
                "scope": "base_646",
                "capability": row.get("capability", f"ID{cid}"),
                "track": row.get("track"),
                "classification": "EXTERNAL_EVIDENCE_REQUIRED",
                "blocker_type": "signed_load_evidence",
                "reason": "Signed multi-worker capacity/load attestation — ID644",
                "internal_action": "none — requires signed load test under production topology",
            }
        )

    for ctrl in _CONTROL_EXTERNAL:
        rows.append(
            {
                "id": ctrl["id"],
                "scope": "governing_control",
                "capability": ctrl["id"],
                "track": ctrl["id"].split("-")[0],
                "classification": "EXTERNAL_BLOCKED",
                "blocker_type": "external_infrastructure_or_audit",
                "reason": ctrl["reason"],
                "internal_action": "none — human/external provisioning required",
            }
        )
    return rows


def external_registry_report() -> dict[str, Any]:
    rows = external_registry_rows()
    by_class: dict[str, int] = {}
    for row in rows:
        cls = row["classification"]
        by_class[cls] = by_class.get(cls, 0) + 1
    return {
        "total": len(rows),
        "counts": by_class,
        "capability_ids_blocked": len([r for r in rows if isinstance(r.get("id"), int)]),
        "controls_blocked": len([r for r in rows if isinstance(r.get("id"), str)]),
        "rows": rows,
        "policy": "EXTERNAL_BLOCKED and EXTERNAL_EVIDENCE_REQUIRED are excluded from internal closure numerator",
    }
