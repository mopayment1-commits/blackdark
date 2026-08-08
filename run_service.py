#!/usr/bin/env python3
"""
BLACKDARK — Microservice launcher.

Examples:
  python run_service.py web          # UI/API on :8080
  python run_service.py aggregator   # market worker on :8091
  python run_service.py arbitrage    # arb bot on :8092
  python run_service.py ingestion    # data ingestion on :8093
  python run_service.py all          # monolith on :8080
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import encoding_bootstrap  # noqa: F401 — UTF-8 Arabic in console
from path_safety import validate_bind_host, validate_port

MODES = {
    "all": ("dashboard:app", 8080),
    "web": ("dashboard:app", 8080),
    "aggregator": ("microservices.worker_app:app", 8091),
    "arbitrage": ("microservices.worker_app:app", 8092),
    "ingestion": ("microservices.worker_app:app", 8093),
}
_ALLOWED_TARGETS = frozenset(target for target, _ in MODES.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="BLACKDARK microservice launcher")
    parser.add_argument("mode", choices=list(MODES.keys()), nargs="?", default="all")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    if args.mode not in MODES:
        raise SystemExit(f"Unsupported mode: {args.mode!r}")

    try:
        host = validate_bind_host(args.host)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    os.environ["SERVICE_MODE"] = args.mode
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if args.mode == "web":
        os.environ.setdefault("RUN_AGGREGATOR", "false")
        os.environ.setdefault("INGESTION_ENABLED", "false")

    target, default_port = MODES[args.mode]
    if target not in _ALLOWED_TARGETS:
        raise SystemExit(f"Unsupported uvicorn target: {target!r}")

    try:
        port = validate_port(args.port or default_port)
        health_port = validate_port(int(os.getenv("HEALTH_PORT", str(port + 100))))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    from health_sidecar import start_health_sidecar

    start_health_sidecar(health_port)
    print(f"Health sidecar: http://0.0.0.0:{health_port}/health/live")

    try:
        from bd_platform.auto_keys import apply_keys_to_process_env, ensure_keys_file

        ensure_keys_file()
        applied = apply_keys_to_process_env()
        if applied:
            print(f"Platform keys loaded from keys/platform_keys.env ({applied})")
    except Exception:
        pass

    try:
        from execution_keys import apply_exchange_keys_to_env, ensure_keys_file as ensure_exec_keys

        ensure_exec_keys()
        applied_exec = apply_exchange_keys_to_env()
        if applied_exec:
            print(f"Exchange keys loaded from keys/exchange_keys.env ({applied_exec})")
    except Exception:
        pass

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        target,
        "--host",
        host,
        "--port",
        str(port),
    ]
    # Viral / HA: honor WEB_CONCURRENCY (or UVICORN_WORKERS) for web/monolith.
    workers = 1
    if args.mode in {"web", "all"}:
        try:
            workers = max(
                1,
                int(os.getenv("WEB_CONCURRENCY") or os.getenv("UVICORN_WORKERS") or "1"),
            )
        except ValueError:
            workers = 1
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    print(
        f"Starting BLACKDARK | mode={args.mode} port={port} workers={workers}"
    )
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
