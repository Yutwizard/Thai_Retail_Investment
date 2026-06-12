# Quantitative Multi-Sleeve Investment Programme — Thai Retail Edition

A research-grounded, hedge-fund-style personal portfolio implementable on **SET, TFEX and Thai fund platforms**, built per the [programme handbook](docs/Quant_MultiSleeve_Programme_Handbook.docx). Private working document — not investment, legal or tax advice.

**Current parameterisation: THB 600,000** (recommended floor) — full 3-market trend sleeve (S50 + Gold Online + USD/THB), strategic weights 50/25/20/5.

## Architecture

Four sleeves with low mutual correlation, under a portfolio-level risk overlay:

| Sleeve | Weight | Instruments | Role |
|--------|--------|-------------|------|
| A — Global + Thai equity beta | 50% | DRs/DRx, SET50 tracker, RMF/SSF/ThaiESG feeders | Long-run growth engine; tax-wrapped core |
| B — Trend following | 25% | TFEX: S50, Gold Online, USD/THB futures | Crisis diversifier; the "hedge fund" sleeve |
| C — Defensive carry / ballast | 20% | MMF + short-duration gov-bond fund | Yield; rebalancing dry powder; 2nd-line margin reserve |
| D — Cash buffer | 5% | Broker cash | 1st-line TFEX margin buffer |

Overlay: **10% portfolio vol target** (Moreira–Muir, trend sleeve scaled first, beta below m = 0.7) and a **−15% drawdown circuit breaker** (halve gross exposure; restore inside −7.5%). Mechanical and non-negotiable.

## Repository layout

```
config/parameters.yaml       Appendix A master parameter sheet — single source of truth.
                             null values = unmeasured [P0]/[P2] inputs; code fails loudly on them.
src/quant_programme/
  config.py                  Parameter sheet loader (fail-loud on unmeasured values)
  data/loaders.py            Ingestion adapter boundary (SeriesSource protocol + CSV/parquet drops)
  data/continuous.py         Roll trigger + panama back-adjustment + auditable roll log (Ch.5.2)
  data/validation.py         Automated validation suite, run on every refresh (Ch.5.3)
  signals/trend.py           12m TSMOM signal, 3m/6m ensemble, EWMA(λ=0.94) vol (Ch.6.1, B.1)
  sizing.py                  Constant-risk contract sizing + granularity rule (B.2, Ch.2.4)
  costs.py                   Cost engine: actual fees + tick slippage, rolls = round trips (Ch.6.2)
  backtest/engine.py         Phase 2 trend-sleeve backtest (monthly + vol band + signal flips)
  backtest/metrics.py        Sharpe vs THOR, max DD, hit rate, cost drag (B.5)
  portfolio/overlay.py       Vol-target multiplier + circuit breaker (Ch.2.2, B.3)
  portfolio/simulation.py    Phase 3 four-sleeve simulation (Ch.7)
  portfolio/margin.py        Peak-stress margin adequacy model (Ch.3.4, 7.4, B.4)
  reporting/daily_sheet.py   Phase 4+ daily cycle output (Ch.8.1)
  reporting/results_register.py  Config-hash run register for reproducibility (Ch.6.4)
tests/                       Unit tests required by §6.4 + roll/overlay/validation tests
docs/phase_gates.md          Stage-gate exit criteria, Phases 0–6
docs/checklists/             Appendix C operating checklists
docs/risk_register.md        Ch.11 RCSA register
data/raw/                    Drop zone for upstream exports (futures/<INST>.csv, benchmarks/<NAME>.csv)
```

## Data ingestion

No scraping code lives here. The existing Playwright TFEX scraper and BOT API
integration plug in either by implementing the `SeriesSource` protocol
(`src/quant_programme/data/loaders.py`) or by exporting files into `data/raw/`:

- `data/raw/futures/<INSTRUMENT>.csv|parquet` — long format, columns `date, expiry, settle, volume, open_interest` (all listed expiries)
- `data/raw/benchmarks/<NAME>.csv|parquet` — columns `date, value` (THOR, SET50_TRI, GLOBAL_TRI_THB, USDTHB_SPOT)

Continuous series are **rebuilt from raw on every run** — never appended.

## Setup

```bash
pip install -e ".[dev]"
pytest
```

## Where the programme stands

- [ ] **Phase 0** — accounts, fee capture, margin policy → fills the `null` [P0] values in `config/parameters.yaml`
- [ ] **Phase 1** — ≥ 10y validated roll-adjusted data via the loader boundary
- [ ] **Phase 2** — trend backtest: net Sharpe ≥ 0.4, crisis behaviour, plateau, cost drag ≤ 2%
- [ ] **Phase 3** — full simulation: Sharpe ≥ 0.6 net, max DD ≤ 18%, five stress scenarios, margin adequacy
- [ ] **Phase 4** — 4 weeks paper trading, zero-error taxonomy
- [ ] **Phase 5** — go-live at half size, quarter-long validation
- [ ] **Phase 6** — standing governance

See [docs/phase_gates.md](docs/phase_gates.md) for full exit criteria. Failure at a gate sends the work back, never forward.
