# Programme Risk Register (Ch.11)

RCSA-style register. Review at the annual cycle and after any exception.

| # | Risk | Likelihood | Impact | Controls |
|---|------|------------|--------|----------|
| 1 | Roll-methodology error fabricates backtest P&L | Medium | High | Roll log audit; roll-jump validation check; execution-timing robustness test (§6.3) |
| 2 | Cost drag exceeds model in live trading | Medium | Medium | Half-size quarter with 25% tolerance gate; per-trade slippage log; instrument drop rule |
| 3 | Margin call in stress forces liquidation of beta sleeve | Low | High | Peak-stress margin model (§7.4); cash + T+1 MMF two-line defence; 15/10 split fallback |
| 4 | USD/THB futures liquidity deteriorates | Medium | Low | Watch-list status; morning-session limit orders; pre-approved 2-market fallback |
| 5 | DR iNAV deviation / issuer fee erosion | Medium | Low | Night-session execution rule; ADV screen; annual shortlist refresh |
| 6 | Behavioural override after drawdown | Medium | High | Pre-committed change policy (§10.3); mechanical circuit breaker; written exit-criteria culture |
| 7 | Whipsaw regime persists multi-year | Medium | Medium | Sleeve sized to 25%; vol targeting caps damage; statistical-failure clause defines the exit |
| 8 | Single-broker operational failure | Low | Medium | Exportable statements; continuity sheet; positions closable by phone |
| 9 | Tax rule changes (wrappers, SET exemption, remittance regime) | Medium | Medium | Annual review item; domestic-stack design minimises exposure; monitor enacted (not proposed) changes only |
| 10 | Data pipeline silent failure | Medium | Medium | Validation suite gating signal runs; zero-tolerance Phase 4 error class; rebuild-from-raw policy |
