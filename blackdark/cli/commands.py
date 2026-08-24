"""CLI command registry — maps CLI verbs to REST API paths (#167)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from blackdark.cli.client import BlackdarkApiClient


@dataclass(frozen=True)
class CliCommand:
    name: str
    description: str
    method: str
    path_template: str
    institution_only: bool = True


COMMANDS: dict[str, CliCommand] = {
    "price": CliCommand("price", "Aggregated price for asset", "GET", "/api/platform/infra/prices/aggregate"),
    "market-health": CliCommand("market-health", "Market health dashboard", "GET", "/api/platform/market-health/dashboard"),
    "confidence": CliCommand("confidence", "Confidence score", "GET", "/api/platform/confidence/score"),
    "execution-quality": CliCommand(
        "execution-quality", "Execution quality / slippage", "GET", "/api/platform/infra/execution-quality/score"
    ),
    "macro": CliCommand("macro", "Macro context relationships", "GET", "/api/platform/macro/context"),
    "spread": CliCommand("spread", "Gross/net spread calculator", "GET", "/api/platform/infra/spread/calculate"),
    "transfer": CliCommand("transfer", "Transfer optimizer status", "GET", "/api/platform/transfer/optimizer"),
    "entity": CliCommand("entity", "On-chain entity lookup", "GET", "/api/v1/entities/{address}"),
    "tx": CliCommand("tx", "Transaction decoder", "GET", "/api/v1/transactions/{hash}"),
    "dd": CliCommand("dd", "Due diligence research report", "GET", "/api/platform/research/dd-report"),
    "status": CliCommand("status", "CLI + API status", "GET", "/api/platform/cli/status"),
    "alert": CliCommand("alert", "Alert inbox", "GET", "/api/alerts/inbox", institution_only=False),
    "portfolio": CliCommand("portfolio", "Portfolio risk check", "GET", "/api/platform/cli/portfolio-check"),
}


def _build_params(command: str, args: list[str]) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    if command == "price" and args:
        return COMMANDS["price"].path_template, {"asset": args[0].upper()}, None
    if command == "market-health":
        return COMMANDS["market-health"].path_template, {"asset": (args[0] if args else "BTC").upper()}, None
    if command == "confidence" and args:
        return COMMANDS["confidence"].path_template, {"asset": args[0].upper()}, None
    if command == "execution-quality" and args:
        return (
            COMMANDS["execution-quality"].path_template,
            {"asset": args[0].upper(), "amount_usd": float(args[1]) if len(args) > 1 else 5000.0},
            None,
        )
    if command == "macro":
        return COMMANDS["macro"].path_template, {"asset": (args[0] if args else "BTC").upper()}, None
    if command == "spread" and args:
        return COMMANDS["spread"].path_template, {"symbol": args[0].upper()}, None
    if command == "transfer":
        params = {
            "asset": (args[0] if len(args) > 0 else "USDT").upper(),
            "source_cex": args[1] if len(args) > 1 else "binance",
            "dest_cex": args[2] if len(args) > 2 else "kraken",
            "amount_usd": float(args[3]) if len(args) > 3 else 1000.0,
        }
        return COMMANDS["transfer"].path_template, params, None
    if command == "entity" and args:
        path = COMMANDS["entity"].path_template.replace("{address}", args[0])
        chain = args[1] if len(args) > 1 else "ethereum"
        return path, {"chain": chain}, None
    if command == "tx" and args:
        path = COMMANDS["tx"].path_template.replace("{hash}", args[0])
        chain = args[1] if len(args) > 1 else "ethereum"
        return path, {"chain": chain}, None
    if command == "dd" and args:
        mode = args[1] if len(args) > 1 and args[1] in {"one_page", "full"} else "one_page"
        return COMMANDS["dd"].path_template, {"asset": args[0].upper(), "mode": mode}, None
    if command == "status":
        return COMMANDS["status"].path_template, None, None
    if command == "alert":
        sub = (args[0] if args else "list").lower()
        if sub != "list":
            raise ValueError("Only 'alert list' is supported")
        return COMMANDS["alert"].path_template, {"limit": 20}, None
    if command == "portfolio":
        sub = (args[0] if args else "check").lower()
        if sub != "check":
            raise ValueError("Only 'portfolio check' is supported")
        asset = args[1] if len(args) > 1 else "BTC"
        return COMMANDS["portfolio"].path_template, {"asset": asset.upper()}, None
    raise ValueError(f"Unknown command or missing arguments: {command}")


def run_command(client: BlackdarkApiClient, command: str, args: list[str]) -> dict[str, Any]:
    path, params, body = _build_params(command, args)
    spec = COMMANDS.get(command)
    if spec is None:
        raise ValueError(f"Unknown command: {command}")
    if spec.method == "GET":
        return client.get(path, params=params)
    return client.post(path, json_body=body)


def command_names() -> list[str]:
    return sorted(COMMANDS.keys())
