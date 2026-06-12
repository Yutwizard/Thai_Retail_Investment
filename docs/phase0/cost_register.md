# Phase 0 Deliverable — Cost Register

Every fee **measured, not assumed** (§4.1 tasks 5–6). These values are the inputs to
`config/parameters.yaml` (instrument `commission_per_side_thb`, `costs.set_commission_rate`)
and feed the Phase 2 cost model directly.

## TFEX fee schedule (per contract, per side)

| Instrument | Broker commission | Exchange fee | Clearing fee | **Total per side (THB)** | VAT incl.? |
|---|---|---|---|---|---|
| S50 Index Futures | | | | | |
| Gold Online Futures | | | | | |
| USD/THB Futures | | | | | |

## SET / fund fees

| Item | Value | Notes |
|---|---|---|
| SET commission rate (incl. VAT) | ____ % | tier: |
| DR issuer fee in conversion ratio (per shortlist name) | | see DR shortlist memo |
| RMF/SSF/ThaiESG feeder TERs | | per provider, see comparison below |
| MMF TER | | |
| Bond fund TER | | |

## Live round-trip test log (first real slippage observations)

One minimum-size round trip per instrument class. Record fill vs prevailing bid/offer **mid at order time**.

| Date | Instrument | Side/qty | Mid at order | Fill | Slippage (ticks) | Total fees (THB) | Reconciled vs statement |
|---|---|---|---|---|---|---|---|
| | S50 ×1 (open+close same day) | | | | | | ☐ |
| | Gold Online ×1 | | | | | | ☐ |
| | USD/THB ×1 | | | | | | ☐ |
| | DR (board lot / small order) | | | | | | ☐ |
| | Fund subscription (small) | | | | | | ☐ |

## Tax-wrapper provider comparison (≥ 3 providers)

| Provider | Global index feeder | TER | Switching fee | Master-fund tracking difference | Selected |
|---|---|---|---|---|---|
| | | | | | ☐ |
| | | | | | ☐ |
| | | | | | ☐ |
