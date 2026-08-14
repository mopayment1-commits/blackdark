# Data Integrity & Provenance Audit

**SHA:** `f7659e72abff1991e25e74eec92a2697e45bc317`  
**Canonical layer:** `canonical_data_layer.py` (LIVE fails closed without provenance)  
**Stale guard:** `stale_price_guard.py`  
**L2 remainder:** synthetic_mid labeled; full_mesh_l2_complete=false

Integrity cases covering missing/stale/conflict/partial coverage: **PASS**.

A decision that cannot be proved is withheld (Net-Edge reject, dimension veto → Do Not Touch, execution freeze).
