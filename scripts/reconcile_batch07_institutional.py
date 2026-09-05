#!/usr/bin/env python3
"""Batch07 final institutional reconciliation — audit-defect closure only."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_batch07_institutional_package import main  # noqa: E402

if __name__ == "__main__":
    main()
