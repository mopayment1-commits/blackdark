"""Example: API usage — runnable in CI (#853)."""

from __future__ import annotations

from sdk.blackdark.client import BlackdarkClient


def main() -> None:
    client = BlackdarkClient(base_url="https://api.blackdark.io")
    # Documented public endpoints only — no hidden APIs
    print("SDK version: blackdark-sdk/1.0.0")
    print("Coverage honesty endpoint available via client.coverage_honesty()")


if __name__ == "__main__":
    main()
