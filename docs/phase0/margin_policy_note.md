# Phase 0 Deliverable — Margin Policy Note (Critical Item, §3.4)

## Broker collateral policy

Obtain the broker's **written** answer:

- MMF units eligible as TFEX margin collateral? **YES / NO** (attach correspondence)
- If cash-only: pre-authorise same-day MMF redemption instructions (T+1 arrival)
  as the documented second line of margin defence. ☐ done

Record in `config/parameters.yaml → margin_model.broker_collateral_policy`
(`cash_only` or `funds_eligible`).

## Current TFEX margin levels (as of ____ — TFEX revises with volatility)

| Instrument | Initial margin / contract | Maintenance margin / contract |
|---|---|---|
| S50 Index Futures | | |
| Gold Online Futures | | |
| USD/THB Futures | | |

Record in `config/parameters.yaml → instruments.*.initial_margin_thb / maintenance_margin_thb`.

## Cash buffer sizing

Size the 5% buffer against **peak stressed** initial margin: TFEX raises IM by 50%
mid-crisis simultaneously with maximum sleeve position count, plus two days of
adverse variation margin at 3× daily vol.

Once IM values are recorded, run:

```bash
python scripts/phase0_status.py --buffer --contracts S50=2 GO=1 USDTHB=3 --daily-vol-thb 4000
```

Decision rule: if the computed buffer exceeds 5% of capital (THB 30,000 at 600k),
shift the ballast split from 20/5 to **15/10** rather than risk forced liquidation
of the beta sleeve. Update `strategic_weights` in the parameter sheet accordingly.

**Computed peak requirement:** THB ________  **Split decision:** 20/5 ☐  15/10 ☐
