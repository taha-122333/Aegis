"""
Risk metrics: measures of how bad things could realistically get for a
portfolio. Covers Value at Risk (VaR), Conditional VaR (CVaR), max
drawdown, Sharpe ratio, Sortino ratio, and a historical stress test.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm


def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """
    Combines individual asset returns into a single daily return series
    for the whole portfolio, using the given weights.
    """
    aligned_weights = weights.reindex(returns.columns).fillna(0)
    return returns @ aligned_weights


def historical_var(port_returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical VaR: looks at ACTUAL past daily returns and finds the loss
    level that was only exceeded (1 - confidence) of the time. E.g. 95%
    VaR = the loss so bad it only happened (or was worse) on 5% of days.
    Returned as a positive number representing the loss (e.g. 0.03 = 3%).
    """
    return -np.percentile(port_returns, (1 - confidence) * 100)


def historical_cvar(port_returns: pd.Series, confidence: float = 0.95) -> float:
    """
    CVaR (Conditional VaR / Expected Shortfall): the AVERAGE loss on just
    the worst days — the ones beyond the VaR cutoff. Answers "given that
    we're in that bad 5%, how bad is it on average?" Always >= VaR.
    """
    var_threshold = np.percentile(port_returns, (1 - confidence) * 100)
    tail_losses = port_returns[port_returns <= var_threshold]
    return -tail_losses.mean()


def parametric_var(daily_mean: float, daily_vol: float, confidence: float = 0.95) -> float:
    """
    Parametric VaR (aka variance-covariance method): instead of using
    actual historical data, ASSUMES returns follow a normal distribution
    (bell curve) and computes VaR directly from the math of that curve.
    Faster than historical VaR, but relies on an assumption real markets
    often violate — actual markets have "fatter tails" than a normal
    distribution predicts, meaning extreme days happen more often than
    this method expects. Pass daily_mean and daily_vol (same time period).
    """
    z_score = norm.ppf(1 - confidence)
    return -(daily_mean + z_score * daily_vol)


def max_drawdown(port_returns: pd.Series) -> float:
    """
    Max drawdown: the largest peak-to-trough decline in portfolio value
    over the period. Answers "what's the worst loss I'd have felt if I
    bought at the top and watched it fall before recovering?" Returned
    as a positive fraction (e.g. 0.30 = a 30% drawdown).
    """
    cumulative = (1 + port_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return -drawdown.min()


def sharpe_ratio(port_returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Sharpe ratio: return earned per unit of TOTAL volatility. Higher is
    better. Annualized here so it's comparable across different assets
    or time periods.
    """
    excess_returns = port_returns - risk_free / periods_per_year
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)


def sortino_ratio(port_returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Sortino ratio: like Sharpe, but only penalizes DOWNSIDE volatility
    (bad days) — good days aren't treated as "risk" since investors don't
    mind volatility that comes from gains. Considered more realistic by
    many practitioners.
    """
    excess_returns = port_returns - risk_free / periods_per_year
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    return (excess_returns.mean() / downside_std) * np.sqrt(periods_per_year)


def stress_test_period(returns: pd.DataFrame, weights: pd.Series, start: str, end: str) -> dict:
    """
    Stress test: applies the CURRENT portfolio weights to actual
    historical returns during a known crisis window, to see how that
    exact portfolio would have performed if it existed back then. Uses
    real historical data, not a simulation — grounded in what actually
    happened, not a statistical guess.
    """
    window = returns.loc[start:end]
    port_ret = portfolio_returns(window, weights)
    cumulative_return = (1 + port_ret).prod() - 1
    worst_day = port_ret.min()
    dd = max_drawdown(port_ret)
    return {
        "period": f"{start} to {end}",
        "cumulative_return": cumulative_return,
        "worst_single_day": worst_day,
        "max_drawdown": dd,
    }