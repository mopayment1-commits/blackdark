#!/usr/bin/env python3
"""Run i18n 38-locale audit and emit closure artifact."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from i18n_enforcement import audit_i18n_coverage, closure_flags  # noqa: E402
from i18n_service import LOCALES, invalidate_catalogs  # noqa: E402

ADDED = [
    "uk",
    "sw",
    "ta",
    "te",
    "mr",
    "jv",
    "cs",
    "sv",
    "ro",
    "el",
    "pt-PT",
    "hu",
    "pcm",
]


def main() -> int:
    invalidate_catalogs()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_i18n_38_locales.py",
            "tests/test_i18n_language_actually_switches.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    pytest_ok = proc.returncode == 0
    flags = closure_flags(pytest_ok=pytest_ok)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    artifact = {
        "generated_at": datetime.now(UTC).isoformat(),
        "material_sha": sha,
        "existing_locale_count_before": 25,
        "final_locale_count": len(LOCALES),
        "locales_added": ADDED,
        "implementation_paths": [
            "i18n_service.py",
            "i18n_enforcement.py",
            "locales/*.json",
            "email_outbox.py",
            "alert_service.py",
            "scripts/i18n_38_locale_build.py",
            "tests/test_i18n_38_locales.py",
        ],
        "pytest_output": proc.stdout[-4000:],
        "pytest_stderr": proc.stderr[-2000:],
        **flags,
    }
    out = ROOT / "docs" / "I18N_38_LOCALE_CLOSURE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: artifact[k] for k in sorted(artifact) if k.startswith(("SUPPORTED", "USER_", "AI_", "NOTIFICATION", "EMAIL", "BILLING", "RTL", "MISSING", "UNINTENTIONAL", "UNLOCALIZED", "BROKEN", "KNOWN", "LOCAL_", "PASS_"))}, indent=2))
    return 0 if flags["PASS_ENGINEERING_I18N"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
