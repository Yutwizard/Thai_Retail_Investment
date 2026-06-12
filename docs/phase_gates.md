# Stage-Gate Exit Criteria

> Failure at a gate sends the work back, never forward. Do not advance until **all** criteria for the phase are met. (Handbook Ch.4–9)

## Phase 0 — Accounts, Wrappers and Infrastructure (Week 1)

- [ ] All accounts open and funded with at least the test amounts (SET cash, TFEX, DRx wallet if applicable, fund access).
- [ ] One successful round trip executed and reconciled in each instrument class (1× S50, 1× GO, 1× USD/THB, 1 DR order, 1 fund subscription).
- [ ] Cost-per-round-trip documented per contract/product including observed test slippage → `config/parameters.yaml`.
- [ ] Broker margin-collateral policy confirmed **in writing**; cash buffer sized per handbook §3.4 (20/5 or 15/10 split).
- [ ] DR shortlist of 4–6 names completed with designated primaries (ADV > THB 5m, tight iNAV, documented issuer fee).
- [ ] RMF/SSF/ThaiESG providers selected; first contributions scheduled — the tax sleeve does not wait for quant validation.

## Phase 1 — Data Layer (Weeks 1–2)

- [ ] ≥ 10 years of validated back-adjusted daily series for each Sleeve B instrument.
- [ ] Roll log saved and version-controlled.
- [ ] Validation suite passes with zero unexplained flags.
- [ ] Benchmark series (THOR, SET50 TRI, global TRI, USD/THB spot) loaded and reconciled.

## Phase 2 — Trend Sleeve Backtest (Weeks 2–4)

- [ ] Combined sleeve net Sharpe ≥ 0.4 (vs THOR) over the full sample in the selected variant.
- [ ] Crisis-window test PASSED (flat-to-positive in majority of equity-crisis windows). *A high Sharpe with failed crisis behaviour is a FAIL.*
- [ ] Sensitivity grid (lookback {6m, 9m, 12m} × vol window {40d, 60d, 90d} × rebalance {monthly, monthly+band}) shows a **plateau, not a peak**; selected cell documented.
- [ ] Cost drag ≤ 2% p.a. of sleeve capital at the intended capital level.
- [ ] Granularity test confirms instrument set for the actual capital level (2- or 3-market sleeve).
- [ ] Execution-timing robustness check passed (next-day-open run degrades only marginally → no look-ahead bias).

If cost drag exceeds 2%, responses in order: lengthen lookback → widen the rebalance band → drop the weakest instrument. **Never add complexity.**

## Phase 3 — Full Portfolio Simulation (Weeks 4–5)

- [ ] Simulated full-period Sharpe ≥ 0.6 net; max drawdown ≤ 18%.
- [ ] All five stress scenarios PASS (1997 THB crisis, 2008 crash, COVID gap crash, 2022 rate shock, whipsaw year), including margin adequacy with **no forced Sleeve A liquidation**.
- [ ] Circuit-breaker and vol-targeting logs reviewed; trigger behaviour matches specification exactly.
- [ ] Final strategic weights and the cash/ballast split (20/5 or 15/10) locked into `config/parameters.yaml`.

## Phase 4 — Paper Trading (Weeks 5–9, minimum 4 weeks)

- [ ] Four consecutive weeks with **zero** signal errors, **zero** missed actions, **zero** uncaught data faults.
- [ ] At least one roll per instrument executed cleanly in simulation.
- [ ] Observed slippage consistent with the Phase 2 cost model (within 1.5 ticks).
- [ ] Daily Sheet and monthly pack generation fully automated.

Error tolerances (4-week window): signal error 0 · missed action 0 · data fault 0 · slippage breach ≤ 2 (both explained) · process deviation ≤ 1 (with checklist fix deployed).

## Phase 5 — Go-Live at Half Size (Weeks 9–16)

Funding order: Sleeves C+D in full → Sleeve A in full → Sleeve B at **50% of target risk**.

- [ ] One full calendar quarter at half size with all five validation metrics on target:
  realised cost drag within 25% of model · trend-sleeve P&L correlation > 0.95 vs paper twin · zero operational breaks · margin utilisation never > 60% of buffer · DR fills within the assumed iNAV band.
- [ ] Realised costs reconciled into the cost register; Phase 2 assumptions updated if materially different.
- [ ] Scale-up executed in two weekly steps with no operational breaks.

Two consecutive missed quarters send the trend sleeve back to Phase 4.

## Phase 6 — Standing Governance (Ongoing)

Pre-committed change policy — the system may change **only** under:

1. **Structural market change** (contract spec change, DR delisting without substitute, fund closure, tax-regime change).
2. **Statistical failure** — rolling 3-year live performance below the 5th percentile of the Phase 3 simulated distribution.
3. **Annual plateau check failure** — the parameter region is no longer on a plateau in the updated grid.

A losing month, quarter, or year within the simulated distribution is explicitly **not** a reason to change anything. Document every proposed change, sleep on it for two weeks, re-test through Phases 2–3 before deployment.
