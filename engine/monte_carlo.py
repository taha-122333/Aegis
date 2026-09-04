"""
Monte Carlo simulation: instead of relying on one single historical path,
this simulates thousands of possible random future paths for a portfolio,
based on its historical mean return and volatility, to build a picture of
the full range of what could plausibly happen going forward.
"""

import numpy as np


def simulate_portfolio_paths(
    port_mean: float,
    port_vol: float,
    n_days: int = 252,
    n_simulations: int = 10000,
    initial_value: float = 1.0,
    seed: int = 42,
) -> np.ndarray:
    """
    Simulates n_simulations possible future paths for the portfolio over
    n_days, by drawing random daily returns from a normal distribution
    built from the portfolio's own historical annual mean and volatility.
    port_mean and port_vol should be ANNUAL figures — this function
    converts them to daily internally. Returns an array of shape
    (n_simulations, n_days + 1): each row is one possible future,
    starting at initial_value.
    """
    rng = np.random.default_rng(seed)
    daily_mean = port_mean / 252
    daily_vol = port_vol / np.sqrt(252)

    daily_returns = rng.normal(daily_mean, daily_vol, size=(n_simulations, n_days))
    paths = np.zeros((n_simulations, n_days + 1))
    paths[:, 0] = initial_value
    paths[:, 1:] = initial_value * np.cumprod(1 + daily_returns, axis=1)
    return paths


def monte_carlo_var(paths: np.ndarray, confidence: float = 0.95) -> float:
    """
    Monte Carlo VaR: looks at the FINAL value across all simulated paths
    and finds the loss level only exceeded by (1 - confidence) of them.
    Same idea as historical VaR, but built from simulated futures instead
    of the one actual past we happened to observe.
    """
    final_values = paths[:, -1]
    initial_value = paths[0, 0]
    final_returns = (final_values - initial_value) / initial_value
    return -np.percentile(final_returns, (1 - confidence) * 100)


def monte_carlo_cvar(paths: np.ndarray, confidence: float = 0.95) -> float:
    """
    Monte Carlo CVaR: average loss among just the worst simulated
    outcomes (beyond the VaR cutoff).
    """
    final_values = paths[:, -1]
    initial_value = paths[0, 0]
    final_returns = (final_values - initial_value) / initial_value
    threshold = np.percentile(final_returns, (1 - confidence) * 100)
    tail = final_returns[final_returns <= threshold]
    return -tail.mean()