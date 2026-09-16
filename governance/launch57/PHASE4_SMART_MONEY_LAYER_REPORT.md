# Phase 4 Smart Money + Instant Layer

BUILD_ORDER: 20→16→17→13→14→15→18→19→53→54→55→56→57
COMMIT: bd9698cdbaaca381ea7e4c4661b1cc815836f4fa
STATUS: PENDING_VERIFICATION (builder max — no PASS_ENGINEERING from builder)

## Handler modules
- launch57.smart_money_batch1 (items 20,16,17,13,14)
- launch57.smart_money_batch2 (items 15,18,19,53,54)
- launch57.smart_money_batch3 (items 55,56,57)

## Legacy bypass debt (documented, not fixed)
When LAUNCH57_SMART_MONEY_BATCH*_CAP_IDS emptied → batch01/batch02/batch10/batch12_dedicated generic delegate.

## CAP-0916 extension path
cap646/runtime.py → cap978/verify.py → launch57.smart_money_batch3
