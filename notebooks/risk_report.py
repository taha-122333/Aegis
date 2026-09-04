"""
Builds a one-page risk report for each Sprint 2 allocation method: VaR/CVaR
(historical, parametric, Monte Carlo), max drawdown, Sharpe/Sortino ratios,
a COVID-crash stress test, and a Monte Carlo fan chart of possible futures.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib.pyplot as plt

from engine.data_loader import get_prices
from engine.returns import compute_returns
from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    risk_parity,
    kelly_portfolio,
    normalize_weights,
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


def build_report(name, weights, returns, mean_returns, cov):
    port_ret = portfolio_returns(returns, weights)
    port_mean, port_vol = portfolio_performance(weights.values, mean_returns, cov)

    hist_var = historical_var(port_ret)
    hist_cvar = historical_cvar(port_ret)
    param_var = parametric_var(port_mean / 252, port_vol / np.sqrt(252))

    paths = simulate_portfolio_paths(port_mean, port_vol, n_days=252, n_simulations=10000)
    mc_var = monte_carlo_var(paths)
    mc_cvar = monte_carlo_cvar(paths)

    dd = max_drawdown(port_ret)
    sharpe = sharpe_ratio(port_ret)
    sortino = sortino_ratio(port_ret)

    stress = stress_test_period(returns, weights, "2020-02-19", "2020-03-23")

    print(f"\n{'='*50}")
    print(f"RISK REPORT: {name}")
    print(f"{'='*50}")
    print(f"Expected annual return: {port_mean:.2%}")
    print(f"Expected annual volatility: {port_vol:.2%}")
    print(f"Sharpe ratio: {sharpe:.2f}")
    print(f"Sortino ratio: {sortino:.2f}")
    print(f"Max historical drawdown: {dd:.2%}")
    print(f"\n-- Value at Risk (95% confidence, 1-day) --")
    print(f"Historical VaR: {hist_var:.2%}")
    print(f"Parametric VaR: {param_var:.2%}")
    print(f"Monte Carlo VaR (1-year horizon): {mc_var:.2%}")
    print(f"\n-- Conditional VaR / Expected Shortfall (95%) --")
    print(f"Historical CVaR: {hist_cvar:.2%}")
    print(f"Monte Carlo CVaR (1-year horizon): {mc_cvar:.2%}")
    print(f"\n-- Stress Test: COVID Crash ({stress['period']}) --")
    print(f"Cumulative return: {stress['cumulative_return']:.2%}")
    print(f"Worst single day: {stress['worst_single_day']:.2%}")
    print(f"Max drawdown during crash: {stress['max_drawdown']:.2%}")

    return paths


def plot_monte_carlo_fan(paths, name, out_path):
    fig, ax = plt.subplots(figsize=(9, 6))
    days = np.arange(paths.shape[1])

    sample_idx = np.random.choice(paths.shape[0], size=200, replace=False)
    for idx in sample_idx:
        ax.plot(days, paths[idx], color="steelblue", alpha=0.05)

    p5 = np.percentile(paths, 5, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p95 = np.percentile(paths, 95, axis=0)
    ax.plot(days, p50, color="black", linewidth=2, label="Median path")
    ax.plot(days, p5, color="red", linestyle="--", label="5th percentile")
    ax.plot(days, p95, color="green", linestyle="--", label="95th percentile")

    ax.set_xlabel("Trading days ahead")
    ax.set_ylabel("Portfolio value (starting at 1.0)")
    ax.set_title(f"Monte Carlo Simulation — {name} (1 year, 10,000 paths)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Saved Monte Carlo fan chart to {out_path}")


def main():
    prices = get_prices()
    returns = compute_returns(prices)
    returns_clean = returns.dropna()

    mean_returns = annualized_mean_returns(returns_clean)
    cov = returns_clean.cov() * 252

    markowitz_weights = markowitz_min_variance(mean_returns, cov)
    parity_weights = risk_parity(cov)
    kelly_weights = normalize_weights(kelly_portfolio(mean_returns, cov))

    portfolios = [
        ("Markowitz (Min Var)", markowitz_weights, "data/monte_carlo_markowitz.png"),
        ("Risk Parity", parity_weights, "data/monte_carlo_risk_parity.png"),
        ("Kelly (normalized)", kelly_weights, "data/monte_carlo_kelly.png"),
    ]

    for name, weights, plot_path in portfolios:
        paths = build_report(name, weights, returns_clean, mean_returns, cov)
        plot_monte_carlo_fan(paths, name, plot_path)


if __name__ == "__main__":
    main()