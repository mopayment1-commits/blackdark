# Data Integrity & Provenance Audit

**SHA:** `a5663e74f02a95fceabd27a151f805260a4507eb`  
**Canonical layer:** `canonical_data_layer.py` (LIVE fails closed without provenance)  
**Stale guard:** `stale_price_guard.py`  
**L2 remainder:** synthetic_mid labeled; full_mesh_l2_complete=false

Integrity cases covering missing/stale/conflict/partial coverage: **PASS**.

A decision that cannot be proved is withheld (Net-Edge reject, dimension veto → Do Not Touch, execution freeze).
