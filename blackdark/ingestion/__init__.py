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

__all__ = [
    "alternative_me_status",
    "arkham_connector_status",
    "coingecko_connector_status",
    "fetch_coingecko_markets",
    "fetch_coingecko_price",
    "fetch_entity_intelligence_input",
    "fetch_fear_greed_index",
    "run_alternative_me_ingest",
    "run_coingecko_primary_ingest",
]
