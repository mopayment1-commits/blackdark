#!/usr/bin/env python3
"""Open .env.softlaunch.local in the easiest local editor (Notepad on Windows)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.softlaunch.local"


def ensure_file() -> None:
    if ENV_PATH.is_file():
        return
    print("File missing — creating with bootstrap_free_human_ops.py ...")
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts" / "bootstrap_free_human_ops.py"),
            "--admin-email",
            os.getenv("ADMIN_EMAIL", "mopayment1@gmail.com"),
        ],
        cwd=str(ROOT),
    )


def main() -> int:
    ensure_file()
    print(f"Opening: {ENV_PATH}")
    print("Do NOT paste secrets into chat or email.")
    if sys.platform.startswith("win"):
        # Notepad — simplest for non-experts on Windows
        subprocess.Popen(["notepad.exe", str(ENV_PATH)])
        return 0
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-t", str(ENV_PATH)])
        return 0
    # Linux: try common editors, then print path
    for cmd in (
        ["xdg-open", str(ENV_PATH)],
        ["gedit", str(ENV_PATH)],
        ["nano", str(ENV_PATH)],
    ):
        try:
            subprocess.Popen(cmd)
            return 0
        except FileNotFoundError:
            continue
    print(f"Open this file manually:\n{ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
