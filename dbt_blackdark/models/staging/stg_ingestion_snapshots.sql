select
    export_id,
    snapshot_id,
    source_id,
    category,
    payload_json,
    fetched_at,
    status,
    exported_at,
    product
from {{ source('blackdark_lake', 'ingestion_snapshots') }}
