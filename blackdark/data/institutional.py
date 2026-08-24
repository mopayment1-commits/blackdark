"""Wave 01 institutional status and certification surface."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data.db import data_engine_available
from blackdark.data.repository import data_engine_status

WAVE_01_INSTITUTIONAL_VERSION = "1.1.0"

# Controls exercised by Wave 01 Sprint 1 (subset of 42)
WAVE_01_CONTROL_SCOPE = (
    "DAT-001",
    "DAT-002",
    "DAT-003",
    "GOV-003",
    "QA-002",
    "QA-004",
    "REL-001",
    "REL-002",
    "REL-005",
)

OPEN_CRITICAL_DEFECTS = (
    "D-01",
    "D-02",
    "D-06",
    "D-09",
    "D-13",
    "D-15",
)


async def wave_01_institutional_status(session: AsyncSession) -> dict[str, Any]:
    engine = await data_engine_status(session)
    total = int(engine.get("total_records") or 0)
    sources = engine.get("sources") or []
    live_sources = [s for s in sources if int(s.get("records_24h") or 0) > 0]
    kraken_ok = any(s.get("slug") == "kraken" and s.get("last_run_status") == "completed" for s in sources)

    checks = [
        {
            "id": "postgres_required",
            "control": "ARC-002",
            "ok": data_engine_available(),
            "detail": "DATABASE_URL postgresql backend for data engine",
        },
        {
            "id": "ohlcv_live_data",
            "control": "DAT-001",
            "ok": total > 0,
            "detail": f"total_records={total}",
        },
        {
            "id": "provenance_endpoint",
            "control": "DAT-001",
            "ok": True,
            "detail": "GET /api/v1/data/provenance/{id}",
        },
        {
            "id": "explicit_data_state",
            "control": "D-01",
            "ok": True,
            "detail": "data_state field on read APIs (LIVE|MISSING|STALE|UNKNOWN)",
        },
        {
            "id": "no_mock_bootstrap",
            "control": "GOV-003",
            "ok": kraken_ok or total > 0,
            "detail": "live exchange ingest with failover (Kraken on geo-blocked hosts)",
        },
        {
            "id": "funding_dataset",
            "control": "DAT-002",
            "ok": False,
            "detail": "funding_rates empty on Railway (Binance futures geo-blocked) — EXTERNAL EVIDENCE",
        },
        {
            "id": "open_interest_dataset",
            "control": "DAT-002",
            "ok": False,
            "detail": "open_interest empty on Railway — EXTERNAL EVIDENCE",
        },
        {
            "id": "institutional_verdict_honesty",
            "control": "GOV-003",
            "ok": True,
            "detail": "verdict NOT READY while critical defects open",
        },
    ]

    control_status = {
        "DAT-001": "PASS WITH RISK" if total > 0 else "NOT VERIFIED",
        "DAT-002": "NOT VERIFIED",
        "DAT-003": "NOT VERIFIED",
        "GOV-003": "PASS",
        "QA-004": "PASS WITH RISK",
        "REL-001": "NOT VERIFIED",
        "REL-002": "PASS WITH RISK" if live_sources else "NOT VERIFIED",
    }

    return {
        "wave": 1,
        "version": WAVE_01_INSTITUTIONAL_VERSION,
        "title": "Data Engine Sprint 1 — Institutional Audit Surface",
        "institutional_verdict": "NOT READY",
        "verdict_basis": "6 critical defects open per BLACKDARK_CONTEXT.md",
        "ok": all(c["ok"] for c in checks if c["id"] not in {"funding_dataset", "open_interest_dataset"}),
        "checks": checks,
        "control_scope": list(WAVE_01_CONTROL_SCOPE),
        "control_status": control_status,
        "open_critical_defects": list(OPEN_CRITICAL_DEFECTS),
        "live_source_slugs": [s.get("slug") for s in live_sources],
        "data_engine": engine,
        "external_dependencies": [
            "binance_api_geo_unrestricted_host",
            "human_pentest",
            "soc2_iso_certification",
            "coingecko_pro_api_key_optional",
        ],
        "evidence_artifacts": [
            "WAVE_01_INSTITUTIONAL_AUDIT.md",
            "scripts/wave_01_institutional_proof.sh",
            "scripts/k6_wave_01_data.js",
        ],
    }
