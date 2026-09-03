"""
Runs all three allocation methods on the Aegis asset universe, prints a
weights comparison table, and plots the efficient frontier with each
method's portfolio marked on it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from engine.data_loader import get_prices
from engine.returns import compute_returns
from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    efficient_frontier,
    risk_parity,
    kelly_portfolio,
    normalize_weights,
    portfolio_performance,
)


def main():
    prices = get_prices()
    returns = compute_returns(prices)
    returns = returns.dropna()  # drop any remaining gap days for this comparison

    mean_returns = annualized_mean_returns(returns)
    cov = returns.cov() * 252

    # Run each allocator
    markowitz_weights = markowitz_min_variance(mean_returns, cov)
    parity_weights = risk_parity(cov)
    kelly_weights = normalize_weights(kelly_portfolio(mean_returns, cov))

    # Build comparison table
    comparison = pd.DataFrame({
        "Markowitz (Min Var)": markowitz_weights,
        "Risk Parity": parity_weights,
        "Kelly (normalized)": kelly_weights,
    }).round(4)
    print("\n=== Weights Comparison ===")
    print(comparison)

    # Print performance of each
    print("\n=== Performance Comparison ===")
    for name, weights in [
        ("Markowitz", markowitz_weights),
        ("Risk Parity", parity_weights),
        ("Kelly", kelly_weights),
    ]:
        ret, vol = portfolio_performance(weights.values, mean_returns, cov)
        print(f"{name}: return={ret:.2%}, volatility={vol:.2%}")

    # Plot efficient frontier with each method marked
    frontier = efficient_frontier(mean_returns, cov, n_points=30)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(frontier["volatility"], frontier["return"], "b-", label="Efficient Frontier")

    for name, weights, marker, color in [
        ("Markowitz (Min Var)", markowitz_weights, "*", "red"),
        ("Risk Parity", parity_weights, "^", "green"),
        ("Kelly (normalized)", kelly_weights, "s", "purple"),
    ]:
        ret, vol = portfolio_performance(weights.values, mean_returns, cov)
        ax.scatter(vol, ret, marker=marker, s=150, color=color, label=name, zorder=5)

    ax.set_xlabel("Volatility (annualized)")
    ax.set_ylabel("Expected Return (annualized)")
    ax.set_title("Efficient Frontier with Allocation Methods")
    ax.legend()
    fig.tight_layout()

    out_path = "data/efficient_frontier.png"
    fig.savefig(out_path, dpi=150)
    print(f"\nSaved plot to {out_path}")


if __name__ == "__main__":
    main()