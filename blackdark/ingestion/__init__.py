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
from blackdark.ingestion.binance_connector import (
    binance_connector_status,
    fetch_binance_futures_funding,
    fetch_binance_spot_ticker,
)
from blackdark.ingestion.coingecko_connector import (
    coingecko_connector_status,
    fetch_coingecko_markets,
    fetch_coingecko_price,
    run_coingecko_primary_ingest,
)
from blackdark.ingestion.exchange_flow_metric import compute_token_exchange_flows
from blackdark.ingestion.exchange_netflow_intelligence import compute_exchange_netflow
from blackdark.ingestion.futures_cvd_metric import compute_futures_cvd
from blackdark.ingestion.investing_com_connector import (
    fetch_investing_news_context,
    investing_com_connector_status,
)
from blackdark.ingestion.lending_markets_connector import (
    fetch_lending_markets,
    lending_markets_connector_status,
)
from blackdark.ingestion.order_flow_intelligence import compute_order_flow_intelligence
from blackdark.ingestion.polygon_io_connector import (
    fetch_polygon_macro_context,
    polygon_io_connector_status,
)
from blackdark.ingestion.polygonscan_connector import (
    fetch_polygon_onchain_health,
    polygonscan_connector_status,
)
from blackdark.ingestion.solana_rpc_connector import (
    fetch_solana_chain_health,
    solana_rpc_connector_status,
)
from blackdark.ingestion.theblock_connector import (
    fetch_theblock_research_context,
    theblock_connector_status,
)
from blackdark.ingestion.tronscan_connector import (
    fetch_tron_account,
    fetch_tron_transactions,
    tronscan_connector_status,
)

__all__ = [
    "alternative_me_status",
    "arkham_connector_status",
    "binance_connector_status",
    "coingecko_connector_status",
    "compute_exchange_netflow",
    "compute_token_exchange_flows",
    "compute_order_flow_intelligence",
    "compute_futures_cvd",
    "fetch_binance_futures_funding",
    "fetch_binance_spot_ticker",
    "fetch_coingecko_markets",
    "fetch_coingecko_price",
    "fetch_entity_intelligence_input",
    "fetch_fear_greed_index",
    "fetch_investing_news_context",
    "fetch_lending_markets",
    "fetch_polygon_macro_context",
    "fetch_polygon_onchain_health",
    "fetch_solana_chain_health",
    "fetch_theblock_research_context",
    "fetch_tron_account",
    "fetch_tron_transactions",
    "investing_com_connector_status",
    "lending_markets_connector_status",
    "polygon_io_connector_status",
    "polygonscan_connector_status",
    "run_alternative_me_ingest",
    "run_coingecko_primary_ingest",
    "solana_rpc_connector_status",
    "theblock_connector_status",
    "tronscan_connector_status",
]
