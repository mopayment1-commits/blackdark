# Performance / Load / Stress / Soak Report

**SHA:** `a5663e74f02a95fceabd27a151f805260a4507eb`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.61 p95_ms=5.14 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=20.49 p95_ms=25.38 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
