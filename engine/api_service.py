"""
Bridges the core engine (allocators, risk metrics, Monte Carlo) to the
API layer: takes raw ticker lists coming from HTTP requests and turns them
into the return/covariance data everything else expects.
"""

import numpy as np
import pandas as pd

from engine.data_loader import download_prices
from engine.returns import compute_returns, align_trading_days
from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    risk_parity,
    kelly_portfolio_bounded,
    portfolio_performance,
)
from engine.risk_metrics import (
    portfolio_returns,
    historical_var,
    historical_cvar,
    parametric_var,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    stress_test_period,
)
from engine.monte_carlo import simulate_portfolio_paths, monte_carlo_var, monte_carlo_cvar


class InsufficientDataError(Exception):
    """Raised when there isn't enough usable price history for the requested tickers."""


def fetch_returns(tickers: list[str]) -> pd.DataFrame:
    """
    Downloads fresh price data for the given tickers (NOT the cached
    default-universe file, since API requests can name any tickers) and
    converts it to daily returns, aligned onto a shared trading calendar.
    """
    prices = download_prices(tickers=tickers)
    prices = align_trading_days(prices)
    if prices.shape[0] < 30:
        raise InsufficientDataError(
            f"Only {prices.shape[0]} overlapping trading days found for {tickers} — "
            f"need at least 30 to compute meaningful statistics."
        )
    return compute_returns(prices)


def compute_weights(returns: pd.DataFrame, method: str, target_return: float = None) -> pd.Series:
    """
    Dispatches to the right allocator — same idea as backtest.py's
    compute_target_weights, but for a single one-off allocation rather
    than a walk-forward simulation.
    """
    mean_returns = annualized_mean_returns(returns)
    cov = returns.cov() * 252

    if method == "markowitz":
        return markowitz_min_variance(mean_returns, cov, target_return=target_return)
    elif method == "risk_parity":
        return risk_parity(cov)
    elif method == "kelly":
        return kelly_portfolio_bounded(mean_returns, cov)
    elif method == "equal_weight":
        n = len(mean_returns)
        return pd.Series(1 / n, index=mean_returns.index)
    else:
        raise ValueError(f"Unknown method: {method!r}")


def build_allocation_result(tickers: list[str], method: str, target_return: float = None) -> dict:
    """Full pipeline for the /allocate endpoint: fetch data, compute weights, compute expected performance."""
    returns = fetch_returns(tickers)
    weights = compute_weights(returns, method, target_return)
    mean_returns = annualized_mean_returns(returns)
    cov = returns.cov() * 252
    exp_return, exp_vol = portfolio_performance(weights.values, mean_returns, cov)

    return {
        "weights": weights.round(4).to_dict(),
        "expected_return": round(float(exp_return), 4),
        "expected_volatility": round(float(exp_vol), 4),
    }


def build_risk_report(tickers: list[str], method: str, confidence: float = 0.95) -> dict:
    """Full pipeline for the /risk-report endpoint: fetch data, compute weights, run every Sprint 3 risk metric."""
    returns = fetch_returns(tickers)
    weights = compute_weights(returns, method)
    mean_returns = annualized_mean_returns(returns)
    cov = returns.cov() * 252
    exp_return, exp_vol = portfolio_performance(weights.values, mean_returns, cov)

    port_ret = portfolio_returns(returns, weights)

    hist_var = historical_var(port_ret, confidence)
    hist_cvar = historical_cvar(port_ret, confidence)
    param_var = parametric_var(exp_return / 252, exp_vol / np.sqrt(252), confidence)

    paths = simulate_portfolio_paths(exp_return, exp_vol, n_days=252, n_simulations=5000)
    mc_var = monte_carlo_var(paths, confidence)
    mc_cvar = monte_carlo_cvar(paths, confidence)

    dd = max_drawdown(port_ret)
    sharpe = sharpe_ratio(port_ret)
    sortino = sortino_ratio(port_ret)

    stress = None
    try:
        stress = stress_test_period(returns, weights, "2020-02-19", "2020-03-23")
    except Exception:
        pass  # requested tickers may not have data reaching back to 2020

    return {
        "weights": weights.round(4).to_dict(),
        "expected_return": round(float(exp_return), 4),
        "expected_volatility": round(float(exp_vol), 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "sortino_ratio": round(float(sortino), 4),
        "max_drawdown": round(float(dd), 4),
        "value_at_risk": {
            "historical": round(float(hist_var), 4),
            "parametric": round(float(param_var), 4),
            "monte_carlo_1y": round(float(mc_var), 4),
        },
        "conditional_value_at_risk": {
            "historical": round(float(hist_cvar), 4),
            "monte_carlo_1y": round(float(mc_cvar), 4),
        },
        "covid_stress_test": stress,
    }