# Reliability / HA / DR / Failure Injection Report

**SHA:** `9204933e42da8891833b9f8205269a832a6bcfd9`  
**3 AM definition:** production-bad conditions with no developer catching the process.

| Scenario | Verdict | Blocks bad decision | Fails safe |
|---|---|---|---|
| source_or_binance_down | PASS | True | True |
| websocket_disconnect | PASS | True | True |
| stale_or_contradictory_data | PASS | True | True |
| database_down | PASS | True | True |
| redis_down | PASS | True | True |
| slow_external_api | PASS | True | True |
| user_spike | PASS | False | True |
| ai_model_stop | PASS | True | True |
| partial_fill_or_exec_fail | PASS | True | True |
| server_crash_restart | PASS | True | True |

On-call Telegram configured: **True**  
On-call live drill: see `drills.telegram_oncall_live` (PASS requires telegram ok + message_id; secrets never recorded).

Cloud multi-AZ: **FAIL** (unpaid external). Local Postgres streaming HA is a different control and is not this report's cloud HA claim.

DR region/AZ loss: **FAIL** (D20 / EXT_CLOUD_HA). Local probe-DB DROP + pg_restore: see drill `postgres_dump_restore` (D22). Backup restore: `sqlite_restore` / `postgres_dump_restore`.
