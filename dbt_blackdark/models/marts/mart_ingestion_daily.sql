select
    category,
    date(exported_at) as export_day,
    count(*) as snapshot_count
from {{ ref('stg_ingestion_snapshots') }}
group by 1, 2
