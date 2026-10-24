#!/usr/bin/env python3
"""Check TLS/HSTS/CAA posture for SSL Labs follow-up (read-only)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import Request, urlopen


def _run(cmd: list[str], timeout: int = 25) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout)
        return out.decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return f"ERROR: {exc}"


def check_cert(host: str) -> dict[str, str]:
    raw = _run(
        [
            "openssl",
            "s_client",
            "-connect",
            f"{host}:443",
            "-servername",
            host,
            "-brief",
        ]
    )
    dates = _run(
        [
            "bash",
            "-lc",
            f"echo | openssl s_client -connect {host}:443 -servername {host} 2>/dev/null "
            f"| openssl x509 -noout -dates -issuer",
        ]
    )
    info: dict[str, str] = {"s_client": raw.strip()[:500]}
    for line in dates.splitlines():
        if line.startswith("notBefore=") or line.startswith("notAfter=") or line.startswith("issuer="):
            info[line.split("=", 1)[0]] = line.split("=", 1)[1].strip()
    if "notAfter=" in dates:
        try:
            after = re.search(r"notAfter=(.+)", dates)
            if after:
                exp = datetime.strptime(after.group(1).strip(), "%b %d %H:%M:%S %Y %Z")
                exp = exp.replace(tzinfo=UTC)
                days = (exp - datetime.now(UTC)).days
                info["days_until_expiry"] = str(days)
        except ValueError:
            pass
    return info


def check_hsts(host: str) -> dict[str, str]:
    url = f"https://{host}/"
    req = Request(url, method="HEAD")
    try:
        with urlopen(req, timeout=20) as resp:
            hsts = resp.headers.get("Strict-Transport-Security", "")
            return {
                "hsts": hsts,
                "hsts_ok": "yes"
                if "max-age=31536000" in hsts
                and "includeSubDomains" in hsts
                and "preload" in hsts
                else "no",
                "server": resp.headers.get("Server", ""),
            }
    except URLError as exc:
        return {"hsts": "", "hsts_ok": "no", "error": str(exc)}


def check_caa(zone: str) -> dict[str, str]:
    out = _run(["dig", f"{zone}", "CAA", "+short"])
    if out.startswith("ERROR"):
        out = _run(["dig", "@1.1.1.1", zone, "type257", "+short"])
    return {"caa": out.strip() or "(none)", "caa_present": "yes" if "issue" in out else "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="SSL Labs posture checks")
    parser.add_argument("--host", default="blackdark.io")
    args = parser.parse_args()
    host = args.host.strip()
    print(f"Host: {host}\n")
    cert = check_cert(host)
    print("Certificate:")
    for k in ("notBefore", "notAfter", "days_until_expiry", "issuer"):
        if k in cert:
            print(f"  {k}: {cert[k]}")
    hsts = check_hsts(host)
    print("\nHSTS:")
    print(f"  {hsts.get('hsts', hsts.get('error', ''))}")
    print(f"  expected shape ok: {hsts.get('hsts_ok')}")
    print(f"  server: {hsts.get('server', '')}")
    caa = check_caa(host)
    print("\nDNS CAA:")
    print(f"  {caa['caa']}")
    print(f"  present: {caa['caa_present']}")
    print("\nPlatform notes: OCSP stapling and PQC are controlled by Railway/Cloudflare edge, not app code.")
    print("See deploy/tls/SSL_LABS_REMEDIATION.md and deploy/dns/caa-blackdark-io.md")
    failed = hsts.get("hsts_ok") != "yes"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
