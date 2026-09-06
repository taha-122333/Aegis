# Aegis — Methodology

This document explains the reasoning behind Aegis's design choices, the assumptions baked into its math, and its known limitations. It's meant to be readable on its own, without needing to read the code.

## The problem

Given a set of assets, two questions: how much should be allocated to each one, and how much could realistically be lost. Aegis answers both with three different allocation philosophies and a full risk-analysis suite, then validates all of it against real historical data.

## Three allocation methods, not one

There's no single "correct" way to build a portfolio? different methods optimize for different things, and understanding each one of them is actually what a win is defined by : 

- **Markowitz (mean-variance)** minimizes volatility for a given return target. It produces the mathematically "safest" portfolio for a given return, but it can be highly concentrated, and it's sensitive to how expected returns are estimated.

- **Risk parity** forgets return estimation almost entirely and instead tries to equalize each asset's contribution to risk. It's more diversified by construction, at the cost of not being able to optimize returns based on demand.

- **Kelly criterion** targets long-run compound growth rather than smoothness. It's the most aggressive method here.

## Key assumptions

- **Returns are estimated from historical averages.** Every method here assumes the past mean return and covariance are reasonable estimates of the future. 

- **VaR/CVaR (parametric)** assumes returns are normally distributed. Real markets have "fatter tails" than a normal distribution predicts, extreme days happen more often than this method expects. Historical and Monte Carlo VaR/CVaR are included specifically to cross-check the parametric estimate against methods that don't share this assumption.

- **Monte Carlo simulation** draws random daily returns from a normal distribution parameterized by a portfolio's own historical mean/volatility. It captures a wider range of "what could happen" than the single historical path actually observed, but it inherits the same normality assumption as parametric VaR.

- **The backtest is walk-forward** — at each monthly rebalance, weights are computed using only a trailing window of past data, never data from the future relative to that point. This avoids look-ahead bias.

- **Transaction costs are modeled simply**, as a fixed basis-point cost proportional to turnover. Real trading costs also include price impact, bid-ask spread variation over time, and liquidity constraints, this is a simplification, not a full market-microstructure model.

## Known limitations

- **Estimation risk.** All three methods are only as good as their return and covariance estimates, and those estimates are inherently noisy over any finite historical window.

- **Unconstrained Kelly is numerically unstable when assets are highly correlated.** This project's asset universe includes BTC-USD and ETH-USD, which are highly correlated (~0.78). Kelly's weights come from inverting the covariance matrix, and a near-singular matrix (which high correlation produces) makes that inversion highly sensitive to small changes in the input data. This was observed directly: in the walk-forward backtest (Sprint 4), raw Kelly re-estimated monthly on a rolling window produced catastrophically unstable weights (a -1055% simulated total return). It was also observed in the dashboard (Sprint 6): re-running raw Kelly with a few additional months of price data shifted its SPY short position from about -72% to -60%, meaningfully changing its behavior during a stress test. Both are the same underlying issue. 
**Fix applied:** a bounded/fractional Kelly (`kelly_portfolio_bounded`) clips weights to a defined range before renormalizing.

- **The COVID stress test window is short (about 5 weeks)** and reflects one specific historical crisis. A portfolio that performed well during COVID isn't guaranteed to perform well in a different kind of crisis.

- **The equal-weight baseline was competitive.** In the Sprint 4 backtest, naive equal weighting (465% return) was close to Kelly's leading result (500%) and outperformed both Markowitz and Risk Parity on raw return.

- **This is a research/educational tool.** It doesn't account for taxes, margin requirements, real-world liquidity constraints, or regulatory considerations, and nothing it produces is investment advice.

## What this project demonstrates

This project diagnosed two real problems: 1 unconstrained Kelly's numerical instability under high asset correlation, caught via a backtest producing an impossible result, root-caused to matrix conditioning, and fixed with a standard practitioner technique.
And 2 the general fragility of any allocation method to its underlying data assumptions, made concrete by watching the same portfolio's hedge strength change measurably with a few added months of data. Both are the kind of things you only encounter by actually building and stress-testing a system, not by implementing the formulas in isolation.