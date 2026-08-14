# Performance / Load / Stress / Soak Report

**SHA:** `86c347afce91220e98c3eb2e727611417369bbd7`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.67 p95_ms=3.55 n=30.  
Local 2-worker HTTP pack (`http_load_local`): verdict=PASS p50_ms=15.26 p95_ms=319.68 n=80.  
Chrome public pages (`chrome_public_pages`): verdict=PASS.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
