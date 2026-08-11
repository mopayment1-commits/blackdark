#!/usr/bin/env python3
"""Open Soft Launch env file in the OS default editor (Notepad on Windows).

If the env file is missing or empty, regenerate it first.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / ".env.softlaunch.local"


def _ensure_env(admin_email: str, rotate: bool) -> Path:
    path = DEFAULT_ENV
    needs = (not path.exists()) or path.stat().st_size < 100
    if needs or rotate:
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "bootstrap_free_human_ops.py"),
            "--admin-email",
            admin_email,
        ]
        if rotate or needs:
            cmd.append("--rotate")
        subprocess.check_call(cmd)
    return path


def _open(path: Path) -> int:
    if sys.platform.startswith("win"):
        # Prefer Notepad explicitly so Git Bash users see the same editor.
        return subprocess.call(["notepad", str(path)])
    if sys.platform == "darwin":
        return subprocess.call(["open", str(path)])
    # Linux / cloud VM
    for editor in (os.environ.get("EDITOR"), "xdg-open", "nano", "vi"):
        if not editor:
            continue
        try:
            return subprocess.call([editor, str(path)])
        except FileNotFoundError:
            continue
    print(path)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--admin-email", default="mopayment1@gmail.com")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--no-open", action="store_true", help="Only ensure file exists")
    args = ap.parse_args()

    path = _ensure_env(args.admin_email, args.rotate)
    size = path.stat().st_size
    print(f"Env ready: {path} ({size} bytes)")
    if size < 100:
        print("ERROR: env file still too small", file=sys.stderr)
        return 2
    if args.no_open:
        return 0
    return _open(path)


if __name__ == "__main__":
    raise SystemExit(main())
