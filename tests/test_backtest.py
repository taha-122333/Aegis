"""
Unit tests for backtest.py. Uses a small synthetic 3-asset price series
so results are predictable and fast to check.
"""

import numpy as np
import pandas as pd
import pytest

from engine.returns import align_trading_days
from engine.backtest import get_rebalance_dates, compute_target_weights, run_backtest


def test_align_trading_days_drops_partial_rows():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.DataFrame(
        {
            "STOCK": [100, np.nan, 102, 103, 104],  # missing on day 2 (e.g. weekend)
            "CRYPTO": [50, 51, 52, 53, 54],          # trades every day
        },
        index=dates,
    )
    aligned = align_trading_days(prices)
    assert len(aligned) == 4  # the NaN row is dropped
    assert not aligned.isna().any().any()


def test_get_rebalance_dates_monthly():
    dates = pd.date_range("2024-01-01", "2024-04-30", freq="B")  # business days
    rebal_dates = get_rebalance_dates(dates, freq="M")
    assert len(rebal_dates) == 4  # Jan, Feb, Mar, Apr
    assert rebal_dates[0].month == 1
    assert rebal_dates[-1].month == 4


def test_equal_weight_target_sums_to_one():
    np.random.seed(0)
    returns_window = pd.DataFrame(
        np.random.normal(0.0005, 0.01, (100, 3)),
        columns=["A", "B", "C"],
    )
    weights = compute_target_weights("equal_weight", returns_window)
    assert np.isclose(weights.sum(), 1.0)
    assert np.allclose(weights.values, 1 / 3)


@pytest.fixture
def sample_prices():
    np.random.seed(1)
    n_days = 400
    dates = pd.bdate_range("2022-01-01", periods=n_days)
    prices = pd.DataFrame(
        {
            "A": 100 * np.cumprod(1 + np.random.normal(0.0004, 0.01, n_days)),
            "B": 100 * np.cumprod(1 + np.random.normal(0.0003, 0.008, n_days)),
            "C": 100 * np.cumprod(1 + np.random.normal(0.0006, 0.015, n_days)),
        },
        index=dates,
    )
    return prices


def test_run_backtest_equal_weight_produces_valid_curve(sample_prices):
    result = run_backtest(sample_prices, method="equal_weight", lookback_days=100, rebalance_freq="M")
    equity_curve = result["equity_curve"]
    assert len(equity_curve) > 0
    assert (equity_curve > 0).all()  # portfolio value should never go to zero or negative


def test_higher_transaction_costs_reduce_final_value(sample_prices):
    low_cost = run_backtest(sample_prices, method="equal_weight", lookback_days=100, transaction_cost_bps=0.0)
    high_cost = run_backtest(sample_prices, method="equal_weight", lookback_days=100, transaction_cost_bps=500.0)
    assert low_cost["equity_curve"].iloc[-1] > high_cost["equity_curve"].iloc[-1]