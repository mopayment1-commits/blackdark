"""
BLACKDARK — Full due diligence bundle (questions ①–⑳).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


async def build_full_due_diligence_bundle() -> dict[str, Any]:
    from acquisition_assets_service import build_acquisition_asset_audit
    from data_moat_guard import build_moat_build_status
    from due_diligence import due_diligence_report
    from flywheel_saturation_guard import flywheel_saturation_status
    from observability import observability_status
    from retention_service import retention_guard_status

    acquisition = await build_acquisition_asset_audit()
    moat = await build_moat_build_status()
    tech = due_diligence_report()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary_en": (
            "Conditional acquisition: salvageable architecture, emerging data moat, "
            "rules-first AI with ML flywheel. Not a rewrite-trigger."
        ),
        "architecture_verdict": "ACCEPTABLE_WITH_DEBT",
        "scale_100_users": "ok",
        "scale_100k_users": "requires_postgres_redis_horizontal_scaling",
        "ai_verdict": "rules_engine_production_ml_flywheel_phase_1",
        "due_diligence_checks": tech,
        "acquisition_assets": acquisition,
        "data_moat": moat,
        "retention_guard": retention_guard_status(),
        "flywheel_saturation": flywheel_saturation_status(),
        "observability": observability_status(),
        "documentation": {
            "architecture": "docs/ARCHITECTURE.md",
            "runbook": "docs/RUNBOOK.md",
            "data_room": "docs/DATA_ROOM.md",
            "storage": "STORAGE_ARCHITECTURE.md",
            "microservices": "docs/MICROSERVICES_ARCHITECTURE.md",
            "deploy": "DEPLOY.md",
        },
    }
