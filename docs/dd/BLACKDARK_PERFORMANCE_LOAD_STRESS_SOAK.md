# Performance / Load / Stress / Soak Report

**SHA:** `9204933e42da8891833b9f8205269a832a6bcfd9`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.61 p95_ms=3.37 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=15.99 p95_ms=404.33 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
