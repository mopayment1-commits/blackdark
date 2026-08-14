# Performance / Load / Stress / Soak Report

**SHA:** `99e4db09eff8ec642d047aa72c231b6c6cf36bc6`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.56 p95_ms=2.95 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=16.21 p95_ms=19.97 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
