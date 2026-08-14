# Performance / Load / Stress / Soak Report

**SHA:** `760a5b4336ab69ed3fd8752a68d9a4e770d9bece`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.44 p95_ms=2.96 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=19.25 p95_ms=83.09 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
