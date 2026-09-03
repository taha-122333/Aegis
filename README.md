# Aegis — Portfolio Construction & Risk Engine

Aegis is a portfolio construction and risk engine: given a set of assets or
strategies, it answers how much to allocate to each one and how much you
could realistically lose. It covers mean-variance optimization, risk parity,
the Kelly criterion, Monte Carlo simulation, and VaR/CVaR risk metrics.

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
- Sprint 3 — Risk Analytics: not started
- Sprint 4 — Historical Backtest: not started
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
  expected returns and covariance. Note: unconstrained portfolio Kelly can
  produce negative (short) weights on highly correlated assets — this is
  expected behavior, not a bug, and is a known reason practitioners often
  use fractional Kelly in practice.

## Tech stack

- Core engine: Python 3.14, numpy, pandas, scipy, matplotlib
- Data: yfinance, cached locally as Parquet (pyarrow)
- API layer (later): FastAPI
- Presentation (later, optional): Streamlit or a minimal Next.js page
- Tests: pytest

## Project structure

```
aegis/
├── engine/ # core logic: data loading, returns, allocators, risk
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
```

