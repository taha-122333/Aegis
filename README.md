# Aegis — Portfolio Construction & Risk Engine

Aegis is a portfolio construction and risk engine: given a set of assets or
strategies, it answers how much to allocate to each one and how much you
could realistically lose. It covers mean-variance optimization, risk parity,
the Kelly criterion, Monte Carlo simulation, VaR/CVaR risk metrics, and a
walk-forward historical backtest.

Aegis is the second project in a quant-finance portfolio, alongside
[Probatio](https://github.com/xReFaLL/Probatio), a strategy backtesting
platform. Aegis is fully standalone — it does its own data ingestion and
does not require Probatio to run. It reuses the same free data sources
(currently Yahoo Finance via `yfinance`) and a similar
Parquet-based storage pattern for consistency across the two projects, but
keeps its own independent copy of data.

**Disclaimer:** This is a research/educational tool. Nothing here is
investment advice.

## Status

- Sprint 0 — Setup & Foundations: done
- Sprint 1 — Data & Returns Module: done
- Sprint 2 — Core Allocators: done
- Sprint 3 — Risk Analytics: done
- Sprint 4 — Historical Backtest: done
- Sprint 5 — API Layer: not started
- Sprint 6 — Presentation Layer (stretch): not started
- Sprint 7 — Polish & Documentation: not started

## Asset universe (Sprint 1)

AAPL, MSFT, NVDA (large-cap stocks), SPY (S&P 500 ETF), GLD (gold),
BTC-USD, ETH-USD (crypto). Configurable in `engine/config.py`.

## Allocation methods (Sprint 2)

- **Markowitz (mean-variance):** finds the minimum-variance portfolio for a
  given target return, and traces the full efficient frontier.
- **Risk parity:** allocates so each asset contributes an equal share of
  total portfolio risk, rather than an equal dollar amount.
- **Kelly criterion:** solves for the growth-optimal allocation given
  expected returns and covariance, via covariance matrix inversion. A
  **bounded/fractional version** (`kelly_portfolio_bounded`) clips weights
  to a sane range before renormalizing — see Sprint 4 notes below for why
  this matters in practice, not just in theory.

## Risk analytics (Sprint 3)

For each allocation method, `notebooks/risk_report.py` computes VaR
(historical, parametric, Monte Carlo), CVaR/Expected Shortfall, max
drawdown, Sharpe ratio, Sortino ratio, a COVID-crash stress test
(Feb 19 – Mar 23, 2020), and a 10,000-path Monte Carlo simulation with a
fan chart of possible 1-year futures.

Notable finding: during the COVID stress test, the Kelly portfolio was the
only one that stayed profitable (+0.36%), because its short position in
SPY acted as a hedge against the broad market selloff.

## Historical backtest (Sprint 4)

`notebooks/backtest_comparison.py` runs a **walk-forward** backtest (no
look-ahead bias — weights at each rebalance are computed only from a
trailing lookback window, never touching future data) with monthly
rebalancing and realistic transaction costs, comparing Markowitz vs. Risk
Parity vs. Kelly vs. a naive Equal Weight baseline.

**Key finding:** unconstrained (raw) Kelly, when re-estimated on a rolling
window, produced catastrophic, unstable weights (-1055% total return) due
to matrix inversion becoming unstable on a near-singular covariance matrix
(BTC and ETH are highly correlated, ~0.78). This is a known real-world
failure mode of portfolio Kelly, not a coding bug — fixed with a bounded/
fractional Kelly that clips extreme weights before renormalizing, the same
approach real practitioners use. After the fix, results were sane: Kelly
led on total return (500%) but with a lower Sharpe than Markowitz/Risk
Parity, and the naive Equal Weight baseline proved a genuinely hard
benchmark to beat (465% return, competitive Sharpe) — consistent with
real-world diversification research.

## Tech stack

- Core engine: Python 3.14, numpy, pandas, scipy, matplotlib
- Data: yfinance, cached locally as Parquet (pyarrow)
- API layer (later): FastAPI
- Presentation (later, optional): Streamlit or a minimal Next.js page
- Tests: pytest

## Project structure

```
aegis/
├── engine/ # core logic: data loading, returns, allocators, risk, backtest
├── data/ # cached price data + generated plots (gitignored)
├── tests/ # pytest unit tests
└── notebooks/ # exploratory/analysis scripts
```

## Running it

```bash
pip install -r requirements.txt
python -m pytest
python -m engine.data_loader
python notebooks/explore_returns.py
python notebooks/compare_allocators.py
python notebooks/risk_report.py
python notebooks/backtest_comparison.py
```