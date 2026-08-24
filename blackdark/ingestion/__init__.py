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
from blackdark.ingestion.exchange_flow_metric import compute_token_exchange_flows
from blackdark.ingestion.solana_rpc_connector import (
    fetch_solana_chain_health,
    solana_rpc_connector_status,
)
from blackdark.ingestion.theblock_connector import (
    fetch_theblock_research_context,
    theblock_connector_status,
)

__all__ = [
    "alternative_me_status",
    "arkham_connector_status",
    "coingecko_connector_status",
    "compute_token_exchange_flows",
    "fetch_coingecko_markets",
    "fetch_coingecko_price",
    "fetch_entity_intelligence_input",
    "fetch_fear_greed_index",
    "fetch_solana_chain_health",
    "fetch_theblock_research_context",
    "run_alternative_me_ingest",
    "run_coingecko_primary_ingest",
    "solana_rpc_connector_status",
    "theblock_connector_status",
]
