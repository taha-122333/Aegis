# Aegis — Methodology

This document explains the reasoning behind Aegis's design choices, the assumptions baked into its math, and its known limitations. It's meant to be readable on its own, without needing to read the code.

## The problem

Given a set of assets, two questions: how much should be allocated to each one, and how much could realistically be lost. Aegis answers both with three different allocation philosophies and a full risk-analysis suite, then validates all of it against real historical data.

## Why three allocation methods, not one

There's no single "correct" way to build a portfolio — different methods optimize for different things, and understanding *why* they disagree is more informative than picking a winner:

- **Markowitz (mean-variance)** minimizes volatility for a given return target. It's the textbook approach, and it produces the mathematically "safest" portfolio for a given return — but it can be highly concentrated (in this project's universe, it puts 100% of its weight in just two of seven assets), and it's sensitive to how expected returns are estimated.

- **Risk parity** sidesteps return estimation almost entirely and instead equalizes each asset's *contribution to risk*. It's more diversified by construction, at the cost of not explicitly optimizing for return at all.

- **Kelly criterion** targets long-run compound growth rather than smoothness. It's the most aggressive method here, and the project's most interesting result came from a real failure mode this method hit (see "Known limitations" below).

## Key assumptions

- **Returns are estimated from historical averages.** Every method here assumes the past mean return and covariance are reasonable estimates of the future. This is a standard simplification, not a Aegis-specific choice — it's also a well-known weakness of mean-variance-style investing in general (see below).

- **VaR/CVaR (parametric)** assumes returns are normally distributed. Real markets have "fatter tails" than a normal distribution predicts, extreme days happen more often than this method expects. Historical and Monte Carlo VaR/CVaR are included specifically to cross-check the parametric estimate against methods that don't share this assumption.

- **Monte Carlo simulation** draws random daily returns from a normal distribution parameterized by a portfolio's own historical mean/volatility. It captures a wider range of "what could happen" than the single historical path actually observed, but it inherits the same normality assumption as parametric VaR.

- **The backtest is walk-forward** — at each monthly rebalance, weights are computed using only a trailing window of past data, never data from the future relative to that point. This avoids look-ahead bias, a common way backtests overstate real-world performance.

- **Transaction costs are modeled simply**, as a fixed basis-point cost proportional to turnover. Real trading costs also include price impact, bid-ask spread variation over time, and liquidity constraints, this is a simplification, not a full market-microstructure model.

## Known limitations

- **Estimation risk.** All three methods are only as good as their return and covariance estimates, and those estimates are inherently noisy over any finite historical window. This is a fundamental, well-documented limitation of mean-variance-style portfolio theory in general, not a bug specific to this implementation.

- **Unconstrained Kelly is numerically unstable when assets are highly correlated.** This project's asset universe includes BTC-USD and ETH-USD, which are highly correlated (~0.78). Kelly's weights come from inverting the covariance matrix, and a near-singular matrix (which high correlation produces) makes that inversion highly sensitive to small changes in the input data. This was observed directly: in the walk-forward backtest (Sprint 4), raw Kelly re-estimated monthly on a rolling window produced catastrophically unstable weights (a -1055% simulated total return). It was also observed in the dashboard (Sprint 6): re-running raw Kelly with a few additional months of price data shifted its SPY short position from about -72% to -60%, meaningfully changing its behavior during a stress test. Both are the same underlying issue. 
**Fix applied:** a bounded/fractional Kelly (`kelly_portfolio_bounded`) clips weights to a defined range before renormalizing — the same practical approach real-world quants use rather than deploying raw Kelly directly.

- **The COVID stress test window is short (about 5 weeks)** and reflects one specific historical crisis. It's a useful sanity check, not a comprehensive risk assessment — a portfolio that performed well during COVID isn't guaranteed to perform well in a different kind of crisis (e.g. a slow-grinding bear market, a liquidity crisis, or a rate shock).

- **The equal-weight baseline was competitive.** In the Sprint 4 backtest, naive equal weighting (465% return) was close to Kelly's leading result (500%) and outperformed both Markowitz and Risk Parity on raw return.
This is a well-documented finding in real portfolio theory research (diversification is a genuinely hard benchmark to beat)

- **This is a research/educational tool.** It doesn't account for taxes, margin requirements, real-world liquidity constraints, or regulatory considerations, and nothing it produces is investment advice.

## What this project demonstrates

Beyond implementing the standard formulas, this project surfaced and diagnosed two real, non-obvious problems: (1) unconstrained Kelly's numerical instability under high asset correlation, caught via a backtest producing an impossible result, root-caused to matrix conditioning, and fixed with a standard practitioner technique; and (2) the general fragility
of any allocation method to its underlying data assumptions, made concrete by watching the same portfolio's hedge strength change measurably with a few added months of data. Both are the kind of things you only encounter by actually building and stress-testing a system, not by implementing the formulas in isolation.