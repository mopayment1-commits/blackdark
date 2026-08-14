# Performance / Load / Stress / Soak Report

**SHA:** `dad20dc7fbc5a56f1778c80b3692ae564583218b`  
**D18 Performance:** FAIL  
**D19 Load/Stress/Spike:** FAIL  
**D39 Launch capacity:** FAIL

Local ASGI pack (`asgi_latency`): verdict=PASS p50_ms=2.48 p95_ms=3.0 n=30.

This local TestClient pack is **not** a production SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local pack PASSes.
