# Phase 0 — Broker Selection Scorecard

One broker offering **both** SET cash and TFEX derivatives accounts (single-broker
simplifies funding and collateral). Score at least three candidates before choosing.

Selection criteria (handbook §4.1):

| Criterion | Weight | Broker 1: ____ | Broker 2: ____ | Broker 3: ____ |
|---|---|---|---|---|
| TFEX commission per contract (S50 / GO / USD/THB, per side, incl. exchange + clearing) — negotiable above modest volume? | High | | | |
| SET commission tier (incl. VAT) | High | | | |
| DR night-session access (19:00–03:00 for US/EU underlyings) | High | | | |
| Margin-collateral policy: cash-only or MMF units eligible? (§3.4 — get it **in writing**) | High | | | |
| API quality, or at minimum exportable daily statements | Medium | | | |
| Settrade DRx wallet support (only needed for the THB 300k variant) | Low | | | |
| Fund-mart access (RMF/SSF/ThaiESG + MMF + bond fund in one place) | Medium | | | |

**Decision:** ____________________  **Date:** ____________

Record the chosen broker in `config/parameters.yaml → phase0_register.broker`.
