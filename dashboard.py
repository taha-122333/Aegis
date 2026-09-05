"""
Aegis dashboard: an interactive Streamlit interface for exploring
portfolio allocations and risk analysis. This file adds NO new finance
logic of its own — it's purely a visual layer on top of the engine
functions built in Sprints 1-5, exactly as planned ("presentation, built
last, so most time goes into the real math/engineering").

Run with: streamlit run dashboard.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from engine.config import TICKERS
from engine.data_loader import download_prices
from engine.returns import compute_returns, align_trading_days
from engine.allocators import (
    annualized_mean_returns,
    markowitz_min_variance,
    risk_parity,
    kelly_portfolio,
    kelly_portfolio_bounded,
    normalize_weights,
    efficient_frontier,
    portfolio_performance,
)
from engine.risk_metrics import (
    portfolio_returns,
    historical_var,
    historical_cvar,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    stress_test_period,
)
from engine.monte_carlo import simulate_portfolio_paths


st.set_page_config(page_title="Aegis — Portfolio & Risk Dashboard", layout="wide")


@st.cache_data(show_spinner="Downloading price data...")
def load_returns(tickers: tuple) -> pd.DataFrame:
    """
    Downloads and caches return data for a given set of tickers. The
    input is a tuple (not a list) because Streamlit's cache needs
    inputs it can use as a lookup key, and lists can't be used that way
    - tuples can.
    """
    prices = download_prices(tickers=list(tickers))
    prices = align_trading_days(prices)
    return compute_returns(prices)


def compute_weights(returns: pd.DataFrame, method: str, target_return: float = None) -> pd.Series:
    """Dispatches to the right allocator, same pattern as backtest.py and api_service.py."""
    mean_returns = annualized_mean_returns(returns)
    cov = returns.cov() * 252
    if method == "Markowitz (Min Variance)":
        return markowitz_min_variance(mean_returns, cov, target_return=target_return)
    elif method == "Risk Parity":
        return risk_parity(cov)
    elif method == "Kelly (bounded)":
        return kelly_portfolio_bounded(mean_returns, cov)
    elif method == "Kelly (raw, unconstrained)":
        return normalize_weights(kelly_portfolio(mean_returns, cov))
    else:  # Equal Weight
        n = len(mean_returns)
        return pd.Series(1 / n, index=mean_returns.index)


st.title("Aegis — Portfolio Construction & Risk Dashboard")
st.caption("Research/educational tool. Not investment advice.")

# --- Sidebar controls ---
st.sidebar.header("Portfolio Setup")
selected_tickers = st.sidebar.multiselect("Asset universe", options=TICKERS, default=TICKERS)

custom_raw = st.sidebar.text_input("Add custom tickers (comma-separated)", "")
if custom_raw.strip():
    custom = [t.strip().upper() for t in custom_raw.split(",") if t.strip()]
    selected_tickers = list(dict.fromkeys(selected_tickers + custom))  # de-dupe, keep order

method = st.sidebar.selectbox(
    "Allocation method",
    ["Markowitz (Min Variance)", "Risk Parity", "Kelly (bounded)", "Kelly (raw, unconstrained)", "Equal Weight"],
)
if method == "Kelly (raw, unconstrained)":
    st.sidebar.caption(
        "⚠️ Raw Kelly is only stable here because this is a single one-off "
        "allocation. Sprint 4's backtest showed unconstrained Kelly becomes "
        "dangerously unstable when re-estimated repeatedly on a rolling window."
    )

target_return = None
if method == "Markowitz (Min Variance)":
    if st.sidebar.checkbox("Set a target annual return?", value=False):
        target_return = st.sidebar.slider("Target annual return", 0.0, 1.0, 0.15, 0.01)

run_clicked = st.sidebar.button("Run analysis", type="primary")

if len(selected_tickers) < 2:
    st.warning("Select at least 2 tickers in the sidebar to run an analysis.")
    st.stop()

if not run_clicked:
    st.info("Configure your portfolio in the sidebar, then click **Run analysis**.")
    st.stop()

# --- Core computation ---
returns = load_returns(tuple(selected_tickers))
mean_returns = annualized_mean_returns(returns)
cov = returns.cov() * 252
weights = compute_weights(returns, method, target_return)
exp_return, exp_vol = portfolio_performance(weights.values, mean_returns, cov)

# --- Weights section ---
st.header("Portfolio Weights")
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(8, 4))
    weights.sort_values().plot(kind="barh", ax=ax, color="steelblue")
    ax.set_xlabel("Weight")
    ax.set_title(f"{method} — Weights")
    st.pyplot(fig)

with col2:
    st.metric("Expected annual return", f"{exp_return:.2%}")
    st.metric("Expected annual volatility", f"{exp_vol:.2%}")
    st.dataframe(weights.round(4).rename("Weight"))

# --- Efficient frontier ---
st.header("Efficient Frontier")
frontier = efficient_frontier(mean_returns, cov, n_points=30)
fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.plot(frontier["volatility"], frontier["return"], "b-", label="Efficient Frontier")
ax2.scatter(exp_vol, exp_return, marker="*", s=250, color="red", zorder=5, label=method)
ax2.set_xlabel("Volatility (annualized)")
ax2.set_ylabel("Expected Return (annualized)")
ax2.legend()
st.pyplot(fig2)

# --- Risk metrics ---
st.header("Risk Metrics")
port_ret = portfolio_returns(returns, weights)

col3, col4, col5 = st.columns(3)
col3.metric("Sharpe ratio", f"{sharpe_ratio(port_ret):.2f}")
col4.metric("Sortino ratio", f"{sortino_ratio(port_ret):.2f}")
col5.metric("Max drawdown", f"{max_drawdown(port_ret):.2%}")

col6, col7 = st.columns(2)
col6.metric("Historical VaR (95%, 1-day)", f"{historical_var(port_ret):.2%}")
col7.metric("Historical CVaR (95%, 1-day)", f"{historical_cvar(port_ret):.2%}")

try:
    stress = stress_test_period(returns, weights, "2020-02-19", "2020-03-23")
    st.subheader("COVID Crash Stress Test (Feb 19 – Mar 23, 2020)")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Cumulative return", f"{stress['cumulative_return']:.2%}")
    sc2.metric("Worst single day", f"{stress['worst_single_day']:.2%}")
    sc3.metric("Max drawdown during crash", f"{stress['max_drawdown']:.2%}")
except Exception:
    st.caption("Not enough historical data for this ticker set to run the COVID stress test.")

# --- Monte Carlo ---
st.header("Monte Carlo Simulation (1 year, 5,000 paths)")
paths = simulate_portfolio_paths(exp_return, exp_vol, n_days=252, n_simulations=5000)
fig3, ax3 = plt.subplots(figsize=(9, 5))
days = np.arange(paths.shape[1])
sample_idx = np.random.choice(paths.shape[0], size=150, replace=False)
for idx in sample_idx:
    ax3.plot(days, paths[idx], color="steelblue", alpha=0.05)
p5, p50, p95 = np.percentile(paths, [5, 50, 95], axis=0)
ax3.plot(days, p50, color="black", linewidth=2, label="Median path")
ax3.plot(days, p5, color="red", linestyle="--", label="5th percentile")
ax3.plot(days, p95, color="green", linestyle="--", label="95th percentile")
ax3.set_xlabel("Trading days ahead")
ax3.set_ylabel("Portfolio value (starting at 1.0)")
ax3.legend()
st.pyplot(fig3)