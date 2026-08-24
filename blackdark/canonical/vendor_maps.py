"""Vendor-specific symbol maps — single source for external ID resolution."""

from __future__ import annotations

COINGECKO_IDS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "LTC": "litecoin",
    "TRX": "tron",
    "ATOM": "cosmos",
    "UNI": "uniswap",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SUI": "sui",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "AAVE": "aave",
    "MKR": "maker",
    "CRV": "curve-dao-token",
    "INJ": "injective-protocol",
    "SEI": "sei-network",
    "TIA": "celestia",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "USDC": "usd-coin",
    "USDT": "tether",
    "WBTC": "wrapped-bitcoin",
}

COINGECKO_REVERSE: dict[str, str] = {v: k for k, v in COINGECKO_IDS.items()}

KRAKEN_PAIRS: dict[str, str] = {
    "BTC": "XBTUSD",
    "DOGE": "XDGUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
    "ADA": "ADAUSD",
    "DOT": "DOTUSD",
    "LINK": "LINKUSD",
    "LTC": "LTCUSD",
    "AVAX": "AVAXUSD",
    "ATOM": "ATOMUSD",
    "UNI": "UNIUSD",
    "NEAR": "NEARUSD",
    "APT": "APTUSD",
    "ARB": "ARBUSD",
}

KRAKEN_BASE_REVERSE: dict[str, str] = {
    "XBT": "BTC",
    "XDG": "DOGE",
}

BINANCE_QUOTE_SUFFIX = "USDT"
