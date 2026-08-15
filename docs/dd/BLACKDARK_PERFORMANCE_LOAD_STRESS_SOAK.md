# Performance / Load / Stress / Soak Report

**SHA:** `f7659e72abff1991e25e74eec92a2697e45bc317`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.62 p95_ms=3.16 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=13.11 p95_ms=396.86 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
