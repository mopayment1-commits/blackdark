"""FIPS 140-3 path assessment — no false certification claims."""

from __future__ import annotations

import os
from typing import Any


def fips_path_status() -> dict[str, Any]:
    openssl_fips = os.getenv("OPENSSL_FIPS", "").strip() in {"1", "true", "yes"}
    return {
        "fips_140_3_validated_in_runtime": False,
        "openssl_fips_env_hint": openssl_fips,
        "local_engineering_path": "cryptography + AES-GCM envelope in secrets_vault",
        "status": "NEEDS_EXTERNAL_VERIFICATION",
        "note": "No FIPS 140-3 module validation claimed without provider evidence",
    }
