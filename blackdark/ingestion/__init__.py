"""Data ingestion layer — primary external source connectors."""

from blackdark.ingestion.alternative_me_connector import (
    alternative_me_status,
    fetch_fear_greed_index,
    run_alternative_me_ingest,
)
from blackdark.ingestion.arkham_connector import (
    arkham_connector_status,
    fetch_entity_intelligence_input,
)
from blackdark.ingestion.coingecko_connector import (
    coingecko_connector_status,
    fetch_coingecko_markets,
    fetch_coingecko_price,
    run_coingecko_primary_ingest,
)
from blackdark.ingestion.debank_connector import (
    debank_connector_status,
    fetch_debank_total_balance,
)
from blackdark.ingestion.dexscreener_connector import (
    dexscreener_connector_status,
    fetch_dex_pairs,
)
from blackdark.ingestion.etherscan_connector import (
    etherscan_connector_status,
    fetch_eth_balance,
    fetch_whale_flow_signal,
)

__all__ = [
    "alternative_me_status",
    "arkham_connector_status",
    "coingecko_connector_status",
    "debank_connector_status",
    "dexscreener_connector_status",
    "etherscan_connector_status",
    "fetch_coingecko_markets",
    "fetch_coingecko_price",
    "fetch_debank_total_balance",
    "fetch_dex_pairs",
    "fetch_entity_intelligence_input",
    "fetch_eth_balance",
    "fetch_fear_greed_index",
    "fetch_whale_flow_signal",
    "run_alternative_me_ingest",
    "run_coingecko_primary_ingest",
]
