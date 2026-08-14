# Performance / Load / Stress / Soak Report

**SHA:** `c3da0ce7a851a0edf3689db24a13a95e98204ad2`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.62 p95_ms=3.07 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=11.61 p95_ms=327.94 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
