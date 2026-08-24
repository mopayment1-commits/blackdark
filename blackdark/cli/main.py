"""BLACKDARK CLI entrypoint — Feature #167 (Institution tier)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from blackdark.cli.client import BlackdarkApiClient, CliApiError
from blackdark.cli.commands import COMMANDS, command_names, run_command
from blackdark.cli.errors import EXIT_ERROR, EXIT_OK, EXIT_USAGE

__version__ = "1.0.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blackdark",
        description="BLACKDARK CLI — Institution tier REST API wrapper (#167)",
    )
    parser.add_argument("--version", action="version", version=f"blackdark {__version__}")
    parser.add_argument("--base-url", default=None, help="API base URL (default: BLACKDARK_API_URL)")
    parser.add_argument("--api-key", default=None, help="X-API-Key header")
    parser.add_argument("--token", default=None, help="Bearer session token")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("command", nargs="?", choices=command_names() + ["help"], help="Command name")
    parser.add_argument("args", nargs="*", help="Command arguments")
    return parser


def _format_human(command: str, data: dict[str, Any]) -> str:
    if command == "price":
        price = data.get("weighted_price") or data.get("price_usd") or data.get("price")
        return f"{data.get('asset', 'ASSET')}: ${float(price or 0):,.4f} (sources: {data.get('source_count', '?')})"
    if command == "alert":
        alerts = data.get("alerts") or []
        lines = [f"Alerts ({len(alerts)}):"]
        for row in alerts[:10]:
            lines.append(f"  - [{row.get('level', 'info')}] {row.get('title')}: {row.get('body')}")
        return "\n".join(lines) if alerts else "No alerts."
    if command == "portfolio":
        return data.get("headline") or data.get("one_sentence") or json.dumps(data, indent=2)
    if command == "dd":
        report = data.get("report") or data
        return report.get("headline") or report.get("summary") or json.dumps(report, indent=2)
    if command == "status":
        return f"CLI v{__version__} | API: {data.get('api_url')} | tier: {data.get('tier', 'unknown')}"
    headline = data.get("headline") or data.get("summary")
    if headline:
        return str(headline)
    return json.dumps(data, indent=2, default=str)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    if not ns.command or ns.command == "help":
        lines = ["BLACKDARK CLI commands (Institution tier):"]
        for name in command_names():
            spec = COMMANDS[name]
            lines.append(f"  blackdark {name} — {spec.description}")
        lines.append("\nExamples:")
        lines.append("  blackdark price BTC")
        lines.append("  blackdark alert list")
        lines.append("  blackdark portfolio check ETH")
        lines.append("  blackdark dd BTC one_page")
        print("\n".join(lines))
        return EXIT_OK

    client = BlackdarkApiClient(
        base_url=ns.base_url,
        api_key=ns.api_key,
        bearer_token=ns.token,
    )

    try:
        data = run_command(client, ns.command, ns.args)
    except ValueError as exc:
        print(f"Usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except CliApiError as exc:
        print(f"API error ({exc.status}): {exc}", file=sys.stderr)
        return exc.exit_code

    if ns.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(_format_human(ns.command, data))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
