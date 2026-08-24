"""Tests — BLACKDARK CLI (#167)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from blackdark.cli.client import BlackdarkApiClient, CliApiError
from blackdark.cli.commands import _build_params, run_command
from blackdark.cli.errors import EXIT_AUTH, EXIT_NOT_FOUND, EXIT_OK, EXIT_RATE_LIMIT, EXIT_USAGE, exit_code_for_http
from blackdark.cli.main import main


def test_exit_code_mapping():
    assert exit_code_for_http(401) == EXIT_AUTH
    assert exit_code_for_http(403) == EXIT_AUTH
    assert exit_code_for_http(404) == EXIT_NOT_FOUND
    assert exit_code_for_http(429) == EXIT_RATE_LIMIT
    assert exit_code_for_http(422) == EXIT_USAGE


def test_build_params_price():
    path, params, body = _build_params("price", ["btc"])
    assert path.endswith("/aggregate")
    assert params == {"asset": "BTC"}
    assert body is None


def test_build_params_alert_list():
    path, params, body = _build_params("alert", ["list"])
    assert "/inbox" in path
    assert params == {"limit": 20}


def test_build_params_portfolio_check():
    path, params, body = _build_params("portfolio", ["check", "eth"])
    assert "portfolio-check" in path
    assert params == {"asset": "ETH"}


def test_run_command_mocked():
    client = MagicMock(spec=BlackdarkApiClient)
    client.get.return_value = {"ok": True, "weighted_price": 100}
    out = run_command(client, "price", ["BTC"])
    assert out["weighted_price"] == 100
    client.get.assert_called_once()


def test_cli_api_error_exit_code():
    err = CliApiError("denied", status=403, exit_code=EXIT_AUTH)
    assert err.exit_code == EXIT_AUTH


def test_main_help_exit_ok():
    assert main(["help"]) == EXIT_OK


def test_main_success_json(capsys):
    mock_client = MagicMock(spec=BlackdarkApiClient)
    mock_client.get.return_value = {"weighted_price": 50000, "asset": "BTC", "source_count": 5}
    with patch("blackdark.cli.main.BlackdarkApiClient", return_value=mock_client):
        code = main(["price", "BTC", "--json"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["weighted_price"] == 50000


def test_main_api_error_exit_auth(capsys):
    mock_client = MagicMock(spec=BlackdarkApiClient)
    mock_client.get.side_effect = CliApiError("forbidden", status=403, exit_code=EXIT_AUTH)
    with patch("blackdark.cli.main.BlackdarkApiClient", return_value=mock_client):
        code = main(["price", "BTC"])
    assert code == EXIT_AUTH
    err = capsys.readouterr().err
    assert "forbidden" in err.lower() or "403" in err


def test_main_usage_error():
    with pytest.raises(SystemExit):
        main(["not-a-command"])
