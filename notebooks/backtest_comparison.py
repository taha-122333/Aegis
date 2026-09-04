"""
Runs the full walk-forward backtest for all four strategies (Markowitz,
Risk Parity, Kelly, Equal Weight), plots their equity curves together,
and prints a final comparison table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd

from engine.data_loader import get_prices
from engine.backtest import run_backtest
from engine.risk_metrics import sharpe_ratio, sortino_ratio, max_drawdown


def main():
    prices = get_prices()

    methods = ["markowitz", "risk_parity", "kelly", "equal_weight"]
    labels = {
        "markowitz": "Markowitz (Min Var)",
        "risk_parity": "Risk Parity",
        "kelly": "Kelly",
        "equal_weight": "Equal Weight (baseline)",
    }

    results = {}
    for method in methods:
        print(f"Running backtest: {labels[method]}...")
        results[method] = run_backtest(prices, method=method)

    # Plot equity curves together
    fig, ax = plt.subplots(figsize=(10, 6))
    for method in methods:
        ax.plot(results[method]["equity_curve"], label=labels[method])
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value (starting at 1.0)")
    ax.set_title("Backtest: Allocation Strategy Comparison")
    ax.legend()
    fig.tight_layout()
    out_path = "data/backtest_comparison.png"
    fig.savefig(out_path, dpi=150)
    print(f"\nSaved equity curve chart to {out_path}")

    # Print comparison table
    print("\n=== Backtest Comparison ===")
    rows = []
    for method in methods:
        equity = results[method]["equity_curve"]
        daily_returns = equity.pct_change().dropna()
        total_cost = results[method]["turnover_log"]["cost"].sum()

        rows.append({
            "Strategy": labels[method],
            "Total Return": f"{(equity.iloc[-1] / equity.iloc[0] - 1):.2%}",
            "Sharpe": f"{sharpe_ratio(daily_returns):.2f}",
            "Sortino": f"{sortino_ratio(daily_returns):.2f}",
            "Max Drawdown": f"{max_drawdown(daily_returns):.2%}",
            "Total Cost Paid": f"{total_cost:.2%}",
            "# Rebalances": len(results[method]["turnover_log"]),
        })

    table = pd.DataFrame(rows).set_index("Strategy")
    print(table.to_string())


if __name__ == "__main__":
    main()