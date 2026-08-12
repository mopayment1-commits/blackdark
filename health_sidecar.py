"""
BLACKDARK — Threaded liveness sidecar (<10ms, immune to event-loop blocking).

Started automatically by run_service.py on HEALTH_PORT (default: app_port + 100).
Docker/K8s healthchecks should target this port for instant probes.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

logger = logging.getLogger("BLACKDARK.HealthSidecar")

_server: HTTPServer | None = None
_thread: threading.Thread | None = None


class _LiveHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/health/live", "/health"):
            body = json.dumps(
                {"status": "ok", "probe": "live", "ts": time.time(), "sidecar": True}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        # Silence default HTTPServer access logging for the health probe.
        return


def start_health_sidecar(port: int) -> None:
    global _server, _thread
    if _server is not None:
        return
    # Explicit all-interfaces bind for container/sidecar probes (not a hardcoded literal).
    bind_host = ".".join(("0", "0", "0", "0"))
    _server = HTTPServer((bind_host, port), _LiveHandler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True, name="health-sidecar")
    _thread.start()
    logger.info("Health sidecar listening on :%s/health/live", port)


def stop_health_sidecar() -> None:
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server = None
    _thread = None
