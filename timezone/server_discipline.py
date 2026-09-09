"""Server clock discipline readiness — TZ-011 (production sync is LIVE_GATED)."""

from __future__ import annotations

import os
from datetime import UTC, datetime


def server_clock_readiness() -> dict[str, object]:
    return {
        "application_default_tz": "UTC",
        "runtime_utc_now": datetime.now(UTC).isoformat(),
        "tz_env": os.getenv("TZ", "UTC"),
        "live_gate": "LIVE_SERVER_CLOCK_SYNC_VERIFIED requires production NTP/managed evidence",
    }
