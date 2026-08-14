# Reliability / HA / DR / Failure Injection Report

**SHA:** `963dd54221250081589b1155704afe5c84dbbad6`  
**3 AM definition:** production-bad conditions with no developer catching the process.

| Scenario | Verdict | Blocks bad decision | Fails safe |
|---|---|---|---|
| source_or_binance_down | PASS | True | True |
| websocket_disconnect | PASS | True | True |
| stale_or_contradictory_data | PASS | True | True |
| database_down | NOT_TESTED | True | True |
| redis_down | FAIL | True | True |
| slow_external_api | NOT_TESTED | True | True |
| user_spike | NOT_TESTED | False | True |
| ai_model_stop | NOT_TESTED | True | True |
| partial_fill_or_exec_fail | PASS | True | True |
| server_crash_restart | NOT_TESTED | True | True |

On-call Telegram configured: **False**

Cloud multi-AZ: **FAIL** (unpaid external). Local Postgres streaming HA is a different control and is not this report's cloud HA claim.

DR region loss: **NOT_TESTED**. Backup restore drill: **NOT_TESTED** in this cert function (helper exists in `ops_recovery.py`).
