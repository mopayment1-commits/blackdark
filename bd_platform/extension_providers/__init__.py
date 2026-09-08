"""Extension provider contracts for Batch13 external-dependent capabilities."""

from bd_platform.extension_providers.bi_connectors import execute_local_contract as bi_connectors_contract
from bd_platform.extension_providers.datashare import execute_local_contract as datashare_contract
from bd_platform.extension_providers.dbt_connector import execute_local_contract as dbt_connector_contract
from bd_platform.extension_providers.real_time_feed import execute_local_contract as real_time_feed_contract

EXTENSION_PROVIDER_CONTRACTS = {
    647: real_time_feed_contract,
    648: datashare_contract,
    649: dbt_connector_contract,
    650: bi_connectors_contract,
}
