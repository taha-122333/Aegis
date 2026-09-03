"""
Loads prices, computes returns, and saves a correlation heatmap so we can
eyeball how the asset universe relates before building allocators on top.
"""

import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Ensure project root is on sys.path so sibling package `engine` can be imported
# when running this script directly (e.g. `python notebooks/explore_returns.py`).
# Python sets sys.path[0] to the script's directory, which is `notebooks/`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.data_loader import get_prices
from engine.returns import compute_returns, compute_correlation


def main():
    prices = get_prices()
    returns = compute_returns(prices)
    corr = compute_correlation(returns)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

    ax.set_title("Asset Return Correlation Matrix")
    fig.colorbar(im, ax=ax, label="Correlation")
    fig.tight_layout()

    out_path = "data/correlation_heatmap.png"
    fig.savefig(out_path, dpi=150)
    print(f"Saved heatmap to {out_path}")


if __name__ == "__main__":
    main()