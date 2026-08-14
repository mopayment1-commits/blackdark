# Data Integrity & Provenance Audit

**SHA:** `dad20dc7fbc5a56f1778c80b3692ae564583218b`  
**Canonical layer:** `canonical_data_layer.py` (LIVE fails closed without provenance)  
**Stale guard:** `stale_price_guard.py`  
**L2 remainder:** synthetic_mid labeled; full_mesh_l2_complete=false

Integrity cases covering missing/stale/conflict/partial coverage: **PASS**.

A decision that cannot be proved is withheld (Net-Edge reject, dimension veto → Do Not Touch, execution freeze).
