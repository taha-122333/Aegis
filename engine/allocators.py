"""
Portfolio allocation methods: mean-variance optimization (Markowitz),
risk parity, and the Kelly criterion. Given expected returns and a
covariance matrix, each function returns a set of portfolio weights
(one number per asset, saying what fraction of capital goes into it).
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def annualized_mean_returns(returns: pd.DataFrame) -> pd.Series:
    """
    Average daily return, scaled up to a yearly figure (x252 trading days).
    This is our estimate of each asset's expected return going forward,
    based purely on its own past history — a common simplification.
    """
    return returns.mean() * 252


def portfolio_performance(weights: np.ndarray, mean_returns: pd.Series, cov: pd.DataFrame):
    """
    Given a set of weights, returns the portfolio's expected annual return
    and annual volatility (standard deviation) — the two numbers every
    allocation method is trying to balance against each other.
    """
    port_return = np.dot(weights, mean_returns)
    port_vol = np.sqrt(weights @ cov.values @ weights)
    return port_return, port_vol


def _weights_sum_to_one(weights):
    return np.sum(weights) - 1


def markowitz_min_variance(mean_returns: pd.Series, cov: pd.DataFrame, target_return: float = None) -> pd.Series:
    """
    Finds the portfolio with the lowest possible volatility, optionally
    constrained to hit a specific target annual return. No target = the
    global minimum-variance portfolio. No short-selling (weights >= 0),
    fully invested (weights sum to 1).
    """
    n = len(mean_returns)
    init_guess = np.repeat(1 / n, n)
    bounds = tuple((0.0, 1.0) for _ in range(n))

    constraints = [{"type": "eq", "fun": _weights_sum_to_one}]
    if target_return is not None:
        constraints.append({
            "type": "eq",
            "fun": lambda w: np.dot(w, mean_returns) - target_return,
        })

    def objective(w):
        return w @ cov.values @ w  # portfolio variance

    result = minimize(objective, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
    return pd.Series(result.x, index=mean_returns.index)


def efficient_frontier(mean_returns: pd.Series, cov: pd.DataFrame, n_points: int = 30) -> pd.DataFrame:
    """
    Traces the efficient frontier: for a range of target returns spanning
    what's achievable, finds the minimum-variance portfolio at each one.
    Returns a table of (target_return, return, volatility, weights...) —
    this is what gets plotted as the classic "efficient frontier" curve.
    """
    min_ret = mean_returns.min()
    max_ret = mean_returns.max()
    targets = np.linspace(min_ret, max_ret, n_points)

    rows = []
    for target in targets:
        weights = markowitz_min_variance(mean_returns, cov, target_return=target)
        port_return, port_vol = portfolio_performance(weights.values, mean_returns, cov)
        row = {"target_return": target, "return": port_return, "volatility": port_vol}
        row.update(weights.to_dict())
        rows.append(row)

    return pd.DataFrame(rows)


def risk_parity(cov: pd.DataFrame) -> pd.Series:
    """
    Finds weights where every asset contributes an EQUAL SHARE of total
    portfolio risk — not an equal dollar amount, an equal risk contribution.
    A volatile asset like Bitcoin ends up with a smaller weight than gold,
    because it takes less of it to contribute the same amount of risk.
    Solved by minimizing the spread between each asset's risk contribution.
    """
    n = cov.shape[0]
    init_guess = np.repeat(1 / n, n)
    bounds = tuple((0.0001, 1.0) for _ in range(n))
    constraints = [{"type": "eq", "fun": _weights_sum_to_one}]

    def risk_contributions(w):
        port_vol = np.sqrt(w @ cov.values @ w)
        marginal_contrib = cov.values @ w
        return w * marginal_contrib / port_vol

    def objective(w):
        rc = risk_contributions(w)
        target = np.mean(rc)
        return np.sum((rc - target) ** 2)

    result = minimize(objective, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
    return pd.Series(result.x, index=cov.columns)


def kelly_single_asset(mean_return: float, variance: float, risk_free: float = 0.0) -> float:
    """
    Kelly criterion for one asset: the fraction of capital to bet that
    maximizes long-run compound growth rate. f* = (expected excess return)
    / variance. Can come out above 1 (implying leverage) or negative
    (implying a short position) — usually capped in practice.
    """
    return (mean_return - risk_free) / variance


def kelly_portfolio(mean_returns: pd.Series, cov: pd.DataFrame, risk_free: float = 0.0) -> pd.Series:
    """
    Portfolio version of Kelly: f = Sigma^-1 (mu - rf), where Sigma^-1 is
    the inverse of the covariance matrix. This finds the growth-optimal
    allocation across all assets simultaneously, accounting for how they
    move together (not just each asset in isolation).
    """
    excess_returns = mean_returns - risk_free
    inv_cov = np.linalg.inv(cov.values)
    raw_weights = inv_cov @ excess_returns.values
    return pd.Series(raw_weights, index=mean_returns.index)


def normalize_weights(weights: pd.Series) -> pd.Series:
    """
    Rescales weights so they sum to 1 (100% of capital) while keeping
    their relative proportions intact. Kelly's raw output doesn't sum to
    1 by default, so we normalize it to compare fairly against the other
    two methods on the same footing.
    """
    return weights / weights.sum()