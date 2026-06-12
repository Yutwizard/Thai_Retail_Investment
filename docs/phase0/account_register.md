# Phase 0 Deliverable — Account Register

Account numbers, platforms, funding rails, cut-off times (handbook §4.2).
Keep account numbers out of git if this repo ever leaves your control —
mask to last 4 digits.

| Account | Provider | Account no. (masked) | Platform | Funding rail | Cut-off times | Opened | Funded |
|---|---|---|---|---|---|---|---|
| SET cash | | | | | | ☐ | ☐ |
| TFEX derivatives | | | | | | ☐ | ☐ |
| Settrade DRx wallet (if 300k variant) | | | | | | ☐ | ☐ |
| Fund trading (broker fund-mart / AMC direct) | | | | | | ☐ | ☐ |
| RMF | | | — | | | ☐ | ☐ |
| SSF | | | — | | | ☐ | ☐ |
| ThaiESG | | | — | | | ☐ | ☐ |
| Money market fund (T+1) | | | — | | **redemption cut-off: ____** | ☐ | ☐ |
| Short-duration gov bond fund | | | — | | redemption cut-off: ____ | ☐ | ☐ |

> A 12:00 vs 15:30 MMF cut-off changes the margin-defence timeline by a day (§4.1).
> Record MMF/bond-fund choices in `config/parameters.yaml → phase0_register`.
