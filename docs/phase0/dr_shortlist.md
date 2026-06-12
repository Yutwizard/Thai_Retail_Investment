# Phase 0 Deliverable — DR Shortlist Memo

Screen the DR universe (§4.1 task 7). Output: **4–6 names with one designated primary
per exposure** (one US/global index DR as core; optionally one Asia satellite).

Screening criteria:
- ADV > THB 5–10m
- Underlying matches target beta
- Historical iNAV deviation tight and mean-reverting
- Issuer fee in the conversion ratio documented

| DR symbol | Underlying | Issuer | ADV (THB m) | iNAV deviation behaviour | Issuer fee (conversion ratio) | Night session? | Role | Primary? |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | US/global core | ☐ |
| | | | | | | | US/global backup | ☐ |
| | | | | | | | Asia satellite | ☐ |
| | | | | | | | | ☐ |
| | | | | | | | | ☐ |
| | | | | | | | | ☐ |

Operating rules reminder (§3.2): buy only while the underlying market is open
(night session for US/EU); limit orders anchored to issuer iNAV; consolidate DRx
accumulation into the standard DR line as positions grow.

Record designated primaries in `config/parameters.yaml → phase0_register.dr_shortlist`.
