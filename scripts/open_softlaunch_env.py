#!/usr/bin/env python3
"""Open Soft Launch env file in the OS default editor (Notepad on Windows).

If the env file is missing or empty, regenerate it first.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / ".env.softlaunch.local"
_EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
# Fixed editor binaries only — never pass raw untrusted CLI/env tokens to the OS.
_SAFE_EDITORS = {
    "win": ("notepad",),
    "darwin": ("open",),
    "linux": ("xdg-open", "nano", "vi", "vim"),
}


def _validate_admin_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    if len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        raise ValueError(f"Invalid admin email: {raw!r}")
    if any(ch in email for ch in (";", "|", "&", "$", "`", "\n", "\r", " ", "\t")):
        raise ValueError(f"Invalid admin email: {raw!r}")
    return email


def _load_bootstrap():
    path = ROOT / "scripts" / "bootstrap_free_human_ops.py"
    spec = importlib.util.spec_from_file_location("bootstrap_free_human_ops", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bootstrap module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ensure_env(admin_email: str, rotate: bool) -> Path:
    """Regenerate env in-process — no subprocess argv taint sink (Sonar S2076/S6350)."""
    email = _validate_admin_email(admin_email)
    path = DEFAULT_ENV
    needs = (not path.exists()) or path.stat().st_size < 100
    if needs or rotate:
        bootstrap = _load_bootstrap()
        result = bootstrap.write_softlaunch_env(admin_email=email, rotate=bool(rotate or needs))
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "bootstrap_failed")
    return path


def _open(path: Path) -> int:
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Refusing to open path outside project root")
    target = str(path.resolve())
    if sys.platform.startswith("win"):
        return subprocess.call([_SAFE_EDITORS["win"][0], target])  # nosec B603
    if sys.platform == "darwin":
        return subprocess.call([_SAFE_EDITORS["darwin"][0], target])  # nosec B603
    # Prefer allowlisted editors only — never forward raw EDITOR / CLI tokens.
    candidates: list[str] = []
    env_editor = Path((os.environ.get("EDITOR") or "").strip()).name
    if env_editor in _SAFE_EDITORS["linux"]:
        candidates.append(env_editor)
    candidates.extend(_SAFE_EDITORS["linux"])
    seen: set[str] = set()
    for editor in candidates:
        if editor in seen:
            continue
        seen.add(editor)
        try:
            return subprocess.call([editor, target])  # nosec B603
        except FileNotFoundError:
            continue
    print(target)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--admin-email", default="mopayment1@gmail.com")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--no-open", action="store_true", help="Only ensure file exists")
    args = ap.parse_args()

    try:
        path = _ensure_env(args.admin_email, args.rotate)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
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
