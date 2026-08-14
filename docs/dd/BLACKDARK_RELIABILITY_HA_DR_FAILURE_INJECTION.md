# Reliability / HA / DR / Failure Injection Report

**SHA:** `dad20dc7fbc5a56f1778c80b3692ae564583218b`  
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

On-call Telegram configured: **False**

Cloud multi-AZ: **FAIL** (unpaid external). Local Postgres streaming HA is a different control and is not this report's cloud HA claim.

DR region loss: **FAIL** (evaluated missing — chaos dead-Postgres pack is not region loss). Backup restore: see drill `postgres_dump_restore` / `sqlite_restore`.
